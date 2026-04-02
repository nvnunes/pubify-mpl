import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import pytest

from pubify_mpl.adjust import (
    force_font_family,
    hide_annotations,
    hide_cbar,
    hide_grid,
    hide_labels,
    hide_tick_labels,
    hide_ticks,
    match_axis_height,
    match_axis_span,
    match_axis_width,
    remove_outside_padding,
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


def _content_bbox_in_figure_coords(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_position().frozen() for ax in fig.axes if ax.get_visible()]
    for text in (getattr(fig, "_suptitle", None), getattr(fig, "_supxlabel", None), getattr(fig, "_supylabel", None)):
        if text is not None and text.get_visible():
            boxes.append(fig.transFigure.inverted().transform_bbox(text.get_window_extent(renderer)).frozen())
    return Bbox.from_extents(
        min(box.x0 for box in boxes),
        min(box.y0 for box in boxes),
        max(box.x1 for box in boxes),
        max(box.y1 for box in boxes),
    )


def test_remove_outside_padding_tightens_outer_axes_margins_but_preserves_internal_gap():
    fig, axs = plt.subplots(1, 2, figsize=(6, 3))
    fig.subplots_adjust(left=0.25, right=0.70, bottom=0.28, top=0.72, wspace=0.45)
    left_before = axs[0].get_position().frozen()
    right_before = axs[1].get_position().frozen()
    outer_left_before = left_before.x0
    outer_right_before = 1.0 - right_before.x1
    outer_bottom_before = left_before.y0
    outer_top_before = 1.0 - left_before.y1
    gap_ratio_before = (right_before.x0 - left_before.x1) / left_before.width

    remove_outside_padding(fig)

    left_after = axs[0].get_position().frozen()
    right_after = axs[1].get_position().frozen()
    gap_ratio_after = (right_after.x0 - left_after.x1) / left_after.width

    assert left_after.x0 < outer_left_before
    assert 1.0 - right_after.x1 < outer_right_before
    assert left_after.y0 < outer_bottom_before
    assert 1.0 - left_after.y1 < outer_top_before
    assert gap_ratio_after == pytest.approx(gap_ratio_before)
    plt.close(fig)


def test_remove_outside_padding_scales_manual_colorbar_axes_and_shared_labels():
    fig, axs = plt.subplots(1, 2, figsize=(6, 3))
    fig.subplots_adjust(left=0.22, right=0.62, bottom=0.24, top=0.70, wspace=0.35)
    cax = fig.add_axes([0.72, 0.24, 0.04, 0.46])
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")

    content_before = _content_bbox_in_figure_coords(fig)
    left_before = axs[0].get_position().frozen()
    cax_before = cax.get_position().frozen()
    supxlabel_y_before = fig._supxlabel.get_position()[1]
    supylabel_x_before = fig._supylabel.get_position()[0]
    cax_gap_ratio_before = (cax_before.x0 - axs[1].get_position().x1) / left_before.width

    remove_outside_padding(fig)

    content_after = _content_bbox_in_figure_coords(fig)
    left_after = axs[0].get_position().frozen()
    cax_after = cax.get_position().frozen()
    cax_gap_ratio_after = (cax_after.x0 - axs[1].get_position().x1) / left_after.width

    assert content_after.x0 < content_before.x0
    assert content_after.y0 < content_before.y0
    assert content_after.x1 > content_before.x1
    assert content_after.y1 > content_before.y1
    assert cax_after.x1 > cax_before.x1
    assert cax_gap_ratio_after == pytest.approx(cax_gap_ratio_before)
    assert fig._supxlabel.get_position()[1] < supxlabel_y_before
    assert fig._supylabel.get_position()[0] < supylabel_x_before
    assert fig._supxlabel.get_text() == "Shared X"
    assert fig._supylabel.get_text() == "Shared Y"
    plt.close(fig)


def test_match_axis_height_matches_vertical_span_only():
    fig = plt.figure(figsize=(6, 3))
    ref_ax = fig.add_axes([0.12, 0.22, 0.32, 0.48])
    target_ax = fig.add_axes([0.76, 0.10, 0.04, 0.72])
    target_before = target_ax.get_position().frozen()
    ref_pos = ref_ax.get_position().frozen()

    match_axis_height(target_ax, ref_ax)

    target_after = target_ax.get_position().frozen()
    assert target_after.x0 == pytest.approx(target_before.x0)
    assert target_after.width == pytest.approx(target_before.width)
    assert target_after.y0 == pytest.approx(ref_pos.y0)
    assert target_after.height == pytest.approx(ref_pos.height)
    plt.close(fig)


def test_match_axis_width_matches_horizontal_span_only():
    fig = plt.figure(figsize=(6, 3))
    ref_ax = fig.add_axes([0.18, 0.20, 0.52, 0.18])
    target_ax = fig.add_axes([0.05, 0.78, 0.90, 0.05])
    target_before = target_ax.get_position().frozen()
    ref_pos = ref_ax.get_position().frozen()

    match_axis_width(target_ax, ref_ax)

    target_after = target_ax.get_position().frozen()
    assert target_after.y0 == pytest.approx(target_before.y0)
    assert target_after.height == pytest.approx(target_before.height)
    assert target_after.x0 == pytest.approx(ref_pos.x0)
    assert target_after.width == pytest.approx(ref_pos.width)
    plt.close(fig)


def test_match_axis_span_rejects_unknown_axis():
    fig, ax = plt.subplots()
    target_ax = fig.add_axes([0.8, 0.1, 0.05, 0.8])

    with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
        match_axis_span(target_ax, ax, axis="z")

    plt.close(fig)


def test_match_axis_height_can_be_applied_after_remove_outside_padding_for_equal_aspect_axes():
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.6), sharey=True)
    fig.subplots_adjust(left=0.05, right=0.96, bottom=0.09, top=0.98, wspace=0.10)

    for ax in axs:
        ax.imshow([[1, 2], [3, 4]], origin="lower")

    fig.supylabel("Shared Y", x=0.0)
    left_bbox = axs[0].get_position()
    right_bbox = axs[1].get_position()
    cax = fig.add_axes(
        [
            right_bbox.x1 + 0.015,
            min(left_bbox.y0, right_bbox.y0) + 0.01,
            0.02,
            max(left_bbox.y1, right_bbox.y1) - min(left_bbox.y0, right_bbox.y0) - 0.02,
        ]
    )
    fig.colorbar(axs[0].images[0], cax=cax, orientation="vertical")

    remove_outside_padding(fig)
    match_axis_height(cax, axs[1])
    fig.canvas.draw()

    ref_pos = axs[1].get_position().frozen()
    cbar_pos = cax.get_position().frozen()
    assert cbar_pos.y0 == pytest.approx(ref_pos.y0)
    assert cbar_pos.height == pytest.approx(ref_pos.height)
    plt.close(fig)
