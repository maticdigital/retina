"""Shared analyst scoring workspace — sliders, observations, screenshots, auto-save, AI re-evaluate."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
from typing import Any

import streamlit as st

from app.components.score_display import progress_bar_html, save_indicator, score_ring_html
from app.components.styles import COLORS, hex_to_rgba
from app.services.projects import upsert_analyst_score
from app.services.storage import upload_screenshot

logger = logging.getLogger(__name__)

# Human-readable labels for sub-dimensions
DIMENSION_LABELS = {
    "brand_clarity_consistency": "Brand Clarity & Consistency",
    "value_proposition_strength": "Value Proposition Strength",
    "content_quality_tone": "Content Quality & Tone",
    "visual_identity_differentiation": "Visual Identity & Differentiation",
    "visual_design_quality": "Visual Design Quality",
    "navigation_information_architecture": "Navigation & Information Architecture",
    "interaction_design_micro_interactions": "Interaction Design & Micro-interactions",
    "responsiveness_cross_device": "Responsiveness & Cross-Device",
    "content_layout_readability": "Content Layout & Readability",
    "cta_effectiveness": "CTA Effectiveness",
    "user_journey_funnel_design": "User Journey & Funnel Design",
    "trust_signals_social_proof": "Trust Signals & Social Proof",
    "lead_capture_form_design": "Lead Capture & Form Design",
    "strategic_positioning_vs_competitors": "Strategic Positioning vs Competitors",
}

LENS_DISPLAY_NAMES = {
    "brand_messaging": "Brand & Messaging",
    "experience_design": "Experience & Design",
    "conversion_strategy": "Conversion & Strategy",
}

# Placeholder guidance for observation text areas
OBSERVATION_PLACEHOLDERS = {
    "brand_messaging": (
        "How clearly does the website communicate who it is for, what it offers, "
        "and why it matters?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• Value proposition clarity — is it immediately obvious what the company does "
        "and who it serves?\n"
        "• Brand consistency — does the visual identity and tone feel cohesive across pages?\n"
        "• Content quality — does messaging speak to buyer outcomes, or focus inward "
        "on features and capabilities?\n"
        "• Competitive differentiation — does the site stand apart from competitors, "
        "or could this brand be swapped for any peer?\n\n"
        "Connect every finding to business impact: visitor confidence, conversion likelihood, "
        "competitive positioning."
    ),
    "experience_design": (
        "How intuitive, modern, and intentional does the website feel — from navigation "
        "and layout to visual hierarchy and mobile responsiveness?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• Visual design quality — does the site feel current, or does it signal "
        "an outdated digital presence?\n"
        "• Navigation & information architecture — can visitors find what they need "
        "without friction?\n"
        "• Mobile experience — does the site deliver a first-class experience on the "
        "devices most visitors use?\n"
        "• Interaction design — do micro-interactions and transitions reinforce "
        "quality and guide attention?\n\n"
        "Frame observations in terms of visitor engagement, time-on-site, "
        "and the likelihood visitors take action."
    ),
    "conversion_strategy": (
        "How effectively does the website turn attention into action through clear CTAs, "
        "logical user paths, and trust-building content?\n\n"
        "Start with what works — then identify where gaps create opportunity:\n"
        "• CTA effectiveness — are calls-to-action clear, compelling, and strategically "
        "placed where visitor intent is highest?\n"
        "• User journey design — does the path from landing to conversion feel natural, "
        "or does it create unnecessary friction?\n"
        "• Trust signals — does the site establish credibility through social proof, "
        "case studies, testimonials, and security indicators?\n"
        "• Lead capture — are forms optimized for completion, and does the site "
        "offer value before asking for information?\n\n"
        "Frame every finding in terms of conversion rate impact and revenue opportunity."
    ),
}


def render_analyst_lens(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_dimensions: dict[str, float],
    existing_data: dict[str, Any] | None,
    site_data: dict | None = None,
) -> None:
    """Render the full analyst scoring workspace for one lens.

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

    # Load existing data into session state on first load
    _init_session_state(lens_name, sub_dimensions, existing_data)

    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;'>"
        f"Scoring <strong style='color:{COLORS['text']};'>{site_url}</strong></p>",
        unsafe_allow_html=True,
    )

    # --- Running Score ---
    current_scores = {}
    for dim_key in sub_dimensions:
        sk = f"analyst_{lens_name}_{dim_key}"
        current_scores[dim_key] = st.session_state.get(sk, 0.0)

    running_total = sum(current_scores.values())

    col_score, col_sliders = st.columns([1, 3])

    with col_score:
        st.markdown(
            score_ring_html(running_total, max_total, size=140, label=display_name),
            unsafe_allow_html=True,
        )
        # Save indicator
        save_status = st.session_state.get(f"_save_status_{lens_name}", "saved")
        st.markdown(save_indicator(save_status), unsafe_allow_html=True)

        # Re-evaluate with AI button
        if site_data:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if st.button(
                "Re-evaluate with AI",
                key=f"re_eval_{lens_name}",
                help="Use Claude AI to generate fresh scores and observations based on the site's data.",
            ):
                _re_evaluate_with_ai(
                    project_id, site_url, lens_name, sub_dimensions, site_data,
                )

    with col_sliders:
        st.markdown(
            '<div class="workspace-section"><h4>Sub-Dimensions</h4>',
            unsafe_allow_html=True,
        )
        for dim_key, max_val in sub_dimensions.items():
            label = DIMENSION_LABELS.get(dim_key, dim_key.replace("_", " ").title())
            sk = f"analyst_{lens_name}_{dim_key}"
            step = 0.5
            st.slider(
                label,
                min_value=0.0,
                max_value=max_val,
                step=step,
                key=sk,
                help=f"Score out of {max_val:.0f}",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Score breakdown bars ---
    st.markdown(
        '<div class="workspace-section"><h4>Score Breakdown</h4>',
        unsafe_allow_html=True,
    )
    for dim_key, max_val in sub_dimensions.items():
        label = DIMENSION_LABELS.get(dim_key, dim_key.replace("_", " ").title())
        val = current_scores.get(dim_key, 0)
        st.markdown(progress_bar_html(val, max_val, label), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Observations ---
    st.markdown(
        '<div class="workspace-section"><h4>Observations</h4>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

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
    )

    # --- Screenshot Upload ---
    st.markdown(
        '<div class="workspace-section"><h4>Supporting Screenshots</h4>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload screenshot evidence",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"upload_{lens_name}",
        accept_multiple_files=True,
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
