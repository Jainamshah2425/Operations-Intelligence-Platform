"""
Central configuration for the Operations Intelligence Platform.

Keeping paths, mappings, and business thresholds in one place means the
whole pipeline (and every notebook) reads from a single source of truth.
Change a threshold here and every stage picks it up.
"""
from pathlib import Path

# --- Project paths (resolved relative to the project root) -------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_CSV = DATA_DIR / "india_all_restaurants_details.csv"   # immutable source
CLEANED_DIR = DATA_DIR / "cleaned"
CLEAN_CSV = CLEANED_DIR / "zomato_clean.csv"
CUISINES_CSV = CLEANED_DIR / "zomato_cuisines.csv"
SQL_DIR = ROOT / "sql"
DB_PATH = SQL_DIR / "zomato.db"
OUTPUTS_DIR = ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# --- Cleaning rules ----------------------------------------------------------
# Rating strings that mean "no real rating" rather than a number.
NON_RATINGS = {"NEW", "0", "-", "", "nan", "none"}

# City name standardisation. The dataset is mostly clean already, but we map
# known aliases so the same real-world city never splits across two labels.
CITY_MAP = {
    "Bangalore": "Bengaluru",
    "Mysore": "Mysuru",
    "Pondicherry": "Puducherry",
    "Gurgaon": "Delhi NCR",
    "Noida": "Delhi NCR",
    "New Delhi": "Delhi NCR",
    "Delhi": "Delhi NCR",
}

# Tier-1 metros for the city_tier engineered feature.
TIER1_CITIES = {
    "Delhi NCR", "Mumbai", "Bengaluru", "Hyderabad",
    "Chennai", "Pune", "Kolkata", "Ahmedabad",
}

# --- Business thresholds -----------------------------------------------------
DATA_QUALITY_THRESHOLD = 90.0   # pipeline FAILs below this % of usable rows
LOW_RATING_CUTOFF = 3.0         # "low rating" band for risk / RCA
HIGH_RATING_CUTOFF = 4.0        # "high rated" band
ISOLATION_CONTAMINATION = 0.05  # expected fraction of anomalies

# 5-factor opportunity score weights (must sum sensibly; comp is a penalty).
OPPORTUNITY_WEIGHTS = {
    "rating": 0.35,
    "demand": 0.25,
    "online": 0.20,
    "gap": 0.10,
    "competition": -0.10,
}
