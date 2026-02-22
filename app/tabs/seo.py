"""SEO & AI Visibility tab — meta tags, heading hierarchy, crawlability, structured data."""

from __future__ import annotations

import streamlit as st

from app.components.charts import lighthouse_gauge
from app.components.explanations import (
    error_banner_html,
    warning_banner_html,
    SEO_AUDIT_EXPLANATIONS,
)
from app.components.score_display import progress_bar_html
from app.components.styles import COLORS, hex_to_rgba

# SEO score breakdown dimensions (removed accessibility — now in Performance)
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

    seo_data = scores.get("seo_ai_visibility", {})
    breakdown = seo_data.get("breakdown", {})

    if is_primary:
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;'>{url}</p>",
            unsafe_allow_html=True,
        )

    # Score breakdown bars
    if breakdown:
        st.markdown("##### Score Breakdown")
        for key, (label, max_val) in SEO_BREAKDOWN.items():
            val = breakdown.get(key, 0)
            st.markdown(progress_bar_html(val, max_val, label), unsafe_allow_html=True)
        st.markdown("---")

    # === Blended SEO Score Gauge ===
    st.markdown("##### SEO Lighthouse Score")
    st.markdown(
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

    st.markdown("---")

    # === Meta Title & Description — Show Actual Text ===
    _render_meta_info(lh)
    st.markdown("---")

    # === Crawlability Checks — robots.txt, sitemap, crawlable ===
    _render_crawlability(lh)
    st.markdown("---")

    # === SEO Audit Results by Group ===
    _render_audit_groups(lh)


def _render_meta_info(lh: dict) -> None:
    """Show meta title and description with length analysis."""
    st.markdown("##### Meta Title & Description")
    st.markdown(
        f"<p style='color:{COLORS['text_dim']};font-size:0.78rem;margin-bottom:0.5rem;'>"
        "These are the most important on-page SEO elements. They appear in search results and directly "
        "impact click-through rates.</p>",
        unsafe_allow_html=True,
    )

    mobile_audits = lh.get("mobile", {}).get("audits", [])

    title_audit = _find_audit(mobile_audits, "document-title")
    desc_audit = _find_audit(mobile_audits, "meta-description")

    # Title
    _render_meta_card(
        title_audit,
        "Page Title",
        "document-title",
    )

    # Description
    _render_meta_card(
        desc_audit,
        "Meta Description",
        "meta-description",
    )


def _render_meta_card(audit: dict | None, label: str, audit_id: str) -> None:
    """Render a meta tag card with status and explanation."""
    score = audit.get("score") if audit else None
    display_val = audit.get("display_value", "") if audit else ""
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

    st.markdown(
        f"<div style='padding:12px 16px;margin:6px 0;background:{COLORS['bg_card']};"
        f"border:1px solid {hex_to_rgba(color, 0.25)};border-radius:8px;"
        f"box-shadow:{COLORS['shadow']};'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='font-weight:600;color:{COLORS['text']};font-size:0.85rem;'>{label}</span>"
        f"<span style='color:{color};font-size:0.8rem;font-weight:600;'>{icon} {status}</span></div>"
        f"<div style='color:{COLORS['text_muted']};font-size:0.78rem;margin-top:6px;'>{why_text}</div>"
        f"{display_html}</div>",
        unsafe_allow_html=True,
    )


def _render_crawlability(lh: dict) -> None:
    """Render crawlability checks with prominent warnings."""
    st.markdown("##### Crawlability & Indexing")
    st.markdown(
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

        explanation = SEO_AUDIT_EXPLANATIONS.get(audit_id, {})
        why_text = explanation.get("why", "")

        if score >= 0.9:
            st.markdown(
                f"<div style='padding:10px 14px;margin:4px 0;background:{hex_to_rgba(COLORS['success'], 0.05)};"
                f"border-left:3px solid {COLORS['success']};border-radius:6px;'>"
                f"<span style='color:{COLORS['success']};font-weight:600;font-size:0.85rem;'>"
                f"✓ {label}</span>"
                f"<div style='color:{COLORS['text_muted']};font-size:0.75rem;margin-top:2px;'>{why_text}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                error_banner_html(label, why_text),
                unsafe_allow_html=True,
            )


def _render_audit_groups(lh: dict) -> None:
    """Render SEO audit results organized by group with explanations."""
    mobile_audits = lh.get("mobile", {}).get("audits", [])
    if not mobile_audits:
        st.markdown(
            f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;font-style:italic;'>"
            "Detailed audit data not available. Re-run analysis to see full details.</p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown("##### SEO Audit Details")

    # Build audit lookup
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

            if why_text:
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
