import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go


@st.cache_data(ttl=300)
def _fetch_close(tickers_tuple: tuple, period: str = "1y") -> pd.DataFrame:
    tickers = list(tickers_tuple)
    all_tickers = list(dict.fromkeys(tickers + ["SPY"]))
    raw = yf.download(all_tickers, period=period, progress=False, auto_adjust=True)

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": all_tickers[0]})

    return close.dropna(how="all")


def _compute_metrics(positions: pd.DataFrame, close: pd.DataFrame) -> dict:
    port_tickers = [t for t in positions["ticker"] if t in close.columns]
    weights = (
        positions.set_index("ticker")["weight"]
        .reindex(port_tickers)
        .fillna(0)
        / 100
    )
    weights /= weights.sum()

    returns = close.pct_change().dropna()
    port_ret = returns[port_tickers].mul(weights, axis=1).sum(axis=1)
    spy_ret = returns["SPY"] if "SPY" in returns.columns else None

    ann_return = port_ret.mean() * 252
    ann_vol = port_ret.std() * np.sqrt(252)
    risk_free = 0.05
    sharpe = (ann_return - risk_free) / ann_vol if ann_vol > 0 else float("nan")

    if spy_ret is not None:
        cov = np.cov(port_ret.values, spy_ret.values)
        beta = cov[0, 1] / cov[1, 1]
    else:
        beta = float("nan")

    var_95 = float(np.percentile(port_ret, 5))

    cumulative = (1 + port_ret).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_dd = float(drawdown.min())

    individual_betas = {}
    if spy_ret is not None:
        for ticker in port_tickers:
            c = np.cov(returns[ticker].values, spy_ret.values)
            individual_betas[ticker] = c[0, 1] / c[1, 1]

    return {
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "beta": beta,
        "var_95": var_95,
        "max_dd": max_dd,
        "port_ret": port_ret,
        "drawdown": drawdown,
        "individual_betas": individual_betas,
    }


def render(positions: pd.DataFrame) -> None:
    st.subheader("Risk Metrics")

    tickers_key = tuple(sorted(positions["ticker"].tolist()))
    with st.spinner("Fetching 1-year price history…"):
        close = _fetch_close(tickers_key)

    m = _compute_metrics(positions, close)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ann. Return", f"{m['ann_return']:.1%}")
    c2.metric("Ann. Volatility", f"{m['ann_vol']:.1%}")
    c3.metric("Sharpe Ratio", f"{m['sharpe']:.2f}")
    c4.metric("Beta (vs SPY)", f"{m['beta']:.2f}")
    c5.metric("Max Drawdown", f"{m['max_dd']:.1%}")

    total_value = positions["market_value"].sum()
    var_dollar = abs(m["var_95"] * total_value)
    st.info(
        f"**Value at Risk (95 %, 1-day):** {m['var_95']:.2%} of portfolio "
        f"→ **${var_dollar:,.0f}** at risk on a bad day"
    )

    st.divider()

    # Drawdown chart
    st.subheader("Portfolio Drawdown (1 Year)")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=m["drawdown"].index,
            y=m["drawdown"].values,
            fill="tozeroy",
            fillcolor="rgba(239,68,68,0.25)",
            line=dict(color="#ef4444", width=1.5),
            name="Drawdown",
        )
    )
    fig.update_layout(
        yaxis_tickformat=".1%",
        height=280,
        margin=dict(t=10, b=10),
        yaxis_title="Drawdown",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Individual betas
    if m["individual_betas"]:
        st.subheader("Individual Betas vs SPY")
        beta_df = pd.DataFrame(
            m["individual_betas"].items(), columns=["Ticker", "Beta"]
        ).sort_values("Beta")

        fig = px.bar(
            beta_df,
            x="Ticker",
            y="Beta",
            color="Beta",
            color_continuous_scale=["#3b82f6", "#f59e0b", "#ef4444"],
            color_continuous_midpoint=1,
            labels={"Beta": "Beta"},
        )
        fig.add_hline(
            y=1,
            line_dash="dash",
            line_color="gray",
            annotation_text="Market β = 1",
            annotation_position="top right",
        )
        fig.update_layout(height=300, margin=dict(t=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
