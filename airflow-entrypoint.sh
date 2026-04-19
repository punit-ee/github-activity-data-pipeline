#!/bin/bash
# Airflow container entrypoint wrapper
# This script installs dbt packages before starting the Airflow service

set -e

echo "Checking for dbt packages..."
if [ ! -d "/opt/airflow/dbt_packages/dbt_utils" ]; then
    echo "Installing dbt packages..."
    cd /opt/airflow
    dbt deps --profiles-dir /opt/airflow --project-dir /opt/airflow
    echo "✅ dbt packages installed successfully"
else
    echo "✅ dbt packages already installed"
fi

# Execute the original entrypoint with all arguments
exec /entrypoint "$@"

