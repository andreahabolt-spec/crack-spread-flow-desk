import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import (
    LEG_NAMES, LEGS_0, GASOLINE_0_GAL, DIESEL_0_GAL, GALLONS_PER_BARREL,
    DAYS, DT, N_PATHS, SEED, MU, SIGMA, CORR,
    NOTIONAL_BBL, CONTRACT_BBL, POSITION_BBL,
    CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, CURVE_CHART_DAYS,
    MARGIN_USD, R, DAILY_FUNDING,
    BASIS_VOL, BASIS_PERSISTENCE, BASIS_SEED_OFFSET, CURVE_SCENARIOS, CURVE_BUMP,
    SCENARIO_PATHS, SCENARIOS, THIN_CRACK_LEGS_0, THIN_CRACK_VOL_MULT,
)
from calc import (
    simulate_correlated_paths, compute_crack, futures_price, roll_yield, run_desk,
    simulate_basis, average_pnl, equal_correlation, run_scenario, summarize,
)


def usd(x):
    """Format a number as dollars, with the minus sign in front: -$1,234."""
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


# Streamlit reads text between two dollar signs as math. These small functions
# put a backslash before each dollar sign, so that $ is shown as a normal dollar sign.
def esc(text):
    return text.replace("$", "\\$")


def md(text):
    st.markdown(esc(text))


def cap(text):
    st.caption(esc(text))


def info(text):
    st.info(esc(text))


st.set_page_config(page_title="Crack Spread Flow Desk", layout="wide")
st.title("Crack Spread Flow Desk")
cap("Educational simulator of a 3:2:1 crack spread position over 21 trading days. "
    "All prices are simulated.")

# ---------- Sidebar: simulation settings ----------
st.sidebar.header("Simulation settings")
n_paths = st.sidebar.number_input(
    "Number of simulated months (paths)", min_value=1, max_value=500, value=N_PATHS, step=1
)
seed = st.sidebar.number_input(
    "Random seed (same seed = same paths)", min_value=0, value=SEED, step=1
)

# ---------- Simulate the paths and compute the crack ----------
paths = simulate_correlated_paths(LEGS_0, MU, SIGMA, CORR, DAYS, n_paths, seed)
crack_paths = compute_crack(paths[:, :, 0], paths[:, :, 1], paths[:, :, 2])
results = [
    run_desk(paths[p], POSITION_BBL, CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING)
    for p in range(n_paths)
]
days_axis = list(range(DAYS + 1))
MAX_LINES = 20          # we draw at most 20 lines per chart, to keep it readable

# ---------- Tabs ----------
tab_overview, tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Market", "Position & P&L", "Risk", "Scenarios & Report"]
)

@st.cache_data
def overview_numbers():
    """Run 500 simulated months with the default settings, for the Overview page."""
    sim = simulate_correlated_paths(LEGS_0, MU, SIGMA, CORR, DAYS, 500, SEED)
    runs = [
        run_desk(sim[p], POSITION_BBL, CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING)
        for p in range(500)
    ]
    price = np.array([x["price_pnl"].sum() for x in runs])
    roll = np.array([x["roll_pnl"].sum() for x in runs])
    funding = np.array([x["funding"].sum() for x in runs])
    total = np.array([x["cum_pnl"][-1] for x in runs])
    return price, roll, funding, total


