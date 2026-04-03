# SMA vs EMA Crossover Backtesting System

A from-scratch quantitative backtesting system that implements Simple Moving Average (SMA) and Exponential Moving Average (EMA) crossover strategies, compares their risk-adjusted performance, and optimises parameters using walk-forward validation.

Built without any financial libraries — all strategy logic, performance metrics, and optimisation are implemented in pure Python.

---

## File Structure

```
sma-ema-backtest/
├── README.md
├── sma.py             ← SMA strategy: load, compute, backtest, metrics
├── ema.py             ← EMA strategy: same structure, different MA calculation
├── compare.py         ← Run both strategies side by side and print results
└── grid_search.py     ← Parameter optimisation with walk-forward validation
```

---

## Installation

```bash
pip install yfinance python-dateutil
```

No other dependencies required. All metric calculations use the Python standard library.

---

## Usage

All scripts accept a freely typed date range at runtime. The date parser recognises most common formats — `2016-01-01`, `Jan 1 2016`, and `1/1/2016` all work.

### Run SMA strategy only

```bash
python sma.py
```

```
Ticker (e.g. AAPL): AAPL
Start date: 2016-01-01
  -> Parsed as 2016-01-01
End date: 2026-01-01
  -> Parsed as 2026-01-01
Short MA window (e.g. 20): 20
Long MA window (e.g. 50): 50
```

### Run EMA strategy only

```bash
python ema.py
```

### Compare SMA vs EMA side by side

```bash
python compare.py
```

Results on AAPL (2016-01-01 to 2026-01-01), short window 20, long window 50:

```
Loaded 2514 trading days for AAPL (2016-01-01 to 2026-01-01).
  [Risk-free] Average 3-month T-bill yield (2016-01-01 to 2026-01-01): 2.16%

Ticker: AAPL  |  Short window: 20  |  Long window: 50

Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          359.20     404.43
Buy & Hold Return (%)       1046.73    1044.52
Max Drawdown (%)             -29.09     -25.30
Sharpe Ratio                   0.77       0.77
Total Trades                     55         45

Winner by metric:
  Strategy Return : EMA
  Max Drawdown    : EMA  (lower is better)
  Sharpe Ratio    : EMA
  Total Trades    : EMA  (fewer is cheaper)
```

### Walk-forward grid search

```bash
python grid_search.py
```

Results on AAPL (2016-01-01 to 2026-01-01):

```
Loaded 2514 trading days for AAPL (2016-01-01 to 2026-01-01).
  [Risk-free] Average 3-month T-bill yield (2016-01-01 to 2026-01-01): 2.16%

Total data: 2514 trading days

Optimising SMA via walk-forward...
  Walk-forward: 7 windows, test window = 252 days, min train = 504 days

Optimising EMA via walk-forward...
  Walk-forward: 7 windows, test window = 252 days, min train = 504 days

==============================================================
            Params  Mean Test Sharpe   Full Sharpe
--------------------------------------------------------------
SMA         (5, 30)             1.25          1.07
EMA         (5, 20)             1.30          1.25
==============================================================

Top 5 SMA parameter combinations (mean test Sharpe):
  Short   Long   Mean Sharpe
  --------------------------
      5     30          1.25
     10     80          1.25
      5     20          1.23
      5     70          1.23
      5     80          1.22

Top 5 EMA parameter combinations (mean test Sharpe):
  Short   Long   Mean Sharpe
  --------------------------
      5     20          1.30
     10     20          1.20
      5    180          1.10
      5    170          1.07
      5    140          1.07

Overall winner (by mean test Sharpe): EMA  (1.30 vs 1.25)
```

---

## Strategy Logic

### Simple Moving Average (SMA)

The arithmetic mean of the past $n$ closing prices, where each day carries equal weight:

$$\text{SMA}(t,\, n) = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

The SMA series is $n - 1$ elements shorter than the price series — there is no valid average until $n$ data points have been observed.

### Exponential Moving Average (EMA)

A weighted average that gives more weight to recent prices, controlled by a smoothing factor $\alpha$:

$$\text{EMA}(t) = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}(t-1), \qquad \alpha = \frac{2}{n+1}$$

Unlike SMA, EMA uses all historical data — older prices decay exponentially but never reach zero. EMA is the same length as the price series because day 1 is initialised with the first price directly.

### Crossover Signals

