# Protótipo MVP - Sistema RAG Gratuito

## Setup Rápido - 30 Minutos

Este é um protótipo funcional do sistema RAG usando apenas tecnologias gratuitas.

## 1. Backend FastAPI Mínimo

### requirements.txt
```txt
fastapi==0.104.1
uvicorn==0.24.0
sentence-transformers==2.2.2
qdrant-client==1.7.0
python-multipart==0.0.6
beautifulsoup4==4.12.2
requests==2.31.0
# docling  # Adicionar quando disponível
```

### main.py
```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import requests
from bs4 import BeautifulSoup
import hashlib
import time
from typing import List, Optional
import os

app = FastAPI(title="RAG System MVP", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth simples
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "demo123")
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != SITE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    return credentials.credentials

# Configuração
QDRANT_URL = os.getenv("QDRANT_URL", "https://your-cluster.qdrant.tech")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "documents"

# Clientes globais
embedding_model = None
qdrant_client = None

@app.on_event("startup")
async def startup_event():
    global embedding_model, qdrant_client
    
    # Carregar modelo de embedding
    print("Carregando modelo de embedding...")
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Conectar Qdrant
    print("Conectando ao Qdrant...")
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
    )
    
    # Criar coleção se não existir
    try:
        qdrant_client.get_collection(COLLECTION_NAME)
        print(f"Coleção '{COLLECTION_NAME}' já existe")
    except:
        print(f"Criando coleção '{COLLECTION_NAME}'...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 dimensions
                distance=Distance.COSINE
            )
        )

# Modelos Pydantic
class DocumentAdd(BaseModel):
    url: HttpUrl
    title: Optional[str] = None

class QueryRAG(BaseModel):
    query: str
    max_results: int = 5

class RAGResult(BaseModel):
    content: str
    score: float
    source_url: str
    title: Optional[str] = None

# Funções auxiliares
def extract_text_from_url(url: str) -> tuple[str, str]:
    """Extrair texto de uma URL (HTML, PDF básico)"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        
        if 'html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Remover scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            title = soup.title.string if soup.title else None
        else:
            # Para PDFs e outros, usar o conteúdo como texto
            text = response.text
            title = None
        
        # Limpar texto
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:50000], title  # Limitar a 50k caracteres
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar URL: {str(e)}")

def create_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Criar chunks de texto"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

def generate_id(text: str) -> str:
    """Gerar ID único para um chunk"""
    return hashlib.md5(text.encode()).hexdigest()

# Endpoints
@app.get("/")
async def root():
    return {"message": "RAG System MVP", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/add-document")
async def add_document(doc: DocumentAdd, token: str = Depends(verify_token)):
    """Adicionar documento ao sistema RAG"""
    
    try:
        # Extrair texto
        text, extracted_title = extract_text_from_url(str(doc.url))
        title = doc.title or extracted_title or str(doc.url)
        
        # Criar chunks
        chunks = create_chunks(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto da URL")
        
        # Gerar embeddings
        embeddings = embedding_model.encode(chunks)
        
        # Preparar pontos para Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = generate_id(f"{doc.url}_{i}")
            points.append(PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "content": chunk,
                    "source_url": str(doc.url),
                    "title": title,
                    "chunk_index": i,
                    "timestamp": time.time()
                }
            ))
        
        # Inserir no Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        return {
            "message": "Documento adicionado com sucesso",
            "url": str(doc.url),
            "title": title,
            "chunks_created": len(chunks),
            "processing_time": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/query", response_model=List[RAGResult])
async def query_rag(query: QueryRAG, token: str = Depends(verify_token)):
    """Consultar sistema RAG"""
    
    try:
        # Gerar embedding da query
        query_embedding = embedding_model.encode([query.query])
        
        # Buscar no Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding[0].tolist(),
            limit=query.max_results,
            with_payload=True
        )
        
        # Formatar resultados
        results = []
        for hit in search_results:
            results.append(RAGResult(
                content=hit.payload["content"],
                score=hit.score,
                source_url=hit.payload["source_url"],
                title=hit.payload.get("title")
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na consulta: {str(e)}")

@app.get("/stats")
async def get_stats(token: str = Depends(verify_token)):
    """Estatísticas do sistema"""
    
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        
        return {
            "collection_name": COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "indexed_vectors": collection_info.indexed_vectors_count,
            "status": collection_info.status,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "vector_size": 384
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@app.delete("/clear")
async def clear_collection(token: str = Depends(verify_token)):
    """Limpar todos os documentos (apenas para desenvolvimento)"""
    
    try:
        qdrant_client.delete_collection(COLLECTION_NAME)
        
        # Recriar coleção vazia
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
        return {"message": "Coleção limpa com sucesso"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar coleção: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 2. Frontend React + Vite

### package.json
```json
{
  "name": "rag-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "typescript": "^5.2.2",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}
```

### src/App.tsx
```tsx
import React, { useState } from 'react';
import './App.css';

interface RAGResult {
  content: string;
  score: number;
  source_url: string;
  title?: string;
}

interface DocumentAdd {
  url: string;
  title?: string;
}

const API_BASE = 'http://localhost:8000'; // Alterar para URL do Railway

function App() {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [newDoc, setNewDoc] = useState<DocumentAdd>({ url: '', title: '' });
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<RAGResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const authenticate = () => {
    if (password === 'demo123') { // Usar mesma senha do backend
      setIsAuthenticated(true);
      setMessage('Autenticado com sucesso!');
    } else {
      setMessage('Senha incorreta!');
    }
  };

  const addDocument = async () => {
    if (!newDoc.url) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/add-document`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify(newDoc)
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`Documento adicionado: ${result.chunks_created} chunks criados`);
        setNewDoc({ url: '', title: '' });
      } else {
        setMessage('Erro ao adicionar documento');
      }
    } catch (error) {
      setMessage('Erro de conexão');
    }
    setLoading(false);
  };

  const searchDocuments = async () => {
    if (!query) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify({ query, max_results: 5 })
      });

      if (response.ok) {
        const searchResults = await response.json();
        setResults(searchResults);
        setMessage(`${searchResults.length} resultados encontrados`);
      } else {
        setMessage('Erro na busca');
      }
    } catch (error) {
      setMessage('Erro de conexão');
    }
    setLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md w-96">
          <h1 className="text-2xl font-bold mb-4">RAG System MVP</h1>
          <input
            type="password"
            placeholder="Senha de acesso"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border rounded mb-4"
            onKeyPress={(e) => e.key === 'Enter' && authenticate()}
          />
          <button
            onClick={authenticate}
            className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
          >
            Entrar
          </button>
          {message && <p className="mt-2 text-sm text-red-600">{message}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Sistema RAG - Protótipo</h1>
        
        {message && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {message}
          </div>
        )}

        {/* Adicionar Documento */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">Adicionar Documento</h2>
          <div className="space-y-3">
            <input
              type="url"
              placeholder="URL do documento (PDF, HTML, etc.)"
              value={newDoc.url}
              onChange={(e) => setNewDoc({ ...newDoc, url: e.target.value })}
              className="w-full p-2 border rounded"
            />
            <input
              type="text"
              placeholder="Título (opcional)"
              value={newDoc.title}
              onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
              className="w-full p-2 border rounded"
            />
            <button
              onClick={addDocument}
              disabled={loading || !newDoc.url}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              {loading ? 'Processando...' : 'Adicionar Documento'}
            </button>
          </div>
        </div>

        {/* Busca RAG */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">Consulta RAG</h2>
          <div className="flex space-x-3">
            <input
              type="text"
              placeholder="Digite sua pergunta..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 p-2 border rounded"
              onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
            />
            <button
              onClick={searchDocuments}
              disabled={loading || !query}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? 'Buscando...' : 'Buscar'}
            </button>
          </div>
        </div>

        {/* Resultados */}
        {results.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Resultados</h2>
            <div className="space-y-4">
              {results.map((result, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900">
                      {result.title || 'Documento'}
                    </h3>
                    <span className="text-sm text-gray-500">
                      Score: {result.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-2">{result.content}</p>
                  <a
                    href={result.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm"
                  >
                    Ver fonte →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
```

## 3. Deploy Instructions

### Backend (Railway)
1. Criar conta no Railway.app
2. Connect GitHub repository
3. Add environment variables:
   - `QDRANT_URL`: URL do Qdrant Cloud
   - `QDRANT_API_KEY`: API key do Qdrant
   - `SITE_PASSWORD`: Senha do sistema
4. Deploy automático

### Frontend (Vercel)
1. Criar conta no Vercel
2. Import GitHub repository
3. Alterar `API_BASE` no App.tsx para URL do Railway
4. Deploy automático

### Qdrant Cloud
1. Criar conta em cloud.qdrant.io
2. Criar cluster (free tier)
3. Copiar URL e API key
4. Cluster estará ativo

## 4. Teste Rápido

```bash
# 1. Clone o repositório
git clone <repo-url>
cd rag-system

# 2. Backend local (opcional)
cd backend
pip install -r requirements.txt
export SITE_PASSWORD=demo123
export QDRANT_URL=<your-qdrant-url>
export QDRANT_API_KEY=<your-api-key>
python main.py

# 3. Frontend local (opcional)
cd frontend
npm install
npm run dev
```

## 5. Exemplos de Uso

### Adicionar Documento
```bash
curl -X POST "https://your-app.railway.app/add-document" \
  -H "Authorization: Bearer demo123" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.html", "title": "Example Doc"}'
```

### Consultar RAG
```bash
curl -X POST "https://your-app.railway.app/query" \
  -H "Authorization: Bearer demo123" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?", "max_results": 3}'
```

Este protótipo demonstra todas as funcionalidades principais do sistema RAG com custos zero!
