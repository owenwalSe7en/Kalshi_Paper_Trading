import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from strategies.example_weather_bot import WeatherCheapYes


def test_decide_returns_bool():
    bot = WeatherCheapYes()
    row = {"ticker": "WX123", "close_px": 0.1, "payout": 1.0, "settled_at": "2024-01-01T00:00:00Z"}
    assert isinstance(bot.decide(row), bool)


def test_run_creates_tables(tmp_path):
    db_path = tmp_path / "kalshi_data.db"
    os.environ["KALSHI_EMAIL"] = "demo@example.com"
    os.environ["KALSHI_PASSWORD"] = "pass"
    from core.data_loader import DB
    from core.data_loader import upsert_prices
    from core.simulator import run_all
    from core.metrics import update_stats

    # patch DB path
    orig_db = DB
    import core.data_loader
    import core.simulator
    import core.metrics
    core.data_loader.DB = str(db_path)
    core.simulator.DB = str(db_path)
    core.metrics.DB = str(db_path)

    upsert_prices([
        {
            "ticker": "WX1",
            "theme": "WX",
            "close_px": 0.1,
            "payout": 1.0,
            "settled_at": "2024-01-01T00:00:00Z",
        }
    ])
    run_all(selected_strategy=None)
    update_stats()

    con = sqlite3.connect(db_path)
    try:
        con.execute("SELECT 1 FROM prices")
        con.execute("SELECT 1 FROM trades")
    finally:
        con.close()

    # restore DB path
    core.data_loader.DB = orig_db
    core.simulator.DB = orig_db
    core.metrics.DB = orig_db

