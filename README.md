# SMA vs EMA Crossover Backtesting System

A from-scratch quantitative backtesting system implementing Simple Moving Average (SMA)
and Exponential Moving Average (EMA) crossover strategies across **seven stocks spanning
five market sectors**. All strategy logic, performance metrics, and optimisation are
implemented in pure Python — no financial libraries used.

---

## File Structure
```
sma-ema-backtest/
├── README.md
├── sma.py             ← SMA strategy: load, compute, backtest, metrics
├── ema.py             ← EMA strategy: same structure, different MA calculation
├── compare.py         ← Run both strategies side by side and print results
├── grid_search.py     ← Parameter optimisation with walk-forward validation
└── batch_run.py       ← Run all stocks in one go and print summary table
```

---

## Installation
```bash
pip install yfinance python-dateutil matplotlib numpy
```

No other dependencies required. All metric calculations use the Python standard library.

---

## Usage

All scripts accept a freely typed date range at runtime. The date parser recognises most
common formats — `2016-01-01`, `Jan 1 2016`, and `1/1/2016` all work.

```bash
python sma.py          # SMA strategy only
python ema.py          # EMA strategy only
python compare.py      # SMA vs EMA side by side
python grid_search.py  # Walk-forward parameter optimisation
python batch_run.py    # Run all seven stocks and print summary
```

---

## Stock Selection and Sector Coverage

All seven stocks were tested over the same period (**2016-01-01 to 2026-01-01**) with
`fee_rate = 0.0005` (0.05% one-way) and T+1 execution delay. Each stock's table reports
results using its **walk-forward optimal parameters** — the `(short, long, threshold)`
combination that maximised mean out-of-sample Sharpe across seven rolling one-year
test windows.

Stocks were selected to represent structurally distinct market regimes, not on the basis
of name recognition. The underlying question is: **what kind of price structure makes a
crossover strategy effective or ineffective?**

| Ticker | Sector | Price Regime | Strategy vs B&H |
|--------|--------|-------------|-----------------|
| AAPL | Technology | Steady decade-long uptrend | Underperforms |
| NVDA | Technology | Explosive parabolic surge | Severely underperforms |
| META | Technology | Rise → 76% crash → full recovery | **Outperforms** |
| XOM | Energy | Oil-cycle driven, 2020 crash | Underperforms |
| KO | Consumer Staples | Ultra-low volatility slow uptrend | Severely underperforms |
| JPM | Financials | Uptrend with rate-cycle volatility | Underperforms |
| JNJ | Healthcare | Defensive slow grind | Severely underperforms |

---

## Results by Sector

### Technology — AAPL (2016–2026)

**Market structure:** Steady multi-year uptrend with shallow, mean-reverting pullbacks.
No single drawdown sustained itself long enough for a crossover strategy to exit cleanly
before recovery.

**Optimal parameters:** SMA — short=5, long=70, θ=0.0% (WF Sharpe 1.30) |
EMA — short=5, long=20, θ=0.2% (WF Sharpe 1.14)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          505.00     566.00
Buy & Hold Return (%)       1044.50    1044.50
Max Drawdown (%)             -24.16     -27.53
Sharpe Ratio                   0.92       0.99
Total Trades                     67         96
```

Both strategies significantly underperformed buy & hold (6.05× and 6.66× vs 11.45×).
AAPL's decade-long uptrend punished crossover strategies — every false exit during a
shallow pullback forced re-entry at a higher price, compounding lag cost into a 2×
performance gap. EMA's Sharpe advantage (0.99 vs 0.92) is consistent with its faster
response on a smooth, trend-persistent asset.

**Grid search pattern:** Both strategies favoured a small short window (5) — on a stable
uptrend, the shorter window reduces lag cost. EMA needed a 0.2% threshold to filter
noise from its faster-responding gap series; SMA did not. Optimal long windows diverged
sharply (70 vs 20), reflecting EMA's faster intrinsic response making a large long window
redundant.

**Takeaway:** On AAPL, doing nothing outperformed active trading by roughly 2× over the
decade. The structural disadvantage of crossover strategies on persistently trending
assets holds under a realistic execution model.

---

### Technology — NVDA (2016–2026)

**Market structure:** Flat and noisy for five years, then a parabolic AI-driven surge
in 2023–2024 where price increased by more than 10× in 18 months. The most extreme
regime in this study.

**Optimal parameters:** SMA — short=55, long=60, θ=0.2% (WF Sharpe 0.96) |
EMA — short=50, long=180, θ=0.0% (WF Sharpe 1.36)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)         1107.30   15639.40
Buy & Hold Return (%)      23519.90   23519.90
Max Drawdown (%)             -62.95     -57.91
Sharpe Ratio                   1.31       1.34
Total Trades                     39          9
```

