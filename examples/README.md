# Examples

This directory contains comprehensive examples demonstrating how to use the GitHub Archive data pipeline client.

## Overview

The examples are organized by complexity and use case:

1. **basic_usage.py** - Simple single-file downloads
2. **advanced_usage.py** - Batch downloads, concurrent processing, and analysis
3. **production_usage.py** - Production-ready implementation with monitoring and structured logging

## Quick Start

### Basic Usage

Download a single hour of GitHub Archive data:

```bash
python examples/basic_usage.py
```

This example demonstrates:
- Simple download workflow
- Basic error handling
- Streaming to avoid memory issues
- Proper resource cleanup with context managers

### Advanced Usage

Download multiple hours with concurrent processing:

```bash
python examples/advanced_usage.py
```

This example demonstrates:
- Date range generation
- Concurrent downloads with ThreadPoolExecutor
- Progress tracking and metrics
- Custom timeout configuration
- Basic data analysis (event type distribution)

### Production Usage

Production-ready pipeline with monitoring:

```bash
python examples/production_usage.py
```

This example demonstrates:
- **Structured JSON logging** for production monitoring
- **Retry logic with exponential backoff**
- **Metrics collection** (download time, file size, success/failure rates)
- **Health checks** before processing
- **Graceful error handling** with proper exit codes

## Design Patterns Demonstrated

### 1. Factory Pattern
See: `ingestion/factory.py`

The `GitHubArchiveClientFactory` provides convenient methods for creating clients with different configurations:

```python
from ingestion.factory import GitHubArchiveClientFactory

# Different client configurations
default_client = GitHubArchiveClientFactory.create_default()
production_client = GitHubArchiveClientFactory.create_for_production()
test_client = GitHubArchiveClientFactory.create_for_testing()
```

### 2. Configuration Object Pattern
See: `ingestion/config.py`

Centralized, type-safe configuration management:

```python
from ingestion.config import PipelineConfig

# Load from environment variables
config = PipelineConfig.from_env()
config.validate()

# Use in client
from ingestion.factory import GitHubArchiveClientFactory
client = GitHubArchiveClientFactory.create_from_config(config.github_archive)
```

### 3. Strategy Pattern
The production example demonstrates strategy pattern for retry logic - you can easily swap retry strategies.

### 4. Template Method Pattern
The `GitHubArchiveDownloader` class in production_usage.py uses template method pattern, allowing subclasses to override specific steps.

## Best Practices Implemented

### 1. Logging

#### Structured Logging for Production
```python
from examples.production_usage import setup_production_logging

setup_production_logging()
# Logs are now in JSON format, easily parsed by log aggregators
```

#### Development Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### 2. Error Handling

All examples demonstrate comprehensive error handling:

```python
try:
    with GitHubArchiveClient() as client:
        response = client.download_events(date_hour)
except ValueError as e:
    # Handle invalid date format
    logger.error(f"Invalid date: {e}")
except GitHubArchiveDownloadError as e:
    # Handle download failures (network, HTTP errors)
    logger.error(f"Download failed: {e}")
except Exception as e:
    # Catch unexpected errors
    logger.exception(f"Unexpected error: {e}")
```

### 3. Resource Management

Use context managers for automatic cleanup:

```python
# Client automatically closes session
with GitHubArchiveClient() as client:
    response = client.download_events(date_hour)

# Custom downloader with cleanup
with GitHubArchiveDownloader(output_dir) as downloader:
    metrics = downloader.download_with_retry(date_hour)
```

### 4. Streaming for Large Files

Always stream large files to avoid memory issues:

```python
response = client.download_events(date_hour)

with open(output_file, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)
```

### 5. Concurrent Processing

Use `ThreadPoolExecutor` with reasonable limits:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(download_func, date): date
        for date in date_list
    }
    
    for future in as_completed(futures):
        result = future.result()
        # Process result
```

## Test-Driven Development (TDD)

The project follows TDD principles with comprehensive test coverage:

### Unit Tests
- `tests/unit/test_github_archive_client.py` - Core client tests
- `tests/unit/test_github_archive_client_enhanced.py` - Enhanced edge cases
- `tests/unit/test_config.py` - Configuration tests
- `tests/unit/test_factory.py` - Factory pattern tests

### Integration Tests
- `tests/integration/test_github_archive_client_integration.py` - Real API tests

### Running Tests

```bash
# All tests
python -m unittest discover -s tests -p "test_*.py"

