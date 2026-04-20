output "airflow_sa_email" {
  description = "Airflow service account email"
  value       = google_service_account.airflow.email
}

output "dbt_sa_email" {
  description = "dbt service account email"
  value       = google_service_account.dbt.email
}

output "airflow_sa_key" {
  description = "Airflow service account key (base64 encoded)"
  value       = google_service_account_key.airflow.private_key
  sensitive   = true
}

output "dbt_sa_key" {
  description = "dbt service account key (base64 encoded)"
  value       = google_service_account_key.dbt.private_key
  sensitive   = true
}

