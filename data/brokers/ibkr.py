import pandas as pd
from .base import BaseConnector


class IBKRConnector(BaseConnector):
    """Requires TWS or IB Gateway running on localhost:7497 (paper) or 7496 (live)."""

    def get_positions(self) -> pd.DataFrame:
        try:
            from ibapi.client import EClient  # noqa: F401
        except ImportError:
            raise ImportError(
                "Install the IB TWS API from https://interactivebrokers.github.io/tws-api/ "
                "then run: pip install ibapi"
            )

        raise NotImplementedError(
            "The IBKR connector requires a custom EWrapper/EClient implementation. "
            "Use the CSV Upload option and export your positions from TWS as a CSV."
        )
