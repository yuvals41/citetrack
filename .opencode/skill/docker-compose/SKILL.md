---
name: docker-compose
description: Docker Compose operations for container orchestration, service deployment, and local development environment management
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Docker Compose Skill

Manage Docker containers and services for local development in the Citetrack platform.

## When to Use

- Starting/stopping local development services
- Rebuilding containers after code changes
- Viewing service logs and debugging
- Checking service health status
- Managing infrastructure dependencies (postgres, redis, rabbitmq)

## Quick Start

```bash
# Always run from deployment directory
cd deployment

# 1. Start infrastructure first (postgres, redis, rabbitmq, milvus)
docker compose -f docker-compose-infra.yaml up -d

# 2. Start application services
docker compose up -d --build <servicename>

# 3. Check everything is running
docker compose ps
```

## Compose Files

| File | Purpose | Key Services |
|------|---------|--------------|
| `docker-compose.yaml` | Main application services | agentflow, visual-content-generator, researcher, application-server, admin-backend, admin-frontend, social-publisher, desktop-frontend |
| `docker-compose-infra.yaml` | Infrastructure dependencies | postgres, redis, rabbitmq, milvus (standalone, etcd, minio) |

## Service Ports Reference

### Application Services

| Service | API Port | Debug Port | Description |
|---------|----------|------------|-------------|
| application-server | 38888 | - | Main API backend |
| application-server (WS) | 8090 | - | WebSocket connections |
| agentflow | 5000 | 6000 | AI orchestration engine |
| researcher | 5001 | 6001 | Semantic search service |
| visual-content-generator | (load balanced) | - | Media generation (5 replicas) |
| admin-backend | 9123 | 6003 | Admin portal API |
| admin-frontend | 8080 | - | Admin portal UI |
| desktop-frontend | 8100 | - | Mobile/web frontend |
| social-publisher | 50317 | - | Social media integration |

### Infrastructure Services

| Service | Port | UI Port | Description |
|---------|------|---------|-------------|
| postgres | 5432 | - | Primary database |
| redis | 6379 | - | Caching and sessions |
| rabbitmq | 5672 | 15672 | Message broker (UI: guest/guest) |
| milvus | 19530 | 9091 | Vector database (metrics) |

## Examples

### Start Infrastructure

```bash
cd deployment

# Start all infrastructure
docker compose -f docker-compose-infra.yaml up -d

# Verify infrastructure is healthy
docker compose -f docker-compose-infra.yaml ps
```

### Start Specific Service with Rebuild

```bash
cd deployment

# Single service
docker compose up -d --build agentflow

# Multiple services
docker compose up -d --build agentflow researcher visual-content-generator

# Rebuild without cache (when dependencies change)
docker compose build --no-cache agentflow && docker compose up -d agentflow
```

### View Logs

```bash
cd deployment

# Follow logs for a service
docker compose logs -f agentflow

# Last 50 lines
docker compose logs --tail 50 application-server

# Multiple services
docker compose logs -f agentflow researcher

# Filter with grep (e.g., errors only)
docker compose logs -f agentflow | grep -i error
```

### Health Check

```bash
# Check all service statuses
docker compose ps

# Individual health endpoints
curl http://localhost:38888/api/health  # Application Server
curl http://localhost:5000/health       # AgentFlow
curl http://localhost:5001/health       # Researcher
curl http://localhost:9123/api/health   # Admin Backend

# Container resource usage
docker stats
```

### Stop Services

```bash
cd deployment

# Stop specific service
docker compose stop agentflow

# Stop and remove containers
docker compose down

# Stop and remove with volumes (DESTRUCTIVE - removes data)
docker compose down -v
```

## Common Issues & Solutions

### Service Won't Start

```bash
# Check logs for errors
docker compose logs <servicename> --tail 100

# Verify dependencies are running
docker compose -f docker-compose-infra.yaml ps

# Check for port conflicts
lsof -i :<port>
```

### Database Connection Errors

```bash
# Ensure postgres is running
docker compose -f docker-compose-infra.yaml up -d postgres

# Check postgres logs
docker compose -f docker-compose-infra.yaml logs postgres

# Run migrations if needed
cd apps/api && npx prisma migrate deploy
```

### RabbitMQ Connection Issues

```bash
# Ensure RabbitMQ is running
docker compose -f docker-compose-infra.yaml up -d rabbitmq

# Access UI at http://localhost:15672 (guest/guest)
# Check queues and connections
```

### Memory Issues

```bash
# Check resource usage
docker stats

# Clean up unused resources
docker system prune -a

# Check disk usage
docker system df
```

## Guidelines

1. **Always start from `deployment/` directory** - compose files expect this context
2. **Start infrastructure first** - services depend on postgres, redis, rabbitmq
3. **Use `--build` flag** - ensures code changes are reflected in containers
4. **Check health endpoints** - `/health` on each service confirms it's ready
5. **Use `--no-cache` sparingly** - only when dependencies change, takes longer
6. **Never use `-v` flag casually** - `docker compose down -v` deletes volumes/data

## Commands

```bash
# Core commands
docker compose up -d --build <service>     # Start with rebuild
docker compose down                         # Stop all services
docker compose ps                           # List running services
docker compose logs -f <service>           # Follow logs
docker compose restart <service>           # Restart service
docker compose exec <service> bash         # Shell into container

# Infrastructure
docker compose -f docker-compose-infra.yaml up -d      # Start infra
docker compose -f docker-compose-infra.yaml down       # Stop infra
docker compose -f docker-compose-infra.yaml ps         # Infra status

# Debugging
docker compose logs <service> --tail 50    # Recent logs
docker stats                                # Resource usage
docker compose exec <service> env          # Check environment
```

## Reference Files

- `deployment/docker-compose.yaml` - Main services configuration
- `deployment/docker-compose-infra.yaml` - Infrastructure configuration
- `deployment/proxy/` - Nginx reverse proxy configs
- `deployment/dns/` - Local DNS setup for *.solaraai.local
- `docs/50_Standards/LOCAL_DEV_INFO.md` - Local dev credentials
