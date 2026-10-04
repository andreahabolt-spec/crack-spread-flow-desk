"""Assumptions for the Crack Spread Flow Desk.

All prices are simulated. Every leg is in USD per barrel.
"""

GALLONS_PER_BARREL = 42

# --- Starting market (day 0) ---
CRUDE_0 = 78.00                  # USD per barrel
GASOLINE_0_GAL = 2.50            # USD per gallon
DIESEL_0_GAL = 3.00              # USD per gallon
GASOLINE_0 = GASOLINE_0_GAL * GALLONS_PER_BARREL    # 105.00 USD per barrel
DIESEL_0 = DIESEL_0_GAL * GALLONS_PER_BARREL        # 126.00 USD per barrel

LEG_NAMES = ["Crude", "Gasoline", "Diesel"]
LEGS_0 = [CRUDE_0, GASOLINE_0, DIESEL_0]

# --- Simulation settings ---
DAYS = 21            # trading days in the month
DT = 1 / 252         # one trading day, as a fraction of a year
N_PATHS = 5          # number of simulated months
SEED = 42            # fixed seed: same seed gives the same paths

# --- Price model ---
MU = 0.02                        # yearly drift, same for the three legs
SIGMA = [0.25, 0.20, 0.18]       # yearly volatility: crude, gasoline, diesel
CORR = [                         # correlation of daily moves
    [1.00, 0.80, 0.75],          # crude
    [0.80, 1.00, 0.85],          # gasoline
    [0.75, 0.85, 1.00],          # diesel
]

# --- The position: long the 3:2:1 crack ---
NOTIONAL_BBL = 10_000      # barrels of crude, which is 10 contracts
CONTRACT_BBL = 1_000       # one futures contract = 1,000 barrels (42,000 gallons)
# Barrels per leg, in the order crude, gasoline, diesel.
# Negative = short. Long crack = short crude, long gasoline and diesel.
POSITION_BBL = [-NOTIONAL_BBL, NOTIONAL_BBL * 2 / 3, NOTIONAL_BBL * 1 / 3]

# --- Futures curve (cost of carry) ---
# futures price = spot x exp(carry x time to expiry)
# carry = interest rate + storage cost - convenience yield (all per year)
R = 0.02                             # interest rate, continuous compounding
STORAGE = [0.03, 0.02, 0.02]         # crude, gasoline, diesel
CONVENIENCE = [0.01, 0.16, 0.14]     # crude, gasoline, diesel
CARRY = [R + s - c for s, c in zip(STORAGE, CONVENIENCE)]    # 0.04, -0.12, -0.10
NEAR_EXPIRY_DAY = 10                 # the near contract expires on day 10
CONTRACT_GAP_DAYS = 21               # the next contract expires one month later
CURVE_CHART_DAYS = 63                # length of the curve chart (about 3 months)

# --- Funding ---
MARGIN_PCT = 0.10                                    # margin = 10% of the crude leg's value
MARGIN_USD = MARGIN_PCT * CRUDE_0 * NOTIONAL_BBL     # 0.10 x 78 x 10,000 = 78,000 USD
DAILY_FUNDING = -MARGIN_USD * R * DT                 # cost of financing the margin, per day

# --- Basis: physical price minus the futures-referenced price (USD per barrel) ---
BASIS_VOL = [0.20, 0.40, 0.35]      # size of the daily random shock: crude, gasoline, diesel
BASIS_PERSISTENCE = 0.90            # share of yesterday's basis still there today
BASIS_SEED_OFFSET = 1000            # the basis uses its own random numbers

# --- Curve scenarios: change in carry per year, for crude, gasoline, diesel ---
CURVE_SCENARIOS = {
    "Products' backwardation flattens": [0.00, 0.08, 0.08],
    "Products' backwardation steepens": [0.00, -0.08, -0.08],
    "Crude contango steepens": [0.06, 0.00, 0.00],
    "Crude moves to backwardation": [-0.08, 0.00, 0.00],
}
CURVE_BUMP = 0.01                   # 1 percentage point of carry, for the sensitivity table

# --- Scenarios (Scenarios & Report tab) ---
SCENARIO_PATHS = 500                 # simulated months in each scenario
# vol_mult multiplies all volatilities. corr sets every correlation between the legs
# to the same number (None = keep the base correlations).
SCENARIOS = {
    "Base case": {"vol_mult": 1.0, "corr": None},
    "Volatility x1.5": {"vol_mult": 1.5, "corr": None},
    "Volatility x2": {"vol_mult": 2.0, "corr": None},
    "Correlation 0.5": {"vol_mult": 1.0, "corr": 0.5},
    "Correlation 0.7": {"vol_mult": 1.0, "corr": 0.7},
    "Correlation 0.9": {"vol_mult": 1.0, "corr": 0.9},
    "Stress: volatility x2 and correlation 0.5": {"vol_mult": 2.0, "corr": 0.5},
}

# --- Edge case: a thin crack, with extreme volatility ---
THIN_CRACK_LEGS_0 = [78.00, 80.00, 82.00]   # crude, gasoline, diesel (USD per barrel)
THIN_CRACK_VOL_MULT = 2.0
