from __future__ import annotations

from math import isfinite
from numbers import Real
from typing import Any, TypeAlias


StyleSpec: TypeAlias = dict[str, Any]

DEFAULT_STYLE: StyleSpec = {
    "base_fontsize_pt": 12.0,
    "axes_labelsize_pt": 12.0,
    "tick_labelsize_pt": 11.0,
    "legend_fontsize_pt": 11.0,
    "title_fontsize_pt": 13.0,
    "line_width_pt": -1.0,
    "axes_line_width_pt": 0.8,
    "tick_length_pt": 3.0,
}


def normalized_style(style: StyleSpec | None = None) -> StyleSpec:
    """Return a complete Matplotlib export style dictionary."""

    if style is not None and not isinstance(style, dict):
        raise TypeError("style must be a style dictionary or None.")
    resolved = dict(DEFAULT_STYLE)
    if style is not None:
        unknown_keys = [key for key in style if key not in DEFAULT_STYLE]
        if unknown_keys:
            unknown = ", ".join(repr(key) for key in unknown_keys)
            allowed = ", ".join(sorted(DEFAULT_STYLE))
            raise ValueError(f"unknown style option(s): {unknown}. Expected one of: {allowed}.")

        for key, value in style.items():
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"style option {key!r} must be a finite number.")
            if not isfinite(float(value)):
                raise ValueError(f"style option {key!r} must be a finite number.")

        resolved.update(style)
    return resolved
