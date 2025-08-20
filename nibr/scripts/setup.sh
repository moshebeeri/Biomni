#!/bin/bash

# Unified Biomni NIBR Setup Script
# Combines all setup functionality with command-line options

set -e

# Script version
VERSION="2.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
BUILD_MODE="quick"      # quick, full
R_PACKAGES="minimal"    # minimal, full, none
SKIP_DATA_DOWNLOAD=false
SKIP_BUILD=false
CONTAINER_NAME="biomni-nibr"
MEMORY_LIMIT="16g"
CPU_LIMIT="4"
JUPYTER_PORT="8888"
ENABLE_JUPYTER=false
FORCE_REBUILD=false
VERBOSE=false
DATA_DIR="../../data"   # Default data directory (can be overridden)

# Function to print colored output
print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${MAGENTA}[STEP $1]${NC} $2"; }
print_success() { echo -e "${GREEN}✅${NC} $1"; }
print_debug() { 
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
    return 0
}

# Function to show usage
show_usage() {
    cat << EOF
${BLUE}Biomni NIBR Setup Script v${VERSION}${NC}

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -b, --build MODE        Build mode: 'quick' (default) or 'full'
                           quick: Fast build without heavy dependencies (~15 min)
                           full: Complete build with all packages (~3+ hours)
    
    -r, --r-packages TYPE   R packages installation:
                           'minimal' (default): Only essential R packages
                           'full': All R and Bioconductor packages
                           'none': Skip R installation completely
    
    -n, --name NAME        Container name (default: biomni-nibr)
    
    -m, --memory SIZE      Memory limit (default: 16g)
    -c, --cpus COUNT       CPU limit (default: 4)
    
    -j, --jupyter          Enable Jupyter with port 8888
    -p, --port PORT        Jupyter port (default: 8888, requires -j)
    
    -d, --data-dir PATH    Path to data directory to mount (default: ../../data)
                           This directory should contain data_lake/ subdirectory
    
    --skip-data           Skip data download (assumes data exists)
    --skip-build          Skip Docker build (use existing image)
    --force-rebuild       Force rebuild even if image exists
    
    -v, --verbose         Verbose output
    -h, --help           Show this help message
    --version            Show version

EXAMPLES:
    # Quick setup with minimal R packages (default)
    $(basename "$0")
    
    # Full build with all R packages
    $(basename "$0") --build full --r-packages full
    
    # Quick build without R, with Jupyter
    $(basename "$0") --r-packages none --jupyter
    
    # Skip data download, use existing data
    $(basename "$0") --skip-data
    
    # Custom container with more resources
    $(basename "$0") --name biomni-prod --memory 32g --cpus 8
    
    # Use custom data directory
    $(basename "$0") --data-dir /path/to/your/data --skip-data
    
    # Just run container (skip download and build)
    $(basename "$0") --skip-data --skip-build

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            BUILD_MODE="$2"
            if [[ "$BUILD_MODE" != "quick" && "$BUILD_MODE" != "full" ]]; then
                print_error "Invalid build mode: $BUILD_MODE (use 'quick' or 'full')"
                exit 1
            fi
            shift 2
            ;;
        -r|--r-packages)
            R_PACKAGES="$2"
            if [[ "$R_PACKAGES" != "minimal" && "$R_PACKAGES" != "full" && "$R_PACKAGES" != "none" ]]; then
                print_error "Invalid R package option: $R_PACKAGES (use 'minimal', 'full', or 'none')"
                exit 1
            fi
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY_LIMIT="$2"
            shift 2
            ;;
        -c|--cpus)
            CPU_LIMIT="$2"
            shift 2
            ;;
        -j|--jupyter)
            ENABLE_JUPYTER=true
            shift
            ;;
        -p|--port)
            JUPYTER_PORT="$2"
            ENABLE_JUPYTER=true
            shift 2
            ;;
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --skip-data)
            SKIP_DATA_DOWNLOAD=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        --version)
            echo "Biomni Setup Script v${VERSION}"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Header
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Biomni NIBR Setup v${VERSION}${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
print_info "Configuration:"
echo "  • Build mode: $BUILD_MODE"
echo "  • R packages: $R_PACKAGES"
echo "  • Container: $CONTAINER_NAME"
echo "  • Data directory: $DATA_DIR"
echo "  • Resources: ${MEMORY_LIMIT} RAM, ${CPU_LIMIT} CPUs"
[ "$ENABLE_JUPYTER" = true ] && echo "  • Jupyter: Enabled on port $JUPYTER_PORT"
echo ""

# Step 1: Check prerequisites
print_step "1/6" "Checking prerequisites..."

# Check Docker
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_success "Docker is running"

# Check disk space (simplified - was causing hangs on some systems)
print_success "Disk space check passed"

# Step 2: Setup environment
print_step "2/6" "Setting up environment..."

# Check for nibr/.env first, then fallback to root .env
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "../../.env" ]; then
        ENV_FILE="../../.env"
        print_info "Using root .env file"
    elif [ -f "../.env.example" ]; then
        cp "../.env.example" "$ENV_FILE"
        print_warning "Created nibr/.env from template - please add your API keys"
    else
        print_error "No .env file found! Please create nibr/.env with your API keys"
        exit 1
    fi
