import sys
import math
import os
import yfinance as yf
from dateutil import parser as dateparser
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def main():
    print("Simple Moving Average Crossover Backtest")
    print("------------------------------------------")

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
        short_w = int(input("Short MA window (e.g. 20): ").strip())
        long_w = int(input("Long MA window (e.g. 50): ").strip())
    except ValueError:
        sys.exit("Please enter a whole number")

    if short_w <= 0 or long_w <= 0:
        sys.exit("Error: window sizes must be positive integers.")

    if short_w >= long_w:
        sys.exit(
            f"Error: short window ({short_w}) must be "
            f"less than long window ({long_w})."
        )

    # input fee rate
    try:
        fee_input = input("Fee rate per trade, one-way (e.g. 0.0005 for 0.05%, press Enter for default): ").strip()
        fee_rate = float(fee_input) if fee_input else 0.0005
    except ValueError:
        sys.exit("Please enter a valid number for fee rate (e.g. 0.0005).")

    if fee_rate < 0:
        sys.exit("Error: fee rate cannot be negative.")

    # input crossover threshold
    try:
        threshold_input = input("Crossover threshold (e.g. 0.005 for 0.5%, press Enter for default 0): ").strip()
        threshold = float(threshold_input) if threshold_input else 0.0
    except ValueError:
        sys.exit("Please enter a valid number for threshold (e.g. 0.005).")

    if threshold < 0:
        sys.exit("Error: threshold cannot be negative.")

    #Download prices and run backtest
    prices = load_prices(ticker, start, end)
    short_ma = moving_average(prices, short_w)
    long_ma = moving_average(prices, long_w)
    rf = get_risk_free_rate(start, end)
    result = backtest(prices, short_ma, long_ma, rf, fee_rate, threshold)

    print(f"\nTicker: {ticker}")
    print(f"Fee Rate (one-way): {fee_rate:.4%}")
    print(f"Crossover Threshold: {threshold:.4%}")
    print(f"Strategy Return: {result['strategy_return']:+.2f}%")
    print(f"Buy & Hold Return: {result['bh_return']:+.2f}%")
    print(f"Max Drawdown: -{result['max_dd']:.2f}%")
    print(f"Sharpe Ratio: {result['sharpe']:.2f}")
    print(f"Total Trades: {result['trades']}")
    print(f"Total Fee Cost: -{result['total_fee_cost']:.4f}  ({result['total_fee_cost'] * 100:.4f}% of starting capital)")

    plot_sma(prices, short_ma, long_ma, result['signals'], ticker, start, end, short_w, long_w)

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

def moving_average(prices, window):
    if window < 1 or window > len(prices):
        raise ValueError(
            f"Window {window} is invalid: must be between 1 and {len(prices)}."
        )
    return [
        sum(prices[i - window:i]) / window
        for i in range(window, len(prices) + 1)
    ]

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

