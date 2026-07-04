# Project Documentation - Operations Intelligence Platform

Technical specification and methodology record. The README is for discovery; this
document is for reviewers evaluating rigour.

## 1. Project Scope
An automated analytics platform that turns a raw restaurant dataset into validated,
statistically-profiled, anomaly-aware operational intelligence, delivered as an
executive dashboard and an auto-generated PDF report. **In scope:** ETL automation,
data-quality gating, EDA, SQL business analysis, opportunity scoring, statistics,
forecasting methodology, anomaly detection, reporting. **Out of scope:** live data
ingestion, real-time streaming, production scheduling (documented as future work).
**Simulated stakeholder:** the operations team of a restaurant aggregator deciding
where to expand and which restaurants to flag for intervention.

## 2. Problem Statement
Not "analyse restaurants" but: *which cities and cuisines offer the best expansion
opportunity, which restaurants represent operational risk, and how can this be
monitored and reported continuously without manual rework?*

## 3. Assumptions
- The Zomato dataset is a **single snapshot**, not a time series. The forecasting
  section therefore uses an **illustrative** monthly adoption trend to demonstrate
  methodology; it is clearly labelled as such.
- `rating` values of `'NEW'`/`'0'` mean *unrated*, so they are treated as null.
- `cost_for_two` of `0` is treated as invalid/missing, not "free".
- City aliases (Gurgaon, Noida, New Delhi) are folded into `Delhi NCR`.
- Tier-1 = the 8 largest metros; everything else is Tier-2+.

## 4. Methodology
- **Cleaning:** per-column functions with data-loss tracking (`pipeline/etl.py`).
- **EDA:** 10 business questions, each with a chart and a written observation.
- **SQL:** 8 documented queries incl. a composite opportunity score.
- **Statistics:** descriptive stats, correlation (with causation caveat), z-scores,
  95% confidence interval on mean rating.
- **Opportunity scoring:** 5-factor MinMax-normalised weighted model
  (rating .35, demand .25, online .20, gap .10, competition -.10).
- **Anomaly detection:** IQR and Z-score (single-variable) plus Isolation Forest
  (multi-variable), plus an explicit business rule (high cost + low rating).
- **Forecasting:** linear regression vs moving average, trade-off documented.

## 5. Pipeline Architecture
```
Raw CSV -> extract -> transform (clean + engineer) -> validate (PASS/FAIL gate)
        -> load (CSV + SQLite) -> SQL queries -> opportunity scores
        -> anomaly detection -> executive PDF report
```
Production note: this would run on a cron schedule or an Airflow DAG rather than
manual execution, writing a dated report to an archive folder each run.

## 6. Validation
Measured on the actual run of 224,520 rows:
- Rows read: 224,520; rows after cleaning: 224,520 (no rows dropped, values nulled)
- Missing ratings (new restaurants): 79,785 (~35.5%) - a finding, not corruption
- Missing/invalid costs: 3,648
- Structural data quality: **98.38%** (valid cost + city)
- Threshold: pipeline FAILs below 90% -> status **PASS**

## 7. Insights (Observation -> Recommendation -> Expected Impact)
1. **O:** Price and rating are near-uncorrelated. **R:** Compete on value and
   consistency, not premium pricing. **I:** Broader addressable market at lower cost.
2. **O:** Tier-2 cities match metro ratings at lower cost/competition.
   **R:** Prioritise Tier-2 delivery infrastructure. **I:** Growth away from
   saturated metros.
3. **O:** ~35% of restaurants are unrated (new). **R:** Track "new restaurant" share
   as a market-momentum metric. **I:** Early read on market entry velocity.
4. **O:** Restaurants without online ordering skew low-rated. **R:** Treat online
   enablement as an operational-health metric. **I:** Structural fix to the
   low-rating cluster.
5. **O:** Premium tier is under-supplied vs its high-rated share. **R:** Test a
   premium delivery product in select cities. **I:** Capture an under-served segment.

## 8. Business Impact
If deployed operationally: expansion decisions shift from intuition to a ranked,
weighted score with sensitivity testing; ~3,400 high-risk restaurants are flagged
automatically for investigation; and the daily reporting that would take an analyst
~6 hours by hand runs in seconds, freeing that time for interpretation.

## 9. Limitations
- Dataset is a snapshot (circa the source's collection date); market has since moved.
- Forecasting uses illustrative, not true time-series, data.
- Anomaly thresholds are not validated against ground-truth labelled incidents.
- Logical duplicates (~9k on name/city/area) are retained unless exact duplicates.

## 10. Future Work
Live data refresh; true time-series forecasting; automated email delivery of the PDF;
per-capita normalisation using demographic data; a predictive rating model; and
integration with a ticketing system so flagged anomalies open investigation tasks.

---

## Timeline & Dependencies
| Phase | Deliverable | Depends on |
|-------|-------------|-----------|
| 1 Setup & First Look | Folder structure, data-quality report | none |
| 2 Cleaning | Clean CSVs + documented functions | 1 |
| 3 EDA | 10 findings with charts | 2 |
| 4 SQL | 8 queries + result CSVs | 2 |
| 5 Dashboard | Power BI executive dashboard | 3, 4 |
| 6 Packaging | README, resume bullet, interview prep | 5 |
| 7 Statistics | Stats + forecasting notebook | 2 |
| 8 Automation | ETL pipeline + validation + anomaly + PDF | 2-5 |
| 9 Documentation | This document | 1-8 |
