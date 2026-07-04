"""
Build the SQLite database for the SQL analysis phase (roadmap Phase 4).

Reads the cleaned CSVs and loads them into sql/zomato.db as two tables:
    restaurants          - one row per restaurant
    restaurant_cuisines  - one row per (restaurant, cuisine) pair

SQLite needs no server and no password: the whole database is just this one
file, which any tool (Python, DB Browser for SQLite, Power BI) can open.

Run from the project root:
    python sql/build_db.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_CSV = ROOT / "data" / "cleaned" / "zomato_clean.csv"
CUISINES_CSV = ROOT / "data" / "cleaned" / "zomato_cuisines.csv"
DB_PATH = ROOT / "sql" / "zomato.db"


def build():
    restaurants = pd.read_csv(CLEAN_CSV)
    cuisines = pd.read_csv(CUISINES_CSV)

    conn = sqlite3.connect(DB_PATH)
    try:
        restaurants.to_sql("restaurants", conn, if_exists="replace", index=False)
        cuisines.to_sql("restaurant_cuisines", conn, if_exists="replace", index=False)
        cur = conn.cursor()
        n_rest = cur.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        n_cuis = cur.execute("SELECT COUNT(*) FROM restaurant_cuisines").fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    print(f"Built {DB_PATH}")
    print(f"  restaurants:         {n_rest:,} rows")
    print(f"  restaurant_cuisines: {n_cuis:,} rows")


if __name__ == "__main__":
    build()
