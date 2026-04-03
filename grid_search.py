import sys
from sma import load_prices, moving_average, backtest as sma_backtest, parse_date, get_risk_free_rate
from ema import exp_moving_average, backtest as ema_backtest


def run_backtest(prices, short_w, long_w, rf, strategy):
    if strategy == 'SMA':
        short_ma = moving_average(prices, short_w)
        long_ma  = moving_average(prices, long_w)
        return sma_backtest(prices, short_ma, long_ma, rf)
    else:
        short_ma = exp_moving_average(prices, short_w)
        long_ma  = exp_moving_average(prices, long_w)
        return ema_backtest(prices, short_ma, long_ma, rf)


def walk_forward(prices, rf, strategy='SMA', test_days=252, min_train_days=504):
    n = len(prices)

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
                if long_w >= train_end:
                    continue
                result = run_backtest(prices[train_end:test_end], short_w, long_w, rf, strategy)
                test_sharpes.append(result['sharpe'])

            if not test_sharpes:
                continue

            mean_sharpe = sum(test_sharpes) / len(test_sharpes)
            all_results[(short_w, long_w)] = mean_sharpe

            if mean_sharpe > best_mean_sharpe:
                best_mean_sharpe = mean_sharpe
                best_params      = (short_w, long_w)

    return best_params, best_mean_sharpe, all_results


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

    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

    start, start_dt = parse_date("Start date: ")
    end, end_dt     = parse_date("End date: ")

    if end_dt <= start_dt:
        sys.exit(f"Error: start date ({start}) must be before end date ({end}).")

    prices = load_prices(ticker, start, end)
    rf     = get_risk_free_rate(start, end)

    print(f"\nTotal data: {len(prices)} trading days")

    print("\nOptimising SMA via walk-forward...")
    sma_best_params, sma_best_sharpe, sma_results = walk_forward(prices, rf, strategy='SMA')

    print("\nOptimising EMA via walk-forward...")
    ema_best_params, ema_best_sharpe, ema_results = walk_forward(prices, rf, strategy='EMA')

    sma_final = run_backtest(prices, *sma_best_params, rf, 'SMA')
    ema_final = run_backtest(prices, *ema_best_params, rf, 'EMA')

    print("\n" + "=" * 62)
    print(f"{'':5} {'Params':>12} {'Mean Test Sharpe':>16} {'Full Sharpe':>12}")
    print("-" * 62)
    print(f"{'SMA':<5} {str(sma_best_params):>12} {sma_best_sharpe:>16.2f} {sma_final['sharpe']:>12.2f}")
    print(f"{'EMA':<5} {str(ema_best_params):>12} {ema_best_sharpe:>16.2f} {ema_final['sharpe']:>12.2f}")
    print("=" * 62)

    print_top_results(sma_results, 'SMA', n=5)
    print_top_results(ema_results, 'EMA', n=5)

    print()
    if sma_best_sharpe > ema_best_sharpe:
        print(f"Overall winner (by mean test Sharpe): SMA  ({sma_best_sharpe:.2f} vs {ema_best_sharpe:.2f})")
    elif ema_best_sharpe > sma_best_sharpe:
        print(f"Overall winner (by mean test Sharpe): EMA  ({ema_best_sharpe:.2f} vs {sma_best_sharpe:.2f})")
    else:
        print("Draw: both strategies achieved the same mean test Sharpe.")


if __name__ == "__main__":
    main()
