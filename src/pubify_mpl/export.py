from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import inspect
import pickle
from pathlib import Path
from typing import Any, Callable, TypeAlias

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.transforms import BboxBase

from . import adjust
from .rc import resolved_pubify_rc
from .style import DEFAULT_STYLE, StyleSpec, normalized_style


@dataclass(frozen=True)
class ResolvedStyle:
    """Resolved Matplotlib styling values available to export callbacks.

    Attributes:
        font_family: Matplotlib font family applied to prepared figure text,
            or ``None`` when no font family is forced.
        base_fontsize_pt: Base font size in points.
        axes_labelsize_pt: Axis-label font size in points, or a negative value
            when labels should keep their existing size.
        tick_labelsize_pt: Tick-label font size in points, or a negative value
            when tick labels should keep their existing size.
        legend_fontsize_pt: Legend font size in points, or a negative value
            when legends should keep their existing size.
        title_fontsize_pt: Title font size in points, or a negative value when
            titles should keep their existing size.
        line_width_pt: Line width in points, or a negative value when line
            widths should keep their existing size.
        axes_line_width_pt: Spine and tick width in points, or a negative value
            when those widths should keep their existing size.
        tick_length_pt: Tick length in points, or a negative value when tick
            lengths should keep their existing size.
    """

    font_family: str | None
    base_fontsize_pt: float
    axes_labelsize_pt: float
    tick_labelsize_pt: float
    legend_fontsize_pt: float
    title_fontsize_pt: float
    line_width_pt: float
    axes_line_width_pt: float
    tick_length_pt: float


PrepareExportCallback: TypeAlias = (
    Callable[[Figure], None]
    | Callable[[Figure, ResolvedStyle], None]
)

def clone_figure_pickle(fig: Figure) -> Figure:
    """Clone a Matplotlib figure through pickle."""

    blob = pickle.dumps(fig, protocol=pickle.HIGHEST_PROTOCOL)
    fig2 = pickle.loads(blob)
    return fig2


def figure_renderer(fig: Figure) -> RendererBase:
    """Return a renderer for a Matplotlib figure after drawing its canvas."""

    fig.canvas.draw()
    try:
        return fig.canvas.get_renderer()
    except AttributeError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        return canvas.get_renderer()


def figure_tight_bbox(fig: Figure) -> BboxBase:
    """Return the drawn figure's tight bounding box in inches."""

    return fig.get_tightbbox(figure_renderer(fig))


_get_renderer = figure_renderer


def _is_vector_output(path: str | Path) -> bool:
    return Path(path).suffix.lower() in {".pdf", ".svg", ".eps", ".ps", ".pgf"}


def _auto_rasterize_axes(
    ax: Axes,
    *,
    scatter_threshold: int = 1000,
    image_pixel_threshold: int = 1_000_000,
    line_vertex_threshold: int = 2000,
) -> list[str]:
    rasterized: list[str] = []

    for coll in ax.collections:
        offsets = getattr(coll, "get_offsets", None)
        if offsets is not None:
            try:
                if len(offsets()) >= scatter_threshold:
                    coll.set_rasterized(True)
                    rasterized.append(type(coll).__name__)
                    continue
            except Exception:
                pass

        get_paths = getattr(coll, "get_paths", None)
        if get_paths is not None:
            try:
                if len(get_paths()) >= scatter_threshold:
                    coll.set_rasterized(True)
                    rasterized.append(type(coll).__name__)
            except Exception:
                pass

    for img in ax.images:
        get_array = getattr(img, "get_array", None)
        if get_array is None:
            continue
        try:
            arr = get_array()
            shape = getattr(arr, "shape", ())
            if len(shape) >= 2 and shape[0] * shape[1] >= image_pixel_threshold:
                img.set_rasterized(True)
                rasterized.append(type(img).__name__)
        except Exception:
            pass

    for line in ax.lines:
        try:
            if len(line.get_xdata(orig=False)) >= line_vertex_threshold:
                line.set_rasterized(True)
                rasterized.append(type(line).__name__)
        except Exception:
            pass

    return rasterized


def _auto_rasterize_figure(
    fig: Figure,
    *,
    scatter_threshold: int = 1000,
    image_pixel_threshold: int = 1_000_000,
    line_vertex_threshold: int = 2000,
) -> list[str]:
    rasterized: list[str] = []
    for ax in fig.get_axes():
        rasterized.extend(
            _auto_rasterize_axes(
                ax,
                scatter_threshold=scatter_threshold,
                image_pixel_threshold=image_pixel_threshold,
                line_vertex_threshold=line_vertex_threshold,
            )
        )
    return rasterized


def auto_rasterize_figure(
    fig: Figure,
    *,
    scatter_threshold: int = 1000,
    image_pixel_threshold: int = 1_000_000,
    line_vertex_threshold: int = 2000,
) -> list[str]:
    """Rasterize heavy Matplotlib artists before vector export."""

    return _auto_rasterize_figure(
        fig,
        scatter_threshold=scatter_threshold,
        image_pixel_threshold=image_pixel_threshold,
        line_vertex_threshold=line_vertex_threshold,
    )


