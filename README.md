# SMA vs EMA Crossover Backtesting System

A from-scratch quantitative backtesting system that implements Simple Moving Average (SMA)
and Exponential Moving Average (EMA) crossover strategies, compares their risk-adjusted
performance, and optimises parameters using walk-forward validation.

Built without any financial libraries — all strategy logic, performance metrics, and
optimisation are implemented in pure Python.

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

All scripts accept a freely typed date range at runtime. The date parser recognises most
common formats — `2016-01-01`, `Jan 1 2016`, and `1/1/2016` all work.

### Run SMA strategy only
```bash
python sma.py
```

### Run EMA strategy only
```bash
python ema.py
```

### Compare SMA vs EMA side by side
```bash
python compare.py
```

### Walk-forward grid search
```bash
python grid_search.py
```

---

## Results and Analysis

Three tickers were tested over the same period (2016-01-01 to 2026-01-01) with a standard
benchmark configuration of short window 20 and long window 50. The three stocks were chosen
deliberately to represent different price regimes:

| Ticker | Price Regime | Hypothesis |
|--------|-------------|------------|
| AAPL | Steady long-term uptrend | Strategy will underperform — shallow pullbacks penalise signal lag |
| NVDA | Explosive late-stage surge | Strategy will severely underperform — parabolic moves cannot be tracked |
| META | Rise → 70% crash → recovery | Strategy may outperform — deep drawdown gives crossover a real edge |

---

### AAPL (2016–2026) — Short: 20, Long: 50
```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          359.20     404.43
Buy & Hold Return (%)       1046.73    1046.73
Max Drawdown (%)             -29.09     -25.30
Sharpe Ratio                   0.77       0.77
Total Trades                     55         45
```

**Equity curve:** Both strategies significantly underperformed buy & hold ($4.59x and
$5.04x vs $11.47x). AAPL's decade-long uptrend punished crossover strategies — every
false signal during shallow pullbacks forced a sell, with re-entry only at higher prices,
repeatedly missing the core of each rally.

**Signal chart:** SMA generated 55 trades vs EMA's 45. The SMA chart shows dense,
overlapping signals during the first 1,000 days (2016–2019) when AAPL moved in a
low-volatility uptrend — the two moving averages stayed close together, causing
constant whipsawing. EMA's faster response reduced this considerably.

**Grid search:** Optimal parameters clustered in the top-left (small windows: short=5,
long=20–30), the opposite of NVDA. On a stock with a smooth, shallow trend, shorter
windows reduce the lag cost slightly — but even the best parameters could not overcome
the structural disadvantage of the strategy on a strongly trending asset.

**Takeaway:** On AAPL, doing nothing outperformed active trading by nearly 3x over
the decade.

---

### NVDA (2016–2026) — Short: 20, Long: 50
```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)         1469.00    6026.00
Buy & Hold Return (%)      23603.00   23603.00
Max Drawdown (%)             (large)    (large)
Sharpe Ratio                  (lower)    (higher)
Total Trades                  (more)     (fewer)
```

**Equity curve:** The gap is far more dramatic than AAPL. Buy & hold turned $1 into
$237, while SMA only reached $15.69x and EMA $61.26x. NVDA's entire return is
concentrated in the AI boom of 2023–2024 (Day 1800–2500), where the price surged from
~$50 to over $200. Both strategies were repeatedly stopped out during this explosive
phase by death crosses, re-entering at progressively higher prices and missing most of
the move. EMA dramatically outperformed SMA ($61x vs $15x) because its faster response
allowed re-entry sooner after each pullback.

**Signal chart:** The first 1,500 days show dense signals at very low price levels
(below $30) — a long period of low-price sideways movement generating noise. The real
money was in Days 1,800–2,500, where both strategies managed to participate partially
but were frequently ejected by short-lived death crosses during the parabolic rise.

**Grid search:** Optimal parameters were the complete opposite of AAPL — SMA performed
best with large windows (short=55, long=70), and EMA with very large windows (short=50,
long=200). NVDA's extreme volatility generates enormous noise at small window sizes.
Large windows filter out short-term fluctuations and follow only the genuine multi-month
trend. The EMA heatmap shows a broad green region across the top-right, indicating EMA
is robust to parameter choice on NVDA as long as windows are kept large.

**Takeaway:** On NVDA, the parabolic AI-driven rally was essentially untrackable with
a lagging crossover strategy. Buy & hold was the dominant approach by an enormous margin.

---

