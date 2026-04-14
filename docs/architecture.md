# Architecture

This document is the source of truth for `pubify-mpl` package shape, public API boundaries, artifact ownership, and export/layout lifecycle.

## Shared Guidance

This repo adopts the shared guidance in:
- `astro-agents/guidance/agent-surface.md`
- `astro-agents/guidance/public-python-projects.md`
- `astro-agents/guidance/python-development.md`

Repo-local package boundaries, public API choices, artifact rules, and lifecycle details in this document remain the source of truth for this repo.

## Package Surface

`pubify_mpl` is the deliberate public Python package boundary.

- Re-export only supported user-facing entrypoints from `pubify_mpl.__init__`.
- Keep docs, examples, and notebook material aligned with package-root imports rather than internal module paths.
- Keep LaTeX-side installation and template-writing behavior behind the public helpers instead of asking callers to reach into internal modules.

## Current Public API

The current package-root API exports:

- `DEFAULT_TEMPLATE`
- `install_pubify_package`
- `prepare`
- `pubify_rc_context`
- `remove_outside_padding`
- `ResolvedStyle`
- `save_fig`
- `use_template`
- `write_tex_template`

## Module Ownership

- `resources.py` owns LaTeX-side file installation and template writing.
- `layout.py` owns template normalization, built-in defaults, and layout geometry calculations.
- `export.py` owns export-time styling, resizing, and save flow.
- `adjust.py` owns lower-level figure adjustment helpers.
- `rc.py` owns the construction-time publication rc context.
- `assets/pubify.sty` is the packaged LaTeX-side asset distributed with the Python package.

## Artifact Boundaries

- `src/pubify_mpl/assets/` contains shipped package assets used at runtime.
- `examples/` and `gallery/` contain public learning material and tracked supporting assets.
- `debug/` contains TeX-side diagnostic fixtures.
- `build/tex/` is the flat staged compile workspace used for TeX-side validation and debugging.
- `examples/quickstart.ipynb` and `gallery/layout-gallery.pdf` are generated artifacts inside the public learning surface and should not be hand-edited.

## Contract Ownership

- `DEFAULT_TEMPLATE` in `layout.py` is the built-in template contract.
- The README quick-start template block and notebook template rendering must remain aligned with `DEFAULT_TEMPLATE`.
- Template normalization and layout geometry rules live in `layout.py`; public docs should describe those supported keys without redefining them elsewhere.
- Flat staged-TeX basename uniqueness across `gallery/` and `debug/` is a repo contract enforced by the builder.

## Export And Layout Lifecycle

The current workflow is:

1. `prepare(...)` installs `pubify.sty` and writes `pubify-template.tex`.
2. `\figprintlayoutspec` measures document geometry and typography from the LaTeX side.
3. Template values are updated from that measurement when the built-in article example is not enough.
4. `save_fig(...)` exports document-sized figure artifacts using named layout geometry or explicit template sizing.
5. LaTeX macros from `pubify.sty` arrange the exported artifacts into final publication layouts.
