#!/bin/bash
# Unified startup script for GitHub Archive Data Pipeline
# Handles proper startup order and health checking

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}GitHub Archive Data Pipeline - Startup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Function to check if a container is healthy
check_health() {
    local container=$1
    local max_wait=$2
    local elapsed=0

    echo -e "${YELLOW}Waiting for $container to be healthy...${NC}"

    while [ $elapsed -lt $max_wait ]; do
        if docker ps --filter "name=$container" --filter "health=healthy" | grep -q $container; then
            echo -e "${GREEN}✓ $container is healthy${NC}"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done

    echo -e "\n${RED}✗ $container failed to become healthy${NC}"
    return 1
}

# Step 1: Create network if it doesn't exist
echo -e "\n${BLUE}Step 1: Creating Docker network...${NC}"
docker network create github-archive-network 2>/dev/null || echo "Network already exists"
echo -e "${GREEN}✓ Network ready${NC}"

# Step 2: Start infrastructure layer (PostgreSQL + MinIO)
echo -e "\n${BLUE}Step 2: Starting infrastructure (PostgreSQL + MinIO)...${NC}"
docker-compose up -d

echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check PostgreSQL health
check_health "github-archive-postgres" 60 || exit 1

# Check MinIO health
check_health "github-archive-minio" 60 || exit 1

# Step 3: Start Airflow
echo -e "\n${BLUE}Step 3: Starting Airflow services...${NC}"
docker-compose -f docker-compose.airflow.yml up -d

echo -e "${YELLOW}Waiting for Airflow to initialize...${NC}"
sleep 15

# Check Airflow PostgreSQL
check_health "airflow-postgres" 60 || exit 1

# Wait for init to complete
echo -e "${YELLOW}Waiting for Airflow initialization to complete...${NC}"
docker wait airflow-init 2>/dev/null || echo "Init already completed"

# Check Airflow Webserver
check_health "airflow-webserver" 120 || exit 1

# Check Airflow Scheduler
check_health "airflow-scheduler" 120 || exit 1

# Step 4: Start dbt container
echo -e "\n${BLUE}Step 4: Starting dbt container...${NC}"
docker-compose -f docker-compose.dbt.yml up -d

echo -e "${YELLOW}Waiting for dbt container to be ready...${NC}"
sleep 5

if docker ps --filter "name=github-archive-dbt" | grep -q github-archive-dbt; then
    echo -e "${GREEN}✓ dbt container is running${NC}"
else
    echo -e "${RED}✗ dbt container failed to start${NC}"
fi

# Step 5: Show status
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Resource usage
echo -e "${BLUE}Current resource usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -12
echo ""

# Access URLs
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${GREEN}  Airflow UI:     ${NC}http://localhost:8080  (airflow/airflow)"
echo -e "${GREEN}  MinIO Console:  ${NC}http://localhost:9001  (minioadmin/minioadmin)"
echo -e "${GREEN}  pgAdmin:        ${NC}http://localhost:5050  (admin@admin.com/admin)"
echo -e "${GREEN}  PostgreSQL:     ${NC}localhost:5432 (postgres/postgres)"
echo -e "${GREEN}  Airflow DB:     ${NC}localhost:5433 (airflow/airflow)"
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Open Airflow UI: http://localhost:8080"
echo -e "  2. Enable the DAGs you want to run"
echo -e "  3. Monitor execution"
echo ""

echo -e "${BLUE}To view logs:${NC}"
echo -e "  docker logs -f airflow-scheduler"
echo -e "  docker logs -f airflow-webserver"
echo -e "  docker logs -f github-archive-dbt"
echo ""

echo -e "${BLUE}To run dbt commands manually:${NC}"
echo -e "  docker exec -it github-archive-dbt dbt run --profiles-dir /root/.dbt"
echo -e "  docker exec -it github-archive-dbt dbt test --profiles-dir /root/.dbt"
echo ""

echo -e "${BLUE}To stop all services:${NC}"
echo -e "  ./stop.sh"
echo ""

