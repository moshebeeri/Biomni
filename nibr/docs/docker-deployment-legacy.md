# NIBR Biomni + Canvas Docker Deployment Guide

## 🐳 Overview

This guide provides instructions for deploying the complete NIBR Biomni stack with Canvas UI using Docker containers.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended for production)
- 50GB free disk space
- Biomni data lake downloaded or mounted

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/moshebeeri/Biomni.git
cd Biomni/nibr

# Copy environment templates
cp ../.env.example ../.env
cp canvas/.env.docker canvas/.env

# Edit environment files with your API keys
nano ../.env
nano canvas/.env
```

### 2. Launch Stack

```bash
# Make startup script executable
chmod +x start-docker-stack.sh

# Launch interactive menu
./start-docker-stack.sh

# Or launch directly
./start-docker-stack.sh start       # Default stack
./start-docker-stack.sh start dev    # With Jupyter
./start-docker-stack.sh start production  # Full production
```

### 3. Access Services

- **Canvas UI**: http://localhost:3000
- **Backend API**: http://localhost:54367
- **Jupyter Lab**: http://localhost:8888 (dev profile)
- **PostgreSQL**: localhost:5432 (production profile)
- **Redis**: localhost:6379 (production profile)

## 🏗️ Architecture

### Container Services

```yaml
biomni-agent:       # Core Biomni agent with A1 and tools
canvas-backend:     # FastAPI backend for Canvas
canvas-frontend:    # Next.js UI for Canvas
biomni-jupyter:     # Jupyter development environment
postgres:           # PostgreSQL database (production)
redis:              # Redis cache (production)
nginx:              # Reverse proxy (production)
```

### Network Architecture

```
┌─────────────────────────────────────────┐
│           nginx (port 80/443)           │
└──────────┬────────────┬─────────────────┘
           │            │
    ┌──────▼──────┐ ┌──▼──────────┐
    │   Canvas    │ │   Canvas    │
    │  Frontend   │ │   Backend   │
    │  (port 3000)│ │ (port 54367)│
    └─────────────┘ └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Biomni    │
                    │    Agent    │
                    └─────────────┘
```

## 📁 Directory Structure

```
biomni/
├── data/
│   └── data_lake/                 # Biomni data (11GB)
└── nibr/                          # All NIBR customizations
    ├── docker-compose.full-stack.yml   # Main orchestration file
    ├── start-docker-stack.sh           # Launcher script
    ├── DOCKER_DEPLOYMENT.md            # This guide
    ├── docker/
    │   ├── Dockerfile.nibr        # Biomni container
    │   └── docker-compose.yml     # Biomni-only compose
    └── canvas/
        ├── Dockerfile.frontend    # Canvas UI container
        ├── Dockerfile.backend     # Canvas API container
        ├── docker-compose.canvas.yml  # Canvas-only compose
        └── nginx/
            └── default.conf       # Nginx configuration
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# API Keys (Required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Data Path
BIOMNI_LOCAL_DATA_PATH=./data

# Features
USE_PERSISTENT_AGENTS=true
ENABLE_JUPYTER=true
ENABLE_MCP=false

# Authentication
AUTH_ENABLED=false  # Set true for production
```

### Resource Limits

Default resource allocations (adjustable in docker-compose.full-stack.yml):

| Service | CPU | Memory | Purpose |
|---------|-----|--------|---------|
| biomni-agent | 4 cores | 8GB | Core Biomni processing |
| canvas-backend | 2 cores | 4GB | API and agent management |
| canvas-frontend | 2 cores | 2GB | UI serving |
| postgres | 1 core | 1GB | Database (production) |
| redis | 0.5 cores | 512MB | Caching (production) |

## 🛠️ Development Workflow

### Building Images

```bash
# Build all images (from nibr directory)
./start-docker-stack.sh build

# Or build individually (from nibr directory)
docker build -f docker/Dockerfile.nibr -t nibr/biomni:latest ..
docker build -f canvas/Dockerfile.backend -t nibr/canvas-backend:latest canvas/
docker build -f canvas/Dockerfile.frontend -t nibr/canvas-frontend:latest canvas/
```

### Viewing Logs

```bash
# All services
./start-docker-stack.sh logs

# Specific service
./start-docker-stack.sh logs canvas-backend

# Follow logs
docker-compose -f docker-compose.full-stack.yml logs -f
```

### Debugging

```bash
# Check service status
docker-compose -f docker-compose.full-stack.yml ps

# Execute commands in container
docker exec -it canvas-backend bash
docker exec -it biomni-agent python

# Inspect network
docker network ls
docker network inspect biomni_nibr-network
```

## 🚦 Health Checks

All services include health checks:

```bash
# Check health status
docker-compose -f docker-compose.full-stack.yml ps

# Manual health checks
curl http://localhost:54367/health     # Backend
curl http://localhost:3000/api/health  # Frontend
```

## 🔒 Production Deployment

### 1. Enable Production Profile

```bash
# Start with production services
./start-docker-stack.sh start production
```

### 2. Configure SSL (nginx)

Update `nibr/canvas/nginx/default.conf` for SSL:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of configuration
}
```

### 3. Enable Authentication

Set in `.env`:
```bash
AUTH_ENABLED=true
AD_DOMAIN=nibr.local
AD_SERVER=ldap://ad.nibr.local
```

### 4. Database Migration

```bash
# Initialize PostgreSQL
docker exec -it postgres psql -U biomni -d biomni_canvas
# Run migrations from backend/migrations/
```

## 🐛 Troubleshooting

### Common Issues

**Issue: Canvas frontend can't connect to backend**
```bash
# Check network connectivity
docker exec canvas-frontend ping canvas-backend
# Verify environment variable
docker exec canvas-frontend env | grep API_URL
```

**Issue: Biomni agent not accessible**
```bash
# Check agent logs
docker logs biomni-agent
# Verify data mount
docker exec biomni-agent ls /biomni_data/data_lake
```

**Issue: Out of memory**
```bash
# Adjust memory limits in docker-compose.full-stack.yml
# Or use swap
sudo sysctl vm.swappiness=60
```

### Clean Slate

```bash
# Stop and remove everything
./start-docker-stack.sh clean

# Manual cleanup
docker-compose -f docker-compose.full-stack.yml down -v
docker system prune -a
```

## 📊 Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Container resource usage
docker-compose -f docker-compose.full-stack.yml top
```

### Logs Aggregation

For production, consider:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Prometheus + Grafana
- CloudWatch (AWS)

## 🔄 Updates

### Updating Images

```bash
# Pull latest changes
git pull origin main

# Rebuild images
./start-docker-stack.sh build

# Restart services
./start-docker-stack.sh stop
./start-docker-stack.sh start
```

### Rolling Updates

```bash
# Update single service without downtime
docker-compose -f docker-compose.full-stack.yml up -d --no-deps canvas-backend
```

## 📝 Notes

- Data persistence: All data stored in named volumes
- Networking: Services communicate via internal Docker network
- Security: Run behind firewall in production
- Scaling: Use Docker Swarm or Kubernetes for multi-node

## 🆘 Support

For issues or questions:
- Check logs: `./start-docker-stack.sh logs`
- Review health checks: `docker-compose ps`
- Consult documentation: `docs/`
- Contact: NIBR Development Team

---

**Last Updated:** August 25, 2025  
**Version:** 1.0.0