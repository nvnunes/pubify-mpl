from dataclasses import dataclass
import inspect
import pickle
from pathlib import Path
from typing import Any, Callable, TypeAlias

import matplotlib as mpl
from matplotlib import gridspec
import matplotlib.pyplot as plt
from matplotlib.backend_bases import RendererBase
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from . import adjust
from .layout import latex_layout_geometry, normalized_template
from .rc import PUBIFY_FONT_FAMILY, resolved_pubify_rc


@dataclass(frozen=True)
class ResolvedStyle:
    """Resolved export styling values available to ``prepare_export`` callbacks."""

    font_family: str
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
    blob = pickle.dumps(fig, protocol=pickle.HIGHEST_PROTOCOL)
    fig2 = pickle.loads(blob)
    return fig2


def _get_renderer(fig: Figure) -> RendererBase:
    fig.canvas.draw()
    try:
        return fig.canvas.get_renderer()
    except AttributeError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        return canvas.get_renderer()


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


def _resolved_style_from_template(
    resolved_template: dict[str, Any],
    *,
    font_family: str,
) -> ResolvedStyle:
    return ResolvedStyle(
        font_family=font_family,
        base_fontsize_pt=float(resolved_template["base_fontsize_pt"]),
        axes_labelsize_pt=float(resolved_template["axes_labelsize_pt"]),
        tick_labelsize_pt=float(resolved_template["tick_labelsize_pt"]),
        legend_fontsize_pt=float(resolved_template["legend_fontsize_pt"]),
        title_fontsize_pt=float(resolved_template["title_fontsize_pt"]),
        line_width_pt=float(resolved_template["line_width_pt"]),
        axes_line_width_pt=float(resolved_template["axes_line_width_pt"]),
        tick_length_pt=float(resolved_template["tick_length_pt"]),
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

    if positional_capacity == 1:
        prepare_export(fig_copy)
        return


def save_fig(
    fig_or_ax: Figure | Axes,
    layout: str,
    filename: str | Path,
    *,
    template: dict[str, Any] | None = None,
    caption_lines: int | None = None,
    subcaption_lines: int | None = None,
    force_width: float | None = None,
    force_height: float | None = None,
    force_aspect: float | None = None,
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
    prepare_export: PrepareExportCallback | None = None,
    verbose: bool = False,
) -> None:
    """Export a copied Matplotlib figure or axes for a named LaTeX layout.

    `save_fig(...)` normally never modifies the original figure in place. It
    clones the figure, applies publication styling and any requested cleanup to
    that copy, resizes the copy to fit the selected layout, and writes the
    exported file. Passing a `Figure` exports the full composed figure as one
    artifact. Passing an `Axes` exports only that axes panel, optionally keeping
    an attached colorbar. If `skip_clone=True`, export operates on the original
    figure. If `filename` has no suffix, `.pdf` is used by default.

    Args:
        fig_or_ax: `matplotlib.figure.Figure` to export as a full composed
            figure, or `matplotlib.axes.Axes` to export as a single panel.
        layout: Named layout such as `"onewide"`, `"twowide"`, or `"four"`.
        filename: Output path for the exported figure. If no suffix is given,
            `.pdf` is used. Relative paths are created if needed; absolute paths
            require an existing parent directory.
        template: Optional template dictionary. Overrides any active
            `use_template(...)` context.
        caption_lines: Estimated number of lines in the main caption. Defaults to `1`.
        subcaption_lines: Estimated number of lines in each subcaption. Defaults to `0`.
        force_width: Optional width override in inches. Supported for non-wide
            layouts only and must still fit inside the chosen layout budget.
        force_height: Optional height cap in inches. The export is first sized
            normally for the chosen layout and then uniformly scaled down if it
            would otherwise exceed this height. On wide layouts, the default
            sizing uses the full layout width before this cap is applied.
        force_aspect: Optional aspect ratio override for the exported copy.
        dpi: Export DPI for the copied figure.
        keep_titles: Keep axis titles on the copied figure instead of clearing them.
        hide_labels: Remove axis labels and shared figure labels from the copied
            figure.
        hide_annotations: Remove `ax.text(...)` annotations from the copied figure.
        hide_ticks: Remove tick marks and tick labels from the copied figure.
        hide_tick_labels: Remove tick labels while keeping tick positions.
        hide_grid: Disable the grid on the copied figure.
        hide_cbar: Remove attached colorbars and all colorbar axes from the
            copied figure.
        skip_clone: Skip the pickle-clone step and export the original figure in place.
        skip_rasterize: Disable the vector-output rasterization heuristic.
        rasterize_scatter_threshold: Collection-size threshold for auto-rasterizing
            scatter-like artists in vector outputs.
        rasterize_image_pixel_threshold: Pixel-count threshold for auto-rasterizing
            image artists in vector outputs.
        rasterize_line_vertex_threshold: Vertex-count threshold for auto-rasterizing
            line artists in vector outputs.
        extra_rcparams: Additional Matplotlib rcParams applied during export.
        prepare_export: Optional callback that receives the figure object that
            will be exported after the standard cleanup/style pass and can make
            additional changes before rasterization and export sizing. For
            `Figure` input, this is the full composed figure copy. For `Axes`
            input, this is the isolated single-panel figure copy. When
            `skip_clone=True`, this may be the original figure. Callbacks may
            accept either `prepare_export(fig_export)` or
            `prepare_export(fig_export, style)`, where `style` is a
            `ResolvedStyle` carrying the resolved publication styling values.
        verbose: Print export diagnostics.
    """
    resolved_template = normalized_template(template)
    font_family = PUBIFY_FONT_FAMILY
    resolved_style = _resolved_style_from_template(
        resolved_template,
        font_family=font_family,
    )

    if caption_lines is None:
        caption_lines = 1
    caption_lines = int(caption_lines)
    if caption_lines < 0:
        raise ValueError("caption_lines must be non-negative.")

    if subcaption_lines is None:
        subcaption_lines = 0
    subcaption_lines = int(subcaption_lines)
    if subcaption_lines < 0:
        raise ValueError("subcaption_lines must be non-negative.")

    if force_width is not None and force_height is not None:
        raise ValueError("force_width and force_height are mutually exclusive.")
    if isinstance(force_width, str):
        raise ValueError("force_width must be a float in inches.")
    if force_height is not None:
        force_height = float(force_height)
        if force_height <= 0.0:
            raise ValueError("force_height must be positive.")

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

    output_filename = Path(filename).expanduser()
    if not output_filename.suffix:
        output_filename = output_filename.with_suffix(".pdf")
    parent_dir = output_filename.parent
    if output_filename.is_absolute():
        if not parent_dir.exists():
            raise FileNotFoundError(
                f"Parent directory does not exist for output file: {output_filename}"
            )
    else:
        parent_dir.mkdir(parents=True, exist_ok=True)

    fig2 = None
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
            template=resolved_template,
            extra_rcparams=extra_rcparams,
        )
        rc["savefig.dpi"] = dpi
        rc["figure.dpi"] = dpi

        with mpl.rc_context(mpl.rcParamsDefault):
            with mpl.rc_context(rc):
                adjust.force_font_family(fig2, family=font_family)
                fig2.set_facecolor("white")
                if resolved_template["axes_labelsize_pt"] >= 0:
                    adjust.set_axes_labelsize(fig2, resolved_template["axes_labelsize_pt"])
                if resolved_template["tick_labelsize_pt"] >= 0:
                    adjust.set_tick_labelsize(fig2, resolved_template["tick_labelsize_pt"])
                if resolved_template["legend_fontsize_pt"] >= 0:
                    adjust.set_legend_fontsize(fig2, resolved_template["legend_fontsize_pt"])
                if keep_titles and resolved_template["title_fontsize_pt"] >= 0:
                    adjust.set_title_fontsize(fig2, resolved_template["title_fontsize_pt"])
                if resolved_template["line_width_pt"] >= 0:
                    adjust.set_line_width(fig2, resolved_template["line_width_pt"])

                if resolved_template["axes_line_width_pt"] >= 0:
                    adjust.set_spine_width(fig2, resolved_template["axes_line_width_pt"])
                    adjust.set_tick_width(fig2, resolved_template["axes_line_width_pt"])

                if resolved_template["tick_length_pt"] >= 0:
                    adjust.set_tick_length(fig2, resolved_template["tick_length_pt"])

                if prepare_export is not None:
                    _invoke_prepare_export(prepare_export, fig2, resolved_style)

                rasterized_artists = []
                if not skip_rasterize and _is_vector_output(output_filename):
                    rasterized_artists = _auto_rasterize_figure(
                        fig2,
                        scatter_threshold=rasterize_scatter_threshold,
                        image_pixel_threshold=rasterize_image_pixel_threshold,
                        line_vertex_threshold=rasterize_line_vertex_threshold,
                    )

                renderer = _get_renderer(fig2)
                bbox = fig2.get_tightbbox(renderer)

                preserve_composite_aspect = False
                if force_aspect is not None:
                    force_aspect = float(force_aspect)
                elif export_full_figure:
                    force_aspect = bbox.height / bbox.width
                    preserve_composite_aspect = True
                else:
                    fig_aspect = fig2.axes[0].get_aspect()
                    if fig_aspect in {"equal", 1.0}:
                        force_aspect = 1.0
                    elif fig_aspect != "auto":
                        force_aspect = float(fig_aspect)

                if not isinstance(layout, str):
                    raise TypeError(
                        "layout must be a named layout string. "
                        "Use force_width=... or force_height=... to constrain the export."
                    )

                layout_geometry = latex_layout_geometry(
                    layout=layout,
                    layout_spec=resolved_template,
                    caption_lines=caption_lines,
                    subcaption_lines=subcaption_lines,
                )
                layout_width = layout_geometry["width_in"]
                layout_height = layout_geometry["height_in"]
                wide_layout = layout in {"onewide", "twowide", "threewide"}

                if wide_layout:
                    if force_width is not None:
                        raise ValueError(
                            "force_width is not supported for layouts "
                            "'onewide', 'twowide', and 'threewide'. "
                            "Wide layouts always use the full layout width."
                        )
                    width = layout_width
                    if force_aspect is None:
                        force_aspect = bbox.height / bbox.width
                    height = width if force_aspect == 1.0 else width * force_aspect
                elif force_width is None:
                    if force_aspect == 1.0:
                        width = layout_width
                        height = layout_height
                    elif force_aspect is not None:
                        target_width = layout_height / force_aspect
                        target_height = layout_width * force_aspect
                        if target_width > layout_width:
                            width = layout_width
                            height = target_height
                        else:
                            width = target_width
                            height = layout_height
                    else:
                        width = layout_width
                        height = layout_height
                else:
                    width = float(force_width)
                    if width > layout_width + 1e-9:
                        raise ValueError(
                            f"force_width={width:.5f}in exceeds the available width "
                            f"for layout '{layout}' ({layout_width:.5f}in)."
                        )
                    if force_aspect is None:
                        force_aspect = bbox.height / bbox.width
                    height = width if force_aspect == 1.0 else width * force_aspect
                    if height > layout_height + 1e-9:
                        raise ValueError(
                            f"force_width={width:.5f}in with force_aspect {force_aspect:.5f} "
                            f"produces height {height:.5f}in, which exceeds the "
                            f"available height for layout '{layout}' "
                            f"({layout_height:.5f}in)."
                        )

                if force_height is not None and height > force_height + 1e-9:
                    scale = force_height / height
                    width *= scale
                    height *= scale

                for _ in range(10):
                    if preserve_composite_aspect:
                        scale = min(width / bbox.width, height / bbox.height)
                        if abs(scale - 1.0) < 0.005:
                            break
                        current_w, current_h = fig2.get_size_inches()
                        fig2.set_size_inches(current_w * scale, current_h * scale, forward=True)
                    else:
                        wscale = width / bbox.width
                        hscale = height / bbox.height
                        if abs(wscale - 1.0) < 0.005 and abs(hscale - 1.0) < 0.005:
                            break
                        current_w, current_h = fig2.get_size_inches()
                        fig2.set_size_inches(
                            current_w * wscale,
                            current_h * hscale,
                            forward=True,
                        )
                    fig2.canvas.draw()
                    bbox = fig2.get_tightbbox(renderer)

                if verbose:
                    print(f"tight bbox inches: {bbox.width:.2f} {bbox.height:.2f}")
                    if rasterized_artists:
                        print(f"auto-rasterized artists: {', '.join(rasterized_artists)}")

                fig2.savefig(
                    output_filename,
                    dpi=dpi,
                    bbox_inches="tight",
                    pad_inches=0.0,
                )
    finally:
        if fig2 is not None:
            plt.close(fig2)
