resource "google_storage_bucket" "raw_data" {
  name          = var.raw_data_bucket_name
  location      = var.region
  storage_class = "STANDARD"
  labels        = var.labels

  uniform_bucket_level_access = var.enable_uniform_access

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days * 3
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  force_destroy = var.environment != "prod"
}

resource "google_storage_bucket" "archive" {
  name          = var.archive_bucket_name
  location      = var.region
  storage_class = "ARCHIVE"
  labels        = var.labels

  uniform_bucket_level_access = var.enable_uniform_access

  versioning {
    enabled = var.enable_versioning
  }

  force_destroy = var.environment != "prod"
}

resource "google_storage_bucket_iam_member" "raw_data_airflow_admin" {
  bucket = google_storage_bucket.raw_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.airflow_sa_email}"
}

resource "google_storage_bucket_iam_member" "archive_airflow_admin" {
  bucket = google_storage_bucket.archive.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.airflow_sa_email}"
}
