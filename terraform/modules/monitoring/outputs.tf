output "dashboard_url" {
  description = "Monitoring dashboard URL"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.main.id}"
}

