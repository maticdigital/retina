"""CSS styles for the Retina dark theme."""

COLORS = {
    "bg": "#000227",
    "bg_card": "#0a0f3a",
    "bg_hover": "#111852",
    "accent": "#076EFF",
    "accent_hover": "#0858cc",
    "text": "#FFFFFF",
    "text_muted": "#8b92b3",
    "text_dim": "#5a6180",
    "success": "#00d68f",
    "warning": "#ffaa00",
    "error": "#ff3d71",
    "border": "#1a2055",
}


def inject_css() -> str:
    """Return the main CSS to inject via st.markdown."""
    return f"""
<style>
    /* Global overrides */
    .stApp {{
        background-color: {COLORS['bg']};
    }}

    /* Hide default Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['bg_card']};
        border-right: 1px solid {COLORS['border']};
    }}

    section[data-testid="stSidebar"] .stMarkdown h1 {{
        font-size: 1.1rem;
        letter-spacing: 0.05em;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}

    /* Card component */
    .retina-card {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }}
    .retina-card:hover {{
        border-color: {COLORS['accent']};
    }}

    /* Metric card */
    .metric-card {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
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

    /* Status badges */
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
        background: rgba(90, 97, 128, 0.3);
        color: {COLORS['text_muted']};
    }}
    .badge-in_progress {{
        background: rgba(7, 110, 255, 0.2);
        color: {COLORS['accent']};
    }}
    .badge-complete {{
        background: rgba(0, 214, 143, 0.2);
        color: {COLORS['success']};
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }}

    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: {COLORS['bg']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text']} !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['accent']} !important;
        box-shadow: 0 0 0 1px {COLORS['accent']} !important;
    }}

    /* Select boxes */
    .stSelectbox > div > div {{
        background-color: {COLORS['bg']} !important;
        border-color: {COLORS['border']} !important;
        border-radius: 8px !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background-color: {COLORS['bg_card']};
        border-radius: 8px;
        padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 6px;
        padding: 8px 16px;
        color: {COLORS['text_muted']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['accent']} !important;
        color: white !important;
    }}

    /* Project list row */
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
    }}
    .project-row:hover {{
        border-color: {COLORS['accent']};
        background: {COLORS['bg_hover']};
    }}

    /* Divider */
    hr {{
        border-color: {COLORS['border']} !important;
        margin: 1.5rem 0 !important;
    }}

    /* Logo area */
    .sidebar-logo {{
        padding: 1rem 0 1.5rem 0;
        text-align: center;
    }}
    .sidebar-logo svg {{
        max-width: 160px;
        height: auto;
    }}

    /* Nav items */
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
        background: rgba(7, 110, 255, 0.15);
        color: {COLORS['accent']};
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
