#!/bin/bash
# Start Metabase Dashboard for GitHub Archive Analytics

set -e

echo "🚀 Starting Metabase Dashboard..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if network exists
if ! docker network inspect github-archive-network >/dev/null 2>&1; then
    echo -e "${YELLOW}Creating docker network...${NC}"
    docker network create github-archive-network
fi

# Check if PostgreSQL is running
if ! docker ps | grep -q github-archive-postgres; then
    echo -e "${YELLOW}PostgreSQL not running. Starting services...${NC}"
    docker-compose -f docker-compose.yml up -d postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Create metabase database if it doesn't exist
echo -e "${YELLOW}Initializing Metabase database...${NC}"
docker exec github-archive-postgres psql -U postgres -tc \
  "SELECT 1 FROM pg_database WHERE datname = 'metabase'" | grep -q 1 || \
  docker exec github-archive-postgres psql -U postgres -c "CREATE DATABASE metabase;"

# Start Metabase
echo -e "${YELLOW}Starting Metabase container...${NC}"
docker-compose -f docker-compose.metabase.yml up -d metabase

# Wait for Metabase to be healthy
echo -e "${YELLOW}Waiting for Metabase to start (this may take 1-2 minutes)...${NC}"
attempt=0
max_attempts=60
until docker exec github-archive-metabase curl -sf http://localhost:3000/api/health >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Metabase failed to start. Check logs with: docker logs github-archive-metabase"
        exit 1
    fi
    echo -n "."
    sleep 3
done

echo ""
echo -e "${GREEN}✅ Metabase is ready!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 Metabase Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 URL: http://localhost:3000"
echo ""
echo "  📝 First-time setup:"
echo "     1. Create an admin account"
echo "     2. Add PostgreSQL database connection:"
echo "        - Host: postgres"
echo "        - Port: 5432"
echo "        - Database: github_archive"
echo "        - Username: postgres"
echo "        - Password: postgres"
echo "        - Schema: marts"
echo ""
echo "  📚 Documentation: metabase/README.md"
echo "  🔍 Sample queries: metabase/dashboard_queries.sql"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View logs: docker logs -f github-archive-metabase"
echo "Stop Metabase: docker-compose -f docker-compose.metabase.yml down"
echo ""
echo "password: Admin@Marts12"

