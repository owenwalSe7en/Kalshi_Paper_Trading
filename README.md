# Kalshi Paper Trader

A Python-based sandbox for simulating simple Kalshi trading strategies using historical data. It helps you write and test rule-based strategies (like weather or music predictions) with no risk, storing results in SQLite and computing win rate, Sharpe ratio, and p-values to track your model's performance.

A tiny, beginner‑friendly sandbox for testing simple trading ideas on **Kalshi** markets using only historical daily close data.
The project:

* **Scrapes** closed Kalshi markets that match the themes you pick (`WX` for weather, `MUSC` for top‑songs charts).
* **Stores** one row per market in a local SQLite file so there’s no server setup.
* Lets you write a **Strategy** class with a single `decide()` method.
* **Back‑tests** every strategy, logs each pretend trade, then prints basic performance stats (total P/L, win‑rate, p‑value, Sharpe ratio, and expected value per trade).
* Keeps the codebase small so you can read everything in one sitting.

---

## 1  Quick start

```bash
# 1  clone your empty repo
mkdir kalshi_paper_trader && cd $_

# 2  drop these files in (or use GitHub > Add File > Upload)

# 3  create a Python environment
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4  scrape & back‑test (90 days is just an example!)
python run_backtest.py --days 90 --themes WX MUSC
```

**About** `--days N` means: "Download all markets that **settled** during the last **N** days." It **doesn’t wipe older rows** you previously scraped. Want the whole history? Run once with a large number, e.g.

```bash
python run_backtest.py --days 9999 --themes WX MUSC   # ~all history so far
```

After the download, the script will

1. add new rows (or update existing ones) in `prices`,
2. run each strategy on the entire table, and
3. print a summary, e.g.

```
WeatherCheapYes | Trades: 42 | Total P/L: +$12.30 | Win‑rate: 57% | p‑val: 0.11 | Sharpe: 0.84 | EV: $0.29
```

You can run a single bot with `--strategy WeatherCheapYes`.

---

## 2  Repo layout

```
kalshi_paper_trader/
│   requirements.txt
│   run_backtest.py          # CLI entry‑point
│   .env.example             # put your Kalshi sandbox creds here
│
├── core/
│   ├── data_loader.py       # fetches & saves daily closes
│   ├── simulator.py         # paper‑trading engine
│   └── metrics.py           # p‑value, Sharpe, EV helpers
│
├── strategies/
│   ├── base.py              # Strategy base class
│   └── example_weather_bot.py
│
└── results/
    └── kalshi_data.db       # auto‑created on first run
```

---

## 3  Environment variables & sandbox login

Kalshi has **two separate sites**:

| Environment | URL                          | Purpose             | Login method                     |
| ----------- | ---------------------------- | ------------------- | -------------------------------- |
| **Live**    | `https://trading.kalshi.com` | real money          | Google/OAuth *or* email‑password |
| **Sandbox** | `https://demo.kalshi.com`    | risk‑free test data | **email‑password only**          |

We default to the sandbox so you can’t lose money while experimenting.

### Create sandbox credentials

1. Visit `https://demo.kalshi.com` in your browser.
2. Click **Sign Up** (Google login won’t appear here).
3. Register with an email + password.

### `.env` file

Copy `.env.example` ➜ `.env` and fill in your sandbox creds:

```
KALSHI_EMAIL=you@example.com
KALSHI_PASSWORD=yourSandboxPassword
```

If you later want live data, change the API host in `core/data_loader.py` and swap in your real credentials.

---

## 4  Database schema (SQLite)

```
Table: prices        # one row per closed market we scraped
 ├─ ticker TEXT PRIMARY KEY
 ├─ theme  TEXT       # e.g. WX or MUSC
 ├─ close_px REAL     # last traded price before market closed
 ├─ payout  REAL      # 1.0 if result was YES, else 0.0
 └─ settled_at TEXT   # ISO timestamp

Table: trades        # one row per pretend trade the simulator creates
 ├─ id INTEGER PRIMARY KEY AUTOINCREMENT
 ├─ strategy TEXT     # which bot placed the trade
 ├─ ticker TEXT
 ├─ entry_px REAL
 ├─ payout  REAL
 ├─ pnl REAL          # payout − entry_px (×1 contract)
 └─ placed_at TEXT    # same as prices.settled_at (v1 assumption)
```

A helper view called **strategy_stats** is rebuilt after every run so you can `SELECT * FROM strategy_stats;` in a SQLite client.

