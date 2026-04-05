import sys
sys.path.insert(0, '/home/claude')

from sma import load_prices, moving_average, backtest as sma_backtest, get_risk_free_rate
from ema import exp_moving_average, backtest as ema_backtest
from grid_search import walk_forward, run_backtest

START = "2016-01-01"
END   = "2026-01-01"
FEE   = 0.0005

STOCKS = [
    ("AAPL", "Technology"),
    ("NVDA", "Technology"),
    ("META", "Technology"),
    ("XOM",  "Energy"),
    ("KO",   "Consumer Staples"),
    ("JPM",  "Financials"),
    ("JNJ",  "Healthcare"),
]

results = {}

for ticker, sector in STOCKS:
    print(f"\n{'='*50}")
    print(f"  {ticker} ({sector})")
    print(f"{'='*50}")

    prices = load_prices(ticker, START, END)
    rf     = get_risk_free_rate(START, END)

    print("  Running SMA walk-forward...")
    sma_params, sma_wf_sharpe, sma_all = walk_forward(prices, rf, strategy='SMA', fee_rate=FEE)
    print("  Running EMA walk-forward...")
    ema_params, ema_wf_sharpe, ema_all = walk_forward(prices, rf, strategy='EMA', fee_rate=FEE)

    sma_s, sma_l, sma_theta = sma_params
    ema_s, ema_l, ema_theta = ema_params

    sma_full = run_backtest(prices, sma_s, sma_l, rf, 'SMA', FEE, sma_theta)
    ema_full = run_backtest(prices, ema_s, ema_l, rf, 'EMA', FEE, ema_theta)

    bh = (prices[-1] / prices[0] - 1) * 100

    results[ticker] = {
        "sector": sector,
        "bh_return": bh,
        "sma": {
            "params": sma_params,
            "wf_sharpe": sma_wf_sharpe,
            "strategy_return": sma_full["strategy_return"],
            "max_dd": sma_full["max_dd"],
            "sharpe": sma_full["sharpe"],
            "trades": sma_full["trades"],
        },
        "ema": {
            "params": ema_params,
            "wf_sharpe": ema_wf_sharpe,
            "strategy_return": ema_full["strategy_return"],
            "max_dd": ema_full["max_dd"],
            "sharpe": ema_full["sharpe"],
            "trades": ema_full["trades"],
        },
    }

    print(f"\n  B&H Return: {bh:.1f}%")
    print(f"  SMA best params: s={sma_s}, l={sma_l}, θ={sma_theta:.3%}  |  WF Sharpe: {sma_wf_sharpe:.2f}  |  Full Return: {sma_full['strategy_return']:.1f}%  |  Sharpe: {sma_full['sharpe']:.2f}  |  Trades: {sma_full['trades']}")
    print(f"  EMA best params: s={ema_s}, l={ema_l}, θ={ema_theta:.3%}  |  WF Sharpe: {ema_wf_sharpe:.2f}  |  Full Return: {ema_full['strategy_return']:.1f}%  |  Sharpe: {ema_full['sharpe']:.2f}  |  Trades: {ema_full['trades']}")

print("\n\nDONE")
import json
with open('/home/claude/batch_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Results saved to batch_results.json")
