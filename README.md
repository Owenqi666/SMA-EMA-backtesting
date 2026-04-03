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
Strategy Return (%)          447.33     452.43
Buy & Hold Return (%)       1046.73    1044.52
Max Drawdown (%)             -24.16     -27.53
Sharpe Ratio                   0.85       0.81
Total Trades                     55         45
Total Fee Cost               -0.0836    -0.0604
```

*Benchmark configuration: fee rate 0.05% one-way, threshold 0%, T+1 execution.*

**Equity curve:** Both strategies significantly underperformed buy & hold (5.48× and
5.53× vs 11.47×). AAPL's decade-long uptrend punished crossover strategies — every
false signal during shallow pullbacks forced a sell, with re-entry only at higher prices,
repeatedly missing the core of each rally. Transaction costs are visible in the fee
column: SMA's higher trade count (55 vs 45) results in 38% more fee drag than EMA
despite similar gross returns.

**Signal chart:** SMA generated 55 trades vs EMA's 45. The SMA chart shows dense,
overlapping signals during the first 1,000 days (2016–2019) when AAPL moved in a
low-volatility uptrend — the two moving averages stayed close together, causing
constant whipsawing. EMA's faster response reduced this considerably.

**Grid search:** Optimal SMA parameters: short=5, long=70, threshold=0% (mean test
Sharpe 1.30). Optimal EMA parameters: short=5, long=20, threshold=0.2% (mean test
Sharpe 1.14). Overall winner by mean test Sharpe: SMA. Both strategies favoured small
short windows — on a smooth, low-volatility uptrend, shorter windows reduce lag cost
slightly. The threshold had minimal effect for SMA at the optimal window pair, but
EMA benefited from a small threshold of 0.2% to filter the noise inherent in its
faster-responding gap series.

**Takeaway:** On AAPL, doing nothing outperformed active trading by roughly 2× over
the decade. The result is consistent with the original analysis — the structural
disadvantage of crossover strategies on persistently trending assets holds even after
the more realistic execution model is applied.

---

### NVDA (2016–2026) — Short: 20, Long: 50
```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)         1316.25    7445.40
Buy & Hold Return (%)      23602.60   23519.92
Max Drawdown (%)             -62.95     -57.91
Sharpe Ratio                   0.87       1.21
Total Trades                     46         43
Total Fee Cost               -0.1122    -0.4992
```

*Benchmark configuration: fee rate 0.05% one-way, threshold 0%, T+1 execution.*

**Equity curve:** The gap is far more dramatic than AAPL. Buy & hold turned 1.0 of initial capital into 237×, while SMA only reached 14.16× and EMA 75.49×. NVDA's entire return is
concentrated in the AI boom of 2023–2024, where the price surged parabolically. Both
strategies were repeatedly stopped out during this explosive phase by death crosses,
re-entering at progressively higher prices and missing most of the move. EMA
dramatically outperformed SMA (75.49× vs 14.16×) because its faster response
allowed re-entry sooner after each pullback. The fee drag on EMA is notably higher
(-0.4992 vs -0.1122) — a consequence of its much larger position size at each trade
during the price surge, where 0.05% of a 75× portfolio is a meaningful absolute cost.

**Signal chart:** The first 1,500 days show dense signals at very low price levels —
a long period of low-price sideways movement generating noise. The real money was in
Days 1,800–2,500, where both strategies managed to participate partially but were
frequently ejected by short-lived death crosses during the parabolic rise. EMA's
signal chart shows notably fewer false exits than SMA during this phase.

**Grid search:** Optimal SMA parameters: short=55, long=60, threshold=0.2% (mean
test Sharpe 0.96). Optimal EMA parameters: short=50, long=180, threshold=0% (mean
test Sharpe 1.36). Overall winner: EMA. The results are the opposite of AAPL —
large windows dominate for both strategies. NVDA's extreme volatility generates
enormous noise at small window sizes; large windows filter short-term fluctuations
and follow only the genuine multi-month trend. The EMA heatmap shows a broad green
region across the top-right, confirming EMA is robust to parameter choice on NVDA
as long as windows are kept large. The small threshold benefit for SMA (0.2%) confirms
that modest noise filtering helps on a volatile asset even with large windows.

**Takeaway:** On NVDA, the parabolic AI-driven rally was essentially untrackable with
a lagging crossover strategy. Buy & hold was the dominant approach by an enormous
margin. EMA's edge over SMA was the largest of the three assets tested.

---

### META (2016–2026) — Short: 20, Long: 50
```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          704.54     805.33
Buy & Hold Return (%)        500.62     550.27
Max Drawdown (%)             -32.89     -23.48
Sharpe Ratio                   0.86       0.89
Total Trades                     43         32
Total Fee Cost               -0.0731    -0.0443
```

*Benchmark configuration: fee rate 0.05% one-way, threshold 0%, T+1 execution.*

**Equity curve:** META is the only case where both strategies outperformed buy & hold
— SMA reached 8.05× vs buy & hold's 6.01×, and EMA 9.05× vs 6.50×. This confirms
the original hypothesis: META's 2022 crash created exactly the environment where
crossover strategies thrive. EMA now clearly outperforms SMA on both return and
drawdown, a result more pronounced than in the previous model due to EMA's lower trade
count reducing fee drag (32 vs 43 trades, fee cost -0.0443 vs -0.0731).

The mechanism is visible in the equity curve. Around Day 1,500 (early 2022), META's
price peaked near USD 370 and began a steep decline to below USD 100. The death cross
triggered a sell signal near the top of this move, keeping the strategy in cash through
most of the 76% drawdown. When the golden cross appeared in mid-2023, the strategy
re-entered near the bottom of the recovery, capturing the full subsequent rally to
USD 650+. Buy & hold suffered the full crash and only recovered later.

**Signal chart:** EMA's signal chart shows notably cleaner entries and exits around
the 2022 crash compared to SMA. EMA identified the death cross earlier and the golden
cross sooner during recovery, resulting in a better entry price on the rebound. Both
charts confirm that the 2022 crash was the single most important event for strategy
performance — everything else was secondary.

**Grid search:** Optimal SMA parameters: short=35, long=40, threshold=0.5% (mean
test Sharpe 0.82). Optimal EMA parameters: short=20, long=90, threshold=2.0% (mean
test Sharpe 0.96). Overall winner: EMA. Unlike AAPL and NVDA, META's EMA heatmap is
almost entirely green — almost any reasonable window combination produces positive
Sharpe, confirming the strategy's edge comes from the market structure rather than
precise parameter tuning. The relatively high optimal threshold for EMA (2.0%) is
notable: it suggests that on META, filtering out marginal crossovers significantly
improves risk-adjusted returns by reducing false exits during the volatile 2022–2023
recovery phase.

**Takeaway:** META remains the clearest demonstration of when crossover strategies
work. The strategy's inherent lag became an advantage — it stayed in the trade long
enough to confirm the trend before selling, then re-entered after the bottom was
confirmed. EMA's outperformance over SMA on this asset is now cleaner and more
convincing with the realistic execution model applied.

---

### Cross-Asset Comparison

| Ticker | SMA Return | EMA Return | Buy & Hold | SMA vs B&H | EMA vs B&H | Best Window (EMA) |
|--------|-----------|-----------|------------|------------|------------|-------------------|
| AAPL | 5.48x | 5.53x | 11.47x | -52% | -52% | short=5, long=20, θ=0.2% |
| NVDA | 14.16x | 75.49x | 237.03x | -94% | -68% | short=50, long=180, θ=0% |
| META | 8.05x | 9.05x | 6.01x | +34% | +39% | short=20, long=90, θ=2.0% |

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
The lower trade count also means systematically less fee drag — on META, EMA's fee
cost was 39% lower than SMA's despite similar gross exposure.

**Both strategies underperform buy & hold on strongly trending assets.** AAPL and NVDA
demonstrate this clearly. The strategy is structurally disadvantaged when an asset
moves upward persistently with only shallow pullbacks — the lag cost exceeds the
drawdown-protection benefit.

**META demonstrates the strategy's genuine edge.** A deep, sustained crash followed
by recovery is exactly the environment crossover strategies were designed for. The 2022
META drawdown of 76% was avoided almost entirely, with EMA producing 9.05× vs buy &
hold's 6.50× — outperformance of approximately 39%.

**Optimal parameters are asset-specific and cannot be transferred.** AAPL rewarded
small windows, NVDA required very large windows, and META performed well across almost
any parameter combination. The optimal threshold also varies significantly: 0% for NVDA
(noise filtering hurts on a directional trend), 0.2% for AAPL, and 2.0% for META
(aggressive filtering helps during choppy recovery phases). Walk-forward validation
is essential to avoid fitting parameters to a single historical episode.

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

Signal generation is based on the **percentage gap** between the short and long MA,
defined as:

$$g_t = \frac{S_t - L_t}{L_t}$$

where $S_t$ is the short (fast) MA and $L_t$ is the long (slow) MA on day $t$. Using
a relative gap rather than an absolute difference ensures the signal condition is
scale-invariant — a $1\%$ separation means the same thing whether the stock trades
at USD 20 or USD 200.

**Golden cross — buy signal:** the gap crosses upward through the threshold $\theta$:

$$g_{t-1} \leq \theta \quad \text{and} \quad g_t > \theta \implies \text{buy}$$

**Death cross — sell signal:** the gap crosses downward through $-\theta$:

$$g_{t-1} \geq -\theta \quad \text{and} \quad g_t < -\theta \implies \text{sell}$$

When $\theta = 0$ this reduces to the classical crossover: a signal fires the moment
the fast MA crosses the slow MA. When $\theta > 0$, the fast MA must pull away from
the slow MA by more than $\theta$ before a signal is recorded. See the following
section for the rationale.

The strategy is fully invested when holding (all-in) and holds cash otherwise.
No short selling.

### Noise Filter — Crossover Threshold

A plain crossover signal fires the instant the two moving averages change their
relative order. In low-volatility or sideways markets, the two MAs hover close
together and cross repeatedly over short intervals — each crossing generates a
trade, but most of them reverse quickly. These are whipsaw trades: the signal is
technically valid but economically meaningless, and each round trip incurs
transaction costs.

Market noise is inherently proportional. A daily fluctuation of 1% on a
USD 50 stock and the same 1% on a USD 500 stock represent the same economic
signal strength, so the filter must operate in percentage terms. The threshold $\theta$
is therefore expressed as a fraction of the long MA value, consistent with how
the gap $g_t$ is defined.

**Effect of raising $\theta$:**

- Fewer trades — only sustained, decisive crossovers trigger signals
- Reduced whipsaw losses in choppy markets
- Slower entry and exit — the strategy lags further behind genuine trend changes
- Risk of missing the early part of a move entirely if the gap never exceeds $\theta$

The relationship between $\theta$ and window size matters. Smaller windows produce
noisier MA series with larger short-term gaps, so a given $\theta$ has a stronger
filtering effect on small-window strategies. Larger windows already smooth out
short-term noise, so their gap series is quieter and a smaller $\theta$ is sufficient.
This interaction is why $\theta$ is optimised jointly with the window sizes in
`grid_search.py` rather than chosen independently.

The default value is $\theta = 0$, preserving the classical crossover behaviour. The grid search evaluates $\theta$ in {0, 0.2%, 0.5%, 1.0%, 2.0%} alongside all window combinations, selecting the triple $(s, l, \theta)$ that maximises mean out-of-sample Sharpe across walk-forward windows.

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

- **Buy:** the number of shares received is reduced by the fee:
  
  $$\text{shares} = \frac{\text{cash}}{\text{price}} \times (1-f)$$

- **Sell:** the cash proceeds are reduced by the fee:
  
  $$\text{cash} = \text{shares} \times \text{price} \times (1-f)$$

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

`grid_search.py` performs an exhaustive search over three parameters simultaneously:

$$s \in \{5, 10, 15, \ldots, 55\}, \qquad l \in \{20, 30, 40, \ldots, 200\}, \qquad \theta \in \{0,\, 0.002,\, 0.005,\, 0.01,\, 0.02\}$$

where $s$ is the short window, $l$ is the long window, and $\theta$ is the crossover
threshold. All combinations where $s \geq l$ are skipped. The objective function is
the mean out-of-sample Sharpe across all walk-forward windows.

The three parameters are optimised jointly rather than independently because they
interact: the noise-filtering effect of $\theta$ depends on how volatile the MA gap
series is, which is itself determined by the window sizes. Optimising each dimension
in isolation would miss this interaction and potentially select a $\theta$ that is
either redundant or too aggressive given the chosen windows.

The search space grows to approximately 450 combinations per strategy (versus ~90
without $\theta$), which increases runtime by roughly 5× but produces results that
account for realistic cost conditions including both transaction fees and signal noise.

The heatmap output marginalises over $\theta$ — each cell displays the best Sharpe
achieved across all threshold values for that $(s, l)$ pair. The top-5 results table
shows the full three-parameter combination $(s,\, l,\, \theta)$ for each ranked entry.

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