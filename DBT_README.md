# dbt Models - GitHub Archive Data Pipeline

## Overview

This dbt project implements the **conform/curate layers** for the GitHub Archive data pipeline. It transforms raw event data into clean, tested, and documented analytical models.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Raw Layer (PostgreSQL/BigQuery)                            │
│    └── raw.github_events (partitioned, billions of rows)    │
│                        ↓                                    │
│  Staging Layer (Conform) - Views                            │
│    ├── stg_github_events (cleaned, enriched)                │
│    ├── stg_actors (deduplicated users)                      │
│    ├── stg_repositories (deduplicated repos)                │
│    └── stg_organizations (deduplicated orgs)                │
│                        ↓                                    │
│  Marts Layer (Curate) - Tables                              │
│    ├── Core (dimensional model)                             │
│    │   ├── fct_github_events (fact table)                   │
│    │   ├── dim_actors (dimension)                           │
│    │   ├── dim_repositories (dimension)                     │
│    │   └── dim_organizations (dimension)                    │
│    └── Analytics (aggregations)                             │
│        ├── agg_event_type_daily                             │
│        ├── agg_repository_daily                             │
│        └── agg_actor_daily                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── dbt_project.yml          # dbt project configuration
├── profiles.yml             # Connection profiles (Postgres/BigQuery)
├── packages.yml             # dbt package dependencies
├── dbt_models/
│   ├── staging/             # Conform layer (views)
│   │   ├── sources.yml      # Source definitions
│   │   ├── schema.yml       # Model documentation & tests
│   │   ├── stg_github_events.sql
│   │   ├── stg_actors.sql
│   │   ├── stg_repositories.sql
│   │   └── stg_organizations.sql
│   └── marts/               # Curate layer (tables)
│       ├── schema.yml       # Model documentation & tests
│       ├── core/            # Dimensional models
│       │   ├── fct_github_events.sql
│       │   ├── dim_actors.sql
│       │   ├── dim_repositories.sql
│       │   └── dim_organizations.sql
│       └── analytics/       # Aggregations
│           ├── agg_event_type_daily.sql
│           ├── agg_repository_daily.sql
│           └── agg_actor_daily.sql
├── dbt_macros/              # Custom macros & tests
├── dbt_tests/               # Custom data tests
└── dbt_docs/                # Generated documentation
```

## Features

### ✅ Best Practices Implemented

1. **Layered Architecture**
   - Raw → Staging (conform) → Marts (curate)
   - Clear separation of concerns
   - Reusable staging models

2. **Data Quality**
   - Comprehensive dbt tests (not_null, unique, relationships)
   - Custom data quality macros
   - Source freshness checks
   - Referential integrity validation

3. **Performance**
   - Incremental models for large tables
   - Partitioning by date
   - Clustering on key dimensions
   - Efficient aggregations

4. **Documentation**
   - Model-level documentation
   - Column-level descriptions
   - Data lineage tracking
   - Auto-generated docs

5. **Testing**
   - Schema tests (YAML)
   - Custom tests (macros)
   - Data quality tests (dbt_expectations)
   - Anomaly detection

6. **Production Ready**
   - Docker support
   - Multi-environment profiles
   - CI/CD friendly
   - Airflow integration

## Quick Start

### Local Development

1. **Install dbt**
   ```bash
   pip install dbt-core dbt-postgres
   ```

2. **Install dependencies**
   ```bash
   dbt deps
   ```

3. **Test connection**
   ```bash
   dbt debug --profiles-dir .
   ```

4. **Run models**
   ```bash
   # Run all models
   dbt run --profiles-dir .
   
   # Run specific layer
   dbt run --select staging.*
   dbt run --select marts.*
   
   # Run specific model
   dbt run --select stg_github_events
   ```

5. **Run tests**
   ```bash
   # Test all models
   dbt test --profiles-dir .
   
   # Test specific model
   dbt test --select stg_github_events
   ```

6. **Generate documentation**
   ```bash
   dbt docs generate --profiles-dir .
   dbt docs serve --profiles-dir . --port 8080
   ```

### Docker (Production)

1. **Build dbt image**
   ```bash
   docker build -f Dockerfile.dbt -t github-archive-dbt:latest .
   ```

2. **Run with docker-compose**
   ```bash
   # Start dbt container
   docker-compose -f docker-compose.dbt.yml up -d
   
   # Run dbt commands
   docker-compose -f docker-compose.dbt.yml run dbt dbt run
   docker-compose -f docker-compose.dbt.yml run dbt dbt test
   ```

3. **Integrate with existing stack**
   ```bash
   # Ensure network exists
   docker network create github-archive-network
   
   # Start postgres (if not running)
   docker-compose -f docker-compose.yml up -d postgres
   
   # Run dbt
   docker-compose -f docker-compose.dbt.yml run dbt dbt run --target docker
   ```

## Configuration

### Environment Variables

**PostgreSQL (Local/Docker)**
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_DATABASE=github_archive
```

