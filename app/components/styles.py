"""CSS styles for the Retina light theme — modern, minimal, card-based."""

COLORS = {
    "bg": "#F0F2F5",
    "bg_card": "#FFFFFF",
    "bg_hover": "#EDF0F7",
    "accent": "#076EFF",
    "accent_hover": "#0558CC",
    "accent_light": "#EBF2FF",
    "text": "#0A0A2E",
    "text_muted": "#6B7280",
    "text_dim": "#94A3B8",
    "success": "#00C864",
    "warning": "#FFC800",
    "error": "#FF4444",
    "border": "#E2E8F0",
    "shadow": "0 1px 4px rgba(0,0,0,0.06)",
}

LENS_COLORS = {
    "performance_technical_health": "#076EFF",
    "seo_ai_visibility": "#00C864",
    "brand_messaging": "#9B59B6",
    "experience_design": "#E74C3C",
    "conversion_strategy": "#FF8C00",
}

LENS_ICONS = {
    "performance_technical_health": "assets/performance_icon.svg",
    "seo_ai_visibility": "assets/seo_icon.svg",
    "brand_messaging": "assets/brand_icon.svg",
    "experience_design": "assets/experience_icon.svg",
    "conversion_strategy": "assets/conversion_icon.svg",
}

LENS_LABELS = {
    "performance_technical_health": "Performance & Platform",
    "seo_ai_visibility": "SEO & AI Visibility",
    "brand_messaging": "Brand & Messaging",
    "experience_design": "Experience & Design",
    "conversion_strategy": "Conversion & Strategy",
}

LENS_SHORT_LABELS = {
    "performance_technical_health": "Performance",
    "seo_ai_visibility": "SEO & AI",
    "brand_messaging": "Brand",
    "experience_design": "Experience",
    "conversion_strategy": "Conversion",
}

