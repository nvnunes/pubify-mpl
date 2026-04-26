from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import matplotlib as mpl

from .style import normalized_style

PUBIFY_FONT_FAMILY = "serif"
PUBIFY_FONT_SERIF = ["Latin Modern Roman", "LMRoman10"]
PUBIFY_MATHTEXT_FONTSET = "cm"


def resolved_pubify_rc(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
    text_usetex: bool = False,
) -> dict[str, Any]:
    """Return the resolved Matplotlib rc settings implied by a pubify style."""

    resolved = normalized_style(style)
    rc = {
        "font.size": resolved["base_fontsize_pt"],
        "text.usetex": text_usetex,
        "font.family": PUBIFY_FONT_FAMILY,
        "font.serif": list(PUBIFY_FONT_SERIF),
        "mathtext.fontset": PUBIFY_MATHTEXT_FONTSET,
    }
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


def _resolved_pubify_construction_rc(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the construction-time rc subset implied by a pubify style."""

    resolved = normalized_style(style)
    rc = {
        "font.size": resolved["base_fontsize_pt"],
        "font.family": PUBIFY_FONT_FAMILY,
        "font.serif": list(PUBIFY_FONT_SERIF),
        "mathtext.fontset": PUBIFY_MATHTEXT_FONTSET,
    }
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


@contextmanager
def pubify_rc_context(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Apply the construction-time publication rc context implied by a pubify style."""

    rc = _resolved_pubify_construction_rc(style, extra_rcparams=extra_rcparams)
    with mpl.rc_context(mpl.rcParamsDefault):
        with mpl.rc_context(rc):
            yield
