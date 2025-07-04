# Especificações Técnicas Detalhadas

## 1. Estrutura do Banco de Dados

### PostgreSQL Schema

```sql
-- Usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categorias de documentos
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7), -- hex color
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Links de documentos
CREATE TABLE document_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    title VARCHAR(500),
    description TEXT,
    category_id UUID REFERENCES categories(id),
    user_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    file_type VARCHAR(50),
    file_size BIGINT,
    processed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentos processados
CREATE TABLE processed_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_link_id UUID REFERENCES document_links(id),
    original_path TEXT,
    processed_path TEXT,
    text_content TEXT,
    chunk_count INTEGER,
    processing_time_ms INTEGER,
    docling_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunks de texto para RAG
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES processed_documents(id),
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding_id VARCHAR(255), -- referência no vector DB
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs de processamento
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_link_id UUID REFERENCES document_links(id),
    step VARCHAR(100),
    status VARCHAR(50),
    message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. API Endpoints

### Autenticação
```
POST /auth/login
POST /auth/register
POST /auth/refresh
POST /auth/logout
```

### Gerenciamento de Links
```
GET    /api/v1/links              # Listar links
POST   /api/v1/links              # Adicionar novo link
GET    /api/v1/links/{id}         # Detalhes do link
PUT    /api/v1/links/{id}         # Atualizar link
DELETE /api/v1/links/{id}         # Remover link
POST   /api/v1/links/{id}/process # Processar manualmente
```

### Categorias
```
GET    /api/v1/categories         # Listar categorias
POST   /api/v1/categories         # Criar categoria
PUT    /api/v1/categories/{id}    # Atualizar categoria
DELETE /api/v1/categories/{id}    # Remover categoria
```

### Documentos
```
GET    /api/v1/documents          # Listar documentos processados
GET    /api/v1/documents/{id}     # Detalhes do documento
GET    /api/v1/documents/{id}/content # Conteúdo processado
GET    /api/v1/documents/{id}/chunks  # Chunks do documento
```

### RAG Query
```
POST   /api/v1/rag/query          # Consulta RAG
POST   /api/v1/rag/search         # Busca semântica
GET    /api/v1/rag/similar/{id}   # Documentos similares
```

### Monitoramento
```
GET    /api/v1/stats              # Estatísticas gerais
GET    /api/v1/health             # Health check
GET    /api/v1/logs               # Logs de sistema
```

## 3. Modelos Pydantic

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentLinkCreate(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None

class DocumentLink(BaseModel):
    id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    status: ProcessingStatus
    file_type: Optional[str]
    file_size: Optional[int]
    processed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

class RAGQuery(BaseModel):
    query: str
    max_results: int = 10
    threshold: float = 0.7
    category_filter: Optional[List[str]] = None

class RAGResponse(BaseModel):
    query: str
    results: List[dict]
    total_results: int
    processing_time: float
```

## 4. Configuração Docker

### docker-compose.yml
```yaml
version: '3.8'

services:
  # Backend API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
      - REDIS_URL=redis://redis:6379/0
      - VECTOR_DB_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - qdrant

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ragdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Qdrant Vector DB
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # Celery Worker
  worker:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  # Celery Flower (Monitoring)
  flower:
    build: ./backend
    command: celery -A app.celery flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # MinIO (S3 Compatible)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

## 5. Fluxo de Processamento

### Pipeline de Documentos
1. **Upload/Link**: Usuário adiciona URL
2. **Validação**: Verificar se URL é acessível
3. **Download**: Baixar arquivo para storage
4. **Processamento**: Usar Docling para extrair conteúdo
5. **Chunking**: Dividir texto em chunks otimizados
6. **Embedding**: Gerar embeddings dos chunks
7. **Indexação**: Armazenar no vector database
8. **Finalização**: Atualizar status e notificar usuário

### Código de Exemplo (Celery Task)
```python
from celery import Celery
import requests
from docling import DocumentProcessor

@celery.task
def process_document(document_link_id: str):
    # 1. Buscar link no banco
    link = get_document_link(document_link_id)
    
    # 2. Download do arquivo
    response = requests.get(link.url)
    file_path = save_to_storage(response.content, link.id)
    
    # 3. Processar com Docling
    processor = DocumentProcessor()
    result = processor.process(file_path)
    
    # 4. Criar chunks
    chunks = create_chunks(result.text, chunk_size=1024)
    
    # 5. Gerar embeddings
    embeddings = generate_embeddings(chunks)
    
    # 6. Armazenar no vector DB
    store_in_vector_db(chunks, embeddings, document_link_id)
    
    # 7. Atualizar status
    update_document_status(document_link_id, "completed")
```

## 6. Sistema RAG

### Configuração de Busca
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGSystem:
    def __init__(self):
        self.vector_client = QdrantClient("http://qdrant:6333")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def query(self, query: str, top_k: int = 10):
        # Gerar embedding da query
        query_embedding = self.embedder.encode([query])
        
        # Buscar no vector DB
        results = self.vector_client.search(
            collection_name="documents",
            query_vector=query_embedding[0],
            limit=top_k
        )
        
        # Recuperar contexto dos chunks
        context = self.build_context(results)
        
        return {
            "query": query,
            "context": context,
            "sources": [r.payload for r in results]
        }
```

Esta documentação fornece a base técnica completa para implementar o sistema. Agora vou usar o MCP Context7 para buscar as documentações mais atuais das tecnologias.
