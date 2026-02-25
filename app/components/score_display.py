"""Reusable score display components — HTML/CSS rendered via st.markdown."""

from __future__ import annotations

import os

from app.components.styles import COLORS, LENS_COLORS, LENS_ICONS, LENS_SHORT_LABELS, hex_to_rgba


def score_color(score: float, max_score: float) -> str:
    """Return color based on score percentage."""
    pct = (score / max_score * 100) if max_score > 0 else 0
    if pct >= 75:
        return COLORS["success"]
    if pct >= 50:
        return COLORS["warning"]
    return COLORS["error"]


def score_ring_html(
    score: float,
    max_score: float = 100.0,
    size: int = 160,
    label: str = "",
) -> str:
    """Large circular score gauge using inline SVG."""
    pct = min(score / max_score, 1.0) if max_score > 0 else 0
    color = score_color(score, max_score)
    radius = size * 0.38
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - pct)
    cx = cy = size / 2
    display_score = f"{score:.1f}" if isinstance(score, float) else str(score)

    return f"""
<div style="text-align:center;">
  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
    <circle cx="{cx}" cy="{cy}" r="{radius}"
            fill="none" stroke="{COLORS['border']}" stroke-width="8" />
    <circle cx="{cx}" cy="{cy}" r="{radius}"
            fill="none" stroke="{color}" stroke-width="8"
            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            stroke-linecap="round"
            transform="rotate(-90 {cx} {cy})"
            style="transition: stroke-dashoffset 0.6s ease;" />
    <text x="{cx}" y="{cy - 6}" text-anchor="middle"
          font-size="{size * 0.22}px" font-weight="700" fill="{COLORS['text']}">
      {display_score}
    </text>
    <text x="{cx}" y="{cy + size * 0.1}" text-anchor="middle"
          font-size="{size * 0.08}px" fill="{COLORS['text_dim']}">
      / {max_score:.0f}
    </text>
  </svg>
  {f'<div style="color:{COLORS["text_muted"]};font-size:0.85rem;margin-top:4px;">{label}</div>' if label else ''}
</div>
"""


def lens_donut_svg(
    score: float,
    max_score: float = 20.0,
    color: str = "#076EFF",
    size: int = 120,
) -> str:
    """Single-color donut ring for a lens score (0-20)."""
    pct = min(score / max_score, 1.0) if max_score > 0 else 0
    radius = size * 0.38
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - pct)
    cx = cy = size / 2
    display = f"{score:.1f}"

    return f"""
<div style="text-align:center;">
  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
    <circle cx="{cx}" cy="{cy}" r="{radius}"
            fill="none" stroke="{COLORS['border']}" stroke-width="7" />
    <circle cx="{cx}" cy="{cy}" r="{radius}"
            fill="none" stroke="{color}" stroke-width="7"
            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            stroke-linecap="round"
            transform="rotate(-90 {cx} {cy})"
            style="transition: stroke-dashoffset 0.6s ease;" />
    <text x="{cx}" y="{cy - 4}" text-anchor="middle"
          font-size="{size * 0.2}px" font-weight="700" fill="{COLORS['text']}">
      {display}
    </text>
    <text x="{cx}" y="{cy + size * 0.1}" text-anchor="middle"
          font-size="{size * 0.09}px" fill="{COLORS['text_dim']}">
      / {max_score:.0f}
    </text>
  </svg>
</div>
"""


