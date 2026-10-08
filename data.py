# data.py
# All fixed inputs of the simulation. No calculations here.

# Starting futures prices ($/bbl)
CRUDE_0 = 78.00
GASOLINE_0 = 88.50   # about $2.11/gal (1 bbl = 42 gal)
DIESEL_0 = 105.00    # about $2.50/gal

GALLONS_PER_BBL = 42

# Hedge size: 10,000 bbl of crude processed
CRUDE_VOLUME = 10_000

# Simulation settings
DAYS = 21            # one month of trading days
DT = 1 / 252         # one trading day, in years
RISK_FREE = 0.02     # 2%, continuous compounding
MU = 0.02            # drift used in the price paths

# Annual volatilities (base case, before the sidebar multiplier)
SIGMA_CRUDE = 0.25
SIGMA_GASOLINE = 0.20
SIGMA_DIESEL = 0.18

# Worked example shown in Tab 1: the crack falls by $3/bbl
EXAMPLE_CRACK_MOVE = -3.0

# Final Overview text
OVERVIEW_TEXT = (
    "A refiner expects to process 10,000 barrels of crude and sell gasoline "
    "and diesel over a one-month period. Its benchmark crack spread is "
    "currently $16/bbl, and it wants to protect against a narrowing margin. "
    "An external commodities desk structures a short 3:2:1 crack hedge using "
    "crude and product futures. The simulation follows the hedge over 21 "
    "trading days, showing how hedge P&L offsets changes in the refiner's "
    "benchmark margin, and how basis and futures-curve movements affect the "
    "remaining P&L."
)

# ---------------------------------------------------------------
# Tab 2: one illustrative market path
# ---------------------------------------------------------------
CORR = 0.8           # correlation between crude, gasoline and diesel
PATH_SEED = 149      # fixed seed: the same price path at every rerun
BASIS_SEED = 85      # fixed seed: the same basis path at every rerun

# Basis = refiner's physical crack - futures benchmark crack ($/bbl)
BASIS_0 = -0.50      # physical crack starts at $15.50 vs $16.00 benchmark
BASIS_VOL = 0.10     # typical daily change of the basis ($/bbl)

# Roll rule: the hedge starts in the nearby contract and is rolled
# into the deferred contract at the end of ROLL_DAY, before expiry.
NEARBY_EXPIRY = 12   # nearby contract expires on trading day 12
ROLL_DAY = 10        # roll two days before expiry
DAYS_PER_MONTH = 21  # deferred contract expires one month later
