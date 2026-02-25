"""SVG chart generators for Retina PDF reports.

All charts are generated as inline SVG strings — no external dependencies.
Designed for embedding in HTML that WeasyPrint renders to PDF.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

NAVY = "#0A0E27"
ACCENT = "#0066FF"
GRAY_LIGHT = "#E8E8E8"
GRAY_MID = "#9BA8B7"
GRAY_TEXT = "#6B7280"
WHITE = "#FFFFFF"

# Lens colors — spec-defined
LENS_COLORS = {
    "performance_technical_health": "#0066FF",
    "seo_ai_visibility": "#00B8D9",
    "brand_messaging": "#7B61FF",
    "experience_design": "#FF6B6B",
    "conversion_strategy": "#FF8C00",
}

# Quadrant colors
Q_NO_BRAINER = "#00c864"
Q_GROWTH = "#4da6ff"
Q_QUICK_WIN = "#ffc800"
Q_TRANSFORM = "#ff8c00"

QUADRANT_COLORS = {
    "no_brainer": Q_NO_BRAINER,
    "growth_move": Q_GROWTH,
    "quick_win": Q_QUICK_WIN,
    "transformational": Q_TRANSFORM,
}

# Lens display names
LENS_LABELS = {
    "performance_technical_health": "Performance &\nTechnical Health",
    "seo_ai_visibility": "SEO &\nAI Visibility",
    "brand_messaging": "Brand &\nMessaging",
    "experience_design": "Experience &\nDesign",
    "conversion_strategy": "Conversion &\nStrategy",
}

LENS_LABELS_SHORT = {
    "performance_technical_health": "Performance",
    "seo_ai_visibility": "SEO",
    "brand_messaging": "Brand",
    "experience_design": "Experience",
    "conversion_strategy": "Conversion",
}

LENS_ORDER = [
    "performance_technical_health",
    "seo_ai_visibility",
    "brand_messaging",
    "experience_design",
    "conversion_strategy",
]


# ---------------------------------------------------------------------------
# Score ring — circular score gauge
# ---------------------------------------------------------------------------


def score_ring(
    score: float,
    max_score: float = 100.0,
    *,
    size: int = 160,
    stroke_width: int = 10,
    color: str = ACCENT,
    show_max: bool = True,
    label: str | None = None,
) -> str:
    """Generate a circular score gauge.

    Args:
        score: Current score value.
        max_score: Maximum possible score.
        size: SVG width and height.
        stroke_width: Ring stroke width.
        color: Ring fill color.
        show_max: Whether to show "/max" below score.
        label: Optional label below the score (e.g., "Overall Score").

    Returns:
        SVG string.
    """
    cx, cy = size // 2, size // 2
    radius = (size - stroke_width * 2 - 10) // 2
    circumference = 2 * math.pi * radius
    ratio = min(score / max_score, 1.0) if max_score > 0 else 0
    dash = circumference * ratio
    gap = circumference - dash

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
    )

    # Background ring
    lines.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="{GRAY_LIGHT}" stroke-width="{stroke_width}" />'
    )

    # Score ring
    if ratio > 0:
        lines.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-dasharray="{dash:.1f} {gap:.1f}" '
            f'stroke-linecap="round" '
            f'transform="rotate(-90 {cx} {cy})" />'
        )

    # Score text
    score_display = f"{score:.0f}" if score == int(score) else f"{score:.1f}"
    font_size = 36 if size >= 140 else (24 if size >= 90 else 18)
    lines.append(
        f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="{font_size}" '
        f'font-weight="700" fill="{NAVY}">{score_display}</text>'
    )

    if show_max:
        max_display = f"/{int(max_score)}"
        max_font = 13 if size >= 140 else (10 if size >= 90 else 8)
        lines.append(
            f'<text x="{cx}" y="{cy + font_size // 2 + 4}" text-anchor="middle" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="{max_font}" '
            f'fill="{GRAY_TEXT}">{max_display}</text>'
        )

    if label:
        label_y = cy + font_size // 2 + 20
        lines.append(
            f'<text x="{cx}" y="{label_y}" text-anchor="middle" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="11" '
            f'fill="{GRAY_TEXT}">{_escape(label)}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Segmented donut chart — summary page composite score
# ---------------------------------------------------------------------------


def segmented_donut(
    lens_scores: dict[str, float],
    total_score: float,
    *,
    size: int = 220,
    stroke_width: int = 18,
    gap_degrees: float = 3.0,
) -> str:
    """Generate a segmented donut chart showing all 5 lens scores.

    Each lens gets an arc proportional to its score. The arcs are ordered
    by LENS_ORDER and colored with LENS_COLORS. Total score is centered.

    Args:
        lens_scores: Dict mapping lens key to score (0-20 each).
        total_score: Composite score to display in center.
        size: SVG width and height.
        stroke_width: Donut ring stroke width.
        gap_degrees: Gap between segments in degrees.

    Returns:
        SVG string.
    """
    cx, cy = size // 2, size // 2
    radius = (size - stroke_width * 2 - 10) // 2
    circumference = 2 * math.pi * radius

    # Calculate total raw for proportions
    raw_total = sum(lens_scores.get(k, 0) for k in LENS_ORDER)
    if raw_total <= 0:
        raw_total = 1  # avoid division by zero

    # Total degrees available after gaps
    num_segments = len(LENS_ORDER)
    total_gap_degrees = gap_degrees * num_segments
    available_degrees = 360 - total_gap_degrees

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
    )

    # Background ring
    lines.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="#F0F0F0" stroke-width="{stroke_width}" />'
    )

    # Draw segments
    current_angle = -90  # Start from top

    for lens_key in LENS_ORDER:
        score = lens_scores.get(lens_key, 0)
        color = LENS_COLORS.get(lens_key, ACCENT)

        # Arc length proportional to score
        segment_degrees = (score / raw_total) * available_degrees if score > 0 else 0

        if segment_degrees > 0:
            arc_length = (segment_degrees / 360) * circumference
            gap_length = circumference - arc_length

            # Rotation to position this segment
            lines.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
                f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-dasharray="{arc_length:.2f} {gap_length:.2f}" '
                f'stroke-linecap="round" '
                f'transform="rotate({current_angle:.1f} {cx} {cy})" />'
            )

        current_angle += segment_degrees + gap_degrees

    # Center text — total score
    score_display = f"{total_score:.0f}" if total_score == int(total_score) else f"{total_score:.1f}"
    lines.append(
        f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="42" '
        f'font-weight="700" fill="{NAVY}">{score_display}</text>'
    )
    lines.append(
        f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="14" '
        f'fill="{GRAY_TEXT}">/100</text>'
    )
    lines.append(
        f'<text x="{cx}" y="{cy + 36}" text-anchor="middle" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
        f'fill="{GRAY_TEXT}">Overall Score</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Horizontal bar chart — single site scorecard
# ---------------------------------------------------------------------------


def horizontal_bar_chart(
    scores: dict[str, float | None],
    *,
    width: int = 340,
    bar_height: int = 28,
    max_score: float = 20.0,
    use_lens_colors: bool = True,
    pending_color: str = GRAY_LIGHT,
) -> str:
    """Generate a horizontal bar chart for a single site's lens scores.

    Each bar is colored with its respective lens color.

    Args:
        scores: Dict mapping lens key to score (None = pending/not scored).
        width: Total SVG width.
        bar_height: Height of each bar.
        max_score: Maximum score per lens.
        use_lens_colors: Whether to use per-lens colors.
        pending_color: Fill color for pending bars.

    Returns:
        SVG string.
    """
    label_width = 100
    score_width = 60
    chart_width = width - label_width - score_width
    row_height = bar_height + 16
    total_height = row_height * len(LENS_ORDER) + 10

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{total_height}" '
        f'viewBox="0 0 {width} {total_height}">'
    )

    for i, lens_key in enumerate(LENS_ORDER):
        y = i * row_height + 10
        score = scores.get(lens_key)
        is_pending = score is None
        color = LENS_COLORS.get(lens_key, ACCENT) if use_lens_colors else ACCENT

        # Label
        label = LENS_LABELS_SHORT.get(lens_key, lens_key)
        lines.append(
            f'<text x="{label_width - 12}" y="{y + bar_height // 2 + 4}" '
            f'text-anchor="end" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
            f'font-weight="500" fill="{NAVY}">{label}</text>'
        )

        # Background track
        lines.append(
            f'<rect x="{label_width}" y="{y}" '
            f'width="{chart_width}" height="{bar_height}" '
            f'rx="4" fill="{GRAY_LIGHT}" />'
        )

        if is_pending:
            lines.append(
                f'<text x="{label_width + chart_width + 10}" y="{y + bar_height // 2 + 4}" '
                f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="11" '
                f'fill="{GRAY_MID}">Pending</text>'
            )
        else:
            # Filled bar
            bar_w = max(2, (score / max_score) * chart_width)
            lines.append(
                f'<rect x="{label_width}" y="{y}" '
                f'width="{bar_w}" height="{bar_height}" '
                f'rx="4" fill="{color}" />'
            )
            # Score text: "14 /20" with score bold
            lines.append(
                f'<text x="{label_width + chart_width + 10}" y="{y + bar_height // 2 + 4}" '
                f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
                f'fill="{NAVY}">'
                f'<tspan font-weight="700">{score:.0f}</tspan>'
                f'<tspan fill="{GRAY_TEXT}"> /20</tspan></text>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Grouped bar chart — competitive comparison
# ---------------------------------------------------------------------------

SITE_COLORS = [ACCENT, "#FF6B35", "#7B2D8E", "#00A67E"]


def grouped_bar_chart(
    site_scores: list[tuple[str, dict[str, float | None]]],
    *,
    width: int = 660,
    max_score: float = 20.0,
) -> str:
    """Generate a grouped bar chart comparing multiple sites across lenses.

    Args:
        site_scores: List of (label, {lens_key: score}) tuples.
        width: Total SVG width.
        max_score: Max score per lens.

    Returns:
        SVG string.
    """
    n_sites = len(site_scores)
    n_lenses = len(LENS_ORDER)
    label_width = 120
    chart_width = width - label_width - 20
    bar_h = max(12, 28 - (n_sites * 3))
    bar_gap = 3
    group_gap = 22
    group_height = n_sites * (bar_h + bar_gap) + group_gap

    legend_height = 40
    total_height = n_lenses * group_height + legend_height + 20

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{total_height}" '
        f'viewBox="0 0 {width} {total_height}">'
    )

    # Legend
    lx = label_width
    for idx, (label, _) in enumerate(site_scores):
        color = SITE_COLORS[idx % len(SITE_COLORS)]
        lines.append(
            f'<rect x="{lx}" y="6" width="12" height="12" rx="2" fill="{color}" />'
        )
        display_label = label if len(label) <= 28 else label[:25] + "..."
        lines.append(
            f'<text x="{lx + 18}" y="16" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="11" '
            f'fill="{NAVY}">{_escape(display_label)}</text>'
        )
        lx += max(140, len(display_label) * 7 + 30)

    y_offset = legend_height

    for lens_idx, lens_key in enumerate(LENS_ORDER):
        gy = y_offset + lens_idx * group_height

        label = LENS_LABELS_SHORT.get(lens_key, lens_key)
        label_y = gy + (n_sites * (bar_h + bar_gap)) // 2 + 4
        lines.append(
            f'<text x="{label_width - 10}" y="{label_y}" '
            f'text-anchor="end" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
            f'font-weight="500" fill="{NAVY}">{label}</text>'
        )

        for site_idx, (_, scores) in enumerate(site_scores):
            by = gy + site_idx * (bar_h + bar_gap)
            score = scores.get(lens_key)
            color = SITE_COLORS[site_idx % len(SITE_COLORS)]

            lines.append(
                f'<rect x="{label_width}" y="{by}" '
                f'width="{chart_width}" height="{bar_h}" '
                f'rx="3" fill="{GRAY_LIGHT}" />'
            )

            if score is not None:
                bar_w = max(2, (score / max_score) * chart_width)
                lines.append(
                    f'<rect x="{label_width}" y="{by}" '
                    f'width="{bar_w}" height="{bar_h}" '
                    f'rx="3" fill="{color}" />'
                )
                tx = label_width + bar_w + 6
                lines.append(
                    f'<text x="{tx}" y="{by + bar_h // 2 + 4}" '
                    f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="10" '
                    f'font-weight="600" fill="{NAVY}">{score:.1f}</text>'
                )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Strategic Quadrant Matrix (2x2)
# ---------------------------------------------------------------------------


def quadrant_matrix(
    recommendations: list[dict],
    *,
    width: int = 600,
    height: int = 480,
) -> str:
    """Generate a 2x2 strategic quadrant matrix with recommendation dots.

    Args:
        recommendations: List of dicts with keys:
            title, quadrant, effort, impact.
        width: SVG width.
        height: SVG height.

    Returns:
        SVG string.
    """
    margin_left = 50
    margin_right = 20
    margin_top = 20
    margin_bottom = 50
    cw = width - margin_left - margin_right
    ch = height - margin_top - margin_bottom
    mid_x = margin_left + cw // 2
    mid_y = margin_top + ch // 2

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    # Quadrant backgrounds
    quadrant_rects = [
        (margin_left, margin_top, cw // 2, ch // 2, Q_NO_BRAINER, "No-Brainers"),
        (mid_x, margin_top, cw // 2, ch // 2, Q_GROWTH, "Growth Moves"),
        (margin_left, mid_y, cw // 2, ch // 2, Q_QUICK_WIN, "Quick Wins"),
        (mid_x, mid_y, cw // 2, ch // 2, Q_TRANSFORM, "Transformational"),
    ]

    for rx, ry, rw, rh, color, label in quadrant_rects:
        lines.append(
            f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" '
            f'fill="{color}" fill-opacity="0.1" />'
        )
        lines.append(
            f'<text x="{rx + 12}" y="{ry + 22}" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
            f'font-weight="600" fill="{color}">{label}</text>'
        )

    # Axis lines
    lines.append(
        f'<line x1="{margin_left}" y1="{mid_y}" '
        f'x2="{margin_left + cw}" y2="{mid_y}" '
        f'stroke="{NAVY}" stroke-width="1" stroke-opacity="0.2" />'
    )
    lines.append(
        f'<line x1="{mid_x}" y1="{margin_top}" '
        f'x2="{mid_x}" y2="{margin_top + ch}" '
        f'stroke="{NAVY}" stroke-width="1" stroke-opacity="0.2" />'
    )

    # Axis labels
    lines.append(
        f'<text x="{margin_left + cw // 2}" y="{height - 8}" '
        f'text-anchor="middle" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
        f'fill="{GRAY_TEXT}">Effort \u2192</text>'
    )
    lines.append(
        f'<text x="14" y="{margin_top + ch // 2}" '
        f'text-anchor="middle" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="12" '
        f'fill="{GRAY_TEXT}" '
        f'transform="rotate(-90, 14, {margin_top + ch // 2})">'
        f'Impact \u2192</text>'
    )

    # Plot recommendations as numbered dots
    quadrant_map = {
        "no_brainer": (margin_left, margin_top, cw // 2, ch // 2),
        "growth_move": (mid_x, margin_top, cw // 2, ch // 2),
        "quick_win": (margin_left, mid_y, cw // 2, ch // 2),
        "transformational": (mid_x, mid_y, cw // 2, ch // 2),
    }

    by_quadrant: dict[str, list] = {}
    for rec in recommendations:
        q = rec.get("quadrant", "quick_win")
        by_quadrant.setdefault(q, []).append(rec)

    dot_num = 0
    for q, recs in by_quadrant.items():
        area = quadrant_map.get(q)
        if not area:
            continue
        ax, ay, aw, ah = area
        color = QUADRANT_COLORS.get(q, GRAY_MID)

        for idx, rec in enumerate(recs):
            dot_num += 1
            cols = min(3, len(recs))
            row = idx // cols
            col = idx % cols
            px = ax + 40 + col * (aw - 60) // max(cols, 1)
            py = ay + 44 + row * 40

            lines.append(
                f'<circle cx="{px}" cy="{py}" r="14" fill="{color}" />'
            )
            lines.append(
                f'<text x="{px}" y="{py + 4}" text-anchor="middle" '
                f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="11" '
                f'font-weight="700" fill="{WHITE}">{dot_num}</text>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _escape(text: str) -> str:
    """Escape basic HTML entities for SVG text content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
