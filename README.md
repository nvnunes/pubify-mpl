# pubify-mpl

`pubify-mpl` is a small Python tool for exporting Matplotlib figures at sizes that match your LaTeX document, so the figures drop cleanly into papers, theses, and proceedings without trial-and-error resizing.

It combines two parts of a publication workflow:

- Python helpers for exporting Matplotlib figures using document-aware sizes
- a LaTeX package, `pubify.sty`, for arranging exported figures into common panel layouts

This package is meant for researchers who already use Matplotlib and LaTeX and want a cleaner path from Python plots to publication-ready figures. It is not a replacement for Matplotlib. It sits at the export and layout stage.

See [CHANGELOG.md](https://github.com/nvnunes/pubify-mpl/blob/main/CHANGELOG.md) for release history and user-visible changes, and [CONTRIBUTING.md](https://github.com/nvnunes/pubify-mpl/blob/main/CONTRIBUTING.md) for contributor and release workflow guidance.

## Documentation

- [Docs home](https://nvnunes.github.io/pubify-mpl/)
- [Architecture and package boundaries](https://nvnunes.github.io/pubify-mpl/architecture/)
- [Development workflow](https://nvnunes.github.io/pubify-mpl/development/)
- [Testing and verification](https://nvnunes.github.io/pubify-mpl/testing/)
- [API reference](https://nvnunes.github.io/pubify-mpl/api/)

`README.md` remains the public quick-start and usage guide. Durable repo-local owners for package structure, contributor workflow, and verification expectations live in the docs above.

## Requirements

- Python 3.10+
- Matplotlib and NumPy
- a working LaTeX installation

`save_fig()` uses `text.usetex=True`, so LaTeX must be available when you export figures from Python.

On macOS, a common choice is [MacTeX](https://www.tug.org/mactex/). If you want a smaller install, [BasicTeX](https://www.tug.org/mactex/morepackages.html) can also work, but you may need to add missing packages yourself.

LaTeX package requirements:

- `pubify.sty` depends on `graphicx`, `subcaption`, and `etoolbox`
- the staged gallery/debug workspace also uses `lipsum`, so minimal TeX installs may need that package separately

## How It Works

Technically, `save_fig(...)` does not modify your original Matplotlib figure in place. Instead it:

1. makes a copy of the figure
2. applies publication styling and any requested cleanup only to that copy
3. resizes the copy to match the requested width or named LaTeX layout
4. saves the copy to the requested output format

That means your original interactive figure stays unchanged in Python. This is important if you want to keep using the same figure object in a notebook or script after export. If the output filename has no suffix, `save_fig(...)` defaults to PDF.

On the export side, `save_fig(...)` can:

- export a full Matplotlib figure composition when you pass a `Figure`
- export a single panel when you pass an `Axes`
- remove titles, labels, annotations, grids, or colorbars from the exported copy
- scales your copied figure to match the named layout
- use LaTeX text rendering during export so fonts and math match the document more closely

## Quick Start

Install the package:

```bash
pip install pubify-mpl
```

Export a figure into a LaTeX project:

```python
import matplotlib.pyplot as plt

from pubify_mpl import prepare, save_fig

paper_dir = "~/my-paper"
figures_dir = "~/my-paper/figures"

template = {
    # Values for the default LaTeX article class example.
    "textwidth_in": 5.39643,
    "textheight_in": 7.58960,
    "base_fontsize_pt": 12.0,
    "caption_lineheight_pt": 13.6,
    "subcaption_lineheight_pt": 13.6,
}

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
ax.set_xlabel("x")
ax.set_ylabel("y")

prepare(paper_dir, template=template)
save_fig(fig, "onewide", f"{figures_dir}/plot.pdf", template=template)
```

Then in LaTeX:

```tex
\usepackage{pubify}
```

Note that `prepare(...)` generates `pubify-template.tex`, and it contains specs that `pubify.sty` uses on the LaTeX side. Keep `pubify-template.tex` next to `pubify.sty`. Your paper directory will usually look like:

```text
main.tex
pubify.sty
pubify-template.tex
figures/plot.pdf
```

If you do not already know your document dimensions and typography settings, first run `prepare(...)` so `pubify.sty` is available in the LaTeX project. Then add `\figprintlayoutspec` to the LaTeX document once and compile it. That prints the current `textwidth`, `textheight`, base font size, and caption/subcaption line heights, which you can then copy into the Python `template` dictionary.

`pubify-mpl` is fully compatible with Overleaf. If your LaTeX project is synced locally, the same folder layout works directly. If you do not have local sync set up, copy `pubify.sty`, `pubify-template.tex`, and the exported figure PDFs into the Overleaf project manually.

## Examples

- [examples/quickstart.ipynb](https://github.com/nvnunes/pubify-mpl/blob/main/examples/quickstart.ipynb): notebook version of the minimal quick-start example, writing into the tracked example project at [examples/tex/main.tex](https://github.com/nvnunes/pubify-mpl/blob/main/examples/tex/main.tex)
- [gallery/layout-gallery-examples.tex](https://github.com/nvnunes/pubify-mpl/blob/main/gallery/layout-gallery-examples.tex): sample LaTeX source showing the supported panel layouts and macro usage

## Layouts

See layout options in [gallery/layout-gallery.pdf](https://github.com/nvnunes/pubify-mpl/blob/main/gallery/layout-gallery.pdf) including:

- `"one"`: one large panel
- `"onewide"`: one full-width panel
- `"two"`: two stacked panels
- `"twowide"`: two side-by-side panels across the full text width
- `"three"`: three stacked panels
- `"threewide"`: three side-by-side panels across the full text width
- `"four"`: 2x2 grid
- `"six"`: 2x3 grid
- `"sixwide"`: 3x2 grid
- `"nine"`: 3x3 grid
- `"twelve"`: 3x4 grid
- `"twelvewide"`: 4x3 grid
- `"fifteen"`: 3x5 grid
- `"sixteen"`: 4x4 grid
- `"twenty"`: 4x5 grid


## Typical Workflow

1. Run `prepare(...)` to install `pubify.sty` and write an initial `pubify-template.tex`.
2. Measure your real LaTeX document using `\figprintlayoutspec`.
3. Update the template with the values printed by `\figprintlayoutspec`.
4. Export your figures with `save_fig(...)`.
5. Include them in LaTeX with `\figfloat`, `\fig`, and the layout macros.

## Advanced Python Usage

This is an alternative way to use `pubify-mpl` when you export many figures for the same document or keep several document templates in Python.

Define a common set of templates:

```python
PUBIFY_TEMPLATES = {
    "article": {
        "textwidth_in": 5.39643,
        "textheight_in": 7.58960,
        "base_fontsize_pt": 12.0,
        "caption_lineheight_pt": 13.6,
        "subcaption_lineheight_pt": 13.6,
    },
    "thesis": {
        "textwidth_in": 6.5,
        "textheight_in": 8.5,
        "base_fontsize_pt": 11.0,
        "caption_lineheight_pt": 13.0,
        "subcaption_lineheight_pt": 13.0,
    },
}
```

Then when you export many figures for the same document, `use_template(...)` lets you set a default template inside a `with` block:

```python
import matplotlib.pyplot as plt
from pubify_mpl import prepare, save_fig, use_template

paper_dir = "~/mythesis"
figures_dir = "~/mythesis/figures"

# do this once
prepare(paper_dir, template=PUBIFY_TEMPLATES["thesis"])

# create your figures

with use_template(PUBIFY_TEMPLATES["thesis"]):
    save_fig(fig1, "one", f"{figures_dir}/plot-1.pdf")
    save_fig(fig2, "twowide", f"{figures_dir}/plot-2.pdf")
```

`save_fig(...)` generally follows Matplotlib intent directly:

- pass a `Figure` to export the full composed figure as one artifact
- pass an `Axes` to export only that selected panel

This is useful when you need a custom Matplotlib composition that pubify's LaTeX layouts do not model directly, such as two subplots with one shared colorbar. In those cases, build the composition in Matplotlib and export the whole figure for a simple LaTeX slot such as `"one"` or `"onewide"`:

```python
fig, axs = plt.subplots(1, 2, figsize=(6, 3))

im = axs[0].imshow(data_left)
axs[1].imshow(data_right, vmin=im.norm.vmin, vmax=im.norm.vmax, cmap=im.cmap)
fig.colorbar(im, ax=axs, shrink=0.85)

save_fig(fig, "onewide", f"{figures_dir}/comparison.pdf", template=PUBIFY_TEMPLATES["thesis"])
```

This works well for many ordinary composed Matplotlib figures, including cases like shared colorbars, but arbitrary complex composite figures are not yet guaranteed to export perfectly.

For figure construction that needs publication styling at creation time, `pubify_rc_context(...)` exposes the construction-time publication rc subset used for font and text defaults:

```python
from pubify_mpl import pubify_rc_context

with pubify_rc_context(PUBIFY_TEMPLATES["thesis"]):
    fig = build_custom_plot()
```

The intended styling flow is:

- build under `pubify_rc_context(...)` when artist creation depends on Matplotlib rc defaults
- let `save_fig(...)` run its full export-time TeX setup plus normal generic cleanup and normalization afterward
- use `prepare_export(...)` only for figure-specific artists that pubify still cannot reach generically

Lower-level figure adjustment helpers and `prepare_export(...)` are available in the Python API reference for those final figure-specific cases.

For figure-specific styling that pubify cannot discover generically, `prepare_export(...)` may accept a second `style` argument:

```python
def prepare_export(fig_export, style):
    for text in iter_custom_tick_labels(fig_export.axes[0]):
        text.set_fontfamily(style.font_family)
        text.set_fontsize(style.tick_labelsize_pt)
```

One-argument callbacks still work. The optional `style` payload carries the resolved publication styling values for text, lines, ticks, and spines.

## Template Keys

The template dictionary tells `pubify-mpl` how much space is available in your LaTeX document and what spacing `pubify.sty` should use around figure rows, subcaptions, and captions.
Exported figures use the standard LaTeX serif face; the template controls typography sizes, not font family.

| Key | Meaning | Default |
| --- | --- | --- |
| `textwidth_in` | document `\textwidth` in inches | required |
| `textheight_in` | document `\textheight` in inches | required |
| `caption_lineheight_pt` | measured line height used to estimate main caption height | `13.6pt` |
| `subcaption_lineheight_pt` | measured line height used to estimate subcaption height | `13.6pt` |
| `base_fontsize_pt` | base font size used when styling the exported figure copy | `12pt` |
| `axes_labelsize_pt` | axis-label font size; when unset, defaults to `base_fontsize_pt`, and `-1` leaves existing axis-label sizes unchanged | `base_fontsize_pt` |
| `tick_labelsize_pt` | tick-label font size; when unset, defaults to `base_fontsize_pt - 1`, and `-1` leaves existing tick-label sizes unchanged | `base_fontsize_pt - 1` |
| `legend_fontsize_pt` | legend font size; when unset, defaults to `base_fontsize_pt - 1`, and `-1` leaves existing legend sizes unchanged | `base_fontsize_pt - 1` |
| `title_fontsize_pt` | axes-title font size; when unset, defaults to `base_fontsize_pt + 1`, and `-1` leaves existing title sizes unchanged | `base_fontsize_pt + 1` |
| `line_width_pt` | stroke width for plotted lines and compatible collections; `-1` leaves existing line widths unchanged | `-1pt` |
| `axes_line_width_pt` | stroke width for axes spines and tick marks; `-1` leaves existing axes and tick stroke widths unchanged | `0.8pt` |
| `tick_length_pt` | tick length; `-1` leaves existing tick lengths unchanged | `3.0pt` |
| `caption_allowance_in` | extra buffer added beyond the estimated main caption text height | `0.08in` |
| `subcaption_allowance_in` | extra buffer added beyond the estimated subcaption text height | `0.08in` |
| `subcaption_skip_in` | vertical space between a panel and its subcaption | `0.08in` |
| `row_skip_in` | vertical space between rows in stacked layouts | `0.11in` |
| `caption_skip_in` | vertical space between the figure body and the main caption | `0.11in` |
| `post_caption_skip_in` | additional vertical space after the main caption | `0in` |
| `col_gap_in` | horizontal space between columns | `0.02 * textwidth_in` |

For the best match to a real document, copy `textwidth_in`, `textheight_in`, `base_fontsize_pt`, `caption_lineheight_pt`, and `subcaption_lineheight_pt` from `\figprintlayoutspec`.

## Most Common `save_fig()` Options

Some `save_fig()` options control how the exported figure fits into the LaTeX layout:

- `caption_lines=...`: estimate how many lines the main caption will use
- `subcaption_lines=...`: estimate how many lines each subcaption will use
- `force_width=...`: force a smaller export width for non-wide layouts, as long as it still fits inside the selected layout
- `force_height=...`: cap the export height after the normal layout fit; on wide layouts this is the main size-control knob
- `force_aspect=...`: force a specific aspect ratio for the exported copy

`force_width` and `force_height` are mutually exclusive. Wide layouts (`"onewide"`, `"twowide"`, `"threewide"`) use the full layout width by default and do not accept `force_width`.

Other options let you simplify the exported figure content without changing the original figure in Python:

- `hide_labels=True`: remove axis labels and shared figure labels from the exported copy
- `hide_grid=True`: disable the grid on the exported copy
- `hide_cbar=True`: remove attached colorbars and all colorbar axes
- `hide_annotations=True`: remove `ax.text(...)` annotations from the exported copy

## LaTeX Macros

`pubify.sty` separates LaTeX figure layout into three pieces:

- `\figfloat[placement]{body}[caption][label]` creates the outer floating `figure` environment and adds the main caption and label.
- the layout macros such as `\figonewide`, `\figtwowide`, and `\figfour` arrange one or more `\fig{...}` panels into a specific layout.
- `\fig{file}[subcaption][label]` describes one exported panel. The optional subcaption and label are for subcaptions.

In normal use, you place one layout macro inside `\figfloat`. For example:

```tex
\figfloat[b!]
  {\figonewide{\fig{figures/plot.pdf}}}
  [A simple exported plot.]
  [fig:plot]
```

For small multi-panel figures, you can use a direct panel-by-panel form:

```tex
\figfloat[t]
  {
    \figtwowide
      {\fig{figures/left.pdf}[Left panel][fig:left]}
      {\fig{figures/right.pdf}[Right panel][fig:right]}
  }
  [Two-panel figure.]
  [fig:two-panel]
```

For larger grids, use the row-grouped form:

```tex
\figfloat[t]
  {
    \figsix
    {{\fig{figures/a.pdf}}{\fig{figures/b.pdf}}}
    {{\fig{figures/c.pdf}}{\fig{figures/d.pdf}}}
    {{\fig{figures/e.pdf}}{\fig{figures/f.pdf}}}
  }
  [Six-panel figure.]
  [fig:six-panel]
```

The supported layout macros are:

- `\figone`, `\figonewide`
- `\figtwo`, `\figtwowide`
- `\figthree`, `\figthreewide`
- `\figfour`, `\figsix`, `\figsixwide`
- `\fignine`, `\figtwelve`, `\figtwelvewide`
- `\figfifteen`, `\figsixteen`, `\figtwenty`

## Troubleshooting

- If Python export fails with a LaTeX error, check that your TeX installation is available from the command line and includes the required packages.
- If exported figure sizes do not match your document, print `\figprintlayoutspec` from the real document and update your Python template values from that output.
- If LaTeX reports that a figure float is too large for the page, the usual fixes are to shorten the caption, choose a less tall layout, or adjust the template spacing and allowance values.

## Python API Reference

Detailed Python API documentation is at [nvnunes.github.io/pubify-mpl/api/](https://nvnunes.github.io/pubify-mpl/api/).

## LaTeX Package Reference

Common forms:

```tex
\usepackage{pubify}
\usepackage[template=path/pubify-template.tex]{pubify}
\usepackage[debug]{pubify}
\usepackage[template=path/pubify-template.tex,debug]{pubify}
```

Package options:

- `template=...`: load an explicit template file
- `debug`: add figure borders and print layout diagnostics to the LaTeX log

Template resolution:

- if `template=...` is given, `pubify.sty` loads that file
- otherwise, `pubify.sty` loads `pubify-template.tex` if it is present next to `pubify.sty`
- otherwise, `pubify.sty` falls back to its built-in default lengths

## Development Approach

The implementation is intentionally pragmatic. Priority was given to producing a useful, validated tool rather than to maximizing internal elegance or generality. Parts of the implementation were developed with AI-assisted workflows. Development effort was focused on documented behavior, intended performance, and validation rather than on highly refined internal structure.

## License

MIT
