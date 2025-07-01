import argparse
import os
from core.data_loader import fetch_closed_markets, upsert_prices
from core.simulator import run_all
from core.metrics import update_stats

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=90)
parser.add_argument("--themes", nargs="+", default=["WX"])
parser.add_argument("--strategy", default=None)
args = parser.parse_args()

os.makedirs("results", exist_ok=True)

for theme in args.themes:
    rows = fetch_closed_markets(theme, args.days)
    upsert_prices(rows)

run_all(selected_strategy=args.strategy)

stats = update_stats()
for name, ntrades, total_pnl, win_rate, p_val, sharpe, ev in stats:
    sign = "+" if total_pnl >= 0 else "-"
    print(
        f"{name:15s} | Trades: {ntrades:3d} | Total P/L: {sign}${abs(total_pnl):.2f} | Win: {win_rate*100:4.0f}% | p-val: {p_val:.2f} | Sharpe: {sharpe:.2f} | EV: ${ev:.2f}"
    )
