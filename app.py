import streamlit as st

st.set_page_config(page_title="Crack Spread Flow Desk", layout="wide")
st.title("Crack Spread Flow Desk")
st.caption("Educational simulator of a 3:2:1 crack spread position over 21 trading days. "
           "All prices are simulated.")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Market", "Position & P&L", "Risk", "Scenarios & Report"]
)

with tab1:
    st.write("Simulated prices for crude, gasoline and diesel, and the crack - coming next.")
with tab2:
    st.write("Roll yield and daily P&L - coming next.")
with tab3:
    st.write("Basis exposure and curve sensitivity - coming next.")
with tab4:
    st.write("Volatility and correlation scenarios, and the summary report - coming next.")