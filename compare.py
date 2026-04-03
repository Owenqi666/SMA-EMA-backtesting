import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sma import load_prices, moving_average, backtest as sma_backtest, parse_date, get_risk_free_rate
from ema import exp_moving_average, backtest as ema_backtest


def main():
    print("SMA vs EMA Crossover Strategy Comparison")
    print("-----------------------------------------")

    #input ticker
    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

    # input dates
    start, start_dt = parse_date("Start date: ")
    end, end_dt = parse_date("End date: ")

    if end_dt <= start_dt:
        sys.exit(f"Error: start date ({start}) must be before end date ({end}).")

    #input windows
    try:
        short_w = int(input("Short window (e.g. 20): ").strip())
        long_w = int(input("Long window (e.g. 50): ").strip())
    except ValueError:
        sys.exit("Please enter a whole number.")

    if short_w <= 0 or long_w <= 0:
        sys.exit("Error: window sizes must be positive integers.")

    if short_w >= long_w:
        sys.exit(
            f"Error: short window ({short_w}) must be "
            f"less than long window ({long_w})."
        )

    # Download once, share between both strategies
    prices = load_prices(ticker, start, end)
    rf = get_risk_free_rate(start, end)

    # Run SMA backtest
    short_sma = moving_average(prices, short_w)
    long_sma = moving_average(prices, long_w)
    sma_result = sma_backtest(prices, short_sma, long_sma, rf)

    # Run EMA backtest
    short_ema = exp_moving_average(prices, short_w)
    long_ema = exp_moving_average(prices, long_w)
    ema_result = ema_backtest(prices, short_ema, long_ema, rf)

    # Print comparison table
    print(f"\nTicker: {ticker}  |  Short window: {short_w}  |  Long window: {long_w}")
    print()
    print(f"{'Metric':<25} {'SMA':>10} {'EMA':>10}")
    print("-" * 45)

    metrics = [
        ("Strategy Return (%)",   "strategy_return"),
        ("Buy & Hold Return (%)", "bh_return"),
        ("Max Drawdown (%)",      "max_dd"),
        ("Sharpe Ratio",          "sharpe"),
        ("Total Trades",          "trades"),
    ]

    for label, key in metrics:
        sma_val = sma_result[key]
        ema_val = ema_result[key]

        if key == "trades":
            print(f"{label:<25} {sma_val:>10} {ema_val:>10}")
        elif key == "max_dd":
            print(f"{label:<25} {'-'+f'{sma_val:.2f}':>10} {'-'+f'{ema_val:.2f}':>10}")
        else:
            print(f"{label:<25} {sma_val:>10.2f} {ema_val:>10.2f}")

    # Print winner for each metric
    print()
    print("Winner by metric:")
    print(f"  Strategy Return : {'EMA' if ema_result['strategy_return'] > sma_result['strategy_return'] else 'SMA'}")
    print(f"  Max Drawdown    : {'EMA' if ema_result['max_dd'] < sma_result['max_dd'] else 'SMA'}  (lower is better)")
    print(f"  Sharpe Ratio    : {'EMA' if ema_result['sharpe'] > sma_result['sharpe'] else 'SMA'}")
    print(f"  Total Trades    : {'EMA' if ema_result['trades'] < sma_result['trades'] else 'SMA'}  (fewer is cheaper)")

    plot_equity_comparison(prices, sma_result, ema_result, ticker, start, end, short_w, long_w)


def plot_equity_comparison(prices, sma_result, ema_result, ticker, start, end, short_w, long_w):
    """Side-by-side equity curves: SMA vs EMA, each vs buy-and-hold."""
    BG      = "#0f1117"
    PANEL   = "#1a202c"
    GRID    = "#2d3748"
    TEXT    = "#e2e8f0"
    MUTED   = "#718096"

    def build_bh(equity, offset, prices):
        """Build a buy-and-hold curve aligned to the equity curve."""
        n = len(equity)
        p0 = prices[offset]
        return [prices[offset + i] / p0 for i in range(n)]

    sma_equity = sma_result['equity']
    ema_equity = ema_result['equity']
    sma_bh = build_bh(sma_equity, sma_result['offset'], prices)
    ema_bh = build_bh(ema_equity, ema_result['offset'], prices)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"{ticker}  |  Equity Curve Comparison  |  {start} → {end}  "
                 f"|  Short: {short_w}  Long: {long_w}",
                 color=TEXT, fontsize=12, y=1.01)

    configs = [
        (axes[0], sma_equity, sma_bh, "#63b3ed", "SMA Strategy"),
        (axes[1], ema_equity, ema_bh, "#76e4f7", "EMA Strategy"),
    ]

    for ax, equity, bh, strat_color, title in configs:
        ax.set_facecolor(PANEL)
        x = list(range(len(equity)))
        ax.plot(x, equity, color=strat_color, linewidth=1.8, label=title)
        ax.plot(x, bh,     color="#f6ad55",   linewidth=1.4, linestyle="--",
                label="Buy & Hold", alpha=0.85)
        ax.axhline(1.0, color=GRID, linewidth=0.8, linestyle=":")

        final_strat = equity[-1]
        final_bh    = bh[-1]
        ax.annotate(f"{final_strat:.2f}×", xy=(len(equity)-1, final_strat),
                    color=strat_color, fontsize=8, va='bottom')
        ax.annotate(f"{final_bh:.2f}×",   xy=(len(bh)-1, final_bh),
                    color="#f6ad55", fontsize=8, va='top')

        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.set_xlabel("Trading Days", color=MUTED, fontsize=9)
        ax.set_ylabel("Portfolio Value (normalised)", color=MUTED, fontsize=9)
        ax.set_title(title, color=TEXT, fontsize=11, pad=8)
        ax.legend(facecolor="#0f1117", edgecolor=GRID, labelcolor=TEXT, fontsize=8)
        ax.grid(True, color=GRID, linewidth=0.5, linestyle="--", alpha=0.5)

    plt.tight_layout()
    os.makedirs("images", exist_ok=True)
    s = start[:10].replace("-", "_")
    e = end[:10].replace("-", "_")
    fname = f"images/{ticker}_{s}_{e}_compare.png"
    fig.savefig(fname, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"\n  [Chart saved] {fname}")


if __name__ == "__main__":
    main()
