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