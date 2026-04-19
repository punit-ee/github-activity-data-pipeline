# github-activity-data-pipeline

Modern data platform built with Airflow, BigQuery, dbt, and Terraform to analyze GitHub Archive events. The pipeline ingests hourly GitHub activity data, builds curated analytical models, and visualizes trends in open-source development through an interactive dashboard.

## Features

✅ **Production-Ready Client** - Robust HTTP client with retry logic and timeouts  
✅ **Design Patterns** - Factory, Configuration Object, Strategy patterns  
✅ **TDD Approach** - Comprehensive unit and integration tests  
✅ **Structured Logging** - JSON logging for production monitoring  
✅ **Type Safety** - Full type hints and dataclass configurations  
✅ **Resource Management** - Context managers for automatic cleanup  
✅ **Error Handling** - Custom exceptions with detailed error messages  
✅ **Concurrent Processing** - Thread-safe batch downloads  

## Quick Start

### Local Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from ingestion.github_archive_client import GitHubArchiveClient

# Simple download
with GitHubArchiveClient() as client:
    response = client.download_events("2026-03-13-10")
    with open("events.json.gz", "wb") as output:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                output.write(chunk)
```

### Using Factory Pattern

```python
from ingestion.factory import GitHubArchiveClientFactory

# Production client
client = GitHubArchiveClientFactory.create_for_production()

# Or use configuration
from ingestion.config import PipelineConfig

config = PipelineConfig.from_env()
client = GitHubArchiveClientFactory.create_from_config(config.github_archive)
```

### Airflow DAG (Production Orchestration) ✨

**Modern Airflow 2.8.x with @dag decorators + Docker support**

```bash
# Option 1: Automated setup (Recommended)
./scripts/setup_airflow.sh

# Option 2: Manual setup
docker-compose up -d  # Infrastructure
docker-compose -f docker-compose.airflow.yml up airflow-init  # Init
docker-compose -f docker-compose.airflow.yml up -d  # Start

# Access Airflow UI
open http://localhost:8080
# Login: airflow / airflow
```

**Features:**
- 📅 Daily schedule (2 AM UTC)
- 🔄 Incremental loading (tracks state)
- 🎯 Backfill support for historical data
- ⚡ Automatic retries with error handling
- 📊 Detailed metrics and monitoring
- 🐳 Complete Docker environment
- ✨ Modern @dag and @task decorators
- 💾 **Storage fallback** - Auto-recovers files from MinIO/GCS if local file is missing

See [AIRFLOW_DOCKER_GUIDE.md](AIRFLOW_DOCKER_GUIDE.md) for complete guide.

## Examples

See the `examples/` directory for comprehensive examples:

- **basic_usage.py** - Simple single-file downloads
- **advanced_usage.py** - Batch downloads, concurrent processing
- **production_usage.py** - Production-ready with monitoring and structured logging
- **test_storage_fallback.py** - Demonstrate storage fallback mechanism

Run an example:
```bash
python examples/basic_usage.py
```

For detailed documentation, see [examples/README.md](examples/README.md)

## Testing

### Run All Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Unit Tests Only

```bash
python -m unittest discover -s tests/unit -p "test_*.py"
```

### Integration Tests

```bash
RUN_INTEGRATION_TESTS=1 python -m unittest discover -s tests/integration -p "test_*.py"
```

### Test Coverage

- ✅ Core client functionality
- ✅ Error handling and edge cases
- ✅ Configuration management
- ✅ Factory pattern
- ✅ Network error scenarios
- ✅ Date validation (including leap years)
- ✅ Timeout handling
- ✅ Context manager behavior

## Architecture

### Design Patterns

**Factory Pattern** (`ingestion/factory.py`, `ingestion/backends.py`) ✨
- Flexible client creation with different configurations
- Predefined configurations for common use cases (production, testing, etc.)
- Storage and database backend factories

**Configuration Object Pattern** (`ingestion/config.py`)
- Type-safe configuration management
- Environment variable support
- Validation logic

**Strategy Pattern** (throughout codebase)
- Configurable retry strategies
- Extensible download workflows
- Pluggable storage backends (MinIO/GCS) ✨
- Pluggable database backends (PostgreSQL/BigQuery) ✨

### Infrastructure

**Local Development** (docker-compose.yml):
- **MinIO**: S3-compatible object storage
- **PostgreSQL**: Relational database
- **pgAdmin**: Database web UI

**Production**:
- **Google Cloud Storage**: Object storage
- **BigQuery**: Data warehouse

```bash
# Start local infrastructure
docker-compose up -d

