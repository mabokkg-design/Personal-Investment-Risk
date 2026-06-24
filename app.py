import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Automotion — Portfolio Risk Dashboard",
    page_icon="📊",
    layout="wide",
)

from data.brokers.base import POSITIONS_SCHEMA
from data.brokers.csv_import import CSVImportConnector


SAMPLE_CSV = """ticker,quantity,avg_cost
AAPL,50,150.00
MSFT,30,280.00
GOOGL,10,120.00
AMZN,15,170.00
NVDA,20,450.00
SPY,25,420.00
QQQ,15,380.00
"""


def load_positions(source: str, uploaded_file=None) -> pd.DataFrame | None:
    try:
        if source == "Sample Portfolio":
            return CSVImportConnector(SAMPLE_CSV).get_positions()

        if source == "CSV Upload":
            if uploaded_file is None:
                return None
            return CSVImportConnector(uploaded_file.read()).get_positions()

        if source == "Alpaca":
            from data.brokers.alpaca import AlpacaConnector
            return AlpacaConnector().get_positions()

        if source == "Interactive Brokers":
            from data.brokers.ibkr import IBKRConnector
            return IBKRConnector().get_positions()

        if source == "Schwab":
            from data.brokers.schwab import SchwabConnector
            return SchwabConnector().get_positions()

        if source == "Robinhood":
            from data.brokers.robinhood import RobinhoodConnector
            return RobinhoodConnector().get_positions()

    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Automotion")
    st.caption("Personal Investment Risk Dashboard")
    st.divider()

    source = st.selectbox(
        "Data Source",
        ["Sample Portfolio", "CSV Upload", "Alpaca", "Interactive Brokers", "Schwab", "Robinhood"],
    )

    uploaded_file = None
    if source == "CSV Upload":
        st.caption("Required columns: `ticker`, `quantity`, `avg_cost`")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    connect_clicked = st.button("Load Portfolio", type="primary", use_container_width=True)

    st.divider()
    st.caption("Market data via Yahoo Finance · Refreshed every 5 min")

# ── Session state ──────────────────────────────────────────────────────────────
if "positions" not in st.session_state:
    st.session_state.positions = None

if connect_clicked:
    with st.spinner("Loading portfolio…"):
        st.session_state.positions = load_positions(source, uploaded_file)

positions = st.session_state.positions

# ── Main content ───────────────────────────────────────────────────────────────
if positions is None or positions.empty:
    st.title("Welcome to Automotion")
    st.markdown(
        """
        A personal **portfolio risk dashboard** inspired by institutional tools like Aladdin® by BlackRock.

        **Get started:**
        1. Select a data source in the sidebar
        2. Click **Load Portfolio**

        **Available sources:**
        | Source | Notes |
        |---|---|
        | Sample Portfolio | Pre-loaded demo with 7 holdings |
        | CSV Upload | Upload a file with `ticker`, `quantity`, `avg_cost` columns |
        | Alpaca | Requires `ALPACA_API_KEY` + `ALPACA_SECRET_KEY` in `.env` |
        | Interactive Brokers | Requires TWS or IB Gateway running locally |
        | Schwab | OAuth login flow on first run |
        | Robinhood | Requires credentials in `.env` |
        """
    )
    st.stop()

# ── Navigation tabs ────────────────────────────────────────────────────────────
tabs = st.tabs(["Overview", "Risk Metrics", "Allocation", "Correlation", "Monte Carlo"])

from ui import overview, risk_metrics, allocation, correlation, monte_carlo_ui

with tabs[0]:
    overview.render(positions)

with tabs[1]:
    risk_metrics.render(positions)

with tabs[2]:
    allocation.render(positions)

with tabs[3]:
    correlation.render(positions)

with tabs[4]:
    monte_carlo_ui.render(positions)
