"""Performance & Technical Health tab — merged Lighthouse, CWV, tech stack, accessibility, audits."""

from __future__ import annotations

import streamlit as st

from app.components.charts import lighthouse_gauge
from app.components.explanations import (
    audit_card_html,
    cwv_metric_html,
    get_interpretation,
    interpretation_html,
    section_narrative_html,
    tech_card_html,
    warning_banner_html,
    CATEGORY_LABELS,
    CWV_EXPLANATIONS,
    TECH_EXPLANATIONS,
)
from app.components.score_display import lens_donut_svg, progress_bar_html, _read_lens_icon
from app.components.styles import COLORS, LENS_COLORS, LENS_DEFINITIONS as STYLE_DEFS, hex_to_rgba

LENS_KEY = "performance_technical_health"
LENS_TITLE = "Performance & Platform"

# Performance breakdown dimension labels
PERF_BREAKDOWN = {
    "lighthouse_performance": ("Lighthouse Performance", 6),
    "lighthouse_best_practices": ("Best Practices", 3),
    "core_web_vitals": ("Core Web Vitals", 5),
    "mobile_desktop_parity": ("Mobile/Desktop Parity", 2),
    "tech_stack_health": ("Tech Stack Health", 4),
}

# Lighthouse categories to show in Performance tab
PERFORMANCE_CATEGORIES = ["performance", "accessibility", "best-practices"]


def render(site_data: list[dict], project: dict) -> None:
    """Render the Performance & Technical Health tab."""
    if not site_data:
        st.info("No analysis data available. Run an analysis first.")
        return

    primary_url = project.get("primary_url", "")

    for idx, sd in enumerate(site_data):
        url = sd.get("site_url", "Unknown")
        is_primary = url == primary_url or idx == 0

        if is_primary:
            _render_site_performance(sd, is_primary=True)
        else:
            with st.expander(f"Competitor: {url}", expanded=False):
                _render_site_performance(sd, is_primary=False)


