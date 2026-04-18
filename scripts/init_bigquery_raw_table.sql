-- ============================================================================
-- BigQuery Raw Table Setup Script
-- ============================================================================
-- Purpose: Initialize raw.github_events table with partitioning and clustering
-- Usage:   bq query --use_legacy_sql=false < scripts/init_bigquery_raw_table.sql
-- ============================================================================

-- Note: Dataset must be created first via CLI:
-- bq mk --dataset --location=US raw

CREATE TABLE IF NOT EXISTS `raw.github_events` (
    event_id        STRING      NOT NULL,
    event_type      STRING      NOT NULL,
    created_at      TIMESTAMP   NOT NULL,

    -- Actor
    actor_id        STRING,
    actor_login     STRING,

    -- Repository
    repo_id         STRING,
    repo_name       STRING,

    -- Organization
    org_id          STRING,
    org_login       STRING,

    -- Event metadata
    is_public       BOOL        NOT NULL,
    payload         JSON,

    -- Lineage tracking
    source_file     STRING      NOT NULL,
    ingested_at     TIMESTAMP   NOT NULL,
    updated_at      TIMESTAMP   NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY event_type, repo_id, actor_login
OPTIONS (
    description = '''Raw GitHub Archive events from https://www.gharchive.org

    Partitioning: Daily by created_at (automatic, zero maintenance)
    Clustering: event_type, repo_id, actor_login (optimized for analytics)
    Upsert Pattern: MERGE with partition filter (see scratch_28.sql Section 5)

    CRITICAL: Always include DATE(created_at) filter to avoid full table scans!
    ''',
    require_partition_filter = true,
    partition_expiration_days = NULL,
    labels = [("env", "production"), ("layer", "raw"), ("source", "github_archive")]
);

