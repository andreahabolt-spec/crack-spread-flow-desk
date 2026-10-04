import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import MONTHS, EUROBOB_MID, HALF_SPREAD, SCREEN_ORDERS
from calc import bid_offer

st.set_page_config(page_title="Gasoline Swaps Desk", layout="wide")
st.title("Gasoline Swaps Desk")
st.caption("Educational simulator. All prices are illustrative.")

# ---------- Sidebar: market inputs ----------
st.sidebar.header("Market inputs")
st.sidebar.caption("Eurobob swap mid prices, USD per tonne")

mids = {}
for month in MONTHS:
    mids[month] = st.sidebar.number_input(
        month, value=EUROBOB_MID[month], step=0.25, format="%.2f"
    )

half_spread = st.sidebar.number_input(
    "Half bid-offer spread (USD per tonne)",
    value=HALF_SPREAD, min_value=0.0, step=0.25, format="%.2f",
)

# ---------- Build the screen table ----------
rows = []
for month in MONTHS:
    bid, offer = bid_offer(mids[month], half_spread)
    orders = SCREEN_ORDERS[month]
    rows.append({
        "Month": month,
        "Bid from": orders["bid_client"],
        "Bid lots": orders["bid_lots"],
        "Bid": bid,
        "Offer": offer,
        "Offer lots": orders["offer_lots"],
        "Offer from": orders["offer_client"],
        "Bid-offer": round(offer - bid, 2),
    })
screen = pd.DataFrame(rows)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Screen", "Spreads & Cracks", "Client Desk", "End-of-Day Report"]
)

with tab1:
    st.subheader("Eurobob swap screen (Argus Eurobob Oxy FOB Rotterdam Barges)")
    st.caption("Prices in USD per tonne. One lot = 1,000 tonnes.")

    st.dataframe(screen, hide_index=True)

    with st.expander("How to read this screen"):
        st.markdown(
            """
- **Bid**: the highest price a client will pay. This client wants to **buy**.
- **Offer**: the lowest price a client will accept. This client wants to **sell**.
- **Bid-offer**: the gap between the two. A small gap means a liquid market.
- **Lots**: the size of each order. 5 lots = 5,000 tonnes.
- **Bid from / Offer from**: the client behind each order. The broker knows who they are.
- A swap for a month settles against the **average** of the daily Argus prices of that month.
            """
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=screen["Month"], y=screen["Offer"],
                             name="Offer", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=screen["Month"], y=[mids[m] for m in MONTHS],
                             name="Mid", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=screen["Month"], y=screen["Bid"],
                             name="Bid", mode="lines+markers"))
    fig.update_layout(
        title="Eurobob swap curve by delivery month",
        xaxis_title="Delivery month",
        yaxis_title="USD per tonne",
        height=380,
    )
    st.plotly_chart(fig)

with tab2:
    st.write("Inter-month spreads and crack vs Brent - coming next.")
with tab3:
    st.write("Client requests, execution and blotter - coming next.")
with tab4:
    st.write("Closing prices, volume and commission - coming next.")