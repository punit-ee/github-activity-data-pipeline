-- ============================================================================
-- CONSOLIDATED DASHBOARD QUERIES
-- Quick reference for 2-dashboard setup
-- ============================================================================

-- ============================================================================
-- DASHBOARD 1: EXECUTIVE OVERVIEW
-- Total widgets: 13
-- ============================================================================

-- 1. Total Events (Last 30 Days) - NUMBER
SELECT COUNT(*) as total_events
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days';

-- 2. Active Developers (Last 7 Days) - NUMBER
SELECT COUNT(DISTINCT actor_id) as active_developers
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
  AND is_bot = false;

-- 3. Active Repositories (Last 7 Days) - NUMBER
SELECT COUNT(DISTINCT repo_id) as active_repos
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days';

-- 4. Total Organizations - NUMBER
SELECT COUNT(*) as total_orgs
FROM marts.dim_organizations
WHERE org_login IS NOT NULL;    

-- 5. Daily Event Trend (Last 90 Days) - LINE CHART
SELECT
  event_date,
  COUNT(*) as total_events
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY event_date
ORDER BY event_date;

    -- 6. Bot vs Human Activity Trend - AREA CHART (STACKED)
SELECT
  event_date,
  SUM(bot_events) as bot_events,
  SUM(human_events) as human_events
FROM marts.agg_event_type_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_date
ORDER BY event_date;

-- 7. Event Type Distribution (Last 30 Days) - PIE or BAR CHART
SELECT
  event_type,
  SUM(total_events) as events,
  ROUND(100.0 * SUM(total_events) / SUM(SUM(total_events)) OVER (), 2) as percentage
FROM marts.agg_event_type_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_type
ORDER BY events DESC
LIMIT 10;

-- 8. Public vs Private Events - STACKED AREA CHART
SELECT
  event_date,
  SUM(public_events) as public_events,
  SUM(private_events) as private_events
FROM marts.agg_event_type_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_date
ORDER BY event_date;

-- 9. Top 20 Most Active Repositories (Last 7 Days) - TABLE
SELECT
  repo_name,
  SUM(total_events) as total_events,
  SUM(unique_contributors) as contributors,
  SUM(push_events) as pushes,
  SUM(pull_request_events) as pull_requests
FROM marts.agg_repository_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY repo_name
ORDER BY total_events DESC
LIMIT 20;

-- 10. Top 25 Most Active Developers (Last 7 Days) - TABLE
SELECT
  actor_login,
  SUM(total_events) as total_events,
  SUM(unique_repositories) as repositories_contributed,
  SUM(unique_event_types) as event_variety
FROM marts.agg_actor_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
  AND is_bot = false
GROUP BY actor_login
ORDER BY total_events DESC
LIMIT 25;

-- 11. Top Organizations by Activity - TABLE
SELECT
  org_login,
  total_events,
  total_repositories,
  ROUND(DATE_PART('day', CURRENT_TIMESTAMP - last_seen_at)) as days_since_activity
FROM marts.dim_organizations
WHERE org_login IS NOT NULL
ORDER BY total_events DESC
LIMIT 15;

-- 12. Repository Popularity Distribution - PIE CHART
SELECT
  popularity_tier,
  COUNT(*) as repository_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM marts.dim_repositories
GROUP BY popularity_tier
ORDER BY
  CASE popularity_tier
    WHEN 'viral' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END;

-- 13. Trending Repositories (Highest Growth) - TABLE
WITH current_week AS (
  SELECT repo_id, SUM(total_events) as events
  FROM marts.agg_repository_daily
  WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY repo_id
),
previous_week AS (
  SELECT repo_id, SUM(total_events) as events
  FROM marts.agg_repository_daily
  WHERE event_date >= CURRENT_DATE - INTERVAL '14 days'
    AND event_date < CURRENT_DATE - INTERVAL '7 days'
  GROUP BY repo_id
)
SELECT
  r.repo_name,
  c.events as current_week_events,
  COALESCE(p.events, 0) as previous_week_events,
  c.events - COALESCE(p.events, 0) as growth,
  ROUND(100.0 * (c.events - COALESCE(p.events, 0)) / NULLIF(p.events, 0), 2) as growth_percentage
