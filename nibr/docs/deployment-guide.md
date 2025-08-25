# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the NIBR Biomni stack in different environments.

## Prerequisites

### System Requirements

**Minimum Hardware:**
- CPU: 4 cores
- RAM: 16GB
- Storage: 50GB free space
- Network: Stable internet connection

**Recommended Hardware:**
- CPU: 8+ cores
- RAM: 32GB
- Storage: 100GB SSD
- Network: High-speed internet

### Software Requirements

1. **Docker**: Version 20.10+
   ```bash
   docker --version
   ```

2. **Docker Compose**: Version 2.0+
   ```bash
   docker-compose --version
   ```

3. **Git**: For cloning repository
   ```bash
   git --version
   ```

4. **Make** (optional): For using Makefile commands
   ```bash
   make --version
   ```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/biomni.git
cd biomni/nibr
```

### 2. Set Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

Required environment variables:
```bash
# API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional API Keys
AZURE_OPENAI_API_KEY=...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Data Path (optional, defaults to ../data)
BIOMNI_LOCAL_DATA_PATH=/path/to/data

# Jupyter Token (optional, defaults to 'biomni')
# Access Jupyter at: http://localhost:8888?token=biomni
JUPYTER_TOKEN=biomni
```

### 3. Download Data Lake (First Time Only)
```bash
# The data lake will be downloaded automatically on first run
# Alternatively, pre-download manually:
cd ..
python scripts/download_data.py
cd nibr
```

### 4. Build and Start Services
```bash
# Build all containers
./scripts/rebuild-containers.sh --all

# Start services
docker-compose -f docker-compose.full-stack.yml up -d

# Or build and start in one command
./scripts/rebuild-containers.sh --all --start
```

### 5. Verify Deployment
```bash
# Check container status
./scripts/container-status.sh

# Check service health
curl http://localhost:54367/health
```

### 6. Access Services
- Canvas UI: http://localhost:3000
- Backend API: http://localhost:54367
- Jupyter Lab: http://localhost:8888?token=biomni (dev profile only)

## Deployment Profiles

### Development Profile

Includes Jupyter Lab and development tools:

```bash
# Start with development profile
docker-compose -f docker-compose.full-stack.yml --profile dev up -d

# Or using rebuild script
./scripts/rebuild-containers.sh --all --dev --start
```

Services included:
- ✅ Biomni Agent
- ✅ Canvas Backend
- ✅ Canvas Frontend
- ✅ Jupyter Lab (http://localhost:8888?token=biomni)
- ❌ PostgreSQL
- ❌ Redis
- ❌ Nginx

### Production Profile

Full stack with database and caching:

```bash
# Start with production profile
docker-compose -f docker-compose.full-stack.yml --profile production up -d

# Or using rebuild script
./scripts/rebuild-containers.sh --all --prod --start
```

Services included:
- ✅ Biomni Agent
- ✅ Canvas Backend
- ✅ Canvas Frontend
- ❌ Jupyter Lab
- ✅ PostgreSQL
- ✅ Redis
- ✅ Nginx

### Custom Deployment

Start specific services:

```bash
# Start only core services
docker-compose -f docker-compose.full-stack.yml up -d biomni-agent canvas-backend canvas-frontend

# Start with specific profiles
docker-compose -f docker-compose.full-stack.yml \
  --profile dev \
  --profile production \
  up -d
```

## Configuration

### 1. API Keys Configuration

Configure multiple LLM providers in `.env`:

```bash
# Primary providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Additional providers
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
GOOGLE_API_KEY=...
GROQ_API_KEY=...
```

### 2. Database Configuration

For production deployment with PostgreSQL:

```bash
# Database settings in .env
POSTGRES_USER=biomni
POSTGRES_PASSWORD=secure-password-here
POSTGRES_DB=biomni_canvas
DATABASE_URL=postgresql://biomni:secure-password-here@postgres:5432/biomni_canvas
```

### 3. Redis Configuration

For production caching:

```bash
# Redis settings in .env
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=optional-password
```

### 4. Nginx Configuration

Custom nginx configuration:

```nginx
# canvas/nginx/default.conf
upstream backend {
    server canvas-backend:54367;
}

upstream frontend {
    server canvas-frontend:3000;
}

server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Operations

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.full-stack.yml up -d

# Start with logs
docker-compose -f docker-compose.full-stack.yml up

# Start specific service
docker-compose -f docker-compose.full-stack.yml up -d canvas-backend
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.full-stack.yml down

# Stop and remove volumes (DATA LOSS!)
docker-compose -f docker-compose.full-stack.yml down -v

# Stop specific service
docker-compose -f docker-compose.full-stack.yml stop canvas-backend
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.full-stack.yml logs -f

