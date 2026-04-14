# Testing

This document is the source of truth for verification commands and completion expectations in `pubify-mpl`.

## Shared Validation

Use the shared base testing guidance in `astro-agents/validation/base-testing.md`.

## Environment

Use the repo-local Python environment in `./.conda`.

Install or refresh the editable development environment with:

```bash
./.conda/bin/pip install -e ".[dev]"
```

## Canonical Verification Commands

Run the full test suite with:

```bash
./.conda/bin/python3.12 -m pytest -q -p no:cacheprovider
```

Then run the repo-local hook with:

```bash
sh .githooks/pre-commit
```

## Important Test Surfaces

- `tests/test_readme.py` guards README and canonical-template drift.
- `tests/test_layout.py` guards Python-vs-`pubify.sty` default consistency.
- `tests/test_build_gallery.py` guards staged TeX workspace behavior.
- `tests/test_release.py` guards release-script invariants.

## Completion Expectations

- Substantial changes finish with the full pytest command plus `sh .githooks/pre-commit`.
- Changes to TeX-side behavior require staged compile verification from `build/tex/`, not only Python tests.
- README examples, notebook templates, and layout-default documentation must keep docs and example drift green.
- Prefer verification of externally visible behavior and published usage over tests coupled tightly to internal structure.

## Hook Behavior

The repo-local pre-commit hook:

- regenerates `examples/quickstart.ipynb`
- refreshes `gallery/layout-gallery.pdf`
- runs `./.conda/bin/mkdocs build --strict`
- stages those generated outputs, including `site/`

It may rewrite tracked generated files even when you did not edit them directly.