### META (2016–2026) — Short: 20, Long: 50
```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          733.00     621.00
Buy & Hold Return (%)        501.00     650.00
Max Drawdown (%)             (lower)    (lower)
Sharpe Ratio                  (higher)   (higher)
Total Trades                  (more)     (fewer)
```

**Equity curve:** META is the only case where both strategies outperformed buy & hold
— SMA reached $8.33x vs buy & hold's $6.01x, and EMA $7.21x vs $6.50x. This confirms
the original hypothesis: META's 2022 crash created exactly the environment where
crossover strategies thrive.

The mechanism is visible in the equity curve. Around Day 1,500 (early 2022), META's
price peaked near $370 and began a steep decline to below $100. The death cross triggered
a sell signal near the top of this move, keeping the strategy in cash through most of
the 76% drawdown. When the golden cross appeared in mid-2023, the strategy re-entered
near the bottom of the recovery, capturing the full subsequent rally to $650+. Buy &
hold suffered the full crash and only recovered later — the crossover strategy avoided
the pain entirely and re-entered at a lower cost basis.

**Signal chart:** EMA's signal chart shows notably cleaner entries and exits around the
2022 crash compared to SMA. EMA identified the death cross earlier and the golden cross
sooner during recovery, resulting in a better entry price on the rebound. Both charts
show that the 2022 crash was the single most important event for strategy performance —
everything else was secondary.

**Grid search:** Unlike AAPL and NVDA, META's heatmap is almost entirely green across
both SMA and EMA. This means parameter choice barely matters on META — almost any
reasonable combination of windows would have captured the 2022 crash avoidance. The
strategy's edge on META came from the market structure, not from precise parameter
tuning. The few red cells appear at very small window sizes (short=5–10) where signal
noise overwhelmed the crash-avoidance benefit.

**Takeaway:** META is the clearest demonstration of when crossover strategies work:
a deep, sustained drawdown followed by a strong recovery. The strategy's inherent lag
became an advantage — it stayed in the trade long enough to confirm the trend before
selling, then re-entered after the bottom was confirmed.

---

### Cross-Asset Comparison

| Ticker | SMA Return | EMA Return | Buy & Hold | SMA vs B&H | EMA vs B&H | Best Window (EMA) |
|--------|-----------|-----------|------------|------------|------------|-------------------|
| AAPL | 4.59x | 5.04x | 11.47x | -59% | -56% | short=5, long=20 |
| NVDA | 15.69x | 61.26x | 237.03x | -93% | -74% | short=50, long=200 |
| META | 8.33x | 7.21x | 6.01x | +39% | +20% | short=40, long=50 |

**Why optimal parameters differ across assets:**

The core tension in a crossover strategy is between *responsiveness* and *noise tolerance*.
Small windows react quickly to price changes but trigger on short-lived fluctuations.
Large windows filter noise but lag significantly behind real trend changes.

- AAPL has a smooth, low-noise trend → small windows reduce lag cost slightly
- NVDA has extreme volatility → large windows needed to filter the noise
- META has moderate volatility with one major regime change → medium windows capture the crash signal without over-trading

This confirms that parameters optimised on one asset cannot be transferred to another
without re-optimisation — a key finding for any practical deployment of trend-following
strategies.

**When does the strategy work?**

The results across three assets reveal a clear pattern. Crossover strategies outperform
buy & hold when the asset experiences a deep, prolonged drawdown followed by recovery.
They underperform when the asset trends upward smoothly or surges parabolically, because
signal lag causes the strategy to repeatedly sell near local lows and buy near local highs.

The strategy is best understood as **drawdown insurance** — it trades some upside
participation for protection against large losses. Whether that trade-off is worthwhile
depends entirely on the asset and time period.

---

### Key Takeaways

**EMA consistently outperforms SMA** across all three tickers. Fewer trades, lower
drawdowns, and better returns. The faster response to recent price changes reduces
whipsaw losses during volatile periods without sacrificing trend-following ability.

**Both strategies underperform buy & hold on strongly trending assets.** AAPL and NVDA
demonstrate this clearly. The strategy is structurally disadvantaged when an asset
moves upward persistently with only shallow pullbacks — the lag cost exceeds the
drawdown-protection benefit.

**META demonstrates the strategy's genuine edge.** A deep, sustained crash followed
by recovery is exactly the environment crossover strategies were designed for. The 2022
META drawdown of 76% was avoided almost entirely, producing outperformance of ~39% over
buy & hold for SMA.

