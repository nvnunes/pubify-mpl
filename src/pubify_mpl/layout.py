from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator, TypeAlias

TemplateSpec: TypeAlias = dict[str, Any]
TemplateInput: TypeAlias = TemplateSpec | None

_TEX_PT_PER_IN = 72.27
_LATEX_WIDTH_SAFETY_PT = 1.5
_LATEX_HEIGHT_SAFETY_PT = 2.0

DEFAULT_TEMPLATE = {
    "textwidth_in": 5.39643,
    "textheight_in": 7.58960,
    "base_fontsize_pt": 12.0,
    "line_width_pt": -1.0,
    "axes_line_width_pt": 0.8,
    "tick_length_pt": 3.0,
    "caption_lineheight_pt": 13.6,
    "subcaption_lineheight_pt": 13.6,
    "row_skip_in": 0.11,
    "caption_skip_in": 0.11,
    "subcaption_skip_in": 0.08,
    "subcaption_allowance_in": 0.08,
    "caption_allowance_in": 0.08,
}
_CURRENT_TEMPLATE: ContextVar[TemplateInput] = ContextVar(
    "pubify_mpl_current_template", default=None
)

LAYOUTS = {
    "one": {"cols": 1, "rows": 1, "height_mode": "full_page"},
    "onewide": {"cols": 1, "rows": 1, "height_mode": "wide"},
    "two": {"cols": 1, "rows": 2, "height_mode": "stacked"},
    "twowide": {"cols": 2, "rows": 1, "height_mode": "wide"},
    "three": {"cols": 1, "rows": 3, "height_mode": "stacked"},
    "threewide": {"cols": 3, "rows": 1, "height_mode": "wide"},
    "four": {"cols": 2, "rows": 2, "height_mode": "stacked"},
    "six": {"cols": 2, "rows": 3, "height_mode": "stacked"},
    "sixwide": {"cols": 3, "rows": 2, "height_mode": "stacked"},
    "nine": {"cols": 3, "rows": 3, "height_mode": "stacked"},
    "twelve": {"cols": 3, "rows": 4, "height_mode": "stacked"},
    "twelvewide": {"cols": 4, "rows": 3, "height_mode": "stacked"},
    "fifteen": {"cols": 3, "rows": 5, "height_mode": "stacked"},
    "sixteen": {"cols": 4, "rows": 4, "height_mode": "stacked"},
    "twenty": {"cols": 4, "rows": 5, "height_mode": "stacked"},
}


def normalized_template(template: TemplateInput = None) -> TemplateSpec:
    if template is None:
        template = _CURRENT_TEMPLATE.get()
    elif not isinstance(template, dict):
        raise TypeError("template must be a template dictionary or None.")

    spec = dict(DEFAULT_TEMPLATE)
    if template is not None:
        spec.update(template)

    if "col_gap_in" not in spec:
        spec["col_gap_in"] = spec["textwidth_in"] * 0.02

    if "axes_labelsize_pt" not in spec:
        spec["axes_labelsize_pt"] = spec["base_fontsize_pt"]
    if "tick_labelsize_pt" not in spec:
        spec["tick_labelsize_pt"] = spec["base_fontsize_pt"] - 1
    if "legend_fontsize_pt" not in spec:
        spec["legend_fontsize_pt"] = spec["base_fontsize_pt"] - 1
    if "title_fontsize_pt" not in spec:
        spec["title_fontsize_pt"] = spec["base_fontsize_pt"] + 1

    spec["caption_lineheight_in"] = spec["caption_lineheight_pt"] / _TEX_PT_PER_IN
    spec["subcaption_lineheight_in"] = spec["subcaption_lineheight_pt"] / _TEX_PT_PER_IN

    if "post_caption_skip_in" not in spec:
        spec["post_caption_skip_in"] = 0.0

    if "textwidth_in" not in spec or "textheight_in" not in spec:
        raise ValueError("template must define 'textwidth_in' and 'textheight_in'.")
    return spec


@contextmanager
def use_template(template: TemplateSpec) -> Iterator[None]:
    """Temporarily set a default template for `save_fig(...)` calls.

    Inside the `with` block, any `save_fig(...)` call that does not pass an
    explicit `template=...` argument will use this template.

    Args:
        template: Template dictionary to activate inside the context.
    """
    token = _CURRENT_TEMPLATE.set(template)
    try:
        yield
    finally:
        _CURRENT_TEMPLATE.reset(token)


