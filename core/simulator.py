"""Runs strategies against stored prices and logs pretend trades."""
import sqlite3
import importlib
import glob
from datetime import datetime as dt
from pathlib import Path

DB = "results/kalshi_data.db"


def load_strategies():
    """Import all strategy modules and return Strategy subclasses."""
    mods = glob.glob("strategies/*.py")
    for m in mods:
        if m.endswith("base.py"):
            continue
        importlib.import_module(Path(m).stem, "strategies")
    from strategies.base import Strategy
    return Strategy.__subclasses__()


def run_all(selected_strategy=None):
    """Run each strategy (or a specific one) and log trades."""
    from strategies.base import Strategy

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS trades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy TEXT,
            ticker TEXT,
            entry_px REAL,
            payout REAL,
            pnl REAL,
            placed_at TEXT
        )"""
    )

    for Strat in load_strategies():
        if selected_strategy and Strat.NAME != selected_strategy:
            continue
        rows = cur.execute(
            "SELECT ticker, close_px, payout, settled_at FROM prices WHERE theme = ?",
            (Strat.THEME,),
        ).fetchall()
        trades = []
        for ticker, px, payout, ts in rows:
            bot = Strat()
            if bot.decide(
                {
                    "ticker": ticker,
                    "close_px": px,
                    "payout": payout,
                    "settled_at": ts,
                }
            ):
                pnl = payout - px
                trades.append((Strat.NAME, ticker, px, payout, pnl, ts))
        with con:
            con.executemany(
                "INSERT INTO trades(strategy,ticker,entry_px,payout,pnl,placed_at) VALUES (?,?,?,?,?,?)",
                trades,
            )
    con.close()
