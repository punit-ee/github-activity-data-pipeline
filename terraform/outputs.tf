output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "raw_dataset_id" {
  description = "Raw dataset ID"
  value       = module.bigquery.raw_dataset_id
}

output "staging_dataset_id" {
  description = "Staging dataset ID"
  value       = module.bigquery.staging_dataset_id
}

output "marts_dataset_id" {
  description = "Marts dataset ID"
  value       = module.bigquery.marts_dataset_id
}

output "raw_table_id" {
  description = "Raw events table ID"
  value       = module.bigquery.raw_table_id
}

output "airflow_service_account_email" {
  description = "Airflow service account email"
  value       = module.iam.airflow_sa_email
}

output "dbt_service_account_email" {
  description = "dbt service account email"
  value       = module.iam.dbt_sa_email
}

output "raw_data_bucket_name" {
  description = "Raw data GCS bucket name"
  value       = module.storage.raw_data_bucket_name
}

output "raw_data_bucket_url" {
  description = "Raw data GCS bucket URL"
  value       = module.storage.raw_data_bucket_url
}

output "archive_bucket_name" {
  description = "Archive GCS bucket name"
  value       = module.storage.archive_bucket_name
}

output "archive_bucket_url" {
  description = "Archive GCS bucket URL"
  value       = module.storage.archive_bucket_url
}

