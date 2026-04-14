# Contributing

This document is for human contributors working on `pubify-mpl`.

For package usage, examples, and API behavior, see [README.md](README.md).
For canonical local setup and daily commands, see [docs/development.md](docs/development.md).
For canonical verification commands and completion expectations, see [docs/testing.md](docs/testing.md).
For release history, see [CHANGELOG.md](CHANGELOG.md).

## Development Setup

[`docs/development.md`](docs/development.md) owns the canonical local setup and daily command surface.

`pubify-mpl` targets Python 3.10+ and expects a working LaTeX installation for export and TeX-side checks.

Install the project with development dependencies:

```bash
./.conda/bin/pip install -e ".[dev]"
```

If you are not using the repo-local `.conda` environment, install the same extras into your own environment.

## Local Checks

[`docs/testing.md`](docs/testing.md) owns the canonical verification path.

The normal full verification sequence for nontrivial changes is:

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
sh .githooks/pre-commit
```

That hook is not just linting. It may rewrite tracked generated outputs even if you did not edit them directly. See [docs/development.md](docs/development.md) for the generated-artifact list and local workflow.

## TeX-Side Changes

For the canonical staged TeX debug workflow, follow [docs/development.md](docs/development.md).

TeX development should be validated from the staged workspace in `build/tex/`, not only through Python tests.

A typical flow is:

```bash
./.conda/bin/python3.12 scripts/build_tex_assets.py debug/debug-subcaptions.tex
cd build/tex
latexmk -g -pdf -interaction=nonstopmode debug-subcaptions.tex
```

This keeps the staged `.tex`, `.aux`, `.fls`, `.fdb_latexmk`, and `.log` files together so TeX warnings and `pubify` debug output are easy to inspect.

## Release Process

Releases are standardized around the checked-in script:

```bash
./.conda/bin/python3.12 scripts/release.py
```

This is the canonical release path. It performs the full release flow and aborts immediately if any requirement is not met.

### Branch Flow

The intended branch workflow is:

1. develop new work on `develop`
2. fast-forward `main` to the intended release state
3. run the release from `main`
4. fast-forward `develop` back to the released `main` state

The release script itself must run from `main`, but the normal development branch is `develop`.

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
Because the pre-commit hook regenerates tracked outputs, the release script restores the known generated hook outputs from `HEAD` before its final clean-worktree check. Any remaining changes after that are treated as a real release blocker.

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
