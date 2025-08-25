# Network Setup

## Overview

The NIBR Biomni stack uses Docker's bridge networking with a custom network configuration to enable secure inter-service communication while exposing necessary ports to the host.

## Network Architecture

```mermaid
graph TB
    subgraph "Host Network"
        HOST[Host Machine<br/>localhost]
        PORT3000[Port 3000]
        PORT8888[Port 8888]
        PORT54367[Port 54367]
        PORT5432[Port 5432]
        PORT6379[Port 6379]
        PORT80[Port 80/443]
    end
    
    subgraph "Docker Network: nibr-network (172.28.0.0/16)"
        subgraph "Service IPs"
            BIOMNI_IP[biomni-agent<br/>172.28.0.x]
            BACKEND_IP[canvas-backend<br/>172.28.0.x]
            FRONTEND_IP[canvas-frontend<br/>172.28.0.x]
            JUPYTER_IP[biomni-jupyter<br/>172.28.0.x]
            POSTGRES_IP[postgres<br/>172.28.0.x]
            REDIS_IP[redis<br/>172.28.0.x]
            NGINX_IP[nginx<br/>172.28.0.x]
        end
    end
    
    HOST --> PORT3000
    HOST --> PORT8888
    HOST --> PORT54367
    HOST --> PORT5432
    HOST --> PORT6379
    HOST --> PORT80
    
    PORT3000 --> FRONTEND_IP
    PORT8888 --> JUPYTER_IP
    PORT54367 --> BACKEND_IP
    PORT5432 --> POSTGRES_IP
    PORT6379 --> REDIS_IP
    PORT80 --> NGINX_IP
    
    FRONTEND_IP <--> BACKEND_IP
    BACKEND_IP <--> BIOMNI_IP
    BACKEND_IP <--> POSTGRES_IP
    BACKEND_IP <--> REDIS_IP
    NGINX_IP --> FRONTEND_IP
    NGINX_IP --> BACKEND_IP
```

## Network Configuration

### Docker Compose Network Definition

```yaml
networks:
  nibr-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Network Properties
- **Name**: `nibr-network`
- **Driver**: Bridge (default Docker network driver)
- **Subnet**: `172.28.0.0/16` (65,534 usable IP addresses)
- **Gateway**: `172.28.0.1` (automatically assigned)
- **DNS**: Docker's embedded DNS server

## Service Communication

### Internal Communication

Services communicate using Docker's internal DNS resolution:

| Service | Internal Hostname | Internal Port | Protocol |
|---------|------------------|---------------|----------|
| biomni-agent | biomni-agent | 8000 | HTTP |
| canvas-backend | canvas-backend | 54367 | HTTP |
| canvas-frontend | canvas-frontend | 3000 | HTTP |
| biomni-jupyter | biomni-jupyter | 8888 | HTTP |
| postgres | postgres | 5432 | PostgreSQL |
| redis | redis | 6379 | Redis |
| nginx | nginx | 80/443 | HTTP/HTTPS |

### Example Internal URLs
```bash
# Backend connecting to Biomni agent
http://biomni-agent:8000/api/v1/agent

# Backend connecting to PostgreSQL
postgresql://biomni:password@postgres:5432/biomni_canvas

# Backend connecting to Redis
redis://redis:6379/0

# Nginx proxying to backend
http://canvas-backend:54367
```

### External Access

Port mappings for host access:

| Service | Host Port | Container Port | Purpose |
|---------|-----------|---------------|---------|
| canvas-frontend | 3000 | 3000 | Web UI |
| canvas-backend | 54367 | 54367 | API endpoint |
| biomni-jupyter | 8888 | 8888 | Jupyter Lab |
| postgres | 5432 | 5432 | Database access |
| redis | 6379 | 6379 | Cache access |
| nginx | 80, 443 | 80, 443 | Production proxy |

## Service Discovery

### DNS Resolution

Docker provides automatic DNS resolution for service names:

```python
# Python example - Backend connecting to Biomni
import requests

# Using service name (recommended)
response = requests.get("http://biomni-agent:8000/health")

# NOT recommended - using IP directly
# response = requests.get("http://172.28.0.5:8000/health")
```

### Environment Variables

Services can discover each other through environment variables:

```yaml
canvas-backend:
  environment:
    - BIOMNI_AGENT_URL=http://biomni-agent:8000
    - DATABASE_URL=postgresql://biomni:password@postgres:5432/biomni_canvas
    - REDIS_URL=redis://redis:6379
