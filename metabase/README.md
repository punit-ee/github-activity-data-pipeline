# Metabase Dashboard Setup

This directory contains Metabase configuration and dashboard definitions for GitHub Archive analytics.

## Quick Start

### 1. Start Metabase

```bash
# Create network if it doesn't exist
docker network create github-archive-network 2>/dev/null || true

# Start PostgreSQL and Metabase
docker compose -f docker-compose.yml -f docker-compose.metabase.yml up -d

# Wait for Metabase to start (check logs)
docker logs -f github-archive-metabase
```

### 2. Initial Setup

1. **Access Metabase**: http://localhost:3000
2. **Create Admin Account**:
   - Email: admin@example.com
   - Password: (choose a strong password)
   - Company name: GitHub Archive Analytics

3. **Add Database Connection**:
   - Click "Add a database"
   - **Name**: GitHub Archive
   - **Database type**: PostgreSQL
   - **Host**: postgres
   - **Port**: 5432
   - **Database name**: github_archive
   - **Username**: postgres
   - **Password**: postgres
   - **Additional JDBC options**: 
     ```
     searchPath=marts,staging,raw,public&currentSchema=marts
     ```
   - Click "Save"

4. **Sync Database Schema**:
   - Metabase will automatically scan your tables
   - Focus on the `marts` schema

## Pre-Built Dashboards

### Dashboard 1: GitHub Activity Overview

**Cards to create:**

1. **Total Events (Last 30 Days)**
   ```sql
   SELECT COUNT(*) as total_events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days';
   ```

2. **Daily Event Trend**
   ```sql
   SELECT 
     event_date,
     COUNT(*) as events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

3. **Event Type Distribution**
   ```sql
   SELECT 
     event_type,
     SUM(total_events) as events
   FROM marts.agg_event_type_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_type
   ORDER BY events DESC
   LIMIT 10;
   ```

4. **Bot vs Human Activity**
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

5. **Active Users Trend**
   ```sql
   SELECT 
     event_date,
     COUNT(DISTINCT actor_id) as unique_actors
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

### Dashboard 2: Repository Analytics

**Cards to create:**

1. **Top 20 Most Active Repositories**
   ```sql
   SELECT 
     repo_name,
     SUM(total_events) as events,
     SUM(unique_contributors) as contributors,
     SUM(push_events) as pushes,
     SUM(pull_request_events) as pull_requests
   FROM marts.agg_repository_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
   GROUP BY repo_name
   ORDER BY events DESC
   LIMIT 20;
   ```

2. **Repository Growth Over Time**
   ```sql
   SELECT 
     event_date,
     COUNT(DISTINCT repo_id) as active_repositories
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

3. **Repository Popularity Distribution**
   ```sql
   SELECT 
     popularity_tier,
     COUNT(*) as repository_count
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

4. **Push vs Pull Request Activity**
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

### Dashboard 3: Developer Activity

**Cards to create:**

1. **Top 50 Most Active Developers**
   ```sql
   SELECT 
     actor_login,
     SUM(total_events) as total_events,
     SUM(unique_repositories) as repositories_contributed,
     SUM(unique_event_types) as event_types
   FROM marts.agg_actor_daily
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
     AND is_bot = false
   GROUP BY actor_login
   ORDER BY total_events DESC
   LIMIT 50;
   ```

