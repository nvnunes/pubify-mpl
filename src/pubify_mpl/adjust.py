from __future__ import annotations

from collections.abc import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox


def _iter_figure_shared_labels(fig: Figure) -> Iterable:
    for attr in ("_supxlabel", "_supylabel"):
        label = getattr(fig, attr, None)
        if label is not None:
            yield label


def _iter_movable_figure_text(fig: Figure) -> Iterable:
    seen: set[int] = set()
    for text in [getattr(fig, "_suptitle", None), *list(_iter_figure_shared_labels(fig)), *fig.texts]:
        if text is None or not text.get_visible():
            continue
        if id(text) in seen:
            continue
        if text.get_transform() is not fig.transFigure:
            continue
        seen.add(id(text))
        yield text


def _union_bboxes(bboxes: Iterable[Bbox]) -> Bbox | None:
    filtered = [bbox for bbox in bboxes if bbox.width > 0 and bbox.height > 0]
    if not filtered:
        return None
    return Bbox.from_extents(
        min(bbox.x0 for bbox in filtered),
        min(bbox.y0 for bbox in filtered),
        max(bbox.x1 for bbox in filtered),
        max(bbox.y1 for bbox in filtered),
    )


def iter_axes(root: Figure | Axes) -> Iterable[Axes]:
    """Yield all axes reachable from a figure or axes tree without duplicates."""

    seen: set[int] = set()

    def walk(ax: Axes) -> Iterable[Axes]:
        key = id(ax)
        if key in seen:
            return
        seen.add(key)
        yield ax
        for child in getattr(ax, "child_axes", ()):
            yield from walk(child)

    if isinstance(root, Axes):
        yield from walk(root)
        return

    for ax in root.get_axes():
        yield from walk(ax)


def iter_styled_axes(fig: Figure) -> Iterable[Axes]:
    """Yield axes that participate in pubify's standard styling traversal."""

    yield from iter_axes(fig)


_iter_axes = iter_axes
_iter_styled_axes = iter_styled_axes


def _coerce_axes(target: Figure | Axes, axes: Axes | Iterable[Axes] | None = None) -> list[Axes]:
    if axes is None:
        return list(iter_axes(target))
    if isinstance(axes, Axes):
        return list(iter_axes(axes))
    resolved: list[Axes] = []
    for ax in axes:
        resolved.extend(iter_axes(ax))
    return resolved


def clear_titles(fig: Figure | Axes) -> None:
    """Clear axes titles on a figure or axes tree.

    Args:
        fig: Figure or axes whose titles should be cleared.
    """
    for ax in iter_axes(fig):
        ax.set_title("")
    if isinstance(fig, Figure) and getattr(fig, "_suptitle", None) is not None:
        fig._suptitle.set_text("")


def hide_labels(fig: Figure | Axes) -> None:
    """Remove x/y axis labels and shared figure labels on a figure or axes tree.

    Args:
        fig: Figure or axes whose labels should be removed.
    """
    for ax in iter_axes(fig):
        ax.set_xlabel("")
        ax.set_ylabel("")
    if isinstance(fig, Figure):
        for label in _iter_figure_shared_labels(fig):
            label.set_text("")


def hide_annotations(fig: Figure | Axes) -> None:
    """Remove `ax.text(...)` annotations on a figure or axes tree.

    Args:
        fig: Figure or axes whose text annotations should be removed.
    """
    for ax in iter_axes(fig):
        for text in list(ax.texts):
            text.remove()


def hide_ticks(fig: Figure | Axes) -> None:
    """Remove tick locations and tick labels on a figure or axes tree.

    Args:
        fig: Figure or axes whose ticks should be removed.
    """
    for ax in iter_axes(fig):
        ax.set_xticks([])
        ax.set_yticks([])


def hide_tick_labels(fig: Figure | Axes) -> None:
    """Remove tick labels while preserving tick locations.

    Args:
        fig: Figure or axes whose tick labels should be cleared.
    """
    for ax in iter_axes(fig):
        ax.set_xticklabels([])
        ax.set_yticklabels([])


def hide_grid(target: Figure | Axes, axes: Axes | Iterable[Axes] | None = None) -> None:
    """Disable gridlines on the selected axes.

    Args:
        target: Figure or axes that defines the traversal root.
        axes: Optional axes selection. When omitted, all axes in `target` are used.
    """
    for ax in _coerce_axes(target, axes):
        ax.grid(False)