# Access MinIO Console: http://localhost:9001
# Access pgAdmin: http://localhost:5050
```

### Project Structure

```
github-activity-data-pipeline/
├── ingestion/              # Core client library
│   ├── github_archive_client.py  # Main client
│   ├── config.py          # Configuration management
│   ├── factory.py         # Client factory
│   ├── storage.py         # Storage backends ✨ NEW
│   ├── database.py        # Database backends ✨ NEW
│   └── backends.py        # Backend factories ✨ NEW
├── examples/              # Usage examples
│   ├── basic_usage.py
│   ├── advanced_usage.py
│   ├── production_usage.py
│   ├── storage_example.py      ✨ NEW
│   ├── database_example.py     ✨ NEW
│   ├── complete_pipeline.py    ✨ NEW
│   └── README.md
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── scripts/
│   └── init_db.sql       # Database initialization ✨ NEW
├── docker-compose.yml    # Local infrastructure ✨ NEW
├── .env.example          # Local config template ✨ NEW
└── requirements.txt
```

## Configuration

Configure via environment variables:

```bash
# Client configuration
export GITHUB_ARCHIVE_CONNECT_TIMEOUT=10.0
export GITHUB_ARCHIVE_READ_TIMEOUT=60.0
export GITHUB_ARCHIVE_MAX_RETRIES=5

# Download configuration
export DOWNLOAD_CHUNK_SIZE=2097152  # 2MB
export DOWNLOAD_MAX_WORKERS=5
export DOWNLOAD_OUTPUT_DIR="./data"

# Logging configuration
export LOG_LEVEL=INFO
export LOG_JSON=true  # Enable structured JSON logging
```

## Logging

### Development Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
```

### Production Logging (Structured JSON)

```python
from examples.production_usage import setup_production_logging

setup_production_logging()
# Logs are now in JSON format for easy parsing by log aggregators
```

## Implementation Features

### Error Handling
- Custom exception hierarchy
- Detailed error messages with context
- Proper exception chaining

### Resource Management
- Context managers for automatic cleanup
- Session reuse for better performance
- Proper timeout configuration

### Type Safety
- Full type hints throughout
- Dataclasses for configuration
- Runtime validation

### Testing
- Test-Driven Development (TDD)
- High test coverage
- Unit and integration test separation

### Monitoring & Observability
- Structured logging
- Metrics collection
- Health checks
- Retry logic with exponential backoff

## API Reference

### GitHubArchiveClient

Main client for downloading GitHub Archive data.

```python
client = GitHubArchiveClient(
    timeout=(5.0, 30.0),  # (connect_timeout, read_timeout)
    session=None,          # Optional custom session
)

# Download events for a specific hour
response = client.download_events("2026-03-13-10")

# Build URL for a date_hour
url = client.build_url("2026-03-13-10")
```

### GitHubArchiveClientFactory

Factory for creating preconfigured clients.

```python
# Default configuration
client = GitHubArchiveClientFactory.create_default()

# Production optimized (longer timeouts)
client = GitHubArchiveClientFactory.create_for_production()

# Testing (short timeouts, mockable)
client = GitHubArchiveClientFactory.create_for_testing(session=mock_session)

# Fast (minimal timeouts)
client = GitHubArchiveClientFactory.create_fast()

# Resilient (extended timeouts for unreliable networks)
client = GitHubArchiveClientFactory.create_resilient()
```

## Contributing

1. Write tests first (TDD approach)
2. Follow existing code style
3. Add type hints
4. Update documentation
5. Run all tests before submitting

## License

See LICENSE file for details.

