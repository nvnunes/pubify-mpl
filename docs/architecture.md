# Architecture

`pubify-mpl` owns TeX-free Matplotlib figure preparation and export behavior.

## Package Surface

Supported package-root imports:

- `DEFAULT_STYLE`
- `ResolvedStyle`
- `auto_rasterize_figure`
- `figure_renderer`
- `figure_tight_bbox`
- `normalized_style`
- `prepare_figure`
- `pubify_rc_context`
- `remove_outside_padding`
- `save_fig`

## Module Ownership

- `adjust.py` owns lower-level figure adjustment helpers.
- `style.py` owns Matplotlib export-style defaults and normalization.
- `rc.py` owns construction-time and export-time Matplotlib rc settings.
- `export.py` owns cloning, axes isolation, cleanup, callback invocation,
  rasterization heuristics, and explicit-size saving.

Font replacement is a generic capability, not a package-wide typography
policy. `prepare_figure(...)`, `save_fig(...)`, and `pubify_rc_context(...)`
accept an explicit `font_family`; when omitted, `pubify-mpl` does not force a
target font or install TeX-like serif defaults. Target packages own those
profiles.

## Dependency Boundary

`pubify-mpl` must not depend on `pubify-tex` or ship TeX assets. LaTeX layout,
template writing, and document-aware named-layout export belong in
`pubify-tex`, which may depend on `pubify-mpl`.
