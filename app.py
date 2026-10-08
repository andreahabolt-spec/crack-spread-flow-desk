# app.py
# The screen only. Inputs come from data.py, maths from calc.py.

import altair as alt
import pandas as pd
import streamlit as st

import calc
import data


def money(x):
    """Format a dollar amount with its sign, e.g. +$30,000 or -$30,000."""
    sign = "+" if x > 0 else "-" if x < 0 else ""
    return f"{sign}${abs(x):,.0f}"


def equation(a, b):
    """Write 'a + b = total' with clean signs, for on-screen checks."""
    plain = lambda x: f"${abs(x):,.0f}"
    first = ("-" if a < 0 else "") + plain(a)
    second = ("- " if b < 0 else "+ ") + plain(b)
    return f"{first} {second} = **{money(a + b)}**".replace("$", "\\$")


st.set_page_config(page_title="Refiner crack-spread hedge", page_icon="🛢️")
st.title("Refiner crack-spread hedge")

tab1, tab2 = st.tabs(["Overview & Hedge Setup", "Simulation"])

# Values used in Tab 1
crack_0 = calc.compute_crack(data.CRUDE_0, data.GASOLINE_0, data.DIESEL_0)
vol_crude, vol_gas, vol_diesel = calc.hedge_volumes(data.CRUDE_VOLUME)

