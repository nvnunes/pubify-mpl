import pickle
from pathlib import Path
from typing import Any, Callable

import matplotlib as mpl
from matplotlib import gridspec
import matplotlib.pyplot as plt
from matplotlib.backend_bases import RendererBase
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from . import adjust
from .layout import latex_layout_geometry, normalized_template


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


def save_fig(
    fig_or_ax: Figure | Axes,
    layout: str,
    filename: str | Path,
    *,
    template: dict[str, Any] | None = None,
    caption_lines: int | None = None,
    subcaption_lines: int | None = None,
    force_width: float | None = None,
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
    prepare_copy: Callable[[Figure], None] | None = None,
    verbose: bool = False,
) -> None:
    """Export a copied Matplotlib figure for a named LaTeX layout.

    `save_fig(...)` normally never modifies the original figure in place. It
    clones the figure, applies publication styling and any requested cleanup to
    that copy, resizes the copy to fit the selected layout, and writes the
    exported file. If `skip_clone=True`, export operates on the original figure.
    If `filename` has no suffix, `.pdf` is used by default.

    Args:
        fig_or_ax: `matplotlib.figure.Figure` or `matplotlib.axes.Axes` to export.
        layout: Named layout such as `"onewide"`, `"twowide"`, or `"four"`.
        filename: Output path for the exported figure. If no suffix is given,
            `.pdf` is used. Relative paths are created if needed; absolute paths
            require an existing parent directory.
        template: Optional template dictionary. Overrides any active
            `use_template(...)` context.
        caption_lines: Estimated number of lines in the main caption. Defaults to `1`.
        subcaption_lines: Estimated number of lines in each subcaption. Defaults to `0`.
        force_width: Optional width override in inches. Must still fit inside the
            chosen layout budget.
        force_aspect: Optional aspect ratio override for the exported copy.
        dpi: Export DPI for the copied figure.
        keep_titles: Keep axis titles on the copied figure instead of clearing them.
        hide_labels: Remove axis labels from the copied figure.
        hide_annotations: Remove `ax.text(...)` annotations from the copied figure.
        hide_ticks: Remove tick marks and tick labels from the copied figure.
        hide_tick_labels: Remove tick labels while keeping tick positions.
        hide_grid: Disable the grid on the copied figure.
        hide_cbar: Remove a colorbar when exporting a single-axes panel.
        skip_clone: Skip the pickle-clone step and export the original figure in place.
        skip_rasterize: Disable the vector-output rasterization heuristic.
        rasterize_scatter_threshold: Collection-size threshold for auto-rasterizing
            scatter-like artists in vector outputs.
        rasterize_image_pixel_threshold: Pixel-count threshold for auto-rasterizing
            image artists in vector outputs.
        rasterize_line_vertex_threshold: Vertex-count threshold for auto-rasterizing
            line artists in vector outputs.
        extra_rcparams: Additional Matplotlib rcParams applied during export.
        prepare_copy: Optional callback that receives the copied figure after
            the standard cleanup/style pass and can make additional changes
            before rasterization and export sizing.
        verbose: Print export diagnostics.
    """
    resolved_template = normalized_template(template)
    base_fontsize = resolved_template["base_fontsize_pt"]

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

    if isinstance(fig_or_ax, mpl.axes.Axes):
        fig = fig_or_ax.figure
        axis_idx = fig.axes.index(fig_or_ax)
    elif isinstance(fig_or_ax, mpl.figure.Figure):
        fig = fig_or_ax
        axis_idx = 0
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
        keep_ax = fig2.axes[axis_idx]
        keep_extra_axes = set()

        if not hide_cbar:
            for child in keep_ax.get_children():
                cb = getattr(child, "colorbar", None)
                if cb is not None and getattr(cb, "ax", None) is not None:
                    keep_extra_axes.add(cb.ax)

        for ax in list(fig2.axes):
            if ax is keep_ax or ax in keep_extra_axes:
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
            adjust.hide_grid(keep_ax)

        if hide_cbar:
            adjust.hide_cbar(keep_ax)

        rc = {
            "savefig.dpi": dpi,
            "figure.dpi": dpi,
            "font.size": base_fontsize,
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Latin Modern Roman", "LMRoman10"],
            "mathtext.fontset": "cm",
            "text.latex.preamble": r"""
\usepackage[T1]{fontenc}
\usepackage[tracking]{microtype}
\usepackage{amsmath}
\usepackage{amssymb}
""",
        }
        if extra_rcparams:
            rc.update(extra_rcparams)

        with mpl.rc_context(mpl.rcParamsDefault):
            with mpl.rc_context(rc):
                adjust.force_font_family(fig2, family="serif")
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

                if prepare_copy is not None:
                    prepare_copy(fig2)

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

                if force_aspect is not None:
                    force_aspect = float(force_aspect)
                else:
                    fig_aspect = fig2.axes[0].get_aspect()
                    if fig_aspect in {"equal", 1.0}:
                        force_aspect = 1.0
                    elif fig_aspect != "auto":
                        force_aspect = float(fig_aspect)

                if not isinstance(layout, str):
                    raise TypeError(
                        "layout must be a named layout string. "
                        "Use force_width=... to constrain the exported width."
                    )

                layout_geometry = latex_layout_geometry(
                    layout=layout,
                    layout_spec=resolved_template,
                    caption_lines=caption_lines,
                    subcaption_lines=subcaption_lines,
                )
                layout_width = layout_geometry["width_in"]
                layout_height = layout_geometry["height_in"]

                if force_width is None:
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

                for _ in range(10):
                    wscale = width / bbox.width
                    hscale = height / bbox.height
                    if abs(wscale - 1.0) < 0.005 and abs(hscale - 1.0) < 0.005:
                        break
                    current_w, current_h = fig2.get_size_inches()
                    fig2.set_size_inches(current_w * wscale, current_h * hscale, forward=True)
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