def _resolved_style_from_spec(
    style: StyleSpec | None = None,
    *,
    font_family: str | None,
) -> ResolvedStyle:
    resolved = normalized_style(style)
    return ResolvedStyle(
        font_family=font_family,
        base_fontsize_pt=float(resolved["base_fontsize_pt"]),
        axes_labelsize_pt=float(resolved["axes_labelsize_pt"]),
        tick_labelsize_pt=float(resolved["tick_labelsize_pt"]),
        legend_fontsize_pt=float(resolved["legend_fontsize_pt"]),
        title_fontsize_pt=float(resolved["title_fontsize_pt"]),
        line_width_pt=float(resolved["line_width_pt"]),
        axes_line_width_pt=float(resolved["axes_line_width_pt"]),
        tick_length_pt=float(resolved["tick_length_pt"]),
    )


def _invoke_prepare_export(
    prepare_export: PrepareExportCallback,
    fig_copy: Figure,
    style: ResolvedStyle,
) -> None:
    try:
        signature = inspect.signature(prepare_export)
    except (TypeError, ValueError) as exc:
        raise TypeError("prepare_export must be an inspectable callable.") from exc

    positional_capacity = 0
    has_varargs = False
    for parameter in signature.parameters.values():
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional_capacity += 1
        elif parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            has_varargs = True

    if positional_capacity == 0 and not has_varargs:
        raise TypeError(
            "prepare_export must accept at least one positional argument for the export figure."
        )
    if not has_varargs and positional_capacity not in {1, 2}:
        raise TypeError(
            "prepare_export must accept either one positional argument (fig_export) or "
            "two positional arguments (fig_export, style)."
        )
    if has_varargs or positional_capacity >= 2:
        prepare_export(fig_copy, style)
        return
    prepare_export(fig_copy)


@contextmanager
def prepare_figure(
    fig_or_ax: Figure | Axes,
    *,
    style: StyleSpec | None = None,
    dpi: int = 300,
    keep_titles: bool = False,
    hide_labels: bool = False,
    hide_annotations: bool = False,
    hide_ticks: bool = False,
    hide_tick_labels: bool = False,
    hide_grid: bool = False,
    hide_cbar: bool = False,
    skip_clone: bool = False,
    extra_rcparams: dict[str, Any] | None = None,
    text_usetex: bool = False,
    font_family: str | None = None,
    prepare_export: PrepareExportCallback | None = None,
) -> Iterator[Figure]:
    """Yield a Matplotlib figure prepared for downstream export.

    The original figure is cloned by default. Passing an ``Axes`` isolates that
    panel and, unless ``hide_cbar=True``, any attached colorbar axes. The yielded
    figure is closed automatically when the context exits unless
    ``skip_clone=True`` was used.
    """

    resolved_style = normalized_style(style)
    style_object = _resolved_style_from_spec(resolved_style, font_family=font_family)

    export_full_figure = False
    if isinstance(fig_or_ax, mpl.axes.Axes):
        fig = fig_or_ax.figure
        axis_idx = fig.axes.index(fig_or_ax)
    elif isinstance(fig_or_ax, mpl.figure.Figure):
        fig = fig_or_ax
        axis_idx = None
        export_full_figure = True
    else:
        raise TypeError("fig_or_ax must be a Figure or Axes instance.")

    if skip_clone:
        fig2 = fig
    else:
        try:
            fig2 = clone_figure_pickle(fig)
        except Exception as exc:
            raise RuntimeError(
                "Figure pickle-clone failed. This can happen with some custom artists/backends.\n"
                f"Original error: {type(exc).__name__}: {exc}"
            ) from exc

    try:
        export_ax = None
        if not export_full_figure:
            assert axis_idx is not None
            export_ax = fig2.axes[axis_idx]
            keep_extra_axes = set()
            if not hide_cbar:
                for child in export_ax.get_children():
                    cb = getattr(child, "colorbar", None)
                    if cb is not None and getattr(cb, "ax", None) is not None:
                        keep_extra_axes.add(cb.ax)

            for ax in list(fig2.axes):
                if ax is export_ax or ax in keep_extra_axes:
                    continue
                fig2.delaxes(ax)

            if len(fig2.axes) == 1:
                fig2.axes[0].set_subplotspec(gridspec.GridSpec(1, 1, figure=fig2)[0])

        if not keep_titles:
            adjust.clear_titles(fig2)
        if hide_labels:
            adjust.hide_labels(fig2)
        if hide_annotations:
            adjust.hide_annotations(fig2)
        if hide_ticks:
            adjust.hide_ticks(fig2)
        elif hide_tick_labels:
            adjust.hide_tick_labels(fig2)
        if hide_grid:
            adjust.hide_grid(fig2)
        if hide_cbar:
            if export_full_figure:
                adjust.hide_cbar(fig2)
            else:
                assert export_ax is not None
                adjust.hide_cbar(export_ax)

        rc = resolved_pubify_rc(
            style=resolved_style,
            extra_rcparams=extra_rcparams,
            text_usetex=text_usetex,
            font_family=font_family,
        )
        rc["savefig.dpi"] = dpi
        rc["figure.dpi"] = dpi

        with mpl.rc_context(mpl.rcParamsDefault):
            with mpl.rc_context(rc):
                if font_family is not None:
                    adjust.force_font_family(fig2, family=font_family)
                fig2.set_facecolor("white")
                if resolved_style["axes_labelsize_pt"] >= 0:
                    adjust.set_axes_labelsize(fig2, resolved_style["axes_labelsize_pt"])
                if resolved_style["tick_labelsize_pt"] >= 0:
                    adjust.set_tick_labelsize(fig2, resolved_style["tick_labelsize_pt"])
                if resolved_style["legend_fontsize_pt"] >= 0:
                    adjust.set_legend_fontsize(fig2, resolved_style["legend_fontsize_pt"])
                if keep_titles and resolved_style["title_fontsize_pt"] >= 0:
                    adjust.set_title_fontsize(fig2, resolved_style["title_fontsize_pt"])
                if resolved_style["line_width_pt"] >= 0:
                    adjust.set_line_width(fig2, resolved_style["line_width_pt"])
                if resolved_style["axes_line_width_pt"] >= 0:
                    adjust.set_spine_width(fig2, resolved_style["axes_line_width_pt"])
                    adjust.set_tick_width(fig2, resolved_style["axes_line_width_pt"])
                if resolved_style["tick_length_pt"] >= 0:
                    adjust.set_tick_length(fig2, resolved_style["tick_length_pt"])
                if prepare_export is not None:
                    _invoke_prepare_export(prepare_export, fig2, style_object)
                yield fig2
    finally:
        if not skip_clone:
            plt.close(fig2)


