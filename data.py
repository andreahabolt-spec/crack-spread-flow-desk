"""Illustrative market data for the Gasoline Swaps Desk.

All prices and clients are made up for education.
Real Argus and ICE prices are paid data, so we type them in by hand.
"""

# --- Contract facts (from the ICE contract pages) ---
LOT_SIZE_MT = 1000      # one Eurobob swap lot = 1,000 tonnes
BBL_PER_MT = 8.33       # conversion used in the ICE gasoline crack contract

# --- Settings we choose ourselves (illustrative) ---
HALF_SPREAD = 1.00          # bid = mid - 1.00, offer = mid + 1.00 (USD per tonne)
COMMISSION_PER_MT = 0.05    # placeholder rate, per tonne, per side

# --- Months shown on the screen ---
MONTHS = ["Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27"]

# --- Mid price of the Eurobob swap, USD per tonne ---
EUROBOB_MID = {
    "Nov-26": 776.00,
    "Dec-26": 780.00,
    "Jan-27": 772.00,
    "Feb-27": 770.00,
    "Mar-27": 785.00,
}

# --- Brent swap, USD per barrel ---
BRENT_SWAP = {
    "Nov-26": 80.50,
    "Dec-26": 80.00,
    "Jan-27": 79.50,
    "Feb-27": 79.00,
    "Mar-27": 78.80,
}

# --- Fictional clients (the people who call the broker) ---
CLIENTS = {
    "Northbridge Bank": "Investment bank, trading desk",
    "Alpine Commodities": "Commodity house",
    "Meridian Capital": "Fund",
    "Atlas Oil": "Oil major",
    "Delta Trading": "Independent trader",
}

# --- Credit lines ---
# In this simulation every pair of clients can trade together,
# except the two pairs below, which have no credit line.
BLOCKED_PAIRS = [
    ("Meridian Capital", "Atlas Oil"),
    ("Delta Trading", "Northbridge Bank"),
]

# --- Orders on the screen ---
# Who is behind the best bid and the best offer for each month, and the size in lots.
SCREEN_ORDERS = {
    "Nov-26": {"bid_client": "Delta Trading",      "bid_lots": 5,
               "offer_client": "Northbridge Bank", "offer_lots": 10},
    "Dec-26": {"bid_client": "Alpine Commodities", "bid_lots": 10,
               "offer_client": "Atlas Oil",        "offer_lots": 10},
    "Jan-27": {"bid_client": "Northbridge Bank",   "bid_lots": 5,
               "offer_client": "Meridian Capital", "offer_lots": 5},
    "Feb-27": {"bid_client": "Atlas Oil",          "bid_lots": 5,
               "offer_client": "Delta Trading",    "offer_lots": 10},
    "Mar-27": {"bid_client": "Meridian Capital",   "bid_lots": 10,
               "offer_client": "Alpine Commodities", "offer_lots": 5},
}