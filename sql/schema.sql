-- Schema reference for the Operations Intelligence Platform (SQLite).
-- Tables are created automatically by the ETL load step (pandas to_sql),
-- but this file documents the expected structure for reviewers.

-- Main analysis-ready table: one row per restaurant.
CREATE TABLE IF NOT EXISTS restaurants (
    name              TEXT,
    city_clean        TEXT,      -- standardised city name
    city_tier         TEXT,      -- 'Tier 1' or 'Tier 2+'
    location          TEXT,      -- locality / area within the city
    cusine            TEXT,      -- raw comma-separated cuisines
    rating            REAL,      -- cleaned float; NULL = new / unrated
    votes             INTEGER,   -- number of ratings received
    cost_for_two      REAL,      -- cleaned float in INR; NULL = invalid/unknown
    price_tier        TEXT,      -- Budget / Mid-range / Premium / Luxury
    has_online_order  INTEGER,   -- 1 = yes, 0 = no
    has_table_booking INTEGER,   -- 1 = yes, 0 = no
    delivery_only     INTEGER    -- 1 = yes, 0 = no
);

-- Normalised cuisine table: one row per (restaurant, cuisine) pair.
-- Use this ONLY for cuisine-level analysis to avoid double-counting restaurants.
CREATE TABLE IF NOT EXISTS restaurant_cuisines (
    name         TEXT,
    city_clean   TEXT,
    cuisine      TEXT,
    rating       REAL,
    cost_for_two REAL
);

-- Helpful indexes for the analysis queries.
CREATE INDEX IF NOT EXISTS idx_rest_city   ON restaurants(city_clean);
CREATE INDEX IF NOT EXISTS idx_rest_tier   ON restaurants(city_tier);
CREATE INDEX IF NOT EXISTS idx_cuis_name   ON restaurant_cuisines(cuisine);