def save_fig(
    fig_or_ax: Figure | Axes,
    filename: str | Path,
    *,
    width: float | None = None,
    height: float | None = None,
    style: StyleSpec | None = None,
    dpi: int = 300,
    keep_titles: bool = False,
    hide_labels: bool = False,
    hide_annotations: bool = False,
    hide_ticks: bool = False,
    hide_tick_labels: bool = False,
    hide_grid: bool = False,
    hide_cbar: bool = False,
    skip_clone: bool = False,
    skip_rasterize: bool = False,
    rasterize_scatter_threshold: int = 1000,
    rasterize_image_pixel_threshold: int = 1_000_000,
    rasterize_line_vertex_threshold: int = 2000,
    extra_rcparams: dict[str, Any] | None = None,
    text_usetex: bool = False,
    font_family: str | None = None,
    prepare_export: PrepareExportCallback | None = None,
    bbox_inches: str | None = "tight",
    pad_inches: float = 0.0,
    verbose: bool = False,
) -> None:
    """Prepare and save a Matplotlib figure with explicit output sizing.

    This Matplotlib-only helper does not know about LaTeX layout names or TeX
    templates. Callers that need document-aware layout sizing should use
    ``pubify_tex.save_fig(...)``.
    """

    output_filename = Path(filename).expanduser()
    if not output_filename.suffix:
        output_filename = output_filename.with_suffix(".png")
    parent_dir = output_filename.parent
    if output_filename.is_absolute():
        if not parent_dir.exists():
            raise FileNotFoundError(
                f"Parent directory does not exist for output file: {output_filename}"
            )
    else:
        parent_dir.mkdir(parents=True, exist_ok=True)

    if width is not None:
        width = float(width)
        if width <= 0:
            raise ValueError("width must be positive.")
    if height is not None:
        height = float(height)
        if height <= 0:
            raise ValueError("height must be positive.")

    with prepare_figure(
        fig_or_ax,
        style=style,
        dpi=dpi,
        keep_titles=keep_titles,
        hide_labels=hide_labels,
        hide_annotations=hide_annotations,
        hide_ticks=hide_ticks,
        hide_tick_labels=hide_tick_labels,
        hide_grid=hide_grid,
        hide_cbar=hide_cbar,
        skip_clone=skip_clone,
        extra_rcparams=extra_rcparams,
        text_usetex=text_usetex,
        font_family=font_family,
        prepare_export=prepare_export,
    ) as fig_export:
        if width is not None or height is not None:
            current_width, current_height = fig_export.get_size_inches()
            if width is None:
                assert height is not None
                width = current_width * (height / current_height)
            if height is None:
                height = current_height * (width / current_width)
            fig_export.set_size_inches(width, height, forward=True)

        rasterized_artists = []
        if not skip_rasterize and _is_vector_output(output_filename):
            rasterized_artists = auto_rasterize_figure(
                fig_export,
                scatter_threshold=rasterize_scatter_threshold,
                image_pixel_threshold=rasterize_image_pixel_threshold,
                line_vertex_threshold=rasterize_line_vertex_threshold,
            )

        if verbose:
            bbox = figure_tight_bbox(fig_export)
            print(f"tight bbox inches: {bbox.width:.2f} {bbox.height:.2f}")
            if rasterized_artists:
                print(f"auto-rasterized artists: {', '.join(rasterized_artists)}")

        fig_export.savefig(
            output_filename,
            dpi=dpi,
            bbox_inches=bbox_inches,
            pad_inches=pad_inches,
        )
