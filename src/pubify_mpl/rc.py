from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import matplotlib as mpl

from .style import normalized_style


def resolved_pubify_rc(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
    text_usetex: bool = False,
    font_family: str | None = None,
) -> dict[str, Any]:
    """Return target-neutral Matplotlib rc settings implied by a pubify style."""

    resolved = normalized_style(style)
    rc = {
        "font.size": resolved["base_fontsize_pt"],
        "text.usetex": text_usetex,
    }
    if font_family is not None:
        rc["font.family"] = font_family
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


def _resolved_pubify_construction_rc(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
    font_family: str | None = None,
) -> dict[str, Any]:
    """Return the target-neutral construction-time rc subset implied by a pubify style."""

    resolved = normalized_style(style)
    rc = {
        "font.size": resolved["base_fontsize_pt"],
    }
    if font_family is not None:
        rc["font.family"] = font_family
    if extra_rcparams:
        rc.update(extra_rcparams)
    return rc


@contextmanager
def pubify_rc_context(
    style: dict[str, Any] | None = None,
    *,
    extra_rcparams: dict[str, Any] | None = None,
    font_family: str | None = None,
) -> Iterator[None]:
    """Apply a target-neutral Matplotlib construction rc context."""

    rc = _resolved_pubify_construction_rc(
        style,
        extra_rcparams=extra_rcparams,
        font_family=font_family,
    )
    with mpl.rc_context(mpl.rcParamsDefault):
        with mpl.rc_context(rc):
            yield
