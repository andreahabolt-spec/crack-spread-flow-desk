# calc.py
# All the maths of the project. No Streamlit code here.

import numpy as np


def compute_crack(crude, gasoline, diesel):
    """3:2:1 crack spread in $/bbl: (2 x Gasoline + 1 x Diesel) / 3 - Crude."""
    return (2 * gasoline + 1 * diesel) / 3 - crude


def hedge_volumes(crude_volume):
    """
    Short 3:2:1 crack hedge.
    Buy crude, sell gasoline (2/3 of the volume) and diesel (1/3).
    Positive = bought, negative = sold. Notional-equivalent barrels.
    """
    crude = crude_volume
    gasoline = -crude_volume * 2 / 3
    diesel = -crude_volume * 1 / 3
    return crude, gasoline, diesel


def pnl_split(crack_move, crude_volume):
    """
    Split a crack move into the three P&L lines.
    Change in unhedged margin + hedge P&L = residual P&L
    The refiner is long the crack, the hedge is short the crack.
    """
    unhedged = crack_move * crude_volume      # physical exposure (long crack)
    hedge = -crack_move * crude_volume        # futures hedge (short crack)
    residual = unhedged + hedge               # what is left
    return unhedged, hedge, residual


# ---------------------------------------------------------------
# Tab 2: one illustrative path
# ---------------------------------------------------------------
def simulate_price_path(prices0, mu, sigmas, corr, days, seed):
    """
    One path of correlated GBM prices for crude, gasoline and diesel.
    Returns an array of shape (days + 1, 3). Row 0 = hedge inception.
    """
    dt = 1 / 252
    prices0 = np.array(prices0)
    sigmas = np.array(sigmas)

    # Same correlation between every pair of legs, then Cholesky
    corr_matrix = np.array([[1, corr, corr],
                            [corr, 1, corr],
                            [corr, corr, 1]])
    L = np.linalg.cholesky(corr_matrix)

    rng = np.random.default_rng(seed)
    z = rng.standard_normal((days, 3)) @ L.T       # correlated draws

    log_steps = (mu - sigmas**2 / 2) * dt + sigmas * np.sqrt(dt) * z
    log_path = np.vstack([np.zeros(3), np.cumsum(log_steps, axis=0)])
    return prices0 * np.exp(log_path)


def simulate_basis(basis0, daily_vol, days, seed):
    """Physical crack minus futures crack: a random walk, in cents."""
    rng = np.random.default_rng(seed)
    steps = rng.standard_normal(days) * daily_vol
    basis = np.concatenate([[basis0], basis0 + np.cumsum(steps)])
    return np.round(basis, 2)


def contract_crack(bench_crack, curve_spread, days_to_expiry, days_per_month):
    """
    Price of a crack futures contract with a constant curve shape.
    It trades above the benchmark by curve_spread per month to expiry,
    so deferred minus nearby = curve_spread at all times.
    """
    return bench_crack + curve_spread * days_to_expiry / days_per_month


def rolled_short_crack_pnl(bench_crack, curve_spread, crude_volume,
                           nearby_expiry, roll_day, days_per_month):
    """
    Cumulative P&L ($) of the short crack hedge, day by day, with the roll.
    Days 0 to roll_day: the hedge holds the nearby contract.
    End of roll_day: close nearby, open deferred, both at market prices,
    so the roll itself creates no profit or loss.
    After roll_day: the hedge holds the deferred contract.
    """
    deferred_expiry = nearby_expiry + days_per_month
    pnl = [0.0]
    for t in range(1, len(bench_crack)):
        # contract held from the end of day t-1 to the end of day t
        expiry = nearby_expiry if t - 1 < roll_day else deferred_expiry
        price_before = contract_crack(bench_crack[t - 1], curve_spread,
                                      expiry - (t - 1), days_per_month)
        price_after = contract_crack(bench_crack[t], curve_spread,
                                     expiry - t, days_per_month)
        daily = -crude_volume * (price_after - price_before)   # short
        pnl.append(pnl[-1] + daily)
    return np.array(pnl)


def run_hedge(path, basis, curve_spread, crude_volume,
              nearby_expiry, roll_day, days_per_month):
    """
    All daily series of Tab 2, in $ (cumulative from day 0).
    Change in unhedged margin + hedge P&L = residual P&L
    Residual P&L = basis contribution + roll impact
    """
    crude, gas, dsl = path[:, 0], path[:, 1], path[:, 2]

    bench_crack = compute_crack(crude, gas, dsl)       # futures benchmark
    physical_crack = bench_crack + basis               # refiner's crack

    # Refiner: long the physical crack
    unhedged = (physical_crack - physical_crack[0]) * crude_volume

    # Hedge price effect, leg by leg (flat curve)
    vol_crude, vol_gas, vol_dsl = hedge_volumes(crude_volume)
    price_effect = (vol_crude * (crude - crude[0])
                    + vol_gas * (gas - gas[0])
                    + vol_dsl * (dsl - dsl[0]))

    # Roll impact: selected curve minus flat curve, same path, same roll rule
    args = (crude_volume, nearby_expiry, roll_day, days_per_month)
    with_curve = rolled_short_crack_pnl(bench_crack, curve_spread, *args)
    flat_curve = rolled_short_crack_pnl(bench_crack, 0.0, *args)
    roll_impact = with_curve - flat_curve

    hedge = price_effect + roll_impact
    residual = unhedged + hedge
    basis_contrib = (basis - basis[0]) * crude_volume

    return {
        "bench_crack": bench_crack, "physical_crack": physical_crack,
        "basis": basis, "unhedged": unhedged, "hedge": hedge,
        "residual": residual, "basis_contrib": basis_contrib,
        "roll_impact": roll_impact,
    }
