variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "airflow_sa_name" {
  description = "Airflow service account name"
  type        = string
}

variable "dbt_sa_name" {
  description = "dbt service account name"
  type        = string
}

variable "raw_dataset_id" {
  description = "Raw dataset ID"
  type        = string
}

variable "staging_dataset_id" {
  description = "Staging dataset ID"
  type        = string
}

variable "marts_dataset_id" {
  description = "Marts dataset ID"
  type        = string
}