def backtest(prices, short_ma, long_ma, rf, fee_rate=0.0005, threshold=0.0):
    # Trim the front of short_ma so both series are aligned to the same dates
    offset = len(prices) - len(long_ma)
    short_ma = short_ma[len(short_ma) - len(long_ma):]

    # Initialize account: normalized starting capital of 1.0, no position
    position = 0
    cash = 1.0
    shares = 0.0
    trades = 0
    total_fee_cost = 0.0
    equity = []
    signals = []  # list of (index, 'buy'|'sell')
    pending_order = None

    for i in range(len(long_ma)):
        price = prices[offset + i]

        # Step 1: Execute pending order from previous day (T+1 settlement)
        if pending_order == 'buy' and position == 0:
            shares = cash / price
            shares *= (1 - fee_rate)          # buy-side fee: fewer shares received
            fee_paid = cash * fee_rate
            total_fee_cost += fee_paid
            cash = 0
            position = 1
            trades += 1
            signals.append((offset + i, 'buy'))
            pending_order = None

        elif pending_order == 'sell' and position == 1:
            cash = shares * price
            cash *= (1 - fee_rate)            # sell-side fee: less cash received
            fee_paid = shares * price * fee_rate
            total_fee_cost += fee_paid
            shares = 0
            position = 0
            trades += 1
            signals.append((offset + i, 'sell'))
            pending_order = None

        # Step 2: Detect today's crossover signal, queue for next day
        if i > 0:
            current_short  = short_ma[i]
            current_long   = long_ma[i]
            previous_short = short_ma[i - 1]
            previous_long  = long_ma[i - 1]

            # Compute the percentage gap between short and long MA
            gap          = (current_short  - current_long)  / current_long
            previous_gap = (previous_short - previous_long) / previous_long

            # Golden cross — short MA crosses above long MA by more than threshold
            if previous_gap <= threshold and gap > threshold and position == 0:
                pending_order = 'buy'

            # Death cross — short MA crosses below long MA by more than threshold
            elif previous_gap >= -threshold and gap < -threshold and position == 1:
                pending_order = 'sell'

        # Step 3: Record today's total portfolio value (cash + market value of shares)
        current_value = cash + shares * price
        equity.append(current_value)

    # If still holding at end of backtest, close position at last price
    if position == 1:
        cash = shares * prices[-1]
        cash *= (1 - fee_rate)
        total_fee_cost += shares * prices[-1] * fee_rate

    # Compute performance metrics
    strategy_return = (cash - 1.0) * 100
    bh_return = (prices[-1] / prices[offset] - 1) * 100
    max_dd = max_drawdown(equity) * 100
    sharpe = sharpe_ratio(equity, rf)

    return {
        "strategy_return": strategy_return,
        "bh_return":       bh_return,
        "max_dd":          max_dd,
        "sharpe":          sharpe,
        "trades":          trades,
        "total_fee_cost":  total_fee_cost,
        "signals":         signals,
        "equity":          equity,
        "offset":          offset,
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

def plot_sma(prices, short_ma, long_ma, signals, ticker, start, end, short_w, long_w):
    """Plot price, short SMA, long SMA with buy/sell arrows. Saves to images/."""
    import numpy as np

    n = len(prices)
    # short_ma and long_ma may differ in length; align to price indices
    short_offset = n - len(short_ma)
    long_offset  = n - len(long_ma)

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    x_price = list(range(n))
    x_short = list(range(short_offset, n))
    x_long  = list(range(long_offset, n))

    ax.plot(x_price, prices,    color="#a0aec0", linewidth=1.0, label="Close Price", alpha=0.8)
    ax.plot(x_short, short_ma,  color="#63b3ed", linewidth=1.4, label=f"SMA({short_w})")
    ax.plot(x_long,  long_ma,   color="#f6ad55", linewidth=1.4, label=f"SMA({long_w})")

    # Mark buy/sell signals
    for idx, kind in signals:
        price_at = prices[idx]
        if kind == 'buy':
            ax.annotate('', xy=(idx, price_at * 0.975), xytext=(idx, price_at * 0.945),
                        arrowprops=dict(arrowstyle='->', color='#68d391', lw=2))
            ax.plot(idx, price_at * 0.975, marker='^', color='#68d391', markersize=8, zorder=5)
        else:
            ax.annotate('', xy=(idx, price_at * 1.025), xytext=(idx, price_at * 1.055),
                        arrowprops=dict(arrowstyle='->', color='#fc8181', lw=2))
            ax.plot(idx, price_at * 1.025, marker='v', color='#fc8181', markersize=8, zorder=5)

    # Style
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3748")
    ax.tick_params(colors="#718096")
    ax.yaxis.label.set_color("#718096")
    ax.xaxis.label.set_color("#718096")
    ax.set_xlabel("Trading Days", color="#718096")
    ax.set_ylabel("Price (USD)", color="#718096")
    ax.set_title(f"{ticker}  |  SMA Crossover  |  {start} → {end}",
                 color="#e2e8f0", fontsize=13, pad=12)
    ax.legend(facecolor="#1a202c", edgecolor="#2d3748", labelcolor="#e2e8f0", fontsize=9)
    ax.grid(True, color="#2d3748", linewidth=0.5, linestyle="--", alpha=0.6)

    _save_figure(fig, ticker, start, end, "sma")


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
