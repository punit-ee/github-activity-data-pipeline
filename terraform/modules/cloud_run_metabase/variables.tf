variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
}

variable "metabase_image" {
  description = "Metabase container image"
  type        = string
  default     = "metabase/metabase:v0.49.3"
}

variable "db_password" {
  description = "Database password for Metabase"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "VPC ID for private networking"
  type        = string
  default     = ""
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = string
  default     = "0"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = string
  default     = "10"
}

variable "allow_public_access" {
  description = "Allow public access to Metabase"
  type        = bool
  default     = true
}

