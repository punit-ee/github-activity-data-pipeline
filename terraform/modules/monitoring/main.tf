resource "google_monitoring_alert_policy" "bigquery_slot_utilization" {
  display_name = "BigQuery Slot Utilization High"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Slot utilization > 80%"

    condition_threshold {
      filter          = "resource.type = \"bigquery_project\" AND metric.type = \"bigquery.googleapis.com/slots/total_allocated\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  documentation {
    content   = "BigQuery slot utilization is above 80%. Consider increasing slot reservations."
    mime_type = "text/markdown"
  }
}

resource "google_monitoring_alert_policy" "bigquery_query_execution_time" {
  display_name = "BigQuery Query Execution Time High"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Query execution time > 5 minutes"

    condition_threshold {
      filter          = "resource.type = \"bigquery_project\" AND metric.type = \"bigquery.googleapis.com/query/execution_times\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 300

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_99"
      }
    }
  }

  notification_channels = var.notification_channels

  documentation {
    content   = "BigQuery query execution time is above 5 minutes (99th percentile). Investigate slow queries."
    mime_type = "text/markdown"
  }
}

resource "google_monitoring_alert_policy" "storage_bytes_received" {
  display_name = "GCS Upload Rate Spike"
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "Upload rate 10x above baseline"

    condition_threshold {
      filter          = "resource.type = \"gcs_bucket\" AND metric.type = \"storage.googleapis.com/network/received_bytes_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10000000000

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.notification_channels

  documentation {
    content   = "GCS upload rate is significantly elevated. Verify ingestion pipeline."
    mime_type = "text/markdown"
  }
}

resource "google_logging_metric" "ingestion_errors" {
  name        = "github_archive_ingestion_errors"
  description = "Count of ingestion errors"

  filter = <<-EOT
    resource.type = "bigquery_dataset"
    resource.labels.dataset_id = "${var.raw_dataset_id}"
    severity >= ERROR
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"

    labels {
      key         = "error_type"
      value_type  = "STRING"
      description = "Type of error"
    }
  }

  label_extractors = {
    "error_type" = "EXTRACT(jsonPayload.error_type)"
  }
}

resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "GitHub Archive Pipeline - ${upper(var.environment)}"

    mosaicLayout = {
      columns = 12

      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "BigQuery Bytes Processed"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"bigquery_project\" AND metric.type = \"bigquery.googleapis.com/query/scanned_bytes\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          widget = {
            title = "BigQuery Query Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"bigquery_project\" AND metric.type = \"bigquery.googleapis.com/query/count\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          yPos   = 4
          widget = {
            title = "GCS Storage Used"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type = \"gcs_bucket\" AND metric.type = \"storage.googleapis.com/storage/total_bytes\""
                    aggregation = {
                      alignmentPeriod  = "3600s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
              }]
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          yPos   = 4
          widget = {
            title = "Ingestion Errors"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type = \"logging.googleapis.com/user/github_archive_ingestion_errors\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}

