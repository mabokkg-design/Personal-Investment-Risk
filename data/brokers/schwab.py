import os
import pandas as pd
import streamlit as st
from .base import BaseConnector


def _secret(key: str, default: str | None = None) -> str | None:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)


class SchwabConnector(BaseConnector):
    def get_positions(self) -> pd.DataFrame:
        try:
            import schwab
        except ImportError:
            raise ImportError("Run: pip install schwab-py")

        api_key = _secret("SCHWAB_API_KEY")
        app_secret = _secret("SCHWAB_APP_SECRET")
        if not api_key or not app_secret:
            raise EnvironmentError(
                "Set SCHWAB_API_KEY and SCHWAB_APP_SECRET in Streamlit Cloud → "
                "App settings → Secrets (or in a local .env file)."
            )

        token_path = _secret("SCHWAB_TOKEN_PATH", "schwab_token.json")
        callback_url = _secret("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

        client = schwab.auth.client_from_token_file(
            token_path, api_key, app_secret, callback_url=callback_url
        )

        resp = client.get_accounts(
            fields=[schwab.client.Client.Account.Fields.POSITIONS]
        )
        data = resp.json()

        rows = []
        for acct in data:
            for pos in acct.get("securitiesAccount", {}).get("positions", []):
                instrument = pos.get("instrument", {})
                symbol = instrument.get("symbol", "")
                if not symbol:
                    continue
                rows.append(
                    {
                        "ticker": symbol,
                        "quantity": float(pos.get("longQuantity", 0)),
                        "avg_cost": float(pos.get("averagePrice", 0)),
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("No positions found in Schwab account.")

        return self._enrich_positions(df)
