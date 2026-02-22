"""Export tab — PDF generation, JSON download, report completeness preview."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.components.styles import COLORS

LENS_NAMES = {
    "performance_technical_health": "Performance & Technical Health",
    "seo_ai_visibility": "SEO & AI Visibility",
    "brand_messaging": "Brand & Messaging",
    "experience_design": "Experience & Design",
    "conversion_strategy": "Conversion & Strategy",
}


def render(
    project: dict,
    site_data: list[dict],
    analyst_scores: list[dict],
    reports: list[dict],
) -> None:
    """Render the Export tab."""

    # --- Completeness Preview ---
    st.markdown("##### Report Completeness")

    primary_url = project.get("primary_url", "")
    auto_scores = {}
    if site_data:
        primary_sd = None
        for sd in site_data:
            if sd.get("site_url") == primary_url:
                primary_sd = sd
                break
        if not primary_sd:
            primary_sd = site_data[0]
        auto_scores = primary_sd.get("automated_scores", {})

    total_score = 0.0
    total_max = 0.0
    completeness_html = ""

    for key, label in LENS_NAMES.items():
        if key in ("performance_technical_health", "seo_ai_visibility"):
            data = auto_scores.get(key, {})
            score = data.get("score")
        else:
            score = None
            for a in analyst_scores:
                if a.get("lens_name") == key and a.get("site_url") == primary_url:
                    sub = a.get("sub_scores", {})
                    if sub:
                        score = sum(float(v) for v in sub.values())
                    break

        is_complete = score is not None and score > 0
        if is_complete:
            icon = f'<span class="checklist-done">✓</span>'
            score_str = f'<span style="color:{COLORS["success"]}">{score:.1f}/20</span>'
            total_score += score
        else:
            icon = f'<span class="checklist-pending">○</span>'
            score_str = f'<span style="color:{COLORS["text_dim"]}">Not scored</span>'

        total_max += 20.0
        completeness_html += f"""
<div class="checklist-item">
  {icon}
  <span style="color:{COLORS['text']};flex:1;">{label}</span>
  {score_str}
</div>"""

    # Total row
    completeness_html += f"""
<div style="display:flex;justify-content:space-between;padding:0.75rem 0;margin-top:0.5rem;
            border-top:2px solid {COLORS['border']};">
  <span style="color:{COLORS['text']};font-weight:700;font-size:1.1rem;">Total Retina Score</span>
  <span style="color:{COLORS['accent']};font-weight:700;font-size:1.1rem;">{total_score:.1f}/{total_max:.0f}</span>
</div>"""

    st.markdown(
        f'<div class="retina-card">{completeness_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --- Export Actions ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Generate PDF Report")
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;'>"
            "Generate a full PDF report with all scores, charts, and analysis.</p>",
            unsafe_allow_html=True,
        )
        if project["status"] == "complete":
            if st.button("Generate PDF Report", type="primary", use_container_width=True):
                _generate_pdf(project)
        else:
            st.markdown(
                f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;font-style:italic;'>"
                "Run an analysis first to generate a PDF report.</p>",
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("##### Download JSON Data")
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;'>"
            "Download all project data as structured JSON.</p>",
            unsafe_allow_html=True,
        )
        export_data = {
            "project": {
                "name": project.get("name"),
                "primary_url": project.get("primary_url"),
                "competitor_urls": project.get("competitor_urls", []),
                "status": project.get("status"),
            },
            "site_data": site_data,
            "analyst_scores": analyst_scores,
            "reports": [
                {k: v for k, v in r.items() if k != "pdf_path"}
                for r in reports
            ],
        }
        st.download_button(
            "Download JSON",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"retina-{project.get('name', 'export').replace(' ', '-').lower()}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")

    # --- Previous Reports ---
    st.markdown("##### Previous Reports")
    if not reports:
        st.markdown(
            f"<p style='color:{COLORS['text_dim']};font-size:0.85rem;'>No reports generated yet.</p>",
            unsafe_allow_html=True,
        )
        return

    for report in reports:
        try:
            gen_at = datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
            date_str = gen_at.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, KeyError):
            date_str = "Unknown date"

        score = report.get("retina_score", 0)
        pdf_path = report.get("pdf_path")

        rc1, rc2, rc3 = st.columns([3, 1, 1])
        with rc1:
            st.markdown(f"**{date_str}**")
        with rc2:
            st.markdown(f"Score: **{score:.1f}**")
        with rc3:
            if pdf_path:
                st.markdown(f"[Download PDF]({pdf_path})")

        ai = report.get("ai_analysis", {})
        if ai and ai.get("executive_summary"):
            with st.expander("AI Analysis Summary"):
                st.markdown(ai["executive_summary"][:500])

        st.markdown("---")


def _generate_pdf(project: dict) -> None:
    """Trigger PDF report generation."""
    from app.services.pipeline import run_analysis_sync

    project_id = project["id"]
    primary_url = project["primary_url"]
    competitors = project.get("competitor_urls", [])

    progress_bar = st.progress(0, text="Generating report...")

    def progress_callback(msg: str) -> None:
        progress_bar.progress(0.5, text=msg)

    try:
        result = run_analysis_sync(
            project_id=project_id,
            primary_url=primary_url,
            competitor_urls=competitors,
            progress_callback=progress_callback,
        )
        progress_bar.progress(1.0, text="Complete!")
        st.success(f"Report generated! Score: {result['retina_score']:.1f}")
        if result.get("pdf_url"):
            st.markdown(f"[Download PDF]({result['pdf_url']})")
        st.rerun()
    except Exception as e:
        progress_bar.empty()
        st.error(f"Report generation failed: {e}")
