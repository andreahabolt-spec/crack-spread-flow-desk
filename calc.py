"""Calculations for the Gasoline Swaps Desk.

Each function does one small job, so it is easy to explain.
"""

from data import LOT_SIZE_MT, BBL_PER_MT, BLOCKED_PAIRS, COMMISSION_PER_MT


def to_lots(volume_mt):
    """Convert tonnes into lots. 10,000 tonnes = 10 lots."""
    return volume_mt / LOT_SIZE_MT


def is_valid_volume(volume_mt):
    """A volume is valid if it is positive and a multiple of 1,000 tonnes."""
    return volume_mt > 0 and volume_mt % LOT_SIZE_MT == 0


def bid_offer(mid, half_spread):
    """Return (bid, offer) around a mid price."""
    return round(mid - half_spread, 2), round(mid + half_spread, 2)


def month_spread(near_price, far_price):
    """Inter-month spread = near month minus far month (USD per tonne).
    A positive spread means the near month is more expensive."""
    return round(near_price - far_price, 2)


def crack(eurobob_usd_per_mt, brent_usd_per_bbl):
    """Gasoline crack vs Brent, in USD per barrel.
    Step 1: convert gasoline from tonnes to barrels (divide by 8.33).
    Step 2: subtract the Brent price."""
    return round(eurobob_usd_per_mt / BBL_PER_MT - brent_usd_per_bbl, 2)


def swap_settlement(fixed_price, floating_average, volume_mt, side):
    """Money received (+) or paid (-) at the end of the month.
    The buyer pays the fixed price and receives the monthly average of Argus.
    side is "buy" or "sell"."""
    difference = floating_average - fixed_price
    if side == "buy":
        return round(difference * volume_mt, 2)
    return round(-difference * volume_mt, 2)


def commission(volume_mt, rate_per_mt=COMMISSION_PER_MT):
    """Commission for one side of a trade."""
    return round(volume_mt * rate_per_mt, 2)


def credit_ok(client_a, client_b):
    """False if the two clients have no credit line together."""
    blocked = [frozenset(pair) for pair in BLOCKED_PAIRS]
    return frozenset([client_a, client_b]) not in blocked


if __name__ == "__main__":
    # Quick check with the example we discussed.
    print("Lots for 10,000 t:", to_lots(10000))
    print("Is 10,000 t valid?", is_valid_volume(10000))
    print("Is 10,500 t valid?", is_valid_volume(10500))
    print("Bid/offer Dec:", bid_offer(780, 1.00))
    print("Dec/Jan spread:", month_spread(780, 772))
    print("Dec crack ($/bbl):", crack(780, 80))
    print("Buyer, fixed 780, average 800, 10,000 t:", swap_settlement(780, 800, 10000, "buy"))
    print("Buyer, fixed 780, average 760, 10,000 t:", swap_settlement(780, 760, 10000, "buy"))
    print("Commission, 10,000 t:", commission(10000))
    print("Credit Fund / Oil major:", credit_ok("Meridian Capital", "Atlas Oil"))
    print("Credit Bank / Fund:", credit_ok("Northbridge Bank", "Meridian Capital"))