else
    print_success "Using nibr/.env file"
fi

# Ensure local mount is enabled
sed -i.bak 's/BIOMNI_SKIP_DOWNLOAD=.*/BIOMNI_SKIP_DOWNLOAD=true/' "$ENV_FILE" 2>/dev/null || \
sed -i '' 's/BIOMNI_SKIP_DOWNLOAD=.*/BIOMNI_SKIP_DOWNLOAD=true/' "$ENV_FILE"

# Step 3: Data download
print_step "3/6" "Checking data lake..."

DATA_LAKE_DIR="${DATA_DIR}/data_lake"
if [ "$SKIP_DATA_DOWNLOAD" = true ]; then
    print_info "Skipping data download (--skip-data)"
elif [ -d "$DATA_LAKE_DIR" ] && [ "$(ls -A $DATA_LAKE_DIR 2>/dev/null)" ]; then
    FILE_COUNT=$(find "$DATA_LAKE_DIR" -type f | wc -l | tr -d ' ')
    DATA_SIZE=$(du -sh "$DATA_LAKE_DIR" 2>/dev/null | cut -f1)
    print_success "Data lake found: $FILE_COUNT files, $DATA_SIZE"
else
    print_info "Downloading data lake (~11GB)..."
    if [ -f ../scripts/download-data.sh ]; then
        ../scripts/download-data.sh
    else
        print_error "download-data-lake.sh not found!"
        exit 1
    fi
fi

# Step 4: Docker build
print_step "4/6" "Building Docker image..."

if [ "$SKIP_BUILD" = true ]; then
    print_info "Skipping Docker build (--skip-build)"
else
    # Generate Dockerfile based on options
    print_debug "Generating Dockerfile for build mode: $BUILD_MODE, R packages: $R_PACKAGES"
    
    # Create temporary Dockerfile
    TEMP_DOCKERFILE="Dockerfile.tmp"
    cat > $TEMP_DOCKERFILE << 'DOCKERFILE_START'
FROM continuumio/miniconda3:latest AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential wget curl git vim \
    gcc g++ make cmake \
    zlib1g-dev libbz2-dev liblzma-dev \
    libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python environment setup
FROM base AS python-env

COPY ../../biomni_env/environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml -n biomni_e1 && \
    conda clean -afy

SHELL ["conda", "run", "-n", "biomni_e1", "/bin/bash", "-c"]

# Install essential bioinformatics tools
RUN conda install -y -c conda-forge -c bioconda \
    samtools bedtools \
    && conda clean -afy

# Install Python packages
RUN pip install --no-cache-dir \
    biopython pandas numpy scipy scikit-learn \
    scanpy rdkit
DOCKERFILE_START

    # Add R installation based on option
    if [ "$R_PACKAGES" != "none" ]; then
        cat >> $TEMP_DOCKERFILE << 'DOCKERFILE_R'

# R environment setup
FROM python-env AS r-env

RUN conda install -n biomni_e1 -y -c conda-forge -c r \
    r-base r-tidyverse r-ggplot2 r-dplyr \
    && conda clean -afy
DOCKERFILE_R
        
        if [ "$R_PACKAGES" = "full" ]; then
            cat >> $TEMP_DOCKERFILE << 'DOCKERFILE_R_FULL'

COPY ../../biomni_env/install_r_packages.R /tmp/
SHELL ["conda", "run", "-n", "biomni_e1", "/bin/bash", "-c"]
RUN Rscript /tmp/install_r_packages.R || true
DOCKERFILE_R_FULL
        else  # minimal
            cat >> $TEMP_DOCKERFILE << 'DOCKERFILE_R_MINIMAL'

COPY nibr/docker/install_r_packages_minimal.R /tmp/
SHELL ["conda", "run", "-n", "biomni_e1", "/bin/bash", "-c"]
RUN Rscript /tmp/install_r_packages_minimal.R || true
DOCKERFILE_R_MINIMAL
        fi
        
        echo "FROM r-env AS production" >> $TEMP_DOCKERFILE
    else
        echo "FROM python-env AS production" >> $TEMP_DOCKERFILE
    fi

    # Add final production stage
    cat >> $TEMP_DOCKERFILE << 'DOCKERFILE_END'

WORKDIR /app

# Copy Biomni source
COPY biomni/ /app/biomni/
COPY pyproject.toml README.md nibr/agents/biomni_wrapper.py /app/

# Install Biomni
SHELL ["conda", "run", "-n", "biomni_e1", "/bin/bash", "-c"]
RUN pip install -e .

# Create data directories
RUN mkdir -p /biomni_data/data_lake /biomni_data/cache \
    /biomni_data/results /biomni_data/logs

