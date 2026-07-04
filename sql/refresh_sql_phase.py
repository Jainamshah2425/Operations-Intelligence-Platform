"""Regenerate cuisines CSV, rebuild DB, and re-export all 8 query result CSVs."""
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.etl import explode_cuisines
from pipeline.config import CLEAN_CSV, CUISINES_CSV, DB_PATH, OUTPUTS_DIR, SQL_DIR


def export_queries(conn):
    raw = (SQL_DIR / "analysis_queries.sql").read_text(encoding="utf-8")
    exported = []
    for i, stmt in enumerate(raw.split(";"), start=1):
        stmt = stmt.strip()
        if not stmt:
            continue
        code = "\n".join(
            ln for ln in stmt.splitlines() if not ln.strip().startswith("--")
        ).strip()
        if not code.upper().startswith("SELECT"):
            continue
        m = re.search(r"Q(\d+)\s*-\s*([^:\n]+)", stmt)
        qnum = m.group(1) if m else str(i)
        df = pd.read_sql_query(code, conn)
        out = OUTPUTS_DIR / f"q{qnum}_results.csv"
        df.to_csv(out, index=False)
        exported.append((out.name, len(df)))
    return exported


def main():
    restaurants = pd.read_csv(CLEAN_CSV)
    cuisines = explode_cuisines(restaurants)
    cuisines.to_csv(CUISINES_CSV, index=False)
    print(f"Wrote {CUISINES_CSV.name}: {len(cuisines):,} rows")

    db_target = DB_PATH
    db_tmp = DB_PATH.with_name("zomato_refresh.db")
    try:
        conn = sqlite3.connect(db_tmp)
        restaurants.to_sql("restaurants", conn, if_exists="replace", index=False)
        cuisines.to_sql("restaurant_cuisines", conn, if_exists="replace", index=False)
        exported = export_queries(conn)
        conn.close()
        try:
            if db_target.exists():
                db_target.unlink()
            db_tmp.replace(db_target)
            print(f"Rebuilt {db_target.name}")
        except OSError:
            print(f"Could not replace {db_target.name} (close DB Browser if open).")
            print(f"Fresh database saved as {db_tmp.name} — queries exported from there.")
    except sqlite3.OperationalError as exc:
        raise SystemExit(f"SQLite error: {exc}") from exc

    for name, rows in exported:
        print(f"  {name}: {rows} rows")

    zero = (cuisines["cuisine"] == "0").sum()
    print(f"\nCuisine '0' rows remaining: {zero}")


if __name__ == "__main__":
    main()
