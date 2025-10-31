# Deployment Guide - SynthAIx

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Security](#security)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Docker** 20.10+ and Docker Compose 2.0+
- **OpenAI API Key** (from https://platform.openai.com)
- **Minimum Resources:**
  - 2 CPU cores
  - 4GB RAM
  - 10GB disk space

### Recommended for Production

- **4+ CPU cores**
- **8GB+ RAM**
- **50GB+ SSD storage**
- **Load balancer** (nginx, HAProxy, or cloud LB)
- **Monitoring** (Prometheus, Grafana)
- **Log aggregation** (ELK, Loki)

---

## Local Development

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd synthaix

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# Access frontend
open http://localhost:8501

# View API docs
open http://localhost:8000/docs
```

### 4. Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - synthaix-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DEBUG=False
      - LOG_LEVEL=INFO
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MAX_WORKERS=40
    volumes:
      - chroma_data:/app/data/chroma_db
    depends_on:
      - redis
    networks:
      - synthaix-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - synthaix-network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    networks:
      - synthaix-network

networks:
  synthaix-network:
    driver: bridge

volumes:
  redis_data:
  chroma_data:
```

### Build and Deploy

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

---

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Push images to ECR:**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push backend
docker tag synthaix-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-backend:latest

# Tag and push frontend
docker tag synthaix-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-frontend:latest
```

2. **Create ECS Task Definition:**

```json
{
  "family": "synthaix",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-backend:latest",
      "memory": 2048,
      "cpu": 1024,
      "essential": true,
      "environment": [
        {"name": "REDIS_HOST", "value": "redis.xxx.cache.amazonaws.com"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxx:secret:openai-key"
        }
      ],
      "portMappings": [
        {"containerPort": 8000, "protocol": "tcp"}
      ]
    },
    {
      "name": "frontend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/synthaix-frontend:latest",
      "memory": 1024,
      "cpu": 512,
      "essential": true,
      "environment": [
        {"name": "BACKEND_URL", "value": "http://backend:8000"}
      ],
      "portMappings": [
        {"containerPort": 8501, "protocol": "tcp"}
      ]
    }
  ]
}
```

3. **Create ElastiCache Redis:**

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id synthaix-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1
```

4. **Deploy to ECS:**

```bash
aws ecs create-service \
  --cluster synthaix-cluster \
  --service-name synthaix-service \
  --task-definition synthaix \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=xxx,containerName=frontend,containerPort=8501
```

### Google Cloud Platform (GCP)

#### Using Cloud Run

1. **Build and push to GCR:**

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push
docker tag synthaix-backend gcr.io/PROJECT_ID/synthaix-backend
docker push gcr.io/PROJECT_ID/synthaix-backend

docker tag synthaix-frontend gcr.io/PROJECT_ID/synthaix-frontend
docker push gcr.io/PROJECT_ID/synthaix-frontend
```

2. **Deploy to Cloud Run:**

```bash
# Deploy backend
gcloud run deploy synthaix-backend \
  --image gcr.io/PROJECT_ID/synthaix-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars REDIS_HOST=xxx \
  --set-secrets OPENAI_API_KEY=openai-key:latest

# Deploy frontend
gcloud run deploy synthaix-frontend \
  --image gcr.io/PROJECT_ID/synthaix-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL=https://synthaix-backend-xxx.run.app
```

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name synthaix-rg --location eastus

# Create container registry
az acr create --resource-group synthaix-rg --name synthaix --sku Basic

# Push images
az acr build --registry synthaix --image synthaix-backend:latest ./backend
az acr build --registry synthaix --image synthaix-frontend:latest ./frontend

# Deploy container group
az container create \
  --resource-group synthaix-rg \
  --name synthaix \
  --image synthaix.azurecr.io/synthaix-backend:latest \
  --cpu 2 \
  --memory 4 \
  --environment-variables REDIS_HOST=xxx \
  --secure-environment-variables OPENAI_API_KEY=xxx \
  --ports 8000 8501
```

---

## Security

### 1. Environment Variables

**Never commit secrets to git:**

```bash
# Use .env file (gitignored)
echo "OPENAI_API_KEY=sk-xxx" >> .env

# Or use cloud secret managers
# AWS Secrets Manager
# GCP Secret Manager
# Azure Key Vault
```

### 2. HTTPS/SSL

**Generate SSL certificates:**

```bash
# Let's Encrypt (free)
certbot certonly --standalone -d synthaix.yourdomain.com

# Or use cloud-managed certificates
```

**nginx SSL configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name synthaix.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. API Authentication

**Add API key authentication:**

```python
# backend/app/core/security.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 4. Rate Limiting

**Using slowapi:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/data/generate")
@limiter.limit("10/minute")
async def generate_data(request: Request):
    ...
```

---

## Monitoring

### Prometheus Metrics

**Add to backend:**

```python
# requirements.txt
prometheus-client==0.19.0

# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

requests_total = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
active_jobs = Gauge('active_jobs', 'Active generation jobs')
```

**Prometheus config:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'synthaix'
    static_configs:
      - targets: ['backend:8000']
```

### Grafana Dashboard

**Import dashboard from JSON or create custom:**

Key metrics to monitor:
- Request rate
- Response times
- Error rates
- Active jobs
- Queue length
- CPU/Memory usage

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing OPENAI_API_KEY
# 2. Redis connection failed
# 3. Port already in use

# Verify environment
docker-compose exec backend env | grep OPENAI
```

### Frontend can't connect to backend

```bash
# Check network
docker-compose exec frontend ping backend

# Verify BACKEND_URL
docker-compose exec frontend env | grep BACKEND_URL

# Test from frontend container
docker-compose exec frontend curl http://backend:8000/api/v1/health
```

### High memory usage

```bash
# Check resource usage
docker stats

# Reduce MAX_WORKERS
# Decrease chunk_size
# Enable streaming responses

# Restart with limited memory
docker-compose down
docker-compose up -d --scale backend=1
```

### Data generation slow

**Optimization checklist:**
- [ ] Increase MAX_WORKERS
- [ ] Use faster OpenAI model
- [ ] Disable deduplication for testing
- [ ] Increase chunk_size
- [ ] Check OpenAI API rate limits
- [ ] Verify network latency

---

## Backup and Recovery

### Backup ChromaDB

```bash
# Backup vector database
docker cp synthaix-backend:/app/data/chroma_db ./backups/chroma_db_$(date +%Y%m%d)

# Restore
docker cp ./backups/chroma_db_20251031 synthaix-backend:/app/data/chroma_db
```

### Backup Redis

```bash
# Backup Redis data
docker exec synthaix-redis redis-cli BGSAVE
docker cp synthaix-redis:/data/dump.rdb ./backups/redis_$(date +%Y%m%d).rdb
```

---

## Performance Tuning

### Backend Optimization

```bash
# Increase worker processes
uvicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Use gunicorn with uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Database Optimization

```python
# ChromaDB settings
CHROMA_BATCH_SIZE = 1000
CHROMA_N_RESULTS = 5  # Reduce for faster queries

# Redis connection pool
redis_client = redis.Redis(
    connection_pool=redis.ConnectionPool(
        max_connections=50
    )
)
```

---

**For additional help, consult the main README.md or open an issue on GitHub.**
