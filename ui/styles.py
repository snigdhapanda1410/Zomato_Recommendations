"""
Custom CSS styles and UI card templates for the Zomato AI Restaurant Recommender.
Premium dark theme with glassmorphism, glow effects, and micro-animations
inspired by the Stitch design system.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap');

/* ── Design Tokens ─────────────────────────────────────────────────── */
:root {
    --brand-dark: #0D0D12;
    --brand-sidebar: #111118;
    --brand-surface: #1A1A24;
    --brand-surface-hover: #22222E;
    --brand-verdict-bg: #151520;
    --brand-red: #E23744;
    --primary-red: #E23744;
    --brand-red-hover: #FF5A60;
    --brand-red-glow: rgba(226, 55, 68, 0.35);
    --brand-gold: #FFB800;
    --brand-green: #34D399;
    --brand-green-dark: #065F46;
    --text-primary: #F1F1F5;
    --text-secondary: #C4C4D0;
    --text-muted: #8B8FA3;
    --text-subtle: #5A5A6E;
    --border-subtle: rgba(255, 255, 255, 0.06);
    --border-light: rgba(255, 255, 255, 0.10);
}

/* ── Keyframe Animations ───────────────────────────────────────────── */
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 15px rgba(226, 55, 68, 0.35); }
    50% { box-shadow: 0 0 28px rgba(226, 55, 68, 0.65); }
}

@keyframes badgePulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.04); }
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Base Typography & Background ──────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, .brand-font {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}

.stApp {
    background-color: var(--brand-dark) !important;
}

/* ── Scrollbar ─────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--brand-sidebar); }
::-webkit-scrollbar-thumb { background: #2A2A36; border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: var(--brand-red); }

/* ── Main Container ────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 1.25rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ── Top Header Bar ────────────────────────────────────────────────── */
.top-header-bar {
    background: rgba(26, 26, 36, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-subtle);
    padding: 0.65rem 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem;
    border-radius: 0;
    position: sticky;
    top: 0;
    z-index: 20;
}

.top-header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34D399;
    animation: badgePulse 2s ease-in-out infinite;
    display: inline-block;
}

.top-header-text {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.7);
}

.top-header-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.75rem;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-light);
    font-size: 0.7rem;
    color: rgba(255,255,255,0.8);
    font-weight: 500;
}

.blr-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f59e0b, #E23744);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.6rem;
    font-weight: 700;
    color: #fff;
}

/* ── Sidebar Styling ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: var(--brand-sidebar) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stTextArea textarea,
section[data-testid="stSidebar"] .stMultiSelect > div > div {
    background-color: var(--brand-surface) !important;
    border: 1px solid var(--border-light) !important;
    color: var(--text-primary) !important;
    border-radius: 12px !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
section[data-testid="stSidebar"] .stTextArea textarea:focus {
    border-color: rgba(226, 55, 68, 0.6) !important;
    box-shadow: 0 0 0 1px rgba(226, 55, 68, 0.4) !important;
}

section[data-testid="stSidebar"] .stSlider > div > div > div {
    background: #2A2A36 !important;
}

section[data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {
    color: var(--brand-gold) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600;
}

/* Sidebar brand header */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1rem;
}

.sidebar-logo {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: linear-gradient(135deg, #E23744 0%, #FF5A60 100%);
    padding: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 18px rgba(226, 55, 68, 0.4);
}

.sidebar-logo-inner {
    width: 100%;
    height: 100%;
    background: var(--brand-sidebar);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}

.sidebar-brand-text {
    display: flex;
    flex-direction: column;
}

.sidebar-brand-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 1.2rem;
    color: #fff;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.sidebar-brand-ai {
    padding: 0.1rem 0.4rem;
    font-size: 0.55rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    border-radius: 4px;
    background: rgba(226, 55, 68, 0.2);
    color: var(--brand-red);
    border: 1px solid rgba(226, 55, 68, 0.3);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.sidebar-brand-sub {
    font-size: 0.62rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.sidebar-section-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.sidebar-section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.sidebar-model-tag {
    font-size: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--brand-red);
    background: rgba(226, 55, 68, 0.1);
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
}

.sidebar-caption {
    font-size: 0.72rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin-top: 0.25rem;
}

.filter-label-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.2rem;
}

.filter-label {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.filter-count {
    font-size: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.4);
}

.ai-prompt-tag {
    font-size: 0.55rem;
    color: var(--brand-red);
    background: rgba(226, 55, 68, 0.1);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
}

/* ── Hero Section ──────────────────────────────────────────────────── */
.hero-section {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    background: linear-gradient(135deg, #1A1A24 0%, #14141E 50%, #0D0D12 100%);
    border: 1px solid var(--border-light);
    padding: 2.5rem;
    margin-bottom: 1.75rem;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.3);
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -100px;
    left: -100px;
    width: 400px;
    height: 400px;
    background: rgba(226, 55, 68, 0.12);
    border-radius: 50%;
    filter: blur(90px);
    pointer-events: none;
}

.hero-section::after {
    content: '';
    position: absolute;
    bottom: -100px;
    right: -100px;
    width: 400px;
    height: 400px;
    background: rgba(255, 184, 0, 0.08);
    border-radius: 50%;
    filter: blur(100px);
    pointer-events: none;
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border-light);
    font-size: 0.72rem;
    color: rgba(255,255,255,0.9);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    margin-bottom: 1rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    letter-spacing: 0.03em;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.15;
    margin-bottom: 0.75rem;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.03em;
}

.hero-gradient-text {
    background: linear-gradient(to right, #E23744, #FF6B6B, #FFB800);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-style: italic;
}

.hero-subtitle {
    font-size: 0.9rem;
    color: var(--text-secondary);
    max-width: 680px;
    line-height: 1.6;
}

/* ── KPI Stats Grid ────────────────────────────────────────────────── */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
    gap: 0.85rem;
    margin-top: 1.5rem;
}

.kpi-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 14px;
    padding: 0.85rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    transition: all 0.25s ease;
}

.kpi-card:hover {
    border-color: rgba(226, 55, 68, 0.4);
    background: rgba(255, 255, 255, 0.08);
}

.kpi-label {
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.kpi-value {
    font-size: 1rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
}

.kpi-value-green {
    color: #34D399;
}

/* ── Quick Discovery Presets ───────────────────────────────────────── */
.presets-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}

.presets-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.6);
}

.presets-subtitle {
    font-size: 0.68rem;
    color: var(--text-muted);
}

/* Style the preset Streamlit buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: var(--brand-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: 16px !important;
    padding: 0.75rem 1rem !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
    width: 100% !important;
}

div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: var(--brand-red) !important;
    box-shadow: 0 8px 30px rgba(226, 55, 68, 0.18) !important;
    transform: translateY(-2px) !important;
}

/* ── Primary Button ────────────────────────────────────────────────── */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #E23744 0%, #FF5A60 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    border-radius: 12px !important;
    box-shadow: 0 0 22px rgba(226, 55, 68, 0.4) !important;
    transition: all 0.2s ease !important;
    animation: pulseGlow 3s ease-in-out infinite;
    letter-spacing: 0.02em;
    width: 100%;
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 30px rgba(226, 55, 68, 0.7) !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary / Reset Button ──────────────────────────────────────── */
div.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    border: 1px solid var(--border-light) !important;
    color: var(--text-muted) !important;
    border-radius: 12px !important;
    font-size: 0.78rem !important;
    transition: all 0.2s ease !important;
}

div.stButton > button:not([kind="primary"]):hover {
    border-color: rgba(255,255,255,0.2) !important;
    background: rgba(255,255,255,0.03) !important;
    color: var(--text-primary) !important;
}

/* ── Radio Buttons (Budget Pills) ──────────────────────────────────── */
section[data-testid="stSidebar"] .stRadio > div {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0.4rem !important;
}

section[data-testid="stSidebar"] .stRadio > div > label {
    background: var(--brand-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 0.5rem 0.5rem !important;
    text-align: center !important;
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stRadio > div > label:hover {
    color: var(--text-primary) !important;
}

section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: linear-gradient(135deg, #E23744 0%, #FF5A60 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 16px rgba(226, 55, 68, 0.45) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
}

/* ── Results Header ────────────────────────────────────────────────── */
.results-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1.25rem;
}

.results-title-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.results-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}

.results-subtitle {
    font-size: 0.72rem;
    color: var(--text-muted);
}

/* ── Active Filter Chips ───────────────────────────────────────────── */
.filter-chips-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.65rem;
    border-radius: 9999px;
    background: #1F1F2B;
    border: 1px solid rgba(226, 55, 68, 0.3);
    color: rgba(255,255,255,0.9);
    font-size: 0.72rem;
    font-weight: 500;
}

.filter-chip-label {
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
    margin-right: 0.25rem;
}

.candidates-pill {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: #34D399;
    background: rgba(52, 211, 153, 0.1);
    border: 1px solid rgba(52, 211, 153, 0.2);
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
}

/* ── Recommendation Card ───────────────────────────────────────────── */
.recom-card {
    background: var(--brand-surface);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 18px;
    padding: 1.5rem 1.6rem;
    margin-bottom: 1.25rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    animation: fadeSlideUp 0.4s ease forwards;
}

/* Left edge glow */
.recom-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(180deg, rgba(226, 55, 68, 0.8), rgba(226, 55, 68, 0));
    opacity: 0.4;
    transition: opacity 0.3s ease, width 0.3s ease;
    border-top-left-radius: 18px;
    border-bottom-left-radius: 18px;
}

.recom-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(226, 55, 68, 0.14);
    border-color: rgba(226, 55, 68, 0.6);
}

.recom-card:hover::before {
    opacity: 1;
    width: 4px;
}

.recom-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.3rem;
}

.recom-card-left {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}

.recom-rank-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.recom-rank-badge {
    background: linear-gradient(135deg, #E23744 0%, #FF5A60 100%);
    color: #FFFFFF;
    font-size: 0.6rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    box-shadow: 0 0 12px rgba(226, 55, 68, 0.4);
}

.recom-rank-badge-secondary {
    background: #2A2A36;
    color: rgba(255,255,255,0.9);
    font-size: 0.6rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid var(--border-light);
}

.recom-match-score {
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
}

.recom-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
    transition: color 0.2s ease;
}

.recom-card:hover .recom-title {
    color: #FF6B6B;
}

.recom-address {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

/* Rating Badge */
.recom-card-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.3rem;
}

.recom-rating-box {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: var(--brand-green-dark);
    color: var(--brand-green);
    padding: 0.4rem 0.8rem;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1rem;
    font-family: 'Outfit', sans-serif;
    box-shadow: 0 0 14px rgba(52, 211, 153, 0.25);
    border: 1px solid rgba(52, 211, 153, 0.3);
    animation: badgePulse 4s ease-in-out infinite;
}

.recom-review-count {
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
}

/* ── Metadata Badges Row ───────────────────────────────────────────── */
.recom-badges-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1rem 0;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.7rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 500;
}

.badge-cuisine {
    background: var(--brand-sidebar);
    color: rgba(255,255,255,0.9);
    border: 1px solid var(--border-light);
}

.badge-cost {
    background: rgba(255, 184, 0, 0.1);
    color: var(--brand-gold);
    border: 1px solid rgba(255, 184, 0, 0.25);
    font-family: 'JetBrains Mono', monospace;
}

.badge-location {
    background: rgba(59, 130, 246, 0.1);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.25);
}

.badge-votes {
    background: rgba(139, 92, 246, 0.1);
    color: #A78BFA;
    border: 1px solid rgba(139, 92, 246, 0.25);
    font-family: 'JetBrains Mono', monospace;
}

/* ── AI Verdict Box ────────────────────────────────────────────────── */
.ai-verdict-box {
    background: var(--brand-verdict-bg);
    border-left: 4px solid var(--brand-red);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-top: 0.5rem;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.15);
}

.ai-verdict-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}

.ai-verdict-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.68rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    color: var(--brand-red);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.ai-verdict-tag {
    font-size: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.4);
}

.ai-verdict-text {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0;
    font-style: italic;
}

/* ── Relaxation Banner ─────────────────────────────────────────────── */
.relaxation-banner {
    background: #111625;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-left: 4px solid #38BDF8;
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 1.25rem;
    color: var(--text-muted);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.75rem;
}

.relaxation-banner strong {
    color: #7DD3FC;
}

.relaxation-icon {
    background: rgba(56, 189, 248, 0.2);
    color: #7DD3FC;
    padding: 0.25rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

/* ── Fallback Banner ───────────────────────────────────────────────── */
.fallback-banner {
    background: #1D1712;
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-left: 4px solid #F59E0B;
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 1.25rem;
    color: var(--text-muted);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.75rem;
}

.fallback-banner strong {
    color: #FDE68A;
}

.fallback-icon {
    background: rgba(245, 158, 11, 0.2);
    color: #FCD34D;
    padding: 0.25rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

/* ── Empty State Card ──────────────────────────────────────────────── */
.empty-state-card {
    background: rgba(26, 26, 36, 0.4);
    border: 2px dashed rgba(255, 255, 255, 0.1);
    border-radius: 18px;
    padding: 3rem 2rem;
    text-align: center;
    margin: 2rem 0;
}

.empty-state-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto 1rem auto;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: inset 0 2px 6px rgba(0,0,0,0.2);
}

.empty-state-title {
    font-size: 1.15rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
}

.empty-state-desc {
    font-size: 0.82rem;
    color: var(--text-muted);
    max-width: 480px;
    margin: 0 auto 1rem auto;
    line-height: 1.55;
}

.empty-state-link {
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--brand-red);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}

/* ── Bottom Action Strip ───────────────────────────────────────────── */
.bottom-action-strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-subtle);
    margin-top: 0.5rem;
}

.bottom-summary-text {
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
}

/* ── Expander Dark Override ────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--brand-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
}

div[data-testid="stExpander"] {
    border-color: var(--border-subtle) !important;
    background: var(--brand-sidebar) !important;
    border-radius: 12px !important;
}

div[data-testid="stExpander"] details {
    border-color: var(--border-subtle) !important;
}

/* ── Download Button Dark ──────────────────────────────────────────── */
div.stDownloadButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border-light) !important;
    color: rgba(255,255,255,0.9) !important;
    border-radius: 12px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

div.stDownloadButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #FFFFFF !important;
}

/* ── Footer ────────────────────────────────────────────────────────── */
.dark-footer {
    position: relative;
    padding-top: 2rem;
    padding-bottom: 3rem;
    margin-top: 2.5rem;
    text-align: center;
}

.dark-footer::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--brand-red), transparent);
    opacity: 0.4;
}

.footer-content {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    font-size: 0.72rem;
    color: var(--text-muted);
}

.footer-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.footer-brand-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}

.footer-tech {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-muted);
}

/* ── System Info Details ───────────────────────────────────────────── */
.system-info-panel {
    background: rgba(13, 13, 18, 0.7);
    border-top: 1px solid var(--border-subtle);
    padding: 0.75rem 1rem;
    font-size: 0.65rem;
    color: var(--text-muted);
}

.system-info-row {
    display: flex;
    justify-content: space-between;
    padding: 0.2rem 0;
}

.system-info-value {
    font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.8);
}

.system-info-value-green {
    font-family: 'JetBrains Mono', monospace;
    color: #34D399;
}

/* ── Detail Grid Amenities ─────────────────────────────────────────── */
.amenity-card {
    background: var(--brand-sidebar);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 0.75rem;
}

.amenity-label {
    font-size: 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
}

.amenity-value {
    font-size: 0.75rem;
    color: #FFFFFF;
    font-weight: 500;
}

.amenity-value-ok { color: #34D399; }
.amenity-value-no { color: #EF4444; }

/* ── Toast / Metric Overrides ──────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--brand-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
}

[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
}

/* ── Text input & text area dark overrides ─────────────────────────── */
.stTextInput input, .stTextArea textarea {
    background-color: var(--brand-surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-light) !important;
    border-radius: 12px !important;
}

.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: var(--text-subtle) !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(226, 55, 68, 0.6) !important;
    box-shadow: 0 0 0 1px rgba(226, 55, 68, 0.4) !important;
}

/* ── Selectbox dark override ───────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] {
    background-color: var(--brand-surface) !important;
}

.stSelectbox [data-baseweb="select"] > div {
    background-color: var(--brand-surface) !important;
    border-color: var(--border-light) !important;
    color: var(--text-primary) !important;
    border-radius: 12px !important;
}

/* ── Divider override ──────────────────────────────────────────────── */
hr {
    border-color: var(--border-subtle) !important;
}
</style>
"""


