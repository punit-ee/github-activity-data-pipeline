-- ============================================================================
-- PostgreSQL Raw Table Setup Script
-- ============================================================================
-- Purpose: Initialize raw.github_events table with partitions and indexes
-- Usage:   psql -d github_archive -f scripts/init_postgres_raw_table.sql
-- ============================================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS raw;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS raw.github_events (
    event_id        TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    event_date      DATE        NOT NULL,

    -- Actor
    actor_id        TEXT,
    actor_login     TEXT,

    -- Repository
    repo_id         TEXT,
    repo_name       TEXT,

    -- Organization
    org_id          TEXT,
    org_login       TEXT,

    -- Event metadata
    is_public       BOOLEAN     NOT NULL DEFAULT TRUE,
    payload         TEXT,

    -- Lineage
    source_file     TEXT        NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Composite PK (must include partition key for partitioned tables)
    PRIMARY KEY (event_id, event_date),

    -- Constraints
    CONSTRAINT chk_event_type_not_empty  CHECK (event_type <> ''),
    CONSTRAINT chk_source_file_not_empty CHECK (source_file <> ''),
    CONSTRAINT chk_event_date_matches_created_at CHECK (event_date = created_at::date)

) PARTITION BY RANGE (event_date);

-- Create partitions (adjust dates as needed)
CREATE TABLE IF NOT EXISTS raw.github_events_2026_01
    PARTITION OF raw.github_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS raw.github_events_2026_02
    PARTITION OF raw.github_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS raw.github_events_2026_03
    PARTITION OF raw.github_events
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE TABLE IF NOT EXISTS raw.github_events_2026_04
    PARTITION OF raw.github_events
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE IF NOT EXISTS raw.github_events_2026_05
    PARTITION OF raw.github_events
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

-- Default partition for unexpected dates
CREATE TABLE IF NOT EXISTS raw.github_events_default
    PARTITION OF raw.github_events DEFAULT;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_github_events_created_at
    ON raw.github_events USING BRIN (created_at)
    WITH (pages_per_range = 128);

CREATE INDEX IF NOT EXISTS idx_github_events_event_type
    ON raw.github_events (event_type, event_date);

CREATE INDEX IF NOT EXISTS idx_github_events_repo
    ON raw.github_events (repo_id, event_date)
    WHERE repo_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_github_events_actor
    ON raw.github_events (actor_login, event_date)
    WHERE actor_login IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_github_events_org
    ON raw.github_events (org_id, event_date)
    WHERE org_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_github_events_source_file
    ON raw.github_events (source_file);

-- Performance tuning
ALTER TABLE raw.github_events SET (
    toast_tuple_target = 8160,
    fillfactor = 90,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Statistics
ALTER TABLE raw.github_events ALTER COLUMN event_type SET STATISTICS 1000;
ALTER TABLE raw.github_events ALTER COLUMN repo_id SET STATISTICS 1000;
ALTER TABLE raw.github_events ALTER COLUMN actor_login SET STATISTICS 1000;

-- Comments
COMMENT ON TABLE raw.github_events IS
    'Raw GitHub Archive events - append-optimized with upsert support. Partitioned monthly.';
COMMENT ON COLUMN raw.github_events.event_id IS
    'GitHub event ID - unique within partition, not globally unique';
COMMENT ON COLUMN raw.github_events.payload IS
    'Raw JSON payload as TEXT - parse in transformation layer';
COMMENT ON COLUMN raw.github_events.event_date IS
    'Partition key - must equal created_at::date';

-- Helper function to create next partition
CREATE OR REPLACE FUNCTION raw.create_next_partition()
RETURNS void AS $$
DECLARE
    next_month date := date_trunc('month', CURRENT_DATE + interval '1 month');
    partition_name text := 'raw.github_events_' || to_char(next_month, 'YYYY_MM');
    start_date text := next_month::text;
    end_date text := (next_month + interval '1 month')::text;
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %s PARTITION OF raw.github_events FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
    RAISE NOTICE 'Created partition % for range [%, %)', partition_name, start_date, end_date;
END;
$$ LANGUAGE plpgsql;

-- Verify setup
DO $$
BEGIN
    RAISE NOTICE 'Setup complete! Table: raw.github_events';
    RAISE NOTICE 'Run this monthly: SELECT raw.create_next_partition();';
END $$;

