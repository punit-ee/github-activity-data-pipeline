-- Custom test: Ensure no future events in the data

SELECT
    event_id,
    created_at,
    event_date
FROM {{ ref('stg_github_events') }}
WHERE created_at > CURRENT_TIMESTAMP
    OR event_date > CURRENT_DATE

