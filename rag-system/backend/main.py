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
from dotenv import load_dotenv

load_dotenv()

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
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "documents"

# Validar configuração
if not QDRANT_URL:
    raise ValueError("QDRANT_URL environment variable is required")

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        
        if 'html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Remover scripts e styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Tentar extrair título
            title = None
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            
            # Extrair texto principal
            text = soup.get_text()
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
    return {
        "message": "RAG System MVP", 
        "status": "running",
        "endpoints": {
            "health": "/health",
            "add_document": "/add-document",
            "query": "/query",
            "stats": "/stats",
            "clear": "/clear"
        }
    }

@app.get("/health")
async def health():
    try:
        # Testar conexão com Qdrant
        collections = qdrant_client.get_collections()
        return {
            "status": "healthy", 
            "timestamp": time.time(),
            "qdrant_connected": True,
            "collections": len(collections.collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "qdrant_connected": False,
            "error": str(e)
        }

@app.post("/add-document")
async def add_document(doc: DocumentAdd, token: str = Depends(verify_token)):
    """Adicionar documento ao sistema RAG"""
    
    try:
        # Extrair texto
        print(f"Processando URL: {doc.url}")
        text, extracted_title = extract_text_from_url(str(doc.url))
        title = doc.title or extracted_title or str(doc.url)
        
        # Criar chunks
        chunks = create_chunks(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto da URL")
        
        print(f"Criados {len(chunks)} chunks")
        
        # Gerar embeddings
        print("Gerando embeddings...")
        embeddings = embedding_model.encode(chunks)
        
        # Preparar pontos para Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = generate_id(f"{doc.url}_{i}_{time.time()}")
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
        print("Inserindo no Qdrant...")
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
        print(f"Erro ao processar documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/query", response_model=List[RAGResult])
async def query_rag(query: QueryRAG, token: str = Depends(verify_token)):
    """Consultar sistema RAG"""
    
    try:
        print(f"Processando query: {query.query}")
        
        # Gerar embedding da query
        query_embedding = embedding_model.encode([query.query])
        
        # Buscar no Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding[0].tolist(),
            limit=query.max_results,
            with_payload=True,
            score_threshold=0.3  # Filtrar resultados muito ruins
        )
        
        print(f"Encontrados {len(search_results)} resultados")
        
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
        print(f"Erro na consulta: {str(e)}")
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
            "vector_size": 384,
            "config": {
                "chunk_size": 500,
                "overlap": 50,
                "max_text_length": 50000
            }
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
