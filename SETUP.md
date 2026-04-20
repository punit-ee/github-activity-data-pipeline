# Complete Setup Guide
## GitHub Archive Analytics Pipeline

This guide will help you set up and run the complete pipeline in **5 minutes**.

---

## Prerequisites

Before starting, ensure you have:

- **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop))
  - At least **8GB RAM** allocated to Docker
  - At least **10GB free disk space**
- **Internet connection** (to download GitHub Archive data)

**That's it!** No Python installation, no manual database setup required.

---

## Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/github-activity-data-pipeline.git
cd github-activity-data-pipeline
```

### Step 2: Review Environment Configuration (Optional)

The project comes with sensible defaults. You can optionally customize settings:

```bash
# Copy example environment file
cp .env.example .env

# Edit if needed (optional)
nano .env
```

**Default settings work out of the box!** No changes required.

### Step 3: Start All Services

```bash
./start.sh
```

**What happens:**
1. Docker pulls images (first time only, ~5 minutes)
2. Initializes PostgreSQL database
3. Starts Airflow, Metabase, MinIO
4. Runs health checks
5. Shows you access URLs

**Expected output:**
```
✅ All services are healthy!

Access your services:
  Airflow:  http://localhost:8080 (airflow / airflow)
  Metabase: http://localhost:3000 (setup on first visit)
  MinIO:    http://localhost:9001 (minioadmin / minioadmin)
```

---

## Access Services

### 1. Airflow (Orchestration)

**URL**: http://localhost:8080  
**Login**: `airflow` / `airflow`

**First-time setup:**
1. Click on the "github_archive_pipeline" DAG
2. Toggle it to **ON** (top-right switch)
3. Click **"Trigger DAG"** to run manually

### 2. Metabase (Dashboards)

**URL**: http://localhost:3000

**First-time setup:**
1. Create admin account (email, password, organization name)
2. Click "Add a database"
3. Fill in connection details:
   - Database type: **PostgreSQL**
   - Name: `GitHub Archive`
   - Host: `postgres`
   - Port: `5432`
   - Database name: `github_archive`
   - Username: `postgres`
   - Password: `postgres`
4. Click "Save"

### 3. MinIO (Object Storage)

**URL**: http://localhost:9001  
**Login**: `minioadmin` / `minioadmin`

Browse uploaded GitHub Archive files in the `github-archive` bucket.

---

## Running Your First Pipeline

### Option 1: Process Last Few Hours (Recommended for Testing)

1. Open Airflow: http://localhost:8080
2. Enable "github_archive_pipeline"
3. Click "Trigger DAG w/ config"
4. Set parameters:
   ```
   backfill_start: 2026-04-18-0
   backfill_end: 2026-04-18-5
   ```
5. Click "Trigger"

**This will process 6 hours of data (~3-5 minutes).**

### Option 2: Automatic Incremental Mode

1. Enable "github_archive_pipeline" in Airflow
2. Wait for the hourly schedule (runs at minute 0 every hour)
3. Pipeline automatically detects last processed hour
4. Processes all missing hours

---

## Monitoring Pipeline Execution

### In Airflow UI

1. Go to http://localhost:8080
2. Click on "github_archive_pipeline"
3. Click on the latest run (green = success, red = failed)
4. View individual task status:
   - **download_from_github** - Downloads .json.gz files
   - **upload_to_storage** - Uploads to MinIO
   - **ingest_to_database** - Loads to PostgreSQL

### Check Data in Database

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U postgres -d github_archive

# Check raw events count
SELECT COUNT(*) FROM raw.github_events;

# Check latest event date
SELECT MAX(event_date) FROM raw.github_events;

# Exit
\q
```

---

## Running dbt Transformations

After data is ingested, run dbt to create analytics models:

### Option 1: Via Airflow DAG

1. Go to Airflow UI
2. Enable "dbt_transform_github_archive"
3. Trigger manually (or wait for schedule)

### Option 2: Manual Execution

```bash
# Run all models
docker exec -it dbt-runner dbt run --profiles-dir .

# Run tests
docker exec -it dbt-runner dbt test --profiles-dir .

# View documentation
docker exec -it dbt-runner dbt docs generate --profiles-dir .
docker exec -it dbt-runner dbt docs serve --port 8081

# Open http://localhost:8081 in browser
```

---

## Setting Up Metabase Dashboards

### Option 1: Automated Setup (Recommended)

```bash
docker exec -it metabase python /app/metabase/setup_dashboards.py
```

### Option 2: Manual Setup

