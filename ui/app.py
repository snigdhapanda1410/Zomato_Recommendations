"""
Zomato AI Restaurant Recommender — Streamlit Web Application (Phase 5).

Renders the pixel-perfect Google Stitch dark-theme frontend matching stitch/screen.png,
with full REST backend integration and live recommendation inference.
"""

from pathlib import Path
import sys
import streamlit as st
import streamlit.components.v1 as components

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure page layout and title
st.set_page_config(
    page_title="Zomato AI Concierge - Bangalore Restaurant Recommendations",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit's default chrome, top toolbar, sidebar, and padding to give 100% screen to Stitch design
st.markdown(
    """
    <style>
        header[data-testid="stHeader"] { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }
        .stDeployButton { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="collapsedControl"] { display: none !important; }
        
        .stApp {
            background-color: #0D0D12 !important;
        }
        .main, .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100vw !important;
        }
        iframe {
            width: 100% !important;
            min-height: 100vh !important;
            border: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load the exact HTML code matching stitch/screen.png
html_file = Path(__file__).parent / "index.html"
if not html_file.exists():
    html_file = PROJECT_ROOT / "stitch" / "code.html"

html_content = html_file.read_text(encoding="utf-8")

# Render full screen responsive component
components.html(html_content, height=2400, scrolling=True)
