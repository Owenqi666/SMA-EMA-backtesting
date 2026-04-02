# SMA vs EMA Crossover Backtesting System

A from-scratch quantitative backtesting system that implements Simple Moving Average (SMA) and Exponential Moving Average (EMA) crossover strategies, compares their risk-adjusted performance, and optimises parameters using grid search with train/test validation.

Built without any financial libraries — all strategy logic, performance metrics, and optimisation are implemented in pure Python.

---

## File Structure

```
sma-ema-backtest/
├── README.md
├── project_fixed.py   ← SMA strategy: load, compute, backtest, metrics
├── ema.py             ← EMA strategy: same structure, different MA calculation
├── compare.py         ← Run both strategies side by side and print results
└── grid_search.py     ← Parameter optimisation with train/test split
```

---

## Installation

```bash
pip install yfinance
```

No other dependencies required. All metric calculations use the Python standard library.

---

## Usage

### Run SMA strategy only

```bash
python project_fixed.py
```

```
Ticker (e.g. AAPL): AAPL
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

Example output:

```
Ticker: AAPL  |  Short window: 20  |  Long window: 50

Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)           12.34      15.67
Buy & Hold Return (%)         18.50      18.50
Max Drawdown (%)             -23.10     -19.80
Sharpe Ratio                   0.45       0.61
Total Trades                      8         12

Winner by metric:
  Strategy Return : EMA
  Max Drawdown    : EMA  (lower is better)
  Sharpe Ratio    : EMA
  Total Trades    : SMA  (fewer is cheaper)
```

### Grid search parameter optimisation

```bash
python grid_search.py
```

Scans 200+ window combinations on the training set (2020–2022), then evaluates the best parameters on an unseen test set (2023–2024).

Results on AAPL (2020-01-01 to 2024-12-31):

```
Loaded 1257 trading days for AAPL (2020-01-01 to 2024-12-31).

Train: 754 days  |  Test: 503 days

=======================================================
            Params  Train Sharpe   Test Sharpe
-------------------------------------------------------
SMA         (5, 30)          0.99          0.66
EMA         (5, 20)          0.98          1.03
=======================================================

Top 5 SMA parameter combinations (train set):
  Short   Long   Sharpe
  ----------------------
      5     30     0.99
      5     20     0.90
     50    100     0.89
     15     20     0.89
     55    100     0.86

Top 5 EMA parameter combinations (train set):
  Short   Long   Sharpe
  ----------------------
      5     20     0.98
     10     20     0.86
      5    190     0.78
      5    200     0.78
      5    140     0.71

Overall winner (by test Sharpe): EMA  (1.03 vs 0.66)
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

**Sharpe Ratio** — risk-adjusted return, measuring excess return earned per unit of risk, annualised using 252 trading days:

$$\text{Sharpe} = \frac{\mu - r_f / 252}{\sigma} \times \sqrt{252}$$

where $\mu$ is the mean daily return, $\sigma$ is its standard deviation, and $r_f = 0.05$ by default.

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

where $s$ is the short window and $l$ is the long window. All combinations where $s \geq l$ are skipped. The objective function is the Sharpe ratio.

### Train/Test Split

To guard against overfitting, the data is split before optimisation:

```
Full data  2020–2024
  ├── Train  60%  2020–2022  ← grid search runs here
  └── Test   40%  2023–2024  ← best params evaluated here
```

A large drop in Sharpe from train to test suggests the parameters are overfit to historical data and may not generalise to new market conditions.

---

## Limitations

- **Lookahead bias:** closing prices are used for both signal generation and trade execution on the same day. In practice, execution would occur the following open.
- **No transaction costs:** brokerage fees and slippage are not modelled.
- **In-sample risk:** even with a train/test split, both sets are drawn from the same 5-year period and may share market regime characteristics.
- **Single asset:** the system is designed for one ticker at a time.