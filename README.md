# pubify-mpl

`pubify-mpl` is a small Python tool for exporting Matplotlib figures at sizes that match your LaTeX document, so the figures drop cleanly into papers, theses, and proceedings without trial-and-error resizing.

It combines two parts of a publication workflow:

- Python helpers for exporting Matplotlib figures using document-aware sizes
- a LaTeX package, `pubify.sty`, for arranging exported figures into common panel layouts

This package is meant for researchers who already use Matplotlib and LaTeX and want a cleaner path from Python plots to publication-ready figures. It is not a replacement for Matplotlib. It sits at the export and layout stage.

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
4. saves the copy to PDF

That means your original interactive figure stays unchanged in Python. This is important if you want to keep using the same figure object in a notebook or script after export.

On the export side, `save_fig(...)` can:

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
- [gallery/layout-gallery.tex](https://github.com/nvnunes/pubify-mpl/blob/main/gallery/layout-gallery.tex): sample LaTeX source showing the supported panel layouts and macro usage

## Layouts

See layout options in [gallery/layout-gallery.pdf](https://github.com/nvnunes/pubify-mpl/blob/main/gallery/layout-gallery.pdf) including:

- `"one"`: one large panel
- `"onewide"`: one short wide panel
- `"two"`: two stacked panels
- `"twowide"`: two side-by-side panels
- `"three"`: three stacked panels
- `"threewide"`: three side-by-side panels
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

For advanced styling on the exported copy, use `prepare_copy` together with
`apply_publication_style(...)`:

```python
from pubify_mpl import apply_publication_style, save_fig

def _prepare_copy(fig_copy):
    apply_publication_style(
        fig_copy,
        line_width=1.5,
        tick_labelsize=9.0,
    )

save_fig(
    fig,
    "onewide",
    f"{figures_dir}/plot.pdf",
    template=PUBIFY_TEMPLATES["thesis"],
    prepare_copy=_prepare_copy,
)
```

## Template Keys

The template dictionary tells `pubify-mpl` how much space is available in your LaTeX document and what spacing `pubify.sty` should use around figure rows, subcaptions, and captions.

| Key | Meaning | Default |
| --- | --- | --- |
| `textwidth_in` | document `\textwidth` in inches | required |
| `textheight_in` | document `\textheight` in inches | required |
| `base_fontsize_pt` | base font size used when styling the exported figure copy | `12pt` |
| `caption_lineheight_pt` | measured line height used to estimate main caption height | `13.6pt` |
| `subcaption_lineheight_pt` | measured line height used to estimate subcaption height | `13.6pt` |
| `caption_allowance_in` | extra buffer added beyond the estimated main caption text height | `0.08in` |
| `subcaption_allowance_in` | extra buffer added beyond the estimated subcaption text height | `0.08in` |
| `single_row_layout_max_height_in` | maximum total layout height budget used for single-row layouts such as `"onewide"` or `"twowide"` | `textheight_in / 3` |
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
- `force_width=...`: force a smaller export width, as long as it still fits inside the selected layout
- `force_aspect=...`: force a specific aspect ratio for the exported copy

Other options let you simplify the exported figure content without changing the original figure in Python:

- `hide_labels=True`: remove axis labels from the exported copy
- `hide_grid=True`: disable the grid on the exported copy
- `hide_cbar=True`: remove a colorbar when exporting a single-axes panel
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

All layouts also support the row-grouped form. For larger grids, that is the normal pattern:

```tex
\figfloat[t]
  {
    \figfour
    {{\fig{figures/a.pdf}}{\fig{figures/b.pdf}}}
    {{\fig{figures/c.pdf}}{\fig{figures/d.pdf}}}
  }
  [Four-panel figure.]
  [fig:four-panel]
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

## License

MIT