# ---------------------------------------------------------------
# TAB 1: Overview & Hedge Setup
# ---------------------------------------------------------------
with tab1:

    # 1. The client situation
    st.subheader("The situation")
    st.write(data.OVERVIEW_TEXT)

    # 2. Starting market and benchmark crack
    st.subheader("Starting benchmark futures prices")
    st.write(
        "Front-month futures: WTI crude, RBOB gasoline and NY Harbor ULSD "
        "diesel. Product futures are quoted in \\$/gal, so we convert them "
        "to \\$/bbl (1 bbl = 42 gal)."
    )

    gas_gal = data.GASOLINE_0 / data.GALLONS_PER_BBL
    diesel_gal = data.DIESEL_0 / data.GALLONS_PER_BBL

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Crude ($/bbl)", f"{data.CRUDE_0:.2f}")
    c2.metric("Gasoline ($/bbl)", f"{data.GASOLINE_0:.2f}")
    c3.metric("Diesel ($/bbl)", f"{data.DIESEL_0:.2f}")
    c4.metric("3:2:1 crack ($/bbl)", f"{crack_0:.2f}")

    st.markdown(
        f"Gasoline: \\${gas_gal:.4f}/gal × 42 = \\${data.GASOLINE_0:.2f}/bbl  \n"
        f"Diesel: \\${diesel_gal:.4f}/gal × 42 = \\${data.DIESEL_0:.2f}/bbl"
    )

    st.markdown(
        f"Crack = (2 × Gasoline + 1 × Diesel) / 3 − Crude  \n"
        f"= (2 × {data.GASOLINE_0:.2f} + 1 × {data.DIESEL_0:.2f}) / 3 "
        f"− {data.CRUDE_0:.2f} = **\\${crack_0:.2f}/bbl**"
    )
    st.caption(
        "These are futures prices, not the refiner's own physical prices. "
        "Its real crude cost and product sales can differ by location and "
        "quality. This gap is the basis risk shown in Tab 2."
    )
    st.info(
        f"The \\${crack_0:.0f}/bbl crack is the **benchmark margin** the hedge "
        "aims to protect. It is a starting reference, not the P&L of the "
        "simulation."
    )

    # 3. Hedge setup
    st.subheader("Hedge setup")
    st.write(
        "The refiner is naturally **long the crack**: it loses when product "
        "prices fall relative to crude. To protect its margin, the desk "
        "executes a **short crack hedge** with futures."
    )

    legs = pd.DataFrame({
        "Leg": ["Crude", "Gasoline", "Diesel"],
        "Direction": ["Buy", "Sell", "Sell"],
        "Volume (bbl)": [vol_crude, abs(vol_gas), abs(vol_diesel)],
        "Price ($/bbl)": [data.CRUDE_0, data.GASOLINE_0, data.DIESEL_0],
    })
    legs["Notional ($)"] = legs["Volume (bbl)"] * legs["Price ($/bbl)"]
    st.dataframe(
        legs.style.format({
            "Volume (bbl)": "{:,.0f}",
            "Price ($/bbl)": "{:.2f}",
            "Notional ($)": "{:,.0f}",
        }),
        hide_index=True,
        width="stretch",
    )

    terms = pd.DataFrame({
        "Term": ["Client", "Executed by", "Hedge direction", "Ratio",
                 "Size", "Horizon"],
        "Value": ["Refiner", "External commodities desk",
                  "Short crack (buy crude, sell products)",
                  "3:2:1 (3 crude → 2 gasoline + 1 diesel)",
                  f"{data.CRUDE_VOLUME:,} bbl of crude",
                  f"{data.DAYS} trading days (one month)"],
    })
    st.dataframe(terms, hide_index=True, width="stretch")

    st.caption(
        "Volumes are notional-equivalent barrels for the simulation. "
        "They do not necessarily match a whole number of exchange-traded "
        "contracts, and the 3:2:1 benchmark does not exactly match every "
        "refinery's real yield."
    )

    # 4. How the P&L works, with a worked example
    st.subheader("How the P&L works")
    st.markdown(
        "**Change in unhedged margin + Hedge P&L = Residual P&L**"
    )

    move = data.EXAMPLE_CRACK_MOVE
    unhedged, hedge, residual = calc.pnl_split(move, data.CRUDE_VOLUME)
    st.write(
        f"Example: the crack falls by \\${abs(move):.0f}/bbl, from "
        f"\\${crack_0:.0f} to \\${crack_0 + move:.0f}, on "
        f"{data.CRUDE_VOLUME:,} bbl."
    )

    example = pd.DataFrame({
        "Line": ["Change in unhedged margin", "Hedge P&L", "Residual P&L"],
        "Calculation": [
            f"{move:+.0f} × {data.CRUDE_VOLUME:,}",
            f"{-move:+.0f} × {data.CRUDE_VOLUME:,}",
            "sum of the two lines",
        ],
        "Amount": [money(unhedged), money(hedge), money(residual)],
    })
    st.dataframe(example, hide_index=True, width="stretch")

    st.write(
        "The residual is about \\$0 before basis differences and costs. "
        "Tab 2 shows what makes it move away from zero."
    )

    # 5. Limits of the hedge
    st.subheader("What the hedge does not guarantee")
    st.write(
        "The hedge protects the **benchmark** margin, not the refiner's "
        "actual net profit. Real crude costs, product yields, timing, "
        "location and operating costs can all differ from the benchmark."
    )

    # 6. Assumptions (closed by default to keep the tab short)
    with st.expander("Key assumptions"):
        st.markdown(
            f"- Tab 2 uses one illustrative price path (correlated GBM, "
            f"drift {data.MU:.0%}, correlation {data.CORR}), fixed so it is "
            f"the same at every rerun.\n"
            f"- Volatility: crude {data.SIGMA_CRUDE:.0%}, gasoline "
            f"{data.SIGMA_GASOLINE:.0%}, diesel {data.SIGMA_DIESEL:.0%} "
            f"per year.\n"
            f"- Interest rate {data.RISK_FREE:.0%}, continuous compounding.\n"
            "- No slippage and no fees.\n"
            "- Initial and variation margin are excluded from this P&L "
            "simulation (futures do require margin in practice)."
        )

# ---------------------------------------------------------------
# TAB 2: Simulation
# ---------------------------------------------------------------
# Chart settings shared by both charts
X_AXIS = alt.X(
    "Day:Q",
    title="Trading day (0 = hedge inception, 21 = final trading day)",
    scale=alt.Scale(domain=[0, data.DAYS]),
    axis=alt.Axis(values=list(range(data.DAYS + 1)), format="d"),
)
GREY = "#999999"