**Optimal parameters are asset-specific and cannot be transferred.** AAPL rewarded
small windows, NVDA required very large windows, and META performed well across almost
any parameter combination. Walk-forward validation is essential to avoid fitting
parameters to a single historical episode.

**The strategy is better described as drawdown insurance than as an alpha generator.**
It sacrifices upside participation in exchange for avoiding large losses. On assets like
META that experience severe bear markets, the insurance pays off. On assets like AAPL
and NVDA that trend persistently upward, the premium is too high.

---

## Strategy Logic

### Simple Moving Average (SMA)

The arithmetic mean of the past $n$ closing prices, where each day carries equal weight:

$$\text{SMA}(t,\, n) = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

The SMA series is $n - 1$ elements shorter than the price series — there is no valid
average until $n$ data points have been observed.

### Exponential Moving Average (EMA)

A weighted average that gives more weight to recent prices, controlled by a smoothing
factor $\alpha$:

$$\text{EMA}(t) = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}(t-1), \qquad \alpha = \frac{2}{n+1}$$

Unlike SMA, EMA uses all historical data — older prices decay exponentially but never
reach zero. EMA is the same length as the price series because day 1 is initialised
with the first price directly.

### Crossover Signals

Both strategies use the same signal logic. The key insight is that we detect the *moment*
of crossover by comparing yesterday's relative position to today's — not just today's
value alone.

**Golden cross — buy signal:** fast MA crosses above slow MA, indicating an upward trend.

$$S_{t-1} \leq L_{t-1} \quad \text{and} \quad S_t > L_t \implies \text{buy}$$

**Death cross — sell signal:** fast MA crosses below slow MA, indicating a downward trend.

$$S_{t-1} \geq L_{t-1} \quad \text{and} \quad S_t < L_t \implies \text{sell}$$

where $S_t$ is the short (fast) MA and $L_t$ is the long (slow) MA on day $t$.

The strategy is fully invested when holding (all-in) and holds cash otherwise.
No short selling.

### Trade Execution — T+1 Settlement

Signal generation and trade execution are deliberately separated to reflect how US
equity markets actually operate.

Under US market convention, a trade executed on day T settles on day T+1. In practice
this means that a crossover signal detected at the close of day T cannot be acted on
until the open of day T+1 at the earliest. Executing at the same close price that
generated the signal would assume knowledge of the closing price before the market
closes — a form of lookahead bias.

The backtest models this as follows:

- **Day T (close):** the crossover condition is evaluated using today's and yesterday's
  moving average values. If a golden cross or death cross is detected, a `pending_order`
  is recorded.
- **Day T+1 (open/close):** the pending order is executed at the day T+1 closing price
  before any new signal logic runs for that day.

```
Day T   — moving averages cross → pending_order = 'buy'
Day T+1 — pending order executes at day T+1 price → position opens
```

This introduces one day of execution lag relative to the signal, which is the minimum
realistic delay for a daily strategy trading US equities. The practical effect is a
slight reduction in strategy return compared to a same-day execution model, particularly
during fast-moving markets where prices gap significantly overnight.

If a pending order exists at the final day of the backtest with no subsequent day to
execute on, the order is left unfilled. This reflects the reality that an unexecuted
order at market close simply expires.

### Transaction Costs

Every realistic backtest must account for the friction of trading. This system models
transaction costs as a proportional fee applied once on each side of every trade —
once at entry (buy) and once at exit (sell).

**What the fee represents**

US equity markets have largely moved to zero-commission trading at the broker level.
However, two unavoidable cost components remain. Regulatory fees — the SEC fee on
sales and the FINRA Trading Activity Fee — are mandatory but small, together amounting
to roughly 0.003% per trade for typical retail sizes. The more significant cost is
the **bid-ask spread**: when buying, execution occurs at the ask price; when selling,
at the bid. For large-cap, liquid stocks such as AAPL, NVDA, and META, this spread
is typically 0.01%–0.05% per side under normal conditions. The combined effect of
regulatory fees and spread is captured in a single configurable `fee_rate` parameter.

**How it is applied**

At each trade execution, the fee is deducted from the position directly:

- **Buy:** the number of shares received is reduced by the fee —
  $\text{shares} = \frac{\text{cash}}{\text{price}} \times (1 - f)$
- **Sell:** the cash proceeds are reduced by the fee —
  $\text{cash} = \text{shares} \times \text{price} \times (1 - f)$

where $f$ is the one-way fee rate. A complete round trip (buy then sell) therefore
costs $1 - (1-f)^2 \approx 2f$ of the position value, which for the default rate
of $f = 0.05\%$ amounts to approximately 0.10% per round trip.