2. **Developer Activity Level Distribution**
   ```sql
   SELECT 
     activity_level,
     COUNT(*) as developer_count
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

3. **Daily Active Developers**
   ```sql
   SELECT 
     event_date,
     COUNT(DISTINCT CASE WHEN is_bot = false THEN actor_id END) as human_developers,
     COUNT(DISTINCT CASE WHEN is_bot = true THEN actor_id END) as bots
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
   GROUP BY event_date
   ORDER BY event_date;
   ```

4. **Activity by Hour of Day**
   ```sql
   SELECT 
     event_hour,
     COUNT(*) as events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
   GROUP BY event_hour
   ORDER BY event_hour;
   ```

5. **Activity by Day of Week**
   ```sql
   SELECT 
     event_day_of_week,
     COUNT(*) as events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY event_day_of_week
   ORDER BY event_day_of_week;
   ```

### Dashboard 4: Organization Insights

**Cards to create:**

1. **Top Organizations by Activity**
   ```sql
   SELECT 
     org_login,
     total_events,
     total_repositories,
     last_seen_at
   FROM marts.dim_organizations
   WHERE org_login IS NOT NULL
   ORDER BY total_events DESC
   LIMIT 25;
   ```

2. **Organization vs Individual Activity**
   ```sql
   SELECT 
     CASE WHEN org_id IS NOT NULL THEN 'Organization' ELSE 'Individual' END as type,
     COUNT(*) as events
   FROM marts.fct_github_events
   WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
   GROUP BY CASE WHEN org_id IS NOT NULL THEN 'Organization' ELSE 'Individual' END;
   ```

## Dashboard Configuration Tips

### Visualization Types

- **Line Charts**: Use for time-series (daily trends, activity over time)
- **Bar Charts**: Use for comparisons (event types, top repositories)
- **Pie Charts**: Use for distributions (bot vs human, activity levels)
- **Numbers**: Use for KPIs (total events, active users)
- **Tables**: Use for detailed listings (top repositories, developers)

### Filters to Add

Add these filters to dashboards for interactivity:

1. **Date Range Filter**: 
   - Field: `event_date`
   - Default: Last 30 days
   - Options: Last 7 days, 30 days, 90 days, Custom

2. **Event Type Filter**:
   - Field: `event_type`
   - Allow multiple selections

3. **Repository Filter**:
   - Field: `repo_name`
   - Searchable dropdown

4. **Bot Filter**:
   - Field: `is_bot`
   - Options: All, Bots Only, Humans Only

### Auto-Refresh

For real-time monitoring:
1. Edit Dashboard → Settings
2. Set "Auto-refresh" to 5 or 15 minutes
3. Enable "Fullscreen" mode for display dashboards

## Metabase Management

### Backup Metabase Configuration

```bash
# Backup Metabase database
docker exec github-archive-postgres pg_dump -U postgres metabase > metabase_backup_$(date +%Y%m%d).sql
```

### Restore Metabase Configuration

```bash
# Restore from backup
docker exec -i github-archive-postgres psql -U postgres metabase < metabase_backup_YYYYMMDD.sql
```

### Update Metabase

```bash
# Pull latest version
docker compose -f docker-compose.metabase.yml pull metabase

# Restart with new version
docker compose -f docker-compose.metabase.yml up -d metabase
```

## Security Recommendations

1. **Change Default Credentials**: Update PostgreSQL password in production
2. **Enable HTTPS**: Use reverse proxy (nginx) with SSL certificates
3. **Configure Email**: Set up SMTP for alerts and notifications
4. **User Management**: Create role-based access (Admin, Analyst, Viewer)
5. **Audit Logging**: Enable activity logging in Metabase settings

## Performance Optimization

1. **Database Indexes**: Ensure your fact/dimension tables have proper indexes
2. **Query Caching**: Enable in Metabase Settings → Caching
3. **Result Limits**: Set reasonable limits on large queries
4. **Scheduled Refreshes**: Pre-compute expensive queries during off-peak hours

## Troubleshooting

### Metabase Won't Start

```bash
# Check logs
docker logs github-archive-metabase

# Restart container
docker restart github-archive-metabase
```

### Can't Connect to PostgreSQL

- Verify network: `docker network inspect github-archive-network`
- Check PostgreSQL is running: `docker ps | grep postgres`
- Test connection: `docker exec github-archive-metabase ping postgres`

### Slow Queries

- Check query execution plan in PostgreSQL
- Add indexes on frequently filtered columns
- Use aggregation tables instead of fact table for dashboards
- Enable Metabase query caching

## Resources

- [Metabase Documentation](https://www.metabase.com/docs/latest/)
- [SQL Best Practices](https://www.metabase.com/learn/sql-questions/)
- [Dashboard Design Guide](https://www.metabase.com/learn/dashboards/)

