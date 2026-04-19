# Consolidated Metabase Dashboards

Instead of creating 6 separate dashboards, this guide shows how to create **2 comprehensive dashboards** that contain all the important widgets organized logically.

## Overview

- **Dashboard 1: Executive Overview** - High-level metrics and trends for stakeholders
- **Dashboard 2: Technical Deep Dive** - Detailed analytics for data analysts and engineers

---

## Dashboard 1: Executive Overview 📊

**Purpose**: High-level GitHub activity insights for leadership and stakeholders

### Layout & Widgets

#### Row 1: Key Metrics (Big Numbers)
1. **Total Events (Last 30 Days)** - Number card
   ```sql
   SELECT COUNT(*) as total_events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days';
   ```

2. **Active Developers (Last 7 Days)** - Number card
   ```sql
   SELECT COUNT(DISTINCT actor_id) as active_developers
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
     AND is_bot = false;
   ```

3. **Active Repositories (Last 7 Days)** - Number card
   ```sql
   SELECT COUNT(DISTINCT repo_id) as active_repos
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days';
   ```

4. **Total Organizations** - Number card
   ```sql
   SELECT COUNT(*) as total_orgs
   FROM marts.dim_organizations
   WHERE org_login IS NOT NULL;
   ```

#### Row 2: Activity Trends
5. **Daily Event Trend (Last 90 Days)** - Line chart
   ```sql
   SELECT
     event_date,
     COUNT(*) as total_events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

6. **Bot vs Human Activity Trend** - Area chart (stacked)
   ```sql
   SELECT
     event_date,
     SUM(bot_events) as bot_events,
     SUM(human_events) as human_events
   FROM marts.agg_event_type_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

#### Row 3: Activity Breakdown
7. **Event Type Distribution (Last 30 Days)** - Pie chart or Bar chart
   ```sql
   SELECT
     event_type,
     SUM(total_events) as events,
     ROUND(100.0 * SUM(total_events) / SUM(SUM(total_events)) OVER (), 2) as percentage
   FROM marts.agg_event_type_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_type
   ORDER BY events DESC
   LIMIT 10;
   ```

8. **Public vs Private Events** - Stacked area chart
   ```sql
   SELECT
     event_date,
     SUM(public_events) as public_events,
     SUM(private_events) as private_events
   FROM marts.agg_event_type_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

#### Row 4: Top Performers
9. **Top 20 Most Active Repositories (Last 7 Days)** - Table
   ```sql
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
   ```

10. **Top 25 Most Active Developers (Last 7 Days)** - Table
    ```sql
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
    ```

#### Row 5: Organization & Repository Insights
11. **Top Organizations by Activity** - Table
    ```sql
    SELECT
      org_login,
      total_events,
      total_repositories,
      ROUND(DATE_PART('day', CURRENT_TIMESTAMP - last_seen_at)) as days_since_activity
    FROM marts.dim_organizations
    WHERE org_login IS NOT NULL
    ORDER BY total_events DESC
    LIMIT 15;
    ```

12. **Repository Popularity Distribution** - Pie chart
    ```sql
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
    ```

#### Row 6: Trending
13. **Trending Repositories (Highest Growth)** - Table
    ```sql
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
    ```

### Dashboard Filters (Apply to All Cards)
- **Date Range**: Last 7/30/90 days (default: 30)
- **Event Type**: All/Specific types
- **Exclude Bots**: Yes/No toggle

---

## Dashboard 2: Technical Deep Dive 🔧

**Purpose**: Detailed analytics for developers, data engineers, and analysts

### Layout & Widgets

#### Row 1: Data Quality & Freshness
1. **Data Freshness Status** - Table
   ```sql
   SELECT
     MAX(event_date) as latest_event_date,
     MAX(ingested_at) as latest_ingestion,
     ROUND(DATE_PART('hour', CURRENT_TIMESTAMP - MAX(ingested_at))::numeric, 1) as hours_since_ingestion,
     COUNT(DISTINCT event_date) as days_available
   FROM marts.fct_github_events;
   ```

2. **Daily Record Counts (Last 30 Days)** - Bar chart
   ```sql
   SELECT
     event_date,
     COUNT(*) as record_count
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

3. **Null Value Analysis** - Table
   ```sql
   SELECT
     COUNT(*) as total_records,
     SUM(CASE WHEN actor_id IS NULL THEN 1 ELSE 0 END) as null_actor_id,
     SUM(CASE WHEN repo_id IS NULL THEN 1 ELSE 0 END) as null_repo_id,
     SUM(CASE WHEN org_id IS NULL THEN 1 ELSE 0 END) as null_org_id,
     ROUND(100.0 * SUM(CASE WHEN org_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as org_coverage_pct
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days';
   ```

#### Row 2: Activity Patterns (Time-Based)
4. **Hourly Activity Pattern (Heatmap)** - Pivot table or Heatmap
   ```sql
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
   ```

5. **Activity by Hour of Day** - Line chart
   ```sql
   SELECT
     event_hour,
     COUNT(*) as events,
     COUNT(DISTINCT actor_id) as unique_actors
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
     AND is_bot = false
   GROUP BY event_hour
   ORDER BY event_hour;
   ```

6. **Activity by Day of Week** - Bar chart
   ```sql
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
   ```

#### Row 3: Event Type Analysis
7. **Event Type Trend Over Time** - Multi-line chart
   ```sql
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
   ```

8. **Event Type Engagement Metrics** - Table
   ```sql
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
   ```