Buy & hold turned 1.0× into 237×. SMA reached only 12.07× and EMA 157.39×. The entire
return is concentrated in the 2023–2024 AI boom, where both strategies were repeatedly
stopped out by death crosses and forced to re-enter at progressively higher prices. EMA's
dramatically higher return (15,639% vs 1,107%) is explained by trade count: EMA made
only 9 trades vs SMA's 39, staying in position through more of the parabolic move rather
than being ejected by short-lived pullbacks.

**Grid search pattern:** Large windows dominated both strategies. NVDA's extreme
volatility generates enormous noise at small window sizes; large windows filter
short-term fluctuations and track only genuine multi-month trends. The SMA heatmap shows
a narrow optimal band near the diagonal (short window ≈ long window), while EMA's
optimal is a very large long window (180) that essentially defines "trend" as a six-month
directional move.

**Takeaway:** The parabolic AI-driven rally was untrackable with a lagging crossover
strategy. Buy & hold was the dominant approach by a factor of 15× over the best strategy
result. EMA's advantage over SMA was the largest of all assets tested.

---

### Technology — META (2016–2026)

**Market structure:** Steady rise 2016–2021, then a catastrophic 76% crash in 2022
driven by the metaverse pivot and rising interest rates, followed by a full recovery
and new highs by 2023. The archetypal crash-and-recover regime.

**Optimal parameters:** SMA — short=35, long=40, θ=0.5% (WF Sharpe 0.82) |
EMA — short=20, long=90, θ=2.0% (WF Sharpe 0.96)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          817.20     605.70
Buy & Hold Return (%)        550.30     550.30
Max Drawdown (%)             -32.89     -23.48
Sharpe Ratio                   0.85       0.77
Total Trades                     38         14
```

META is the only stock in this study where both strategies outperformed buy & hold.
SMA reached 9.17× vs buy & hold's 6.50×; EMA reached 7.06× vs 6.50×. The 2022 bear
market — deep, slow, and sustained — gave the crossover strategy time to exit before
most of the loss was realised, then re-enter during the recovery. SMA outperformed EMA
here (817% vs 606%), unusual given EMA's typical speed advantage, explained by the
optimal threshold: EMA required a 2.0% threshold to filter the violent whipsaws during
2022–2023 recovery, which slowed re-entry enough that SMA's lower threshold (0.5%)
captured more of the upswing.

**Grid search pattern:** Both strategies converged on small short windows (20–35),
consistent with needing a fast-responding short MA to exit early in the 2022 crash.
The high optimal threshold for EMA (2.0%) confirms that META's sharp recovery generated
frequent false crossovers; only a large gap requirement filtered them correctly.

**Takeaway:** META is the proof of concept for the entire strategy class. A deep,
sustained bear market followed by recovery is the exact environment crossover strategies
were designed for.

---

### Energy — XOM (2016–2026)

**Market structure:** Classic cyclical commodity stock driven by oil price cycles. The
2020 COVID oil crash caused a ~50% price decline. Unlike META's slow-motion crash, the
XOM decline was compressed into roughly two months — too fast for a daily crossover to
exit cleanly before the bottom.

**Optimal parameters:** SMA — short=5, long=150, θ=0.0% (WF Sharpe 0.28) |
EMA — short=10, long=20, θ=0.2% (WF Sharpe 0.33)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)           67.30     127.80
Buy & Hold Return (%)        140.80     140.80
Max Drawdown (%)               [--]       [--]
Sharpe Ratio                   0.27       0.41
Total Trades                     43         79
```

