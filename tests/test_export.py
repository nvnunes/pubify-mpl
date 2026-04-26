from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pytest

from pubify_mpl import (
    ResolvedStyle,
    auto_rasterize_figure,
    figure_tight_bbox,
    normalized_style,
    prepare_figure,
    pubify_rc_context,
    save_fig,
)
import pubify_mpl.export as export_mod
from pubify_mpl.adjust import hide_labels as public_hide_labels
from pubify_mpl.export import clone_figure_pickle
from pubify_mpl.rc import resolved_pubify_rc


def make_composite_figure(*, with_shared_colorbar: bool = True):
    fig, axs = plt.subplots(1, 2, figsize=(6, 3))
    images = []
    for idx, ax in enumerate(axs):
        image = ax.imshow([[idx + 1, idx + 2], [idx + 3, idx + 4]], origin="lower")
        images.append(image)
        ax.set_xlabel(f"X {idx}")
        ax.set_ylabel(f"Y {idx}")
        ax.set_title(f"Panel {idx}")
        ax.text(0.5, 0.5, f"Note {idx}", transform=ax.transAxes)
        ax.grid(True)

    if with_shared_colorbar:
        cbar = fig.colorbar(images[-1], ax=axs, shrink=0.85)
        cbar.set_label("Scale")
        fig.subplots_adjust(wspace=0.3, right=0.88, top=0.82)
    else:
        fig.subplots_adjust(wspace=0.3, top=0.82)

    fig.suptitle("Composite Figure")
    fig.supxlabel("Shared X")
    fig.supylabel("Shared Y")
    return fig, axs


def test_prepare_figure_preserves_original_by_default():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")

    with prepare_figure(fig, hide_labels=True) as fig_copy:
        assert fig_copy is not fig
        assert fig_copy.axes[0].get_xlabel() == ""

    assert ax.get_xlabel() == "X"
    plt.close(fig)


def test_prepare_figure_can_skip_clone():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")

    with prepare_figure(fig, hide_labels=True, skip_clone=True) as fig_export:
        assert fig_export is fig

    assert ax.get_xlabel() == ""
    plt.close(fig)


def test_prepare_figure_isolates_axes_and_attached_colorbar():
    fig, axs = make_composite_figure()

    with prepare_figure(axs[1], keep_titles=True) as fig_copy:
        assert len(fig_copy.axes) == 2
        assert [ax.get_title() for ax in fig_copy.axes if ax.get_title()] == ["Panel 1"]
        assert any(ax.get_ylabel() == "Scale" for ax in fig_copy.axes)

    plt.close(fig)


def test_prepare_figure_hide_cbar_removes_attached_colorbar():
    fig, axs = make_composite_figure()

    with prepare_figure(axs[1], keep_titles=True, hide_cbar=True) as fig_copy:
        assert len(fig_copy.axes) == 1
        assert fig_copy.axes[0].get_title() == "Panel 1"
        assert not any(ax.get_ylabel() == "Scale" for ax in fig_copy.axes)

    plt.close(fig)


def test_prepare_figure_cleanup_runs_before_callback():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    observed = {}

    def prepare_export(fig_copy):
        observed["xlabel"] = fig_copy.axes[0].get_xlabel()
        observed["ylabel"] = fig_copy.axes[0].get_ylabel()

    with prepare_figure(fig, hide_labels=True, prepare_export=prepare_export):
        pass

    assert observed == {"xlabel": "", "ylabel": ""}
    plt.close(fig)


def test_prepare_figure_callback_can_receive_resolved_style():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    ax.set_xlabel("X")
    ax.set_title("Title")
    observed = {}

    def prepare_export(fig_copy, style):
        copied_ax = fig_copy.axes[0]
        observed["style"] = style
        observed["xlabel_size"] = copied_ax.xaxis.label.get_fontsize()
        observed["tick_size"] = copied_ax.get_xticklabels()[0].get_fontsize()
        observed["legend_size"] = copied_ax.get_legend().get_texts()[0].get_fontsize()
        observed["title_size"] = copied_ax.title.get_fontsize()

    with prepare_figure(
        fig,
        style={
            "base_fontsize_pt": 11.0,
            "axes_labelsize_pt": 14.0,
            "tick_labelsize_pt": 12.5,
            "legend_fontsize_pt": 10.5,
            "title_fontsize_pt": 15.0,
            "line_width_pt": 2.5,
            "axes_line_width_pt": 1.1,
            "tick_length_pt": 4.5,
        },
        keep_titles=True,
        prepare_export=prepare_export,
    ):
        pass

    assert isinstance(observed["style"], ResolvedStyle)
    assert observed["style"].axes_labelsize_pt == 14.0
    assert observed["xlabel_size"] == 14.0
    assert observed["tick_size"] == 12.5
    assert observed["legend_size"] == 10.5
    assert observed["title_size"] == 15.0
    plt.close(fig)


def test_normalized_style_rejects_unknown_options():
    with pytest.raises(ValueError, match="unknown style option"):
        normalized_style({"font_sze": 12.0})


