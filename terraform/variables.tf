variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "labels" {
  description = "Common labels to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "terraform_state_bucket" {
  description = "GCS bucket for Terraform state"
  type        = string
}

variable "raw_dataset_id" {
  description = "BigQuery dataset for raw data"
  type        = string
  default     = "raw"
}

variable "staging_dataset_id" {
  description = "BigQuery dataset for staging data"
  type        = string
  default     = "staging"
}

variable "marts_dataset_id" {
  description = "BigQuery dataset for marts data"
  type        = string
  default     = "marts"
}

variable "partition_expiration_days" {
  description = "Number of days before partitions expire (null for no expiration)"
  type        = number
  default     = null
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for BigQuery tables"
  type        = bool
  default     = true
}

variable "airflow_sa_name" {
  description = "Service account name for Airflow"
  type        = string
  default     = "github-archive-airflow"
}

variable "dbt_sa_name" {
  description = "Service account name for dbt"
  type        = string
  default     = "github-archive-dbt"
}

variable "raw_data_bucket_name" {
  description = "GCS bucket name for raw data storage"
  type        = string
}

variable "archive_bucket_name" {
  description = "GCS bucket name for archived data"
  type        = string
}

variable "lifecycle_age_days" {
  description = "Days before moving objects to archive storage"
  type        = number
  default     = 90
}

variable "enable_versioning" {
  description = "Enable object versioning in GCS buckets"
  type        = bool
  default     = false
}

variable "enable_uniform_access" {
  description = "Enable uniform bucket-level access"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

