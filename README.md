# Operations Intelligence Platform
### End-to-End Automated Analytics on 224,000+ Indian Restaurant Records

An automated Python -> SQL -> Power BI pipeline built on the Zomato India dataset.
It ingests raw data, validates its own quality, statistically profiles operational
health, flags anomalies, forecasts trends, and reports to management - with a single
command.

> Portfolio project on public restaurant data. The transferable skill is the
> *pipeline* an Operations Analytics team builds: automated, validated,
> statistically grounded, anomaly-aware, and presented to a management audience.

---

## Business Question
How can an operations team monitor 224K+ records automatically, catch data-quality
issues and anomalies early, and report actionable insight to management without
manual rework?

## Key Findings
- **Cost does not buy ratings** - correlation between price and rating is near zero;
  Indian diners reward value-for-money, not premium pricing.
- **Metros are saturated** - Delhi NCR, Mumbai and Bengaluru hold the most
  restaurants, while several **Tier-2 cities** match their ratings at lower cost.
- **~35% of restaurants are unrated (new)** - a large new-entrant tail, and a
  data-quality signal that must be handled (not counted as zero).
- **Premium is under-supplied vs how well it performs** - high-rated share climbs
  with price tier even though the market is mostly Budget/Mid-range.

## Data Quality Issues Resolved
- `rating`: text (`'NEW'`, `'0'`, garbage) -> float; unrated mapped to null, not 0
- `cost_for_two`: stripped thousands-commas (`'1,200'` -> `1200.0`); `0` -> null
- `city_clean`: folded aliases (Gurgaon/Noida/New Delhi -> Delhi NCR)
- `cusine`: exploded multi-value column into a normalised cuisine table (473K rows)
- Engineered: `price_tier`, `city_tier`, `has_online_order`, `has_table_booking`

**Structural data quality after cleaning: 98.4%** (valid cost + city).

## Pipeline
```
Raw CSV -> Python ETL -> Validation (pass/fail) -> SQLite
        -> 8 SQL business queries -> Opportunity scoring
        -> Anomaly detection (IQR / Z-score / Isolation Forest)
        -> Auto-generated PDF report
```
Run it all with one command (~15 sec on this machine):
```bash
python -m pipeline.run_pipeline
```

## Stack
Python | Pandas | NumPy | scikit-learn | SciPy | SQLite | Power BI | Matplotlib/Seaborn

## Project Structure
```
data/                         raw + cleaned CSVs (gitignored, kept local)
notebooks/  01_first_look  02_cleaning  03_eda  04_statistics_forecasting
sql/        schema.sql  analysis_queries.sql  build_db.py
pipeline/   config etl validate anomaly opportunity report run_pipeline
outputs/    q*_results.csv  city_opportunity_scores.csv  figures/  reports/
docs/       PROJECT_DOCUMENTATION.md
```

## How to Run
1. `pip install -r requirements.txt`
2. Add the raw dataset to `data/` (see `pipeline/config.py` for the expected filename)
3. Notebooks in order: `01 -> 02 -> 03 -> 04` (data cleaning + analysis story)
4. `python -m pipeline.run_pipeline` for the full automated ETL + report

---

## Resume Bullet
> Built an end-to-end Python, SQL, and Power BI analytics pipeline processing 224K+
> records; automated data validation and ETL with a pass/fail quality gate;
> engineered business features and a 5-factor weighted opportunity-scoring model;
> applied statistics (correlation, z-scores, 95% confidence intervals) and trend
> forecasting; implemented anomaly detection (IQR, Z-score, Isolation Forest) to
> flag operational risk; delivered an executive dashboard and auto-generated PDF
> reporting layer enabling data-driven operational decisions.
