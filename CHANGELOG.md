# Changelog

## 1.0.4

- Added `skip_clone` to `save_fig(...)`.
- Added `pubify_rc_context(...)` for figure construction that depends on publication-style Matplotlib rc defaults.
- Renamed `prepare_export(...)` to `prepare_copy(...)`.
- Simplified the LaTeX syntax for small layouts.
- Fixed wrapped `\fig{...}` panels in direct layouts so subcaptions and labels compile correctly.

## 1.0.3

- Tightened export styling policy around template-driven text and stroke defaults.
- Simplified the figure adjustment surface and improved export-time cleanup behavior.

## 1.0.2

- Renamed the gallery example source to `layout-gallery-examples.tex`.
- Updated the examples and documentation to point at the renamed gallery source.

## 1.0.1

- Fixed README links so they render correctly on PyPI.
- Added GitHub Pages deployment for the documentation site.

## 1.0.0

- Initial public release of `pubify-mpl`.
