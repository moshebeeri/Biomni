# Biomni NIBR Deployment Guide

> **Note**: All NIBR-specific files are now organized under the `nibr/` directory to maintain clean separation from the upstream Biomni codebase.

## Overview

This guide documents the deployment of Biomni for NIBR (Novartis Institutes for BioMedical Research) using Docker containers with local data mounting. This setup is optimized for contractors and developers working on Mac machines with limited resources.

**Last Updated**: November 2024  
**Version**: 2.1.0-NIBR  
**Script Version**: nibr/scripts/setup.sh v2.1.0

## Documentation

### Container Documentation
- [Container Architecture](docs/container-architecture.md) - Service components and architecture overview
- [Build Process](docs/container-build.md) - Docker build process and optimization
- [Network Setup](docs/network-setup.md) - Network configuration and troubleshooting
- [Deployment Guide](docs/deployment-guide.md) - Step-by-step deployment instructions
- [Jupyter Integration](docs/jupyter-integration.md) - Jupyter Lab integration in biomni container
- [Legacy Docker Deployment](docs/docker-deployment-legacy.md) - Previous deployment approach

### Project Documentation
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Technical implementation roadmap
- [Next Plan](next-plan.md) - Current priorities and milestones (Updated Aug 25, 2025)

## Architecture

```
Mac Host (35GB free)
├── biomni/
│   ├── data/                    # 14GB local data lake
│   │   ├── data_lake/           # 76 biomedical datasets
│   │   └── benchmark/           # Test data
│   ├── Dockerfile.fast          # Optimized Docker build (no heavy R)
│   ├── biomni_local_mount.py   # Wrapper to skip S3 downloads
│   └── quick-tier2-setup.sh    # Automated setup script
│
Docker Container (biomni-nibr)
├── Memory: 16GB
├── CPUs: 4 cores
├── Mounted: /biomni_data → ./data
└── Image: 3.25GB
```

## Quick Start

### Prerequisites
- Mac with 35GB+ free disk space
- Docker Desktop installed and running
- 16GB+ RAM available

### One-Command Setup

```bash
# Option 1: From project root
cd nibr && ./scripts/setup.sh

# Option 2: From scripts directory  
cd nibr/scripts && ./setup.sh

# With Jupyter enabled
./scripts/setup.sh --jupyter

# Full build with all packages (slow)
./scripts/setup.sh --build full --r-packages full

# Skip R packages completely for fastest build
./scripts/setup.sh --r-packages none

# Custom resources
./scripts/setup.sh --memory 32g --cpus 8
```

The unified script supports:
- **Build modes**: `quick` (15 min) or `full` (3+ hours)
- **R packages**: `minimal`, `full`, or `none`
- **Jupyter**: Optional with `--jupyter`
- **Resources**: Configurable memory and CPU limits
- **Skip options**: `--skip-data`, `--skip-build`

### Script Options Reference

```bash
cd nibr/scripts && ./setup.sh [OPTIONS]

OPTIONS:
    -b, --build MODE        # 'quick' (default) or 'full'
    -r, --r-packages TYPE   # 'minimal' (default), 'full', or 'none'
    -n, --name NAME        # Container name (default: biomni-nibr)
    -m, --memory SIZE      # Memory limit (default: 16g)
    -c, --cpus COUNT       # CPU limit (default: 4)
    -j, --jupyter          # Enable Jupyter on port 8888
    -p, --port PORT        # Jupyter port (requires -j)
    --skip-data           # Skip data download
    --skip-build          # Skip Docker build
    --force-rebuild       # Force rebuild even if image exists
    -v, --verbose         # Verbose output
    -h, --help           # Show help
```

## Data Lake Details

### Current Data Status
- **Location**: `/Users/mb/projects/novartis/biomni/data/data_lake/`
- **Size**: 14GB
- **Files**: 76 biomedical datasets
- **Format**: Parquet, CSV, TSV, PKL, JSON files

### Key Datasets
| File | Size | Description |
|------|------|-------------|
| BindingDB_All_202409.tsv | 2.8GB | Drug-protein binding affinities |
| DepMap_*.csv | ~1.4GB | Cancer cell line dependencies |
| DisGeNET.parquet | 3MB | Gene-disease associations |
| gtex_tissue_gene_tpm.parquet | - | Gene expression across tissues |
| kg.csv | - | Precision medicine knowledge graph |

### Data Categories
- **Protein Interactions**: affinity_capture-ms, two-hybrid, co-fractionation
- **Drug Discovery**: BindingDB, Broad Repurposing Hub, DDInter databases
- **Cancer Research**: DepMap CRISPR screens, gene expression
- **Disease Genetics**: DisGeNET, OMIM, GWAS catalog
- **Gene Expression**: GTEx, proteinatlas
- **Single Cell**: CellxGene Census datasets

