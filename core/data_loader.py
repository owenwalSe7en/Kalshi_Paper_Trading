"""Fetch closed Kalshi markets for chosen themes and save to SQLite."""
import os
import sqlite3
import datetime as dt
from kalshi_python import ApiInstance, Configuration
from dotenv import load_dotenv

load_dotenv()
api = ApiInstance(
    email=os.getenv("KALSHI_EMAIL"),
    password=os.getenv("KALSHI_PASSWORD"),
    configuration=Configuration(host="https://demo-api.kalshi.com/trade-api/v2"),
)

DB = "results/kalshi_data.db"

THEME_MAP = {
    "WX": "WX",
    "MUSC": "MUSC",
}


def fetch_closed_markets(theme: str, days_back: int):
    """Return a list of dicts for markets settled in the given window."""
    prefix = THEME_MAP.get(theme)
    if prefix is None:
        return []

    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=days_back)
    page = 1
    out = []
    while True:
        resp = api.get_markets(status="closed", per_page=500, page=page)
        if not resp.markets:
            break
        for m in resp.markets:
            settlement = dt.datetime.fromisoformat(m.settlement_time.replace("Z", "+00:00"))
            if (
                m.series_ticker.startswith(prefix)
                and start <= settlement <= end
            ):
                out.append(
                    {
                        "ticker": m.ticker,
                        "theme": theme,
                        "close_px": m.close_price,
                        "payout": 1.0 if m.result == "yes" else 0.0,
                        "settled_at": m.settlement_time,
                    }
                )
        page += 1
    return out


def upsert_prices(rows):
    """Insert or update price rows in the SQLite database."""
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS prices(
                    ticker TEXT PRIMARY KEY,
                    theme TEXT,
                    close_px REAL,
                    payout REAL,
                    settled_at TEXT
                )"""
    )
    with con:
        con.executemany(
            """INSERT OR REPLACE INTO prices
            (ticker, theme, close_px, payout, settled_at)
            VALUES (:ticker, :theme, :close_px, :payout, :settled_at)""",
            rows,
        )
    con.close()