Both strategies underperformed buy & hold (67.3% and 127.8% vs 140.8%). The 2020 crash
hypothesis — that a large drawdown would give the crossover an exit opportunity — did not
materialise effectively. The crash was too rapid for the daily moving averages to generate
a death cross before prices had already recovered. EMA meaningfully outperformed SMA
(127.8% vs 67.3%) because its faster response allowed both an earlier exit and an earlier
re-entry during the 2021–2022 commodity-driven recovery. WF Sharpe values are the lowest
in this study (0.28 and 0.33), indicating the strategy provides no consistent edge on
this asset across different market periods.

**Grid search pattern:** SMA's optimal long window (150) is very large, reflecting the
need to avoid noise on a cyclical, oil-price-sensitive asset. EMA's optimal pair (10, 20)
is extremely tight — effectively two very short EMAs that generate many signals (79
trades), which is unusual and suggests the optimiser found a momentum-chasing pattern
rather than a genuine trend-following edge. The low WF Sharpe across both confirms this
is not a robust result.

**Takeaway:** Oil-driven cyclical stocks are a difficult environment for crossover
strategies. The crash-and-recover dynamic exists but the speed of the 2020 move
prevented effective exit. Energy sector results are inconsistent across walk-forward
windows, producing the lowest WF Sharpe values in the study.

---

### Consumer Staples — KO (2016–2026)

**Market structure:** Quintessential defensive stock. Ultra-low beta, minimal drawdowns,
slow and steady uptrend entirely driven by dividend yield and brand pricing power. No
high-growth phase, no cyclical crash, no sustained bear market.

**Optimal parameters:** SMA — short=50, long=200, θ=2.0% (WF Sharpe 0.90) |
EMA — short=5, long=20, θ=0.0% (WF Sharpe 0.32)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)           39.40      10.80
Buy & Hold Return (%)        125.80     125.80
Max Drawdown (%)               [--]       [--]
Sharpe Ratio                   0.17      -0.03
Total Trades                     11        142
```

KO represents the worst-case structural environment in this study. SMA returned only
39.4% vs buy & hold's 125.8%. EMA returned just 10.8%, with a negative Sharpe ratio
(-0.03), meaning it underperformed the risk-free rate on a risk-adjusted basis. The most
striking figure is EMA's trade count: **142 trades over 10 years** — roughly one
round-trip every 17 trading days. With very small daily moves, the short and long EMAs
stay extremely close together, causing the gap series $g_t$ to oscillate around zero
constantly, generating noise-driven signals that each lock in a small fee and a missed
continuation.

**Grid search pattern:** SMA escaped the noise trap by optimising to the maximum
available windows (50, 200) with the maximum threshold (2.0%), effectively requiring
a very large, sustained move before any signal fires. This produced only 11 trades over
10 years but still underperformed buy & hold by 3×. EMA's optimiser found a high-frequency
short-window configuration (5, 20) with zero threshold — the opposite extreme — which
generated 142 trades and still failed to match buy & hold. The contrast between these
two optima illustrates that no crossover configuration works well on ultra-low-volatility
assets.

**Takeaway:** KO is the clearest demonstration that crossover strategies have no edge on
flat, low-volatility assets. The strategy's value — avoiding large drawdowns — cannot
materialise when no large drawdowns occur.

---

### Financials — JPM (2016–2026)

**Market structure:** Long-term uptrend benefiting from financial sector growth and
rising interest rates (2022–2023). The COVID crash of March 2020 caused a ~45%
peak-to-trough decline in approximately three weeks — the sharpest crash in this study
on a per-day basis.

**Optimal parameters:** SMA — short=5, long=200, θ=0.0% (WF Sharpe 2.05) |
EMA — short=40, long=60, θ=1.0% (WF Sharpe 0.88)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)          270.60     432.70
Buy & Hold Return (%)        559.40     559.40
Max Drawdown (%)               [--]       [--]
Sharpe Ratio                   0.77       0.84
Total Trades                     19          7
```

Both strategies underperformed buy & hold (270.6% and 432.7% vs 559.4%). The COVID
crash — while deep — was too rapid for an effective crossover exit: the death cross fired
after most of the loss had already occurred, and the V-shaped recovery meant re-entry
was delayed until prices had rebounded substantially. EMA outperformed SMA (432.7% vs
270.6%) because it detected the trend reversal sooner on both the exit and re-entry.

