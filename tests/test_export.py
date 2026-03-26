from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pubify_mpl import save_fig, use_template, write_tex_template
from pubify_mpl.export import _auto_rasterize_figure

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
