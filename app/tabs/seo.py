"""SEO & AI Visibility tab — meta tags, heading hierarchy, crawlability, structured data."""

from __future__ import annotations

import streamlit as st

from app.components.charts import lighthouse_gauge
from app.components.explanations import (
    error_banner_html,
    get_interpretation,
    interpretation_html,
    section_narrative_html,
    warning_banner_html,
    SEO_AUDIT_EXPLANATIONS,
)
from app.components.score_display import lens_donut_svg, progress_bar_html, _read_lens_icon
from app.components.styles import COLORS, LENS_COLORS, LENS_DEFINITIONS as STYLE_DEFS, hex_to_rgba

LENS_KEY = "seo_ai_visibility"
LENS_TITLE = "SEO & AI Visibility"

# SEO score breakdown dimensions
SEO_BREAKDOWN = {
    "lighthouse_seo": ("Lighthouse SEO Score", 6),
    "structured_data": ("Structured Data", 3),
    "meta_completeness": ("Meta Completeness", 3),
    "mobile_friendliness": ("Mobile Friendliness", 2),
    "indexability": ("Indexability Signals", 2),
}

# Audit groups — organized by SEO concern
AUDIT_GROUPS = {
    "Meta Tags": [
        ("document-title", "Page Title"),
        ("meta-description", "Meta Description"),
        ("canonical", "Canonical URL"),
        ("hreflang", "Hreflang Tags"),
        ("html-has-lang", "HTML Lang Attribute"),
    ],
    "Crawlability & Indexing": [
        ("robots-txt", "robots.txt"),
        ("is-crawlable", "Crawlable"),
        ("crawlable-anchors", "Crawlable Links"),
        ("http-status-code", "HTTP Status"),
    ],
    "Structured Data": [
        ("structured-data-item", "Schema Markup"),
    ],
    "Content Quality": [
        ("image-alt", "Image Alt Text"),
        ("heading-order", "Heading Hierarchy"),
        ("link-text", "Descriptive Link Text"),
    ],
    "Mobile Usability": [
        ("viewport", "Viewport Meta"),
        ("tap-targets", "Tap Targets"),
        ("font-size", "Font Size"),
    ],
}


def render(site_data: list[dict], project: dict) -> None:
    """Render the SEO & AI Visibility tab."""
    if not site_data:
        st.info("No analysis data available. Run an analysis first.")
        return

    primary_url = project.get("primary_url", "")

    for idx, sd in enumerate(site_data):
        url = sd.get("site_url", "Unknown")
        is_primary = url == primary_url or idx == 0

        if is_primary:
            _render_site_seo(sd, is_primary=True)
        else:
            with st.expander(f"Competitor: {url}", expanded=False):
                _render_site_seo(sd, is_primary=False)


