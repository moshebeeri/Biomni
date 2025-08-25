#!/bin/bash

# NIBR Biomni Container Status Script
# Quick status check for all containers

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.full-stack.yml"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  NIBR Biomni Container Status${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to check container status
check_container() {
    local container=$1
    local friendly_name=$2
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container}$"; then
        local status=$(docker ps --filter "name=${container}" --format "{{.Status}}")
        echo -e "${GREEN}✓${NC} ${friendly_name}: ${GREEN}Running${NC} (${status})"
        
        # Show ports if exposed
        local ports=$(docker ps --filter "name=${container}" --format "{{.Ports}}" | sed 's/0.0.0.0://g' | sed 's/->.*//g' | tr ',' ' ')
        if [ -n "$ports" ]; then
            echo "  Ports: $ports"
        fi
        
        # Special case for biomni-agent - show Jupyter status
        if [ "$container" = "biomni-agent" ] && [ -n "$ports" ] && [[ "$ports" == *"8888"* ]]; then
            echo "  Jupyter: http://localhost:8888?token=biomni"
        fi
    else
        if docker ps -a --format "table {{.Names}}" | grep -q "^${container}$"; then
            echo -e "${YELLOW}○${NC} ${friendly_name}: ${YELLOW}Stopped${NC}"
        else
            echo -e "${RED}✗${NC} ${friendly_name}: ${RED}Not Found${NC}"
        fi
    fi
}

# Check core services
echo -e "${BLUE}Core Services:${NC}"
check_container "biomni-agent" "Biomni Agent (with Jupyter)"
echo ""

# Check Canvas services
echo -e "${BLUE}Canvas Services:${NC}"
check_container "canvas-backend" "Canvas Backend"
check_container "canvas-frontend" "Canvas Frontend"
echo ""

# Check supporting services
echo -e "${BLUE}Supporting Services:${NC}"
check_container "postgres" "PostgreSQL"
check_container "redis" "Redis Cache"
check_container "nginx" "Nginx Proxy"
echo ""

# Show resource usage
echo -e "${BLUE}Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "biomni|canvas|postgres|redis|nginx" || echo "No containers running"
echo ""

# Show access URLs if services are running
if docker ps --format "{{.Names}}" | grep -q "canvas-frontend"; then
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Canvas UI:    ${GREEN}http://localhost:3000${NC}"
fi
if docker ps --format "{{.Names}}" | grep -q "canvas-backend"; then
    echo -e "  Backend API:  ${GREEN}http://localhost:54367${NC}"
fi
if docker ps --format "{{.Names}}" | grep -q "biomni-agent"; then
    echo -e "  Jupyter Lab:  ${GREEN}http://localhost:8888?token=biomni${NC} (integrated in biomni-agent)"
fi

echo ""
echo -e "${BLUE}Quick Actions:${NC}"
echo "  Start all:     docker-compose -f $COMPOSE_FILE up -d"
echo "  Stop all:      docker-compose -f $COMPOSE_FILE down"
echo "  View logs:     docker-compose -f $COMPOSE_FILE logs -f [service]"
echo "  Rebuild:       ./rebuild-containers.sh --all"