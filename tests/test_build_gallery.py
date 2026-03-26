import importlib.util
from pathlib import Path


def _load_build_assets_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_tex_assets.py"
    spec = importlib.util.spec_from_file_location("build_tex_assets", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_assets_writes_complete_workspace(tmp_path, monkeypatch):
    module = _load_build_assets_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "GALLERY_SOURCE_DIR", tmp_path / "gallery")
    monkeypatch.setattr(module, "DEBUG_SOURCE_DIR", tmp_path / "debug")
    monkeypatch.setattr(module, "SOURCE_ROOTS", (module.GALLERY_SOURCE_DIR, module.DEBUG_SOURCE_DIR))
    monkeypatch.setattr(module, "BUILD_DIR", tmp_path / "build" / "tex")
    module.GALLERY_SOURCE_DIR.mkdir()
    module.DEBUG_SOURCE_DIR.mkdir()
    (module.GALLERY_SOURCE_DIR / "layout-gallery.tex").write_text("\\documentclass{article}\\begin{document}Hi\\end{document}\n")

    module.main()

    assert (module.BUILD_DIR / "layout-gallery.tex").exists()
    assert (module.BUILD_DIR / "pubify.sty").exists()
    assert (module.BUILD_DIR / "pubify-template.tex").exists()
    assert (module.BUILD_DIR / "fig-example-one.pdf").exists()
    assert (module.BUILD_DIR / "fig-example-twenty.pdf").exists()


def test_build_assets_accepts_requested_tex_file(tmp_path, monkeypatch):
    module = _load_build_assets_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "GALLERY_SOURCE_DIR", tmp_path / "gallery")
    monkeypatch.setattr(module, "DEBUG_SOURCE_DIR", tmp_path / "debug")
    monkeypatch.setattr(module, "SOURCE_ROOTS", (module.GALLERY_SOURCE_DIR, module.DEBUG_SOURCE_DIR))
    monkeypatch.setattr(module, "BUILD_DIR", tmp_path / "build" / "tex")
    module.GALLERY_SOURCE_DIR.mkdir()
    module.DEBUG_SOURCE_DIR.mkdir()
    (module.DEBUG_SOURCE_DIR / "debug-subcaptions.tex").write_text("\\documentclass{article}\\begin{document}Hi\\end{document}\n")

    module.main(["debug/debug-subcaptions.tex"])

    assert (module.BUILD_DIR / "debug-subcaptions.tex").exists()
    assert (module.BUILD_DIR / "pubify.sty").exists()
    assert (module.BUILD_DIR / "fig-example-one.pdf").exists()
    assert not (module.BUILD_DIR / "layout-gallery.tex").exists()


def test_build_assets_copies_local_input_dependencies(tmp_path, monkeypatch):
    gallery_dir = tmp_path / "gallery"
    debug_dir = tmp_path / "debug"
    gallery_dir.mkdir(parents=True)
    debug_dir.mkdir(parents=True)
    (debug_dir / "main.tex").write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "\\input{../gallery/_body}\n"
        "\\end{document}\n"
    )
    (gallery_dir / "_body.tex").write_text("Body text.\n")

    module = _load_build_assets_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "GALLERY_SOURCE_DIR", gallery_dir)
    monkeypatch.setattr(module, "DEBUG_SOURCE_DIR", debug_dir)
    monkeypatch.setattr(module, "SOURCE_ROOTS", (module.GALLERY_SOURCE_DIR, module.DEBUG_SOURCE_DIR))
    monkeypatch.setattr(module, "BUILD_DIR", tmp_path / "build" / "tex")

    module.main(["debug/main.tex"])

    assert (module.BUILD_DIR / "main.tex").exists()
    assert (module.BUILD_DIR / "_body.tex").exists()
