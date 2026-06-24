import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go


@st.cache_data(ttl=300)
def _fetch_returns(tickers_tuple: tuple, period: str = "1y") -> pd.DataFrame:
    tickers = list(tickers_tuple)
    raw = yf.download(tickers, period=period, progress=False, auto_adjust=True)

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})

    return close.pct_change().dropna(how="all")


def render(positions: pd.DataFrame) -> None:
    st.subheader("Return Correlation Matrix (1 Year)")

    tickers_key = tuple(sorted(positions["ticker"].tolist()))
    with st.spinner("Fetching historical data…"):
        returns = _fetch_returns(tickers_key)

    cols = [t for t in positions["ticker"] if t in returns.columns]
    corr = returns[cols].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu_r",
            zmid=0,
            zmin=-1,
            zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 12},
            colorbar=dict(title="r"),
        )
    )
    fig.update_layout(height=500, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # High-correlation pairs
    st.subheader("Highly Correlated Pairs  |r| > 0.70")
    pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if abs(r) > 0.70:
                pairs.append(
                    {"Asset 1": cols[i], "Asset 2": cols[j], "Correlation": round(r, 3)}
                )

    if pairs:
        pair_df = pd.DataFrame(pairs).sort_values("Correlation", ascending=False)
        st.dataframe(pair_df, use_container_width=True, hide_index=True)
        st.warning(
            "High correlation reduces diversification benefit. "
            "Consider trimming overlapping positions."
        )
    else:
        st.success("No highly correlated pairs — portfolio appears well-diversified.")
