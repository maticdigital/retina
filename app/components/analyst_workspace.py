"""Shared analyst scoring workspace — display-only cards, observations, screenshots, auto-save, AI re-evaluate."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
from typing import Any

import streamlit as st

from app.components.score_display import (
    lens_donut_svg,
    save_indicator,
    subdim_card_html,
)
from app.components.styles import COLORS, LENS_COLORS, LENS_DEFINITIONS as STYLE_LENS_DEFS
from app.services.projects import upsert_analyst_score
from app.services.storage import upload_screenshot

logger = logging.getLogger(__name__)

# Human-readable labels for sub-dimensions
DIMENSION_LABELS = {
    "brand_visual_language": "Brand Visual Language",
    "brand_voice_messaging": "Brand Voice & Messaging",
    "value_proposition": "Value Proposition",
    "brand_differentiation": "Brand Differentiation",
    "interface_design": "Interface Design",
    "content_taxonomy": "Content Taxonomy",
    "navigation_architecture": "Navigation Architecture",
    "responsiveness": "Responsiveness",
    "call_to_action_logic": "Call to Action Logic",
    "lead_capture_form_design": "Lead Capture Form Design",
    "trust_signals": "Trust Signals",
    "funnel_design": "Funnel Design",
}

LENS_DISPLAY_NAMES = {
    "brand_messaging": "Brand & Messaging",
    "experience_design": "Experience & Design",
    "conversion_strategy": "Conversion & Strategy",
}

# Guidance text for each sub-dimension score range
DIMENSION_GUIDANCE = {
    5.0: "4-5: Best in class · 3-3.5: Solid · 1.5-2.5: Notable gaps · 0.5-1: Critical",
}

# Placeholder guidance for observation text areas
OBSERVATION_PLACEHOLDERS = {
    "brand_messaging": (
        "How clearly does the website communicate who it is for, what it offers, "
        "and why it matters?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• Brand visual language — is the visual identity cohesive across all pages?\n"
        "• Brand voice & messaging — does the tone speak to the right audience?\n"
        "• Value proposition — is it immediately obvious what the company does "
        "and who it serves?\n"
        "• Brand differentiation — does the site stand apart from competitors?\n\n"
        "Connect every finding to business impact: visitor confidence, conversion likelihood, "
        "competitive positioning."
    ),
    "experience_design": (
        "How intuitive, modern, and intentional does the website feel — from navigation "
        "and layout to visual hierarchy and mobile responsiveness?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• Interface design — does the site feel current and polished?\n"
        "• Content taxonomy — is content organized with clear categories and hierarchy?\n"
        "• Navigation architecture — can visitors find what they need within 2-3 clicks?\n"
        "• Responsiveness — does the site deliver a first-class experience across devices?\n\n"
        "Frame observations in terms of visitor engagement, time-on-site, "
        "and the likelihood visitors take action."
    ),
    "conversion_strategy": (
        "How effectively does the website turn attention into action through clear CTAs, "
        "logical user paths, and trust-building content?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• Call to action logic — are CTAs clear, compelling, and strategically "
        "placed where visitor intent is highest?\n"
        "• Lead capture form design — are forms optimized for completion?\n"
        "• Trust signals — does the site establish credibility through social proof, "
        "case studies, testimonials, and certifications?\n"
        "• Funnel design — does the path from awareness to conversion feel natural?\n\n"
        "Frame every finding in terms of conversion rate impact and revenue opportunity."
    ),
}


def _guidance_for_max(max_val: float) -> str:
    """Return human-readable score range guidance for a sub-dimension."""
    if max_val >= 5.0:
        return DIMENSION_GUIDANCE[5.0]
    elif max_val >= 4.0:
        return DIMENSION_GUIDANCE[4.0]
    else:
        return DIMENSION_GUIDANCE[3.0]


def render_analyst_lens(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_dimensions: dict[str, float],
    existing_data: dict[str, Any] | None,
    site_data: dict | None = None,
) -> None:
    """Render the full analyst scoring workspace for one lens.

    Sub-dimension scores are display-only — set exclusively by the AI
    re-evaluate feature, not by manual analyst input.

    Args:
        project_id: Supabase project ID.
        site_url: URL being scored.
        lens_name: e.g. "brand_messaging".
        sub_dimensions: Dict of dim_key -> max_score from LENS_DEFINITIONS.
        existing_data: Previously saved analyst_scores row, or None.
        site_data: Optional site analysis data dict for AI re-evaluation.
    """
    display_name = LENS_DISPLAY_NAMES.get(lens_name, lens_name)
    max_total = sum(sub_dimensions.values())
    lens_color = LENS_COLORS.get(lens_name, COLORS["accent"])

    # Load existing data into session state on first load
    _init_session_state(lens_name, sub_dimensions, existing_data)

    # --- Running Score ---
    current_scores = {}
    for dim_key in sub_dimensions:
        sk = f"analyst_{lens_name}_{dim_key}"
        current_scores[dim_key] = st.session_state.get(sk, 0.0)

    running_total = sum(current_scores.values())

    # --- Header Row: Lens donut + site label + AI button ---
    hdr_left, hdr_right = st.columns([3, 1])

    with hdr_left:
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;margin-bottom:0.25rem;'>"
            f"Scoring <strong style='color:{COLORS['text']};'>{site_url}</strong></p>",
            unsafe_allow_html=True,
        )
        # Save indicator
        save_status = st.session_state.get(f"_save_status_{lens_name}", "saved")
        st.markdown(save_indicator(save_status), unsafe_allow_html=True)

    with hdr_right:
        st.markdown(
            lens_donut_svg(running_total, max_total, lens_color, size=100),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # --- AI Re-evaluate Button ---
    if site_data:
        btn_col, _ = st.columns([1, 3])
        with btn_col:
            if st.button(
                "Re-evaluate with AI",
                key=f"re_eval_{lens_name}",
                type="primary",
                use_container_width=True,
                help="Use Claude AI to generate fresh scores and observations based on the site's data.",
            ):
                _re_evaluate_with_ai(
                    project_id, site_url, lens_name, sub_dimensions, site_data,
                )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- Sub-Dimension Display Cards (read-only) ---
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.82rem;font-weight:500;"
        f"margin-bottom:0.75rem;'>Sub-Dimensions</p>",
        unsafe_allow_html=True,
    )

    for dim_key, max_val in sub_dimensions.items():
        label = DIMENSION_LABELS.get(dim_key, dim_key.replace("_", " ").title())
        score = current_scores.get(dim_key, 0.0)
        guidance = _guidance_for_max(max_val)
        tooltip = f"Score out of {max_val:.0f}"
        st.markdown(
            subdim_card_html(label, score, max_val, guidance, tooltip),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- Observations ---
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.82rem;font-weight:500;"
        f"margin-bottom:0.5rem;'>Observations</p>",
        unsafe_allow_html=True,
    )

    placeholder = OBSERVATION_PLACEHOLDERS.get(
        lens_name,
        "Write your stream-of-consciousness analysis notes here...",
    )
    obs_key = f"analyst_{lens_name}_observations"
    st.text_area(
        "Raw observations and notes",
        key=obs_key,
        height=200,
        placeholder=placeholder,
        label_visibility="collapsed",
    )

    # --- Screenshot Upload ---
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.82rem;font-weight:500;"
        f"margin-bottom:0.5rem;margin-top:1rem;'>Supporting Screenshots</p>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload screenshot evidence",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"upload_{lens_name}",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # Show existing screenshots
    screenshots_key = f"_screenshots_{lens_name}"
    existing_screenshots = st.session_state.get(screenshots_key, [])

    if uploaded:
        for uf in uploaded:
            try:
                with tempfile.NamedTemporaryFile(suffix=f".{uf.name.split('.')[-1]}", delete=False) as tmp:
                    tmp.write(uf.getbuffer())
                    tmp_path = tmp.name
                url = upload_screenshot(tmp_path, project_id)
                os.unlink(tmp_path)
                if url not in existing_screenshots:
                    existing_screenshots.append(url)
                    st.session_state[screenshots_key] = existing_screenshots
            except Exception as e:
                st.warning(f"Screenshot upload failed: {e}")

    if existing_screenshots:
        cols = st.columns(min(len(existing_screenshots), 4))
        for i, ss_url in enumerate(existing_screenshots):
            with cols[i % 4]:
                st.image(ss_url, use_container_width=True)

    # --- Auto-save ---
    _auto_save(project_id, site_url, lens_name, sub_dimensions, existing_screenshots)


def _init_session_state(
    lens_name: str,
    sub_dimensions: dict[str, float],
    existing_data: dict[str, Any] | None,
) -> None:
    """Initialize session state from existing Supabase data (once)."""
    loaded_key = f"_loaded_{lens_name}"
    if st.session_state.get(loaded_key):
        return

    if existing_data:
        saved_scores = existing_data.get("sub_scores", {})
        for dim_key in sub_dimensions:
            sk = f"analyst_{lens_name}_{dim_key}"
            st.session_state[sk] = float(saved_scores.get(dim_key, 0.0))

        obs = existing_data.get("raw_observations", "")
        st.session_state[f"analyst_{lens_name}_observations"] = obs or ""

        screenshots = existing_data.get("screenshots", [])
        st.session_state[f"_screenshots_{lens_name}"] = screenshots or []

        st.session_state[f"_saved_{lens_name}"] = {
            "scores": {k: float(saved_scores.get(k, 0.0)) for k in sub_dimensions},
            "observations": obs or "",
        }
    else:
        for dim_key in sub_dimensions:
            sk = f"analyst_{lens_name}_{dim_key}"
            if sk not in st.session_state:
                st.session_state[sk] = 0.0

        obs_key = f"analyst_{lens_name}_observations"
        if obs_key not in st.session_state:
            st.session_state[obs_key] = ""

        if f"_screenshots_{lens_name}" not in st.session_state:
            st.session_state[f"_screenshots_{lens_name}"] = []

        st.session_state[f"_saved_{lens_name}"] = {
            "scores": {k: 0.0 for k in sub_dimensions},
            "observations": "",
        }

    st.session_state[loaded_key] = True
    st.session_state[f"_save_status_{lens_name}"] = "saved"


def _auto_save(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_dimensions: dict[str, float],
    screenshots: list[str],
) -> None:
    """Check if values changed and auto-save to Supabase."""
    current_scores = {}
    for dim_key in sub_dimensions:
        sk = f"analyst_{lens_name}_{dim_key}"
        current_scores[dim_key] = st.session_state.get(sk, 0.0)

    observations = st.session_state.get(f"analyst_{lens_name}_observations", "")

    saved_key = f"_saved_{lens_name}"
    saved = st.session_state.get(saved_key, {})

    scores_changed = current_scores != saved.get("scores", {})
    obs_changed = observations != saved.get("observations", "")

    if not scores_changed and not obs_changed:
        return

    # Debounce — at least 1 second between saves
    now = time.time()
    last_save = st.session_state.get("_last_save_time", 0)
    if now - last_save < 1.0:
        st.session_state[f"_save_status_{lens_name}"] = "saving"
        return

    try:
        upsert_analyst_score(
            project_id=project_id,
            site_url=site_url,
            lens_name=lens_name,
            sub_scores=current_scores,
            raw_observations=observations,
            screenshots=screenshots,
        )
        st.session_state[saved_key] = {
            "scores": current_scores.copy(),
            "observations": observations,
        }
        st.session_state["_last_save_time"] = now
        st.session_state[f"_save_status_{lens_name}"] = "saved"
    except Exception as e:
        st.session_state[f"_save_status_{lens_name}"] = "saving"


def _re_evaluate_with_ai(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_dimensions: dict[str, float],
    site_data: dict,
) -> None:
    """Re-evaluate a single lens using the AI analyst seeder."""
    # Add src to path for retina imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

    try:
        from retina.analysis.analyst_seeder import AnalystLensSeeder
        from retina.config import Settings

        settings = Settings()
        if not settings.anthropic_api_key:
            st.warning("Anthropic API key not configured. AI re-evaluation unavailable.")
            return

        with st.spinner(f"AI is re-evaluating {LENS_DISPLAY_NAMES.get(lens_name, lens_name)}..."):
            seeder = AnalystLensSeeder(settings)

            # Build input data from site_data
            lh_data = site_data.get("lighthouse_data", {})
            bw_data = site_data.get("builtwith_data", {})
            auto_scores = site_data.get("automated_scores", {})
            ss_paths = site_data.get("screenshot_paths", {})

            result = seeder.seed(
                site_url=site_url,
                lighthouse_data=lh_data,
                builtwith_data=bw_data,
                screenshot_paths=ss_paths,
                automated_scores=auto_scores,
            )

        lens_result = result.get(lens_name, {})
        if not lens_result:
            st.warning("AI evaluation did not return results for this lens. Try again.")
            return

        # Update session state with new scores
        new_scores = lens_result.get("sub_scores", {})
        for dim_key in sub_dimensions:
            sk = f"analyst_{lens_name}_{dim_key}"
            if dim_key in new_scores:
                st.session_state[sk] = float(new_scores[dim_key])

        # Update observations
        new_obs = lens_result.get("observations", "")
        if new_obs:
            st.session_state[f"analyst_{lens_name}_observations"] = new_obs

        # Mark as needing save
        st.session_state[f"_save_status_{lens_name}"] = "saving"

        # Force re-init on next render
        loaded_key = f"_loaded_{lens_name}"
        if loaded_key in st.session_state:
            del st.session_state[loaded_key]

        st.success("AI re-evaluation complete. Scores and observations updated.")
        st.rerun()

    except Exception as e:
        logger.exception("AI re-evaluation failed for %s", lens_name)
        st.error(f"AI re-evaluation failed: {e}")
