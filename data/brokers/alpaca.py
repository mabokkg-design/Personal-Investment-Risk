import os
import pandas as pd
import streamlit as st
from .base import BaseConnector


def _secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)


class AlpacaConnector(BaseConnector):
    def __init__(self):
        self._key = _secret("ALPACA_API_KEY")
        self._secret = _secret("ALPACA_SECRET_KEY")
        if not self._key or not self._secret:
            raise EnvironmentError(
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY in Streamlit Cloud → "
                "App settings → Secrets (or in a local .env file)."
            )

    def get_positions(self) -> pd.DataFrame:
        try:
            from alpaca.trading.client import TradingClient
        except ImportError:
            raise ImportError("Run: pip install alpaca-py")

        client = TradingClient(self._key, self._secret, paper=True)
        raw = client.get_all_positions()

        rows = [
            {
                "ticker": p.symbol,
                "quantity": float(p.qty),
                "avg_cost": float(p.avg_entry_price),
            }
            for p in raw
        ]
        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("No positions found in Alpaca account.")

        return self._enrich_positions(df)