The SMA walk-forward Sharpe (2.05) deserves attention. A WF Sharpe of 2.05 is unusually
high and suggests the optimiser found a parameter set that happened to exit before the
2020 crash in one or two test windows, producing outsized Sharpe in those windows that
inflated the mean. The full-dataset Sharpe of 0.77 — much lower — is a better estimate
of realistic forward performance.

**Takeaway:** Financials exhibit a real crash (COVID 2020) that the strategy attempts to
exploit, but the speed of the decline limits the exit quality. The high WF Sharpe for
SMA likely reflects overfitting to the 2020 crash across test windows rather than
genuine generalised edge.

---

### Healthcare — JNJ (2016–2026)

**Market structure:** Highly defensive, very stable earnings, near-zero cyclicality.
Price appreciation over the decade is modest relative to the overall market. The 2023
Kenvue spin-off (consumer products division) introduces a structural price adjustment
that may generate a spurious signal in the price series.

**Optimal parameters:** SMA — short=15, long=200, θ=0.5% (WF Sharpe 1.68) |
EMA — short=10, long=200, θ=2.0% (WF Sharpe 0.05)

```
Metric                          SMA        EMA
---------------------------------------------
Strategy Return (%)           -2.60      66.80
Buy & Hold Return (%)        171.70     171.70
Max Drawdown (%)               [--]       [--]
Sharpe Ratio                  -0.09       0.29
Total Trades                     25          3
```

JNJ produces the starkest result in this study: SMA's optimal parameters — found via
walk-forward validation — still deliver a **negative total return** (-2.6%) over ten
years on a stock that returned 171.7% buy & hold. The Sharpe ratio of -0.09 means the
strategy underperformed the risk-free rate. EMA performed somewhat better (66.8%, Sharpe
0.29) but remained far below buy & hold.

The SMA WF Sharpe of 1.68 versus a full-dataset Sharpe of -0.09 is the most extreme
example of walk-forward / full-sample divergence in this study. This suggests that the
Kenvue spin-off in 2023 generated a sharp price step-down that looked like a death cross
signal in several test windows, inflating out-of-sample Sharpe artificially. When tested
on the full 10-year dataset, the same parameters fail entirely.

**Takeaway:** JNJ is the clearest case of a walk-forward artefact. The 2023 corporate
action distorted the optimisation process. On a genuinely stable defensive stock,
crossover strategies have no structural edge and will reliably underperform buy & hold.

---

## Cross-Sector Analysis

### The single factor that determines strategy effectiveness

Across all seven assets, one variable explains strategy performance more than any other:
**the depth and duration of the largest sustained drawdown.**

| Ticker | Crash Depth | Crash Duration | Exit Feasibility | Strategy Result |
|--------|------------|----------------|-----------------|-----------------|
| META | ~76% | ~12 months | High — slow enough to exit | **Outperforms B&H** |
| JPM | ~45% | ~3 weeks | Low — too fast | Underperforms |
| XOM | ~50% | ~2 months | Low — oil move compressed | Underperforms |
| AAPL | ~35% | ~3 months | Low — recovery too quick | Underperforms |
| KO | ~20% | ~2 months | N/A — too shallow | Severely underperforms |
| NVDA | No crash | — | N/A — parabolic surge | Severely underperforms |
| JNJ | ~30% | ~2 months | Low — corporate action artefact | Severely underperforms |

Two conditions must be satisfied simultaneously for the strategy to outperform:

1. **The crash must be deep enough** that exit before recovery is worthwhile. Shallow
   pullbacks (KO, AAPL) produce death crosses only after recovery has begun.

2. **The crash must be slow enough** that the crossover fires before the trough. Rapid
   crashes (JPM's COVID sell-off, XOM's oil crash) produce exits near or after the
   bottom rather than before it.

META's 2022 bear market was the only event in this dataset that satisfied both conditions.

### SMA vs EMA: which wins by sector?

