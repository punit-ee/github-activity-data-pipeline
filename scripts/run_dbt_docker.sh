#!/bin/bash
# Script to run dbt models in Docker

set -e

echo "Running dbt models in Docker..."

# Ensure network exists
docker network create github-archive-network 2>/dev/null || true

# Build dbt image
echo "Building dbt Docker image..."
docker build -f Dockerfile.dbt -t github-archive-dbt:latest .

# Run dbt deps
echo "Installing dbt packages..."
docker run --rm \
    --network github-archive-network \
    -e POSTGRES_HOST=${POSTGRES_HOST:-postgres} \
    -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    -e POSTGRES_DATABASE=${POSTGRES_DATABASE:-github_archive} \
    github-archive-dbt:latest \
    dbt deps

# Run dbt staging models
echo "Running staging models..."
docker run --rm \
    --network github-archive-network \
    -e POSTGRES_HOST=${POSTGRES_HOST:-postgres} \
    -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    -e POSTGRES_DATABASE=${POSTGRES_DATABASE:-github_archive} \
    github-archive-dbt:latest \
    dbt run --select staging.* --target docker

# Run dbt mart models
echo "Running mart models..."
docker run --rm \
    --network github-archive-network \
    -e POSTGRES_HOST=${POSTGRES_HOST:-postgres} \
    -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    -e POSTGRES_DATABASE=${POSTGRES_DATABASE:-github_archive} \
    github-archive-dbt:latest \
    dbt run --select marts.* --target docker

# Run dbt tests
echo "Running dbt tests..."
docker run --rm \
    --network github-archive-network \
    -e POSTGRES_HOST=${POSTGRES_HOST:-postgres} \
    -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    -e POSTGRES_DATABASE=${POSTGRES_DATABASE:-github_archive} \
    github-archive-dbt:latest \
    dbt test --target docker

echo "✅ dbt run complete!"

