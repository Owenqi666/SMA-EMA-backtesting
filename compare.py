import sys
from sma import load_prices, moving_average, backtest as sma_backtest
from ema import exp_moving_average, backtest as ema_backtest


def main():
    print("SMA vs EMA Crossover Strategy Comparison")
    print("-----------------------------------------")

    #input ticker
    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

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
    prices = load_prices(ticker, "2020-01-01", "2024-12-31")

    # Run SMA backtest
    short_sma = moving_average(prices, short_w)
    long_sma = moving_average(prices, long_w)
    sma_result = sma_backtest(prices, short_sma, long_sma)

    # Run EMA backtest
    short_ema = exp_moving_average(prices, short_w)
    long_ema = exp_moving_average(prices, long_w)
    ema_result = ema_backtest(prices, short_ema, long_ema)

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

        # trades is an integer, everything else is a float
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


if __name__ == "__main__":
    main()
