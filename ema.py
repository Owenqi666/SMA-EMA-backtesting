import sys
import math
import os
import yfinance as yf
from dateutil import parser as dateparser
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    print("Exponential Moving Average Crossover Backtest")
    print("----------------------------------------------")

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
    prices = load_prices(ticker, start, end)
    short_ema = exp_moving_average(prices, short_w)
    long_ema = exp_moving_average(prices, long_w)
    rf = get_risk_free_rate(start, end)
    result = backtest(prices, short_ema, long_ema, rf)

    print(f"\nTicker: {ticker}")
    print(f"Strategy Return: {result['strategy_return']:+.2f}%")
    print(f"Buy & Hold Return: {result['bh_return']:+.2f}%")
    print(f"Max Drawdown: -{result['max_dd']:.2f}%")
    print(f"Sharpe Ratio: {result['sharpe']:.2f}")
    print(f"Total Trades: {result['trades']}")

    plot_ema(prices, short_ema, long_ema, result['signals'], ticker, start, end, short_w, long_w)

def parse_date(prompt):
    raw = input(prompt).strip()
    dt = dateparser.parse(raw)
    if dt is None:
        sys.exit(f"Error: cannot parse date '{raw}'. Try YYYY-MM-DD (e.g. 2020-01-01).")
    date_str = dt.strftime('%Y-%m-%d')
    print(f"  -> Parsed as {date_str}")
    return date_str, dt

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

def get_risk_free_rate(start, end):
    try:
        irx = yf.download("^IRX", start=start, end=end, progress=False, auto_adjust=True)
        if irx.empty:
            sys.exit("Error: no ^IRX data returned. Check your date range and internet connection.")
        rate = float(irx["Close"].squeeze().dropna().mean()) / 100
        print(f"  [Risk-free] Average 3-month T-bill yield ({start} to {end}): {rate:.2%}")
        return rate
    except Exception as e:
        sys.exit(f"Error: failed to download ^IRX ({e}).")

def backtest(prices, short_ema, long_ema, rf):

    #EMA is the same length as prices, so no trimming needed
    offset = 0

    #Initialize account: normalized starting capital of 1.0, no position
    position = 0
    cash = 1.0
    shares = 0.0
    trades = 0
    equity = []
    signals = []  # list of (index, 'buy'|'sell')

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
                signals.append((offset + i, 'buy'))

            # Death cross
            elif previous_short >= previous_long and current_short < current_long and position == 1:
                cash = shares * price
                shares = 0
                position = 0
                trades += 1
                signals.append((offset + i, 'sell'))

        #Record today's total portfolio value
        current_value = cash + shares * price
        equity.append(current_value)

    # If still holding at end of backtest, close position at last price
    if position == 1:
        cash = shares * prices[-1]

    strategy_return = (cash - 1.0) * 100
    bh_return = (prices[-1] / prices[offset] - 1) * 100
    max_dd = max_drawdown(equity) * 100
    sharpe = sharpe_ratio(equity, rf)

    return {
        "strategy_return": strategy_return,
        "bh_return": bh_return,
        "max_dd": max_dd,
        "sharpe": sharpe,
        "trades": trades,
        "equity": equity,
        "offset": offset,
        "signals": signals,
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

def sharpe_ratio(equity, rf):
    if len(equity) < 2:
        return 0.0
    daily_returns = [
        (equity[i] - equity[i - 1]) / equity[i - 1]
        for i in range(1, len(equity))
    ]
    rf_daily = rf / 252
    avg = sum(daily_returns) / len(daily_returns)
    excess = avg - rf_daily
    variance = sum((r - avg) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return (excess / std) * math.sqrt(252)

def plot_ema(prices, short_ema, long_ema, signals, ticker, start, end, short_w, long_w):
    """Plot price, short EMA, long EMA with buy/sell arrows. Saves to images/."""
    n = len(prices)
    x = list(range(n))

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    ax.plot(x, prices,     color="#a0aec0", linewidth=1.0, label="Close Price", alpha=0.8)
    ax.plot(x, short_ema,  color="#76e4f7", linewidth=1.4, label=f"EMA({short_w})")
    ax.plot(x, long_ema,   color="#f6ad55", linewidth=1.4, label=f"EMA({long_w})")

    for idx, kind in signals:
        price_at = prices[idx]
        if kind == 'buy':
            ax.plot(idx, price_at * 0.975, marker='^', color='#68d391', markersize=9, zorder=5)
        else:
            ax.plot(idx, price_at * 1.025, marker='v', color='#fc8181', markersize=9, zorder=5)

    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3748")
    ax.tick_params(colors="#718096")
    ax.set_xlabel("Trading Days", color="#718096")
    ax.set_ylabel("Price (USD)", color="#718096")
    ax.set_title(f"{ticker}  |  EMA Crossover  |  {start} → {end}",
                 color="#e2e8f0", fontsize=13, pad=12)
    ax.legend(facecolor="#1a202c", edgecolor="#2d3748", labelcolor="#e2e8f0", fontsize=9)
    ax.grid(True, color="#2d3748", linewidth=0.5, linestyle="--", alpha=0.6)

    _save_figure(fig, ticker, start, end, "ema")


def _save_figure(fig, ticker, start, end, label):
    os.makedirs("images", exist_ok=True)
    s = start[:10].replace("-", "_")
    e = end[:10].replace("-", "_")
    fname = f"images/{ticker}_{s}_{e}_{label}.png"
    fig.savefig(fname, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [Chart saved] {fname}")


if __name__ == "__main__":
    main()