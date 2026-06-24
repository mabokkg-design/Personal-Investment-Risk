import os
import pandas as pd
from .base import BaseConnector


class RobinhoodConnector(BaseConnector):
    def get_positions(self) -> pd.DataFrame:
        try:
            import robin_stocks.robinhood as rh
        except ImportError:
            raise ImportError("Run: pip install robin-stocks")

        username = os.getenv("ROBINHOOD_USERNAME")
        password = os.getenv("ROBINHOOD_PASSWORD")
        if not username or not password:
            raise EnvironmentError(
                "Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD in your .env file."
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
