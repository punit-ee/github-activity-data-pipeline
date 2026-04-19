-- Create Metabase application database
-- This database stores Metabase configuration, users, dashboards, etc.

CREATE DATABASE IF NOT EXISTS metabase;
GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;

\c metabase;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO postgres;

-- Log initialization
SELECT 'Metabase database initialized successfully' AS status;

