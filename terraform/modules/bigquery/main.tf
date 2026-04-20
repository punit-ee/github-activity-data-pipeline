resource "google_bigquery_dataset" "raw" {
  dataset_id                  = var.raw_dataset_id
  friendly_name               = "GitHub Archive Raw Data"
  description                 = "Raw GitHub events data ingested from GitHub Archive"
  location                    = var.region
  default_table_expiration_ms = null
  labels                      = var.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  delete_contents_on_destroy = !var.enable_deletion_protection
}

resource "google_bigquery_dataset" "staging" {
  dataset_id                  = var.staging_dataset_id
  friendly_name               = "GitHub Archive Staging"
  description                 = "Staging layer for dbt transformations"
  location                    = var.region
  default_table_expiration_ms = null
  labels                      = var.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  delete_contents_on_destroy = !var.enable_deletion_protection
}

resource "google_bigquery_dataset" "marts" {
  dataset_id                  = var.marts_dataset_id
  friendly_name               = "GitHub Archive Data Marts"
  description                 = "Curated data marts for analytics and dashboards"
  location                    = var.region
  default_table_expiration_ms = null
  labels                      = var.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  delete_contents_on_destroy = !var.enable_deletion_protection
}

resource "google_bigquery_table" "github_events" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "github_events"
  deletion_protection = var.enable_deletion_protection
  labels              = var.labels
  description         = "Raw GitHub events partitioned by event_date and clustered"

  time_partitioning {
    type                     = "DAY"
    field                    = "event_date"
    expiration_ms            = var.partition_expiration_days != null ? var.partition_expiration_days * 24 * 60 * 60 * 1000 : null
    require_partition_filter = true
  }

  clustering = ["event_type", "repo_id", "actor_id"]

  schema = file("${path.module}/schemas/github_events.json")
}

