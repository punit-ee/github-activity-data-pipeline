output "metabase_url" {
  description = "URL to access Metabase"
  value       = google_cloud_run_service.metabase.status[0].url
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_service.metabase.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.metabase.connection_name
}

output "service_account_email" {
  description = "Service account email for Metabase"
  value       = google_service_account.metabase.email
}

