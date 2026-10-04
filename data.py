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