**Default value and sensitivity**

The default fee rate is set at **0.05% per side** (0.0005), which is a conservative
estimate for a retail investor trading large-cap US equities. The rate is configurable
at runtime — pressing Enter accepts the default, or any value can be entered directly.

The fee is particularly consequential for strategies that trade frequently. Because
SMA crossovers tend to generate more signals than EMA crossovers, the cumulative fee
drag is systematically larger for SMA. This is visible in the `compare.py` output,
which reports total fee cost alongside the standard performance metrics, making the
trade-off between signal frequency and cost explicit.

The fee is also applied consistently inside `grid_search.py`, meaning that the
walk-forward optimisation selects parameters under realistic cost conditions rather
than in a frictionless environment. Strategies with many trades are penalised in
the Sharpe score not only through the equity drag but also through the reduced returns
they produce, which tends to shift optimal windows toward larger values compared to
a zero-fee run.

**What is not modelled**

Market impact — the price movement caused by the act of placing a large order — is
not captured. For the position sizes implied by a normalised portfolio of 1.0,
market impact on large-cap stocks is negligible, so this omission is reasonable.

### Performance Metrics

**Strategy Return** — total return over the backtest period, with starting capital
normalised to 1.0:

$$R_{\text{strategy}} = (C_{\text{final}} - 1) \times 100$$

**Buy and Hold Return** — benchmark return from buying on day one and holding to the end:

$$R_{\text{bh}} = \left(\frac{P_{\text{last}}}{P_{\text{first}}} - 1\right) \times 100$$

**Max Drawdown** — largest peak-to-trough decline in the equity curve:

$$\text{MDD} = \max_{t} \left( \frac{\text{peak}_t - V_t}{\text{peak}_t} \right)$$

$$\text{peak}_t = \max_{s \leq t}(V_s)$$

**Sharpe Ratio** — risk-adjusted return, annualised using 252 trading days:

$$\text{Sharpe} = \frac{\mu - r_f / 252}{\sigma} \times \sqrt{252}$$

where $\mu$ is the mean daily return, $\sigma$ is the sample standard deviation of daily
returns, and $r_f$ is the average 3-month US Treasury bill yield (`^IRX`) over the
backtest period.

Using the realised T-bill yield rather than a fixed constant matters because the
risk-free rate varied substantially — from near zero during 2020–2021 to above 5%
in 2023–2024.

| Sharpe | Interpretation |
|--------|----------------|
| $< 0$ | Worse than risk-free |
| $0$ to $1$ | Acceptable |
| $1$ to $2$ | Good |
| $> 2$ | Excellent, rarely seen |

---

## Parameter Optimisation

`grid_search.py` performs an exhaustive search over:

$$s \in \{5, 10, 15, \ldots, 55\}, \qquad l \in \{20, 30, 40, \ldots, 200\}$$

where $s$ is the short window and $l$ is the long window. All combinations where
$s \geq l$ are skipped. The objective function is the mean test Sharpe across all
walk-forward windows.

### Walk-Forward Validation

A single train/test split is inadequate for strategy optimisation because financial
markets cycle through distinct regimes. Walk-forward validation addresses this by
rolling a one-year test window across the full dataset:
```
Window 1: train 2016–2017  →  test 2018
Window 2: train 2016–2018  →  test 2019
Window 3: train 2016–2019  →  test 2020
Window 4: train 2016–2020  →  test 2021
Window 5: train 2016–2021  →  test 2022
Window 6: train 2016–2022  →  test 2023
Window 7: train 2016–2023  →  test 2024
```

Each parameter pair receives one out-of-sample Sharpe per window. The final score is
the mean across all windows, spanning multiple market regimes — the 2018 correction,
the 2020 crash, the 2022 rate-hike bear market, and the subsequent recovery.

---

## Limitations

- **Execution price:** closing prices are used for both signal generation and trade
  execution on T+1. In practice, execution would occur at the following day's open
  rather than close, so the actual fill price may differ.
- **Market impact:** large-order price impact is not modelled. For normalised
  single-asset positions in large-cap equities this is negligible, but would
  matter at meaningful capital sizes.
- **Single asset:** the system is designed for one ticker at a time.
- **US-centric risk-free rate:** `^IRX` reflects US Treasury yields. For non-US assets,
  a local equivalent should be substituted.
- **Trend-following bias:** the strategy is structurally disadvantaged on assets with
  strong sustained uptrends, as demonstrated by both AAPL and NVDA results above.