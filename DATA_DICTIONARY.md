# Data Dictionary - GitHub Archive dbt Models

## Table of Contents
- [Staging Models](#staging-models)
- [Mart Models - Core](#mart-models---core)
- [Mart Models - Analytics](#mart-models---analytics)

---

## Staging Models

### stg_github_events
**Description:** Cleaned and enriched GitHub events from raw layer  
**Type:** View  
**Grain:** One row per event (unique on event_id + event_date)  
**Source:** raw.github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| event_id | TEXT | GitHub event identifier | No |
| event_date | DATE | Event date (partition key) | No |
| event_type | TEXT | Type of GitHub event (PushEvent, etc.) | No |
| created_at | TIMESTAMP | Event creation timestamp | No |
| actor_id | TEXT | User/bot who triggered the event | No |
| actor_login | TEXT | GitHub username | No |
| repo_id | TEXT | Repository identifier | Yes |
| repo_name | TEXT | Full repository name (owner/repo) | Yes |
| org_id | TEXT | Organization identifier | Yes |
| org_login | TEXT | Organization name | Yes |
| is_public | BOOLEAN | Public repository flag | No |
| payload | TEXT/JSON | Event payload data | Yes |
| source_file | TEXT | Source file from GitHub Archive | No |
| ingested_at | TIMESTAMP | Raw ingestion timestamp | No |
| updated_at | TIMESTAMP | Last update timestamp | No |
| is_bot | BOOLEAN | Bot detection flag | No |
| event_hour | INTEGER | Hour of day (0-23) | No |
| event_day_of_week | INTEGER | Day of week (1=Mon, 7=Sun) | No |
| event_year | INTEGER | Year of event | No |
| event_month | INTEGER | Month of event | No |
| event_day | INTEGER | Day of month | No |

**Key Features:**
- Bot detection using username patterns
- Time dimension extraction
- Data quality filtering
- NULL handling

---

### stg_actors
**Description:** Deduplicated GitHub actors with activity metrics  
**Type:** View  
**Grain:** One row per unique actor  
**Source:** stg_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| actor_id | TEXT | Unique actor identifier | No |
| actor_login | TEXT | GitHub username | No |
| is_bot | BOOLEAN | Bot identification flag | No |
| first_seen_at | TIMESTAMP | First activity timestamp | No |
| last_seen_at | TIMESTAMP | Latest activity timestamp | No |
| total_events | INTEGER | Total event count | No |
| unique_event_types | INTEGER | Number of different event types | No |
| unique_repositories | INTEGER | Number of different repos contributed to | No |
| active_days | INTEGER | Number of days with activity | No |

**Key Features:**
- Aggregates activity across all events
- Identifies bots
- Tracks activity timeline

---

### stg_repositories
**Description:** Deduplicated GitHub repositories with metrics  
**Type:** View  
**Grain:** One row per unique repository  
**Source:** stg_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| repo_id | TEXT | Unique repository identifier | No |
| repo_name | TEXT | Full repository name | No |
| repo_owner | TEXT | Repository owner (extracted) | No |
| repo_slug | TEXT | Repository name (extracted) | No |
| is_public | BOOLEAN | Public repository flag | No |
| is_org_owned | BOOLEAN | Organization ownership flag | No |
| first_seen_at | TIMESTAMP | First activity timestamp | No |
| last_seen_at | TIMESTAMP | Latest activity timestamp | No |
| total_events | INTEGER | Total event count | No |
| unique_contributors | INTEGER | Number of unique contributors | No |
| unique_event_types | INTEGER | Number of different event types | No |
| active_days | INTEGER | Number of days with activity | No |

**Key Features:**
- Parses owner/repo from full name
- Identifies organization-owned repos
- Activity metrics

---

### stg_organizations
**Description:** Deduplicated GitHub organizations with metrics  
**Type:** View  
**Grain:** One row per unique organization  
**Source:** stg_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| org_id | TEXT | Unique organization identifier | No |
| org_login | TEXT | Organization name | No |
| first_seen_at | TIMESTAMP | First activity timestamp | No |
| last_seen_at | TIMESTAMP | Latest activity timestamp | No |
| total_events | INTEGER | Total event count | No |
| total_repositories | INTEGER | Number of unique repositories | No |
| unique_contributors | INTEGER | Number of unique contributors | No |
| unique_event_types | INTEGER | Number of different event types | No |
| active_days | INTEGER | Number of days with activity | No |

**Key Features:**
- Aggregates org-level metrics
- Tracks repository count
- Activity timeline

---

## Mart Models - Core

### fct_github_events
**Description:** Fact table for all GitHub events  
**Type:** Incremental Table (partitioned by event_date)  
**Grain:** One row per event  
**Source:** stg_github_events, stg_repositories

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| event_id | TEXT | Event identifier | No |
| event_date | DATE | Event date (partition key) | No |
| event_type | TEXT | Event type | No |
| created_at | TIMESTAMP | Event timestamp | No |
| event_hour | INTEGER | Hour (0-23) | No |
| event_day_of_week | INTEGER | Day of week (1-7) | No |
| event_year | INTEGER | Year | No |
| event_month | INTEGER | Month | No |
| event_day | INTEGER | Day | No |
| actor_id | TEXT | Actor identifier | No |
| actor_login | TEXT | Actor username | No |
| is_bot | BOOLEAN | Bot flag | No |
| repo_id | TEXT | Repository identifier | Yes |
| repo_name | TEXT | Full repository name | Yes |
| repo_owner | TEXT | Repository owner | Yes |
| repo_slug | TEXT | Repository slug | Yes |
| org_id | TEXT | Organization identifier | Yes |
| org_login | TEXT | Organization name | Yes |
| is_public | BOOLEAN | Public flag | No |
| payload | TEXT/JSON | Event payload | Yes |
| source_file | TEXT | Source file | No |
| ingested_at | TIMESTAMP | Ingestion timestamp | No |
| dbt_updated_at | TIMESTAMP | dbt transformation timestamp | No |

**Key Features:**
- Incremental materialization (only new dates)
- Partitioned by event_date
- Clustered by event_type, repo_id, actor_id
- Denormalized for fast queries

---

### dim_actors
**Description:** Actor dimension with enriched metrics  
**Type:** Table (full refresh)  
**Grain:** One row per unique actor  
**Source:** stg_actors

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| actor_id | TEXT | Unique identifier | No |
| actor_login | TEXT | Username | No |
| is_bot | BOOLEAN | Bot flag | No |
| first_seen_at | TIMESTAMP | First activity | No |
| last_seen_at | TIMESTAMP | Latest activity | No |
| total_events | INTEGER | Total events | No |
| unique_event_types | INTEGER | Event type diversity | No |
| unique_repositories | INTEGER | Repository diversity | No |
| active_days | INTEGER | Days with activity | No |
| activity_level | TEXT | Classification (low/medium/high/very_high) | No |
| avg_events_per_day | NUMERIC | Average daily events | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

**Activity Levels:**
- `very_high`: >= 10,000 events
- `high`: >= 1,000 events
- `medium`: >= 100 events
- `low`: < 100 events

---

### dim_repositories
**Description:** Repository dimension with popularity metrics  
**Type:** Table (full refresh)  
**Grain:** One row per unique repository  
**Source:** stg_repositories

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| repo_id | TEXT | Unique identifier | No |
| repo_name | TEXT | Full name | No |
| repo_owner | TEXT | Owner | No |
| repo_slug | TEXT | Repository name | No |
| is_public | BOOLEAN | Public flag | No |
| is_org_owned | BOOLEAN | Org ownership flag | No |
| first_seen_at | TIMESTAMP | First activity | No |
| last_seen_at | TIMESTAMP | Latest activity | No |
| total_events | INTEGER | Total events | No |
| unique_contributors | INTEGER | Contributor count | No |
| unique_event_types | INTEGER | Event type diversity | No |
| active_days | INTEGER | Days with activity | No |
| popularity_tier | TEXT | Classification (low/medium/high/viral) | No |
| avg_events_per_day | NUMERIC | Average daily events | No |
| contributor_diversity_pct | NUMERIC | % unique contributors | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

**Popularity Tiers:**
- `viral`: >= 100,000 events
- `high`: >= 10,000 events
- `medium`: >= 1,000 events
- `low`: < 1,000 events

---

### dim_organizations
**Description:** Organization dimension with aggregated metrics  
**Type:** Table (full refresh)  
**Grain:** One row per unique organization  
**Source:** stg_organizations

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| org_id | TEXT | Unique identifier | No |
| org_login | TEXT | Organization name | No |
| first_seen_at | TIMESTAMP | First activity | No |
| last_seen_at | TIMESTAMP | Latest activity | No |
| total_events | INTEGER | Total events | No |
| total_repositories | INTEGER | Repository count | No |
| unique_contributors | INTEGER | Contributor count | No |
| unique_event_types | INTEGER | Event type diversity | No |
| active_days | INTEGER | Days with activity | No |
| avg_events_per_day | NUMERIC | Average daily events | No |
| avg_events_per_repo | NUMERIC | Average events per repo | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

---

## Mart Models - Analytics

### agg_event_type_daily
**Description:** Daily aggregation by event type  
**Type:** Incremental Table  
**Grain:** One row per (event_date, event_type)  
**Source:** fct_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| event_date | DATE | Date | No |
| event_type | TEXT | Event type | No |
| total_events | INTEGER | Total events | No |
| unique_actors | INTEGER | Unique users | No |
| unique_repositories | INTEGER | Unique repos | No |
| unique_organizations | INTEGER | Unique orgs | No |
| bot_events | INTEGER | Events from bots | No |
| human_events | INTEGER | Events from humans | No |
| public_events | INTEGER | Public repo events | No |
| private_events | INTEGER | Private repo events | No |
| distinct_hours_active | INTEGER | Hours with activity | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

**Use Cases:**
- Event type trending
- Bot activity monitoring
- Public vs private analysis

---

### agg_repository_daily
**Description:** Daily aggregation by repository  
**Type:** Incremental Table  
**Grain:** One row per (event_date, repo_id)  
**Source:** fct_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| event_date | DATE | Date | No |
| repo_id | TEXT | Repository identifier | No |
| repo_name | TEXT | Repository name | No |
| repo_owner | TEXT | Owner | No |
| repo_slug | TEXT | Slug | No |
| total_events | INTEGER | Total events | No |
| unique_contributors | INTEGER | Unique contributors | No |
| unique_event_types | INTEGER | Event type diversity | No |
| push_events | INTEGER | Push events | No |
| pull_request_events | INTEGER | PR events | No |
| issue_events | INTEGER | Issue events | No |
| issue_comment_events | INTEGER | Issue comment events | No |
| watch_events | INTEGER | Watch/star events | No |
| fork_events | INTEGER | Fork events | No |
| bot_events | INTEGER | Bot events | No |
| human_events | INTEGER | Human events | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

**Use Cases:**
- Trending repositories
- Repository health metrics
- Activity patterns

---

### agg_actor_daily
**Description:** Daily aggregation by actor  
**Type:** Incremental Table  
**Grain:** One row per (event_date, actor_id)  
**Source:** fct_github_events

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| event_date | DATE | Date | No |
| actor_id | TEXT | Actor identifier | No |
| actor_login | TEXT | Username | No |
| is_bot | BOOLEAN | Bot flag | No |
| total_events | INTEGER | Total events | No |
| unique_repositories | INTEGER | Unique repos | No |
| unique_event_types | INTEGER | Event type diversity | No |
| unique_organizations | INTEGER | Unique orgs | No |
| push_events | INTEGER | Push events | No |
| pull_request_events | INTEGER | PR events | No |
| issue_events | INTEGER | Issue events | No |
| issue_comment_events | INTEGER | Issue comment events | No |
| watch_events | INTEGER | Watch events | No |
| distinct_hours_active | INTEGER | Hours with activity | No |
| dbt_updated_at | TIMESTAMP | Last transformation | No |

**Use Cases:**
- User engagement analysis
- Power user identification
- Activity patterns

---

## Event Types Reference

| Event Type | Category | Description | Code Change |
|------------|----------|-------------|-------------|
| PushEvent | code | Push commits to branch | Yes |
| PullRequestEvent | collaboration | PR opened/closed/merged | Yes |
| IssuesEvent | collaboration | Issue opened/closed | No |
| IssueCommentEvent | collaboration | Comment on issue | No |
| PullRequestReviewEvent | collaboration | PR review submitted | No |
| PullRequestReviewCommentEvent | collaboration | Comment on PR review | No |
| CreateEvent | repository | Branch/tag created | No |
| DeleteEvent | repository | Branch/tag deleted | No |
| ForkEvent | repository | Repository forked | No |
| WatchEvent | engagement | Repository starred | No |
| ReleaseEvent | repository | Release published | No |
| PublicEvent | repository | Made public | No |
| MemberEvent | collaboration | Collaborator added | No |
| CommitCommentEvent | collaboration | Comment on commit | No |
| GollumEvent | documentation | Wiki updated | No |

---

## Data Quality Rules

### Not Null Constraints
- event_id, event_date, event_type, created_at (all models)
- actor_id, actor_login (events and actors)
- Primary keys in all dimension tables

### Unique Constraints
- (event_id, event_date) in fct_github_events
- actor_id, actor_login in dim_actors
- repo_id, repo_name in dim_repositories
- org_id, org_login in dim_organizations

### Referential Integrity
- All actor_ids exist in dim_actors
- All repo_ids exist in dim_repositories
- All org_ids exist in dim_organizations

### Business Rules
- event_date = date(created_at)
- No future events
- All counts >= 0
- Bot detection based on username patterns

---

## Performance Considerations

### Partitioning
- **fct_github_events**: Partitioned by event_date (day granularity)
- **Incremental models**: Load only new dates

### Clustering
- **fct_github_events**: Clustered by (event_type, repo_id, actor_id)

### Materialization Strategy
- **Staging**: Views (always fresh, lightweight)
- **Dimensions**: Tables (full refresh, small size)
- **Facts**: Incremental tables (append-only)
- **Aggregations**: Incremental tables (daily updates)

---

## Refresh Strategy

### Daily Updates
1. **Staging models**: Full refresh (views are always current)
2. **Fact table**: Incremental (new dates only)
3. **Dimensions**: Full refresh (relatively small)
4. **Aggregations**: Incremental (new dates only)

### Full Refresh Scenarios
- Schema changes
- Data quality issues
- Historical data corrections
- Run with: `dbt run --full-refresh`

---

*Last Updated: 2026-04-18*  
*dbt Version: 1.7.9*  
*Database: PostgreSQL 16 / BigQuery*

