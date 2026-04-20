project_id              = "your-gcp-project-dev"
region                  = "us-central1"
environment             = "dev"
terraform_state_bucket  = "github-archive-terraform-state-dev"

raw_dataset_id     = "raw"
staging_dataset_id = "staging"
marts_dataset_id   = "marts"

partition_expiration_days  = 90
enable_deletion_protection = false

airflow_sa_name = "github-archive-airflow-dev"
dbt_sa_name     = "github-archive-dbt-dev"

raw_data_bucket_name = "github-archive-raw-data-dev"
archive_bucket_name  = "github-archive-archive-dev"

lifecycle_age_days    = 30
enable_versioning     = false
enable_uniform_access = true

labels = {
  team        = "data-engineering"
  cost_center = "engineering"
  application = "github-archive"
}

