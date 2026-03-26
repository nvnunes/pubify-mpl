from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = REPO_ROOT / "examples" / "quickstart.ipynb"
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pubify_mpl.layout import DEFAULT_TEMPLATE

QUICKSTART_TEMPLATE_KEYS = (
    ("textwidth_in", ".5f"),
    ("textheight_in", ".5f"),
    ("base_fontsize_pt", ".1f"),
    ("caption_lineheight_pt", ".1f"),
    ("subcaption_lineheight_pt", ".1f"),
)


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def render_quickstart_template_dict(*, variable_name: str = "template") -> str:
    lines = [
        f"{variable_name} = {{",
        "    # Values for the default LaTeX article class example.",
    ]
    lines.extend(
        f'    "{key}": {DEFAULT_TEMPLATE[key]:{fmt}},'
        for key, fmt in QUICKSTART_TEMPLATE_KEYS
    )
    lines.append("}")
    return "\n".join(lines)


def template_source_lines() -> list[str]:
    return [
        'paper_dir = "tex"\n',
        'figures_dir = "tex/figures"\n',
        "\n",
        *[
            f"{line}\n"
            for line in render_quickstart_template_dict().splitlines()
        ],
    ]


def build_notebook() -> dict:
    cells = [
        markdown_cell(
            "# pubify-mpl Quick Start\n\n"
            "This notebook mirrors the minimal example from the README. "
            "It creates a simple Matplotlib figure, prepares the tracked example "
            "LaTeX project in `examples/tex/`, and exports the figure using the "
            "`onewide` layout.\n"
        ),
        code_cell(
            "import matplotlib.pyplot as plt\n\n"
            "from pubify_mpl import prepare, save_fig\n"
        ),
        code_cell(
            "".join(template_source_lines())
        ),
        code_cell(
            "fig, ax = plt.subplots()\n"
            "ax.plot([0, 1], [0, 1])\n"
            'ax.set_xlabel("x")\n'
            'ax.set_ylabel("y")\n'
            "plt.show()\n"
        ),
        code_cell(
            "prepare(paper_dir, template=template)\n"
            'save_fig(fig, "onewide", f"{figures_dir}/plot.pdf", template=template)\n'
        ),
        markdown_cell(
            "After running the cells above, your LaTeX project will usually contain:\n\n"
            "```text\n"
            "tex/main.tex\n"
            "tex/pubify.sty\n"
            "tex/pubify-template.tex\n"
            "tex/figures/plot.pdf\n"
            "```\n\n"
            "This notebook writes the generated files into the same `tex/` directory.\n\n"
            "Then in `tex/main.tex` you can use:\n\n"
            "```tex\n"
            "\\usepackage{pubify}\n"
            "```\n"
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    NOTEBOOK_PATH.write_text(json.dumps(build_notebook(), indent=1) + "\n")
    print(f"Updated {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