FROM current_week c
LEFT JOIN previous_week p ON c.repo_id = p.repo_id
JOIN marts.dim_repositories r ON c.repo_id = r.repo_id
WHERE c.events >= 10
ORDER BY growth DESC
LIMIT 15;


-- ============================================================================
-- DASHBOARD 2: TECHNICAL DEEP DIVE
-- Total widgets: 18
-- ============================================================================

-- 1. Data Freshness Status - TABLE
SELECT
  MAX(event_date) as latest_event_date,
  MAX(ingested_at) as latest_ingestion,
  ROUND(DATE_PART('hour', CURRENT_TIMESTAMP - MAX(ingested_at))::numeric, 1) as hours_since_ingestion,
  COUNT(DISTINCT event_date) as days_available
FROM marts.fct_github_events;

-- 2. Daily Record Counts (Last 30 Days) - BAR CHART
SELECT
  event_date,
  COUNT(*) as record_count
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_date
ORDER BY event_date;

-- 3. Null Value Analysis - TABLE
SELECT
  COUNT(*) as total_records,
  SUM(CASE WHEN actor_id IS NULL THEN 1 ELSE 0 END) as null_actor_id,
  SUM(CASE WHEN repo_id IS NULL THEN 1 ELSE 0 END) as null_repo_id,
  SUM(CASE WHEN org_id IS NULL THEN 1 ELSE 0 END) as null_org_id,
  ROUND(100.0 * SUM(CASE WHEN org_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as org_coverage_pct
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days';

-- 4. Hourly Activity Pattern (Heatmap) - PIVOT TABLE or HEATMAP
SELECT
  event_hour,
  event_day_of_week,
  CASE event_day_of_week
    WHEN 0 THEN 'Sunday'
    WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday'
    WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday'
    WHEN 5 THEN 'Friday'
    WHEN 6 THEN 'Saturday'
  END as day_name,
  COUNT(*) as events
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_hour, event_day_of_week
ORDER BY event_day_of_week, event_hour;

-- 5. Activity by Hour of Day - LINE CHART
SELECT
  event_hour,
  COUNT(*) as events,
  COUNT(DISTINCT actor_id) as unique_actors
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
  AND is_bot = false
GROUP BY event_hour
ORDER BY event_hour;

-- 6. Activity by Day of Week - BAR CHART
SELECT
  event_day_of_week,
  CASE event_day_of_week
    WHEN 0 THEN 'Sunday'
    WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday'
    WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday'
    WHEN 5 THEN 'Friday'
    WHEN 6 THEN 'Saturday'
  END as day_name,
  COUNT(*) as events,
  COUNT(DISTINCT actor_id) as unique_actors
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
  AND is_bot = false
GROUP BY event_day_of_week
ORDER BY event_day_of_week;

-- 7. Event Type Trend Over Time - MULTI-LINE CHART
SELECT
  event_date,
  event_type,
  SUM(total_events) as events
FROM marts.agg_event_type_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
  AND event_type IN ('PushEvent', 'PullRequestEvent', 'IssuesEvent',
                      'WatchEvent', 'ForkEvent', 'CreateEvent')
GROUP BY event_date, event_type
ORDER BY event_date, event_type;

-- 8. Event Type Engagement Metrics - TABLE
SELECT
  event_type,
  SUM(total_events) as total_events,
  SUM(unique_actors) as unique_actors,
  SUM(unique_repositories) as unique_repositories,
  ROUND(SUM(total_events)::numeric / NULLIF(SUM(unique_actors), 0), 2) as events_per_actor,
  ROUND(SUM(total_events)::numeric / NULLIF(SUM(unique_repositories), 0), 2) as events_per_repo
FROM marts.agg_event_type_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_type
ORDER BY total_events DESC;

-- 9. Event Type Coverage - TABLE
SELECT
  event_type,
  COUNT(*) as record_count,
  MIN(event_date) as first_seen,
  MAX(event_date) as last_seen,
  COUNT(DISTINCT event_date) as days_active
FROM marts.fct_github_events
GROUP BY event_type
ORDER BY record_count DESC;

-- 10. Developer Activity Level Distribution - PIE CHART
SELECT
  activity_level,
  COUNT(*) as developer_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM marts.dim_actors
WHERE is_bot = false
GROUP BY activity_level
ORDER BY
  CASE activity_level
    WHEN 'very_high' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END;

-- 11. New vs Returning Developers - AREA CHART (STACKED)
WITH first_activity AS (
  SELECT
    actor_id,
    MIN(event_date) as first_seen
  FROM marts.fct_github_events
  GROUP BY actor_id
)
SELECT
  e.event_date,
  COUNT(DISTINCT CASE WHEN f.first_seen = e.event_date THEN e.actor_id END) as new_developers,
  COUNT(DISTINCT CASE WHEN f.first_seen < e.event_date THEN e.actor_id END) as returning_developers
FROM marts.fct_github_events e
JOIN first_activity f ON e.actor_id = f.actor_id
WHERE e.event_date >= CURRENT_DATE - INTERVAL '30 days'
  AND e.is_bot = false
GROUP BY e.event_date
ORDER BY e.event_date;

-- 12. Daily Active Developers Trend - MULTI-LINE CHART
SELECT
  event_date,
  COUNT(DISTINCT CASE WHEN is_bot = false THEN actor_id END) as human_developers,
  COUNT(DISTINCT CASE WHEN is_bot = true THEN actor_id END) as bots,
  COUNT(DISTINCT actor_id) as total_actors
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY event_date
ORDER BY event_date;

-- 13. Repository Growth Over Time - LINE CHART
SELECT
  event_date,
  COUNT(DISTINCT repo_id) as active_repositories,
  COUNT(DISTINCT CASE WHEN is_public THEN repo_id END) as public_repos,
  COUNT(DISTINCT CASE WHEN NOT is_public THEN repo_id END) as private_repos
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY event_date
ORDER BY event_date;

-- 14. Activity Type Breakdown by Repo - STACKED AREA CHART
SELECT
  event_date,
  SUM(push_events) as pushes,
  SUM(pull_request_events) as pull_requests,
  SUM(issue_events) as issues
FROM marts.agg_repository_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY event_date
ORDER BY event_date;

-- 15. Top Repository Owners - TABLE
SELECT
  repo_owner,
  COUNT(DISTINCT repo_id) as repositories,
  SUM(total_events) as total_events,
  ROUND(SUM(total_events)::numeric / COUNT(DISTINCT repo_id), 2) as avg_events_per_repo
FROM marts.dim_repositories
GROUP BY repo_owner
ORDER BY total_events DESC
LIMIT 20;

-- 16. Organization vs Individual Activity - PIE CHART
SELECT
  CASE
    WHEN org_id IS NOT NULL THEN 'Organization'
    ELSE 'Individual'
  END as contributor_type,
  COUNT(*) as events,
  COUNT(DISTINCT actor_id) as unique_contributors,
  COUNT(DISTINCT repo_id) as unique_repositories
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY CASE WHEN org_id IS NOT NULL THEN 'Organization' ELSE 'Individual' END;

-- 17. Organization Activity Trend - LINE CHART
SELECT
  event_date,
  COUNT(DISTINCT org_id) as active_organizations,
  COUNT(*) as org_events
FROM marts.fct_github_events
WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
  AND org_id IS NOT NULL
GROUP BY event_date
ORDER BY event_date;

-- 18. Organizations by Repository Count - BAR CHART
SELECT
  CASE
    WHEN total_repositories >= 100 THEN '100+'
    WHEN total_repositories >= 50 THEN '50-99'
    WHEN total_repositories >= 20 THEN '20-49'
    WHEN total_repositories >= 10 THEN '10-19'
    ELSE '1-9'
  END as repo_count_bucket,
  COUNT(*) as organization_count
FROM marts.dim_organizations
GROUP BY
  CASE
    WHEN total_repositories >= 100 THEN '100+'
    WHEN total_repositories >= 50 THEN '50-99'
    WHEN total_repositories >= 20 THEN '20-49'
    WHEN total_repositories >= 10 THEN '10-19'
    ELSE '1-9'
  END
ORDER BY MIN(total_repositories) DESC;

