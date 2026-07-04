"""
Anomaly detection layer: three methods, simplest to most advanced.

- IQR and Z-score are single-variable, fast, and fully explainable.
- Isolation Forest is multi-variable and catches *combination* anomalies that
  neither single-variable test would flag on its own.

This mirrors how real operations teams work: simple rule-based alerts for known
issues, plus a model to catch the "unknown unknowns".
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest

from pipeline.config import (
    ISOLATION_CONTAMINATION, LOW_RATING_CUTOFF,
)


def iqr_anomalies(series):
    """Flag values outside 1.5*IQR of the quartiles (classic boxplot rule)."""
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    return mask.fillna(False), (lower, upper)


def zscore_anomalies(series, threshold=3.0):
    """Flag values more than `threshold` standard deviations from the mean."""
    s = series.dropna()
    z = pd.Series(stats.zscore(s), index=s.index)
    flagged_index = z.index[z.abs() > threshold]
    mask = pd.Series(False, index=series.index)
    mask.loc[flagged_index] = True
    return mask


def isolation_forest_anomalies(df, features=("rating", "cost_for_two")):
    """Multi-feature unsupervised anomaly flags. Returns a boolean Series aligned
    to df.index (True = anomaly). Rows with missing features are treated as normal."""
    subset = df[list(features)].dropna()
    model = IsolationForest(
        contamination=ISOLATION_CONTAMINATION, random_state=42, n_estimators=100
    )
    preds = model.fit_predict(subset)          # -1 = anomaly, 1 = normal
    mask = pd.Series(False, index=df.index)
    mask.loc[subset.index] = preds == -1
    return mask


def business_risk_flags(df):
    """Explicit business rule: High Cost (> city 75th pct) AND Low Rating (<3.0).
    These are the restaurants an ops team would investigate first."""
    city_p75 = df.groupby("city_clean")["cost_for_two"].transform(
        lambda x: x.quantile(0.75)
    )
    high_cost = df["cost_for_two"] > city_p75
    low_rating = df["rating"] < LOW_RATING_CUTOFF
    return (high_cost & low_rating).fillna(False)


def detect_all(df):
    """Run every method and attach flag columns. Returns (df_with_flags, summary)."""
    df = df.copy()
    df["anom_iqr_cost"], _ = iqr_anomalies(df["cost_for_two"])
    df["anom_zscore_cost"] = zscore_anomalies(df["cost_for_two"])
    df["anom_isoforest"] = isolation_forest_anomalies(df)
    df["operational_risk"] = business_risk_flags(df)

    summary = {
        "iqr_cost_anomalies": int(df["anom_iqr_cost"].sum()),
        "zscore_cost_anomalies": int(df["anom_zscore_cost"].sum()),
        "isolation_forest_anomalies": int(df["anom_isoforest"].sum()),
        "operational_risk_flags": int(df["operational_risk"].sum()),
    }
    return df, summary
