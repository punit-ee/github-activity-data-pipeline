project_id             = "your-gcp-project-prod"
region                 = "us-central1"
environment            = "prod"
terraform_state_bucket = "github-archive-terraform-state-prod"

raw_dataset_id     = "raw"
staging_dataset_id = "staging"
marts_dataset_id   = "marts"

partition_expiration_days  = null
enable_deletion_protection = true

airflow_sa_name = "github-archive-airflow-prod"
dbt_sa_name     = "github-archive-dbt-prod"

raw_data_bucket_name = "github-archive-raw-data-prod"
archive_bucket_name  = "github-archive-archive-prod"

lifecycle_age_days    = 90
enable_versioning     = true
enable_uniform_access = true

notification_channels = []

labels = {
  team        = "data-engineering"
  cost_center = "engineering"
  application = "github-archive"
}