**BigQuery (Production)**
```bash
export GCP_PROJECT_ID=your-project-id
export BIGQUERY_LOCATION=US
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/keyfile.json
```

### Profiles

The project supports multiple targets:

- `postgres` - Local PostgreSQL development
- `docker` - Docker PostgreSQL (connects to postgres service)
- `bigquery` - Production BigQuery

Switch targets:
```bash
dbt run --target postgres
dbt run --target docker
dbt run --target bigquery
```

## Models

### Staging Layer (Conform)

**Purpose:** Clean and standardize raw data

- **stg_github_events**: Cleaned events with bot detection, time dimensions
- **stg_actors**: Deduplicated users with activity metrics
- **stg_repositories**: Deduplicated repos with popularity metrics
- **stg_organizations**: Deduplicated orgs with aggregated stats

**Materialization:** Views (always fresh)

### Marts Layer (Curate)

**Purpose:** Production-ready analytics models

#### Core (Dimensional Model)

- **fct_github_events**: Fact table with denormalized dimensions
- **dim_actors**: Actor dimension with activity levels
- **dim_repositories**: Repository dimension with popularity tiers
- **dim_organizations**: Organization dimension with metrics

**Materialization:** Tables (fast queries)

#### Analytics (Aggregations)

- **agg_event_type_daily**: Daily event type trends
- **agg_repository_daily**: Daily repository activity
- **agg_actor_daily**: Daily user engagement

**Materialization:** Incremental tables (efficient updates)

## Testing

### Built-in Tests

```yaml
tests:
  - not_null
  - unique
  - accepted_values
  - relationships
```

### Custom Tests

```sql
-- Event date matches created_at
{{ test_event_date_matches_created_at(...) }}

-- No orphaned references
{{ test_no_orphaned_references(...) }}

-- Data recency check
{{ test_recency(...) }}
```

### Run Tests

```bash
# All tests
dbt test

# Specific model
dbt test --select stg_github_events

# Store failures for debugging
dbt test --store-failures
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: dbt CI
on: [push, pull_request]

jobs:
  dbt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install dbt-postgres
      - run: dbt deps
      - run: dbt run --profiles-dir .
      - run: dbt test --profiles-dir .
```

### Airflow Integration

See `dags/dbt_transform_dag.py` for Airflow DAG that runs dbt after raw ingestion.

## Airflow Integration

The dbt transformations are orchestrated via Airflow DAG (`dbt_transform_dag.py`) that:

1. Waits for raw data ingestion to complete
2. Runs dbt staging models
3. Runs dbt mart models
4. Runs dbt tests
5. Generates documentation

## Monitoring

### Source Freshness

```bash
dbt source freshness
```

### Model Performance

```bash
# Run with verbose logging
dbt run --log-level debug

# Check run results
cat dbt_target/run_results.json
```

### Data Quality

```bash
# Test failures
dbt test --store-failures

# Check test results
select * from test_results.not_null_stg_github_events_event_id;
```

## Troubleshooting

### Common Issues

**Connection errors**
```bash
# Check connection
dbt debug --profiles-dir .

# Verify environment variables
env | grep POSTGRES
```

**Schema not found**
```sql
-- Create schemas manually if needed
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
```

**Package installation fails**
```bash
# Clear package cache
rm -rf dbt_packages/
dbt deps
```

## Best Practices

1. **Always test locally before deploying**
   ```bash
   dbt run --select model_name
   dbt test --select model_name
   ```

2. **Use incremental models for large tables**
   - Fact tables > 1M rows
   - Daily aggregations

3. **Document your models**
   - Add descriptions in schema.yml
   - Use comments in SQL

4. **Version control everything**
   - Commit all YAML files
   - Track schema changes

5. **Monitor data quality**
   - Set up test alerts
   - Review test failures

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt Utils Package](https://github.com/dbt-labs/dbt-utils)
- [dbt Expectations Package](https://github.com/calogica/dbt-expectations)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review dbt logs: `dbt_logs/dbt.log`
3. Check model-specific logs: `dbt_target/run/`

