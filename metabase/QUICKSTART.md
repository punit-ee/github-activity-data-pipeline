# Metabase Quick Reference

## Start Metabase

```bash
./scripts/start_metabase.sh
```

Access at: http://localhost:3000

## First-Time Setup

### 1. Create Admin Account
- Email: `admin@example.com` (or your email)
- Password: Choose a strong password
- Company: GitHub Archive Analytics

### 2. Add Database Connection

**Manual Setup:**
1. Click "Add a database"
2. Fill in:
   - **Name**: `GitHub Archive`
   - **Database type**: `PostgreSQL`
   - **Host**: `postgres`
   - **Port**: `5432`
   - **Database name**: `github_archive`
   - **Username**: `postgres`
   - **Password**: `postgres`
   - **Additional JDBC options**: `searchPath=marts,staging,raw,public&currentSchema=marts`
3. Click "Save"
4. Wait for schema sync (~30 seconds)

**Automated Setup:**
```bash
python metabase/setup_dashboards.py \
    --url http://localhost:3000 \
    --email admin@example.com \
    --password your-password
```

## Pre-Built Dashboards

The automated setup creates 3 dashboards:

### 1. GitHub Activity Overview
- Total Events (Last 30 Days)
- Daily Event Trend
- Event Type Distribution
- Bot vs Human Activity

### 2. Repository Analytics
- Top 20 Most Active Repositories
- Repository Popularity Distribution

### 3. Developer Activity
- Top 50 Most Active Developers
- Activity by Hour of Day

## Custom SQL Queries

All dashboard SQL queries are in:
```
metabase/dashboard_queries.sql
```

Copy and paste into Metabase → New Question → Native Query

## Common Tasks

### Create a New Question
1. Click "+ New" → "Question"
2. Choose "Native query"
3. Select "GitHub Archive" database
4. Paste SQL from `dashboard_queries.sql`
5. Click "Visualize"
6. Save with a descriptive name

### Add to Dashboard
1. Open question
2. Click "Add to dashboard"
3. Select or create dashboard
4. Resize and position card

### Set Auto-Refresh
1. Open dashboard
2. Click "⚙️" → "Auto-refresh"
3. Select interval (5, 15, or 30 minutes)

## Key Tables

Focus on the `marts` schema:

- **marts.fct_github_events** - All events (event-level detail)
- **marts.agg_event_type_daily** - Daily event type aggregation
- **marts.agg_repository_daily** - Daily repository aggregation
- **marts.agg_actor_daily** - Daily developer aggregation
- **marts.dim_actors** - Developer dimension
- **marts.dim_repositories** - Repository dimension
- **marts.dim_organizations** - Organization dimension

## Useful Filters

Add these as dashboard filters:

1. **Date Range** - `event_date`
2. **Event Type** - `event_type`
3. **Repository** - `repo_name`
4. **Bot Filter** - `is_bot`

## Troubleshooting

### Metabase Won't Start
```bash
docker logs github-archive-metabase
docker restart github-archive-metabase
```

### Can't Connect to Database
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test network
docker exec github-archive-metabase ping postgres
```

### Slow Queries
- Use aggregation tables (`agg_*`) instead of fact table
- Add date filters (`WHERE event_date >= ...`)
- Limit results (`LIMIT 100`)
- Enable query caching in Metabase settings

## Security

For production:
1. Change PostgreSQL password
2. Use reverse proxy with HTTPS
3. Configure SMTP for alerts
4. Set up user roles (Admin, Analyst, Viewer)
5. Enable audit logging

## Backup & Restore

### Backup
```bash
docker exec github-archive-postgres pg_dump -U postgres metabase > metabase_backup.sql
```

### Restore
```bash
docker exec -i github-archive-postgres psql -U postgres metabase < metabase_backup.sql
```

## Resources

- Full Documentation: [metabase/README.md](README.md)
- SQL Queries: [metabase/dashboard_queries.sql](dashboard_queries.sql)
- Metabase Docs: https://www.metabase.com/docs/latest/

