from __future__ import annotations

from collections.abc import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .rc import PUBIFY_FONT_FAMILY


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
    """Remove x/y axis labels on a figure or axes tree.

    Args:
        fig: Figure or axes whose labels should be removed.
    """
    for ax in iter_axes(fig):
        ax.set_xlabel("")
        ax.set_ylabel("")


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
    """Set x/y axis label font size on a figure or axes tree.

    Args:
        fig: Figure or axes whose axis-label text should be updated.
        axes_labelsize: New axis-label font size.
    """
    for ax in iter_styled_axes(_as_figure(fig)):
        ax.xaxis.label.set_fontsize(axes_labelsize)
        ax.yaxis.label.set_fontsize(axes_labelsize)


def set_tick_labelsize(fig: Figure | Axes, tick_labelsize: float) -> None:
    """Set tick label font size on a figure or axes tree.

    Args:
        fig: Figure or axes whose tick labels should be updated.
        tick_labelsize: New tick-label font size.
    """
    for ax in iter_axes(fig):
        ax.tick_params(which="both", labelsize=tick_labelsize)


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


def force_font_family(fig: Figure, family: str = PUBIFY_FONT_FAMILY) -> None:
    """Force a font family across figure text, labels, ticks, and legends.

    Args:
        fig: Figure whose text artists should be updated.
        family: Font family to apply.
    """
    for text in fig.texts:
        text.set_fontfamily(family)

    for ax in iter_styled_axes(fig):
        ax.title.set_fontfamily(family)
        ax.xaxis.label.set_fontfamily(family)
        ax.yaxis.label.set_fontfamily(family)

        for text in ax.texts:
            text.set_fontfamily(family)

        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontfamily(family)

        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontfamily(family)
            leg.get_title().set_fontfamily(family)