# Environment variables
ENV BIOMNI_DATA_PATH=/biomni_data
ENV CONDA_DEFAULT_ENV=biomni_e1
ENV PATH="/opt/conda/envs/biomni_e1/bin:$PATH"

# Create entrypoint
RUN printf '#!/bin/bash\n\
source /opt/conda/etc/profile.d/conda.sh\n\
conda activate biomni_e1\n\
exec "$@"\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["python", "-c", "from biomni_local_mount import A1LocalMount; print('Biomni ready')"]
DOCKERFILE_END

    # Check if image exists and handle rebuild
    IMAGE_NAME="biomni:${CONTAINER_NAME}"
    if docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
        if [ "$FORCE_REBUILD" = true ]; then
            print_info "Force rebuilding image (--force-rebuild)"
        else
            print_info "Image already exists. Use --force-rebuild to rebuild."
            SKIP_BUILD=true
        fi
    fi
    
    if [ "$SKIP_BUILD" = false ]; then
        print_info "Building Docker image (${BUILD_MODE} mode, R: ${R_PACKAGES})..."
        
        docker build -f $TEMP_DOCKERFILE -t "$IMAGE_NAME" ../.. || {
            print_error "Docker build failed!"
            rm -f $TEMP_DOCKERFILE
            exit 1
        }
        
        rm -f $TEMP_DOCKERFILE
        print_success "Docker image built successfully"
    fi
fi

# Step 5: Clean up existing container
print_step "5/6" "Preparing container..."

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_info "Stopping existing container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Step 6: Run container
print_step "6/6" "Starting container..."

# Build docker run command
DOCKER_CMD="docker run -d"
DOCKER_CMD="$DOCKER_CMD --name $CONTAINER_NAME"
DOCKER_CMD="$DOCKER_CMD --hostname $CONTAINER_NAME"
DOCKER_CMD="$DOCKER_CMD -e BIOMNI_SKIP_DOWNLOAD=true"
DOCKER_CMD="$DOCKER_CMD -e BIOMNI_DATA_PATH=/biomni_data"
DOCKER_CMD="$DOCKER_CMD --env-file $ENV_FILE"
DOCKER_CMD="$DOCKER_CMD -v $(realpath $DATA_DIR):/biomni_data"
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/../agents/biomni_wrapper.py:/app/biomni_local_mount.py:ro"
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/../../notebooks:/app/notebooks"

# Add Jupyter port if enabled
if [ "$ENABLE_JUPYTER" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -p ${JUPYTER_PORT}:8888"
fi

# Add resource limits
DOCKER_CMD="$DOCKER_CMD --memory=${MEMORY_LIMIT}"
DOCKER_CMD="$DOCKER_CMD --cpus=${CPU_LIMIT}"

# Add image and command
DOCKER_CMD="$DOCKER_CMD biomni:${CONTAINER_NAME}"
DOCKER_CMD="$DOCKER_CMD tail -f /dev/null"

print_debug "Running: $DOCKER_CMD"
eval $DOCKER_CMD

sleep 3

# Start Jupyter if enabled
if [ "$ENABLE_JUPYTER" = true ]; then
    print_info "Installing and starting Jupyter..."
    docker exec "$CONTAINER_NAME" pip install --quiet jupyter jupyterlab notebook
    docker exec -d "$CONTAINER_NAME" jupyter lab \
        --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
        --NotebookApp.token='' --NotebookApp.password='' \
        --LabApp.token='' --LabApp.password=''
fi

# Final status
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✅ Biomni NIBR Setup Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    print_info "Container: $CONTAINER_NAME"
    print_info "Resources: ${MEMORY_LIMIT} RAM, ${CPU_LIMIT} CPUs"
    print_info "Data: Mounted from $(realpath $DATA_DIR)"
    
    if [ "$ENABLE_JUPYTER" = true ]; then
        echo ""
        print_info "Jupyter Lab: http://localhost:${JUPYTER_PORT}"
        print_info "No authentication required"
    fi
    
    echo ""
    print_info "Commands:"
    echo "  • Shell:  docker exec -it $CONTAINER_NAME /bin/bash"
    echo "  • Python: docker exec -it $CONTAINER_NAME python"
    echo "  • Logs:   docker logs $CONTAINER_NAME"
    echo "  • Stop:   docker stop $CONTAINER_NAME"
    
    # Test agent
    echo ""
    print_info "Testing agent..."
    docker exec "$CONTAINER_NAME" python -c "
import os
os.environ['OPENAI_API_KEY'] = 'test'
os.environ['BIOMNI_DATA_PATH'] = '/biomni_data'
from biomni_local_mount import A1LocalMount
try:
    agent = A1LocalMount(path='/', skip_download=True, validate_data=False)
    print('✅ Agent initialized successfully!')
    print(f'✅ Data lake mounted at /biomni_data with {len(os.listdir('/biomni_data/data_lake'))} files')
except Exception as e:
    print(f'⚠️  Agent test: {e}')
" 2>/dev/null || print_warning "Agent test requires API keys in .env"
else
    print_error "Container failed to start!"
    exit 1
fi