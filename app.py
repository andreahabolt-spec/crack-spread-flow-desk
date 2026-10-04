import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (
    LEG_NAMES, LEGS_0, GASOLINE_0_GAL, DIESEL_0_GAL, GALLONS_PER_BARREL,
    DAYS, N_PATHS, SEED, MU, SIGMA, CORR,
)
from calc import simulate_correlated_paths

st.set_page_config(page_title="Crack Spread Flow Desk", layout="wide")
st.title("Crack Spread Flow Desk")
st.caption("Educational simulator of a 3:2:1 crack spread position over 21 trading days. "
           "All prices are simulated.")

# ---------- Sidebar: simulation settings ----------
st.sidebar.header("Simulation settings")
n_paths = st.sidebar.number_input(
    "Number of simulated months (paths)", min_value=1, max_value=500, value=N_PATHS, step=1
)
seed = st.sidebar.number_input(
    "Random seed (same seed = same paths)", min_value=0, value=SEED, step=1
)

# ---------- Simulate the paths ----------
paths = simulate_correlated_paths(LEGS_0, MU, SIGMA, CORR, DAYS, n_paths, seed)
days_axis = list(range(DAYS + 1))
MAX_LINES = 20          # we draw at most 20 lines per chart, to keep it readable

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Market", "Position & P&L", "Risk", "Scenarios & Report"]
)

with tab1:
    st.subheader("Starting market (day 0)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Crude", f"${LEGS_0[0]:,.2f} per barrel")
    m2.metric("Gasoline", f"${LEGS_0[1]:,.2f} per barrel")
    m2.caption(f"${GASOLINE_0_GAL:.2f} per gallon x {GALLONS_PER_BARREL} gallons")
    m3.metric("Diesel", f"${LEGS_0[2]:,.2f} per barrel")
    m3.caption(f"${DIESEL_0_GAL:.2f} per gallon x {GALLONS_PER_BARREL} gallons")

    st.subheader("Simulated futures prices")
    st.caption(
        f"{n_paths} simulated months of {DAYS} trading days. "
        f"Each line is one possible month. The three charts use the same paths, "
        f"so you can compare the legs."
    )

    cols = st.columns(3)
    for i, name in enumerate(LEG_NAMES):
        fig = go.Figure()
        for p in range(min(n_paths, MAX_LINES)):
            fig.add_trace(go.Scatter(
                x=days_axis, y=paths[p, :, i], mode="lines", name=f"Path {p + 1}"
            ))
        fig.update_layout(
            title=f"{name}",
            xaxis_title="Trading day",
            yaxis_title="USD per barrel",
            height=360,
            showlegend=(i == 2),
        )
        cols[i].plotly_chart(fig)
    if n_paths > MAX_LINES:
        st.caption(f"The charts show the first {MAX_LINES} paths only.")

    st.subheader("Where each path ends (day 21)")
    rows = []
    for p in range(n_paths):
        row = {"Path": p + 1}
        for i, name in enumerate(LEG_NAMES):
            row[f"{name} (USD/bbl)"] = round(paths[p, -1, i], 2)
        for i, name in enumerate(LEG_NAMES):
            row[f"{name} change %"] = round((paths[p, -1, i] / LEGS_0[i] - 1) * 100, 1)
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    with st.expander("How the prices are simulated"):
        st.markdown(
            """
Each leg follows a **random walk with a small upward drift**. Every day, the price is
multiplied by a factor:

`new price = old price x exp( drift + volatility x random number )`

- **Drift** = (2% - volatility squared / 2) / 252 per day. It is tiny.
- **Volatility part** = yearly volatility x square root of (1/252) x random number Z.
  Crude has 25% yearly volatility, gasoline 20%, diesel 18%.
- Z is a random number, mostly between -2 and +2.

**Example, crude on day 1 with Z = +1:**
- drift = (0.02 - 0.25 x 0.25 / 2) / 252 = -0.00004
- volatility part = 0.25 x 0.063 x 1 = 0.0157
- new price = 78 x exp(0.0157) = **79.23 USD per barrel** (up 1.6%)

**Why the legs move together.** If the three random numbers were independent, crude could
rise while gasoline falls for no reason. We want them linked, with a correlation of 0.8
between crude and gasoline. The trick (called Cholesky): the gasoline shock is
**0.8 x the crude shock + 0.6 x a new independent shock**. Since 0.8 x 0.8 + 0.6 x 0.6 = 1,
the gasoline shock keeps its normal size, and its correlation with crude is exactly 0.8.

**Fixed seed.** The random numbers come from a fixed starting number, so the same seed
gives the same paths. This lets you reproduce and explain a result.
            """
        )

    with st.expander("Check: do the simulated legs move together?"):
        st.write(
            "We take every daily move of every path and measure the correlation. "
            "With only 5 paths, the result is rough. Set the number of paths to 500 "
            "in the sidebar, and it gets very close to the inputs."
        )
        log_returns = np.log(paths[:, 1:, :] / paths[:, :-1, :]).reshape(-1, len(LEG_NAMES))
        sim_corr = np.corrcoef(log_returns, rowvar=False)
        c1, c2 = st.columns(2)
        c1.markdown("**Input correlation**")
        c1.dataframe(pd.DataFrame(CORR, index=LEG_NAMES, columns=LEG_NAMES).round(2))
        c2.markdown("**Simulated correlation**")
        c2.dataframe(pd.DataFrame(sim_corr, index=LEG_NAMES, columns=LEG_NAMES).round(2))

with tab2:
    st.write("Roll yield and daily P&L - coming next.")
with tab3:
    st.write("Basis exposure and curve sensitivity - coming next.")
with tab4:
    st.write("Volatility and correlation scenarios, and the summary report - coming next.")