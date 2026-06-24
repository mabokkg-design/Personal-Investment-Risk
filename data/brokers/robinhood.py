import os
import pandas as pd
import streamlit as st
from .base import BaseConnector


def _secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)


class RobinhoodConnector(BaseConnector):
    def get_positions(self) -> pd.DataFrame:
        try:
            import robin_stocks.robinhood as rh
        except ImportError:
            raise ImportError("Run: pip install robin-stocks")

        username = _secret("ROBINHOOD_USERNAME")
        password = _secret("ROBINHOOD_PASSWORD")
        if not username or not password:
            raise EnvironmentError(
                "Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD in Streamlit Cloud → "
                "App settings → Secrets (or in a local .env file)."
            )

        rh.login(username, password)
        raw = rh.account.build_holdings()

        rows = [
            {
                "ticker": symbol,
                "quantity": float(info["quantity"]),
                "avg_cost": float(info["average_buy_price"]),
            }
            for symbol, info in raw.items()
        ]

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("No positions found in Robinhood account.")

        return self._enrich_positions(df)
