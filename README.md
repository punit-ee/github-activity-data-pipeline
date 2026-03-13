# github-activity-data-pipeline
Modern data platform built with Airflow, BigQuery, dbt, and Terraform to analyze GitHub Archive events. The pipeline ingests hourly GitHub activity data, builds curated analytical models, and visualizes trends in open-source development through an interactive dashboard.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run unit tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## GitHub Archive client usage

```python
from ingestion.github_archive_client import GitHubArchiveClient

with GitHubArchiveClient() as client:
    response = client.download_events("2026-03-13-10")
    with open("events.json.gz", "wb") as output:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                output.write(chunk)
```

## Logging

Configure logging at application entrypoint so client logs are visible in production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```
