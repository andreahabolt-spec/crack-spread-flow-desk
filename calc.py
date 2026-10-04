"""Calculations for the Crack Spread Flow Desk."""

import numpy as np

from data import DT


def simulate_correlated_paths(legs0, mu, sigma, corr, days, n_paths, seed):
    """Simulate price paths for several legs that move together.

    legs0: starting prices, for example [crude, gasoline, diesel]
    mu:    yearly drift
    sigma: yearly volatility of each leg
    corr:  correlation matrix of the daily moves
    days:  number of trading days
    n_paths: number of simulated months
    seed:  fixed number, so the result can be reproduced

    Returns an array with shape (n_paths, days + 1, number of legs).
    Day 0 is the starting price.
    """
    rng = np.random.default_rng(seed)
    legs0 = np.array(legs0, dtype=float)
    sigma = np.array(sigma, dtype=float)
    n_legs = len(legs0)

    # Step 1: independent random numbers, one per path, day and leg
    z = rng.standard_normal((n_paths, days, n_legs))

    # Step 2: the Cholesky matrix mixes them so the legs move together
    chol = np.linalg.cholesky(np.array(corr, dtype=float))
    z_corr = z @ chol.T

    # Step 3: daily log return of each leg (drift + random part)
    drift = (mu - 0.5 * sigma ** 2) * DT
    random_part = sigma * np.sqrt(DT) * z_corr
    log_returns = drift + random_part

    # Step 4: add up the log returns and apply them to the starting prices
    paths = np.empty((n_paths, days + 1, n_legs))
    paths[:, 0, :] = legs0
    paths[:, 1:, :] = legs0 * np.exp(np.cumsum(log_returns, axis=1))
    return paths


def compute_crack(crude, gasoline, diesel):
    """3:2:1 crack spread, in USD per barrel of crude.
    (2 x gasoline + 1 x diesel) / 3 - crude
    Works with single prices or with arrays of prices."""
    return (2 * gasoline + diesel) / 3 - crude


def futures_price(spot, carry, days_to_expiry):
    """Cost-of-carry price of a futures contract.
    futures = spot x exp(carry x time to expiry), with time in years."""
    return spot * np.exp(carry * days_to_expiry * DT)


def roll_yield(near_price, far_price):
    """Roll yield = (near - far) / near.
    Positive in backwardation (far is cheaper), negative in contango."""
    return (near_price - far_price) / near_price


def run_desk(path, position_bbl, carry, near_expiry, gap, daily_funding):
    """Trade one simulated month, day by day.

    path:         underlying prices, shape (days + 1, number of legs)
    position_bbl: barrels of each leg, negative = short
    carry:        carry of each leg (per year)
    near_expiry:  day when the near contract expires (the desk rolls at the close)
    gap:          days between the near and the next contract expiry
    daily_funding: funding P&L per day (negative = cost)

    Each day, P&L has three parts:
      price P&L = barrels x change in the underlying price
      roll P&L  = P&L of the futures we hold - price P&L
      funding   = cost of financing the margin
    Returns a dictionary of arrays. Row 0 is day 0, when the position is opened.
    """
    path = np.asarray(path, dtype=float)
    barrels = np.asarray(position_bbl, dtype=float)
    carry = np.asarray(carry, dtype=float)
    n_days = len(path) - 1
    n_legs = len(barrels)

    price_pnl = np.zeros((n_days + 1, n_legs))
    roll_pnl = np.zeros((n_days + 1, n_legs))
    funding = np.zeros(n_days + 1)
    held_price = np.zeros((n_days + 1, n_legs))      # price of the contract we hold
    contract = ["Near (opened)"]

    # Day 0: open the position in the near contract
    held_price[0] = futures_price(path[0], carry, near_expiry)

    # Every day after that
    for t in range(1, n_days + 1):
        # Which contract do we hold today? The near one until it expires, then the next one.
        if t <= near_expiry:
            expiry = near_expiry
            contract.append("Near, rolls at close" if t == near_expiry else "Near")
        else:
            expiry = near_expiry + gap
            contract.append("Next")

        # Price of that same contract today and yesterday
        price_today = futures_price(path[t], carry, expiry - t)
        price_yesterday = futures_price(path[t - 1], carry, expiry - (t - 1))
        held_price[t] = price_today

        # The three parts of the daily P&L
        price_pnl[t] = barrels * (path[t] - path[t - 1])
        futures_pnl = barrels * (price_today - price_yesterday)
        roll_pnl[t] = futures_pnl - price_pnl[t]
        funding[t] = daily_funding

    daily_pnl = price_pnl.sum(axis=1) + roll_pnl.sum(axis=1) + funding
    return {
        "underlying": path,
        "crack": compute_crack(path[:, 0], path[:, 1], path[:, 2]),
        "held_price": held_price,
        "held_crack": compute_crack(held_price[:, 0], held_price[:, 1], held_price[:, 2]),
        "contract": contract,
        "price_pnl": price_pnl,        # by leg, per day
        "roll_pnl": roll_pnl,          # by leg, per day
        "funding": funding,            # per day
        "daily_pnl": daily_pnl,        # total, per day
        "cum_pnl": np.cumsum(daily_pnl),
    }


