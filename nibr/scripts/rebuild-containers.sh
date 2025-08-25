#!/bin/bash

# NIBR Biomni Container Rebuild Script
# This script manages container rebuilding for the NIBR Biomni stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.full-stack.yml"
PROJECT_NAME="nibr-biomni"

# Service definitions - using functions for compatibility
get_dockerfile() {
    case "$1" in
        biomni-agent)
            echo "docker/Dockerfile.nibr"
            ;;
        canvas-backend)
            echo "canvas/Dockerfile.backend.dev"
            ;;
        canvas-frontend)
            echo "canvas/Dockerfile.frontend.dev"
            ;;
    esac
}

get_build_context() {
    case "$1" in
        biomni-agent)
            echo ".."
            ;;
        canvas-backend|canvas-frontend)
            echo "canvas"
            ;;
    esac
}

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check if service exists
service_exists() {
    local service=$1
    docker-compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null
}

# Function to stop and remove a specific container
remove_container() {
    local service=$1
    print_info "Stopping and removing $service..."
    
    # Stop the container if running
    if docker-compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null | grep -q .; then
        docker-compose -f "$COMPOSE_FILE" stop "$service" 2>/dev/null || true
    fi
    
    # Remove the container
    docker-compose -f "$COMPOSE_FILE" rm -f "$service" 2>/dev/null || true
    
    # Remove the image if force rebuild
    if [ "$FORCE_REBUILD" = true ]; then
        local image_name
        case "$service" in
            biomni-agent)
                image_name="nibr/biomni"
                ;;
            canvas-backend)
                image_name="nibr/canvas-backend"
                ;;
            canvas-frontend)
                image_name="nibr/canvas-frontend"
                ;;
            *)
                return
                ;;
        esac
        
        print_info "Removing image $image_name..."
        docker rmi -f "$image_name:latest" 2>/dev/null || true
        docker rmi -f "$image_name:dev" 2>/dev/null || true
    fi
}

# Function to rebuild a specific service
rebuild_service() {
    local service=$1
    local dockerfile=$(get_dockerfile "$service")
    local context=$(get_build_context "$service")
    
    print_status "Rebuilding $service..."
    
    # Remove the old container
    remove_container "$service"
    
    # Build based on service type
    case "$service" in
        biomni-agent)
            print_info "Building Biomni agent (production)..."
            docker build \
                --target production \
                -f "$dockerfile" \
                -t nibr/biomni:latest \
                "$context"
            ;;
        canvas-backend)
            print_info "Building Canvas backend..."
            docker build \
                -f "$dockerfile" \
                -t nibr/canvas-backend:latest \
                "$context"
            ;;
        canvas-frontend)
            print_info "Building Canvas frontend..."
            docker build \
                -f "$dockerfile" \
                -t nibr/canvas-frontend:latest \
                "$context"
            ;;
        *)
            print_warning "No custom build for $service, using docker-compose..."
            docker-compose -f "$COMPOSE_FILE" build "$service"
            ;;
    esac
    
    print_status "$service rebuilt successfully"
}

# Function to rebuild all services
rebuild_all() {
    print_status "Rebuilding all services..."
    
    # Stop all containers
    print_info "Stopping all containers..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Remove volumes if force clean
    if [ "$FORCE_CLEAN" = true ]; then
        print_warning "Removing all volumes (data will be lost)..."
        docker-compose -f "$COMPOSE_FILE" down -v
    fi
    
    # Rebuild each service
    for service in biomni-agent canvas-backend canvas-frontend; do
        rebuild_service "$service"
    done
    
    print_status "All services rebuilt successfully"
}

# Function to start services after rebuild
start_services() {
    local profile=$1
    
    print_info "Starting services..."
    
    if [ -n "$profile" ]; then
        docker-compose -f "$COMPOSE_FILE" --profile "$profile" up -d
    else
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
    
    print_status "Services started"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [SERVICE]

Rebuild Docker containers for NIBR Biomni stack

OPTIONS:
    --all           Rebuild all containers
    --biomni        Rebuild Biomni agent container (includes Jupyter)
    --backend       Rebuild Canvas backend container
    --frontend      Rebuild Canvas frontend container
    --force         Force rebuild (remove images)
    --clean         Clean rebuild (remove volumes - DATA LOSS!)
    --start         Start services after rebuild
    --dev           Use development profile when starting
    --prod          Use production profile when starting
    --help          Show this help message

EXAMPLES:
    $0 --all                    # Rebuild all containers
    $0 --biomni --start         # Rebuild and start Biomni (with Jupyter)
    $0 --frontend --backend     # Rebuild Canvas services
    $0 --all --force --clean    # Complete clean rebuild

SHORTCUTS:
    $0 -a           Same as --all
    $0 -b           Same as --biomni
    $0 -k           Same as --backend
    $0 -f           Same as --frontend
    $0 -F           Same as --force
    $0 -C           Same as --clean
    $0 -s           Same as --start

EOF
}

# Function to check Docker status
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running or not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            print_error "Docker Compose is not installed"
            exit 1
        fi
    fi
}

# Parse arguments
REBUILD_BIOMNI=false
REBUILD_BACKEND=false
REBUILD_FRONTEND=false
REBUILD_ALL=false
FORCE_REBUILD=false
FORCE_CLEAN=false
START_AFTER=false
PROFILE=""

if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --all|-a)
            REBUILD_ALL=true
            shift
            ;;
        --biomni|-b)
            REBUILD_BIOMNI=true
            shift
            ;;
        --backend|-k)
            REBUILD_BACKEND=true
            shift
            ;;
        --frontend|-f)
            REBUILD_FRONTEND=true
            shift
            ;;
        --force|-F)
            FORCE_REBUILD=true
            shift
            ;;
        --clean|-C)
            FORCE_CLEAN=true
            FORCE_REBUILD=true
            shift
            ;;
        --start|-s)
            START_AFTER=true
            shift
            ;;
        --dev)
            PROFILE="dev"
            shift
            ;;
        --prod)
            PROFILE="production"
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_info "NIBR Biomni Container Rebuild Script"
print_info "====================================="

# Check Docker
check_docker

# Confirm destructive operations
if [ "$FORCE_CLEAN" = true ]; then
    print_warning "⚠️  FORCE CLEAN will remove all volumes and data!"
    read -p "Are you sure you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled"
        exit 0
    fi
fi

# Execute rebuilds
if [ "$REBUILD_ALL" = true ]; then
    rebuild_all
else
    # Rebuild individual services
    if [ "$REBUILD_BIOMNI" = true ]; then
        rebuild_service "biomni-agent"
    fi
    
    if [ "$REBUILD_BACKEND" = true ]; then
        rebuild_service "canvas-backend"
    fi
    
    if [ "$REBUILD_FRONTEND" = true ]; then
        rebuild_service "canvas-frontend"
    fi
fi

# Start services if requested
if [ "$START_AFTER" = true ]; then
    start_services "$PROFILE"
    
    print_info "Services are starting up..."
    print_info "Access points:"
    print_status "Canvas UI: http://localhost:3000"
    print_status "Backend API: http://localhost:54367"
    
    if [ "$PROFILE" = "dev" ]; then
        print_status "Jupyter Lab: http://localhost:8888"
    fi
fi

# Show container status
print_info ""
print_info "Container Status:"
docker-compose -f "$COMPOSE_FILE" ps

print_status "Rebuild complete!"

# Cleanup dangling images if force rebuild
if [ "$FORCE_REBUILD" = true ]; then
    print_info "Cleaning up dangling images..."
    docker image prune -f
fi