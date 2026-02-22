"""CSS styles for the Retina light theme — modern, minimal, card-based."""

COLORS = {
    "bg": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "bg_hover": "#EDF0F7",
    "accent": "#076EFF",
    "accent_hover": "#0558CC",
    "accent_light": "#EBF2FF",
    "text": "#0A0A2E",
    "text_muted": "#4A5568",
    "text_dim": "#94A3B8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "border": "#E2E8F0",
    "shadow": "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a 6-char hex color to rgba() string.

    Example: hex_to_rgba('#076EFF', 0.13) -> 'rgba(7, 110, 255, 0.13)'
    """
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

    /* ======== SIDEBAR ======== */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['bg_card']};
        border-right: 1px solid {COLORS['border']};
    }}

    section[data-testid="stSidebar"] .stMarkdown h1 {{
        font-size: 1rem;
        letter-spacing: 0.05em;
        color: {COLORS['text_dim']};
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}

    /* Sidebar buttons — ghost style */
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        border: none !important;
        color: {COLORS['text_muted']} !important;
        text-align: left !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.15s !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {COLORS['bg_hover']} !important;
        color: {COLORS['text']} !important;
    }}

    /* ======== CARDS ======== */
    .retina-card {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: {COLORS['shadow']};
        transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .retina-card:hover {{
        border-color: {hex_to_rgba(COLORS['accent'], 0.3)};
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}

    /* Metric card */
    .metric-card {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem;
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

    /* ======== STATUS BADGES ======== */
    .badge {{
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
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
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
        border: 1px solid {COLORS['border']};
    }}
    /* Primary buttons */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {{
        background-color: {COLORS['accent']} !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0 1px 2px rgba(7, 110, 255, 0.2) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {{
        background-color: {COLORS['accent_hover']} !important;
        box-shadow: 0 2px 8px rgba(7, 110, 255, 0.3) !important;
    }}
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        color: {COLORS['text_muted']} !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: {COLORS['bg_hover']} !important;
        border-color: {COLORS['accent']} !important;
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

    /* Select boxes */
    .stSelectbox > div > div {{
        background-color: {COLORS['bg_card']} !important;
        border-color: {COLORS['border']} !important;
        border-radius: 8px !important;
    }}

    /* ======== TABS ======== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: {COLORS['bg']};
        border-radius: 10px;
        padding: 4px;
        border: 1px solid {COLORS['border']};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 8px 16px;
        color: {COLORS['text_muted']};
        font-weight: 500;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLORS['text']};
        background: {COLORS['bg_hover']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['accent']} !important;
        color: #FFFFFF !important;
        font-weight: 600;
    }}
    /* Remove default tab underline */
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    /* ======== PROJECT LIST ROW ======== */
    .project-row {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: {COLORS['shadow']};
    }}
    .project-row:hover {{
        border-color: {COLORS['accent']};
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}

    /* ======== DIVIDERS ======== */
    hr {{
        border-color: {COLORS['border']} !important;
        margin: 1.5rem 0 !important;
    }}

    /* ======== LOGO ======== */
    .sidebar-logo {{
        padding: 1rem 0 1.5rem 0;
        text-align: center;
    }}
    .sidebar-logo svg {{
        max-width: 160px;
        height: auto;
    }}

    /* ======== NAV ITEMS ======== */
    .nav-item {{
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.25rem;
        cursor: pointer;
        color: {COLORS['text_muted']};
        transition: all 0.15s;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .nav-item:hover {{
        background: {COLORS['bg_hover']};
        color: {COLORS['text']};
    }}
    .nav-item.active {{
        background: {COLORS['accent_light']};
        color: {COLORS['accent']};
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
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
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

    /* ======== SLIDER LABELS ======== */
    .stSlider label {{
        color: {COLORS['text']} !important;
    }}

    /* ======== ANALYST WORKSPACE ======== */
    .workspace-section {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: {COLORS['shadow']};
    }}
    .workspace-section h4 {{
        color: {COLORS['text_dim']};
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
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
        border-radius: 8px !important;
    }}
    .stDownloadButton > button:hover {{
        border-color: {COLORS['accent']} !important;
        color: {COLORS['accent']} !important;
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