with tab2:

    st.subheader("Illustrative market path")
    st.info("Illustrative example, not a forecast. The same path is used "
            "at every rerun.")

    # 1. One fixed market path and basis path
    path = calc.simulate_price_path(
        [data.CRUDE_0, data.GASOLINE_0, data.DIESEL_0], data.MU,
        [data.SIGMA_CRUDE, data.SIGMA_GASOLINE, data.SIGMA_DIESEL],
        data.CORR, data.DAYS, data.PATH_SEED)
    basis = calc.simulate_basis(data.BASIS_0, data.BASIS_VOL, data.DAYS,
                                data.BASIS_SEED)

    # The curve slider sits in the roll section below; read its value here
    curve_spread = st.session_state.get("curve_spread", 0.0)

    res = calc.run_hedge(path, basis, curve_spread, data.CRUDE_VOLUME,
                         data.NEARBY_EXPIRY, data.ROLL_DAY,
                         data.DAYS_PER_MONTH)
    days = list(range(data.DAYS + 1))

    # Day-21 figures, rounded to whole dollars so the sums match on screen
    unhedged_end = round(res["unhedged"][-1])
    hedge_end = round(res["hedge"][-1])
    residual_end = unhedged_end + hedge_end
    basis_end = round(res["basis_contrib"][-1])
    roll_end = round(res["roll_impact"][-1])

    # 2. Chart 1: crack path
    st.markdown("**Crack path**")
    crack_df = pd.DataFrame({
        "Day": days * 3,
        "Series": (["Futures benchmark crack"] * len(days)
                   + ["Refiner's physical crack"] * len(days)
                   + ["Starting benchmark ($16/bbl)"] * len(days)),
        "Value": (list(res["bench_crack"]) + list(res["physical_crack"])
                  + [crack_0] * len(days)),
        "Basis": list(res["basis"]) * 3,
    })
    crack_series = ["Futures benchmark crack", "Refiner's physical crack",
                    "Starting benchmark ($16/bbl)"]
    crack_chart = alt.Chart(crack_df).mark_line(point=True, strokeWidth=3).encode(
        x=X_AXIS,
        y=alt.Y("Value:Q", title="3:2:1 crack ($/bbl)",
                scale=alt.Scale(zero=False)),
        color=alt.Color("Series:N", title=None,
                        scale=alt.Scale(domain=crack_series,
                                        range=["#56B4E9", "#E69F00", GREY]),
                        legend=alt.Legend(orient="bottom")),
        strokeDash=alt.StrokeDash("Series:N",
                                  scale=alt.Scale(domain=crack_series,
                                                  range=[[1, 0], [1, 0], [6, 4]]),
                                  legend=None),
        tooltip=[alt.Tooltip("Day:Q", title="Trading day"),
                 alt.Tooltip("Series:N"),
                 alt.Tooltip("Value:Q", title="$/bbl", format="$.2f"),
                 alt.Tooltip("Basis:Q", title="Basis ($/bbl)", format="+.2f")],
    ).properties(height=340)
    st.altair_chart(crack_chart)

    c1, c2, c3 = st.columns(3)
    c1.metric("Futures crack, day 21 ($/bbl)",
              f"{res['bench_crack'][-1]:.2f}",
              f"{res['bench_crack'][-1] - res['bench_crack'][0]:+.2f}")
    c2.metric("Physical crack, day 21 ($/bbl)",
              f"{res['physical_crack'][-1]:.2f}",
              f"{res['physical_crack'][-1] - res['physical_crack'][0]:+.2f}")
    c3.metric("Basis, day 0 → day 21 ($/bbl)",
              f"{res['basis'][0]:+.2f} → {res['basis'][-1]:+.2f}")

    # 3. Chart 2: hedge outcome
    st.subheader("Hedge outcome")
    m1, m2, m3 = st.columns(3)
    m1.metric("Change in unhedged margin", money(unhedged_end))
    m2.metric("Hedge P&L", money(hedge_end))
    m3.metric("Residual P&L", money(residual_end))
    st.markdown(
        "Residual P&L = unhedged margin change + hedge P&L: "
        + equation(unhedged_end, hedge_end)
    )

    pnl_series = ["Change in unhedged margin", "Hedge P&L", "Residual P&L"]
    pnl_df = pd.DataFrame({
        "Day": days * 3,
        "Series": [name for name in pnl_series for _ in days],
        "Value": (list(res["unhedged"]) + list(res["hedge"])
                  + list(res["residual"])),
    })
    pnl_lines = alt.Chart(pnl_df).mark_line(point=True, strokeWidth=3).encode(
        x=X_AXIS,
        y=alt.Y("Value:Q", title="P&L ($)", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Series:N", title=None,
                        scale=alt.Scale(domain=pnl_series,
                                        range=["#E69F00", "#56B4E9",
                                               "#009E73"]),
                        legend=alt.Legend(orient="bottom")),
        tooltip=[alt.Tooltip("Day:Q", title="Trading day"),
                 alt.Tooltip("Series:N"),
                 alt.Tooltip("Value:Q", title="P&L", format="$,.0f")],
    )
    zero_line = alt.Chart(pd.DataFrame({"Value": [0]})).mark_rule(
        color=GREY, strokeWidth=1.5).encode(y=alt.Y("Value:Q", title="P&L ($)"))
    roll_df = pd.DataFrame({"Day": [data.ROLL_DAY],
                            "Label": [f"Roll to deferred (end of day {data.ROLL_DAY})"]})
    roll_line = alt.Chart(roll_df).mark_rule(
        color=GREY, strokeDash=[2, 3]).encode(x="Day:Q")
    roll_label = alt.Chart(roll_df).mark_text(
        align="left", dx=4, color=GREY).encode(
        x="Day:Q", y=alt.value(10), text="Label:N")
    st.altair_chart((pnl_lines + zero_line + roll_line + roll_label)
                    .properties(height=340))

    # 4. What drives the residual: basis and roll
    st.subheader("What drives the residual")
    d1, d2 = st.columns(2)
    d1.metric("Basis contribution", money(basis_end))
    d2.metric("Roll impact", money(roll_end))
    st.markdown(
        "Residual P&L = basis contribution + roll impact: "
        + equation(basis_end, roll_end)
    )

    st.markdown("**Basis risk**")
    st.write(
        f"The basis is the gap between the refiner's physical crack and the "
        f"futures benchmark (location, quality, timing). The futures hedge "
        f"cannot remove it. Only the change matters: "
        f"({res['basis'][-1]:+.2f} − ({res['basis'][0]:+.2f})) × "
        f"{data.CRUDE_VOLUME:,} bbl = {money(basis_end)}.".replace("$", "\\$")
    )

    st.markdown("**Roll risk**")
    st.write(
        f"Roll rule: the hedge starts in the nearby contract and is rolled "
        f"into the deferred contract at the end of day {data.ROLL_DAY}, "
        f"before expiry. Both trades are done at market prices, so the gap "
        f"between the two contracts is not a profit or loss on the roll day. "
        f"The roll impact builds up day by day: if the curve shape stays the "
        f"same, the contract held moves toward the benchmark as it gets "
        f"closer to expiry. For a short crack hedge, this tends to be "
        f"positive in contango and negative in backwardation. It is not a "
        f"guaranteed profit: the crack curve can shift, and outright price "
        f"moves can outweigh it."
    )
    st.slider(
        "Crack curve: deferred minus nearby ($/bbl)",
        min_value=-1.0, max_value=1.0, value=0.0, step=0.25,
        key="curve_spread",
        help="Negative = backwardation, positive = contango.",
    )
    st.caption(
        "Analytical comparison, not a forecast. The market path stays the "
        "same; only the curve shape changes. Roll impact = hedge P&L with "
        "this curve − hedge P&L with a flat curve, using the same roll rule."
    )
