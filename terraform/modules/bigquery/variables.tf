variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "BigQuery dataset location"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
}

variable "raw_dataset_id" {
  description = "Raw dataset ID"
  type        = string
}

variable "staging_dataset_id" {
  description = "Staging dataset ID"
  type        = string
}

variable "marts_dataset_id" {
  description = "Marts dataset ID"
  type        = string
}

variable "partition_expiration_days" {
  description = "Days before partitions expire"
  type        = number
  default     = null
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

