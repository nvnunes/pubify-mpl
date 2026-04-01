# Contributing

This document is for human contributors working on `pubify-mpl`.

For package usage, examples, and API behavior, see `README.md`.
For release history, see `CHANGELOG.md`.

## Development Setup

`pubify-mpl` targets Python 3.10+ and expects a working LaTeX installation for export and TeX-side checks.

Install the project with development dependencies:

```bash
./.conda/bin/pip install -e ".[dev]"
```

If you are not using the repo-local `.conda` environment, install the same extras into your own environment.

## Local Checks

The canonical full test command is:

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
```

The repo also has a local pre-commit hook:

```bash
sh .githooks/pre-commit
```

That hook is not just linting. It regenerates tracked artifacts:

- `examples/quickstart.ipynb`
- `gallery/layout-gallery.pdf`
- `site/`

It may rewrite those files even if you did not edit them directly.

A practical verification sequence after nontrivial changes is:

1. Run the full pytest command.
2. Run `sh .githooks/pre-commit`.

## TeX-Side Changes

TeX development should be validated from the staged workspace in `build/tex/`, not only through Python tests.

A typical flow is:

```bash
./.conda/bin/python3.12 scripts/build_tex_assets.py debug/debug-subcaptions.tex
cd build/tex
latexmk -g -pdf -interaction=nonstopmode debug-subcaptions.tex
```

This keeps the staged `.tex`, `.aux`, `.fls`, `.fdb_latexmk`, and `.log` files together so TeX warnings and `pubify` debug output are easy to inspect.

## Generated Artifacts

These tracked files are generated and should not be edited by hand:

- `examples/quickstart.ipynb`
- `gallery/layout-gallery.pdf`

Refresh them with:

- `scripts/update_quickstart_notebook.py`
- `scripts/update_layout_gallery.py`

## Release Process

Releases are standardized around the checked-in script:

```bash
./.conda/bin/python3.12 scripts/release.py
```

This is the canonical release path. It performs the full release flow and aborts immediately if any requirement is not met.

### Before Running the Release Script

Make the release edits manually first:

1. Update `pyproject.toml` with the new version.
2. Add the matching version entry to `CHANGELOG.md`.

The changelog format is:

```md
## 1.0.4

- User-visible change one.
- User-visible change two.
```

Each release entry must:

- match the version in `pyproject.toml`
- use a `## <version>` heading
- contain at least one non-empty bullet

### What the Release Script Does

The script requires:

- you are on `main`
- the worktree is clean before starting
- `CHANGELOG.md` contains a non-empty entry for the current version
- the release tag does not already exist
- a Twine config file is available

It then runs, in order:

1. full pytest
2. `sh .githooks/pre-commit`
3. a clean-worktree check again
4. a fresh sdist/wheel build
5. `twine check`
6. `git tag v<version>`
7. `git push origin main`
8. `git push origin v<version>`
9. `twine upload`

The script builds fresh artifacts for that run and uploads only those artifacts.

### PyPI Credentials

By default, the release script uses:

```text
~/.pypirc-pubify-mpl
```

You can override that path with:

```bash
./.conda/bin/python3.12 scripts/release.py --config-file /path/to/config
```

## Notes

`AGENTS.md` is reserved for repo-specific notes that help coding agents and new threads avoid mistakes. It should stay focused on non-obvious conventions, not general contributor workflow.
