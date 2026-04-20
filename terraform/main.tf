terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "terraform-state-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  labels = merge(
    var.labels,
    {
      managed_by  = "terraform"
      environment = var.environment
      project     = "github-archive"
    }
  )
}

module "bigquery" {
  source = "./modules/bigquery"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  labels      = local.labels

  raw_dataset_id     = var.raw_dataset_id
  staging_dataset_id = var.staging_dataset_id
  marts_dataset_id   = var.marts_dataset_id

  partition_expiration_days  = var.partition_expiration_days
  enable_deletion_protection = var.enable_deletion_protection
}

module "iam" {
  source = "./modules/iam"

  project_id  = var.project_id
  environment = var.environment

  airflow_sa_name = var.airflow_sa_name
  dbt_sa_name     = var.dbt_sa_name

  raw_dataset_id     = module.bigquery.raw_dataset_id
  staging_dataset_id = module.bigquery.staging_dataset_id
  marts_dataset_id   = module.bigquery.marts_dataset_id
}

module "storage" {
  source = "./modules/storage"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  labels      = local.labels

  raw_data_bucket_name  = var.raw_data_bucket_name
  archive_bucket_name   = var.archive_bucket_name
  lifecycle_age_days    = var.lifecycle_age_days
  enable_versioning     = var.enable_versioning
  enable_uniform_access = var.enable_uniform_access

  airflow_sa_email = module.iam.airflow_sa_email
}

module "monitoring" {
  source = "./modules/monitoring"

  project_id  = var.project_id
  environment = var.environment

  notification_channels = var.notification_channels

  raw_dataset_id = module.bigquery.raw_dataset_id
}
