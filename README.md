# Crack Spread Flow Desk

**Live app:** https://crack-spread-flow-desk.streamlit.app

A simulation of a flow trading desk handling a refiner's request to hedge its refining margin.
The desk goes long a 3:2:1 crack spread for one month. The app shows how much the desk can make or lose, where the P&L comes from, which risks remain, and how the result changes when market conditions change.

*Educational project. All prices are simulated. This is not trading advice.*

## The situation

A refinery buys crude oil and sells gasoline and diesel. Its profit depends on the **crack spread**: the price of the products minus the price of crude. This project uses the standard **3:2:1** crack: 3 barrels of crude become 2 barrels of gasoline and 1 barrel of diesel.

With the prices in the simulation, the crack is **$34 per barrel**: (2 x 105 + 126) / 3 - 78.

## The client's problem

The refiner will process 10,000 barrels next month. If the crack falls from $34 to $30, its margin falls by $4 x 10,000 = **$40,000**. It hedges by selling the crack.

The desk takes the other side: it **buys the crack**. That means long gasoline and diesel futures, and short crude futures. If the crack falls by $4, the refiner's hedge gains $40,000 and the desk loses $40,000.

## What the desk does

For 21 trading days, the desk:

1. **Opens the position:** short 10,000 barrels of crude, long 6,667 barrels of gasoline, long 3,333 barrels of diesel (10, 6.67 and 3.33 contracts of 1,000 barrels).
2. **Marks it every day** and splits the P&L into price, roll and funding.
3. **Rolls the futures** on day 10, when the near contract expires.
4. **Measures the risks the position does not remove:** basis risk and curve risk.
5. **Tests the result** under higher volatility and different correlations.

## What the app shows

| Tab | What it shows |
|---|---|
| **Overview** | The situation, the client's problem, the desk's job, headline results |
| **Market** | Simulated prices, the crack spread, the futures curves |
| **Position & P&L** | The position, a daily trading log, the P&L split, the roll, all simulated months |
| **Risk** | Basis exposure and hedge effectiveness, curve sensitivity and curve scenarios |
| **Scenarios & Report** | Volatility and correlation scenarios, an edge case, a summary report |

## Headline results

500 simulated months, default settings (seed 42):

| | Result |
|---|---|
| Roll P&L, average per month | about $13,000 |
| Price P&L, typical swing | about +/- $39,000 |
| Funding, per month | -$130 |
| Months with a profit | 64% |
| Worst month / best month | -$109,518 / +$140,243 |
| Gain per unit of risk (average P&L / risk) | 0.39 |

The position earns a steady gain from the shape of the futures curve. The price risk around it is about three times larger, and it is not steady.

## Risk

- **Basis risk.** The refiner sells at a physical price, not at the futures price. A $1 move in the crack basis changes its margin by $10,000, and the futures hedge does not offset it. Over 500 simulated months, the futures hedge removes about **96%** of the refiner's risk. About +/- $8,000 a month is left.
- **Curve risk.** The roll gain depends on the shape of the curve. If the products' backwardation flattens by 8 points of carry, the desk loses about $7,400 of its monthly gain. If it steepens by 8 points, the desk gains about $7,400 more.

## Scenarios

500 simulated months in each scenario, with the same random numbers:

| Scenario | Risk (std of monthly P&L) | Months with a profit |
|---|---|---|
| Base case | $39,283 | 64% |
| Volatility x2 | $79,859 | 58% |
| Correlation 0.9 | $25,781 | 70% |
| Correlation 0.5 | $56,201 | 59% |
| Volatility x2 and correlation 0.5 | $113,988 | 54% |

Risk grows with volatility and falls with correlation between the legs, because the desk is long products and short crude. The roll gain stays at about $13,000 in every scenario. An edge case with a thin crack (starting near $2.67) shows that the crack can go negative without breaking the position, since it is made of futures and has no floor.

## How it works

- **Prices.** Crude, gasoline and diesel follow correlated random walks with a small drift (2% a year). Volatilities are 25%, 20% and 18%. Correlations are 0.80 (crude-gasoline), 0.85 (gasoline-diesel) and 0.75 (crude-diesel). The legs are linked with a Cholesky matrix. A fixed seed makes every result reproducible.
- **Futures curves.** Cost of carry: futures price = underlying price x exp(carry x time to expiry). Carry = interest rate + storage - convenience yield. This gives +4% for crude (contango), -12% for gasoline and -10% for diesel (backwardation).
- **Daily P&L.** A loop goes through the days one by one. Each day, P&L = price P&L + roll P&L + funding.
  - Price P&L = barrels x change in the underlying price.
  - Roll P&L = P&L of the futures contract held, minus the price P&L.
  - Funding = 2% a year on a margin of $78,000 (10% of the crude leg), which is $6.19 per day.
- **Basis.** For each leg, basis = 0.90 x yesterday's basis + a random shock. It is independent of the futures price.
- **Checks built into the app.** The price effect equals the crack move x 10,000 barrels. Price + roll + funding equals the total P&L.

## Project structure

```
app.py             The Streamlit page (display only)
calc.py            The calculations: price paths, crack, futures price, roll yield, daily loop, basis, scenarios
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
- The futures curves use assumed carry values, and the curve is fixed for the whole month. Real curves change every day.
- The basis sizes are assumptions, and the basis is independent of the price.
- There is one roll, on day 10 of the month.
- Funding assumes a 10% margin and a 2% rate. There are no trading costs and no slippage.
- The 3:2:1 crack is a simplified refinery. A real refiner's margin does not move exactly like the futures crack. That gap is basis risk.