def _render_site_performance(sd: dict, is_primary: bool = True) -> None:
    """Render performance data for a single site."""
    url = sd.get("site_url", "Unknown")
    lh = sd.get("lighthouse_data", {})
    bw = sd.get("builtwith_data", {})
    scores = sd.get("automated_scores", {})
    interp = sd.get("interpretations") or {}

    perf_data = scores.get(LENS_KEY, {})
    breakdown = perf_data.get("breakdown", {})
    lens_score = perf_data.get("score")

    # --- Lens Header ---
    if is_primary:
        _render_lens_header(lens_score)

    # Section narrative — strategic intro from interpretation
    perf_narrative = (interp.get("performance", {}) or {}).get("section_narrative")
    if perf_narrative:
        st.markdown(section_narrative_html(perf_narrative), unsafe_allow_html=True)

    # Score breakdown bars
    if breakdown:
        st.markdown(
            f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
            f"margin-bottom:0.5rem;'>Score Breakdown</p>",
            unsafe_allow_html=True,
        )
        for key, (label, max_val) in PERF_BREAKDOWN.items():
            val = breakdown.get(key, 0)
            st.markdown(progress_bar_html(val, max_val, label), unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Lighthouse Scores — Blended Mobile/Desktop ===
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Lighthouse Scores</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "Mobile score is primary (Google mobile-first indexing). Desktop shown only when gap exceeds 15 points.</p>",
        unsafe_allow_html=True,
    )

    mobile_lh = lh.get("mobile", {}).get("lighthouse_scores", {})
    desktop_lh = lh.get("desktop", {}).get("lighthouse_scores", {})

    if mobile_lh or desktop_lh:
        cols = st.columns(3)
        for i, cat_key in enumerate(PERFORMANCE_CATEGORIES):
            with cols[i]:
                mobile_val = mobile_lh.get(cat_key)
                desktop_val = desktop_lh.get(cat_key)
                label = CATEGORY_LABELS.get(cat_key, cat_key.title())

                primary_val = mobile_val if mobile_val is not None else desktop_val
                if primary_val is not None:
                    fig = lighthouse_gauge(primary_val, label)
                    st.plotly_chart(fig, use_container_width=True, key=f"lh_blend_{cat_key}_{id(sd)}")

                    if mobile_val is not None and desktop_val is not None:
                        gap = abs(desktop_val - mobile_val)
                        if gap > 15:
                            st.markdown(
                                f"<div style='text-align:center;font-size:0.75rem;color:{COLORS['warning']};'>"
                                f"Mobile: {mobile_val:.0f} | Desktop: {desktop_val:.0f}</div>",
                                unsafe_allow_html=True,
                            )

                    lh_interp = get_interpretation(interp, f"performance.lighthouse.{cat_key}")
                    if lh_interp:
                        st.markdown(interpretation_html(lh_interp), unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div style='text-align:center;color:{COLORS['text_dim']};'>—</div>",
                        unsafe_allow_html=True,
                    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Core Web Vitals — Blended with Explanations ===
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Core Web Vitals</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "Showing mobile measurements. These directly impact user experience and search ranking.</p>",
        unsafe_allow_html=True,
    )

    mobile_cwv = lh.get("mobile", {}).get("core_web_vitals", {})
    desktop_cwv = lh.get("desktop", {}).get("core_web_vitals", {})
    cwv_data = mobile_cwv if mobile_cwv else desktop_cwv

    if cwv_data:
        row1_keys = ["largest_contentful_paint_ms", "first_contentful_paint_ms", "cumulative_layout_shift"]
        cols1 = st.columns(3)
        for i, key in enumerate(row1_keys):
            with cols1[i]:
                val = cwv_data.get(key)
                cwv_interp = get_interpretation(interp, f"performance.cwv.{key}")
                st.markdown(cwv_metric_html(key, val, interpretation=cwv_interp), unsafe_allow_html=True)

        row2_keys = ["total_blocking_time_ms", "speed_index_ms", "interaction_to_next_paint_ms"]
        cols2 = st.columns(3)
        for i, key in enumerate(row2_keys):
            with cols2[i]:
                val = cwv_data.get(key)
                cwv_interp = get_interpretation(interp, f"performance.cwv.{key}")
                st.markdown(cwv_metric_html(key, val, interpretation=cwv_interp), unsafe_allow_html=True)

        if mobile_cwv and desktop_cwv:
            _show_cwv_gaps(mobile_cwv, desktop_cwv)
    else:
        st.markdown(
            f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;font-style:italic;'>"
            "Core Web Vitals data not available.</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Technology Stack (BuiltWith) ===
    _render_tech_stack(bw, interp)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Critical Audit Failures — Grouped by Category ===
    _render_audit_failures(lh, interp)


def _render_lens_header(lens_score: float | None) -> None:
    """Render the Performance lens header with icon + donut."""
    color = LENS_COLORS.get(LENS_KEY, COLORS["accent"])
    definition = STYLE_DEFS.get(LENS_KEY, "")
    icon_svg = _read_lens_icon(LENS_KEY)

    icon_html = ""
    if icon_svg:
        icon_html = f"<div style='width:28px;height:28px;flex-shrink:0;'>{icon_svg}</div>"

    hdr_left, hdr_right = st.columns([3, 1])

    with hdr_left:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
            f"{icon_html}"
            f"<h2 style='color:{COLORS['text']};font-size:1.3rem;margin:0;font-weight:700;'>"
            f"{LENS_TITLE}</h2></div>"
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;margin:0 0 1rem 0;'>"
            f"{definition}</p>",
            unsafe_allow_html=True,
        )

    with hdr_right:
        if lens_score is not None:
            st.markdown(
                lens_donut_svg(lens_score, 20.0, color, size=100),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)