## Container Management

### Basic Commands

```bash
# Check status
docker ps -a | grep biomni-nibr

# Enter container shell
docker exec -it biomni-nibr /bin/bash

# Python interactive
docker exec -it biomni-nibr python

# View logs
docker logs biomni-nibr

# Stop/Start
docker stop biomni-nibr
docker start biomni-nibr

# Remove
docker stop biomni-nibr && docker rm biomni-nibr
```

### Resource Allocation
- **Memory**: 16GB limit, 8GB reserved
- **CPUs**: 4 cores maximum
- **Storage**: Read-only data mount + writable cache

## Using Biomni

### Python API

```python
# Inside container or via docker exec
# Note: biomni_wrapper.py is mounted as biomni_local_mount.py in container
from biomni_local_mount import A1LocalMount

# Initialize agent (skips S3 download, uses mounted data)
agent = A1LocalMount(
    path="/",
    skip_download=True,
    llm="gpt-4"  # or "claude-3", requires API key
)

# Run biomedical queries
result = agent.run("What genes are associated with Alzheimer's disease?")
print(result)
```

### Environment Configuration

Add API keys to `.env` file in the project root:
```bash
# Create .env in project root (not in nibr/)
cp nibr/config/.env.example .env
vi .env  # Add your API keys

# At least one LLM API key required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Local mount settings
BIOMNI_SKIP_DOWNLOAD=true
BIOMNI_LOCAL_DATA_PATH=./data
```

## Jupyter Notebook Access

### Option 1: Run Development Container

```bash
# Stop current container
docker stop biomni-nibr

# Run with Jupyter (port 8888)
docker run -d \
  --name biomni-nibr-jupyter \
  --hostname biomni-nibr \
  -p 8888:8888 \
  -e BIOMNI_SKIP_DOWNLOAD=true \
  -e JUPYTER_TOKEN=nibr \
  --env-file .env \
  -v "$(pwd)/data:/biomni_data" \
  -v "$(pwd)/biomni_local_mount.py:/app/biomni_local_mount.py:ro" \
  -v "$(pwd)/notebooks:/app/notebooks" \
  --memory="16g" \
  --cpus="4" \
  biomni:tier2 \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='nibr'
```

Access at: http://localhost:8888 (token: nibr)

### Option 2: Install Jupyter in Running Container

```bash
# Install Jupyter in existing container
docker exec biomni-nibr pip install jupyter jupyterlab

# Run Jupyter
docker exec -d biomni-nibr jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --NotebookApp.token='nibr'
```

## Optimizations Applied

### 1. Unified Setup Script
- **biomni-setup.sh**: Single script with flexible options
- **Build modes**: Quick (15 min) or Full (3+ hours)
- **R packages**: None, Minimal, or Full installation
- **Dynamic Dockerfile**: Generated based on options

### 2. Fast Docker Build
- **Default**: Quick build without heavy dependencies
- **Build time**: 10-15 minutes (quick) vs 3+ hours (full)
- **Image size**: 3.25GB optimized
- **Skip options**: `--skip-data`, `--skip-build` for faster reruns

### 3. Local Data Mount
- **No S3 downloads**: Uses pre-downloaded data
- **Performance**: Local SSD speed vs network
- **Cost**: No AWS charges
- **Offline**: Works without internet after initial download

### 4. Flexible R Package Management
- **None**: Skip R completely (fastest)
- **Minimal**: Only ggplot2, dplyr, tidyr (default)
- **Full**: All R and Bioconductor packages (slow)

## Troubleshooting

### Common Issues

#### 1. Container won't start
```bash
# Check logs
docker logs biomni-nibr

# Verify data mount
ls -la data/data_lake/

# Check Docker resources
docker system df
```

#### 2. Data not found in container
```bash
# Verify mount inside container
docker exec biomni-nibr ls -la /biomni_data/data_lake/

# Should show 76 files
```

#### 3. Out of memory
```bash
# Check Docker Desktop settings
# Preferences → Resources → Memory: 8GB+

# Monitor usage
docker stats biomni-nibr
```

#### 4. Build failures
```bash
# Clean Docker cache
docker system prune -a

# Use fast Dockerfile
docker build -f Dockerfile.fast -t biomni:tier2 .
```

## File Structure

