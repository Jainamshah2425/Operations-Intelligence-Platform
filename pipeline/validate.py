"""
Validation layer: automated data-quality checks that run after every ETL pass.

The point is that the pipeline can REFUSE to publish when data quality drops
below a threshold, instead of silently pushing bad numbers to a dashboard a
manager later trusts.

Design note: missing RATINGS are treated as a *finding*, not corruption -- on
Zomato a missing rating means a brand-new restaurant, which is legitimate data.
The quality score therefore measures STRUCTURAL completeness (valid cost + city),
while unrated restaurants are reported separately as an analytical signal.
"""
from pipeline.config import DATA_QUALITY_THRESHOLD


def validate(df_raw, df_clean):
    """Compare raw vs cleaned and return a structured quality report dict."""
    rows_read = len(df_raw)
    rows_clean = len(df_clean)

    structurally_valid = df_clean["cost_for_two"].notna() & df_clean["city_clean"].notna()
    valid_rows = int(structurally_valid.sum())

    report = {
        "rows_read": rows_read,
        "rows_after_cleaning": rows_clean,
        "duplicate_rows_in_raw": int(df_raw.duplicated().sum()),
        "missing_ratings_new_restaurants": int(df_clean["rating"].isna().sum()),
        "missing_costs": int(df_clean["cost_for_two"].isna().sum()),
        "invalid_cities": int(df_clean["city_clean"].isna().sum()),
        "structurally_valid_rows": valid_rows,
    }

    quality_pct = round(100.0 * valid_rows / rows_read, 2) if rows_read else 0.0
    report["data_quality_pct"] = quality_pct
    report["pipeline_status"] = (
        "PASS" if quality_pct >= DATA_QUALITY_THRESHOLD
        else f"FAIL - quality {quality_pct}% below {DATA_QUALITY_THRESHOLD}% threshold"
    )
    return report


def print_report(report):
    """Human-readable dump for the console / notebook."""
    print("=" * 50)
    print("DATA QUALITY VALIDATION REPORT")
    print("=" * 50)
    for key, value in report.items():
        print(f"{key:.<38} {value}")
    print("=" * 50)
