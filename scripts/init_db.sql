-- Initialize GitHub Archive database

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- Create github_events table
CREATE TABLE IF NOT EXISTS public.github_events (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    actor JSONB,
    repo JSONB,
    payload JSONB,
    public BOOLEAN,
    created_at TIMESTAMP,
    org JSONB,
    raw_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_github_events_type ON public.github_events(type);
CREATE INDEX IF NOT EXISTS idx_github_events_created_at ON public.github_events(created_at);
CREATE INDEX IF NOT EXISTS idx_github_events_ingested_at ON public.github_events(ingested_at);

-- Create index on actor login
CREATE INDEX IF NOT EXISTS idx_github_events_actor_login ON public.github_events((actor->>'login'));

-- Create index on repo name
CREATE INDEX IF NOT EXISTS idx_github_events_repo_name ON public.github_events((repo->>'name'));

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'GitHub Archive database initialized successfully!';
END $$;

