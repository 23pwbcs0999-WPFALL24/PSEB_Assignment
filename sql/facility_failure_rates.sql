SELECT
        facility_type,
        COUNT(*) AS completed_inspections,
        SUM(failed) AS failures,
        ROUND(100.0 * SUM(failed) / COUNT(*), 1) AS failure_rate_pct
    FROM routine_inspections
    WHERE facility_type IS NOT NULL
    GROUP BY facility_type
    HAVING COUNT(*) >= 50
    ORDER BY 1.0 * SUM(failed) / COUNT(*) DESC,
             completed_inspections DESC,
             facility_type
    LIMIT 10;
