import sqlite3
import pandas as pd
from scipy.stats import binomtest

DB = "results/kalshi_data.db"


def update_stats():
    """Rebuild strategy_stats table and return summary list."""
    con = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT strategy, pnl FROM trades", con)
    if df.empty:
        con.execute("DROP TABLE IF EXISTS strategy_stats")
        con.execute(
            """CREATE TABLE strategy_stats(
                strategy TEXT,
                trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                p_value REAL,
                sharpe REAL,
                ev REAL
            )"""
        )
        con.commit()
        con.close()
        return []

    df["win"] = df["pnl"] > 0
    stats = []
    for strat, g in df.groupby("strategy"):
        pnls = g["pnl"].to_numpy()
        mean = pnls.mean()
        sharpe = mean / pnls.std(ddof=1) if len(pnls) > 1 else 0.0
        p_val = binomtest(g["win"].sum(), len(g), p=0.5).pvalue
        stats.append((strat, len(g), pnls.sum(), g["win"].mean(), p_val, sharpe, mean))

    con.execute("DROP TABLE IF EXISTS strategy_stats")
    con.execute(
        """CREATE TABLE strategy_stats(
            strategy TEXT,
            trades INTEGER,
            total_pnl REAL,
            win_rate REAL,
            p_value REAL,
            sharpe REAL,
            ev REAL
        )"""
    )
    con.executemany(
        "INSERT INTO strategy_stats VALUES (?,?,?,?,?,?,?)",
        stats,
    )
    con.commit()
    con.close()
    return stats