1. Open Metabase: http://localhost:3000
2. Create a new question
3. Copy SQL from `metabase/consolidated_queries.sql`
4. Paste into SQL editor
5. Save and add to dashboard

**SQL Queries Available:**
- Event type distribution
- Daily trends
- Top repositories
- Top developers
- Hourly heatmap
- And 26 more...

---

## Verifying Everything Works

Run these commands to verify the setup:

```bash
# Check all containers are running
docker ps

# Check Airflow DAGs
docker exec -it airflow-webserver airflow dags list

# Check database
docker exec -it postgres psql -U postgres -c "SELECT COUNT(*) FROM raw.github_events;"

# Check dbt models
docker exec -it dbt-runner dbt run --profiles-dir . --select stg_github_events

# Check MinIO buckets
docker exec -it minio mc ls local/
```

**Expected results:**
- All containers status: "Up"
- Airflow DAGs: 3 DAGs listed
- Database: Count > 0 (if pipeline ran)
- dbt: "1 of 1 OK" message
- MinIO: "github-archive" bucket exists

---

## Stopping and Restarting

### Stop Services (Preserve Data)

```bash
./stop.sh
```

Data is preserved in Docker volumes.

### Restart Services

```bash
./start.sh
```

### Clean Everything (Delete All Data)

```bash
docker-compose down -v
rm -rf data/ logs/ dbt_target/
```

**Warning**: This deletes all ingested data and logs!

---

## Troubleshooting

### Issue: Services Won't Start

**Solution:**
```bash
# Check Docker resources
docker stats

# Increase Docker memory to 8GB in Docker Desktop settings
# Restart Docker Desktop
```

### Issue: Airflow Shows "No DAGs"

**Solution:**
```bash
# Wait 1-2 minutes for DAG parsing
# Check scheduler logs
docker logs airflow-scheduler

# Restart scheduler if needed
docker restart airflow-scheduler
```

### Issue: No Data After Pipeline Runs

**Solution:**
```bash
# Check Airflow task logs
# In Airflow UI → DAG → Task → Logs

# Check database connection
docker exec -it postgres psql -U postgres -c "\l"

# Manually trigger ingestion
docker exec -it airflow-scheduler airflow dags trigger github_archive_pipeline
```

### Issue: dbt Tests Fail

**Solution:**
```bash
# View detailed error
docker exec -it dbt-runner dbt test --profiles-dir . --debug

# Run specific model
docker exec -it dbt-runner dbt run --select stg_github_events --profiles-dir .

# Clear dbt cache
docker exec -it dbt-runner rm -rf target/
```

### Issue: Metabase Can't Connect to Database

**Solution:**
1. Ensure you're using `postgres` as hostname (not `localhost`)
2. Check PostgreSQL is running: `docker ps | grep postgres`
3. Try connection test in Metabase
4. Restart Metabase: `docker restart metabase`

### Issue: Out of Disk Space

**Solution:**
```bash
# Check Docker disk usage
docker system df

# Clean up unused images and containers
docker system prune -a

# Remove old dbt artifacts
rm -rf dbt_target/ dbt_logs/
```

---

## Next Steps

### 1. Explore Dashboards
- Open Metabase and create visualizations
- Use SQL queries from `metabase/consolidated_queries.sql`

### 2. Backfill Historical Data
```bash
# Process last 7 days
# In Airflow, trigger with:
#   backfill_start: 2026-04-13-0
#   backfill_end: 2026-04-20-23
```

### 3. Schedule Regular Updates
- Keep "github_archive_pipeline" enabled
- Runs automatically every hour
- Processes new data incrementally

### 4. Customize Transformations
- Edit dbt models in `dbt_models/`
- Add custom tests in `dbt_tests/`
- Run `dbt run --profiles-dir .`

---

## Performance Tips

### For Large Backfills

```bash
# Increase Airflow parallelism
# Edit docker-compose.airflow.yml:
#   max_active_tasks: 8
#   max_active_runs: 2

# Restart Airflow
docker-compose -f docker-compose.airflow.yml restart
```

### For Faster dbt Runs

```bash
# Run only changed models
docker exec -it dbt-runner dbt run --select state:modified+ --profiles-dir .

# Run specific model and downstream
docker exec -it dbt-runner dbt run --select stg_github_events+ --profiles-dir .
```

---

## Support

- **Documentation**: See [README.md](README.md)
- **Data Dictionary**: See [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- **dbt Guide**: See [DBT_README.md](DBT_README.md)
- **Examples**: See [examples/README.md](examples/README.md)

---

**Setup completed! 🎉**

You now have a fully functional data pipeline processing GitHub events.

