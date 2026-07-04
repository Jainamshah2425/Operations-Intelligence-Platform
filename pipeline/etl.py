"""
ETL layer: Extract -> Transform -> Load.

Every cleaning rule lives here as a small, named, testable function so the
same logic runs identically in a notebook demo and in the automated pipeline.
This is the "refactor notebooks into a pipeline" step (roadmap Phase 8).
"""
import sqlite3
import pandas as pd
import numpy as np

from pipeline.config import (
    RAW_CSV, CLEAN_CSV, CUISINES_CSV, DB_PATH,
    NON_RATINGS, CITY_MAP, TIER1_CITIES,
)


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def extract(path=RAW_CSV):
    """Read the immutable raw CSV. low_memory=False silences mixed-type warnings
    on the cost column, which we clean explicitly below."""
    return pd.read_csv(path, low_memory=False)


# ---------------------------------------------------------------------------
# COLUMN-LEVEL CLEANING FUNCTIONS
# ---------------------------------------------------------------------------
def clean_rating(value):
    """'4.1' -> 4.1 ; 'NEW'/'0'/'Nov...'/NaN -> NaN.

    On Zomato, 'NEW' and '0' mean the restaurant has no real rating yet, so we
    map them to null instead of treating 0 as a genuine score (which would drag
    every average down)."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if text.lower() in {s.lower() for s in NON_RATINGS}:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan  # garbage like 'Nov...'


def clean_cost(value):
    """'1,200' -> 1200.0 ; '' / 0 / NaN -> NaN. Commas are thousands separators."""
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", "").strip()
    try:
        cost = float(text)
    except ValueError:
        return np.nan
    return cost if cost > 0 else np.nan   # 0 cost is invalid, not free


def standardise_city(value):
    """Trim whitespace and fold known aliases onto one canonical name."""
    if pd.isna(value):
        return np.nan
    city = str(value).strip()
    return CITY_MAP.get(city, city)


def price_tier(cost):
    """Bucket cost-for-two into four business-facing price bands."""
    if pd.isna(cost):
        return "Unknown"
    if cost < 300:
        return "Budget (<300)"
    if cost < 700:
        return "Mid-range (300-700)"
    if cost < 1500:
        return "Premium (700-1500)"
    return "Luxury (1500+)"


def city_tier(city):
    """Classify a city as Tier 1 metro or Tier 2+ for expansion analysis."""
    return "Tier 1" if city in TIER1_CITIES else "Tier 2+"


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------
def transform(df):
    """Apply every cleaning rule and engineer new features. Returns a NEW frame
    so the raw input is never mutated in place."""
    df = df.copy()

    # Numeric conversions
    df["rating"] = df["rating"].apply(clean_rating)
    df["cost_for_two"] = df["cost_for_two"].apply(clean_cost)

    # Standardisation
    df["city_clean"] = df["city"].apply(standardise_city)

    # Rename for clarity (these are already booleans in this dataset)
    df["has_online_order"] = df["online_order"].astype(bool)
    df["has_table_booking"] = df["table_reservation"].astype(bool)

    # votes = number of ratings received
    df["votes"] = pd.to_numeric(df["rating_count"], errors="coerce").fillna(0).astype(int)

    # location = locality within a city
    df["location"] = df["area"].astype(str).str.strip()

    # Engineered features
    df["price_tier"] = df["cost_for_two"].apply(price_tier)
    df["city_tier"] = df["city_clean"].apply(city_tier)

    # Keep a tidy, analysis-ready column set
    keep = [
        "name", "city_clean", "city_tier", "location", "cusine",
        "rating", "votes", "cost_for_two", "price_tier",
        "has_online_order", "has_table_booking", "delivery_only",
    ]
    return df[keep]


def explode_cuisines(df):
    """Turn the comma-separated 'cusine' column into one row per cuisine so we
    can count cuisines correctly without double-counting restaurants."""
    tmp = df.copy()
    # Raw data uses "0" as a missing-cuisine placeholder (like rating uses "NEW").
    tmp["cusine"] = tmp["cusine"].replace("0", np.nan).fillna("Unknown")
    exploded = tmp.assign(cuisine=tmp["cusine"].str.split(",")).explode("cuisine")
    exploded["cuisine"] = exploded["cuisine"].str.strip()
    exploded = exploded[(exploded["cuisine"] != "") & (exploded["cuisine"] != "0")]
    return exploded[["name", "city_clean", "cuisine", "rating", "cost_for_two"]]


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load_csv(df_clean, df_cuisines):
    """Write cleaned outputs to the cleaned/ folder (raw is never touched)."""
    CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN_CSV, index=False)
    df_cuisines.to_csv(CUISINES_CSV, index=False)


def load_sqlite(df_clean, df_cuisines, db_path=DB_PATH):
    """Load both tables into SQLite so SQL and Power BI can query the same data."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df_clean.to_sql("restaurants", conn, if_exists="replace", index=False)
        df_cuisines.to_sql("restaurant_cuisines", conn, if_exists="replace", index=False)
    finally:
        conn.close()
