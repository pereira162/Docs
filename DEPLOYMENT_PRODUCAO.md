# Deployment e Produção - Sistema RAG

## 1. Configuração de Produção

### Docker Compose para Produção (docker-compose.prod.yml)
```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_build:/usr/share/nginx/html
    depends_on:
      - api
      - frontend
    restart: unless-stopped

  # Frontend (Production Build)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    volumes:
      - frontend_build:/app/build
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://yourdomain.com/api
    restart: unless-stopped

  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://rag_user:${DB_PASSWORD}@postgres:5432/rag_prod
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - SECRET_KEY=${SECRET_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rag_prod
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./backup:/backup
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__GRPC_PORT: 6334
    volumes:
      - qdrant_prod_data:/qdrant/storage
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G

  # Celery Workers
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://rag_user:${DB_PASSWORD}@postgres:5432/rag_prod
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  # Celery Beat Scheduler
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://rag_user:${DB_PASSWORD}@postgres:5432/rag_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Flower (Celery Monitoring)
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app flower --port=5555 --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  # MinIO (S3 Compatible Storage)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_prod_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G

  # Elasticsearch (para busca híbrida)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elastic_prod_data:/usr/share/elasticsearch/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  # Prometheus (Monitoramento)
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  # Grafana (Dashboard)
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

  # Backup Service
  backup:
    build:
      context: ./scripts
      dockerfile: Dockerfile.backup
    environment:
      - DATABASE_URL=postgresql://rag_user:${DB_PASSWORD}@postgres:5432/rag_prod
      - S3_BUCKET=${BACKUP_S3_BUCKET}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}
    volumes:
      - ./backup:/backup
    restart: unless-stopped

volumes:
  postgres_prod_data:
  redis_prod_data:
  qdrant_prod_data:
  minio_prod_data:
  elastic_prod_data:
  prometheus_data:
  grafana_data:
  frontend_build:
```

### 2. Configuração Nginx (nginx/nginx.conf)
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }

    upstream flower_backend {
        server flower:5555;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
            
            # File upload
            client_max_body_size 100M;
        }

        # File uploads (special handling)
        location /api/v1/links {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            client_max_body_size 100M;
            proxy_request_buffering off;
        }

        # Flower monitoring (restricted access)
        location /flower/ {
            auth_basic "Flower Monitoring";
            auth_basic_user_file /etc/nginx/.htpasswd;
            
            proxy_pass http://flower_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }
    }
}
```

### 3. Dockerfile de Produção

#### Backend (backend/Dockerfile.prod)
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Frontend (frontend/Dockerfile.prod)
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost/ || exit 1

EXPOSE 80
```

### 4. Scripts de Deploy

#### Deploy Script (scripts/deploy.sh)
```bash
#!/bin/bash

set -e

echo "🚀 Iniciando deploy do Sistema RAG..."

# Load environment variables
if [ -f .env.prod ]; then
    export $(grep -v '^#' .env.prod | xargs)
fi

# Build and pull latest images
echo "📦 Building images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Database backup
echo "💾 Creating database backup..."
./scripts/backup.sh

# Start services
echo "🔄 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Health checks
echo "🏥 Running health checks..."
./scripts/health-check.sh

echo "✅ Deploy completed successfully!"
```

#### Health Check Script (scripts/health-check.sh)
```bash
#!/bin/bash

set -e

DOMAIN="${DOMAIN:-localhost}"
MAX_RETRIES=5
RETRY_INTERVAL=10

check_service() {
    local service_name=$1
    local url=$2
    local retries=0

    echo "Checking $service_name..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        
        echo "❌ $service_name not ready, retrying in ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
        retries=$((retries + 1))
    done
    
    echo "💥 $service_name failed health check"
    return 1
}

# Check all services
check_service "API" "http://$DOMAIN/health"
check_service "Frontend" "http://$DOMAIN/"
check_service "Qdrant" "http://$DOMAIN:6333/health"

echo "🎉 All services are healthy!"
```

### 5. Monitoring e Alertas

#### Prometheus Configuration (monitoring/prometheus.yml)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Alert Rules (monitoring/alert_rules.yml)
```yaml
groups:
  - name: rag_system_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"

      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backlog"
          description: "Queue has {{ $value }} pending tasks"

      - alert: DatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database has {{ $value }} active connections"
```

### 6. Backup e Recovery

#### Backup Script (scripts/backup.sh)
```bash
#!/bin/bash

set -e

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql"
QDRANT_BACKUP_DIR="$BACKUP_DIR/qdrant_$DATE"

echo "🗄️ Starting backup process..."

# PostgreSQL backup
echo "📊 Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U rag_user rag_prod > "$DB_BACKUP_FILE"
gzip "$DB_BACKUP_FILE"

# Qdrant backup
echo "🔍 Backing up Qdrant..."
mkdir -p "$QDRANT_BACKUP_DIR"
docker-compose exec qdrant /qdrant/qdrant --snapshot /qdrant/storage/snapshots/
docker cp $(docker-compose ps -q qdrant):/qdrant/storage/snapshots/ "$QDRANT_BACKUP_DIR/"

# Upload to S3 (if configured)
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 sync "$BACKUP_DIR" "s3://$BACKUP_S3_BUCKET/backups/"
fi

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "qdrant_*" -mtime +7 -exec rm -rf {} \;

echo "✅ Backup completed successfully!"
```

### 7. Environment Variables (.env.prod)
```bash
# Database
DB_PASSWORD=your_super_secure_db_password
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_very_long_secret_key_here
SENTRY_DSN=https://your-sentry-dsn

# Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=secure_flower_password
GRAFANA_PASSWORD=secure_grafana_password

# Storage
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key

# Backup
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Domain
DOMAIN=yourdomain.com
```

Esta configuração de produção fornece um ambiente robusto, escalável e monitorado para o sistema RAG em produção.