@pytest.mark.parametrize("value", ["12.0", True])
def test_normalized_style_rejects_non_numeric_values(value):
    with pytest.raises(TypeError, match="must be a finite number"):
        normalized_style({"base_fontsize_pt": value})


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_normalized_style_rejects_non_finite_values(value):
    with pytest.raises(ValueError, match="must be a finite number"):
        normalized_style({"base_fontsize_pt": value})


def test_prepare_figure_rejects_incompatible_callback_signature():
    fig, ax = plt.subplots()

    def prepare_export(fig_copy, style, extra):
        raise AssertionError("should not be called")

    with pytest.raises(TypeError, match="prepare_export must accept either one positional argument"):
        with prepare_figure(fig, prepare_export=prepare_export):
            pass

    plt.close(fig)


def test_save_fig_uses_explicit_size_and_default_png_suffix(tmp_path: Path):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])

    save_fig(fig, tmp_path / "line-demo", width=2.0, dpi=100, skip_rasterize=True)

    assert (tmp_path / "line-demo.png").exists()
    plt.close(fig)


def test_save_fig_absolute_missing_parent_raises_nicer_error(tmp_path: Path):
    fig, ax = plt.subplots()
    missing_output = tmp_path / "missing" / "plot.png"

    with pytest.raises(FileNotFoundError, match="Parent directory does not exist"):
        save_fig(fig, missing_output)

    plt.close(fig)


def test_save_fig_routes_hide_labels_through_adjust_helper(tmp_path: Path, monkeypatch):
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    calls = []

    def fake_hide_labels(fig_copy):
        calls.append(fig_copy)
        public_hide_labels(fig_copy)

    monkeypatch.setattr("pubify_mpl.export.adjust.hide_labels", fake_hide_labels)

    save_fig(fig, tmp_path / "hide-labels-demo.png", hide_labels=True, skip_rasterize=True)

    assert len(calls) == 1
    assert calls[0] is not fig
    plt.close(fig)


def test_save_fig_passes_rasterize_thresholds_to_helper(tmp_path: Path, monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    captured = {}

    def fake_auto_rasterize_figure(
        fig_copy,
        *,
        scatter_threshold,
        image_pixel_threshold,
        line_vertex_threshold,
    ):
        captured["fig_copy"] = fig_copy
        captured["scatter_threshold"] = scatter_threshold
        captured["image_pixel_threshold"] = image_pixel_threshold
        captured["line_vertex_threshold"] = line_vertex_threshold
        return []

    monkeypatch.setattr("pubify_mpl.export.auto_rasterize_figure", fake_auto_rasterize_figure)

    save_fig(
        fig,
        tmp_path / "thresholds-demo.pdf",
        rasterize_scatter_threshold=11,
        rasterize_image_pixel_threshold=22,
        rasterize_line_vertex_threshold=33,
    )

    assert captured["scatter_threshold"] == 11
    assert captured["image_pixel_threshold"] == 22
    assert captured["line_vertex_threshold"] == 33
    assert captured["fig_copy"] is not fig
    plt.close(fig)


def test_auto_rasterize_scatter_heavy_plot():
    fig, ax = plt.subplots()
    xs = list(range(1500))
    ys = [x % 17 for x in xs]
    coll = ax.scatter(xs, ys, s=2)

    rasterized = auto_rasterize_figure(fig)

    assert coll.get_rasterized() is True
    assert rasterized
    plt.close(fig)


def test_figure_tight_bbox_returns_drawn_bbox():
    fig, ax = plt.subplots(figsize=(2, 1))
    ax.plot([0, 1], [0, 1])

    bbox = figure_tight_bbox(fig)

    assert bbox.width > 0
    assert bbox.height > 0
    plt.close(fig)


def test_resolved_pubify_rc_is_tex_free_by_default():
    rc = resolved_pubify_rc(style={"base_fontsize_pt": 11.0})

    assert rc["font.size"] == 11.0
    assert rc["text.usetex"] is False
    assert rc["font.family"] == "serif"
    assert rc["font.serif"] == ["Latin Modern Roman", "LMRoman10"]
    assert rc["mathtext.fontset"] == "cm"
    assert "text.latex.preamble" not in rc


def test_resolved_pubify_rc_can_enable_usetex_for_callers():
    rc = resolved_pubify_rc(text_usetex=True)

    assert rc["text.usetex"] is True


def test_pubify_rc_context_applies_and_restores_rcparams():
    original_usetex = plt.matplotlib.rcParams["text.usetex"]
    original_font_family = plt.matplotlib.rcParams["font.family"]

    with pubify_rc_context(style={"base_fontsize_pt": 10.0}):
        assert plt.matplotlib.rcParams["text.usetex"] == original_usetex
        assert plt.matplotlib.rcParams["font.family"] == ["serif"]
        assert plt.matplotlib.rcParams["font.size"] == 10.0

    assert plt.matplotlib.rcParams["text.usetex"] == original_usetex
    assert plt.matplotlib.rcParams["font.family"] == original_font_family


def test_clone_figure_pickle_returns_distinct_figure():
    fig, ax = plt.subplots()

    fig2 = clone_figure_pickle(fig)

    assert fig2 is not fig
    assert isinstance(fig2, Figure)
    plt.close(fig)
    plt.close(fig2)
