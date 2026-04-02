import sys
from sma import load_prices, moving_average, backtest as sma_backtest
from ema import exp_moving_average, backtest as ema_backtest


def grid_search(prices, strategy='SMA'):
    """
    Scan all valid (short_w, long_w) combinations and return the pair with the highest Sharpe ratio.
    strategy: 'SMA' or 'EMA'
    returns: (best_short, best_long), best_sharpe, all_results dict
    """
    best_sharpe = -999
    best_params = (0, 0)
    all_results = {}  # (short_w, long_w) → sharpe

    short_range = range(5, 60, 5)    # 5, 10, 15, ..., 55
    long_range  = range(20, 210, 10) # 20, 30, 40, ..., 200

    for short_w in short_range:
        for long_w in long_range:

            # Skip invalid combinations
            if short_w >= long_w:
                continue

            # Compute moving averages and run backtest
            if strategy == 'SMA':
                short_ma = moving_average(prices, short_w)
                long_ma  = moving_average(prices, long_w)
                result   = sma_backtest(prices, short_ma, long_ma)
            else:
                short_ma = exp_moving_average(prices, short_w)
                long_ma  = exp_moving_average(prices, long_w)
                result   = ema_backtest(prices, short_ma, long_ma)

            sharpe = result['sharpe']
            all_results[(short_w, long_w)] = sharpe

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (short_w, long_w)

    return best_params, best_sharpe, all_results


def evaluate_on_test(prices, params, strategy):
    """Run a single backtest on test data using the best params found in training."""
    short_w, long_w = params
    if strategy == 'SMA':
        short_ma = moving_average(prices, short_w)
        long_ma  = moving_average(prices, long_w)
        return sma_backtest(prices, short_ma, long_ma)
    else:
        short_ma = exp_moving_average(prices, short_w)
        long_ma  = exp_moving_average(prices, long_w)
        return ema_backtest(prices, short_ma, long_ma)


def print_top_results(all_results, strategy, n=5):
    """Print the top n parameter combinations by Sharpe ratio."""
    sorted_results = sorted(all_results.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop {n} {strategy} parameter combinations (train set):")
    print(f"  {'Short':>6} {'Long':>6} {'Sharpe':>8}")
    print("  " + "-" * 22)

    for (short_w, long_w), sharpe in sorted_results[:n]:
        print(f"  {short_w:>6} {long_w:>6} {sharpe:>8.2f}")


def main():
    print("SMA vs EMA Grid Search Optimisation")
    print("------------------------------------")

    #input ticker
    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

    # Download once, share between both strategies
    prices = load_prices(ticker, "2020-01-01", "2024-12-31")

    # Train/test split: 60% train, 40% test
    split = int(len(prices) * 0.6)
    train_prices = prices[:split]
    test_prices  = prices[split:]
    print(f"\nTrain: {split} days  |  Test: {len(test_prices)} days")

    # Run grid search on train set only
    print("\nOptimising SMA on train set...")
    sma_best_params, sma_train_sharpe, sma_results = grid_search(train_prices, strategy='SMA')

    print("Optimising EMA on train set...")
    ema_best_params, ema_train_sharpe, ema_results = grid_search(train_prices, strategy='EMA')

    # Evaluate best params on unseen test set
    sma_test_result = evaluate_on_test(test_prices, sma_best_params, 'SMA')
    ema_test_result = evaluate_on_test(test_prices, ema_best_params, 'EMA')

    # Print train vs test comparison
    print("\n" + "=" * 55)
    print(f"{'':5} {'Params':>12} {'Train Sharpe':>13} {'Test Sharpe':>12}")
    print("-" * 55)
    print(f"{'SMA':<5} {str(sma_best_params):>12} {sma_train_sharpe:>13.2f} {sma_test_result['sharpe']:>12.2f}")
    print(f"{'EMA':<5} {str(ema_best_params):>12} {ema_train_sharpe:>13.2f} {ema_test_result['sharpe']:>12.2f}")
    print("=" * 55)

    # Warn if train and test Sharpe differ a lot (sign of overfitting)
    for strategy, train_s, test_s in [
        ('SMA', sma_train_sharpe, sma_test_result['sharpe']),
        ('EMA', ema_train_sharpe, ema_test_result['sharpe']),
    ]:
        drop = train_s - test_s
        if drop > 0.5:
            print(f"Warning: {strategy} Sharpe dropped {drop:.2f} from train to test — possible overfitting.")

    # Print top 5 for each strategy
    print_top_results(sma_results, 'SMA', n=5)
    print_top_results(ema_results, 'EMA', n=5)

    # Overall winner by test Sharpe
    print()
    sma_test_sharpe = sma_test_result['sharpe']
    ema_test_sharpe = ema_test_result['sharpe']
    if sma_test_sharpe > ema_test_sharpe:
        print(f"Overall winner (by test Sharpe): SMA  ({sma_test_sharpe:.2f} vs {ema_test_sharpe:.2f})")
    elif ema_test_sharpe > sma_test_sharpe:
        print(f"Overall winner (by test Sharpe): EMA  ({ema_test_sharpe:.2f} vs {sma_test_sharpe:.2f})")
    else:
        print("Draw: both strategies achieved the same test Sharpe ratio.")


if __name__ == "__main__":
    main()
