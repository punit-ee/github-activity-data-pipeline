#!/bin/bash
# Stop all GitHub Archive Data Pipeline services

set -e

RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Stopping GitHub Archive Data Pipeline${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Stop dbt services
echo -e "${BLUE}Stopping dbt services...${NC}"
docker-compose -f docker-compose.dbt.yml down
echo -e "${GREEN}✓ dbt services stopped${NC}"

# Stop Airflow services
echo -e "\n${BLUE}Stopping Airflow services...${NC}"
docker-compose -f docker-compose.airflow.yml down
echo -e "${GREEN}✓ Airflow services stopped${NC}"

# Stop infrastructure services
echo -e "\n${BLUE}Stopping infrastructure services...${NC}"
docker-compose down
echo -e "${GREEN}✓ Infrastructure services stopped${NC}"

echo ""
echo -e "${GREEN}All services stopped successfully${NC}"
echo ""

echo -e "${BLUE}To start again, run:${NC}"
echo -e "  ./start.sh"
echo ""