def lens_summary_card(
    lens_key: str,
    score: float | None,
    icon_svg: str = "",
) -> str:
    """Lens summary card for the overview — clickable, shows icon + score + status."""
    color = LENS_COLORS.get(lens_key, COLORS["accent"])
    name = LENS_SHORT_LABELS.get(lens_key, lens_key)

    if score is None:
        score_display = "—"
        status = "Analyst review pending"
        status_color = COLORS["text_dim"]
    elif score >= 16:
        score_display = f"{score:.1f}"
        status = "Strong"
        status_color = COLORS["success"]
    elif score >= 11:
        score_display = f"{score:.1f}"
        status = "Functional"
        status_color = COLORS["warning"]
    elif score >= 6:
        score_display = f"{score:.1f}"
        status = "Needs attention"
        status_color = COLORS["error"]
    else:
        score_display = f"{score:.1f}"
        status = "Critical"
        status_color = COLORS["error"]

    icon_html = ""
    if icon_svg:
        icon_html = f"<div style='width:24px;height:24px;flex-shrink:0;'>{icon_svg}</div>"

    return f"""
<div class="lens-card" style="border-top-color:{color};">
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:10px;">
      {icon_html}
      <span class="lens-name">{name}</span>
    </div>
    <span class="lens-score">{score_display}<span style="font-size:0.75rem;color:{COLORS['text_dim']};font-weight:400;">/20</span></span>
  </div>
  <div class="lens-status" style="color:{status_color};">● {status}</div>
</div>
"""


def subdim_card_html(
    name: str,
    score: float,
    max_score: float,
    guidance_text: str = "",
    tooltip_text: str = "",
) -> str:
    """Read-only sub-dimension card with progress bar and score label."""
    pct = min(score / max_score * 100, 100) if max_score > 0 else 0
    tooltip = f' title="{tooltip_text}"' if tooltip_text else ""

    return f"""
<div class="subdim-card">
  <div class="subdim-name">
    <span>{name}</span>
    <div style="display:flex;align-items:center;gap:8px;">
      <span class="subdim-score">{score:.1f} / {max_score:.0f}</span>
      {f'<span class="subdim-tooltip"{tooltip}>?</span>' if tooltip_text else ''}
    </div>
  </div>
  <div class="subdim-bar-track">
    <div class="subdim-bar-fill" style="width:{pct}%;"></div>
  </div>
  {f'<div class="subdim-guidance">{guidance_text}</div>' if guidance_text else ''}
</div>
"""


def progress_bar_html(
    score: float,
    max_score: float,
    label: str = "",
    show_value: bool = True,
) -> str:
    """Horizontal colored progress bar with score label."""
    pct = min(score / max_score * 100, 100) if max_score > 0 else 0
    color = score_color(score, max_score)
    value_str = f"{score:.1f}/{max_score:.0f}" if show_value else ""

    return f"""
<div style="margin-bottom:0.6rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="color:{COLORS['text']};font-size:0.85rem;">{label}</span>
    <span style="color:{COLORS['text_muted']};font-size:0.8rem;font-weight:600;">{value_str}</span>
  </div>
  <div style="background:{COLORS['border']};border-radius:6px;height:8px;overflow:hidden;">
    <div style="background:{color};border-radius:6px;height:100%;width:{pct}%;
                transition:width 0.4s ease;"></div>
  </div>
</div>
"""


def lens_legend_html(scores: dict[str, float | None]) -> str:
    """Horizontal legend row: color dot + lens name + score."""
    from app.components.charts import LENS_ORDER

    items = []
    for key in LENS_ORDER:
        color = LENS_COLORS.get(key, COLORS["accent"])
        name = LENS_SHORT_LABELS.get(key, key)
        score = scores.get(key)
        score_str = f"{score:.1f}/20" if score is not None else "—"
        items.append(
            f"<div style='display:flex;align-items:center;gap:6px;'>"
            f"<span style='width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;'></span>"
            f"<span style='font-size:0.82rem;color:{COLORS['text_muted']};'>{name}</span>"
            f"<span style='font-size:0.82rem;font-weight:600;color:{COLORS['text']};'>{score_str}</span>"
            f"</div>"
        )

    return (
        f"<div style='display:flex;flex-wrap:wrap;gap:20px;justify-content:center;"
        f"padding:12px 0;'>{''.join(items)}</div>"
    )