Both strategies use the same signal logic. The key insight is that we detect the *moment* of crossover by comparing yesterday's relative position to today's — not just today's value alone.

**Golden cross — buy signal:** fast MA crosses above slow MA, indicating an upward trend.

$$S_{t-1} \leq L_{t-1} \quad \text{and} \quad S_t > L_t \implies \text{buy}$$

**Death cross — sell signal:** fast MA crosses below slow MA, indicating a downward trend.

$$S_{t-1} \geq L_{t-1} \quad \text{and} \quad S_t < L_t \implies \text{sell}$$

where $S_t$ is the short (fast) MA and $L_t$ is the long (slow) MA on day $t$.

The strategy is fully invested when holding (all-in) and holds cash otherwise. No short selling.

### Performance Metrics

**Strategy Return** — total return over the backtest period, with starting capital normalised to 1.0:

$$R_{\text{strategy}} = (C_{\text{final}} - 1) \times 100$$

**Buy and Hold Return** — benchmark return from buying on day one and holding to the end:

$$R_{\text{bh}} = \left(\frac{P_{\text{last}}}{P_{\text{first}}} - 1\right) \times 100$$

**Max Drawdown** — largest peak-to-trough decline in the equity curve, measuring worst-case loss:

$$\text{MDD} = \max_{t} \frac{\text{peak}_t - V_t}{\text{peak}_t}, \qquad \text{peak}_t = \max_{s \leq t} V_s$$

**Sharpe Ratio** — risk-adjusted return measuring excess return per unit of risk, annualised using 252 trading days:

$$\text{Sharpe} = \frac{\mu - r_f / 252}{\sigma} \times \sqrt{252}$$

where $\mu$ is the mean daily return, $\sigma$ is the sample standard deviation of daily returns, and $r_f$ is the risk-free rate sourced from the average 3-month US Treasury bill yield (`^IRX`) over the backtest period.

Using the realised T-bill yield rather than a fixed constant matters because the risk-free rate varied substantially across the decade — from near zero during 2020–2021 to above 5% in 2023–2024. A fixed value would systematically overstate or understate excess returns depending on the period chosen.

The sample standard deviation divides by $n - 1$ rather than $n$, which gives an unbiased estimate of the true return volatility when working with a historical sample.

| Sharpe      | Interpretation          |
|-------------|-------------------------|
| $< 0$       | Worse than risk-free    |
| $0$ to $1$  | Acceptable              |
| $1$ to $2$  | Good                    |
| $> 2$       | Excellent, rarely seen  |

---

## Parameter Optimisation

`grid_search.py` performs an exhaustive search over:

$$s \in \{5, 10, 15, \ldots, 55\}, \qquad l \in \{20, 30, 40, \ldots, 200\}$$

where $s$ is the short window and $l$ is the long window. All combinations where $s \geq l$ are skipped. The objective function is the mean test Sharpe across all walk-forward windows.

### Walk-Forward Validation

A single train/test split is inadequate for strategy optimisation because financial markets cycle through distinct regimes — bull markets, bear markets, high-volatility periods, and low-volatility periods — each of which rewards different parameter choices. Parameters optimised on one regime frequently collapse when the regime shifts, producing the large Sharpe drops commonly seen with naive train/test splits.

Walk-forward validation addresses this by rolling a one-year test window across the full dataset:

```
Window 1: train 2016–2017  →  test 2018
Window 2: train 2016–2018  →  test 2019
Window 3: train 2016–2019  →  test 2020
Window 4: train 2016–2020  →  test 2021
Window 5: train 2016–2021  →  test 2022
Window 6: train 2016–2022  →  test 2023
Window 7: train 2016–2023  →  test 2024
```

Each parameter pair receives one out-of-sample Sharpe per window. The final score is the mean across all windows, which spans multiple market regimes — the 2018 correction, the 2020 crash, the 2022 rate-hike bear market, and the subsequent recovery. Parameters that score consistently across these environments are genuinely robust, not just well-fitted to a single historical episode.

---

## Limitations

- **Lookahead bias:** closing prices are used for both signal generation and trade execution on the same day. In practice, execution would occur the following open.
- **No transaction costs:** brokerage fees and slippage are not modelled.
- **Single asset:** the system is designed for one ticker at a time.
- **US-centric risk-free rate:** `^IRX` reflects US Treasury yields. For non-US assets, a local equivalent should be substituted.