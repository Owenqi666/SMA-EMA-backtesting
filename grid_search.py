import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sma import load_prices, moving_average, backtest as sma_backtest, parse_date, get_risk_free_rate
from ema import exp_moving_average, backtest as ema_backtest


# Run a single backtest for a given strategy and return the result dict
def run_backtest(prices, short_w, long_w, rf, strategy, fee_rate=0.0005):
    if strategy == 'SMA':
        short_ma = moving_average(prices, short_w)
        long_ma  = moving_average(prices, long_w)
        return sma_backtest(prices, short_ma, long_ma, rf, fee_rate)
    else:
        short_ma = exp_moving_average(prices, short_w)
        long_ma  = exp_moving_average(prices, long_w)
        return ema_backtest(prices, short_ma, long_ma, rf, fee_rate)


# Scan all valid (short_w, long_w) combinations using walk-forward validation
# Each pair is scored by mean out-of-sample Sharpe across all windows
def walk_forward(prices, rf, strategy='SMA', fee_rate=0.0005, test_days=252, min_train_days=504):
    n = len(prices)

    # Build list of (train_end, test_end) index pairs
    windows = []
    train_end = min_train_days
    while train_end + test_days <= n:
        windows.append((train_end, train_end + test_days))
        train_end += test_days

    if not windows:
        sys.exit(
            f"Error: not enough data for walk-forward validation. "
            f"Need at least {min_train_days + test_days} days, got {n}."
        )

    print(f"  Walk-forward: {len(windows)} windows, "
          f"test window = {test_days} days, "
          f"min train = {min_train_days} days")

    short_range = range(5, 60, 5)
    long_range  = range(20, 210, 10)

    best_mean_sharpe = -999
    best_params      = (0, 0)
    all_results      = {}

    for short_w in short_range:
        for long_w in long_range:
            if short_w >= long_w:
                continue

            test_sharpes = []
            for train_end, test_end in windows:
                # Skip window if train data too short for the long window
                if long_w >= train_end:
                    continue
                result = run_backtest(prices[train_end:test_end], short_w, long_w, rf, strategy, fee_rate)
                test_sharpes.append(result['sharpe'])

            if not test_sharpes:
                continue

            mean_sharpe = sum(test_sharpes) / len(test_sharpes)
            all_results[(short_w, long_w)] = mean_sharpe

            if mean_sharpe > best_mean_sharpe:
                best_mean_sharpe = mean_sharpe
                best_params      = (short_w, long_w)

    return best_params, best_mean_sharpe, all_results


# Print the top n parameter combinations ranked by mean test Sharpe
def print_top_results(all_results, strategy, n=5):
    sorted_results = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    print(f"\nTop {n} {strategy} parameter combinations (mean test Sharpe):")
    print(f"  {'Short':>6} {'Long':>6} {'Mean Sharpe':>12}")
    print("  " + "-" * 26)
    for (short_w, long_w), sharpe in sorted_results[:n]:
        print(f"  {short_w:>6} {long_w:>6} {sharpe:>12.2f}")


def main():
    print("SMA vs EMA Walk-Forward Grid Search")
    print("------------------------------------")

    #input ticker
    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

    # input dates
    start, start_dt = parse_date("Start date: ")
    end, end_dt     = parse_date("End date: ")

    if end_dt <= start_dt:
        sys.exit(f"Error: start date ({start}) must be before end date ({end}).")

    # input fee rate
    try:
        fee_input = input("Fee rate per trade, one-way (e.g. 0.0005 for 0.05%, press Enter for default): ").strip()
        fee_rate = float(fee_input) if fee_input else 0.0005
    except ValueError:
        sys.exit("Please enter a valid number for fee rate (e.g. 0.0005).")

    if fee_rate < 0:
        sys.exit("Error: fee rate cannot be negative.")

    # Download prices and risk-free rate
    prices = load_prices(ticker, start, end)
    rf     = get_risk_free_rate(start, end)

    print(f"\nTotal data: {len(prices)} trading days")
    print(f"Fee rate (one-way): {fee_rate:.4%}")

    # Run walk-forward grid search for both strategies
    print("\nOptimising SMA via walk-forward...")
    sma_best_params, sma_best_sharpe, sma_results = walk_forward(prices, rf, strategy='SMA', fee_rate=fee_rate)

    print("\nOptimising EMA via walk-forward...")
    ema_best_params, ema_best_sharpe, ema_results = walk_forward(prices, rf, strategy='EMA', fee_rate=fee_rate)

    # Evaluate best params on full dataset
    sma_final = run_backtest(prices, *sma_best_params, rf, 'SMA', fee_rate)
    ema_final = run_backtest(prices, *ema_best_params, rf, 'EMA', fee_rate)

    # Print summary table
    print("\n" + "=" * 62)
    print(f"{'':5} {'Params':>12} {'Mean Test Sharpe':>16} {'Full Sharpe':>12}")
    print("-" * 62)
    print(f"{'SMA':<5} {str(sma_best_params):>12} {sma_best_sharpe:>16.2f} {sma_final['sharpe']:>12.2f}")
    print(f"{'EMA':<5} {str(ema_best_params):>12} {ema_best_sharpe:>16.2f} {ema_final['sharpe']:>12.2f}")
    print("=" * 62)

    print_top_results(sma_results, 'SMA', n=5)
    print_top_results(ema_results, 'EMA', n=5)

    # Overall winner by mean test Sharpe
    print()
    if sma_best_sharpe > ema_best_sharpe:
        print(f"Overall winner (by mean test Sharpe): SMA  ({sma_best_sharpe:.2f} vs {ema_best_sharpe:.2f})")
    elif ema_best_sharpe > sma_best_sharpe:
        print(f"Overall winner (by mean test Sharpe): EMA  ({ema_best_sharpe:.2f} vs {sma_best_sharpe:.2f})")
    else:
        print("Draw: both strategies achieved the same mean test Sharpe.")

    plot_heatmaps(sma_results, ema_results, ticker, start, end)


