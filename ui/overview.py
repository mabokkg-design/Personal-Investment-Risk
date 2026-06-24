import streamlit as st
import pandas as pd
import plotly.express as px


def render(positions: pd.DataFrame) -> None:
    total_value = positions["market_value"].sum()
    total_cost = positions["cost_basis"].sum()
    total_pnl = positions["pnl"].sum()
    total_pnl_pct = (total_pnl / total_cost) * 100
    largest = positions.loc[positions["weight"].idxmax(), "ticker"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio Value", f"${total_value:,.2f}")
    c2.metric("Total P&L", f"${total_pnl:+,.2f}", f"{total_pnl_pct:+.2f}%")
    c3.metric("Holdings", len(positions))
    c4.metric("Largest Position", largest)

    st.divider()

    # Holdings table
    st.subheader("Holdings")
    display = positions[
        ["ticker", "quantity", "avg_cost", "current_price", "market_value", "pnl", "pnl_pct", "weight"]
    ].copy()
    display.columns = [
        "Ticker", "Shares", "Avg Cost", "Current Price",
        "Market Value", "P&L ($)", "P&L (%)", "Weight (%)",
    ]

    def _color_pnl(s: pd.Series) -> list[str]:
        return ["color: #22c55e" if v >= 0 else "color: #ef4444" for v in s]

    styled = (
        display.style
        .format({
            "Shares": "{:.4g}",
            "Avg Cost": "${:.2f}",
            "Current Price": "${:.2f}",
            "Market Value": "${:,.2f}",
            "P&L ($)": "${:+,.2f}",
            "P&L (%)": "{:+.2f}%",
            "Weight (%)": "{:.1f}%",
        })
        .apply(_color_pnl, subset=["P&L ($)", "P&L (%)"])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    # Position size bar chart
    st.subheader("Position Sizes")
    fig = px.bar(
        positions.sort_values("market_value", ascending=True),
        x="market_value",
        y="ticker",
        orientation="h",
        color="pnl",
        color_continuous_scale=["#ef4444", "#6b7280", "#22c55e"],
        color_continuous_midpoint=0,
        labels={"market_value": "Market Value ($)", "ticker": "", "pnl": "P&L ($)"},
    )
    fig.update_layout(height=max(300, len(positions) * 45), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
