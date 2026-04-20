resource "google_service_account" "airflow" {
  account_id   = var.airflow_sa_name
  display_name = "Airflow Service Account"
  description  = "Service account for Airflow to ingest data to BigQuery"
}

resource "google_service_account" "dbt" {
  account_id   = var.dbt_sa_name
  display_name = "dbt Service Account"
  description  = "Service account for dbt transformations"
}

resource "google_project_iam_member" "airflow_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "dbt_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_project_iam_member" "dbt_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "raw_airflow_editor" {
  dataset_id = var.raw_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_bigquery_dataset_iam_member" "staging_dbt_editor" {
  dataset_id = var.staging_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "marts_dbt_editor" {
  dataset_id = var.marts_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "raw_dbt_viewer" {
  dataset_id = var.raw_dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_service_account_key" "airflow" {
  service_account_id = google_service_account.airflow.name
}

resource "google_service_account_key" "dbt" {
  service_account_id = google_service_account.dbt.name
}