def normalized_layout_spec(layout_spec: TemplateInput = None) -> TemplateSpec:
    return normalized_template(layout_spec)


def layout_spec_rowgap_in(layout_spec: TemplateInput = None) -> float:
    spec = normalized_template(layout_spec)
    return spec["row_skip_in"]


def layout_spec_colgap_in(layout_spec: TemplateInput = None) -> float:
    spec = normalized_template(layout_spec)
    return spec["col_gap_in"]


def estimated_text_height_in(line_count: int | float = 0, lineheight_in: float = 0.0) -> float:
    return max(float(line_count), 0.0) * float(lineheight_in)


def layout_spec_fullpage_height_in(
    layout_spec: TemplateInput = None,
    caption_lines: int = 0,
    subcaption_lines: int = 0,
) -> float:
    spec = normalized_template(layout_spec)
    height = (
        spec["textheight_in"]
        - spec["caption_allowance_in"]
        - estimated_text_height_in(caption_lines, lineheight_in=spec["caption_lineheight_in"])
        - spec["caption_skip_in"]
        - spec["post_caption_skip_in"]
    )
    if subcaption_lines > 0:
        height -= (
            spec["subcaption_allowance_in"]
            + estimated_text_height_in(
                subcaption_lines, lineheight_in=spec["subcaption_lineheight_in"]
            )
            + spec["subcaption_skip_in"]
        )
    return height


def layout_spec_stacked_height_in(
    layout_spec: TemplateInput = None,
    rows: int = 1,
    caption_lines: int = 0,
    subcaption_lines: int = 0,
) -> float:
    spec = normalized_template(layout_spec)
    height = (
        spec["textheight_in"]
        - spec["caption_allowance_in"]
        - estimated_text_height_in(caption_lines, lineheight_in=spec["caption_lineheight_in"])
        - spec["caption_skip_in"]
        - spec["post_caption_skip_in"]
    )
    if subcaption_lines > 0:
        height -= rows * (
            spec["subcaption_allowance_in"]
            + estimated_text_height_in(
                subcaption_lines, lineheight_in=spec["subcaption_lineheight_in"]
            )
            + spec["subcaption_skip_in"]
        )
    return height


def latex_safety_in(pt_value: float) -> float:
    return pt_value / _TEX_PT_PER_IN


def latex_layout_geometry(
    layout: str = "one",
    layout_spec: TemplateInput = None,
    caption_lines: int = 0,
    subcaption_lines: int = 0,
) -> dict[str, Any]:
    try:
        layout_definition = LAYOUTS[layout]
    except KeyError as exc:
        raise ValueError(f"Unknown layout '{layout}' for LaTeX geometry.") from exc

    spec = normalized_template(layout_spec)
    cols = layout_definition["cols"]
    rows = layout_definition["rows"]
    height_mode = layout_definition["height_mode"]
    textwidth = spec["textwidth_in"]
    colgap = layout_spec_colgap_in(spec)

    width = (textwidth - (cols - 1) * colgap) / cols

    if height_mode == "full_page":
        height = layout_spec_fullpage_height_in(
            spec,
            caption_lines=caption_lines,
            subcaption_lines=subcaption_lines,
        )
    elif height_mode == "wide":
        height = layout_spec_fullpage_height_in(
            spec,
            caption_lines=caption_lines,
            subcaption_lines=subcaption_lines,
        )
    elif height_mode == "stacked":
        height = (
            layout_spec_stacked_height_in(
                spec,
                rows=rows,
                caption_lines=caption_lines,
                subcaption_lines=subcaption_lines,
            )
            - (rows - 1) * layout_spec_rowgap_in(spec)
        ) / rows
    else:
        raise ValueError(f"Unknown height mode '{height_mode}' for layout '{layout}'.")

    width -= latex_safety_in(_LATEX_WIDTH_SAFETY_PT)
    height -= latex_safety_in(_LATEX_HEIGHT_SAFETY_PT)

    if height <= 0:
        raise ValueError(f"Non-positive LaTeX height derived for layout '{layout}'.")
    if width <= 0:
        raise ValueError(f"Non-positive LaTeX width derived for layout '{layout}'.")

    return {
        "layout": layout,
        "cols": cols,
        "rows": rows,
        "width_in": width,
        "height_in": height,
        "height_mode": height_mode,
        "has_subcaption": subcaption_lines > 0,
        "layout_spec": spec,
    }