def plot_heatmaps(sma_results, ema_results, ticker, start, end):
    """Plot side-by-side heatmaps of mean test Sharpe for SMA and EMA."""
    BG   = "#0f1117"
    TEXT = "#e2e8f0"
    MUTED = "#718096"

    short_range = sorted(set(k[0] for k in sma_results))
    long_range  = sorted(set(k[1] for k in sma_results))

    def build_matrix(results, short_range, long_range):
        mat = np.full((len(short_range), len(long_range)), np.nan)
        s_idx = {v: i for i, v in enumerate(short_range)}
        l_idx = {v: i for i, v in enumerate(long_range)}
        for (s, l), sharpe in results.items():
            mat[s_idx[s], l_idx[l]] = sharpe
        return mat

    sma_mat = build_matrix(sma_results, short_range, long_range)
    ema_mat = build_matrix(ema_results, short_range, long_range)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"{ticker}  |  Walk-Forward Mean Test Sharpe  |  {start} → {end}",
                 color=TEXT, fontsize=13, y=1.01)

    for ax, mat, title in [
        (axes[0], sma_mat, "SMA"),
        (axes[1], ema_mat, "EMA"),
    ]:
        ax.set_facecolor(BG)

        # Find global vmin/vmax ignoring NaN
        vmin = np.nanmin(mat)
        vmax = np.nanmax(mat)

        im = ax.imshow(mat, aspect='auto', origin='lower',
                       cmap='RdYlGn', vmin=vmin, vmax=vmax)

        # Mark best cell
        best_idx = np.unravel_index(np.nanargmax(mat), mat.shape)
        ax.plot(best_idx[1], best_idx[0], marker='*', color='white',
                markersize=14, zorder=5,
                label=f"Best: short={short_range[best_idx[0]]}, long={long_range[best_idx[1]]} "
                      f"(Sharpe={mat[best_idx]:.2f})")

        ax.set_xticks(range(len(long_range)))
        ax.set_xticklabels(long_range, rotation=45, ha='right', fontsize=7, color=MUTED)
        ax.set_yticks(range(len(short_range)))
        ax.set_yticklabels(short_range, fontsize=7, color=MUTED)
        ax.set_xlabel("Long Window", color=MUTED, fontsize=10)
        ax.set_ylabel("Short Window", color=MUTED, fontsize=10)
        ax.set_title(f"{title} — Mean Test Sharpe", color=TEXT, fontsize=11, pad=10)

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.yaxis.set_tick_params(color=MUTED, labelcolor=MUTED)

        ax.legend(loc='upper right', facecolor="#1a202c", edgecolor="#2d3748",
                  labelcolor=TEXT, fontsize=7)

        for spine in ax.spines.values():
            spine.set_edgecolor("#2d3748")
        ax.tick_params(colors=MUTED)

    plt.tight_layout()
    os.makedirs("images", exist_ok=True)
    s = start[:10].replace("-", "_")
    e = end[:10].replace("-", "_")
    fname = f"images/{ticker}_{s}_{e}_grid_search.png"
    fig.savefig(fname, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"\n  [Chart saved] {fname}")


if __name__ == "__main__":
    main()
