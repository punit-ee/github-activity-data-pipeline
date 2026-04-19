-- Custom data quality test: Ensure all daily aggregations have positive counts

SELECT
    event_date,
    event_type,
    total_events
FROM {{ ref('agg_event_type_daily') }}
WHERE total_events <= 0
    OR unique_actors <= 0
    OR unique_repositories <= 0