def hide_cbar(target: Figure | Axes, axes: Axes | Iterable[Axes] | None = None) -> None:
    """Remove colorbar axes attached to the selected axes.

    Args:
        target: Figure or axes that defines the traversal root.
        axes: Optional axes selection. When omitted, all axes in `target` are used.
    """
    target_axes = _coerce_axes(target, axes)
    fig = target.figure if isinstance(target, Axes) else target
    cbar_axes = []
    for ax in target_axes:
        for child in ax.get_children():
            cb = getattr(child, "colorbar", None)
            cb_ax = getattr(cb, "ax", None)
            if cb_ax is not None and cb_ax in fig.axes:
                cbar_axes.append(cb_ax)

    for cbar_ax in dict.fromkeys(cbar_axes):
        fig.delaxes(cbar_ax)


def remove_outside_padding(fig: Figure, pad: float = 0.0) -> None:
    """Best-effort removal of outer figure padding while preserving internal spacing.

    This rescales and translates the full figure composition so the outer margin
    is reduced without recomputing the relative spacing among internal axes.
    It works best for composite figures built from multiple axes, manually added
    colorbar axes, and figure-level labels placed in figure coordinates. If you
    also align companion axes with `match_axis_height(...)` or
    `match_axis_width(...)`, call those after `remove_outside_padding(...)`.

    Args:
        fig: Figure whose outer padding should be reduced.
        pad: Optional figure-coordinate padding to leave on each outer edge.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    pad = float(pad)
    if pad < 0.0 or pad >= 0.5:
        raise ValueError("pad must be in the range [0.0, 0.5).")

    content_boxes = [ax.get_position(original=False).frozen() for ax in fig.axes if ax.get_visible()]
    content_boxes.extend(
        fig.transFigure.inverted().transform_bbox(text.get_window_extent(renderer)).frozen()
        for text in _iter_movable_figure_text(fig)
    )
    content_bbox = _union_bboxes(content_boxes)
    if content_bbox is None:
        return
    if content_bbox.width <= 0 or content_bbox.height <= 0:
        return

    target_bbox = Bbox.from_extents(pad, pad, 1.0 - pad, 1.0 - pad)
    sx = target_bbox.width / content_bbox.width
    sy = target_bbox.height / content_bbox.height
    tx = target_bbox.x0 - content_bbox.x0 * sx
    ty = target_bbox.y0 - content_bbox.y0 * sy

    for ax in fig.axes:
        if not ax.get_visible():
            continue
        pos = ax.get_position(original=False)
        ax.set_position(
            [
                tx + pos.x0 * sx,
                ty + pos.y0 * sy,
                pos.width * sx,
                pos.height * sy,
            ]
        )

    for text in _iter_movable_figure_text(fig):
        x, y = text.get_position()
        text.set_position((tx + x * sx, ty + y * sy))


def match_axis_span(target_ax: Axes, ref_ax: Axes, axis: str = "y") -> None:
    """Match one axes span to another while preserving the orthogonal placement.

    This is useful for manually positioned companion axes such as shared
    colorbars that should match the height or width of a reference data axes
    after layout tweaks or export-time adjustments. If you also call
    `remove_outside_padding(...)`, do that first and then rematch the span.

    Args:
        target_ax: Axes whose span should be updated.
        ref_ax: Reference axes whose span should be matched.
        axis: Which span to match. Use `"y"` to match vertical position and
            height, or `"x"` to match horizontal position and width.
    """
    ref_pos = ref_ax.get_position(original=False)
    target_pos = target_ax.get_position(original=False)

    if axis == "y":
        target_ax.set_position(
            [target_pos.x0, ref_pos.y0, target_pos.width, ref_pos.height]
        )
        return
    if axis == "x":
        target_ax.set_position(
            [ref_pos.x0, target_pos.y0, ref_pos.width, target_pos.height]
        )
        return
    raise ValueError("axis must be 'x' or 'y'.")


def match_axis_height(target_ax: Axes, ref_ax: Axes) -> None:
    """Match a target axes height and vertical position to a reference axes.

    If you also call `remove_outside_padding(...)`, do that first and then call
    `match_axis_height(...)`.
    """
    match_axis_span(target_ax, ref_ax, axis="y")


def match_axis_width(target_ax: Axes, ref_ax: Axes) -> None:
    """Match a target axes width and horizontal position to a reference axes.

    If you also call `remove_outside_padding(...)`, do that first and then call
    `match_axis_width(...)`.
    """
    match_axis_span(target_ax, ref_ax, axis="x")


def set_line_width(fig: Figure | Axes, line_width: float) -> None:
    """Set line width on lines and compatible collections.

    Args:
        fig: Figure or axes whose line-like artists should be updated.
        line_width: New stroke width.
    """
    for ax in iter_axes(fig):
        for line in ax.get_lines():
            line.set_linewidth(line_width)

        for coll in ax.collections:
            if hasattr(coll, "set_linewidth"):
                try:
                    coll.set_linewidth(line_width)
                except Exception:
                    pass


def set_spine_width(fig: Figure | Axes, spine_width: float) -> None:
    """Set spine width on a figure or axes tree.

    Args:
        fig: Figure or axes whose spines should be updated.
        spine_width: New spine stroke width.
    """
    for ax in iter_axes(fig):
        for spine in ax.spines.values():
            spine.set_linewidth(spine_width)


def set_tick_width(fig: Figure | Axes, tick_width: float) -> None:
    """Set tick stroke width on a figure or axes tree.

    Args:
        fig: Figure or axes whose ticks should be updated.
        tick_width: New tick stroke width.
    """
    for ax in iter_axes(fig):
        ax.tick_params(which="both", width=tick_width)


def set_tick_length(fig: Figure | Axes, tick_length: float) -> None:
    """Set tick length on a figure or axes tree.

    Args:
        fig: Figure or axes whose ticks should be updated.
        tick_length: New tick length.
    """
    for ax in _iter_axes(fig):
        ax.tick_params(which="both", length=tick_length)


def set_axes_labelsize(fig: Figure | Axes, axes_labelsize: float) -> None:
    """Set x/y axis label and shared figure label font size.

    Args:
        fig: Figure or axes whose axis-label text should be updated.
        axes_labelsize: New axis-label font size.
    """
    figure = _as_figure(fig)
    for ax in iter_styled_axes(figure):
        ax.xaxis.label.set_fontsize(axes_labelsize)
        ax.yaxis.label.set_fontsize(axes_labelsize)
        _set_wcsaxes_axislabel_property(ax, size=axes_labelsize)
    for label in _iter_figure_shared_labels(figure):
        label.set_fontsize(axes_labelsize)


def set_tick_labelsize(fig: Figure | Axes, tick_labelsize: float) -> None:
    """Set tick label font size on a figure or axes tree.

    Args:
        fig: Figure or axes whose tick labels should be updated.
        tick_labelsize: New tick-label font size.
    """
    for ax in iter_axes(fig):
        ax.tick_params(which="both", labelsize=tick_labelsize)
        _set_wcsaxes_ticklabel_property(ax, size=tick_labelsize)


def set_legend_fontsize(fig: Figure | Axes, legend_fontsize: float) -> None:
    """Set legend text and title font size on a figure or axes tree.

    Args:
        fig: Figure or axes whose legends should be updated.
        legend_fontsize: New legend text and title font size.
    """
    for ax in iter_styled_axes(_as_figure(fig)):
        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontsize(legend_fontsize)
            leg.get_title().set_fontsize(legend_fontsize)


def set_title_fontsize(fig: Figure | Axes, title_fontsize: float) -> None:
    """Set axes title font size on a figure or axes tree.

    Args:
        fig: Figure or axes whose titles should be updated.
        title_fontsize: New title font size.
    """
    for ax in iter_styled_axes(_as_figure(fig)):
        ax.title.set_fontsize(title_fontsize)


def _as_figure(root: Figure | Axes) -> Figure:
    return root.figure if isinstance(root, Axes) else root


def force_font_family(fig: Figure, family: str = "serif") -> None:
    """Force a font family across figure text, labels, ticks, and legends.

    Args:
        fig: Figure whose text artists should be updated.
        family: Font family to apply.
    """
    for text in fig.texts:
        text.set_fontfamily(family)
    for label in _iter_figure_shared_labels(fig):
        label.set_fontfamily(family)

    for ax in iter_styled_axes(fig):
        ax.title.set_fontfamily(family)
        ax.xaxis.label.set_fontfamily(family)
        ax.yaxis.label.set_fontfamily(family)
        _set_wcsaxes_axislabel_property(ax, fontfamily=family)
        _set_wcsaxes_ticklabel_property(ax, fontfamily=family)

        for text in ax.texts:
            text.set_fontfamily(family)

        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontfamily(family)

        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontfamily(family)
            leg.get_title().set_fontfamily(family)


def _iter_wcs_coordinate_helpers(ax: Axes) -> Iterable:
    coords = getattr(ax, "coords", None)
    if coords is None:
        return ()
    try:
        return tuple(coords)
    except TypeError:
        return ()


def _set_wcsaxes_axislabel_property(ax: Axes, **kwargs) -> None:
    for coord in _iter_wcs_coordinate_helpers(ax):
        get_axislabel = getattr(coord, "get_axislabel", None)
        set_axislabel = getattr(coord, "set_axislabel", None)
        if get_axislabel is None or set_axislabel is None:
            continue
        try:
            set_axislabel(get_axislabel(), **kwargs)
        except Exception:
            continue


def _set_wcsaxes_ticklabel_property(ax: Axes, **kwargs) -> None:
    for coord in _iter_wcs_coordinate_helpers(ax):
        set_ticklabel = getattr(coord, "set_ticklabel", None)
        if set_ticklabel is None:
            continue
        try:
            set_ticklabel(**kwargs)
        except Exception:
            continue
