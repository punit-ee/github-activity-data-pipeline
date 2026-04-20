output "raw_dataset_id" {
  description = "Raw dataset ID"
  value       = google_bigquery_dataset.raw.dataset_id
}

output "staging_dataset_id" {
  description = "Staging dataset ID"
  value       = google_bigquery_dataset.staging.dataset_id
}

output "marts_dataset_id" {
  description = "Marts dataset ID"
  value       = google_bigquery_dataset.marts.dataset_id
}

output "raw_table_id" {
  description = "Raw events table ID"
  value       = google_bigquery_table.github_events.table_id
}

output "raw_table_full_id" {
  description = "Full raw events table ID"
  value       = "${var.project_id}.${google_bigquery_dataset.raw.dataset_id}.${google_bigquery_table.github_events.table_id}"
}

