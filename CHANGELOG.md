# Changelog

## 1.2.0

- Split LaTeX layout, template, and TeX asset support into `pubify-tex`.
- Removed TeX-facing package-root APIs from `pubify-mpl`.
- Added TeX-free Matplotlib figure preparation through `prepare_figure(...)`.
- Changed `save_fig(...)` to explicit-size Matplotlib export without named LaTeX layouts.

## 1.1.0

- Changed `save_fig(fig, ...)` to export the full composed Matplotlib figure, while `save_fig(ax, ...)` continues to export only the selected axes panel.
- Added support for exporting subplot compositions, including shared colorbars, as a single saved artifact for placement with simple LaTeX layouts such as `"one"` and `"onewide"`.
- Changed wide layouts (`"onewide"`, `"twowide"`, `"threewide"`) to use full layout width by default.
- Added `force_height=...` as the height cap control for exports.

## 1.0.4

- Added `skip_clone` to `save_fig(...)`.
- Added `pubify_rc_context(...)` for figure construction that depends on publication-style Matplotlib rc defaults.
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
