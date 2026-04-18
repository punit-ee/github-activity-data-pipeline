# Answers to Your Questions

## Question 1: Should database be created earlier in Airflow DAG and reused?

### Short Answer
**NO for current implementation** - Each task should create its own database backend instance. Here's why:

### Current DAG Behavior
```python
# ❌ WRONG - Can't do this in Airflow
database = DatabaseFactory.create_from_config(config)  # At DAG level
ingest_to_database(database)  # Pass to task - WON'T WORK!

# ✅ CORRECT - Current implementation
@task()
def ingest_to_database():
    database = DatabaseFactory.create_from_config(config)  # Per task
    with database:
        metrics = database.ingest_from_file(...)
```

### Why Each Task Creates Its Own Connection

**Airflow Constraint:** Tasks communicate via XCom (JSON serialization)
- Database connections **cannot be serialized**
- Must create fresh connection in each task
- This is Airflow's design pattern

**Parallel Execution:** Tasks run on different workers
- `.expand()` creates multiple task instances running simultaneously
- Each needs its own database connection
- Sharing connections = race conditions

### Is This Inefficient?

**NO** - With connection pooling:
```python
# First task creates pool with 10 connections
backend = PostgreSQLBackend(..., use_pooling=True, pool_size=10)

# Each parallel task:
# 1. Gets connection from pool (fast)
# 2. Executes query
# 3. Returns connection to pool (reused)
```

---

## Question 2: Single connection + parallel requests = PROBLEM?

### Short Answer
**YES - Critical issue!** The DAG uses `.expand()` which runs tasks in parallel. Single connection is NOT thread-safe.

### The Problem

```python
# Current DAG flow
hours = ["2026-04-18-0", "2026-04-18-1", "2026-04-18-2", ...]

# This creates parallel tasks!
ingested = ingest_to_database.expand(upload_result=uploaded)

# Runs simultaneously:
# Task 1: Processing hour 0 on Worker 1
# Task 2: Processing hour 1 on Worker 2  
# Task 3: Processing hour 2 on Worker 3
```

**If they shared one connection:** 
- ❌ Race conditions
- ❌ Transaction conflicts  
- ❌ Corrupted data
- ❌ Connection errors

### The Solution: Connection Pooling

I've implemented **ThreadedConnectionPool** for safe parallel execution:

```python
from psycopg2 import pool

# Create pool once
pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,  # Up to 10 parallel tasks
    host=host,
    database=database,
    ...
)

# Each task:
conn = pool.getconn()  # Thread-safe
try:
    # Do work
finally:
    pool.putconn(conn)  # Return to pool
```

---

## Implementation Summary

### What I Changed

**1. Added Connection Pooling to `database.py`:**
```python
class PostgreSQLBackend:
    def __init__(self, ..., use_pooling=False, pool_size=5):
        if use_pooling:
            self.pool = ThreadedConnectionPool(minconn=1, maxconn=pool_size, ...)
        else:
            self.connection = psycopg2.connect(...)
    
    def _get_connection(self):
        """Get connection (from pool or single)"""
    
    def _return_connection(self, conn):
        """Return to pool or do nothing"""
```

**2. Updated `config.py`:**
```python
@dataclass
class DatabaseConfig:
    pg_use_pooling: bool = False  # Set True for Airflow
    pg_pool_size: int = 10
```

**3. Updated `docker-compose.airflow.yml`:**
```yaml
environment:
  POSTGRES_USE_POOLING: "true"   # Enable for parallel tasks
  POSTGRES_POOL_SIZE: "10"       # Max 10 concurrent
```

**4. Updated `backends.py`:**
```python
PostgreSQLBackend(
    ...,
    use_pooling=config.pg_use_pooling,
    pool_size=config.pg_pool_size,
)
```

---

## Configuration Guide

### Local Development (Sequential)
```bash
# Single connection is fine
export POSTGRES_USE_POOLING=false
python examples/complete_pipeline.py
```

### Airflow (Parallel Tasks)
```bash
# Must use pooling
export POSTGRES_USE_POOLING=true
export POSTGRES_POOL_SIZE=10
docker-compose -f docker-compose.airflow.yml up
```

### BigQuery (Always Safe)
BigQuery client is thread-safe by design - no pooling needed!

---

## Test Results

```
Testing PostgreSQL Connection Modes:

1️⃣  Single connection mode:
   ✅ Works for sequential tasks
   ⚠️  NOT safe for parallel tasks

2️⃣  Connection pooling mode:
   ✅ Thread-safe for parallel tasks
   ✅ Efficient connection reuse
   ✅ 3 parallel queries succeeded

✅ ALL TESTS PASSED
```

---

## Architecture Comparison

### Before (UNSAFE for Parallel)
```
DAG Level:
  ❌ Can't create database here (not serializable)

Task Level:
  database = PostgreSQLBackend(use_pooling=False)  # ⚠️ Single connection
  
Parallel Execution:
  Task 1 (hour 0) ─┐
  Task 2 (hour 1) ─┼─> ❌ RACE CONDITION on single connection!
  Task 3 (hour 2) ─┘
```

### After (SAFE for Parallel)
```
DAG Level:
  config sets use_pooling=True

Task Level:
  database = PostgreSQLBackend(use_pooling=True, pool_size=10)
  conn = pool.getconn()  # Thread-safe
  # work...
  pool.putconn(conn)

Parallel Execution:
  Task 1 (hour 0) ─> Connection 1 from pool ✅
  Task 2 (hour 1) ─> Connection 2 from pool ✅
  Task 3 (hour 2) ─> Connection 3 from pool ✅
```

---

## Recommendations

### ✅ Best Practices Applied

1. **Each task creates its own backend instance** (Airflow requirement)
2. **Connection pooling enabled for Airflow** (thread-safety)
3. **Single connection for scripts** (efficiency)
4. **Method moved to database.py** (proper layering)

### 🚀 Production Settings

**Airflow docker-compose.airflow.yml:**
```yaml
environment:
  POSTGRES_USE_POOLING: "true"
  POSTGRES_POOL_SIZE: "10"  # Match Airflow parallelism
```

**Standalone scripts:**
```bash
# Keep pooling OFF for sequential execution
export POSTGRES_USE_POOLING=false
python examples/complete_pipeline.py
```

---

## Quick Verification

```bash
# Test connection pooling
python tests/test_connection_pooling.py

# Test DAG with pooling
export POSTGRES_USE_POOLING=true
airflow dags test github_archive_pipeline 2026-04-18

# Monitor pool usage (in Postgres logs)
docker-compose logs postgres | grep "connection"
```

---

## Summary

| Question | Answer | Implementation |
|----------|--------|----------------|
| **1. Create database early and reuse?** | NO - Each task must create own instance | ✅ Each task calls `DatabaseFactory.create_from_config()` |
| **2. Single connection for parallel?** | NO - Need connection pool | ✅ Implemented `ThreadedConnectionPool` |

**Status:** ✅ Both issues resolved with production-ready patterns!

