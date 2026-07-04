-- ===========================================================================
-- 8 BUSINESS QUERIES  |  Operations Intelligence Platform
-- Each query = a business question + the SQL + the insight it produces.
-- Runnable as-is against sql/zomato.db (see pipeline/run_pipeline.py).
-- ===========================================================================


-- Q1 - City Market Size: where is the opportunity, saturated vs growing?
SELECT
    city_clean,
    city_tier,
    COUNT(*)                    AS total_restaurants,
    ROUND(AVG(rating), 2)       AS avg_rating,
    ROUND(AVG(cost_for_two), 0) AS avg_cost
FROM restaurants
WHERE city_clean IS NOT NULL
GROUP BY city_clean, city_tier
ORDER BY total_restaurants DESC
LIMIT 20;


-- Q2 - Cuisine Gap Analysis: high-rated but under-supplied cuisines.
SELECT
    cuisine,
    COUNT(DISTINCT rc.name)       AS restaurant_count,
    ROUND(AVG(rc.rating), 2)      AS avg_rating,
    ROUND(AVG(rc.cost_for_two), 0) AS avg_cost
FROM restaurant_cuisines rc
WHERE cuisine NOT IN ('Unknown', '0') AND rc.rating IS NOT NULL
GROUP BY cuisine
HAVING restaurant_count > 50
ORDER BY avg_rating DESC, restaurant_count ASC
LIMIT 20;


-- Q3 - Online Order Adoption by City: low adoption = less delivery competition.
SELECT
    city_clean,
    COUNT(*)                                                          AS total,
    SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END)            AS online_count,
    ROUND(100.0 * SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS online_pct
FROM restaurants
GROUP BY city_clean
HAVING total > 100
ORDER BY online_pct ASC;


-- Q4 - Price Tier Sweet Spot: which band produces the most high-rated places?
SELECT
    price_tier,
    COUNT(*)                                    AS restaurant_count,
    ROUND(AVG(rating), 2)                       AS avg_rating,
    COUNT(CASE WHEN rating >= 4.0 THEN 1 END)   AS high_rated_count,
    ROUND(100.0 * COUNT(CASE WHEN rating >= 4.0 THEN 1 END) / COUNT(*), 1) AS high_rated_pct
FROM restaurants
WHERE price_tier != 'Unknown' AND rating IS NOT NULL
GROUP BY price_tier
ORDER BY avg_rating DESC;


-- Q5 - Tier 2+ City Opportunity: high satisfaction, low density = unmet demand.
-- Note: avg_rating >= 3.8 returned 0 rows (Tier 2+ cities cluster ~3.4-3.5).
-- 3.45 keeps cities above the national Tier 2+ average while still surfacing results.
SELECT
    city_clean,
    COUNT(*)                                                AS restaurant_count,
    ROUND(AVG(rating), 2)                                   AS avg_rating,
    ROUND(AVG(cost_for_two), 0)                             AS avg_cost,
    SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END)   AS online_ready
FROM restaurants
WHERE city_tier = 'Tier 2+' AND rating IS NOT NULL
GROUP BY city_clean
HAVING restaurant_count BETWEEN 50 AND 2000
   AND avg_rating >= 3.45
ORDER BY avg_rating DESC, restaurant_count ASC
LIMIT 15;


-- Q6 - Locality Service Gaps in Bengaluru: high density but low satisfaction.
SELECT
    location,
    COUNT(*)                                                AS restaurants,
    ROUND(AVG(rating), 2)                                   AS avg_rating,
    ROUND(AVG(cost_for_two), 0)                             AS avg_cost,
    SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END)   AS online_count
FROM restaurants
WHERE city_clean = 'Bengaluru' AND rating IS NOT NULL
GROUP BY location
HAVING restaurants >= 30
ORDER BY avg_rating ASC, restaurants DESC
LIMIT 15;


-- Q7 - Competitive Density: city x cuisine combinations, most vs least crowded.
SELECT
    rc.city_clean,
    rc.cuisine,
    COUNT(*)                    AS count,
    ROUND(AVG(rc.rating), 2)    AS avg_rating
FROM restaurant_cuisines rc
WHERE rc.cuisine IN ('North Indian', 'South Indian', 'Chinese', 'Fast Food', 'Biryani')
  AND rc.city_clean IN ('Bengaluru', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Pune')
GROUP BY rc.city_clean, rc.cuisine
ORDER BY rc.city_clean, count DESC;


-- Q8 - Recommendation Matrix: rank cities by a composite opportunity score.
SELECT
    city_clean,
    city_tier,
    COUNT(*)                                                        AS restaurant_count,
    ROUND(AVG(rating), 2)                                           AS avg_rating,
    ROUND(100.0 * SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS online_pct,
    ROUND(AVG(cost_for_two), 0)                                     AS avg_cost,
    ROUND(
        (AVG(rating) * 20)
      + (100.0 * SUM(CASE WHEN has_online_order = 1 THEN 1 ELSE 0 END) / COUNT(*) * 0.3)
      - (COUNT(*) * 0.001)
    , 1)                                                            AS opportunity_score
FROM restaurants
WHERE rating IS NOT NULL
GROUP BY city_clean, city_tier
HAVING restaurant_count >= 50
ORDER BY opportunity_score DESC
LIMIT 20;
