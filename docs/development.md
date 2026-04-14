# Development

This document is the source of truth for local setup, generated artifacts, TeX debug workflow, and daily development commands in `pubify-mpl`.

## Local Environment

The canonical local environment is the repo-local `./.conda`.

Install or refresh the editable development environment with:

```bash
./.conda/bin/pip install -e ".[dev]"
```

If you use a different environment, keep the installed dependency set aligned with the same `.[dev]` extras.

## Daily Commands

Run the full test suite with:

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
```

Build the docs site strictly with:

```bash
./.conda/bin/mkdocs build --strict
```

Refresh the tracked notebook with:

```bash
./.conda/bin/python3.12 scripts/update_quickstart_notebook.py
```

Refresh the tracked layout gallery PDF with:

```bash
./.conda/bin/python3.12 scripts/update_layout_gallery.py
```

## Generated Artifacts

These tracked outputs are generated and may be rewritten by `sh .githooks/pre-commit`:

- `examples/quickstart.ipynb`
- `gallery/layout-gallery.pdf`
- `site/`

Do not hand-edit those generated outputs.

## TeX Debug Workflow

Validate TeX-side changes from the staged workspace in `build/tex/`, not only through Python tests.

A typical stage-first flow is:

```bash
./.conda/bin/python3.12 scripts/build_tex_assets.py debug/debug-subcaptions.tex
cd build/tex
latexmk -g -pdf -interaction=nonstopmode debug-subcaptions.tex
```

This keeps the staged `.tex`, `.aux`, `.fls`, `.fdb_latexmk`, and `.log` files together so TeX warnings and `pubify` debug output are easy to inspect.

## Release Workflow

The canonical release entrypoint is:

```bash
./.conda/bin/python3.12 scripts/release.py
```

Release execution must run from `main`.

The release script validates the changelog and worktree state, runs the full pytest command, runs `sh .githooks/pre-commit`, builds fresh artifacts, tags, pushes, and uploads.

Override the default Twine config path when needed with:

```bash
./.conda/bin/python3.12 scripts/release.py --config-file /path/to/config
```

## Contributor Notes

`CONTRIBUTING.md` remains the human-facing contributor and release guide. This document owns the canonical local commands, generated-artifact workflow, and TeX debug path.
