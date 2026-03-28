from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pubify_mpl import save_fig, use_template, write_tex_template
from pubify_mpl.adjust import (
    force_font_family,
    hide_labels as public_hide_labels,
    set_axes_labelsize,
    set_legend_fontsize,
    set_line_width,
    set_spine_width,
    set_tick_labelsize,
    set_tick_length,
    set_tick_width,
    set_title_fontsize,
)
from pubify_mpl.export import _auto_rasterize_figure, clone_figure_pickle

ARTICLE_TEMPLATE = {
    "textwidth_in": 5.39643,
    "textheight_in": 7.58960,
}

AO4ELT_TEMPLATE = {
    "textwidth_in": 6.75,
    "textheight_in": 9.70,
}


def test_save_basic_line_plot(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 0])
    output = save_fig(
        fig,
        "onewide",
        tmp_path / "line-demo.pdf",
        template=ARTICLE_TEMPLATE,
        skip_rasterize=True,
    )
    assert output is None
    assert (tmp_path / "line-demo.pdf").exists()
    plt.close(fig)


def test_save_accepts_force_width_with_layout(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(
        fig,
        "onewide",
        tmp_path / "force-width-demo.pdf",
        template=ARTICLE_TEMPLATE,
        caption_lines=0,
        force_width=2.3,
        skip_rasterize=True,
    )
    assert output is None
    assert (tmp_path / "force-width-demo.pdf").exists()
    plt.close(fig)


def test_save_force_width_rejects_too_wide_request(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        save_fig(
            fig,
            "onewide",
            tmp_path / "too-wide.pdf",
            template=ARTICLE_TEMPLATE,
            force_width=10.0,
            skip_rasterize=True,
        )
    except ValueError as exc:
        assert "exceeds the available width" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    plt.close(fig)


def test_save_accepts_cwd_relative_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(fig, "onewide", "cwd-demo", template=ARTICLE_TEMPLATE, skip_rasterize=True)
    assert output is None
    assert Path("cwd-demo.pdf").exists()
    plt.close(fig)


def test_save_creates_relative_parent_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    output = save_fig(
        fig,
        "onewide",
        "tex/figures/plot.pdf",
        template=ARTICLE_TEMPLATE,
        skip_rasterize=True,
    )
    assert output is None
    assert Path("tex/figures/plot.pdf").exists()
    plt.close(fig)


def test_save_absolute_missing_parent_raises_nicer_error(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    missing_output = tmp_path / "missing" / "plot.pdf"
    try:
        save_fig(fig, "onewide", missing_output, template=ARTICLE_TEMPLATE, skip_rasterize=True)
    except FileNotFoundError as exc:
        assert "Parent directory does not exist" in str(exc)
        assert str(missing_output) in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
    plt.close(fig)


def test_save_uses_context_default_template(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    template = {"textwidth_in": 6.5, "textheight_in": 8.5}
    with use_template(template):
        output = save_fig(fig, "onewide", tmp_path / "context-demo.pdf", skip_rasterize=True)
    assert output is None
    assert (tmp_path / "context-demo.pdf").exists()
    plt.close(fig)


def test_save_template_argument_overrides_context_default(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with use_template({"textwidth_in": 6.5, "textheight_in": 8.5}):
        output = save_fig(
            fig,
            "onewide",
            tmp_path / "override-demo.pdf",
            template=AO4ELT_TEMPLATE,
            skip_rasterize=True,
        )
    assert output is None
    assert (tmp_path / "override-demo.pdf").exists()
    plt.close(fig)


def test_save_rejects_non_string_layout(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        save_fig(fig, 3.25, tmp_path / "bad-layout.pdf", template=ARTICLE_TEMPLATE, skip_rasterize=True)
    except TypeError as exc:
        assert "layout must be a named layout string" in str(exc)
    else:
        raise AssertionError("Expected TypeError")
    plt.close(fig)


def test_write_tex_template_explicitly(tmp_path):
    tex_template = write_tex_template(tmp_path / "pubify-template.tex", template=ARTICLE_TEMPLATE)
    assert tex_template.exists()


def test_auto_rasterize_scatter_heavy_plot():
    fig, ax = plt.subplots()
    xs = list(range(1500))
    ys = [x % 17 for x in xs]
    coll = ax.scatter(xs, ys, s=2)
    rasterized = _auto_rasterize_figure(fig)
    assert coll.get_rasterized() is True
    assert rasterized
    plt.close(fig)


def test_auto_rasterize_uses_custom_thresholds():
    fig, ax = plt.subplots()
    xs = list(range(20))
    ys = [x % 5 for x in xs]
    coll = ax.scatter(xs, ys, s=2)
    rasterized = _auto_rasterize_figure(fig, scatter_threshold=10)
    assert coll.get_rasterized() is True
    assert rasterized
    plt.close(fig)


def test_save_passes_rasterize_thresholds_to_helper(tmp_path, monkeypatch):
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

    monkeypatch.setattr("pubify_mpl.export._auto_rasterize_figure", fake_auto_rasterize_figure)

    save_fig(
        fig,
        "onewide",
        tmp_path / "thresholds-demo.pdf",
        template=ARTICLE_TEMPLATE,
        rasterize_scatter_threshold=11,
        rasterize_image_pixel_threshold=22,
        rasterize_line_vertex_threshold=33,
    )

    assert captured["scatter_threshold"] == 11
    assert captured["image_pixel_threshold"] == 22
    assert captured["line_vertex_threshold"] == 33
    assert captured["fig_copy"] is not fig
    plt.close(fig)


def test_prepare_copy_hook_mutates_only_export_copy(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    original_linewidth = ax.lines[0].get_linewidth()
    observed = {}

    def prepare_copy(fig_copy):
        observed["called"] = True
        observed["same_object"] = fig_copy is fig
        fig_copy.axes[0].lines[0].set_linewidth(7.0)

    output = save_fig(
        fig,
        "onewide",
        tmp_path / "edit-copy-demo.pdf",
        template=ARTICLE_TEMPLATE,
        prepare_copy=prepare_copy,
        skip_rasterize=True,
    )

    assert output is None
    assert observed["called"] is True
    assert observed["same_object"] is False
    assert fig.axes[0].lines[0].get_linewidth() == original_linewidth
    assert (tmp_path / "edit-copy-demo.pdf").exists()
    plt.close(fig)


def test_hide_annotations_removes_axis_text(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.text(0.5, 0.5, "demo", transform=ax.transAxes)
    output = save_fig(fig, "onewide", tmp_path / "annot-demo.pdf", template=ARTICLE_TEMPLATE, hide_annotations=True, skip_rasterize=True)
    assert output is None
    assert (tmp_path / "annot-demo.pdf").exists()
    plt.close(fig)


def test_save_routes_hide_labels_through_adjust_helper(tmp_path, monkeypatch):
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    calls = []

    def fake_hide_labels(fig_copy):
        calls.append(fig_copy)
        public_hide_labels(fig_copy)

    monkeypatch.setattr("pubify_mpl.export.adjust.hide_labels", fake_hide_labels)

    save_fig(
        fig,
        "onewide",
        tmp_path / "hide-labels-demo.pdf",
        template=ARTICLE_TEMPLATE,
        hide_labels=True,
        skip_rasterize=True,
    )

    assert len(calls) == 1
    assert calls[0] is not fig
    plt.close(fig)


def test_prepare_copy_runs_after_standard_cleanup(tmp_path):
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    observed = {}

    def prepare_copy(fig_copy):
        observed["xlabel"] = fig_copy.axes[0].get_xlabel()
        observed["ylabel"] = fig_copy.axes[0].get_ylabel()

    save_fig(
        fig,
        "onewide",
        tmp_path / "prepare-copy-cleanup-order.pdf",
        template=ARTICLE_TEMPLATE,
        hide_labels=True,
        prepare_copy=prepare_copy,
        skip_rasterize=True,
    )

    assert observed["xlabel"] == ""
    assert observed["ylabel"] == ""
    plt.close(fig)


def test_save_hide_cbar_removes_single_panel_colorbar(tmp_path):
    fig, ax = plt.subplots()
    img = ax.imshow([[1, 2], [3, 4]])
    fig.colorbar(img, ax=ax)

    save_fig(
        fig,
        "onewide",
        tmp_path / "hide-cbar-demo.pdf",
        template=ARTICLE_TEMPLATE,
        hide_cbar=True,
        skip_rasterize=True,
    )

    assert (tmp_path / "hide-cbar-demo.pdf").exists()
    plt.close(fig)


def test_force_font_family_updates_axis_text_annotations():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.plot([0, 1], [0, 1], label="demo")
    ax.legend()
    annotation = ax.text(0.5, 0.5, "demo", transform=ax.transAxes)
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)

    copied_ax = fig2.axes[0]
    assert copied_ax.texts[0].get_fontfamily() == ["serif"]
    assert copied_ax.xaxis.label.get_fontfamily() == ["serif"]
    assert copied_ax.yaxis.label.get_fontfamily() == ["serif"]
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_ax.get_xticklabels())
    assert all(text.get_fontfamily() == ["serif"] for text in copied_ax.get_legend().get_texts())

    plt.close(fig)
    plt.close(fig2)


def test_force_font_family_updates_figure_text():
    fig, ax = plt.subplots()
    fig.text(0.5, 0.5, "figure note")
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)

    assert fig2.texts[0].get_fontfamily() == ["serif"]

    plt.close(fig)
    plt.close(fig2)


def test_inset_axes_receive_publication_font_and_style():
    fig, ax = plt.subplots()
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    inset = ax.inset_axes([0.6, 0.1, 0.35, 0.35])
    inset.set_xticks([0.0, 0.5, 1.0])
    inset.set_yticks([0.0, 0.5, 1.0])
    fig2 = clone_figure_pickle(fig)

    force_font_family(fig2)
    set_axes_labelsize(fig2, 12.0)
    set_tick_labelsize(fig2, 11.0)
    set_legend_fontsize(fig2, 11.0)
    set_title_fontsize(fig2, 13.0)
    set_line_width(fig2, 1.2)
    set_spine_width(fig2, 0.8)
    set_tick_width(fig2, 0.8)
    set_tick_length(fig2, 3.0)

    copied_main = fig2.axes[0]
    copied_inset = copied_main.child_axes[0]
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_inset.get_xticklabels())
    assert all(tick.get_fontfamily() == ["serif"] for tick in copied_inset.get_yticklabels())
    assert copied_inset.get_xticklabels()[0].get_fontsize() == copied_main.get_xticklabels()[0].get_fontsize()
    assert copied_inset.get_yticklabels()[0].get_fontsize() == copied_main.get_yticklabels()[0].get_fontsize()
    assert copied_inset.spines["bottom"].get_linewidth() == copied_main.spines["bottom"].get_linewidth()

    plt.close(fig)
    plt.close(fig2)
