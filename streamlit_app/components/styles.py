"""Shared Streamlit CSS."""

APP_CSS = """
<style>
h1 { font-size: 1.8rem !important; margin-bottom: 0.5rem; }
h3 {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #4FACFE !important;
    text-transform: uppercase !important;
}
.stNumberInput { margin-bottom: -10px; }
.stSelectbox { margin-bottom: -10px; }
.stDateInput { margin-bottom: -10px; }
div[data-testid="stCheckbox"] { margin-top: 32px !important; }
hr { margin-top: 1rem; margin-bottom: 1rem; border-color: #444; }
.metric-warning { color: #FF4B4B; font-weight: 600; }
div[data-testid="stMetricLabel"] {
    overflow: visible !important;
    text-overflow: unset !important;
    white-space: normal !important;
}
div[data-testid="stMetricValue"] {
    overflow: visible !important;
    text-overflow: unset !important;
    white-space: normal !important;
    word-break: break-word;
    font-size: 1.35rem !important;
}
section[data-testid="stSidebar"] {
    width: calc(21rem * 0.8) !important;
    min-width: calc(21rem * 0.8) !important;
    max-width: calc(21rem * 0.8) !important;
}
section[data-testid="stSidebar"] > div {
    width: calc(21rem * 0.8) !important;
    min-width: calc(21rem * 0.8) !important;
}
</style>
"""

CASHFLOW_SIM_SUMMARY_CSS = """
<style>
section[data-testid="stTabs"] [data-baseweb="tab-panel"]:nth-child(1) div[data-testid="stMetricValue"] {
    font-size: 1rem !important;
}
</style>
"""