def cwv_indicator(
    metric_name: str,
    value: float | None,
    good_threshold: float,
    unit: str = "ms",
) -> str:
    """Core Web Vital metric card with pass/fail coloring."""
    if value is None:
        return f"""
<div class="retina-card" style="text-align:center;padding:1rem;">
  <div style="color:{COLORS['text_dim']};font-size:0.75rem;text-transform:uppercase;
              letter-spacing:0.05em;margin-bottom:6px;">{metric_name}</div>
  <div style="color:{COLORS['text_dim']};font-size:1.5rem;font-weight:700;">—</div>
</div>"""

    is_good = value <= good_threshold
    color = COLORS["success"] if is_good else COLORS["error"]
    icon = "✓" if is_good else "✗"
    display = f"{value:.2f}" if unit == "" else f"{value:.0f}"

    return f"""
<div class="retina-card" style="text-align:center;padding:1rem;border-left:3px solid {color};">
  <div style="color:{COLORS['text_muted']};font-size:0.75rem;text-transform:uppercase;
              letter-spacing:0.05em;margin-bottom:6px;">{metric_name}</div>
  <div style="color:{color};font-size:1.5rem;font-weight:700;">{display}<span style="font-size:0.75rem;"> {unit}</span></div>
  <div style="color:{color};font-size:0.7rem;margin-top:4px;">{icon} {'Good' if is_good else 'Needs Work'}</div>
</div>"""


def tech_tag(name: str, category: str = "") -> str:
    """Styled pill/tag for technology stack items."""
    cat_colors = {
        "cdn": "#076EFF",
        "javascript frameworks": "#9B59B6",
        "web frameworks": "#9B59B6",
        "cms": "#00C864",
        "analytics": "#FF8C00",
        "hosting": "#06B6D4",
        "ssl": "#00C864",
        "widgets": "#EC4899",
        "web servers": "#06B6D4",
    }
    cat_lower = category.lower() if category else ""
    color = cat_colors.get(cat_lower, COLORS["accent"])

    return f"""<span style="display:inline-block;padding:4px 12px;border-radius:16px;
font-size:0.78rem;margin:3px;background:{hex_to_rgba(color, 0.1)};color:{color};
border:1px solid {hex_to_rgba(color, 0.2)};font-weight:500;">{name}</span>"""


def lens_score_card(label: str, score: float | None, max_score: float = 20.0) -> str:
    """Compact lens score card for the overview."""
    if score is None:
        display = "—"
        color = COLORS["text_dim"]
    else:
        display = f"{score:.1f}"
        color = score_color(score, max_score)

    return f"""
<div class="retina-card" style="text-align:center;padding:1rem;">
  <div style="color:{color};font-size:1.8rem;font-weight:700;">{display}</div>
  <div style="color:{COLORS['text_dim']};font-size:0.7rem;text-transform:uppercase;
              letter-spacing:0.04em;margin-top:4px;">/{max_score:.0f}</div>
  <div style="color:{COLORS['text_muted']};font-size:0.8rem;margin-top:6px;">{label}</div>
</div>"""


def audit_result_row(audit_name: str, passed: bool | None) -> str:
    """Single audit check row with pass/fail indicator."""
    if passed is None:
        icon = f'<span style="color:{COLORS["text_dim"]};">—</span>'
        status = "N/A"
        color = COLORS["text_dim"]
    elif passed:
        icon = f'<span style="color:{COLORS["success"]};">✓</span>'
        status = "Pass"
        color = COLORS["success"]
    else:
        icon = f'<span style="color:{COLORS["error"]};">✗</span>'
        status = "Fail"
        color = COLORS["error"]

    return f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:8px 12px;border-bottom:1px solid {COLORS['border']};">
  <span style="color:{COLORS['text']};font-size:0.85rem;">{audit_name}</span>
  <span style="color:{color};font-size:0.8rem;font-weight:600;">{icon} {status}</span>
</div>"""


def save_indicator(status: str = "saved") -> str:
    """Auto-save status indicator."""
    if status == "saving":
        return f'<div style="font-size:0.75rem;color:{COLORS["warning"]};padding:4px 8px;text-align:center;">⟳ Saving...</div>'
    return f'<div style="font-size:0.75rem;color:{COLORS["success"]};padding:4px 8px;text-align:center;">✓ Saved</div>'


def _read_lens_icon(lens_key: str) -> str:
    """Read a lens SVG icon file and return its content."""
    icon_path = LENS_ICONS.get(lens_key, "")
    if icon_path and os.path.exists(icon_path):
        with open(icon_path) as f:
            return f.read()
    return ""
