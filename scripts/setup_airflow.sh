#!/bin/bash
# Setup script for Airflow with Docker
#
# This script:
# - Creates necessary directories
# - Sets up environment variables
# - Initializes Airflow
# - Starts all services

set -e

echo "🚀 Setting up Airflow with Docker"
echo "=================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs dags plugins
mkdir -p data/airflow

# Set up environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."

    # Get UID for Linux compatibility
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        AIRFLOW_UID=$(id -u)
    else
        AIRFLOW_UID=50000
    fi

    cat > .env << EOF
# Airflow Docker Configuration
AIRFLOW_UID=$AIRFLOW_UID
AIRFLOW_GID=0

# Airflow Web UI credentials
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# Pipeline Configuration
PIPELINE_MODE=local
STORAGE_BACKEND=minio
DATABASE_BACKEND=postgresql

# MinIO Settings
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=github-archive
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# PostgreSQL Settings
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=github_archive
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Download Settings
DOWNLOAD_OUTPUT_DIR=/tmp/github-archive
LOG_LEVEL=INFO
EOF

    echo "✅ Created .env file with UID: $AIRFLOW_UID"
else
    echo "⚠️  .env file already exists. Skipping..."
fi

echo ""
echo "🐳 Starting infrastructure services (MinIO + PostgreSQL)..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "🛫 Initializing Airflow..."
docker-compose -f docker-compose.airflow.yml up airflow-init

echo ""
echo "🌟 Starting Airflow services..."
docker-compose -f docker-compose.airflow.yml up -d

echo ""
echo "⏳ Waiting for Airflow to be ready..."
sleep 10

echo ""
echo "✅ Setup complete!"
echo ""
echo "=================================="
echo "📍 Access Points:"
echo "=================================="
echo ""
echo "  🌐 Airflow Web UI:"
echo "     URL: http://localhost:8080"
echo "     Username: airflow"
echo "     Password: airflow"
echo ""
echo "  📦 MinIO Console:"
echo "     URL: http://localhost:9001"
echo "     Username: minioadmin"
echo "     Password: minioadmin"
echo ""
echo "  🗄️  pgAdmin:"
echo "     URL: http://localhost:5050"
echo "     Email: admin@admin.com"
echo "     Password: admin"
echo ""
echo "=================================="
echo "🎯 Next Steps:"
echo "=================================="
echo ""
echo "  1. Open Airflow UI: http://localhost:8080"
echo "  2. Enable the 'github_archive_pipeline' DAG"
echo "  3. Trigger a manual run or wait for scheduled run"
echo ""
echo "📊 Useful Commands:"
echo "  - View logs: docker-compose -f docker-compose.airflow.yml logs -f"
echo "  - Stop: docker-compose -f docker-compose.airflow.yml down"
echo "  - Restart: docker-compose -f docker-compose.airflow.yml restart"
echo ""
echo "✨ Happy orchestrating! 🚀"