with tab_overview:
    st.header("Hedging a refiner's margin: a crack spread flow desk")
    info(
        "**In one sentence:** a refiner wants to protect its refining margin from oil price swings. "
        "Our desk takes the other side of that hedge and goes long the 3:2:1 crack spread for one month. "
        "This app shows how much the desk can make or lose, where the P&L comes from, "
        "and which risks remain."
    )

    st.subheader("The situation")
    md(
        """
A refinery buys crude oil and sells gasoline and diesel. Its profit depends on the gap between
the price of the products and the price of crude. This gap is called the **crack spread**.
We use the standard **3:2:1** version: 3 barrels of crude become 2 barrels of gasoline and
1 barrel of diesel.

With the prices in this simulation, the crack is **$34 per barrel**:
(2 x $105 + $126) / 3 - $78 = $34.
Oil prices are volatile, and the crack moves with them.
        """
    )

    st.subheader("The client's problem")
    md(
        """
The refiner will process **10,000 barrels** of crude next month. If the crack falls, its margin
falls, even if the refinery runs perfectly.

**Example:** the crack falls from $34 to $30. The refiner's margin falls by
$4 x 10,000 barrels = **$40,000**.

The refiner wants to remove this risk, so it hedges by **selling the crack**. Our desk takes the
other side: it **buys the crack**. That means long gasoline and diesel futures, and short crude
futures. If the crack falls by $4, the refiner's hedge gains $40,000, and the desk loses $40,000.
        """
    )

    st.subheader("The desk's job")
    md(
        """
The desk now carries the risk that the client has removed. For one month (21 trading days), it must:

1. **Open the position:** short 10,000 barrels of crude, long 6,667 barrels of gasoline,
   long 3,333 barrels of diesel, using futures.
2. **Mark it every day** and explain where the P&L comes from.
3. **Roll the futures** when the near contract expires.
4. **Watch the risks the position does not remove:** basis risk and curve risk.
        """
    )

    st.subheader("Questions this app answers")
    md(
        """
- How much can the desk make or lose in a month?
- Where does the P&L come from: price moves, the futures curve (roll), or funding?
- Which risks are left after the trade?
- How robust is the result when volatility or correlations change?
        """
    )

    st.subheader("Headline results")
    price_all, roll_all, funding_all, total_all = overview_numbers()
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Roll P&L, average per month", usd(roll_all.mean()))
    h2.metric("Price P&L, typical swing", f"+/- {usd(price_all.std())}")
    h3.metric("Funding, per month", usd(funding_all.mean()))
    h4.metric("Months with a profit", f"{(total_all > 0).mean() * 100:.0f}%")
    md(
        f"The position earns about **{usd(roll_all.mean())}** a month from the shape of the futures "
        f"curve. The price moves around that by about **+/- {usd(price_all.std())}**. "
        f"The curve gain is steady, and the price risk is not. "
        f"Across 500 simulated months, the worst month was **{usd(total_all.min())}** "
        f"and the best was **{usd(total_all.max())}**."
    )
    cap(
        "Based on 500 simulated months with the default settings. "
        "These numbers do not change with the sidebar."
    )

    st.subheader("How to read this app")
    md(
        """
| Tab | What it shows | Status |
|---|---|---|
| **Market** | Simulated prices, the crack spread, the futures curves | Ready |
| **Position & P&L** | The position, a daily trading log, the P&L split, the roll | Ready |
| **Risk** | Basis exposure and curve sensitivity | Ready |
| **Scenarios & Report** | Volatility and correlation scenarios, summary report | Ready |
        """
    )

    st.subheader("Why this project")
    md(
        """
This is a learning project. It shows, with numbers, how a flow desk thinks about a client's hedge
request: what position it takes, what drives its P&L, and which risks remain.
It is built in Python and Streamlit, and every number can be traced to a short, readable function.
        """
    )

    with st.expander("Assumptions and limits"):
        md(
            """
- **All prices are simulated.** They are random paths with a fixed seed. There is no market data.
- **The futures curves are assumptions.** They use cost of carry, with carry of +4% for crude,
  -12% for gasoline and -10% for diesel. Real curves change every day.
- **One roll,** on day 10 of the month.
- **Funding** assumes a margin of 10% of the crude leg ($78,000) and a 2% rate.
  There are no trading costs and no slippage.
- **The 3:2:1 crack is a simplified refinery.** A real refiner's margin does not move exactly like
  the futures crack. That gap is basis risk.
- This is an educational simulation. It is not trading advice.
            """
        )

    with st.expander("Key terms"):
        md(
            """
- **Flow trading:** taking clients' orders and managing the position that results.
- **Futures contract:** an agreement to buy or sell at a set price on a future date.
- **Crack spread:** the price of refined products minus the price of crude oil.
- **Backwardation:** later futures contracts cost less than the near one.
- **Contango:** later futures contracts cost more than the near one.
- **Roll:** when a futures contract expires, replacing it with the next one.
- **Roll yield:** the gain or cost that comes from rolling, because of the shape of the curve.
- **Basis:** the gap between the hedge instrument (the futures) and the price the client
  really pays or receives.
- **Carry:** interest + storage cost - convenience yield. It sets the shape of the futures curve.
            """
        )

