variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "notification_channels" {
  description = "List of notification channel IDs"
  type        = list(string)
}

variable "raw_dataset_id" {
  description = "Raw dataset ID for logging filters"
  type        = string
}

