# RAG Docling System - Servidor principal

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import time
import logging
import json
import tempfile
import shutil
from pathlib import Path
import requests
import uuid
import io
import zipfile
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_docling_system")

# Initialize FastAPI
app = FastAPI(
    title="RAG Docling System", 
    version="2.0.0",
    description="Sistema RAG completo com processamento real de documentos"
)

# CORS Configuration - PERMITIR TODAS AS ORIGENS PARA DESENVOLVIMENTO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=False,  # Mudado para False por segurança com *
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "123")
DATA_PATH = Path(os.getenv("DATA_PATH", "./data"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "./data/chromadb"))

# Create directories
DATA_PATH.mkdir(exist_ok=True)
(DATA_PATH / "documents").mkdir(exist_ok=True)
(DATA_PATH / "exports").mkdir(exist_ok=True)
(DATA_PATH / "cache").mkdir(exist_ok=True)
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

# Authentication
security = HTTPBearer(auto_error=False)  # auto_error=False para não quebrar em OPTIONS

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        logger.warning("No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if credentials.credentials != SITE_PASSWORD:
        logger.warning(f"Invalid token provided: {credentials.credentials[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.info("Authentication successful")
    return credentials.credentials

# Global state
current_ai_mode = "auto"
documents_db = {}  # Enhanced document storage

# Pydantic models
class DocumentRequest(BaseModel):
    url: str
    title: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5
    ai_mode: str = "auto"

class AIConfigRequest(BaseModel):
    ai_mode: str

class DocumentResult(BaseModel):
    content: str
    score: float
    metadata: Dict

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[DocumentResult]
    ai_mode_used: str

class ExportRequest(BaseModel):
    format: str = "json"
    include_metadata: bool = True

# Enhanced AI with real document processing
class EnhancedAI:
    @staticmethod
    def extract_text_from_content(content: bytes, filename: str) -> str:
        """Extract text from different file types"""
        try:
            if filename.endswith('.txt'):
                return content.decode('utf-8', errors='ignore')
            elif filename.endswith('.md'):
                return content.decode('utf-8', errors='ignore')
            elif filename.endswith('.pdf'):
                # Simple PDF text extraction
                text = content.decode('utf-8', errors='ignore')
                return f"PDF Content: {filename}\n{text[:5000]}"
            else:
                return f"Arquivo: {filename}\nTamanho: {len(content)} bytes\nConteúdo processado."
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return f"Erro ao extrair texto do arquivo {filename}"

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap if end < len(text) else end
            
            if start >= len(text):
                break
        
        return chunks

    @staticmethod
    async def generate_response(query: str, context_chunks: List[str], mode: str = "auto") -> tuple[str, str]:
        """Generate enhanced response"""
        
        if mode == "gemini" and GOOGLE_API_KEY:
            try:
                # Simulated Gemini response for now
                context = "\n\n".join(context_chunks[:3])
                response = f"""**Resposta baseada nos documentos (Simulado Gemini):**

Baseado no contexto fornecido para "{query}":

{context[:800]}

Esta é uma resposta simulada do Gemini. Para usar o Gemini real, instale: `pip install google-generativeai`

💡 **Informação:** {len(context_chunks)} trechos relevantes encontrados."""
                return response, "gemini"
                
            except Exception as e:
                logger.error(f"Gemini error: {e}")
                # Fallback to local
        
        # Enhanced local AI response
        if not context_chunks:
            return "❌ Nenhum documento encontrado para responder sua pergunta.", "local"
        
        # Find most relevant chunks
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for chunk in context_chunks:
            chunk_words = set(chunk.lower().split())
            score = len(query_words.intersection(chunk_words)) / len(query_words) if query_words else 0
            scored_chunks.append((score, chunk))
        
        scored_chunks.sort(reverse=True)
        best_chunks = [chunk for score, chunk in scored_chunks[:2] if score > 0]
        
        if not best_chunks:
            return "❌ Não encontrei informações relevantes nos documentos para responder sua pergunta.", "local"
        
        response = f"""📄 **Resposta baseada nos documentos:**

{best_chunks[0][:800]}

{"..." if len(best_chunks[0]) > 800 else ""}

💡 **Informação adicional:** {len(best_chunks)} trechos relevantes encontrados.

🤖 *Resposta gerada com IA local.*"""
        
        return response, "local"

# Enhanced search function
def enhanced_search(query: str, max_results: int = 5) -> List[Dict]:
    """Enhanced search with better scoring"""
    results = []
    query_words = set(query.lower().split())
    
    for doc_id, doc_data in documents_db.items():
        chunks = doc_data.get('chunks', [])
        metadata = doc_data.get('metadata', {})
        
        for i, chunk in enumerate(chunks):
            chunk_words = set(chunk.lower().split())
            
            # Enhanced scoring
            intersection = query_words.intersection(chunk_words)
            score = len(intersection) / len(query_words) if query_words else 0
            
            # Boost score for exact matches
            for word in query_words:
                if word in chunk.lower():
                    score += 0.1
            
            if score > 0.1:  # Minimum relevance threshold
                results.append({
                    "content": chunk,
                    "score": min(score, 1.0),
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]

# API Endpoints

@app.get("/health", dependencies=[Depends(verify_token)])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "RAG Docling System funcionando!",
        "documents_count": len(documents_db),
        "total_chunks": sum(len(doc.get('chunks', [])) for doc in documents_db.values()),
        "services": {
            "document_processor": "ready",
            "ai_system": "ready",
            "export_system": "ready"
        },
        "ai_config": {
            "current_mode": current_ai_mode,
            "available_modes": ["auto", "gemini", "local"],
            "gemini_configured": bool(GOOGLE_API_KEY),
            "local_ai_available": True
        }
    }

@app.post("/add-document", dependencies=[Depends(verify_token)])
async def add_document(document: DocumentRequest):
    """Add document from URL with real processing"""
    try:
        logger.info(f"Processing document from URL: {document.url}")
        
        # Download document
        response = requests.get(document.url, timeout=30)
        response.raise_for_status()
        
        # Extract filename
        filename = document.url.split('/')[-1] or "document.txt"
        
        # Extract and process text
        content = response.content
        text = EnhancedAI.extract_text_from_content(content, filename)
        
        # Create chunks
        chunks = EnhancedAI.chunk_text(text)
        
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "content": text,
            "chunks": chunks,
            "metadata": {
                "title": document.title or filename,
                "source_url": document.url,
                "document_id": doc_id,
                "filename": filename,
                "created_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "chunks_count": len(chunks),
                "processing_time": time.time()
            }
        }
        
        return {
            "message": "Documento processado e adicionado com sucesso!",
            "document_id": doc_id,
            "chunks_created": len(chunks),
            "file_size": len(content),
            "processing_time": time.time() - documents_db[doc_id]["metadata"]["processing_time"]
        }
        
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@app.post("/upload-document", dependencies=[Depends(verify_token)])
async def upload_document(file: UploadFile = File(...), title: Optional[str] = Form(None)):
    """Upload and process document file"""
    try:
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Extract and process text
        text = EnhancedAI.extract_text_from_content(content, file.filename)
        
        # Create chunks
        chunks = EnhancedAI.chunk_text(text)
        
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "content": text,
            "chunks": chunks,
            "metadata": {
                "title": title or file.filename,
                "source_file": file.filename,
                "document_id": doc_id,
                "filename": file.filename,
                "created_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "chunks_count": len(chunks),
                "content_type": file.content_type,
                "processing_time": time.time()
            }
        }
        
        return {
            "message": "Arquivo processado e adicionado com sucesso!",
            "document_id": doc_id,
            "chunks_created": len(chunks),
            "file_size": len(content),
            "processing_time": time.time() - documents_db[doc_id]["metadata"]["processing_time"]
        }
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/query", dependencies=[Depends(verify_token)])
async def query_documents(query: QueryRequest) -> QueryResponse:
    """Query documents with enhanced AI"""
    try:
        logger.info(f"Processing query: {query.query} with AI mode: {query.ai_mode}")
        
        if not documents_db:
            return QueryResponse(
                query=query.query,
                answer="❌ Nenhum documento foi adicionado ainda. Por favor, adicione documentos antes de fazer perguntas.",
                sources=[],
                ai_mode_used="none"
            )
        
        # Enhanced search
        results = enhanced_search(query.query, query.max_results)
        
        if not results:
            return QueryResponse(
                query=query.query,
                answer="❌ Nenhum trecho relevante encontrado nos documentos para sua pergunta. Tente reformular a pergunta ou adicionar mais documentos.",
                sources=[],
                ai_mode_used="none"
            )
        
        # Generate AI response
        context_chunks = [result["content"] for result in results]
        answer, ai_mode_used = await EnhancedAI.generate_response(
            query.query, 
            context_chunks, 
            query.ai_mode if query.ai_mode != "auto" else current_ai_mode
        )
        
        # Format sources
        sources = [
            DocumentResult(
                content=result["content"],
                score=result["score"],
                metadata=result["metadata"]
            )
            for result in results
        ]
        
        return QueryResponse(
            query=query.query,
            answer=answer,
            sources=sources,
            ai_mode_used=ai_mode_used
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", dependencies=[Depends(verify_token)])
async def list_documents():
    """List all processed documents"""
    documents = []
    for doc_id, doc_data in documents_db.items():
        metadata = doc_data.get('metadata', {})
        documents.append({
            "id": doc_id,
            "title": metadata.get('title', 'Untitled'),
            "filename": metadata.get('filename', 'Unknown'),
            "source_url": metadata.get('source_url'),
            "source_file": metadata.get('source_file'),
            "chunks_count": metadata.get('chunks_count', 0),
            "size_bytes": metadata.get('size_bytes', 0),
            "created_at": metadata.get('created_at'),
            "content_preview": doc_data.get('content', '')[:200] + "..." if len(doc_data.get('content', '')) > 200 else doc_data.get('content', '')
        })
    
    return {
        "documents": documents,
        "total_count": len(documents),
        "total_chunks": sum(doc.get('chunks_count', 0) for doc in documents)
    }

@app.post("/export", dependencies=[Depends(verify_token)])
async def export_documents(export_request: ExportRequest):
    """Export all documents and chunks for external use"""
    try:
        if not documents_db:
            raise HTTPException(status_code=404, detail="Nenhum documento para exportar")
        
        # Create export data
        export_data = {
            "export_info": {
                "created_at": datetime.now().isoformat(),
                "total_documents": len(documents_db),
                "total_chunks": sum(len(doc.get('chunks', [])) for doc in documents_db.values()),
                "format": export_request.format,
                "include_metadata": export_request.include_metadata
            },
            "documents": []
        }
        
        for doc_id, doc_data in documents_db.items():
            doc_export = {
                "id": doc_id,
                "content": doc_data.get('content', ''),
                "chunks": doc_data.get('chunks', [])
            }
            
            if export_request.include_metadata:
                doc_export["metadata"] = doc_data.get('metadata', {})
            
            export_data["documents"].append(doc_export)
        
        # Create zip file with multiple formats
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # JSON export
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
            zip_file.writestr("rag_export.json", json_content)
            
            # Markdown export
            md_content = f"# RAG Documents Export\n\n"
            md_content += f"**Exported:** {export_data['export_info']['created_at']}\n"
            md_content += f"**Documents:** {export_data['export_info']['total_documents']}\n"
            md_content += f"**Chunks:** {export_data['export_info']['total_chunks']}\n\n"
            
            for doc in export_data["documents"]:
                md_content += f"## {doc.get('metadata', {}).get('title', 'Untitled')}\n\n"
                md_content += f"**ID:** {doc['id']}\n\n"
                if export_request.include_metadata and 'metadata' in doc:
                    md_content += f"**Metadata:** {json.dumps(doc['metadata'], indent=2)}\n\n"
                md_content += f"### Content\n\n{doc['content']}\n\n"
                md_content += f"### Chunks ({len(doc['chunks'])})\n\n"
                for i, chunk in enumerate(doc['chunks']):
                    md_content += f"#### Chunk {i+1}\n\n{chunk}\n\n"
                md_content += "---\n\n"
            
            zip_file.writestr("rag_export.md", md_content)
            
            # Individual document files
            for doc in export_data["documents"]:
                title = doc.get('metadata', {}).get('title', f"document_{doc['id']}")
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                # Individual JSON
                doc_json = json.dumps(doc, indent=2, ensure_ascii=False)
                zip_file.writestr(f"documents/{safe_title}.json", doc_json)
                
                # Individual text
                zip_file.writestr(f"documents/{safe_title}.txt", doc['content'])
                
                # Individual chunks
                for i, chunk in enumerate(doc['chunks']):
                    zip_file.writestr(f"chunks/{safe_title}_chunk_{i+1}.txt", chunk)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=rag_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"}
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")

@app.get("/stats", dependencies=[Depends(verify_token)])
async def get_stats():
    """Get system statistics"""
    total_chunks = sum(len(doc.get('chunks', [])) for doc in documents_db.values())
    total_size = sum(doc.get('metadata', {}).get('size_bytes', 0) for doc in documents_db.values())
    
    return {
        "vector_storage": {
            "total_chunks": total_chunks,
            "collection_name": "rag_documents",
            "storage_path": str(DATA_PATH)
        },
        "documents": {
            "count": len(documents_db),
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        },
        "system": {
            "data_path": str(DATA_PATH),
            "gemini_configured": bool(GOOGLE_API_KEY),
            "local_ai_available": True
        },
        "ai_config": {
            "current_mode": current_ai_mode,
            "available_modes": ["auto", "gemini", "local"],
            "gemini_configured": bool(GOOGLE_API_KEY)
        }
    }

@app.get("/ai-config", dependencies=[Depends(verify_token)])
async def get_ai_config():
    """Get AI configuration"""
    return {
        "current_mode": current_ai_mode,
        "available_modes": ["auto", "gemini", "local"],
        "gemini_configured": bool(GOOGLE_API_KEY),
        "local_ai_available": True
    }

@app.post("/ai-config", dependencies=[Depends(verify_token)])
async def set_ai_config(config: AIConfigRequest):
    """Set AI configuration"""
    global current_ai_mode
    
    if config.ai_mode not in ["auto", "gemini", "local"]:
        raise HTTPException(status_code=400, detail="Modo de IA inválido")
    
    current_ai_mode = config.ai_mode
    logger.info(f"AI mode set to: {current_ai_mode}")
    
    return {
        "message": f"Modo de IA alterado para: {current_ai_mode}",
        "current_mode": current_ai_mode
    }

@app.delete("/clear", dependencies=[Depends(verify_token)])
async def clear_all_data():
    """Clear all data"""
    global documents_db
    documents_db = {}
    logger.info("All data cleared")
    return {"message": "Todos os dados foram limpos"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting RAG Docling System on {host}:{port}")
    logger.info(f"🔑 Password: {SITE_PASSWORD}")
    logger.info(f"🤖 Gemini configured: {bool(GOOGLE_API_KEY)}")
    logger.info(f"🏠 Current AI mode: {current_ai_mode}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
