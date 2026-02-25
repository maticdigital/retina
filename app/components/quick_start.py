"""Quick Start onboarding panel — 5-step getting started guide."""

from __future__ import annotations

import streamlit as st

from app.components.styles import COLORS


QUICK_START_STEPS = [
    ("1", "Create a new analysis", "Enter the primary URL and up to 3 competitor URLs."),
    ("2", "Run data collection", "Performance and SEO scores generate automatically."),
    ("3", "Score the analyst lenses", "Brand, Experience, and Conversion need your input."),
    ("4", "Review AI observations", "Refine with AI or write your own analysis."),
    ("5", "Export the PDF report", "Generate a branded report for your client."),
]


def render_quick_start_panel() -> None:
    """Render the Quick Start panel (triggered by ? icon in sidebar).

    Displays as a container in the main content area with the 5-step
    getting started checklist and a dismiss button.
    """
    st.markdown(
        f"<div class='retina-card' style='max-width:640px;margin:0 auto 2rem;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;'>"
        f"<h3 style='color:{COLORS['text']};font-size:1.1rem;margin:0;'>Getting Started with Retina</h3>"
        f"<span style='color:{COLORS['text_dim']};font-size:0.75rem;'>Quick Start Guide</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    steps_html = ""
    for num, title, desc in QUICK_START_STEPS:
        steps_html += f"""
<div class="quick-start-step">
  <div class="quick-start-num">{num}</div>
  <div>
    <div class="quick-start-title">{title}</div>
    <div class="quick-start-desc">{desc}</div>
  </div>
</div>"""

    st.markdown(steps_html + "</div>", unsafe_allow_html=True)

    if st.button("Got it", type="primary", key="dismiss_quick_start"):
        st.session_state["show_quick_start"] = False
        st.rerun()


def render_quick_start_inline() -> None:
    """Render the inline Quick Start steps (for empty dashboard state).

    Same 5 steps but rendered directly in the main content without
    a dismiss button.
    """
    st.markdown(
        f"<div class='retina-card' style='max-width:600px;margin:0 auto 2rem;'>"
        f"<h4 style='color:{COLORS['text']};font-size:1rem;margin-bottom:1rem;'>"
        f"Getting Started with Retina</h4>",
        unsafe_allow_html=True,
    )

    steps_html = ""
    for num, title, desc in QUICK_START_STEPS:
        steps_html += f"""
<div class="quick-start-step">
  <div class="quick-start-num">{num}</div>
  <div>
    <div class="quick-start-title">{title}</div>
    <div class="quick-start-desc">{desc}</div>
  </div>
</div>"""

    st.markdown(steps_html + "</div>", unsafe_allow_html=True)
