output "raw_data_bucket_name" {
  description = "Raw data bucket name"
  value       = google_storage_bucket.raw_data.name
}

output "raw_data_bucket_url" {
  description = "Raw data bucket URL"
  value       = google_storage_bucket.raw_data.url
}

output "archive_bucket_name" {
  description = "Archive bucket name"
  value       = google_storage_bucket.archive.name
}

output "archive_bucket_url" {
  description = "Archive bucket URL"
  value       = google_storage_bucket.archive.url
}