LENS_DEFINITIONS = {
    "performance_technical_health": "Speed, stability, code quality, and technical infrastructure.",
    "seo_ai_visibility": "Discoverability to search engines and AI-driven platforms.",
    "brand_messaging": "How clearly the website communicates who it's for and why it matters.",
    "experience_design": "Intuitiveness, modernity, and intentionality of the digital experience.",
    "conversion_strategy": "How effectively the site turns attention into action.",
}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a 6-char hex color to rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def inject_css() -> str:
    """Return the main CSS to inject via st.markdown."""
    return f"""
<style>
    /* ======== GLOBAL ======== */
    .stApp {{
        background-color: {COLORS['bg']};
    }}

    /* Hide default Streamlit chrome */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Global font smoothing */
    * {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    /* ======== SIDEBAR — Narrow icon rail ======== */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['bg_card']};
        border-right: 1px solid {COLORS['border']};
        width: 68px !important;
        min-width: 68px !important;
        max-width: 68px !important;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        width: 68px !important;
        padding: 0.75rem 0.5rem !important;
    }}

    /* Hide sidebar collapse/expand control */
    button[data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    /* Sidebar icon buttons */
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        border: none !important;
        color: {COLORS['text_muted']} !important;
        text-align: center !important;
        font-size: 1.25rem !important;
        padding: 0.5rem !important;
        border-radius: 12px !important;
        width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto 0.25rem auto !important;
        transition: all 0.15s !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {COLORS['bg_hover']} !important;
        color: {COLORS['text']} !important;
    }}

    /* Active sidebar button */
    section[data-testid="stSidebar"] .stButton > button.sidebar-active,
    section[data-testid="stSidebar"] .sidebar-active .stButton > button {{
        background: #1A1A2E !important;
        color: #FFFFFF !important;
    }}

    /* Sidebar logo */
    .sidebar-logo {{
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }}
    .sidebar-logo svg {{
        max-width: 36px;
        height: auto;
    }}

    /* Sidebar user avatar */
    .sidebar-avatar {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #1A1A2E;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
        margin: 0 auto;
        cursor: pointer;
    }}

    /* ======== CARDS ======== */
    .retina-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 1rem;
        box-shadow: {COLORS['shadow']};
        transition: border-color 0.2s, box-shadow 0.2s;
        border: none;
    }}
    .retina-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}

    /* Metric card */
    .metric-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: {COLORS['shadow']};
    }}
    .metric-card .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLORS['text']};
        line-height: 1.2;
    }}
    .metric-card .metric-label {{
        font-size: 0.85rem;
        color: {COLORS['text_muted']};
        margin-top: 0.25rem;
    }}

    /* Project card (dashboard) */
    .project-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 24px;
        box-shadow: {COLORS['shadow']};
        transition: box-shadow 0.2s;
        cursor: pointer;
        position: relative;
        min-height: 160px;
    }}
    .project-card:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }}
    .project-card .project-name {{
        font-weight: 700;
        font-size: 1.05rem;
        color: {COLORS['text']};
        margin-bottom: 4px;
    }}
    .project-card .project-url {{
        font-size: 0.8rem;
        color: {COLORS['text_muted']};
        margin-bottom: 12px;
    }}
    .project-card .project-score {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text']};
    }}
    .project-card .project-score-label {{
        font-size: 0.75rem;
        color: {COLORS['text_dim']};
    }}
    .project-card .project-arrow {{
        position: absolute;
        top: 20px;
        right: 20px;
        color: {COLORS['text_dim']};
        font-size: 1.1rem;
    }}

    /* Lens summary card */
    .lens-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: {COLORS['shadow']};
        margin-bottom: 0.5rem;
        border-top: 3px solid transparent;
        cursor: pointer;
        transition: box-shadow 0.2s;
    }}
    .lens-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .lens-card .lens-name {{
        font-weight: 600;
        font-size: 0.88rem;
        color: {COLORS['text']};
    }}
    .lens-card .lens-score {{
        font-weight: 700;
        font-size: 1.1rem;
        color: {COLORS['text']};
    }}
    .lens-card .lens-status {{
        font-size: 0.75rem;
        margin-top: 4px;
    }}

    /* Sub-dimension display card */
    .subdim-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: {COLORS['shadow']};
        margin-bottom: 0.75rem;
    }}
    .subdim-card .subdim-name {{
        font-weight: 600;
        font-size: 0.92rem;
        color: {COLORS['text']};
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .subdim-card .subdim-bar-track {{
        background: {COLORS['border']};
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
        margin-bottom: 6px;
    }}
    .subdim-card .subdim-bar-fill {{
        background: {COLORS['accent']};
        border-radius: 6px;
        height: 100%;
        transition: width 0.4s ease;
    }}
    .subdim-card .subdim-score {{
        font-weight: 700;
        font-size: 0.9rem;
        color: {COLORS['text']};
        text-align: right;
    }}
    .subdim-card .subdim-guidance {{
        font-size: 0.72rem;
        color: {COLORS['text_dim']};
        margin-top: 6px;
    }}
    .subdim-card .subdim-tooltip {{
        color: {COLORS['text_dim']};
        font-size: 0.8rem;
        cursor: help;
    }}

    /* ======== STATUS BADGES ======== */
    .badge {{
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .badge-draft {{
        background: {COLORS['bg_hover']};
        color: {COLORS['text_dim']};
    }}
    .badge-in_progress {{
        background: {COLORS['accent_light']};
        color: {COLORS['accent']};
    }}
    .badge-complete {{
        background: {hex_to_rgba(COLORS['success'], 0.12)};
        color: {COLORS['success']};
    }}

    /* ======== BUTTONS ======== */
    /* Primary — dark pill */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {{
        background-color: #1A1A2E !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.5rem 1.5rem !important;
        height: 40px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.2s !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {{
        background-color: #0A0A1E !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }}

    /* Secondary — white pill */
    .stButton > button[kind="secondary"],
    .stButton > button {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 999px !important;
        color: {COLORS['text_muted']} !important;
        font-weight: 500 !important;
        padding: 0.4rem 1.25rem !important;
        transition: all 0.2s !important;
    }}
    .stButton > button[kind="secondary"]:hover,
    .stButton > button:hover {{
        border-color: {COLORS['text_muted']} !important;
        color: {COLORS['text']} !important;
    }}

    /* ======== FORM INPUTS ======== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text']} !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['accent']} !important;
        box-shadow: 0 0 0 2px {hex_to_rgba(COLORS['accent'], 0.15)} !important;
    }}

    .stSelectbox > div > div {{
        background-color: {COLORS['bg_card']} !important;
        border-color: {COLORS['border']} !important;
        border-radius: 8px !important;
    }}

    /* ======== TABS ======== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: transparent;
        border-bottom: 2px solid {COLORS['border']};
        border-radius: 0;
        padding: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 0;
        padding: 10px 20px;
        color: {COLORS['text_muted']};
        font-weight: 500;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLORS['text']};
        background: transparent;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: transparent !important;
        color: {COLORS['text']} !important;
        font-weight: 600;
        border-bottom: 2px solid #1A1A2E !important;
    }}
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    /* ======== DIVIDERS ======== */
    hr {{
        border-color: {COLORS['border']} !important;
        margin: 1.5rem 0 !important;
    }}

    /* ======== TECH TAGS ======== */
    .tech-tags {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 0.5rem 0;
    }}

    /* ======== AUDIT SECTIONS ======== */
    .audit-section {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: {COLORS['shadow']};
    }}
    .audit-section-header {{
        padding: 0.75rem 1rem;
        background: #F8FAFC;
        font-size: 0.8rem;
        font-weight: 600;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid {COLORS['border']};
    }}

    /* ======== CHECKLIST ======== */
    .checklist-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .checklist-done {{
        color: {COLORS['success']};
        font-weight: 600;
    }}
    .checklist-pending {{
        color: {COLORS['text_dim']};
    }}

    /* ======== EXPANDERS ======== */
    .streamlit-expanderHeader {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text']} !important;
    }}

    /* ======== PROGRESS BAR ======== */
    .stProgress > div > div > div > div {{
        background-color: {COLORS['accent']} !important;
    }}

    /* ======== DOWNLOAD BUTTON ======== */
    .stDownloadButton > button {{
        border: 1px solid {COLORS['border']} !important;
        background: {COLORS['bg_card']} !important;
        color: {COLORS['text_muted']} !important;
        border-radius: 999px !important;
    }}
    .stDownloadButton > button:hover {{
        border-color: {COLORS['text_muted']} !important;
        color: {COLORS['text']} !important;
    }}

    /* ======== FOOTER ======== */
    .retina-footer {{
        text-align: center;
        padding: 1.5rem 0;
        margin-top: 3rem;
        border-top: 1px solid {COLORS['border']};
    }}
    .retina-footer svg {{
        height: 18px;
        vertical-align: middle;
        margin-left: 6px;
        opacity: 0.6;
    }}
    .retina-footer span {{
        color: {COLORS['text_dim']};
        font-size: 0.78rem;
    }}

    /* ======== COPILOT PLACEHOLDER ======== */
    .copilot-bar {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 2rem;
    }}
    .copilot-bar input {{
        flex: 1;
        border: none;
        outline: none;
        font-size: 0.9rem;
        color: {COLORS['text_dim']};
        background: transparent;
    }}
    .copilot-label {{
        font-size: 0.75rem;
        color: {COLORS['text_dim']};
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .copilot-badge {{
        background: {COLORS['bg_hover']};
        color: {COLORS['text_dim']};
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    /* ======== QUICK START PANEL ======== */
    .quick-start-step {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 0;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .quick-start-step:last-child {{
        border-bottom: none;
    }}
    .quick-start-num {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: {COLORS['bg_hover']};
        color: {COLORS['text']};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.8rem;
        flex-shrink: 0;
    }}
    .quick-start-title {{
        font-weight: 600;
        font-size: 0.88rem;
        color: {COLORS['text']};
    }}
    .quick-start-desc {{
        font-size: 0.8rem;
        color: {COLORS['text_muted']};
        margin-top: 2px;
    }}
</style>
"""


def status_badge(status: str) -> str:
    """Return HTML for a status badge."""
    labels = {
        "draft": "Draft",
        "in_progress": "In Progress",
        "complete": "Complete",
    }
    label = labels.get(status, status.title())
    return f'<span class="badge badge-{status}">{label}</span>'


def metric_card(value: str, label: str) -> str:
    """Return HTML for a metric display card."""
    return f"""
<div class="metric-card">
    <div class="metric-value">{value}</div>
    <div class="metric-label">{label}</div>
</div>
"""
