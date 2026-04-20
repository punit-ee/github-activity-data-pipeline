# BigQuery Quick Start Guide

## Prerequisites

1. Google Cloud Project with billing enabled
2. Terraform >= 1.0 installed
3. gcloud CLI configured

## Step 1: Enable APIs

```bash
gcloud services enable \
  bigquery.googleapis.com \
  storage-api.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  monitoring.googleapis.com
```

## Step 2: Create Terraform State Bucket

```bash
export PROJECT_ID="your-gcp-project-id"
export ENVIRONMENT="dev"

gsutil mb -p $PROJECT_ID -l us-central1 \
  gs://github-archive-terraform-state-${ENVIRONMENT}

gsutil versioning set on \
  gs://github-archive-terraform-state-${ENVIRONMENT}
```

## Step 3: Configure Terraform Variables

Edit `terraform/environments/dev.tfvars`:

```hcl
project_id = "your-actual-project-id"
raw_data_bucket_name = "your-project-github-archive-raw-dev"
archive_bucket_name = "your-project-github-archive-archive-dev"
terraform_state_bucket = "github-archive-terraform-state-dev"
```

## Step 4: Deploy Infrastructure

```bash
cd terraform

# Initialize
terraform init \
  -backend-config="bucket=github-archive-terraform-state-dev"

# Plan
terraform plan -var-file=environments/dev.tfvars

# Apply
terraform apply -var-file=environments/dev.tfvars
```

## Step 5: Extract Service Account Keys

```bash
# Create directory
mkdir -p ../service-account-keys

# Extract keys
terraform output -raw airflow_sa_key | base64 -d \
  > ../service-account-keys/airflow-dev.json

terraform output -raw dbt_sa_key | base64 -d \
  > ../service-account-keys/dbt-dev.json

# Secure permissions
chmod 600 ../service-account-keys/*.json
```

## Step 6: Configure Environment

Create `.env.bigquery`:

```bash
cp .env.bigquery.example .env.bigquery
```

Edit `.env.bigquery`:

```bash
DATABASE_BACKEND=bigquery
BIGQUERY_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-keys/airflow-dev.json

STORAGE_BACKEND=gcs
GCS_BUCKET=your-project-github-archive-raw-dev
GCS_PROJECT_ID=your-gcp-project-id
```

## Step 7: Test Connection

```bash
export $(cat .env.bigquery | xargs)
python scripts/test_bigquery_connection.py
```

## Step 8: Run Pipeline

### Option A: Local Python

```bash
python -c "
from ingestion.factory import GitHubArchiveClientFactory, DatabaseFactory
from ingestion.config import PipelineConfig
from pathlib import Path

config = PipelineConfig.from_env()

# Download data
with GitHubArchiveClientFactory.create_for_production() as client:
    response = client.download_events('2026-04-20-0')
    with open('/tmp/test.json.gz', 'wb') as f:
        for chunk in response.iter_content(1024*1024):
            f.write(chunk)

# Ingest to BigQuery
with DatabaseFactory.create_from_config(config.database) as db:
    metrics = db.ingest_from_file(Path('/tmp/test.json.gz'))
    print(f'Ingested {metrics.rows_inserted} rows')
"
```

### Option B: Docker with BigQuery

```bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.bigquery.yml \
  up -d

# Access Airflow and trigger DAG
open http://localhost:8080
```

## Infrastructure Overview

### Created Resources

- **BigQuery Datasets**: raw, staging, marts
- **BigQuery Table**: raw.github_events (partitioned + clustered)
- **GCS Buckets**: raw data, archive
- **Service Accounts**: airflow, dbt
- **IAM Bindings**: Least-privilege access
- **Monitoring**: Alerts and dashboard

### Outputs

```bash
# View all outputs
terraform output

# Get specific values
terraform output project_id
terraform output raw_table_full_id
terraform output airflow_service_account_email
```

## Troubleshooting

### Issue: Permission Denied

```bash
# Ensure you're authenticated
gcloud auth application-default login

# Verify project
gcloud config get-value project
```

### Issue: Bucket Already Exists

GCS bucket names are globally unique. Update bucket names in `environments/dev.tfvars`.

### Issue: API Not Enabled

```bash
# Check enabled APIs
gcloud services list --enabled

# Enable missing APIs
gcloud services enable bigquery.googleapis.com
```

## Cleanup

```bash
cd terraform

# Destroy all resources
terraform destroy -var-file=environments/dev.tfvars

# Delete state bucket
gsutil -m rm -r gs://github-archive-terraform-state-dev
```

## Cost Estimation

**Development Environment (dev.tfvars):**
- BigQuery: ~$5-10/month (90-day partition expiration)
- GCS: ~$2-5/month (lifecycle policies)
- **Total**: ~$7-15/month

**Production Environment (prod.tfvars):**
- BigQuery: ~$20-50/month (no expiration)
- GCS: ~$5-15/month (versioning enabled)
- **Total**: ~$25-65/month

*Actual costs depend on data volume and query patterns*

## Next Steps

1. Review [terraform/README.md](terraform/README.md) for detailed documentation
2. Check [TERRAFORM_SETUP.md](TERRAFORM_SETUP.md) for architecture details
3. Customize monitoring alerts in `terraform/modules/monitoring/`
4. Set up CI/CD for automated deployments

