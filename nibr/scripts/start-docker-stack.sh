#!/bin/bash

# NIBR Biomni + Canvas Docker Stack Launcher
# This script manages the containerized deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.full-stack.yml"
ENV_FILE="../.env"
CANVAS_ENV_FILE="canvas/.env"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            print_error "Docker Compose is not installed"
            exit 1
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Check environment files
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found. Creating from template..."
        if [ -f "../.env.example" ]; then
            cp ../.env.example "$ENV_FILE"
            print_warning "Please edit $ENV_FILE with your API keys"
            exit 1
        else
            print_error "No .env.example file found"
            exit 1
        fi
    fi
    
    # Check Canvas environment file
    if [ ! -f "$CANVAS_ENV_FILE" ]; then
        print_warning "Canvas environment file not found. Creating from template..."
        if [ -f "canvas/.env.docker" ]; then
            cp canvas/.env.docker "$CANVAS_ENV_FILE"
            print_warning "Please edit $CANVAS_ENV_FILE with your settings"
        fi
    fi
    
    # Check data directory
    if [ ! -d "../data/data_lake" ]; then
        print_warning "Data lake directory not found at ../data/data_lake"
        print_warning "Please ensure Biomni data is downloaded or mounted"
    fi
    
    print_status "Prerequisites check complete"
}

# Function to build images
build_images() {
    print_status "Building Docker images..."
    
    # Build Biomni image
    print_status "Building Biomni image..."
    docker build -f docker/Dockerfile.nibr -t nibr/biomni:latest ..
    
    # Build Canvas images
    print_status "Building Canvas backend image..."
    docker build -f canvas/Dockerfile.backend -t nibr/canvas-backend:latest canvas/
    
    print_status "Building Canvas frontend image..."
    docker build -f canvas/Dockerfile.frontend -t nibr/canvas-frontend:latest canvas/
    
    print_status "All images built successfully"
}

# Function to start services
start_services() {
    local profile=$1
    
    if [ "$profile" = "dev" ]; then
        print_status "Starting development stack with Jupyter..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" --profile dev up -d
    elif [ "$profile" = "production" ]; then
        print_status "Starting production stack with database and cache..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" --profile production up -d
    else
        print_status "Starting default stack..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    fi
    
    print_status "Waiting for services to become healthy..."
    sleep 10
    
    # Check service health
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
}

# Function to stop services
stop_services() {
    print_status "Stopping all services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down
}

# Function to view logs
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f
    else
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

# Function to clean up
cleanup() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" down -v --remove-orphans
        print_status "Cleanup complete"
    fi
}

# Main menu
show_menu() {
    echo "================================================"
    echo "    NIBR Biomni + Canvas Docker Manager"
    echo "================================================"
    echo "1) Start default stack"
    echo "2) Start development stack (with Jupyter)"
    echo "3) Start production stack (with DB & cache)"
    echo "4) Stop all services"
    echo "5) Build/rebuild images"
    echo "6) View logs (all services)"
    echo "7) View specific service logs"
    echo "8) Show service status"
    echo "9) Clean up (remove all)"
    echo "0) Exit"
    echo "================================================"
}

# Main script
main() {
    check_prerequisites
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select option: " choice
            
            case $choice in
                1)
                    start_services
                    print_status "Canvas UI: http://localhost:3000"
                    print_status "Backend API: http://localhost:54367"
                    ;;
                2)
                    start_services "dev"
                    print_status "Canvas UI: http://localhost:3000"
                    print_status "Backend API: http://localhost:54367"
                    print_status "Jupyter Lab: http://localhost:8888 (token: biomni)"
                    ;;
                3)
                    start_services "production"
                    print_status "Canvas UI: http://localhost:3000"
                    print_status "Backend API: http://localhost:54367"
                    print_status "PostgreSQL: localhost:5432"
                    print_status "Redis: localhost:6379"
                    ;;
                4)
                    stop_services
                    ;;
                5)
                    build_images
                    ;;
                6)
                    view_logs
                    ;;
                7)
                    echo "Available services:"
                    $COMPOSE_CMD -f "$COMPOSE_FILE" ps --services
                    read -p "Enter service name: " service
                    view_logs "$service"
                    ;;
                8)
                    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
                    ;;
                9)
                    cleanup
                    ;;
                0)
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            
            echo
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            start)
                start_services "${2:-}"
                ;;
            stop)
                stop_services
                ;;
            build)
                build_images
                ;;
            logs)
                view_logs "${2:-}"
                ;;
            status)
                $COMPOSE_CMD -f "$COMPOSE_FILE" ps
                ;;
            clean)
                cleanup
                ;;
            *)
                echo "Usage: $0 [start|stop|build|logs|status|clean]"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"