def _show_cwv_gaps(mobile_cwv: dict, desktop_cwv: dict) -> None:
    """Show notable gaps between mobile and desktop CWV values."""
    gaps = []
    for key, info in CWV_EXPLANATIONS.items():
        m_val = mobile_cwv.get(key)
        d_val = desktop_cwv.get(key)
        if m_val is not None and d_val is not None:
            good = info["good"]
            m_status = "good" if m_val <= good else "poor"
            d_status = "good" if d_val <= good else "poor"
            if m_status != d_status:
                name = info["name"]
                unit = info["unit"]
                if unit == "":
                    m_disp = f"{m_val:.3f}"
                    d_disp = f"{d_val:.3f}"
                elif m_val >= 1000:
                    m_disp = f"{m_val / 1000:.1f}s"
                    d_disp = f"{d_val / 1000:.1f}s"
                else:
                    m_disp = f"{m_val:.0f}ms"
                    d_disp = f"{d_val:.0f}ms"
                gaps.append(f"<strong>{name}</strong>: Mobile {m_disp} vs Desktop {d_disp}")

    if gaps:
        st.markdown(
            f"<div style='padding:10px 14px;margin:8px 0;background:{hex_to_rgba(COLORS['warning'], 0.08)};"
            f"border:1px solid {hex_to_rgba(COLORS['warning'], 0.2)};border-radius:8px;'>"
            f"<div style='color:{COLORS['warning']};font-weight:600;font-size:0.85rem;margin-bottom:4px;'>"
            "Notable Mobile vs Desktop Gaps</div>"
            f"<div style='color:{COLORS['text_muted']};font-size:0.8rem;'>"
            + "<br>".join(gaps)
            + "</div></div>",
            unsafe_allow_html=True,
        )


def _render_tech_stack(bw: dict, interp: dict | None = None) -> None:
    """Render BuiltWith technology stack as labeled cards."""
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Technology Stack</p>",
        unsafe_allow_html=True,
    )

    tech_narrative = (interp or {}).get("performance", {}).get("tech_stack", {}).get("section_narrative")
    if tech_narrative:
        st.markdown(section_narrative_html(tech_narrative), unsafe_allow_html=True)

    techs = bw.get("technologies", [])
    if not techs:
        st.markdown(
            warning_banner_html(
                "Technology Stack Data Unavailable",
                "BuiltWith data was not returned for this site. This may indicate the BuiltWith API key "
                "needs credits, the domain is too new, or the site blocks technology detection.",
            ),
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        f"Detected {len(techs)} technologies. Each technology choice affects performance, security, and extensibility.</p>",
        unsafe_allow_html=True,
    )

    # Group by category
    grouped: dict[str, list[dict]] = {}
    for t in techs:
        cats = t.get("categories", [])
        cat = cats[0] if cats else "Other"
        grouped.setdefault(cat, []).append(t)

    priority_cats = [
        "cms", "hosting", "cdn", "javascript frameworks", "web frameworks",
        "analytics", "tag managers", "ssl", "web servers", "payment",
        "advertising", "marketing automation", "widgets", "email",
    ]

    tech_interp_findings = (interp or {}).get("performance", {}).get("tech_stack", {}).get("findings", [])
    tech_interp_map: dict[str, dict] = {}
    for tf in tech_interp_findings:
        if isinstance(tf, dict) and tf.get("name"):
            tech_interp_map[tf["name"].lower()] = tf

    rendered_cats: set[str] = set()
    for cat_lower in priority_cats:
        for cat_name in list(grouped.keys()):
            if cat_name.lower() == cat_lower:
                _render_tech_category(cat_name, grouped[cat_name], tech_interp_map)
                rendered_cats.add(cat_name)

    for cat_name in sorted(grouped.keys()):
        if cat_name not in rendered_cats:
            _render_tech_category(cat_name, grouped[cat_name], tech_interp_map)