def _render_site_seo(sd: dict, is_primary: bool = True) -> None:
    """Render SEO data for a single site."""
    url = sd.get("site_url", "Unknown")
    lh = sd.get("lighthouse_data", {})
    scores = sd.get("automated_scores", {})
    interp = sd.get("interpretations") or {}

    seo_data = scores.get(LENS_KEY, {})
    breakdown = seo_data.get("breakdown", {})
    lens_score = seo_data.get("score")

    # --- Lens Header ---
    if is_primary:
        _render_lens_header(lens_score)

    # Section narrative
    seo_narrative = (interp.get("seo", {}) or {}).get("section_narrative")
    if seo_narrative:
        st.markdown(section_narrative_html(seo_narrative), unsafe_allow_html=True)

    # Score breakdown bars
    if breakdown:
        st.markdown(
            f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
            f"margin-bottom:0.5rem;'>Score Breakdown</p>",
            unsafe_allow_html=True,
        )
        for key, (label, max_val) in SEO_BREAKDOWN.items():
            val = breakdown.get(key, 0)
            st.markdown(progress_bar_html(val, max_val, label), unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Blended SEO Score Gauge ===
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>SEO Lighthouse Score</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "Mobile score is primary. Desktop shown when gap exceeds 15 points.</p>",
        unsafe_allow_html=True,
    )

    mobile_lh = lh.get("mobile", {}).get("lighthouse_scores", {})
    desktop_lh = lh.get("desktop", {}).get("lighthouse_scores", {})

    mobile_seo = mobile_lh.get("seo")
    desktop_seo = desktop_lh.get("seo")

    if mobile_seo is not None or desktop_seo is not None:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            primary_val = mobile_seo if mobile_seo is not None else desktop_seo
            if primary_val is not None:
                fig = lighthouse_gauge(primary_val, "SEO")
                st.plotly_chart(fig, use_container_width=True, key=f"seo_gauge_{id(sd)}")

                if mobile_seo is not None and desktop_seo is not None:
                    gap = abs(desktop_seo - mobile_seo)
                    if gap > 15:
                        st.markdown(
                            f"<div style='text-align:center;font-size:0.75rem;color:{COLORS['warning']};'>"
                            f"Mobile: {mobile_seo:.0f} | Desktop: {desktop_seo:.0f}</div>",
                            unsafe_allow_html=True,
                        )

        seo_interp = get_interpretation(interp, "seo.lighthouse_seo")
        if seo_interp:
            with col2:
                st.markdown(interpretation_html(seo_interp), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Meta Title & Description ===
    _render_meta_info(lh, interp)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === Crawlability Checks ===
    _render_crawlability(lh, interp)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # === SEO Audit Results by Group ===
    _render_audit_groups(lh, interp)


def _render_lens_header(lens_score: float | None) -> None:
    """Render the SEO lens header with icon + donut."""
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


def _render_meta_info(lh: dict, interp: dict | None = None) -> None:
    """Show meta title and description with length analysis."""
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Meta Title & Description</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "These are the most important on-page SEO elements. They appear in search results and directly "
        "impact click-through rates.</p>",
        unsafe_allow_html=True,
    )

    mobile_audits = lh.get("mobile", {}).get("audits", [])

    title_audit = _find_audit(mobile_audits, "document-title")
    desc_audit = _find_audit(mobile_audits, "meta-description")

    _render_meta_card(
        title_audit, "Page Title", "document-title",
        get_interpretation(interp, "seo.meta.document-title"),
    )
    _render_meta_card(
        desc_audit, "Meta Description", "meta-description",
        get_interpretation(interp, "seo.meta.meta-description"),
    )


def _render_meta_card(audit: dict | None, label: str, audit_id: str, interp_data: dict | None = None) -> None:
    """Render a meta tag card with status and explanation."""
    score = audit.get("score") if audit else None
    display_val = audit.get("display_value", "") if audit else ""
    from app.components.explanations import SEO_AUDIT_EXPLANATIONS
    explanation = SEO_AUDIT_EXPLANATIONS.get(audit_id, {})
    why_text = explanation.get("why", "")

    if score is None:
        st.markdown(
            warning_banner_html(label, f"{label} audit data not available."),
            unsafe_allow_html=True,
        )
        return

    if score >= 0.9:
        color = COLORS["success"]
        icon = "✓"
        status = "Present"
    else:
        color = COLORS["error"]
        icon = "✗"
        status = "Missing or Invalid"

    display_html = ""
    if display_val:
        display_html = (
            f"<div style='color:{COLORS['text']};font-size:0.82rem;margin-top:8px;padding:8px;"
            f"background:{hex_to_rgba(COLORS['accent'], 0.05)};border-radius:4px;'>"
            f"<code>{display_val}</code></div>"
        )

    if interp_data:
        detail_html = interpretation_html(interp_data)
    else:
        detail_html = f"<div style='color:{COLORS['text_muted']};font-size:0.78rem;margin-top:6px;'>{why_text}</div>"

    st.markdown(
        f"<div class='retina-card' style='border-left:3px solid {color};'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-weight:600;color:{COLORS['text']};font-size:0.85rem;'>{label}</span>"
        f"<span style='color:{color};font-size:0.8rem;font-weight:600;'>{icon} {status}</span></div>"
        f"{detail_html}"
        f"{display_html}</div>",
        unsafe_allow_html=True,
    )