with tab1:
    st.subheader("Starting market (day 0)")
    cap("These are the underlying prices. The futures curve is built on top of them below.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Crude", f"${LEGS_0[0]:,.2f} per barrel")
    m2.metric("Gasoline", f"${LEGS_0[1]:,.2f} per barrel")
    m2.caption(esc(f"${GASOLINE_0_GAL:.2f} per gallon x {GALLONS_PER_BARREL} gallons"))
    m3.metric("Diesel", f"${LEGS_0[2]:,.2f} per barrel")
    m3.caption(esc(f"${DIESEL_0_GAL:.2f} per gallon x {GALLONS_PER_BARREL} gallons"))

    st.subheader("Simulated prices (underlying)")
    cap(
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
        cap(f"The charts show the first {MAX_LINES} paths only.")

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

    # ----- The crack -----
    st.subheader("The 3:2:1 crack spread")
    st.metric("Crack on day 0", f"${crack_paths[0, 0]:,.2f} per barrel")
    cap(
        f"(2 x {LEGS_0[1]:,.0f} + {LEGS_0[2]:,.0f}) / 3 - {LEGS_0[0]:,.0f} "
        f"= {(2 * LEGS_0[1] + LEGS_0[2]) / 3:,.0f} - {LEGS_0[0]:,.0f} "
        f"= {crack_paths[0, 0]:,.2f} USD per barrel of crude"
    )

    crack_fig = go.Figure()
    for p in range(min(n_paths, MAX_LINES)):
        crack_fig.add_trace(go.Scatter(
            x=days_axis, y=crack_paths[p], mode="lines", name=f"Path {p + 1}"
        ))
    crack_fig.update_layout(
        title="3:2:1 crack spread along each path",
        xaxis_title="Trading day",
        yaxis_title="USD per barrel of crude",
        height=380,
    )
    st.plotly_chart(crack_fig)

    crack_rows = []
    for p in range(n_paths):
        crack_rows.append({
            "Path": p + 1,
            "Crack day 0": round(crack_paths[p, 0], 2),
            "Crack day 21": round(crack_paths[p, -1], 2),
            "Change": round(crack_paths[p, -1] - crack_paths[p, 0], 2),
            "Lowest": round(crack_paths[p].min(), 2),
            "Highest": round(crack_paths[p].max(), 2),
        })
    st.dataframe(pd.DataFrame(crack_rows), hide_index=True)

    with st.expander("How the crack is calculated"):
        md(
            """
- The **crack spread** is what a refiner earns, roughly, by turning crude oil into products.
- The **3:2:1** rule is a simple model of a refinery: **3 barrels of crude** become
  **2 barrels of gasoline** and **1 barrel of diesel**.
- Crack = (2 x gasoline + 1 x diesel) / 3 - crude, in USD per barrel of crude.
- With our prices: (2 x 105 + 126) / 3 = 112. Crude is 78. The crack is **34**.
- If the crack goes up, refining is more profitable. If it goes down, margins shrink.
            """
        )

    # ----- Futures curves -----
    st.subheader("Futures curves (cost of carry)")
    cap(
        "A futures price is not the same as the underlying price. "
        "It depends on how long until the contract expires."
    )

    near_day = NEAR_EXPIRY_DAY
    next_day = NEAR_EXPIRY_DAY + CONTRACT_GAP_DAYS
    curve_rows = []
    for i, name in enumerate(LEG_NAMES):
        near_price = futures_price(LEGS_0[i], CARRY[i], near_day)
        next_price = futures_price(LEGS_0[i], CARRY[i], next_day)
        curve_rows.append({
            "Leg": name,
            "Carry (per year)": f"{CARRY[i] * 100:+.0f}%",
            "Underlying": round(LEGS_0[i], 2),
            f"Near contract (expires day {near_day})": round(near_price, 2),
            f"Next contract (expires day {next_day})": round(next_price, 2),
            "Shape": "Contango" if CARRY[i] > 0 else "Backwardation",
        })
    st.dataframe(pd.DataFrame(curve_rows), hide_index=True)

    curve_days = np.arange(0, CURVE_CHART_DAYS + 1)
    curve_fig = go.Figure()
    for i, name in enumerate(LEG_NAMES):
        pct = (np.exp(CARRY[i] * curve_days * DT) - 1) * 100
        curve_fig.add_trace(go.Scatter(x=curve_days, y=pct, mode="lines", name=name))
    curve_fig.add_vline(x=near_day, line_dash="dot", annotation_text="near expiry")
    curve_fig.add_vline(x=next_day, line_dash="dot", annotation_text="next expiry")
    curve_fig.update_layout(
        title="Futures curve on day 0, as % above or below the underlying price",
        xaxis_title="Days until the contract expires",
        yaxis_title="% vs underlying",
        height=380,
    )
    st.plotly_chart(curve_fig)

    with st.expander("How the futures curve is built"):
        md(
            """
**Cost of carry.** A futures price = underlying price x exp(carry x time to expiry).
Carry = interest rate + storage cost - convenience yield, all per year.

- **Interest rate:** 2%. Holding oil instead of cash costs interest.
- **Storage:** crude 3%, gasoline 2%, diesel 2%.
- **Convenience yield:** the benefit of having oil now. It is high for gasoline (16%) and
  diesel (14%) when the market is tight, and low for crude (1%).

So: crude carry = 2% + 3% - 1% = **+4%** (contango: later contracts cost more).
Gasoline carry = 2% + 2% - 16% = **-12%** (backwardation: later contracts cost less).
Diesel carry = 2% + 2% - 14% = **-10%** (backwardation).

**Example, gasoline.** Underlying 105. The contract expiring in 10 days costs
105 x exp(-0.12 x 10/252) = **104.50**. The contract expiring in 31 days costs
105 x exp(-0.12 x 31/252) = **103.46**.

These carry values are our assumptions, chosen to show both shapes. They are not market data.
            """
        )

    with st.expander("How the prices are simulated"):
        md(
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
    st.subheader("The position: long the 3:2:1 crack")
    cap(
        "The refiner sells the crack to protect its margin. The desk takes the other side "
        "and goes long the crack: short crude, long gasoline and diesel."
    )

    position_rows = []
    for i, name in enumerate(LEG_NAMES):
        position_rows.append({
            "Leg": name,
            "Side": "Long" if POSITION_BBL[i] > 0 else "Short",
            "Barrels": round(abs(POSITION_BBL[i])),
            "Contracts (1,000 bbl)": round(abs(POSITION_BBL[i]) / CONTRACT_BBL, 2),
            "Day 0 price (USD/bbl)": round(LEGS_0[i], 2),
        })
    st.dataframe(pd.DataFrame(position_rows), hide_index=True)
    cap(
        f"A move of 1 USD in the crack is worth 1 x {NOTIONAL_BBL:,} barrels = "
        f"${NOTIONAL_BBL:,} for the desk. Funding: the desk posts a margin of "
        f"${MARGIN_USD:,.0f} (10% of the crude leg) and pays {R * 100:.0f}% a year to finance it, "
        f"which is ${-DAILY_FUNDING:,.2f} per day."
    )

    # ----- Pick a path and read its results -----
    st.subheader("Daily trading log")
    chosen = st.number_input("Path to show", min_value=1, max_value=int(n_paths), value=1, step=1)
    k = chosen - 1
    r = results[k]

    price_total = r["price_pnl"].sum(axis=1)
    roll_total = r["roll_pnl"].sum(axis=1)
    cum_price = np.cumsum(price_total)
    cum_roll = np.cumsum(roll_total)
    cum_funding = np.cumsum(r["funding"])

    md("**Prices**")
    prices_log = pd.DataFrame({
        "Day": days_axis,
        "Contract held": r["contract"],
        "Crude": r["underlying"][:, 0].round(2),
        "Gasoline": r["underlying"][:, 1].round(2),
        "Diesel": r["underlying"][:, 2].round(2),
        "Crack": r["crack"].round(2),
        "Crude future": r["held_price"][:, 0].round(2),
        "Gasoline future": r["held_price"][:, 1].round(2),
        "Diesel future": r["held_price"][:, 2].round(2),
        "Futures crack": r["held_crack"].round(2),
    })
    st.dataframe(prices_log, hide_index=True)
    cap(
        "Crude, Gasoline, Diesel and Crack are the underlying prices. "
        "The 'future' columns are the prices of the contracts the desk holds."
    )

    md("**P&L (USD)**")
    pnl_log = pd.DataFrame({
        "Day": days_axis,
        "Price P&L": price_total.round(0),
        "Roll P&L": roll_total.round(0),
        "Funding": r["funding"].round(2),
        "Daily P&L": r["daily_pnl"].round(0),
        "Cumulative P&L": r["cum_pnl"].round(0),
    })
    st.dataframe(pnl_log, hide_index=True)
    cap("Daily P&L = price P&L + roll P&L + funding.")

    st.download_button(
        "Download the daily log (CSV)",
        data=pd.concat([prices_log, pnl_log.drop(columns="Day")], axis=1).to_csv(index=False),
        file_name=f"daily_log_path_{chosen}.csv",
        mime="text/csv",
    )

    # ----- Cumulative P&L by source -----
    pnl_fig = go.Figure()
    pnl_fig.add_trace(go.Scatter(x=days_axis, y=cum_price, mode="lines", name="Price effect"))
    pnl_fig.add_trace(go.Scatter(x=days_axis, y=cum_roll, mode="lines", name="Roll effect"))
    pnl_fig.add_trace(go.Scatter(x=days_axis, y=cum_funding, mode="lines", name="Funding"))
    pnl_fig.add_trace(go.Scatter(
        x=days_axis, y=r["cum_pnl"], mode="lines", name="Total P&L",
        line=dict(width=4, color="white"),
    ))
    pnl_fig.add_vline(x=NEAR_EXPIRY_DAY, line_dash="dot", annotation_text="roll")
    pnl_fig.update_layout(
        title=f"Cumulative P&L by source, path {chosen}",
        xaxis_title="Trading day",
        yaxis_title="USD",
        height=400,
    )
    st.plotly_chart(pnl_fig)

    # ----- P&L by leg -----
    leg_price = r["price_pnl"].sum(axis=0)
    leg_roll = r["roll_pnl"].sum(axis=0)
    leg_rows = []
    for i, name in enumerate(LEG_NAMES):
        flat_estimate = -POSITION_BBL[i] * LEGS_0[i] * CARRY[i] * DAYS * DT
        leg_rows.append({
            "Leg": name,
            "Price effect (USD)": round(leg_price[i]),
            "Roll effect (USD)": round(leg_roll[i]),
            "Total (USD)": round(leg_price[i] + leg_roll[i]),
            "Roll estimate, flat prices (USD)": round(flat_estimate),
        })
    leg_rows.append({
        "Leg": "Funding",
        "Price effect (USD)": 0,
        "Roll effect (USD)": 0,
        "Total (USD)": round(r["funding"].sum()),
        "Roll estimate, flat prices (USD)": 0,
    })
    leg_rows.append({
        "Leg": "Total",
        "Price effect (USD)": round(leg_price.sum()),
        "Roll effect (USD)": round(leg_roll.sum()),
        "Total (USD)": round(r["cum_pnl"][-1]),
        "Roll estimate, flat prices (USD)": round(sum(row["Roll estimate, flat prices (USD)"] for row in leg_rows)),
    })
    md("**P&L by leg, day 21**")
    st.dataframe(pd.DataFrame(leg_rows), hide_index=True)

    crack_change = crack_paths[k, -1] - crack_paths[k, 0]
    cap(
        f"Check 1: the crack moved {crack_change:+.2f} USD. "
        f"{crack_change:+.2f} x {NOTIONAL_BBL:,} = {crack_change * NOTIONAL_BBL:+,.0f} USD, "
        f"the same as the price effect. "
        f"Check 2: price effect {leg_price.sum():+,.0f} + roll effect {leg_roll.sum():+,.0f} "
        f"+ funding {r['funding'].sum():+,.0f} = total {r['cum_pnl'][-1]:+,.0f} USD."
    )

    # ----- The roll event -----
    st.subheader(f"The roll on day {NEAR_EXPIRY_DAY}")
    near_prices = paths[k, NEAR_EXPIRY_DAY, :]                 # the near contract expires at the underlying
    next_prices = futures_price(near_prices, np.array(CARRY), CONTRACT_GAP_DAYS)
    yields = roll_yield(near_prices, next_prices)
    roll_rows = []
    for i, name in enumerate(LEG_NAMES):
        long_leg = POSITION_BBL[i] > 0
        desk_gain = yields[i] > 0 if long_leg else yields[i] < 0
        roll_rows.append({
            "Leg": name,
            "Desk position": "Long" if long_leg else "Short",
            "Near contract (USD/bbl)": round(near_prices[i], 2),
            "Next contract (USD/bbl)": round(next_prices[i], 2),
            "Roll yield (near - next) / near": f"{yields[i] * 100:+.2f}%",
            "Market shape": "Backwardation" if yields[i] > 0 else "Contango",
            "Effect for the desk": "Gain" if desk_gain else "Cost",
        })
    st.dataframe(pd.DataFrame(roll_rows), hide_index=True)

    # ----- All paths -----
    st.subheader("All simulated months")
    all_fig = go.Figure()
    for p in range(min(n_paths, MAX_LINES)):
        all_fig.add_trace(go.Scatter(
            x=days_axis, y=results[p]["cum_pnl"], mode="lines", name=f"Path {p + 1}"
        ))
    all_fig.update_layout(
        title="Cumulative total P&L, each path",
        xaxis_title="Trading day",
        yaxis_title="USD",
        height=400,
    )
    st.plotly_chart(all_fig)
    if n_paths > MAX_LINES:
        cap(f"The chart shows the first {MAX_LINES} paths only. The table and numbers below use all {n_paths}.")

    summary_rows = []
    for p in range(n_paths):
        res = results[p]
        summary_rows.append({
            "Path": p + 1,
            "Price effect (USD)": round(res["price_pnl"].sum()),
            "Roll effect (USD)": round(res["roll_pnl"].sum()),
            "Funding (USD)": round(res["funding"].sum()),
            "Total P&L (USD)": round(res["cum_pnl"][-1]),
        })
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, hide_index=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Average total P&L", usd(summary_df["Total P&L (USD)"].mean()))
    s2.metric("Worst path", usd(summary_df["Total P&L (USD)"].min()))
    s3.metric("Best path", usd(summary_df["Total P&L (USD)"].max()))
    s4.metric("Paths with a profit", f"{(summary_df['Total P&L (USD)'] > 0).mean() * 100:.0f}%")

    with st.expander("How the daily P&L is built"):
        md(
            f"""
Every day, the desk's P&L has three parts:

1. **Price P&L** = barrels x change in the underlying price, for each leg.
   Example: gasoline rises by 1 USD. The desk is long 6,667 barrels, so it gains **$6,667**.
   Crude rises by 1 USD. The desk is short 10,000 barrels, so it loses **$10,000**.
2. **Roll P&L** = P&L of the futures contract the desk holds, minus the price P&L.
   It comes from the shape of the curve (see the Market tab). It is small each day and steady.
3. **Funding** = the cost of financing the margin.
   {R * 100:.0f}% x ${MARGIN_USD:,.0f} / 252 = **${-DAILY_FUNDING:,.2f} per day**, so about
   ${-DAILY_FUNDING * DAYS:,.0f} over the month. It is tiny compared with the other two.

**The loop.** The code goes through the days one by one. On day 0 it opens the position in the near
contract. Each day it updates the prices, works out the three parts, and adds them to the total.
On day {NEAR_EXPIRY_DAY} the near contract expires. The desk rolls at the close, and from day
{NEAR_EXPIRY_DAY + 1} it holds the next contract.

**Reading the results.** The price P&L is random and can be large in both directions. The roll P&L
and funding are almost the same in every path. That is the nature of this trade: a steady gain from
the curve against a risk from price moves.
            """
        )

    with st.expander("How the roll works"):
        md(
            f"""
- A futures contract expires. On day {NEAR_EXPIRY_DAY}, the near contract expires and the desk
  **rolls**: it closes the near contract and opens the next one, to keep the same position.
- **Roll yield** = (near price - next price) / near price.
  Positive in backwardation (the next contract is cheaper). Negative in contango.
- A **long** position gains from backwardation. A **short** position gains from contango.
- The desk is long gasoline and diesel (backwardation) and short crude (contango).
  So all three legs earn roll yield in this simulation.

**Example, gasoline, if the price stays flat at 105.**
- The near contract is worth 104.50 on day 0 and converges to 105 on day {NEAR_EXPIRY_DAY}: **+0.50**.
- The next contract goes from 103.96 on day {NEAR_EXPIRY_DAY} to 104.50 on day 21: **+0.54**.
- Total: about **+1.04 per barrel** x 6,667 barrels = **about +$7,000**.

The same logic gives about +$3,500 for diesel and about +$2,600 for crude (the desk is short crude
and crude is in contango). So the roll effect is about **+$13,000** for the month.

**Price effect** = barrels x change in the underlying price. **Roll effect** = what the curve adds
or takes away, because contracts move toward the underlying price as they get closer to expiry.
            """
        )

@st.cache_data
def risk_numbers():
    """500 simulated months with the default settings: basis statistics for the Risk tab."""
    sim = simulate_correlated_paths(LEGS_0, MU, SIGMA, CORR, DAYS, 500, SEED)
    bas = simulate_basis(500, DAYS, BASIS_VOL, BASIS_PERSISTENCE, SEED + BASIS_SEED_OFFSET)
    und_crack = compute_crack(sim[:, :, 0], sim[:, :, 1], sim[:, :, 2])
    bas_crack = compute_crack(bas[:, :, 0], bas[:, :, 1], bas[:, :, 2])
    # Change over the month of the refiner's physical margin, before the hedge
    unhedged = (und_crack[:, -1] - und_crack[:, 0] + bas_crack[:, -1] - bas_crack[:, 0]) * NOTIONAL_BBL
    # What is left after the futures hedge: only the basis
    residual = (bas_crack[:, -1] - bas_crack[:, 0]) * NOTIONAL_BBL
    daily_basis_vol = np.diff(bas_crack, axis=1).std()
    return unhedged, residual, daily_basis_vol


with tab3:
    st.subheader("Risk: what the position does not remove")
    cap(
        "The futures hedge removes most of the refiner's price risk, but not all of it. "
        "Two risks are left: basis risk and curve risk."
    )

    # ===================== 1. Basis risk =====================
    st.subheader("1. Basis risk: the refiner's physical margin vs the futures hedge")
    md(
        """
The refiner does not sell gasoline at the futures price. It sells at a local, physical price.
The gap between the two is the **basis**: physical price minus futures-referenced price.
The hedge follows the futures, so any move in the basis is **not covered**.
Our desk prices and explains this hedge, so it must know how well it works.
        """
    )

    exposure_rows = []
    for i, name in enumerate(LEG_NAMES):
        exposure_rows.append({
            "Leg": name,
            "Barrels": round(abs(POSITION_BBL[i])),
            "Margin changes by (USD) if this leg's basis moves by 1 USD": round(abs(POSITION_BBL[i])),
            "Assumed basis shock per day (USD/bbl)": BASIS_VOL[i],
        })
    md("**Basis exposure by leg**")
    st.dataframe(pd.DataFrame(exposure_rows), hide_index=True)
    cap(
        f"For the whole crack: a 1 USD move in the crack basis changes the refiner's margin by "
        f"{NOTIONAL_BBL:,} x 1 = ${NOTIONAL_BBL:,}, and the hedge does not offset it."
    )

    unhedged, residual, daily_basis_vol = risk_numbers()
    effectiveness = 1 - residual.var() / unhedged.var()
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Basis exposure", f"${NOTIONAL_BBL:,} per $1")
    b2.metric("Daily basis volatility (crack)", f"${daily_basis_vol:.2f} per barrel")
    b3.metric("Risk left after the hedge", f"+/- {usd(residual.std())} a month")
    b4.metric("Hedge effectiveness", f"{effectiveness * 100:.0f}%")
    md(
        f"Without a hedge, the refiner's margin moves by about **+/- {usd(unhedged.std())}** in a month. "
        f"After the futures hedge, about **+/- {usd(residual.std())}** is left. "
        f"The hedge removes about **{effectiveness * 100:.0f}%** of the risk. The rest is basis."
    )
    cap("Based on 500 simulated months with the default settings. These numbers do not change with the sidebar.")

    hist_fig = go.Figure()
    hist_fig.add_trace(go.Histogram(x=unhedged, name="No hedge", opacity=0.65, nbinsx=40))
    hist_fig.add_trace(go.Histogram(x=residual, name="After the futures hedge", opacity=0.65, nbinsx=40))
    hist_fig.update_layout(
        barmode="overlay",
        title="Change in the refiner's margin over one month, 500 simulated months",
        xaxis_title="USD",
        yaxis_title="Number of months",
        height=380,
    )
    st.plotly_chart(hist_fig)

    # ----- Basis along one path -----
    basis = simulate_basis(n_paths, DAYS, BASIS_VOL, BASIS_PERSISTENCE, seed + BASIS_SEED_OFFSET)
    basis_crack = compute_crack(basis[:, :, 0], basis[:, :, 1], basis[:, :, 2])
    risk_path = st.number_input(
        "Path to show (basis chart)", min_value=1, max_value=int(n_paths), value=1, step=1, key="risk_path"
    )
    q = risk_path - 1
    physical_crack = crack_paths[q] + basis_crack[q]

    rc1, rc2 = st.columns(2)
    crack_basis_fig = go.Figure()
    crack_basis_fig.add_trace(go.Scatter(
        x=days_axis, y=crack_paths[q], mode="lines", name="Futures-referenced crack"))
    crack_basis_fig.add_trace(go.Scatter(
        x=days_axis, y=physical_crack, mode="lines", name="Physical crack (the refiner's margin)"))
    crack_basis_fig.update_layout(
        title=f"The two cracks, path {risk_path}",
        xaxis_title="Trading day", yaxis_title="USD per barrel", height=360,
        legend=dict(orientation="h", y=-0.3),
    )
    rc1.plotly_chart(crack_basis_fig)

    gap_fig = go.Figure()
    gap_fig.add_trace(go.Scatter(x=days_axis, y=basis_crack[q], mode="lines", name="Crack basis"))
    gap_fig.add_hline(y=0, line_dash="dot")
    gap_fig.update_layout(
        title=f"The gap between them (crack basis), path {risk_path}",
        xaxis_title="Trading day", yaxis_title="USD per barrel", height=360, showlegend=False,
    )
    rc2.plotly_chart(gap_fig)

    with st.expander("How the basis is modelled"):
        md(
            """
- Each leg has a basis: **physical price - futures-referenced price**, in USD per barrel.
- It starts at zero. Each day: **basis = 0.90 x yesterday's basis + a random shock**.
  The shock has a typical size of 0.20 USD for crude, 0.40 for gasoline and 0.35 for diesel.
- So the basis wanders, but it is pulled back towards zero. It is independent of the futures price.
- **Crack basis** = (2 x gasoline basis + diesel basis) / 3 - crude basis. Same formula as the crack.
- The refiner's margin change = crack move (hedged by futures) + crack basis change (not hedged).
- **Hedge effectiveness** = 1 - (risk left after the hedge)^2 / (risk without the hedge)^2.

**Example.** The crack basis goes from 0 to +0.80 USD. The refiner earns 0.80 x 10,000 = **$8,000**
more or less than its hedge predicts. A move of 1 USD would be $10,000.

These basis sizes are assumptions chosen to be realistic in order of magnitude. They are not market data.
            """
        )

    # ===================== 2. Curve risk =====================
    st.subheader("2. Curve risk: what if the shape of the curve changes?")
    md(
        """
The desk's steady gain comes from the shape of the futures curve (the roll effect, about $13,000
a month). If the curve changes shape, that gain changes. Here we re-run the same simulated months
with a different curve. **The prices are identical, so every difference comes from the curve.**
        """
    )

    sample = paths[:min(n_paths, 100)]
    base_price, base_roll, base_total = average_pnl(
        sample, POSITION_BBL, CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING
    )

    sens_rows = []
    for i, name in enumerate(LEG_NAMES):
        bumped = list(CARRY)
        bumped[i] += CURVE_BUMP
        _, _, bumped_total = average_pnl(
            sample, POSITION_BBL, bumped, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING
        )
        change = bumped_total - base_total
        sens_rows.append({
            "Leg": name,
            "Desk position": "Long" if POSITION_BBL[i] > 0 else "Short",
            "Carry now (per year)": f"{CARRY[i] * 100:+.0f}%",
            "P&L change if carry rises by 1 point (USD)": round(change),
            "Effect": "Gain" if change > 0 else "Cost",
        })
    md("**Curve sensitivity: carry up by 1 percentage point, one leg at a time**")
    st.dataframe(pd.DataFrame(sens_rows), hide_index=True)

    scenario_rows = [{
        "Scenario": "Base case",
        "Carry crude / gasoline / diesel": " / ".join(f"{c * 100:+.0f}%" for c in CARRY),
        "Roll effect (USD)": round(base_roll),
        "Total P&L (USD)": round(base_total),
        "Change vs base (USD)": 0,
    }]
    for scenario_name, shift in CURVE_SCENARIOS.items():
        new_carry = [c + s for c, s in zip(CARRY, shift)]
        _, scenario_roll, scenario_total = average_pnl(
            sample, POSITION_BBL, new_carry, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING
        )
        scenario_rows.append({
            "Scenario": scenario_name,
            "Carry crude / gasoline / diesel": " / ".join(f"{c * 100:+.0f}%" for c in new_carry),
            "Roll effect (USD)": round(scenario_roll),
            "Total P&L (USD)": round(scenario_total),
            "Change vs base (USD)": round(scenario_total - base_total),
        })
    scenario_df = pd.DataFrame(scenario_rows)
    md("**Curve scenarios**")
    st.dataframe(scenario_df, hide_index=True)
    cap(f"Average over the first {len(sample)} simulated months. Funding is included in the totals.")

    scenario_fig = go.Figure(go.Bar(
        x=scenario_df["Scenario"][1:], y=scenario_df["Change vs base (USD)"][1:],
        text=scenario_df["Change vs base (USD)"][1:], textposition="outside",
    ))
    scenario_fig.update_layout(
        title="Change in the month's P&L compared with the base curve",
        yaxis_title="USD", height=380,
    )
    st.plotly_chart(scenario_fig)

    with st.expander("How to read the curve risk"):
        md(
            """
- **Steepening** means the contracts further out move further away from the near contract.
  For a backwardated leg, the curve slopes down more. For a contango leg, it slopes up more.
- **Flattening** is the opposite: the curve gets closer to flat.
- The desk is **long gasoline and diesel**, which are in backwardation. It gains the roll yield.
  If that backwardation **flattens**, the gain shrinks. If it **steepens**, the gain grows.
- The desk is **short crude**, which is in contango. If the contango **steepens**, the desk gains more.
  If crude moves to backwardation, the desk loses part of its gain.

**Example, gasoline.** Carry goes from -12% to -4%, a flatter curve. The roll gain on gasoline
falls from about $7,000 to about $2,300: 6,667 barrels x $105 x 8% x 21/252 = about $4,700 less.

In this model the curve is fixed for the whole month. In real markets the curve also changes
during the month, which moves the daily P&L as well.
            """
        )

@st.cache_data
def scenario_results():
    """Run every scenario once: 500 simulated months each, with the same random numbers."""
    out = {}
    for name, setting in SCENARIOS.items():
        sigma = [s * setting["vol_mult"] for s in SIGMA]
        if setting["corr"] is None:
            corr = CORR
        else:
            corr = equal_correlation(setting["corr"], len(LEG_NAMES))
        result = run_scenario(
            LEGS_0, MU, sigma, corr, DAYS, SCENARIO_PATHS, SEED,
            POSITION_BBL, CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING,
        )
        out[name] = {"summary": summarize(result), "total": result["total"]}

    # Edge case: a thin crack with extreme volatility
    thin_result = run_scenario(
        THIN_CRACK_LEGS_0, MU, [s * THIN_CRACK_VOL_MULT for s in SIGMA], CORR, DAYS, SCENARIO_PATHS, SEED,
        POSITION_BBL, CARRY, NEAR_EXPIRY_DAY, CONTRACT_GAP_DAYS, DAILY_FUNDING,
    )
    return out, summarize(thin_result)


with tab4:
    st.subheader("Scenarios: how robust is the result?")
    cap(
        f"The same position and the same random numbers, with different market conditions. "
        f"{SCENARIO_PATHS} simulated months in each scenario. "
        f"These results do not change with the sidebar."
    )

    scenarios, thin = scenario_results()
    base = scenarios["Base case"]["summary"]

    scenario_rows = []
    for name, item in scenarios.items():
        s = item["summary"]
        scenario_rows.append({
            "Scenario": name,
            "Average P&L (USD)": round(s["average"]),
            "Risk (USD)": round(s["risk"]),
            "Worst 5% of months (USD)": round(s["worst_5pct"]),
            "Worst month (USD)": round(s["worst"]),
            "Best month (USD)": round(s["best"]),
            "Months with a profit": f"{s['profit_share'] * 100:.0f}%",
            "Roll P&L (USD)": round(s["roll"]),
            "Gain per unit of risk": round(s["efficiency"], 2),
        })
    scenario_table = pd.DataFrame(scenario_rows)
    st.dataframe(scenario_table, hide_index=True)
    cap(
        "Risk = standard deviation of the monthly P&L. "
        "Worst 5% of months = 5% of months ended below this number. "
        "Gain per unit of risk = average P&L / risk."
    )
    st.download_button(
        "Download the scenario table (CSV)",
        data=scenario_table.to_csv(index=False),
        file_name="scenario_table.csv",
        mime="text/csv",
    )

    box_fig = go.Figure()
    for name, item in scenarios.items():
        box_fig.add_trace(go.Box(y=item["total"], name=name, boxpoints=False))
    box_fig.update_layout(
        title="Total P&L over one month, by scenario",
        yaxis_title="USD",
        height=450,
        showlegend=False,
        xaxis=dict(tickangle=-25),
    )
    st.plotly_chart(box_fig)

    vol2 = scenarios["Volatility x2"]["summary"]
    corr5 = scenarios["Correlation 0.5"]["summary"]
    corr9 = scenarios["Correlation 0.9"]["summary"]
    stress = scenarios["Stress: volatility x2 and correlation 0.5"]["summary"]
    averages = [item["summary"]["average"] for item in scenarios.values()]

    st.subheader("What the scenarios show")
    md(
        f"""
- **Volatility.** Doubling the volatility raises the monthly risk from {usd(base['risk'])} to
  {usd(vol2['risk'])}, about {vol2['risk'] / base['risk']:.1f} times more. The roll gain stays at about
  {usd(vol2['roll'])} a month, so it covers a smaller part of the risk. The gain per unit of risk falls
  from {base['efficiency']:.2f} to {vol2['efficiency']:.2f}.
- **Correlation.** Moving the correlation between the legs from 0.9 to 0.5 raises the risk from
  {usd(corr9['risk'])} to {usd(corr5['risk'])}. The desk is long products and short crude. When the legs
  move together, gains on one side offset losses on the other. When they move apart, the offset is weaker.
- **Both together.** With volatility x2 and correlation 0.5, the risk is {usd(stress['risk'])} and the
  worst month is {usd(stress['worst'])}. The roll gain of {usd(stress['roll'])} is small next to this.
- **Average P&L.** It stays between {usd(min(averages))} and {usd(max(averages))} in all scenarios.
  These differences are mostly random noise from using 500 months. The risk changes much more than the average.
        """
    )

    with st.expander("How the scenarios are built"):
        md(
            """
- Each scenario simulates 500 months with the **same random numbers**, so differences come from the
  scenario and not from luck.
- **Volatility x2** multiplies the volatility of crude, gasoline and diesel by 2
  (25%, 20%, 18% become 50%, 40%, 36%).
- **Correlation 0.5 / 0.7 / 0.9** sets the correlation of every pair of legs to that number.
  The base case uses 0.80, 0.75 and 0.85.
- The curves, the position, the roll and the funding are the same in every scenario.
- **Gain per unit of risk** = average monthly P&L / risk. It is similar in spirit to a Sharpe ratio,
  but for one month, and without a risk-free rate.
            """
        )

    # ===================== Edge case =====================
    st.subheader("Edge case: a thin crack and extreme volatility")
    md(
        f"""
What if the crack starts near zero, and the volatility is doubled? Prices cannot go below zero in this
model, but the **crack** can: if gasoline and diesel fall while crude rises. Here the starting prices are
crude {THIN_CRACK_LEGS_0[0]:.0f}, gasoline {THIN_CRACK_LEGS_0[1]:.0f} and diesel {THIN_CRACK_LEGS_0[2]:.0f},
so the crack starts at **${thin['start_crack']:.2f}**.
        """
    )
    thin_rows = [
        ("Starting crack", f"${thin['start_crack']:.2f} per barrel"),
        ("Lowest crack seen in any month", f"{'-' if thin['lowest_crack'] < 0 else ''}${abs(thin['lowest_crack']):.2f} per barrel"),
        ("Months where the crack went below zero", f"{thin['negative_crack_share'] * 100:.0f}%"),
        ("Average P&L", usd(thin["average"])),
        ("Risk", usd(thin["risk"])),
        ("Worst month", usd(thin["worst"])),
    ]
    st.dataframe(pd.DataFrame(thin_rows, columns=["Metric", "Value"]), hide_index=True)
    md(
        "**Result:** a negative crack is not a problem for the position. It is made of futures, "
        "so its P&L moves one for one with the prices, with no floor. "
        "A client contract with a floor at zero would be an option, and it would need option pricing. "
        "That is outside this model."
    )

    # ===================== Summary report =====================
    st.subheader("Summary report (base case)")
    unhedged_r, residual_r, _ = risk_numbers()
    effectiveness_r = 1 - residual_r.var() / unhedged_r.var()
    report_rows = [
        ("Position", f"Long 3:2:1 crack, {NOTIONAL_BBL:,} barrels, {DAYS} trading days"),
        ("Simulated months", f"{SCENARIO_PATHS}"),
        ("Average total P&L", usd(base["average"])),
        ("   of which roll yield", usd(base["roll"])),
        ("   of which price moves", usd(base["price"])),
        ("   of which funding", usd(base["funding"])),
        ("Risk (standard deviation of the monthly P&L)", usd(base["risk"])),
        ("Worst 5% of months are below", usd(base["worst_5pct"])),
        ("Worst month / best month", f"{usd(base['worst'])} / {usd(base['best'])}"),
        ("Months with a profit", f"{base['profit_share'] * 100:.0f}%"),
        ("Gain per unit of risk (average P&L / risk)", f"{base['efficiency']:.2f}"),
        ("Basis risk left after the futures hedge (refiner)", f"+/- {usd(residual_r.std())} a month"),
        ("Hedge effectiveness (refiner)", f"{effectiveness_r * 100:.0f}%"),
    ]
    st.dataframe(pd.DataFrame(report_rows, columns=["Metric", "Value"]), hide_index=True)

    md(
        f"""
**Key points**
- The position earns about **{usd(base['roll'])}** a month from the shape of the futures curve.
  This part is steady.
- The price moves add or take away about **{usd(base['risk'])}** a month (one standard deviation).
  The roll gain is about {base['roll'] / base['risk'] * 100:.0f}% of that.
- The desk made a profit in **{base['profit_share'] * 100:.0f}%** of months. In the worst 5% of months, it lost
  more than **{usd(-base['worst_5pct'])}**.
- Risk grows with volatility and falls with correlation between the legs. The roll gain does not change.
- The refiner's futures hedge removes about **{effectiveness_r * 100:.0f}%** of its risk. The rest is basis.
        """
    )