---

## 5  Coding your own strategy

Create a new file in `strategies/`, subclass `Strategy`, fill in `decide()`.

```python
# strategies/my_new_bot.py
from strategies.base import Strategy

class MyNewBot(Strategy):
    NAME  = "MyNewBot"     # must be unique
    THEME = "WX"           # only gets data rows where theme == THEME

    def decide(self, row):
        """row is a dict with keys ticker, close_px, payout, settled_at."""
        # example rule: buy YES if price < 0.25
        if row["close_px"] < 0.25:
            return True   # place the trade (stake = 1 contract)
        return False      # skip
```

No need to calculate P/L yourself—the simulator handles it.

---

## 6  File‑by‑file stubs

Below are minimal versions so the project runs immediately. Feel free to expand them.

```python
# requirements.txt
kalshi-python
python-dotenv
pandas
scipy
```

```python
# core/data_loader.py
"""Fetch closed Kalshi markets for chosen themes and save to SQLite."""
import os, sqlite3, datetime as dt
from kalshi_python import ApiInstance, Configuration
from dotenv import load_dotenv

load_dotenv()
api = ApiInstance(email=os.getenv("KALSHI_EMAIL"),
                  password=os.getenv("KALSHI_PASSWORD"),
                  configuration=Configuration(host="https://demo-api.kalshi.com/trade-api/v2"))

DB = "results/kalshi_data.db"

THEME_MAP = {
    "WX": "WX",    # weather series tickers start with WX
    "MUSC": "MUSC"  # top‑songs markets start with MUSC
}

```

```python
# core/simulator.py
"""Runs every strategy against rows in the prices table and logs fake trades."""
import sqlite3, importlib, glob
from datetime import datetime as dt
from pathlib import Path

DB = "results/kalshi_data.db"

# discover all Strategy subclasses dynamically

```

```python
# strategies/base.py
class Strategy:
    NAME  = "Base"   # override
    THEME = "WX"     # override

    def decide(self, row):
        raise NotImplementedError
```

```python
# strategies/example_weather_bot.py
from strategies.base import Strategy

class WeatherCheapYes(Strategy):
    NAME  = "WeatherCheapYes"
    THEME = "WX"

    def decide(self, row):
        # buy one contract if price < 0.30
        return row["close_px"] < 0.30
```

```python
# run_backtest.py
import argparse, os
from core.data_loader import fetch_closed_markets, upsert_prices
from core.simulator   import run_all
from core.metrics     import update_stats

parser = argparse.ArgumentParser()
parser.add_argument("--days", type=int, default=90)
parser.add_argument("--themes", nargs="+", default=["WX"])
args = parser.parse_args()

os.makedirs("results", exist_ok=True)

for theme in args.themes:
    rows = fetch_closed_markets(theme, args.days)
    upsert_prices(rows)

run_all()

stats = update_stats()
for s in stats:
    name, ntrades, total_pnl, win_rate, p_val, sharpe, ev = s
    sign = "+" if total_pnl >= 0 else "-"
    print(f"{name:15s} | Trades: {ntrades:3d} | Total P/L: {sign}${abs(total_pnl):.2f} | Win: {win_rate*100:4.0f}"
          f" | p-val: {p_val:.2f} | Sharpe: {sharpe:.2f} | EV: ${ev:.2f}")
```

---

## 7  Automating daily runs

A weather‑prediction strategy only needs fresh data **once a day**, right after Kalshi settles yesterday’s markets (usually early morning UTC). Run the same scrape/back‑test daily so your SQLite file and stats stay current.

| Platform             | How to schedule `run_backtest.py`                                                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Linux / macOS**    | `crontab -e` → `0 6 * * * /path/venv/bin/python /path/run_backtest.py --days 9999 --themes WX MUSC`                                                       |
| **Windows**          | Task Scheduler → new basic task → daily → action = *Start a program* → program = `python.exe`, arguments = `run_backtest.py --days 9999 --themes WX MUSC` |
| **GitHub Actions**   | Push repo to GitHub, add workflow with `cron: "0 10 * * *"`; cache `results/kalshi_data.db` as an artifact                                                |
| **Always‑on Pi/VPS** | Same cron job as above                                                                                                                                    |

Need a quick local script loop instead? Add this to `run_backtest.py` bottom and run it once:

```python
import schedule, time, os
schedule.every().day.at("06:00").do(lambda:
    os.system("python run_backtest.py --days 9999 --themes WX MUSC"))
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