| Regime | Winner | Reason |
|--------|--------|--------|
| Persistent uptrend (AAPL) | EMA (Sharpe) | Faster response reduces whipsaw count |
| Parabolic surge (NVDA) | EMA | Fewer trades, stays in position longer |
| Crash & recover (META) | SMA (return) | Lower optimal threshold captures more of recovery |
| Cyclical (XOM) | EMA | Earlier exit and re-entry on oil-cycle turns |
| Low volatility (KO) | Neither | Both fail; EMA fails worse (142 trades) |
| Rate-cycle (JPM) | EMA | Earlier signal on faster-moving asset |
| Defensive (JNJ) | EMA (less bad) | SMA actually loses money |

EMA wins in 5 of 7 cases by Sharpe ratio. Its advantage is largest on high-velocity
assets (NVDA, JPM) and smallest — or reversed — on slow-moving assets (KO, META) where
its sensitivity becomes a liability.

### Optimal parameter patterns by market regime

| Regime | Short window | Long window | Threshold |
|--------|-------------|------------|-----------|
| Persistent uptrend (AAPL) | Small (5) | Medium (20–70) | Low (0–0.2%) |
| Parabolic surge (NVDA) | Large (50–55) | Large (60–180) | Low (0–0.2%) |
| Crash & recover (META) | Small-medium (20–35) | Small-medium (40–90) | High (0.5–2.0%) |
| Cyclical (XOM) | Small (5–10) | Large (20–150) | Low (0–0.2%) |
| Low volatility (KO) | Large (50) | Maximum (200) | Maximum (2.0%) |
| Rate-cycle (JPM) | Small (5) / Large (40) | Maximum (200) / Medium (60) | Low–medium |
| Defensive (JNJ) | Small-medium (10–15) | Maximum (200) | Medium (0.5–2.0%) |

The most consistent pattern: **low-volatility assets require the maximum available
threshold and window sizes just to minimise damage, but still underperform.** High-
velocity assets require large windows to avoid noise. Deep-crash assets require small
short windows for fast exit but high thresholds to filter recovery whipsaws.

Parameters are not transferable across assets. A parameter set optimal for META will
produce excessive trades on KO and miss NVDA's rally entirely.

---

## Strategy Logic

### Simple Moving Average (SMA)

$$\text{SMA}(t, w) = \frac{1}{w} \sum_{i=0}^{w-1} P_{t-i}$$

SMA weights all $w$ observations equally. It is computationally simple and robust to
short-term noise, but slower to respond to price changes. A new data point affects the
SMA for exactly $w$ days.

### Exponential Moving Average (EMA)

$$\text{EMA}(t) = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}(t-1), \quad \alpha = \frac{2}{w+1}$$

EMA assigns exponentially decaying weights to past prices. Recent observations have
greater influence than older ones. It responds faster to trend changes than SMA, but
is also more sensitive to short-term noise. Unlike SMA, every past observation has
non-zero weight.

### Crossover Signals

The strategy generates signals based on the **percentage gap** between short and long
moving averages:

$$g_t = \frac{\text{MA}_{\text{short}}(t) - \text{MA}_{\text{long}}(t)}{\text{MA}_{\text{long}}(t)}$$

**Golden cross (buy signal):** $g_{t-1} \leq \theta$ and $g_t > \theta$

**Death cross (sell signal):** $g_{t-1} \geq -\theta$ and $g_t < -\theta$

where $\theta \geq 0$ is the crossover threshold. At $\theta = 0$ this reduces to the
standard crossover. At $\theta > 0$, the moving averages must separate by more than
$\theta$ before a signal fires, filtering noise-driven crossovers.

A percentage gap is used rather than an absolute gap so that the threshold scales with
price level across multi-year backtests.

### Noise Filter Threshold

The threshold $\theta$ addresses a structural problem: on assets where the two moving
averages remain close together for extended periods (slow uptrends, low-volatility
stocks), the gap series $g_t$ oscillates around zero repeatedly, generating a high
volume of false signals. KO's 142-trade EMA run at θ=0% versus 11-trade SMA run at
θ=2.0% quantifies the cost of omitting this parameter.

The interaction between $\theta$ and window sizes is why all three parameters are
optimised jointly. The noise-filtering effect of $\theta$ depends on how volatile the
gap series is, which is itself determined by the window sizes.

### T+1 Settlement

```
Day T   — crossover detected on close → pending_order = 'buy'/'sell'
Day T+1 — pending order executes at day T+1 closing price
```

