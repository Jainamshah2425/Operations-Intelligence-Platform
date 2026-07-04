"""
One-command orchestrator for the Operations Intelligence Platform.

    python -m pipeline.run_pipeline

Runs the full flow end to end:
    extract -> transform -> validate -> load (CSV + SQLite)
    -> run SQL business queries and export results
    -> compute city opportunity scores
    -> detect anomalies
    -> generate an executive PDF report
Everything is timed so we can quantify the automation benefit.
"""
import re
import time
import sqlite3

import pandas as pd

from pipeline import etl, validate as validate_mod, anomaly, report as report_mod
from pipeline.opportunity import city_opportunity_table
from pipeline.config import (
    RAW_CSV, DB_PATH, OUTPUTS_DIR, SQL_DIR,
    CLEAN_CSV, CUISINES_CSV,
)

MANUAL_ESTIMATE_MINUTES = 360  # ~6 hrs to do this by hand, once


def run_sql_queries():
    """Execute each query in analysis_queries.sql and export results as CSVs."""
    query_file = SQL_DIR / "analysis_queries.sql"
    raw = query_file.read_text(encoding="utf-8")

    # Split on ';', keep only real statements, strip pure-comment blocks.
    statements = [s.strip() for s in raw.split(";") if s.strip()]
    conn = sqlite3.connect(DB_PATH)
    exported = []
    try:
        for i, stmt in enumerate(statements, start=1):
            code = "\n".join(
                ln for ln in stmt.splitlines() if not ln.strip().startswith("--")
            ).strip()
            if not code.upper().startswith("SELECT"):
                continue
            # Pull a friendly name from the "-- Qn - Title" comment if present.
            m = re.search(r"Q(\d+)\s*-\s*([^:\n]+)", stmt)
            qnum = m.group(1) if m else str(i)
            df = pd.read_sql_query(code, conn)
            out = OUTPUTS_DIR / f"q{qnum}_results.csv"
            df.to_csv(out, index=False)
            exported.append(out.name)
    finally:
        conn.close()
    return exported


def build_key_findings(clean, opp, anomaly_summary):
    """Derive a few headline findings straight from the data for the PDF."""
    top_city = opp.iloc[0]
    rated = clean.dropna(subset=["rating"])
    findings = [
        f"Top opportunity city: {top_city['city_clean']} "
        f"(score {top_city['opportunity_score']:.1f}, "
        f"avg rating {top_city['avg_rating']:.2f}).",
        f"{clean['rating'].isna().sum():,} restaurants are unrated (new) - "
        f"{100 * clean['rating'].isna().mean():.1f}% of the dataset.",
        f"Average rating across rated restaurants is {rated['rating'].mean():.2f} "
        f"on a 5-point scale.",
        f"{anomaly_summary['operational_risk_flags']:,} restaurants flagged as "
        f"operational risk (high cost + low rating).",
        f"Online ordering enabled at "
        f"{100 * clean['has_online_order'].mean():.1f}% of restaurants.",
    ]
    return findings


def main():
    start = time.time()
    print("Starting Operations Intelligence pipeline...\n")

    # 1. Extract
    raw = etl.extract(RAW_CSV)
    print(f"[extract]  {len(raw):,} raw rows read from {RAW_CSV.name}")

    # 2. Transform
    clean = etl.transform(raw)
    cuisines = etl.explode_cuisines(clean)
    print(f"[transform] {len(clean):,} clean rows, {len(cuisines):,} cuisine rows")

    # 3. Validate
    report = validate_mod.validate(raw, clean)
    validate_mod.print_report(report)
    if report["pipeline_status"].startswith("FAIL"):
        print("\nPipeline halted: data quality below threshold.")
        return

    # 4. Load
    etl.load_csv(clean, cuisines)
    etl.load_sqlite(clean, cuisines)
    print(f"[load]      wrote {CLEAN_CSV.name}, {CUISINES_CSV.name}, {DB_PATH.name}")

    # 5. SQL business queries -> CSVs
    exported = run_sql_queries()
    print(f"[sql]       exported {len(exported)} query result files: {exported}")

    # 6. Opportunity scores
    opp = city_opportunity_table(clean)
    opp.to_csv(OUTPUTS_DIR / "city_opportunity_scores.csv", index=False)
    print(f"[score]     opportunity table for {len(opp)} cities")

    # 7. Anomaly detection
    flagged, anomaly_summary = anomaly.detect_all(clean)
    flagged[flagged["operational_risk"]].to_csv(
        OUTPUTS_DIR / "operational_risk_restaurants.csv", index=False
    )
    print(f"[anomaly]   {anomaly_summary}")

    # 8. Executive PDF
    findings = build_key_findings(clean, opp, anomaly_summary)
    pdf_path = report_mod.generate_report(report, anomaly_summary, findings)
    print(f"[report]    wrote {pdf_path}")

    # Automation metric
    minutes = (time.time() - start) / 60
    saved = round(100 * (1 - minutes / MANUAL_ESTIMATE_MINUTES), 1)
    print(f"\nDone in {minutes:.2f} min "
          f"(vs ~{MANUAL_ESTIMATE_MINUTES/60:.0f} hr manual  ->  ~{saved}% time saved).")


if __name__ == "__main__":
    main()
