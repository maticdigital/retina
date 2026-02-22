"""Reusable score display components — HTML/CSS rendered via st.markdown."""

from __future__ import annotations

from app.components.styles import COLORS, hex_to_rgba


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


def cwv_indicator(
    metric_name: str,
    value: float | None,
    good_threshold: float,
    unit: str = "ms",
) -> str:
    """Core Web Vital metric card with pass/fail coloring."""
    if value is None:
        return f"""
<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
            border-radius:10px;padding:1rem;text-align:center;
            box-shadow:{COLORS['shadow']};">
  <div style="color:{COLORS['text_dim']};font-size:0.75rem;text-transform:uppercase;
              letter-spacing:0.05em;margin-bottom:6px;">{metric_name}</div>
  <div style="color:{COLORS['text_dim']};font-size:1.5rem;font-weight:700;">—</div>
</div>"""

    is_good = value <= good_threshold
    color = COLORS["success"] if is_good else COLORS["error"]
    icon = "✓" if is_good else "✗"
    display = f"{value:.2f}" if unit == "" else f"{value:.0f}"

    return f"""
<div style="background:{COLORS['bg_card']};border:1px solid {hex_to_rgba(color, 0.25)};
            border-radius:10px;padding:1rem;text-align:center;
            box-shadow:{COLORS['shadow']};">
  <div style="color:{COLORS['text_muted']};font-size:0.75rem;text-transform:uppercase;
              letter-spacing:0.05em;margin-bottom:6px;">{metric_name}</div>
  <div style="color:{color};font-size:1.5rem;font-weight:700;">{display}<span style="font-size:0.75rem;"> {unit}</span></div>
  <div style="color:{color};font-size:0.7rem;margin-top:4px;">{icon} {'Good' if is_good else 'Needs Work'}</div>
</div>"""


def tech_tag(name: str, category: str = "") -> str:
    """Styled pill/tag for technology stack items."""
    cat_colors = {
        "cdn": "#076EFF",
        "javascript frameworks": "#8B5CF6",
        "web frameworks": "#8B5CF6",
        "cms": "#10B981",
        "analytics": "#F59E0B",
        "hosting": "#06B6D4",
        "ssl": "#10B981",
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
<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
            border-radius:10px;padding:1rem;text-align:center;
            box-shadow:{COLORS['shadow']};">
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
        return f'<div style="font-size:0.75rem;color:{COLORS["warning"]};padding:4px 8px;">⟳ Saving...</div>'
    return f'<div style="font-size:0.75rem;color:{COLORS["success"]};padding:4px 8px;">✓ Saved</div>'