One day of execution lag — the minimum realistic delay for a daily strategy. The
practical effect is a small reduction in strategy return relative to same-day execution,
most visible during fast markets where prices gap overnight.

### Transaction Costs

$$\text{shares}_{\text{buy}} = \frac{\text{cash}}{\text{price}} \times (1 - f), \qquad
\text{cash}_{\text{sell}} = \text{shares} \times \text{price} \times (1 - f)$$

A complete round trip costs approximately $2f$ of position value. At the default rate
$f = 0.05\%$, this is 0.10% per round trip. The fee is applied inside `grid_search.py`,
so walk-forward optimisation penalises high-frequency strategies in both absolute return
and Sharpe, shifting optimal windows toward larger values versus a zero-fee run.

### Performance Metrics

**Strategy Return**

$$R = (C_{\text{final}} - 1) \times 100$$

**Buy and Hold Return**

$$R_{\text{bh}} = \left(\frac{P_{\text{last}}}{P_{\text{first}}} - 1\right) \times 100$$

**Max Drawdown**

$$\text{MDD} = \max_{t} \left( \frac{\text{peak}_t - V_t}{\text{peak}_t} \right)$$

**Sharpe Ratio (annualised)**

$$\text{Sharpe} = \frac{\mu_d - r_f / 252}{\sigma_d} \times \sqrt{252}$$

where $\mu_d$ is mean daily return, $\sigma_d$ is sample standard deviation, and $r_f$
is the average 3-month US Treasury bill yield (`^IRX`) over the test period. The
realised yield is used — not a fixed constant — because rates varied from near zero
(2020–2021) to above 5% (2023–2024).

---

## Parameter Optimisation

`grid_search.py` performs an exhaustive three-dimensional search:

$$s \in \{5, 10, \ldots, 55\}, \quad l \in \{20, 30, \ldots, 200\}, \quad \theta \in \{0,\, 0.002,\, 0.005,\, 0.01,\, 0.02\}$$

All combinations where $s \geq l$ are skipped. The objective function is the mean
out-of-sample Sharpe across all walk-forward windows. The three parameters are optimised
jointly because $\theta$'s effectiveness depends on the volatility of the gap series,
which is itself determined by $(s, l)$.

The heatmap marginalises over $\theta$ — each cell shows the best Sharpe across all
threshold values for that $(s, l)$ pair. The top-5 table shows the full $(s, l, \theta)$
combination for each ranked entry.

### Walk-Forward Validation

```
Window 1: train 2016–2017  →  test 2018
Window 2: train 2016–2018  →  test 2019
Window 3: train 2016–2019  →  test 2020
Window 4: train 2016–2020  →  test 2021
Window 5: train 2016–2021  →  test 2022
Window 6: train 2016–2022  →  test 2023
Window 7: train 2016–2023  →  test 2024
```

Each parameter combination is scored across test windows spanning the 2018 correction,
the 2020 COVID crash, the 2022 rate-hike bear market, and the 2023–2024 recovery.
The mean Sharpe across seven windows guards against parameter sets that fit one
particular market episode.

---

## Limitations

- **Execution price:** T+1 execution uses the following day's closing price. Actual
  fills would occur at the open, so prices may differ, particularly after overnight news.
- **Market impact:** large-order price impact is not modelled. Negligible for normalised
  single-asset positions in liquid equities, but significant at real capital sizes.
- **Single asset:** the system backtests one ticker at a time. Cross-asset correlation
  and portfolio-level risk management are not considered.
- **US-centric risk-free rate:** `^IRX` reflects US Treasury yields. For non-US assets
  a local equivalent should be substituted.
- **Trend-following structural bias:** the strategy is systematically disadvantaged on
  persistently trending assets and parabolic moves where lagging indicators cannot
  keep pace with price velocity.
- **Survivorship bias:** all seven stocks are current index constituents and known
  survivors. Companies that were delisted or significantly impaired during 2016–2026
  are not represented, which may overstate sector-level results.
- **Corporate actions:** spin-offs and special dividends (JNJ/Kenvue 2023) are not
  explicitly modelled. Yahoo Finance adjusted close accounts for these partially, but
  price discontinuities may generate spurious crossover signals — as observed in JNJ's
  strongly divergent WF Sharpe (1.68) versus full-dataset Sharpe (-0.09).
