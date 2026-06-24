import streamlit as st
import pandas as pd
import plotly.express as px


def render(positions: pd.DataFrame) -> None:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Portfolio Allocation")
        fig = px.pie(
            positions,
            values="market_value",
            names="ticker",
            hole=0.42,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=420, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Position Weights")
        sorted_pos = positions.sort_values("weight", ascending=True)
        fig = px.bar(
            sorted_pos,
            x="weight",
            y="ticker",
            orientation="h",
            color="weight",
            color_continuous_scale="Blues",
            labels={"weight": "Weight (%)", "ticker": ""},
        )
        fig.update_layout(
            height=420,
            margin=dict(t=10),
            coloraxis_showscale=False,
            xaxis_ticksuffix="%",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Concentration metrics
    top3_weight = positions.nlargest(3, "weight")["weight"].sum()
    hhi = ((positions["weight"] / 100) ** 2).sum()
    effective_n = 1 / hhi if hhi > 0 else float("nan")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Top-3 Concentration",
        f"{top3_weight:.1f}%",
        help="Weight of the three largest positions",
    )
    col2.metric(
        "HHI",
        f"{hhi:.4f}",
        help="Herfindahl–Hirschman Index: 1.0 = single holding, 1/n = equal-weight",
    )
    col3.metric(
        "Effective # Holdings",
        f"{effective_n:.1f}",
        help="1 / HHI — the equivalent number of equal-weight positions",
    )
