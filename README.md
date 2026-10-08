# Crack Spread Flow Desk

**Live app:** https://crack-spread-flow-desk.streamlit.app

A simulation of an oil major's trading desk hedging its refinery's margin. The desk sells the 3:2:1 crack spread in the futures market for one month. The app shows what the hedge offsets, what it costs, and which risks remain. You can change the market view (tight or loose, a shock on one day, even negative prices) and see the result.

*Educational project. All prices are simulated. ExxonMobil is only an example of an oil major: the app uses no company data. This is not trading advice.*

## The idea

A refinery buys crude and sells gasoline and diesel. Its margin is the **crack spread**: (2 x gasoline + diesel) / 3 - crude, per barrel of crude (the 3:2:1 rule). With the simulated prices it is **$34 per barrel**.

The refinery processes 10,000 barrels a month. If the crack falls by $4, its margin falls by $40,000. The company's trading desk hedges this by **selling the crack in futures**: long crude, short gasoline and short diesel (10, 6.67 and 3.33 contracts of 1,000 barrels). If the crack falls by $4, the hedge gains $40,000. If it rises, the hedge loses and the refinery keeps the extra margin.

## What the app shows

The app has two tabs.

| Tab | What it shows |
|---|---|
| **The hedge** | The story in five questions, one visual each: 1. What are we protecting? (the crack, all paths). 2. What does the hedge do? (one path: margin, hedge and net result). 3. What does it cost? (the futures curve). 4. What is left? (risk without and with the hedge). 5. What if the market changes? (scenario table, with your own market view). |
| **Under the hood** | The details behind each number. A. The three cracks. B. The simulated market (all paths, then one selected path). C. The hedge, day by day. D. Risk: basis and curve. E. Scenarios and report. F. Assumptions and key terms. |

## Three cracks

| Crack | What it is | Real-world version | Day 0 |
|---|---|---|---|
| **Market crack** | The reference, from market prices | Spot WTI, or Dated Brent | 34.00 |
| **Futures crack** | The hedge: from the futures contracts the desk holds | NYMEX or ICE futures | 33.38 |
| **Refinery crack** | What the refinery really earns: market crack plus a local gap | Its own price: benchmark plus a differential | 34.00 |

**Gap between the refinery and the futures = local gap + curve.** The local gap (refinery against market) is the **basis risk**: the hedge does not cover it. The curve (market against futures) decides **what the hedge costs**. The price moves of the refinery and the hedge cancel exactly, so: net result = local gap + roll and curve P&L + funding.

## Market view (sidebar)

| Control | What it does |
|---|---|
| **Market tightness**, -10 to +10 | Moves the carry of all three legs together. Positive: tighter market, more backwardation. Negative: looser market, more contango. |
| **A shock during the month** | A day, a change in tightness, and a price jump in USD per barrel for crude and for the products. A jump can push a price below zero. |
| **Storage is full** | Removes the cap on contango, as in April 2020, when oil tanks were full. |
| **Advanced** | Extra carry or price jump for one leg (to flip a single leg), how much the curve moves each day, the link between prices and the curve, and whether prices drift with the curve. |

A line under the title says which market view is applied. Contango is capped at interest + storage (crude 5%, products 4%), because traders would buy, store and sell forward.

## Headline results

500 simulated months, base case (seed 42):

| | Result |
|---|---|
| Refinery margin risk without the hedge | +/- $38,805 a month |
| Risk left after the hedge (basis, curve moves, funding) | +/- $8,950 a month |
| Share of the risk removed | 95% |
| Cost of the hedge | $12,876 a month |
| Peak cash the company puts up | $103,912 on average, more than $151,588 in the worst 5% of months |

**Net result = basis effect + roll and curve P&L + funding.** The price moves of the refinery and the hedge cancel exactly.

## Scenarios

| Scenario | Risk without hedge | Risk after hedge | Share removed | Cost of the hedge | Peak cash, worst 5% |
|---|---|---|---|---|---|
| Base case | $38,805 | $8,950 | 95% | $12,876 | $151,588 |
| Volatility x2 | $77,124 | $8,953 | 99% | $12,877 | $224,100 |
| Correlation 0.5 | $55,258 | $8,892 | 97% | $12,903 | $181,291 |
| Correlation 0.9 | $26,058 | $8,956 | 88% | $12,861 | $124,684 |
| Volatility x2 and correlation 0.5 | $110,528 | $8,896 | 99% | $12,904 | $281,236 |

The risk without the hedge grows with volatility and falls with correlation, because the refinery is long the crack and the legs offset each other. The risk after the hedge barely changes, because I assume the basis is independent of prices. In a real crisis, the basis widens too.

## How it works

- **Prices.** Crude, gasoline and diesel move by a random number of **dollars** each day, so a price can cross zero (volatility in dollars = yearly volatility x starting price; correlations 0.80, 0.85, 0.75, built with a Cholesky matrix). By default, each leg's expected drift equals its carry, so the curve gives no free lunch. A fixed seed makes every result reproducible.
- **Futures curves.** Cost of carry: futures price = underlying price + carry x starting price x time to expiry. Carry = interest + storage - convenience yield: +4% for crude (contango), -12% for gasoline and -10% for diesel (backwardation). The carry moves every day: it is pulled back to its normal level, plus a random move linked to the price move.
- **Hedge P&L.** A loop goes through the days one by one. Each day: hedge P&L = price P&L + roll and curve P&L + funding.
  - Price P&L = barrels x change in the underlying price.
  - Roll and curve P&L = barrels x (change in the futures price - change in the underlying price). It can be a gain or a cost.
  - Funding = 2% a year on the margin ($78,000) plus the cash the hedge has paid out so far (variation margin).
- **Refinery margin.** 10,000 barrels x change in the physical crack. Physical crack = underlying crack + basis crack.
- **Basis.** For each leg, basis = 0.90 x yesterday's basis + a random shock. It is independent of the futures price.

## Project structure

```
app.py             The Streamlit page (display only)
calc.py            The calculations: prices and curves, crack, futures price, daily loop, basis, scenarios
data.py            All the assumptions: prices, volatilities, correlations, carry, funding, scenarios
requirements.txt   Python packages
```

## Run it locally

```
pip install -r requirements.txt
streamlit run app.py
```

On Windows, if those commands are not recognized, use `py -m pip install -r requirements.txt` and `py -m streamlit run app.py`.

## Assumptions and limits

- All prices are simulated. There is no market data.
- The starting curve, the size of its daily moves and its link to prices are assumptions.
- The basis sizes are assumptions, and the basis is independent of the price.
- One roll, on day 10. No trading costs. One interest rate for borrowing and lending.
- Negative prices come only from a shock you set (for example crude -$100). In April 2020, WTI settled below zero. The carry formula is linear in dollars, so it still works at negative prices.
- A shock is the same in every simulated month. It shifts the averages, not the spread of the results.
- The 3:2:1 crack is a simplified refinery.

## Next steps (not built)

- A snapshot of real market data as the starting prices and curve.
- A curve that reacts to prices in more detail (today: one link, -0.5).
- Options on the crack, to give the refinery a floor without giving up the upside.
