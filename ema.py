import sys
import csv
import math
import yfinance as yf

def main():
    print("Exponential Moving Average Crossover Backtest")
    print("----------------------------------------------")

    #input ticker
    ticker = input("Ticker (e.g. AAPL): ").strip().upper()
    if not ticker:
        sys.exit("Error: ticker cannot be empty.")

    #input windows
    try:
        short_w = int(input("Short EMA window (e.g. 20): ").strip())
        long_w = int(input("Long EMA window (e.g. 50): ").strip())
    except ValueError:
        sys.exit("Please enter a whole number.")

    if short_w <= 0 or long_w <= 0:
        sys.exit("Error: window sizes must be positive integers.")

    if short_w >= long_w:
        sys.exit(
            f"Error: short window ({short_w}) must be "
            f"less than long window ({long_w})."
        )

    #Download prices and run backtest
    prices = load_prices(ticker, "2020-01-01", "2024-12-31")
    short_ema = exp_moving_average(prices, short_w)
    long_ema = exp_moving_average(prices, long_w)
    result = backtest(prices, short_ema, long_ema)

    print(f"\nTicker: {ticker}")
    print(f"Strategy Return: {result['strategy_return']:+.2f}%")
    print(f"Buy & Hold Return: {result['bh_return']:+.2f}%")
    print(f"Max Drawdown: -{result['max_dd']:.2f}%")
    print(f"Sharpe Ratio: {result['sharpe']:.2f}")
    print(f"Total Trades: {result['trades']}")


# Download daily OHLCV data
def load_prices(ticker, start, end):
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        raise ValueError(
            f"No data found for '{ticker}'. "
            "Check the ticker symbol and your internet connection."
        )

    prices = data["Close"].squeeze().dropna().tolist()
    if len(prices) < 2:
        raise ValueError(
            f"Only {len(prices)} trading day(s) found for '{ticker}' "
            f"between {start} and {end}. Need at least 2."
        )

    print(f"Loaded {len(prices)} trading days for {ticker} ({start} to {end}).")
    return prices


def exp_moving_average(prices, window):

    if window < 1 or window > len(prices):
        raise ValueError(
            f"Window {window} is invalid: must be between 1 and {len(prices)}."
        )

    alpha = 2 / (window + 1)

    ema = [prices[0]]
    for i in range(1, len(prices)):
        ema.append(alpha * prices[i] + (1 - alpha) * ema[-1])
    return ema


def backtest(prices, short_ema, long_ema):

    #EMA is the same length as prices, so no trimming needed
    offset = 0

    #Initialize account: normalized starting capital of 1.0, no position
    position = 0
    cash = 1.0
    shares = 0.0
    trades = 0
    equity = []

    for i in range(len(long_ema)):
        price = prices[offset + i]

        if i > 0:
            previous_short = short_ema[i - 1]
            previous_long = long_ema[i - 1]
            current_short = short_ema[i]
            current_long = long_ema[i]

            # Golden cross
            if previous_short <= previous_long and current_short > current_long and position == 0:
                shares = cash / price
                cash = 0
                position = 1
                trades += 1

            # Death cross
            elif previous_short >= previous_long and current_short < current_long and position == 1:
                cash = shares * price
                shares = 0
                position = 0
                trades += 1

        #Record today's total portfolio value
        current_value = cash + shares * price
        equity.append(current_value)

    # If still holding at end of backtest, close position at last price
    if position == 1:
        cash = shares * prices[-1]

    strategy_return = (cash - 1.0) * 100
    bh_return = (prices[-1] / prices[offset] - 1) * 100
    max_dd = max_drawdown(equity) * 100
    sharpe = sharpe_ratio(equity)

    return {
        "strategy_return": strategy_return,
        "bh_return": bh_return,
        "max_dd": max_dd,
        "sharpe": sharpe,
        "trades": trades,
        "equity": equity,
        "offset": offset,
    }


def max_drawdown(equity):
    peak = equity[0]
    max_dd = 0.0

    for val in equity:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd

    return max_dd


def sharpe_ratio(equity, risk_free=0.05):

    if len(equity) < 2:
        return 0.0

    daily_returns = [
        (equity[i] - equity[i - 1]) / equity[i - 1]
        for i in range(1, len(equity))
    ]

    rf_daily = risk_free / 252
    avg = sum(daily_returns) / len(daily_returns)
    excess = avg - rf_daily

    variance = sum((r - avg) ** 2 for r in daily_returns) / len(daily_returns)
    std = math.sqrt(variance)

    if std == 0:
        return 0.0

    return (excess / std) * math.sqrt(252)


if __name__ == "__main__":
    main()
