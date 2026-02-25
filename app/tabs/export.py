"""Export tab — PDF generation, JSON download, report completeness preview."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.components.explanations import get_interpretation, interpretation_html
from app.components.styles import COLORS

LENS_NAMES = {
    "performance_technical_health": "Performance & Platform",
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

    # --- Report Summary ---
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1.1rem;font-weight:600;"
        f"margin-bottom:0.5rem;'>Report Summary</p>",
        unsafe_allow_html=True,
    )

    # Project info card
    competitors = project.get("competitor_urls", [])
    comp_text = f"{len(competitors)} competitor{'s' if len(competitors) != 1 else ''}" if competitors else "No competitors"
    user = st.session_state.get("user", {})
    analyst_name = user.get("name", "Unknown")

    st.markdown(
        f"<div class='retina-card'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:8px;'>"
        f"<span style='color:{COLORS['text']};font-weight:600;'>{project.get('name', 'Untitled')}</span>"
        f"<span style='color:{COLORS['text_muted']};font-size:0.82rem;'>{comp_text}</span></div>"
        f"<div style='color:{COLORS['text_muted']};font-size:0.85rem;margin-bottom:4px;'>"
        f"{project.get('primary_url', '')}</div>"
        f"<div style='color:{COLORS['text_dim']};font-size:0.78rem;'>Analyst: {analyst_name}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- Completeness Checklist ---
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.5rem;'>Report Completeness</p>",
        unsafe_allow_html=True,
    )

    primary_url = project.get("primary_url", "")
    auto_scores = {}
    primary_sd = None
    if site_data:
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
            icon = f'<span style="color:{COLORS["success"]};font-weight:700;">✓</span>'
            score_str = f'<span style="color:{COLORS["success"]};font-weight:600;">{score:.1f}/20</span>'
            total_score += score
        else:
            icon = f'<span style="color:{COLORS["text_dim"]};">○</span>'
            score_str = f'<span style="color:{COLORS["text_dim"]};">Not scored</span>'

        total_max += 20.0
        completeness_html += f"""
<div style="display:flex;align-items:center;gap:10px;padding:10px 0;
            border-bottom:1px solid {COLORS['border']};">
  {icon}
  <span style="color:{COLORS['text']};flex:1;font-size:0.88rem;">{label}</span>
  {score_str}
</div>"""

    # Show interpretation of overall score if available
    interp = primary_sd.get("interpretations") or {} if primary_sd else {}
    score_interp = get_interpretation(interp, "overall.retina_score")
    score_interp_html = ""
    if score_interp and score_interp.get("what"):
        score_interp_html = (
            f"<div style='color:{COLORS['text_muted']};font-size:0.82rem;margin-top:6px;'>"
            f"{score_interp['what']}</div>"
        )

    # Total row
    completeness_html += f"""
<div style="display:flex;flex-direction:column;padding:0.75rem 0;margin-top:0.5rem;
            border-top:2px solid {COLORS['border']};">
  <div style="display:flex;justify-content:space-between;">
    <span style="color:{COLORS['text']};font-weight:700;font-size:1.1rem;">Total Retina Score</span>
    <span style="color:{COLORS['accent']};font-weight:700;font-size:1.1rem;">{total_score:.1f}/{total_max:.0f}</span>
  </div>
  {score_interp_html}
</div>"""

    st.markdown(
        f'<div class="retina-card">{completeness_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # --- Export Actions ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
            f"margin-bottom:0.25rem;'>Generate PDF Report</p>"
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;margin-bottom:0.75rem;'>"
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
        st.markdown(
            f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
            f"margin-bottom:0.25rem;'>Download JSON Data</p>"
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;margin-bottom:0.75rem;'>"
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

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # --- Previous Reports ---
    st.markdown(
        f"<p style='color:{COLORS['text']};font-size:1rem;font-weight:600;"
        f"margin-bottom:0.5rem;'>Previous Reports</p>",
        unsafe_allow_html=True,
    )
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

        st.markdown(
            f"<div class='retina-card' style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<div>"
            f"<div style='color:{COLORS['text']};font-weight:600;font-size:0.88rem;'>{date_str}</div>"
            f"<div style='color:{COLORS['text_muted']};font-size:0.82rem;'>Score: {score:.1f}/100</div>"
            f"</div>"
            + (f"<a href='{pdf_path}' style='color:{COLORS['accent']};font-size:0.85rem;"
               f"text-decoration:none;font-weight:600;'>Download PDF →</a>" if pdf_path else "")
            + f"</div>",
            unsafe_allow_html=True,
        )

        ai = report.get("ai_analysis", {})
        if ai and ai.get("executive_summary"):
            with st.expander("AI Analysis Summary"):
                st.markdown(ai["executive_summary"][:500])


def _generate_pdf(project: dict) -> None:
    """Trigger PDF report generation with step-by-step progress."""
    from app.services.pipeline import run_analysis_sync

    project_id = project["id"]
    primary_url = project["primary_url"]
    competitors = project.get("competitor_urls", [])

    # Step-by-step progress display
    steps_container = st.empty()
    steps_done: list[str] = []
    current_step = ""

    def _render_steps():
        html = "<div class='retina-card'>"
        for s in steps_done:
            html += (
                f"<div style='padding:6px 0;color:{COLORS['success']};font-size:0.85rem;'>"
                f"✓ {s}</div>"
            )
        if current_step:
            html += (
                f"<div style='padding:6px 0;color:{COLORS['accent']};font-size:0.85rem;'>"
                f"⟳ {current_step}</div>"
            )
        html += "</div>"
        steps_container.markdown(html, unsafe_allow_html=True)

    def progress_callback(msg: str) -> None:
        nonlocal current_step
        if current_step:
            steps_done.append(current_step)
        current_step = msg
        _render_steps()

    try:
        result = run_analysis_sync(
            project_id=project_id,
            primary_url=primary_url,
            competitor_urls=competitors,
            progress_callback=progress_callback,
        )
        if current_step:
            steps_done.append(current_step)
        current_step = ""
        _render_steps()

        st.success(f"Report generated! Score: {result['retina_score']:.1f}")
        if result.get("pdf_url"):
            st.markdown(f"[Download PDF]({result['pdf_url']})")
        st.rerun()
    except ImportError as e:
        steps_container.empty()
        if "weasyprint" in str(e).lower():
            st.error(
                "PDF generation requires WeasyPrint. Install it with: "
                "`pip install weasyprint`"
            )
        else:
            st.error(f"Report generation failed: {e}")
    except Exception as e:
        steps_container.empty()
        st.error(f"Report generation failed: {e}")