def simulate_basis(n_paths, days, vol, persistence, seed):
    """Basis = physical price minus the futures-referenced price, in USD per barrel.

    Each day: basis = persistence x yesterday's basis + a random shock.
    So the basis wanders, but it is pulled back towards zero.
    Day 0 is zero. Returns an array with shape (n_paths, days + 1, number of legs).
    """
    rng = np.random.default_rng(seed)
    vol = np.asarray(vol, dtype=float)
    shocks = rng.standard_normal((n_paths, days, len(vol))) * vol

    basis = np.zeros((n_paths, days + 1, len(vol)))
    for t in range(1, days + 1):
        basis[:, t, :] = persistence * basis[:, t - 1, :] + shocks[:, t - 1, :]
    return basis


def average_pnl(paths, position_bbl, carry, near_expiry, gap, daily_funding):
    """Run the desk on every path and average the result.
    Returns (price P&L, roll P&L, total P&L), in USD."""
    runs = [
        run_desk(p, position_bbl, carry, near_expiry, gap, daily_funding)
        for p in paths
    ]
    price = np.mean([x["price_pnl"].sum() for x in runs])
    roll = np.mean([x["roll_pnl"].sum() for x in runs])
    total = np.mean([x["cum_pnl"][-1] for x in runs])
    return price, roll, total


def equal_correlation(rho, n_legs):
    """Correlation matrix where every pair of legs has the same correlation rho."""
    return rho * np.ones((n_legs, n_legs)) + (1 - rho) * np.eye(n_legs)


def run_scenario(legs0, mu, sigma, corr, days, n_paths, seed,
                 position_bbl, carry, near_expiry, gap, daily_funding):
    """Simulate many months with the given market settings, and run the desk on each one.
    Returns a dictionary with one number per month for each part of the P&L,
    plus the lowest crack seen in each month."""
    paths = simulate_correlated_paths(legs0, mu, sigma, corr, days, n_paths, seed)
    runs = [
        run_desk(p, position_bbl, carry, near_expiry, gap, daily_funding)
        for p in paths
    ]
    return {
        "total": np.array([x["cum_pnl"][-1] for x in runs]),
        "price": np.array([x["price_pnl"].sum() for x in runs]),
        "roll": np.array([x["roll_pnl"].sum() for x in runs]),
        "funding": np.array([x["funding"].sum() for x in runs]),
        "start_crack": runs[0]["crack"][0],
        "lowest_crack": np.array([x["crack"].min() for x in runs]),
    }


def summarize(result):
    """The main numbers of a scenario, from the result of run_scenario."""
    total = result["total"]
    return {
        "average": total.mean(),
        "risk": total.std(),                       # spread of the monthly P&L
        "worst_5pct": np.percentile(total, 5),     # 5% of months are worse than this
        "worst": total.min(),
        "best": total.max(),
        "profit_share": (total > 0).mean(),
        "roll": result["roll"].mean(),
        "price": result["price"].mean(),
        "funding": result["funding"].mean(),
        "efficiency": total.mean() / total.std(),  # average P&L per unit of risk
        "start_crack": result["start_crack"],
        "lowest_crack": result["lowest_crack"].min(),
        "negative_crack_share": (result["lowest_crack"] < 0).mean(),
    }
