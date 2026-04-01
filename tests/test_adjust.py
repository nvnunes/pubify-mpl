import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pubify_mpl.adjust import (
    force_font_family,
    hide_annotations,
    hide_cbar,
    hide_grid,
    hide_labels,
    hide_tick_labels,
    hide_ticks,
    set_axes_labelsize,
    set_legend_fontsize,
    set_line_width,
    set_spine_width,
    set_tick_labelsize,
    set_tick_length,
    set_tick_width,
    set_title_fontsize,
    iter_axes,
    iter_styled_axes,
)


def test_hide_labels_clears_labels_on_main_and_inset_axes():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])
    inset.set_xlabel("Inset X")
    inset.set_ylabel("Inset Y")

    hide_labels(fig)

    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == ""
    assert inset.get_xlabel() == ""
    assert inset.get_ylabel() == ""
    assert fig._supxlabel.get_text() == ""
    assert fig._supylabel.get_text() == ""
    plt.close(fig)


def test_iter_axes_yields_main_and_inset_axes_without_duplicates():
    fig, ax = plt.subplots()
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])

    axes = list(iter_axes(fig))

    assert axes == [ax, inset]
    plt.close(fig)


def test_iter_styled_axes_matches_pubify_styled_axes_traversal():
    fig, ax = plt.subplots()
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])

    axes = list(iter_styled_axes(fig))

    assert axes == [ax, inset]
    plt.close(fig)


def test_hide_annotations_removes_axis_text_on_main_and_inset_axes():
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "main", transform=ax.transAxes)
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])
    inset.text(0.5, 0.5, "inset", transform=inset.transAxes)

    hide_annotations(fig)

    assert not ax.texts
    assert not inset.texts
    plt.close(fig)


def test_hide_ticks_clears_tick_locations():
    fig, ax = plt.subplots()
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])

    hide_ticks(fig)

    assert list(ax.get_xticks()) == []
    assert list(ax.get_yticks()) == []
    plt.close(fig)


def test_hide_tick_labels_preserves_tick_locations():
    fig, ax = plt.subplots()
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])

    before_xticks = list(ax.get_xticks())
    before_yticks = list(ax.get_yticks())
    hide_tick_labels(fig)

    assert list(ax.get_xticks()) == before_xticks
    assert list(ax.get_yticks()) == before_yticks
    assert all(label.get_text() == "" for label in ax.get_xticklabels())
    assert all(label.get_text() == "" for label in ax.get_yticklabels())
    plt.close(fig)


def test_hide_grid_disables_grid_on_target_axes():
    fig, ax = plt.subplots()
    ax.grid(True)
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])
    inset.grid(True)

    hide_grid(fig)

    assert all(not line.get_visible() for line in ax.get_xgridlines() + ax.get_ygridlines())
    assert all(
        not line.get_visible() for line in inset.get_xgridlines() + inset.get_ygridlines()
    )
    plt.close(fig)


def test_hide_cbar_removes_colorbar_axes():
    fig, ax = plt.subplots()
    img = ax.imshow([[1, 2], [3, 4]])
    fig.colorbar(img, ax=ax)

    assert len(fig.axes) == 2
    hide_cbar(ax)
    assert len(fig.axes) == 1
    assert fig.axes[0] is ax
    plt.close(fig)


def test_force_font_family_updates_axis_and_figure_text():
    fig, ax = plt.subplots()
    fig.text(0.5, 0.5, "figure")
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.text(0.5, 0.5, "demo", transform=ax.transAxes)

    force_font_family(fig)

    assert fig.texts[0].get_fontfamily() == ["serif"]
    assert fig._supxlabel.get_fontfamily() == ["serif"]
    assert fig._supylabel.get_fontfamily() == ["serif"]
    assert ax.xaxis.label.get_fontfamily() == ["serif"]
    assert ax.yaxis.label.get_fontfamily() == ["serif"]
    assert ax.texts[0].get_fontfamily() == ["serif"]
    plt.close(fig)


def test_set_axes_labelsize_updates_shared_figure_labels():
    fig, ax = plt.subplots()
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    set_axes_labelsize(fig, 12.0)

    assert fig._supxlabel.get_fontsize() == 12.0
    assert fig._supylabel.get_fontsize() == 12.0
    assert ax.xaxis.label.get_fontsize() == 12.0
    assert ax.yaxis.label.get_fontsize() == 12.0
    plt.close(fig)


def test_style_helpers_update_inset_axes():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Main")
    ax.plot([0, 1], [0, 1])
    ax.legend(["main"])
    inset = ax.inset_axes([0.6, 0.1, 0.3, 0.3])
    inset.set_xlabel("Inset X")
    inset.set_ylabel("Inset Y")
    inset.set_title("Inset")
    inset.plot([0, 1], [1, 0])
    inset.legend(["inset"])

    set_axes_labelsize(fig, 12.0)
    set_tick_labelsize(fig, 11.0)
    set_legend_fontsize(fig, 11.0)
    set_title_fontsize(fig, 13.0)
    set_line_width(fig, 1.2)
    set_spine_width(fig, 0.8)
    set_tick_width(fig, 0.8)
    set_tick_length(fig, 3.0)

    assert inset.xaxis.label.get_fontsize() == ax.xaxis.label.get_fontsize()
    assert inset.get_xticklabels()[0].get_fontsize() == ax.get_xticklabels()[0].get_fontsize()
    assert inset.get_legend().get_texts()[0].get_fontsize() == ax.get_legend().get_texts()[0].get_fontsize()
    assert inset.title.get_fontsize() == ax.title.get_fontsize()
    assert inset.spines["bottom"].get_linewidth() == ax.spines["bottom"].get_linewidth()
    assert inset.lines[0].get_linewidth() == ax.lines[0].get_linewidth()
    plt.close(fig)


def test_adjustments_compose_without_conflict():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.grid(True)
    ax.text(0.5, 0.5, "demo", transform=ax.transAxes)

    hide_labels(fig)
    hide_tick_labels(fig)
    hide_grid(fig)
    hide_annotations(fig)

    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == ""
    assert all(label.get_text() == "" for label in ax.get_xticklabels())
    assert all(label.get_text() == "" for label in ax.get_yticklabels())
    assert all(not line.get_visible() for line in ax.get_xgridlines() + ax.get_ygridlines())
    assert not ax.texts
    plt.close(fig)
