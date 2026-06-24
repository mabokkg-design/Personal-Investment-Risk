import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go


@st.cache_data(ttl=300)
def _fetch_returns(tickers_tuple: tuple, period: str = "2y") -> pd.DataFrame:
    tickers = list(tickers_tuple)
    raw = yf.download(tickers, period=period, progress=False, auto_adjust=True)

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})

    return close.pct_change().dropna(how="all")


def _run_simulation(
    weights: np.ndarray,
    mean_ret: np.ndarray,
    cov: np.ndarray,
    n_sims: int,
    n_days: int,
    initial: float,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    L = np.linalg.cholesky(cov)
    results = np.empty((n_sims, n_days))

    for i in range(n_sims):
        z = rng.standard_normal((n_days, len(weights)))
        daily = mean_ret + (z @ L.T)
        port_daily = daily @ weights
        results[i] = initial * np.cumprod(1 + port_daily)

    return results


def render(positions: pd.DataFrame) -> None:
    st.subheader("Monte Carlo Simulation")

    c1, c2, c3 = st.columns(3)
    n_sims = c1.slider("Simulations", 100, 2_000, 500, step=100)
    n_days = c2.slider("Forecast Days", 21, 504, 252, step=21,
                       help="252 ≈ 1 trading year")
    initial = float(
        c3.number_input(
            "Initial Value ($)",
            value=int(positions["market_value"].sum()),
            step=5_000,
            min_value=1_000,
        )
    )

    tickers_key = tuple(sorted(positions["ticker"].tolist()))
    with st.spinner("Running simulation…"):
        returns = _fetch_returns(tickers_key)
        cols = [t for t in positions["ticker"] if t in returns.columns]
        ret_matrix = returns[cols].dropna()

        w = (
            positions.set_index("ticker")["weight"]
            .reindex(cols)
            .fillna(0)
            .values
            .astype(float)
        )
        w /= w.sum()

        mean_ret = ret_matrix.mean().values
        cov = ret_matrix.cov().values

        sim = _run_simulation(w, mean_ret, cov, n_sims, n_days, initial)

    pcts = {p: np.percentile(sim, p, axis=0) for p in [5, 25, 50, 75, 95]}
    x = list(range(n_days))

    fig = go.Figure()

    # Shaded bands
    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=list(pcts[95]) + list(pcts[5][::-1]),
        fill="toself", fillcolor="rgba(59,130,246,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="5th–95th pct",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=list(pcts[75]) + list(pcts[25][::-1]),
        fill="toself", fillcolor="rgba(59,130,246,0.18)",
        line=dict(color="rgba(0,0,0,0)"),
        name="25th–75th pct",
        showlegend=True,
    ))

    # Sample paths
    sample_n = min(60, n_sims)
    for i in range(sample_n):
        fig.add_trace(go.Scatter(
            x=x, y=sim[i],
            mode="lines",
            line=dict(color="rgba(59,130,246,0.04)", width=1),
            showlegend=False,
        ))

    # Median + extremes
    fig.add_trace(go.Scatter(x=x, y=pcts[50], mode="lines",
                             line=dict(color="#3b82f6", width=2.5), name="Median"))
    fig.add_trace(go.Scatter(x=x, y=pcts[5], mode="lines",
                             line=dict(color="#ef4444", width=1.5, dash="dot"), name="5th pct"))
    fig.add_trace(go.Scatter(x=x, y=pcts[95], mode="lines",
                             line=dict(color="#22c55e", width=1.5, dash="dot"), name="95th pct"))

    # Starting-value reference line
    fig.add_hline(y=initial, line_dash="dash", line_color="gray",
                  annotation_text="Initial value", annotation_position="right")

    fig.update_layout(
        height=500,
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        xaxis_title=f"Trading Days (of {n_days})",
        margin=dict(t=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary stats
    final = sim[:, -1]
    prob_profit = (final > initial).mean()

    st.divider()
    st.subheader("Final-Value Distribution")

    cols5 = st.columns(5)
    for col, p in zip(cols5, [5, 25, 50, 75, 95]):
        label = {5: "5th Pct", 25: "25th Pct", 50: "Median", 75: "75th Pct", 95: "95th Pct"}[p]
        col.metric(label, f"${np.percentile(final, p):,.0f}")

    color = "success" if prob_profit >= 0.5 else "warning"
    getattr(st, color)(
        f"**Probability of profit:** {prob_profit:.1%} of {n_sims:,} simulations end above "
        f"the initial ${initial:,.0f}"
    )
