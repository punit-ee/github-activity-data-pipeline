# Terraform Infrastructure for BigQuery

This directory contains Terraform configuration for provisioning BigQuery and GCS infrastructure.

## Structure

```
terraform/
├── main.tf                 # Root module
├── variables.tf            # Root variables
├── outputs.tf             # Root outputs
├── environments/          # Environment-specific configs
│   ├── dev.tfvars
│   └── prod.tfvars
└── modules/              # Reusable modules
    ├── bigquery/         # BigQuery datasets and tables
    ├── iam/              # Service accounts and permissions
    ├── storage/          # GCS buckets
    └── monitoring/       # Alerts and dashboards
```

## Prerequisites

1. Google Cloud SDK installed
2. Terraform >= 1.0
3. GCP project with billing enabled
4. Required APIs enabled:
   - BigQuery API
   - Cloud Storage API
   - Cloud Resource Manager API
   - Identity and Access Management (IAM) API

## Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  bigquery.googleapis.com \
  storage-api.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

### 2. Create Terraform State Bucket

```bash
export PROJECT_ID="your-gcp-project"
export ENVIRONMENT="dev"

gsutil mb -p $PROJECT_ID -l us-central1 gs://github-archive-terraform-state-${ENVIRONMENT}
gsutil versioning set on gs://github-archive-terraform-state-${ENVIRONMENT}
```

### 3. Update Environment Configuration

Edit `environments/dev.tfvars` or `environments/prod.tfvars`:

```hcl
project_id = "your-actual-project-id"
raw_data_bucket_name = "your-unique-bucket-name-raw"
archive_bucket_name = "your-unique-bucket-name-archive"
```

### 4. Initialize Terraform

```bash
cd terraform
terraform init -backend-config="bucket=terraform-state-dev"
```

## Deployment

### Deploy Development Environment

```bash
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

### Deploy Production Environment

```bash
terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

## Getting Service Account Keys

```bash
terraform output -raw airflow_sa_key | base64 -d > service-account-keys/airflow-key.json
terraform output -raw dbt_sa_key | base64 -d > service-account-keys/dbt-key.json
```

Set environment variables:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/airflow-key.json
export GCP_PROJECT_ID=$(terraform output -raw project_id)
```

## Module Details

### BigQuery Module

Creates:
- 3 datasets (raw, staging, marts)
- Partitioned and clustered `github_events` table
- Partition expiration policies
- Dataset access controls

### IAM Module

Creates:
- Airflow service account with BigQuery and GCS permissions
- dbt service account with BigQuery permissions
- Dataset-level IAM bindings
- Service account keys

### Storage Module

Creates:
- Raw data bucket (STANDARD storage)
- Archive bucket (ARCHIVE storage)
- Lifecycle policies
- IAM bindings for service accounts

### Monitoring Module

Creates:
- Alert policies for slot utilization, query performance
- Custom log-based metrics
- Monitoring dashboard

## Cleanup

```bash
terraform destroy -var-file=environments/dev.tfvars
```

## Security Notes

- Service account keys are sensitive - store securely
- Use Workload Identity Federation in production instead of keys
- Enable deletion protection in production
- Restrict access to state bucket
- Rotate service account keys regularly

