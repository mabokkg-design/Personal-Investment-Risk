import os
import pandas as pd
from .base import BaseConnector


class SchwabConnector(BaseConnector):
    def get_positions(self) -> pd.DataFrame:
        try:
            import schwab
        except ImportError:
            raise ImportError("Run: pip install schwab-py")

        api_key = os.getenv("SCHWAB_API_KEY")
        app_secret = os.getenv("SCHWAB_APP_SECRET")
        if not api_key or not app_secret:
            raise EnvironmentError(
                "Set SCHWAB_API_KEY and SCHWAB_APP_SECRET in your .env file."
            )

        token_path = os.getenv("SCHWAB_TOKEN_PATH", "schwab_token.json")
        callback_url = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

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
