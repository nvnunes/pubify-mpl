# pubify-mpl

`pubify-mpl` provides TeX-free Matplotlib figure preparation and export helpers
for pubify workflows.

It owns Matplotlib-specific behavior:

- cloning figures before export
- isolating a selected `Axes` panel from a larger figure
- optionally preserving attached colorbars
- hiding labels, annotations, ticks, grids, titles, and colorbars
- applying publication-style font, line, spine, and tick settings
- running export-time callbacks
- saving explicitly sized Matplotlib outputs

LaTeX layout, `pubify.sty`, template writing, and named layouts such as
`onewide` now live in `pubify-tex`.

## Quick Start

```python
import matplotlib.pyplot as plt

from pubify_mpl import prepare_figure

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])

with prepare_figure(fig, hide_grid=True, text_usetex=False) as fig_export:
    fig_export.set_size_inches(4, 3, forward=True)
    fig_export.savefig("plot.png", dpi=200)
```

For a one-step save with explicit dimensions:

```python
from pubify_mpl import save_fig

save_fig(fig, "plot.png", width=4, height=3, dpi=200)
```

For LaTeX document-aware export:

```python
from pubify_tex import prepare, save_fig
```

## Public API

Package-root imports include:

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

`pubify-mpl 1.2.0` intentionally removes the old TeX APIs from this package.
Use `pubify-tex` for `prepare`, `DEFAULT_TEMPLATE`, `use_template`, and
LaTeX-layout `save_fig`.
