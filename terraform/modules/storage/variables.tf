variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCS bucket region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "labels" {
  description = "Labels to apply to buckets"
  type        = map(string)
}

variable "raw_data_bucket_name" {
  description = "Raw data bucket name"
  type        = string
}

variable "archive_bucket_name" {
  description = "Archive bucket name"
  type        = string
}

variable "lifecycle_age_days" {
  description = "Days before lifecycle transition"
  type        = number
}

variable "enable_versioning" {
  description = "Enable bucket versioning"
  type        = bool
}

variable "enable_uniform_access" {
  description = "Enable uniform bucket-level access"
  type        = bool
}

variable "airflow_sa_email" {
  description = "Airflow service account email"
  type        = string
}

