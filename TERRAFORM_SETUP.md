# BigQuery Terraform Infrastructure Setup

## Overview

Production-ready Terraform configuration for GitHub Archive data pipeline with BigQuery backend.

## Changes Applied

### Infrastructure Modules

**BigQuery Module** (`terraform/modules/bigquery/`)
- 3 datasets: raw, staging, marts
- Partitioned table (DAY) on event_date with partition expiration
- Clustered on event_type, repo_id, actor_id
- Complete schema with 23 fields including JSON payload
- Deletion protection configurable per environment

**IAM Module** (`terraform/modules/iam/`)
- Airflow service account with BigQuery dataEditor and jobUser roles
- dbt service account with read access to raw, write to staging/marts
- GCS objectAdmin for Airflow
- Dataset-level IAM bindings
- Automatic service account key generation

**Storage Module** (`terraform/modules/storage/`)
- Raw data bucket (STANDARD storage class)
- Archive bucket (ARCHIVE storage class)
- Lifecycle policies: STANDARD → NEARLINE (90d) → COLDLINE (270d)
- Uniform bucket-level access
- Versioning support (enabled in prod)

**Monitoring Module** (`terraform/modules/monitoring/`)
- Alert policies: slot utilization, query execution time, storage spike
- Log-based metrics for ingestion errors
- Custom dashboard with 4 visualization panels
- Notification channel integration

### Configuration Files

**Root Module** (`terraform/main.tf`)
- GCS backend for state management
- Module composition with proper dependencies
- Common labels applied to all resources

**Variables** (`terraform/variables.tf`)
- Type validation for environment (dev/staging/prod)
- Sensible defaults for all parameters
- Comprehensive descriptions

**Environment Configs** (`terraform/environments/`)
- `dev.tfvars`: Short retention, no deletion protection
- `prod.tfvars`: No expiration, deletion protection enabled

### Supporting Scripts

**Setup Script** (`scripts/setup_bigquery.sh`)
- Interactive setup workflow
- Terraform validation and planning
- Service account key extraction
- Environment variable instructions

**Connection Test** (`scripts/test_bigquery_connection.py`)
- Validates BigQuery connectivity
- Checks table existence and row counts
- Queries latest data statistics

**Docker Compose** (`docker-compose.bigquery.yml`)
- Override for BigQuery-specific services
- Service account key mounting
- Environment variable configuration

**Environment Template** (`.env.bigquery.example`)
- BigQuery configuration variables
- GCS storage settings
- Production-ready defaults

### Deployment Tools

**Makefile** (`terraform/Makefile`)
- Environment-specific commands
- Simplified workflow: init, plan, apply, destroy
- Format and validation targets

**README** (`terraform/README.md`)
- Complete setup instructions
- Module documentation
- Security best practices
- Troubleshooting guide

## Quick Start

```bash
cd terraform

export PROJECT_ID="your-gcp-project"
export ENVIRONMENT="dev"

gsutil mb -p $PROJECT_ID gs://github-archive-terraform-state-${ENVIRONMENT}

terraform init -backend-config="bucket=github-archive-terraform-state-${ENVIRONMENT}"

terraform plan -var-file=environments/${ENVIRONMENT}.tfvars

terraform apply -var-file=environments/${ENVIRONMENT}.tfvars

terraform output -raw airflow_sa_key | base64 -d > ../service-account-keys/airflow-${ENVIRONMENT}.json

export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/../service-account-keys/airflow-${ENVIRONMENT}.json
export GCP_PROJECT_ID=$(terraform output -raw project_id)

python ../scripts/test_bigquery_connection.py
```

## Features

- Multi-environment support (dev/staging/prod)
- State management with GCS backend
- Least-privilege IAM with service accounts
- Partitioning and clustering for query optimization
- Automated lifecycle policies for cost optimization
- Monitoring and alerting out-of-the-box
- Deletion protection for production
- Comprehensive documentation

## Architecture

```
Airflow (SA) → BigQuery Raw Dataset → dbt (SA) → Staging/Marts
              ↓
           GCS Buckets (Raw/Archive)
              ↓
        Cloud Monitoring (Alerts/Dashboard)
```

## Security

- Service account keys stored in `.gitignore` directory
- Dataset-level IAM instead of project-level
- Uniform bucket access enabled
- Terraform state encrypted in GCS
- Deletion protection in production
- No hardcoded credentials

## Cost Optimization

- Partition expiration (configurable)
- Storage lifecycle policies (STANDARD → NEARLINE → COLDLINE → ARCHIVE)
- Clustering reduces scan costs
- Partition pruning with require_partition_filter
- Slot monitoring alerts

## Monitoring

- Slot utilization alerts (>80%)
- Query performance alerts (>5min p99)
- Storage upload spike detection
- Log-based ingestion error metrics
- Custom dashboard with BigQuery and GCS metrics