```

## Network Security

### 1. Network Isolation

Services are isolated from external networks by default:
- Only explicitly mapped ports are accessible from host
- Inter-container communication uses internal network
- No direct internet access without explicit configuration

### 2. Service Dependencies

Control startup order with health checks:

```yaml
canvas-frontend:
  depends_on:
    canvas-backend:
      condition: service_healthy
```

### 3. Firewall Rules

Recommended host firewall configuration:

```bash
# Allow Docker subnet
sudo ufw allow from 172.28.0.0/16

# Allow specific service ports
sudo ufw allow 3000/tcp  # Canvas UI
sudo ufw allow 54367/tcp # Backend API
sudo ufw allow 8888/tcp  # Jupyter (dev only)

# Block database ports from external access
sudo ufw deny from any to any port 5432
sudo ufw deny from any to any port 6379
```

## Network Troubleshooting

### Common Issues

#### 1. Service Cannot Connect to Another Service

**Check DNS resolution:**
```bash
docker exec canvas-backend nslookup biomni-agent
```

**Check network connectivity:**
```bash
docker exec canvas-backend ping biomni-agent
```

**Verify service is on the same network:**
```bash
docker inspect canvas-backend | grep NetworkMode
docker network inspect nibr-network
```

#### 2. Port Already in Use

**Find process using port:**
```bash
# macOS
lsof -i :3000

# Linux
netstat -tulpn | grep 3000
```

**Solutions:**
- Stop conflicting service
- Change port mapping in docker-compose.yml
- Use different host port:
  ```yaml
  ports:
    - "3001:3000"  # Map to different host port
  ```

#### 3. Cannot Access Service from Host

**Verify port mapping:**
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

**Check service is listening:**
```bash
docker exec canvas-backend netstat -tlnp
```

**Test connectivity:**
```bash
curl http://localhost:54367/health
```

### Network Diagnostics

#### 1. Inspect Network
```bash
# Show network details
docker network inspect nibr-network

# List connected containers
docker network inspect nibr-network | jq '.[0].Containers'
```

#### 2. Container Network Info
```bash
# Show container's network settings
docker inspect canvas-backend --format='{{json .NetworkSettings}}' | jq

# Show container's IP address
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' canvas-backend
```

#### 3. Network Traffic Analysis
```bash
# Monitor network traffic (requires tcpdump in container)
docker exec canvas-backend tcpdump -i eth0 -n

# Show network statistics
docker exec canvas-backend netstat -s
```

## Advanced Configuration

### Custom DNS
Add custom DNS servers to containers:

```yaml
canvas-backend:
  dns:
    - 8.8.8.8
    - 8.8.4.4
```

### Extra Hosts
Add entries to container's /etc/hosts:

```yaml
canvas-backend:
  extra_hosts:
    - "api.example.com:192.168.1.100"
```

### Network Aliases
Create additional network aliases:

```yaml
canvas-backend:
  networks:
    nibr-network:
      aliases:
        - api
        - backend-api
```

### Multiple Networks
Connect service to multiple networks:

```yaml
services:
  canvas-backend:
    networks:
      - nibr-network
      - monitoring-network
```

## Performance Optimization

### 1. MTU Configuration
Optimize for cloud environments:

```yaml
networks:
  nibr-network:
    driver_opts:
      com.docker.network.driver.mtu: 1450
```

### 2. Connection Pooling
Configure connection pools for databases:

```python
# Backend database configuration
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 40
DATABASE_POOL_PRE_PING = True
```

### 3. Keep-Alive Settings
Enable TCP keep-alive for long-lived connections:

```yaml
canvas-backend:
  sysctls:
    - net.ipv4.tcp_keepalive_time=600
    - net.ipv4.tcp_keepalive_intvl=60
    - net.ipv4.tcp_keepalive_probes=3
```

## Monitoring

### Network Metrics
Monitor network performance:

```bash
# Show network stats for all containers
docker stats --format "table {{.Container}}\t{{.NetIO}}"

# Detailed network inspection
docker exec canvas-backend ip -s link show
```

### Connection Tracking
Track active connections:

```bash
# Show established connections
docker exec canvas-backend ss -tunp

# Count connections by state
docker exec canvas-backend netstat -ant | awk '{print $6}' | sort | uniq -c
```