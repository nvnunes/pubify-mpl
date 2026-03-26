import pickle

from matplotlib.figure import Figure


def clone_figure_pickle(fig: Figure) -> Figure:
    blob = pickle.dumps(fig, protocol=pickle.HIGHEST_PROTOCOL)
    fig2 = pickle.loads(blob)
    return fig2


def force_font_family(fig: Figure, family: str = "serif") -> None:
    for ax in fig.get_axes():
        ax.title.set_fontfamily(family)
        ax.xaxis.label.set_fontfamily(family)
        ax.yaxis.label.set_fontfamily(family)

        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontfamily(family)

        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontfamily(family)
            leg.get_title().set_fontfamily(family)


def apply_publication_style(
    fig: Figure,
    base_fontsize: float = 9.0,
    axes_labelsize: float | None = None,
    tick_labelsize: float | None = None,
    legend_fontsize: float | None = None,
    title_fontsize: float | None = None,
    line_width: float = 1.2,
    spine_width: float = 0.8,
    tick_width: float = 0.8,
    tick_length: float = 3.0,
) -> None:
    """Apply publication-oriented styling to an existing figure.

    This helper mutates the figure in place. It is intended for advanced use on
    the copied export figure, typically via `save_fig(..., prepare_copy=...)`,
    rather than on the original interactive figure.

    Args:
        fig: Figure to restyle.
        base_fontsize: Starting font size used to derive text sizes.
        axes_labelsize: Axis-label font size. Defaults to `base_fontsize`.
        tick_labelsize: Tick-label font size. Defaults to `base_fontsize - 1`.
        legend_fontsize: Legend text size. Defaults to `base_fontsize - 1`.
        title_fontsize: Axes-title font size. Defaults to `base_fontsize + 1`.
        line_width: Stroke width applied to plotted lines and compatible
            collections.
        spine_width: Stroke width applied to axes spines.
        tick_width: Stroke width applied to ticks.
        tick_length: Tick length.
    """
    if axes_labelsize is None:
        axes_labelsize = base_fontsize
    if tick_labelsize is None:
        tick_labelsize = base_fontsize - 1
    if legend_fontsize is None:
        legend_fontsize = base_fontsize - 1
    if title_fontsize is None:
        title_fontsize = base_fontsize + 1

    fig.set_facecolor("white")

    for ax in fig.get_axes():
        ax.title.set_fontsize(title_fontsize)
        ax.xaxis.label.set_fontsize(axes_labelsize)
        ax.yaxis.label.set_fontsize(axes_labelsize)

        ax.tick_params(
            which="both",
            direction="out",
            width=tick_width,
            length=tick_length,
            labelsize=tick_labelsize,
        )

        for spine in ax.spines.values():
            spine.set_linewidth(spine_width)

        for line in ax.get_lines():
            line.set_linewidth(line_width)

        for coll in ax.collections:
            if hasattr(coll, "set_linewidth"):
                try:
                    coll.set_linewidth(line_width)
                except Exception:
                    pass

        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontsize(legend_fontsize)
            leg.get_title().set_fontsize(legend_fontsize)