9. **Event Type Coverage** - Table
   ```sql
   SELECT
     event_type,
     COUNT(*) as record_count,
     MIN(event_date) as first_seen,
     MAX(event_date) as last_seen,
     COUNT(DISTINCT event_date) as days_active
   FROM marts.fct_github_events
   GROUP BY event_type
   ORDER BY record_count DESC;
   ```

#### Row 4: Developer Analytics
10. **Developer Activity Level Distribution** - Pie chart
    ```sql
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
    ```

11. **New vs Returning Developers** - Area chart (stacked)
    ```sql
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
    ```

12. **Daily Active Developers Trend** - Multi-line chart
    ```sql
    SELECT
      event_date,
      COUNT(DISTINCT CASE WHEN is_bot = false THEN actor_id END) as human_developers,
      COUNT(DISTINCT CASE WHEN is_bot = true THEN actor_id END) as bots,
      COUNT(DISTINCT actor_id) as total_actors
    FROM marts.fct_github_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY event_date
    ORDER BY event_date;
    ```

#### Row 5: Repository Deep Dive
13. **Repository Growth Over Time** - Line chart
    ```sql
    SELECT
      event_date,
      COUNT(DISTINCT repo_id) as active_repositories,
      COUNT(DISTINCT CASE WHEN is_public THEN repo_id END) as public_repos,
      COUNT(DISTINCT CASE WHEN NOT is_public THEN repo_id END) as private_repos
    FROM marts.fct_github_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY event_date
    ORDER BY event_date;
    ```

14. **Activity Type Breakdown by Repo** - Stacked area chart
    ```sql
    SELECT
      event_date,
      SUM(push_events) as pushes,
      SUM(pull_request_events) as pull_requests,
      SUM(issue_events) as issues
    FROM marts.agg_repository_daily
    WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY event_date
    ORDER BY event_date;
    ```

15. **Top Repository Owners** - Table
    ```sql
    SELECT
      repo_owner,
      COUNT(DISTINCT repo_id) as repositories,
      SUM(total_events) as total_events,
      ROUND(SUM(total_events)::numeric / COUNT(DISTINCT repo_id), 2) as avg_events_per_repo
    FROM marts.dim_repositories
    GROUP BY repo_owner
    ORDER BY total_events DESC
    LIMIT 20;
    ```

#### Row 6: Organization Analytics
16. **Organization vs Individual Activity** - Pie chart
    ```sql
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
    ```

17. **Organization Activity Trend** - Line chart
    ```sql
    SELECT
      event_date,
      COUNT(DISTINCT org_id) as active_organizations,
      COUNT(*) as org_events
    FROM marts.fct_github_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
      AND org_id IS NOT NULL
    GROUP BY event_date
    ORDER BY event_date;
    ```

18. **Organizations by Repository Count** - Bar chart
    ```sql
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
    ```

### Dashboard Filters (Apply to All Cards)
- **Date Range**: Last 7/30/90 days (default: 30)
- **Event Type**: Multi-select dropdown
- **Is Bot**: True/False/All
- **Repository Name**: Searchable dropdown (optional filter)

---

## Setup Instructions

### Step 1: Create Dashboard 1 (Executive Overview)
1. In Metabase, click **"New" → "Dashboard"**
2. Name: **"GitHub Archive - Executive Overview"**
3. Description: **"High-level GitHub activity insights"**
4. Add each query as a new question (SQL → Native query)
5. Choose appropriate visualization for each
6. Arrange widgets in rows as shown above
7. Add dashboard filters

### Step 2: Create Dashboard 2 (Technical Deep Dive)
1. Click **"New" → "Dashboard"**
2. Name: **"GitHub Archive - Technical Deep Dive"**
3. Description: **"Detailed analytics and data quality metrics"**
4. Add each query as a new question
5. Choose appropriate visualization
6. Arrange in organized rows
7. Add dashboard filters

### Step 3: Configure Filters
1. Click **"Edit Dashboard" → "Add Filter"**
2. For Date Range:
   - Type: **"Date filter"**
   - Connect to all date fields
   - Set default: **"Previous 30 days"**
3. For Event Type:
   - Type: **"Text or Category"**
   - Connect to `event_type` fields
   - Allow multiple selections
4. Save filters

### Step 4: Set Auto-Refresh (Optional)
1. Edit Dashboard → Settings
2. Set **"Auto-refresh"**: 15 minutes
3. Enable for live monitoring

---

## Advantages of 2 Dashboards vs 6

✅ **Easier Navigation** - Less clicking between dashboards
✅ **Better Context** - Related metrics are visible together
✅ **Faster Loading** - Modern browsers handle single-page dashboards well
✅ **Clear Separation** - Executive vs Technical audience
✅ **Simpler Maintenance** - Fewer dashboards to update
✅ **Better Storytelling** - Logical flow of information

---

## Tips for Dashboard Organization

1. **Use Row Headers**: Add text cards to label each section
2. **Consistent Sizing**: Keep similar widgets the same size
3. **Color Coding**: Use consistent colors for bot/human, public/private
4. **Tooltips**: Add descriptions to complex queries
5. **Mobile Friendly**: Test on smaller screens
6. **Export Options**: Enable CSV/PNG export for sharing

---

## Next Steps

1. ✅ Create the 2 dashboards using queries above
2. 🎨 Customize colors and visualizations to match your brand
3. 📧 Set up email subscriptions for daily/weekly reports
4. 🔔 Configure alerts for anomalies (e.g., sudden activity drops)
5. 👥 Share with team and gather feedback
6. 🔄 Iterate based on usage patterns

Enjoy your streamlined dashboard experience! 🚀

