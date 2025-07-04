# Guia de Implementação - Sistema RAG com Docling

## Fase 1: Setup do Ambiente de Desenvolvimento

### 1.1 Estrutura de Pastas
```
rag-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models/
│   │   ├── api/
│   │   ├── services/
│   │   ├── core/
│   │   └── utils/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

### 1.2 Backend Requirements (Python)
```txt
# FastAPI Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.0
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Vector Database
qdrant-client==1.7.0
weaviate-client==3.25.3

# Document Processing
docling==1.0.0  # Ajustar versão conforme disponibilidade
pypdf2==3.0.1
python-docx==1.1.0
beautifulsoup4==4.12.2
requests==2.31.0

# Embeddings & ML
sentence-transformers==2.2.2
transformers==4.36.0
torch==2.1.1

# Task Queue
celery==5.3.4
redis==5.0.1
flower==2.0.1

# File Storage
minio==7.2.0
boto3==1.34.0

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Monitoring & Logging
structlog==23.2.0
sentry-sdk[fastapi]==1.38.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Development
black==23.11.0
isort==5.12.0
mypy==1.7.1
```

### 1.3 Frontend Dependencies (Next.js)
```json
{
  "name": "rag-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@types/node": "^20.9.0",
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "typescript": "^5.2.2",
    
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    
    "tailwindcss": "^3.3.6",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    
    "react-hook-form": "^7.47.0",
    "@hookform/resolvers": "^3.3.2",
    "zod": "^3.22.4",
    
    "@tanstack/react-query": "^5.8.4",
    "zustand": "^4.4.7",
    
    "lucide-react": "^0.292.0",
    "date-fns": "^2.30.0",
    "recharts": "^2.8.0"
  },
  "devDependencies": {
    "eslint": "^8.54.0",
    "eslint-config-next": "14.0.3",
    "prettier": "^3.1.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

## Fase 2: Implementação do Backend

### 2.1 Configuração Principal (app/main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.models import Base

# Criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Documentation System",
    description="Sistema de documentação RAG com Docling",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 2.2 Configurações (app/core/config.py)
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/ragdb"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "documents"
    
    # MinIO/S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Processing
    MAX_FILE_SIZE_MB: int = 100
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2.3 Modelos de Banco (app/models/__init__.py)
```python
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document_links = relationship("DocumentLink", back_populates="user")
    categories = relationship("Category", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # hex color
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="categories")
    document_links = relationship("DocumentLink", back_populates="category")

class DocumentLink(Base):
    __tablename__ = "document_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    title = Column(String(500))
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="pending")
    file_type = Column(String(50))
    file_size = Column(Integer)
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="document_links")
    category = relationship("Category", back_populates="document_links")
    processed_document = relationship("ProcessedDocument", back_populates="document_link", uselist=False)

class ProcessedDocument(Base):
    __tablename__ = "processed_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_link_id = Column(UUID(as_uuid=True), ForeignKey("document_links.id"))
    original_path = Column(Text)
    processed_path = Column(Text)
    text_content = Column(Text)
    chunk_count = Column(Integer)
    processing_time_ms = Column(Integer)
    docling_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document_link = relationship("DocumentLink", back_populates="processed_document")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("processed_documents.id"))
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    embedding_id = Column(String(255))  # referência no vector DB
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("ProcessedDocument", back_populates="chunks")
```

## Fase 3: Processamento com Docling

### 3.1 Serviço de Processamento (app/services/document_processor.py)
```python
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import requests
from urllib.parse import urlparse
import mimetypes

# Placeholder para Docling - ajustar imports conforme disponibilidade
# from docling import DocumentProcessor as DoclingProcessor

class DocumentProcessor:
    def __init__(self):
        self.supported_types = {
            'application/pdf': 'pdf',
            'text/html': 'html',
            'text/plain': 'txt',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/markdown': 'md'
        }
    
    async def download_document(self, url: str, destination: Path) -> Dict[str, Any]:
        """Download documento da URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Detectar tipo de arquivo
            content_type = response.headers.get('content-type', '').split(';')[0]
            file_extension = self._get_extension_from_url(url) or self._get_extension_from_content_type(content_type)
            
            # Salvar arquivo
            file_path = destination / f"document{file_extension}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return {
                'file_path': str(file_path),
                'content_type': content_type,
                'file_size': len(response.content),
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    async def process_with_docling(self, file_path: str) -> Dict[str, Any]:
        """Processar documento com Docling"""
        try:
            # Placeholder - implementar quando Docling estiver disponível
            # processor = DoclingProcessor()
            # result = await processor.process_async(file_path)
            
            # Por enquanto, implementação básica baseada no tipo de arquivo
            content = await self._basic_text_extraction(file_path)
            
            return {
                'text_content': content,
                'metadata': {
                    'pages': 1,
                    'word_count': len(content.split()),
                    'char_count': len(content)
                },
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    async def _basic_text_extraction(self, file_path: str) -> str:
        """Extração básica de texto baseada no tipo de arquivo"""
        path = Path(file_path)
        
        if path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif path.suffix.lower() == '.html':
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
        # Adicionar mais tipos conforme necessário
        
        return "Conteúdo não pôde ser extraído com o método básico"
    
    def _get_extension_from_url(self, url: str) -> str:
        """Obter extensão do arquivo da URL"""
        parsed = urlparse(url)
        path = Path(parsed.path)
        return path.suffix if path.suffix else None
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Obter extensão baseada no content-type"""
        extension = mimetypes.guess_extension(content_type)
        return extension if extension else '.bin'
    
    def create_chunks(self, text: str, chunk_size: int = 1024, overlap: int = 100) -> List[Dict[str, Any]]:
        """Criar chunks do texto para RAG"""
        words = text.split()
        chunks = []
        
        start = 0
        chunk_index = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = ' '.join(words[start:end])
            
            chunks.append({
                'index': chunk_index,
                'content': chunk_text,
                'token_count': len(chunk_text.split()),
                'start_pos': start,
                'end_pos': end
            })
            
            start = end - overlap
            chunk_index += 1
            
            if end >= len(words):
                break
        
        return chunks
```

## Próximos Passos

1. **Implementar Celery Tasks** para processamento assíncrono
2. **Configurar Vector Database** (Qdrant) para embeddings
3. **Desenvolver Frontend** com Next.js
4. **Integrar Docling** quando disponível
5. **Implementar sistema RAG** completo
6. **Testes e otimizações**

Esta documentação fornece uma base sólida para implementar o sistema completo de documentação RAG com Docling.
