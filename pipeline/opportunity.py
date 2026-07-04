"""
5-factor weighted opportunity score (roadmap Phase 5, improved version).

Raw metrics live on wildly different scales (rating 0-5, counts in the
thousands, percentages 0-100). We MinMax-normalise every factor to 0-1 first so
the weights -- not the raw magnitudes -- control each factor's influence.
"""
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from pipeline.config import OPPORTUNITY_WEIGHTS, HIGH_RATING_CUTOFF


def city_opportunity_table(df):
    """Aggregate per-city metrics and compute a normalised opportunity score."""
    g = df.groupby("city_clean")
    metrics = pd.DataFrame({
        "restaurant_count": g.size(),
        "avg_rating": g["rating"].mean(),
        "demand_index": g["votes"].sum(),                      # total engagement
        "online_pct": g["has_online_order"].mean() * 100,
        "market_gap": g.apply(                                  # high-rated share
            lambda x: (x["rating"] >= HIGH_RATING_CUTOFF).mean() * 100,
            include_groups=False,
        ),
    })
    metrics["competition_density"] = metrics["restaurant_count"]
    metrics = metrics.dropna(subset=["avg_rating"])
    metrics = metrics[metrics["restaurant_count"] >= 50]

    scaler = MinMaxScaler()
    cols = ["avg_rating", "demand_index", "online_pct", "market_gap", "competition_density"]
    norm = pd.DataFrame(
        scaler.fit_transform(metrics[cols]),
        columns=["rating_n", "demand_n", "online_n", "gap_n", "comp_n"],
        index=metrics.index,
    )

    w = OPPORTUNITY_WEIGHTS
    metrics["opportunity_score"] = (
        w["rating"] * norm["rating_n"]
        + w["demand"] * norm["demand_n"]
        + w["online"] * norm["online_n"]
        + w["gap"] * norm["gap_n"]
        + w["competition"] * norm["comp_n"]
    ) * 100

    return metrics.sort_values("opportunity_score", ascending=False).reset_index()
