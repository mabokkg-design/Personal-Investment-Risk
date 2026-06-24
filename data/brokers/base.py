import pandas as pd
import yfinance as yf

POSITIONS_SCHEMA = ["ticker", "quantity", "avg_cost"]


def fetch_current_prices(tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}

    raw = yf.download(tickers, period="2d", progress=False, auto_adjust=True)

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})

    prices = {}
    for ticker in tickers:
        if ticker in close.columns:
            series = close[ticker].dropna()
            if not series.empty:
                prices[ticker] = float(series.iloc[-1])

    return prices


class BaseConnector:
    def get_positions(self) -> pd.DataFrame:
        raise NotImplementedError

    def _enrich_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        prices = fetch_current_prices(df["ticker"].tolist())

        df = df.copy()
        df["current_price"] = df["ticker"].map(prices)
        df.dropna(subset=["current_price"], inplace=True)

        df["market_value"] = df["quantity"] * df["current_price"]
        df["cost_basis"] = df["quantity"] * df["avg_cost"]
        df["pnl"] = df["market_value"] - df["cost_basis"]
        df["pnl_pct"] = (df["pnl"] / df["cost_basis"]) * 100

        total = df["market_value"].sum()
        df["weight"] = (df["market_value"] / total) * 100

        return df.reset_index(drop=True)
