import streamlit as st

st.set_page_config(page_title="Gasoline Swaps Desk", layout="wide")
st.title("Gasoline Swaps Desk")
st.caption("Educational simulator. All prices are illustrative.")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Screen", "Spreads & Cracks", "Client Desk", "End-of-Day Report"]
)

with tab1:
    st.write("Bids and offers by month - coming next.")
with tab2:
    st.write("Inter-month spreads and crack vs Brent - coming next.")
with tab3:
    st.write("Client requests, execution and blotter - coming next.")
with tab4:
    st.write("Closing prices, volume and commission - coming next.")