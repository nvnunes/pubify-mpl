from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import matplotlib as mpl

from .layout import normalized_template

PUBIFY_FONT_FAMILY = "serif"
PUBIFY_FONT_SERIF = ["Latin Modern Roman", "LMRoman10"]
PUBIFY_MATHTEXT_FONTSET = "cm"
PUBIFY_LATEX_PREAMBLE = r"""
\usepackage[T1]{fontenc}
\usepackage[tracking]{microtype}
\usepackage{amsmath}
\usepackage{amssymb}
"""


def resolved_pubify_rc(
    template: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the resolved Matplotlib rc settings implied by a pubify template."""

    resolved_template = normalized_template(template)
    rc = {
        "font.size": resolved_template["base_fontsize_pt"],
        "text.usetex": True,
        "font.family": PUBIFY_FONT_FAMILY,
        "font.serif": list(PUBIFY_FONT_SERIF),
        "mathtext.fontset": PUBIFY_MATHTEXT_FONTSET,
        "text.latex.preamble": PUBIFY_LATEX_PREAMBLE,
    }
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


def _resolved_pubify_construction_rc(
    template: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the construction-time rc subset implied by a pubify template."""

    resolved_template = normalized_template(template)
    rc = {
        "font.size": resolved_template["base_fontsize_pt"],
        "font.family": PUBIFY_FONT_FAMILY,
        "font.serif": list(PUBIFY_FONT_SERIF),
        "mathtext.fontset": PUBIFY_MATHTEXT_FONTSET,
    }
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


@contextmanager
def pubify_rc_context(
    template: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Apply the construction-time publication rc context implied by a pubify template."""

    rc = _resolved_pubify_construction_rc(template, extra_rcparams=extra_rcparams)
    with mpl.rc_context(mpl.rcParamsDefault):
        with mpl.rc_context(rc):
            yield