def _render_tech_category(category: str, techs: list[dict], tech_interp_map: dict | None = None) -> None:
    """Render a single technology category with cards."""
    cat_explanation = TECH_EXPLANATIONS.get(category.lower(), "")

    st.markdown(
        f"<p style='color:{COLORS['accent']};font-size:0.72rem;text-transform:uppercase;"
        f"letter-spacing:0.05em;font-weight:600;margin:1rem 0 0.25rem 0;'>{category}"
        f"<span style='color:{COLORS['text_dim']};font-weight:400;font-size:0.7rem;margin-left:8px;'>"
        f"{cat_explanation}</span></p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(techs), 3))
    for i, t in enumerate(techs):
        with cols[i % 3]:
            name = t.get("name", "Unknown")
            desc = t.get("description", "")
            t_interp = (tech_interp_map or {}).get(name.lower())
            st.markdown(
                tech_card_html(name, desc, category, interpretation=t_interp),
                unsafe_allow_html=True,
            )


def _render_audit_failures(lh: dict, interp: dict | None = None) -> None:
    """Render critical audit failures grouped by category, sorted by weight."""
    mobile_audits = lh.get("mobile", {}).get("audits", [])
    desktop_audits = lh.get("desktop", {}).get("audits", [])

    audits = mobile_audits if mobile_audits else desktop_audits
    if not audits:
        st.markdown(
            f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;font-style:italic;'>"
            "Detailed audit data not available. Re-run analysis to see full details.</p>",
            unsafe_allow_html=True,
        )
        return

    failures = [
        a for a in audits
        if a.get("score") is not None and a["score"] < 0.5 and a.get("weight", 0) > 0
    ]

    passing = [
        a for a in audits
        if a.get("score") is not None and a["score"] >= 0.9 and a.get("weight", 0) > 0
    ]

    if not failures and not passing:
        return

    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Audit Results</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        f"Based on mobile Lighthouse audit. {len(failures)} issue(s) found, "
        f"{len(passing)} audit(s) passing.</p>",
        unsafe_allow_html=True,
    )

    if failures:
        by_category: dict[str, list[dict]] = {}
        for a in failures:
            cat = a.get("category", "other")
            by_category.setdefault(cat, []).append(a)

        for cat_key in ["performance", "accessibility", "best-practices", "seo"]:
            cat_audits = by_category.get(cat_key, [])
            if not cat_audits:
                continue

            cat_label = CATEGORY_LABELS.get(cat_key, cat_key.title())
            st.markdown(
                f"<div style='color:{COLORS['error']};font-weight:600;font-size:0.85rem;"
                f"margin:0.75rem 0 0.25rem 0;'>{cat_label} Issues ({len(cat_audits)})</div>",
                unsafe_allow_html=True,
            )

            for a in sorted(cat_audits, key=lambda x: x.get("weight", 0), reverse=True):
                a_interp = get_interpretation(interp, f"performance.audits.{a.get('id', '')}")
                st.markdown(
                    audit_card_html(
                        audit_id=a.get("id", ""),
                        title=a.get("title", a.get("id", "Unknown").replace("-", " ").title()),
                        description=a.get("description", ""),
                        score=a.get("score"),
                        display_value=a.get("display_value"),
                        weight=a.get("weight", 0),
                        category=cat_key,
                        interpretation=a_interp,
                    ),
                    unsafe_allow_html=True,
                )

        other_audits = by_category.get("other", [])
        if other_audits:
            st.markdown(
                f"<div style='color:{COLORS['warning']};font-weight:600;font-size:0.85rem;"
                f"margin:0.75rem 0 0.25rem 0;'>Other Issues ({len(other_audits)})</div>",
                unsafe_allow_html=True,
            )
            for a in sorted(other_audits, key=lambda x: x.get("weight", 0), reverse=True):
                a_interp = get_interpretation(interp, f"performance.audits.{a.get('id', '')}")
                st.markdown(
                    audit_card_html(
                        audit_id=a.get("id", ""),
                        title=a.get("title", "Unknown"),
                        description=a.get("description", ""),
                        score=a.get("score"),
                        display_value=a.get("display_value"),
                        weight=a.get("weight", 0),
                        category="other",
                        interpretation=a_interp,
                    ),
                    unsafe_allow_html=True,
                )