```
biomni/
├── nibr/                        # All NIBR-specific files
│   ├── README.md               # This file (main NIBR guide)
│   ├── docker/                 # Container configurations
│   │   ├── Dockerfile.nibr     # Optimized NIBR Dockerfile
│   │   └── docker-compose.yml  # Multi-tier deployment
│   ├── scripts/                # Setup and utility scripts
│   │   ├── setup.sh           # Unified setup script v2.0.0
│   │   ├── download-data.sh   # Data lake download
│   │   └── jupyter-launch.sh  # Jupyter launcher
│   ├── config/                 # Configuration files
│   │   └── .env.example        # Environment template
│   ├── agents/                 # NIBR agent wrappers
│   │   └── biomni_wrapper.py  # Local mount wrapper
│   ├── data-layer/            # Data Layer implementation
│   ├── deployment/            # Deployment configurations
│   ├── docs/                  # Additional documentation
│   └── tests/                 # NIBR-specific tests
├── .env                        # Your API keys (git ignored)
└── data/
    ├── data_lake/             # 76 files, 14GB
    │   ├── BindingDB_All_202409.tsv
    │   ├── DisGeNET.parquet
    │   ├── DepMap_*.csv
    │   └── ... (73 more files)
    ├── benchmark/             # Test datasets
    ├── cache/                # Processing cache
    ├── results/              # Output directory
    └── logs/                 # Application logs
```

## Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Data download | 30-60 min | One-time, 11GB from S3 |
| Docker build (fast) | 10-15 min | Skips R packages |
| Docker build (full) | 3+ hours | With all R/Bioconductor |
| Container start | <5 sec | With mounted data |
| Agent initialization | ~10 sec | Validates data files |
| Query response | Varies | Depends on LLM and complexity |

## Advanced Usage

### Multi-Container Deployment

```bash
# Run multiple tiers from docker-compose
cd nibr/docker
docker-compose up

# Tier 1 (8GB RAM): Literature agent
# Tier 2 (16GB RAM): Molecular biology (biomni-nibr)
# Dev: With Jupyter notebook
```

### Custom Data Subsets

Edit `nibr/scripts/download-data.sh` to download only specific datasets:
```bash
# Essential files only
DATA_FILES=(
    "DisGeNET.parquet"
    "gene_info.parquet"
    "kg.csv"
    "gtex_tissue_gene_tpm.parquet"
)
```

### Production Deployment

For production use:
1. Use proper API keys (not test keys)
2. Enable security options in docker run
3. Set up proper logging and monitoring
4. Use docker-compose for orchestration
5. Consider Kubernetes for scale

## Support

### Resources
- [Biomni Documentation](https://github.com/snap-stanford/Biomni)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/mac/)
- NIBR-specific questions: Contact your team lead

### Container Logs
```bash
# Full logs
docker logs biomni-nibr

# Follow logs
docker logs -f biomni-nibr

# Last 100 lines
docker logs --tail 100 biomni-nibr
```

## What's New in v2.0.0

### Major Changes
- **Unified Script**: Single `biomni-setup.sh` replaces multiple scripts
- **Flexible Builds**: Command-line control over build mode and R packages
- **Dynamic Dockerfile**: Generated based on selected options
- **Improved Performance**: Default quick build ~15 minutes
- **Better Documentation**: Comprehensive README-NIBR.md

### Migration from v1.0
If you used the old scripts:
1. Delete old containers: `docker rm biomni-tier2 biomni-tier2-final`
2. Use new script: `cd nibr/scripts && ./setup.sh` instead of old scripts
3. Your data in `./data/` is preserved and will be reused

## Summary

This NIBR deployment provides:
- ✅ **Fast setup** (15 minutes default, configurable)
- ✅ **Flexible options** (build modes, R packages, resources)
- ✅ **Local data control** (no cloud dependency)
- ✅ **Resource-efficient** (configurable RAM/CPU)
- ✅ **Cost-effective** (no AWS charges)
- ✅ **Developer-friendly** (Jupyter support built-in)
- ✅ **Production-ready** (Docker containerized)

The `biomni-nibr` container is optimized for NIBR molecular biology workloads with the full 14GB biomedical data lake mounted from your Mac.

## Quick Reference

```bash
# Most common commands (from project root)
cd nibr

# Setup and build
./scripts/setup.sh                    # Default setup
./scripts/setup.sh -j                 # With Jupyter
./scripts/setup.sh -r none -j         # Fastest (no R) + Jupyter

# Container management
./scripts/rebuild-containers.sh --all # Rebuild all containers
./scripts/container-status.sh         # Check container status
./scripts/start-docker-stack.sh       # Start full stack

# Container management
docker exec -it biomni-nibr /bin/bash  # Shell access
docker logs biomni-nibr                # View logs
docker stop biomni-nibr                # Stop
docker start biomni-nibr               # Start
```

---
*Last updated: November 2024*
*Version: 2.0.0-NIBR*
*Contact: NIBR Development Team*