def render_recommendation_card_html(
    rank: int,
    name: str,
    cuisine: str,
    rating: float,
    cost: str,
    explanation: str,
    location: str | None = None,
    votes: int | None = None,
) -> str:
    """
    Generate an HTML card for an individual restaurant recommendation.

    Args:
        rank: 1-indexed recommendation position (1 to N).
        name: Name of the restaurant.
        cuisine: Types of cuisine offered.
        rating: Restaurant rating score.
        cost: Approximate cost string.
        explanation: Personalized AI explanation text.
        location: Optional neighborhood string.
        votes: Optional votes count.

    Returns:
        str: Rendered HTML snippet.
    """
    clean_name = str(name).replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    clean_cuisine = str(cuisine).replace("<", "&lt;").replace(">", "&gt;")
    clean_cost = str(cost).replace("<", "&lt;").replace(">", "&gt;")
    clean_explanation = str(explanation).replace("<", "&lt;").replace(">", "&gt;")

    # Rank badge styling: #1 gets gradient, others get secondary
    if rank == 1:
        rank_badge = f'<span class="recom-rank-badge">#{rank} MATCH • BEST MATCH</span>'
    else:
        rank_badge = f'<span class="recom-rank-badge-secondary">#{rank} MATCH</span>'

    location_badge = (
        f'<span class="badge badge-location">📍 {location}</span>'
        if location
        else ""
    )
    votes_badge = (
        f'<span class="badge badge-votes">👥 {votes:,} reviews</span>'
        if votes and votes > 0
        else ""
    )

    # Review count text for the right side
    review_text = ""
    if votes and votes > 0:
        review_text = f'<span class="recom-review-count">{votes:,}+ reviews</span>'

    return f"""
    <div class="recom-card">
        <div class="recom-card-header">
            <div class="recom-card-left">
                <div class="recom-rank-row">
                    {rank_badge}
                </div>
                <h3 class="recom-title">{clean_name}</h3>
            </div>
            <div class="recom-card-right">
                <div class="recom-rating-box">
                    ★ {rating:.1f}
                </div>
                {review_text}
            </div>
        </div>
        <div class="recom-badges-row">
            <span class="badge badge-cuisine">🍽️ {clean_cuisine}</span>
            <span class="badge badge-cost">💰 {clean_cost}</span>
            {location_badge}
            {votes_badge}
        </div>
        <div class="ai-verdict-box">
            <div class="ai-verdict-header">
                <span class="ai-verdict-label">
                    ⚡ AI Critic Verdict
                </span>
                <span class="ai-verdict-tag">Semantic Analysis</span>
            </div>
            <p class="ai-verdict-text">"{clean_explanation}"</p>
        </div>
    </div>
    """