def _render_crawlability(lh: dict, interp: dict | None = None) -> None:
    """Render crawlability checks with prominent warnings."""
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.25rem;'>Crawlability & Indexing</p>"
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "These checks determine whether search engines can find, crawl, and index your pages.</p>",
        unsafe_allow_html=True,
    )

    mobile_audits = lh.get("mobile", {}).get("audits", [])

    critical_items = [
        ("robots-txt", "robots.txt"),
        ("is-crawlable", "Crawlability"),
        ("http-status-code", "HTTP Status Code"),
    ]

    for audit_id, label in critical_items:
        audit = _find_audit(mobile_audits, audit_id)
        if not audit:
            continue

        score = audit.get("score")
        if score is None:
            continue

        crawl_interp = get_interpretation(interp, f"seo.crawlability.{audit_id}")
        from app.components.explanations import SEO_AUDIT_EXPLANATIONS
        explanation = SEO_AUDIT_EXPLANATIONS.get(audit_id, {})
        why_text = explanation.get("why", "")

        if crawl_interp:
            interp_block = interpretation_html(crawl_interp)
        else:
            interp_block = f"<div style='color:{COLORS['text_muted']};font-size:0.75rem;margin-top:2px;'>{why_text}</div>"

        if score >= 0.9:
            st.markdown(
                f"<div style='padding:10px 14px;margin:4px 0;background:{hex_to_rgba(COLORS['success'], 0.05)};"
                f"border-left:3px solid {COLORS['success']};border-radius:6px;'>"
                f"<span style='color:{COLORS['success']};font-weight:600;font-size:0.85rem;'>"
                f"✓ {label}</span>"
                f"{interp_block}"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            if crawl_interp:
                st.markdown(
                    f"<div style='padding:12px 16px;margin:10px 0;background:{hex_to_rgba(COLORS['error'], 0.08)};"
                    f"border:1px solid {hex_to_rgba(COLORS['error'], 0.2)};border-radius:8px;'>"
                    f"<div style='color:{COLORS['error']};font-weight:600;font-size:0.9rem;'>✗ {label}</div>"
                    f"{interp_block}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    error_banner_html(label, why_text),
                    unsafe_allow_html=True,
                )


def _render_audit_groups(lh: dict, interp: dict | None = None) -> None:
    """Render SEO audit results organized by group with explanations."""
    mobile_audits = lh.get("mobile", {}).get("audits", [])
    if not mobile_audits:
        st.markdown(
            f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;font-style:italic;'>"
            "Detailed audit data not available. Re-run analysis to see full details.</p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.5rem;'>SEO Audit Details</p>",
        unsafe_allow_html=True,
    )

    audit_lookup: dict[str, dict] = {}
    for a in mobile_audits:
        aid = a.get("id", "")
        if aid:
            audit_lookup[aid] = a

    for group_name, audit_items in AUDIT_GROUPS.items():
        group_audits = [(aid, label) for aid, label in audit_items if aid in audit_lookup]
        if not group_audits:
            continue

        html = (
            f'<div style="margin:0.75rem 0 0.25rem 0;">'
            f'<div style="color:{COLORS["text"]};font-weight:600;font-size:0.85rem;">{group_name}</div>'
        )

        for audit_id, audit_label in group_audits:
            audit_data = audit_lookup.get(audit_id, {})
            score = audit_data.get("score")
            display_val = audit_data.get("display_value", "")

            if score is None:
                passed = None
            else:
                passed = score >= 0.5

            audit_interp = get_interpretation(interp, f"seo.audits.{audit_id}")
            if not audit_interp:
                audit_interp = get_interpretation(interp, f"seo.meta.{audit_id}")
            if not audit_interp:
                audit_interp = get_interpretation(interp, f"seo.crawlability.{audit_id}")

            from app.components.explanations import SEO_AUDIT_EXPLANATIONS
            explanation = SEO_AUDIT_EXPLANATIONS.get(audit_id, {})
            why_text = explanation.get("why", "")
            display_name = explanation.get("name", audit_label)

            if passed is None:
                icon = f'<span style="color:{COLORS["text_dim"]};">—</span>'
                status_text = "N/A"
                color = COLORS["text_dim"]
            elif passed:
                icon = f'<span style="color:{COLORS["success"]};">✓</span>'
                status_text = "Pass"
                color = COLORS["success"]
            else:
                icon = f'<span style="color:{COLORS["error"]};">✗</span>'
                status_text = "Fail"
                color = COLORS["error"]

            html += (
                f'<div style="padding:8px 12px;border-bottom:1px solid {COLORS["border"]};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="color:{COLORS["text"]};font-size:0.85rem;">{display_name}</span>'
                f'<span style="color:{color};font-size:0.8rem;font-weight:600;">{icon} {status_text}'
            )
            if display_val:
                html += f'<span style="color:{COLORS["text_dim"]};font-size:0.75rem;margin-left:6px;">{display_val}</span>'
            html += '</span></div>'

            if audit_interp:
                html += interpretation_html(audit_interp)
            elif why_text:
                html += (
                    f'<div style="color:{COLORS["text_muted"]};font-size:0.72rem;'
                    f'margin-top:2px;line-height:1.4;">{why_text}</div>'
                )
            html += '</div>'

        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


def _find_audit(audits: list[dict], audit_id: str) -> dict | None:
    """Find an audit by ID in the audit list."""
    for a in audits:
        if a.get("id") == audit_id:
            return a
    return None