# Unit tests only
python -m unittest discover -s tests/unit -p "test_*.py"

# Integration tests (requires network)
RUN_INTEGRATION_TESTS=1 python -m unittest discover -s tests/integration -p "test_*.py"

# Specific test file
python -m unittest tests.unit.test_github_archive_client_enhanced
```

## Environment Variables

Configure the pipeline using environment variables:

### GitHub Archive Client
```bash
export GITHUB_ARCHIVE_CONNECT_TIMEOUT=10.0
export GITHUB_ARCHIVE_READ_TIMEOUT=60.0
export GITHUB_ARCHIVE_MAX_RETRIES=5
export GITHUB_ARCHIVE_USER_AGENT="my-app/2.0"
```

### Download Configuration
```bash
export DOWNLOAD_CHUNK_SIZE=2097152  # 2MB
export DOWNLOAD_MAX_WORKERS=5
export DOWNLOAD_OUTPUT_DIR="./data"
export DOWNLOAD_OVERWRITE=true
```

### Logging Configuration
```bash
export LOG_LEVEL=DEBUG
export LOG_JSON=true
```

## Monitoring and Metrics

The production example includes comprehensive metrics:

```python
from examples.production_usage import GitHubArchiveDownloader

with GitHubArchiveDownloader(output_dir) as downloader:
    metrics = downloader.download_with_retry(date_hour)
    
    print(f"Duration: {metrics.duration_seconds}s")
    print(f"File size: {metrics.file_size_mb}MB")
    print(f"Success: {metrics.success}")
    print(f"Retries: {metrics.retry_count}")
```

## Common Use Cases

### 1. Download Recent Data

```python
from datetime import datetime, timedelta
from pathlib import Path
from ingestion.github_archive_client import GitHubArchiveClient

# Download last 3 hours
now = datetime.utcnow()
output_dir = Path("./data")

with GitHubArchiveClient() as client:
    for hours_ago in range(3):
        dt = now - timedelta(hours=hours_ago + 1)
        date_hour = dt.strftime("%Y-%m-%d-%H")
        
        response = client.download_events(date_hour)
        output_file = output_dir / f"{date_hour}.json.gz"
        
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
```

### 2. Process Events

```python
import gzip
import json

with gzip.open("2026-03-13-10.json.gz", "rt") as f:
    for line in f:
        event = json.loads(line)
        # Process event
        print(f"{event['type']}: {event['actor']['login']}")
```

### 3. Batch Processing with Error Recovery

```python
from examples.advanced_usage import download_date_range_concurrent
from datetime import datetime
from pathlib import Path

start = datetime(2026, 3, 13, 0)
results = download_date_range_concurrent(
    start_date=start,
    hours=24,
    output_dir=Path("./data"),
    max_workers=5
)

print(f"Success: {results['success']}, Failed: {results['failed']}")
```

## Troubleshooting

### Timeout Errors

If you experience timeout errors:

```python
# Increase timeouts
from ingestion.factory import GitHubArchiveClientFactory

client = GitHubArchiveClientFactory.create_resilient()
# Uses (15.0, 120.0) timeouts
```

### Rate Limiting

GitHub Archive doesn't have rate limits, but be respectful:

```python
# Limit concurrent downloads
max_workers=3  # Don't use more than 5
```

### Memory Issues

Always use streaming:

```python
# Good - streams data
for chunk in response.iter_content(chunk_size=1024*1024):
    f.write(chunk)

# Bad - loads everything in memory
content = response.content  # Don't do this
```

## Next Steps

1. Review the code examples
2. Run the tests to understand behavior
3. Try modifying examples for your use case
4. Implement your own processing logic
5. Deploy to production with monitoring

## Additional Resources

- [GitHub Archive Documentation](https://www.gharchive.org/)
- [Requests Library Docs](https://requests.readthedocs.io/)
- Project README: `../README.md`