# Specific service
docker-compose -f docker-compose.full-stack.yml logs -f canvas-backend

# Last 100 lines
docker-compose -f docker-compose.full-stack.yml logs --tail=100 biomni-agent
```

### Rebuilding Services

```bash
# Rebuild all
./scripts/rebuild-containers.sh --all

# Rebuild specific service
./scripts/rebuild-containers.sh --backend

# Force rebuild (remove images)
./scripts/rebuild-containers.sh --all --force

# Clean rebuild (remove volumes)
./scripts/rebuild-containers.sh --all --clean
```

### Scaling Services

```bash
# Scale biomni agents
docker-compose -f docker-compose.full-stack.yml up -d --scale biomni-agent=3

# Check scaled instances
docker ps --filter name=biomni-agent
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:54367/health

# Frontend status
curl http://localhost:3000

# Database connection
docker exec postgres pg_isready -U biomni

# Redis ping
docker exec redis redis-cli ping
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific services
docker stats biomni-agent canvas-backend canvas-frontend

# One-time snapshot
docker stats --no-stream
```

### Container Status

```bash
# Quick status check
./scripts/container-status.sh

# Docker native
docker-compose -f docker-compose.full-stack.yml ps
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Check logs:**
```bash
docker-compose -f docker-compose.full-stack.yml logs
```

**Common causes:**
- Missing environment variables
- Port conflicts
- Insufficient resources

#### 2. Port Already in Use

**Find conflicting process:**
```bash
lsof -i :3000  # Check specific port
```

**Solutions:**
- Stop conflicting service
- Change port in docker-compose.yml

#### 3. Out of Memory

**Check memory usage:**
```bash
docker system df
docker stats --no-stream
```

**Solutions:**
- Increase Docker memory limit
- Remove unused containers/images:
  ```bash
  docker system prune -a
  ```

#### 4. Slow Performance

**Check resource constraints:**
```bash
docker inspect biomni-agent | grep -A 10 Resources
```

**Solutions:**
- Adjust resource limits in docker-compose.yml
- Enable BuildKit for faster builds:
  ```bash
  export DOCKER_BUILDKIT=1
  ```

### Debug Mode

Enable debug logging:

```bash
# Set in .env
BIOMNI_LOG_LEVEL=DEBUG
LOG_LEVEL=debug

# Restart services
docker-compose -f docker-compose.full-stack.yml restart
```

### Container Shell Access

```bash
# Biomni agent
docker exec -it biomni-agent /bin/bash

# Canvas backend
docker exec -it canvas-backend /bin/bash

# Run Python shell in biomni
docker exec -it biomni-agent python
```

## Backup and Recovery

### Backup Volumes

```bash
# Backup all volumes
docker run --rm \
  -v biomni-cache:/data/cache \
  -v biomni-results:/data/results \
  -v canvas-data:/data/canvas \
  -v postgres-data:/data/postgres \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/biomni-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Volumes

```bash
# Restore from backup
docker run --rm \
  -v biomni-cache:/data/cache \
  -v biomni-results:/data/results \
  -v canvas-data:/data/canvas \
  -v postgres-data:/data/postgres \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/biomni-backup-20240825.tar.gz -C /
```

### Database Backup

```bash
# Backup PostgreSQL
docker exec postgres pg_dump -U biomni biomni_canvas > backup.sql

# Restore PostgreSQL
docker exec -i postgres psql -U biomni biomni_canvas < backup.sql
```

## Security

### Production Checklist

- [ ] Change default passwords
- [ ] Use secrets management for API keys
- [ ] Enable HTTPS with valid certificates
- [ ] Restrict database access
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement rate limiting
- [ ] Enable authentication
- [ ] Regular backups

### Environment Variables Security

Never commit `.env` files:

```bash
# Add to .gitignore
.env
.env.local
.env.*.local
```

Use Docker secrets for production:

```yaml
secrets:
  openai_key:
    external: true
    
services:
  biomni-agent:
    secrets:
      - openai_key
```

## Maintenance

### Regular Tasks

**Daily:**
- Check service health
- Monitor resource usage
- Review error logs

**Weekly:**
- Backup data volumes
- Update containers
- Clean unused resources

**Monthly:**
- Security updates
- Performance review
- Capacity planning

### Upgrade Procedure

```bash
# 1. Backup current state
./backup.sh

# 2. Pull latest code
git pull origin main

# 3. Rebuild containers
./scripts/rebuild-containers.sh --all --force

# 4. Run migrations if needed
docker exec canvas-backend python manage.py migrate

# 5. Restart services
docker-compose -f docker-compose.full-stack.yml restart

# 6. Verify functionality
./scripts/container-status.sh
```