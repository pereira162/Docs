# RAG Docling System - Servidor principal com Docling avançado

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
import subprocess

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_docling_system")

# Initialize FastAPI
app = FastAPI(
    title="RAG Docling System", 
    version="2.1.0",
    description="Sistema RAG completo com Docling avançado, Ollama e gerenciamento de documentos"
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

# Enhanced AI with Docling and Ollama integration
class EnhancedAI:
    @staticmethod
    def extract_text_with_docling(content: bytes, filename: str) -> Dict:
        """Extract text using Docling for advanced document processing"""
        try:
            # Try to import Docling
            try:
                from docling.document_converter import DocumentConverter
                from docling.datamodel.base_models import DocumentStream
                from docling.chunking import HybridChunker
                logger.info(f"Using Docling for advanced processing of {filename}")
                
                # Create document stream
                buf = io.BytesIO(content)
                source = DocumentStream(name=filename, stream=buf)
                
                # Convert with Docling
                converter = DocumentConverter()
                result = converter.convert(source)
                
                if result.status.success:
                    doc = result.document
                    
                    # Extract metadata
                    metadata = {
                        "title": doc.name or filename,
                        "pages": getattr(doc, 'page_count', 0),
                        "tables": len([item for item in doc.texts if hasattr(item, 'label') and 'table' in str(item.label).lower()]),
                        "images": len([item for item in doc.texts if hasattr(item, 'label') and 'image' in str(item.label).lower()]),
                        "processing_method": "docling"
                    }
                    
                    # Export to markdown for better structure preservation
                    full_text = doc.export_to_markdown()
                    
                    # Create chunks using Docling's HybridChunker
                    chunker = HybridChunker()
                    chunks = []
                    
                    for chunk in chunker.chunk(doc):
                        chunk_data = {
                            "text": chunk.text,
                            "metadata": chunk.meta.export_json_dict() if hasattr(chunk.meta, 'export_json_dict') else {}
                        }
                        chunks.append(chunk_data)
                    
                    return {
                        "text": full_text,
                        "chunks": chunks,
                        "metadata": metadata,
                        "success": True
                    }
                else:
                    logger.warning(f"Docling failed to process {filename}, falling back to simple extraction")
                    
            except ImportError:
                logger.warning("Docling not available, using fallback extraction")
            except Exception as e:
                logger.error(f"Docling processing error: {e}")
            
            # Fallback to simple extraction
            return EnhancedAI.extract_text_simple(content, filename)
            
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            return {
                "text": f"Erro ao extrair texto do arquivo {filename}: {str(e)}",
                "chunks": [],
                "metadata": {"processing_method": "error", "error": str(e)},
                "success": False
            }

    @staticmethod
    def extract_text_simple(content: bytes, filename: str) -> Dict:
        """Simple text extraction fallback"""
        try:
            if filename.lower().endswith('.txt'):
                text = content.decode('utf-8', errors='ignore')
            elif filename.lower().endswith('.md'):
                text = content.decode('utf-8', errors='ignore')
            elif filename.lower().endswith('.pdf'):
                text = content.decode('utf-8', errors='ignore')[:10000]  # Limit for safety
            else:
                text = f"Arquivo: {filename}\nTamanho: {len(content)} bytes\nConteúdo processado com método simples."
            
            # Simple chunking
            chunks = EnhancedAI.chunk_text_simple(text)
            
            return {
                "text": text,
                "chunks": [{"text": chunk, "metadata": {}} for chunk in chunks],
                "metadata": {"processing_method": "simple", "file_size": len(content)},
                "success": True
            }
        except Exception as e:
            return {
                "text": f"Erro na extração simples: {str(e)}",
                "chunks": [],
                "metadata": {"processing_method": "error", "error": str(e)},
                "success": False
            }

    @staticmethod
    def chunk_text_simple(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking for fallback"""
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
    def check_ollama_available() -> bool:
        """Check if Ollama is available"""
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    async def generate_response_ollama(query: str, context_chunks: List[str], model: str = "llama3.2:1b") -> tuple[str, str]:
        """Generate response using Ollama"""
        try:
            if not EnhancedAI.check_ollama_available():
                raise Exception("Ollama não está disponível")
            
            # Prepare context
            context = "\n\n".join(context_chunks[:3])
            
            prompt = f"""Baseado no contexto fornecido, responda à pergunta de forma precisa e informativa.

CONTEXTO:
{context[:2000]}

PERGUNTA: {query}

RESPOSTA:"""
            
            # Call Ollama
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                return f"🤖 **Resposta do Ollama ({model}):**\n\n{response}\n\n💡 *{len(context_chunks)} trechos relevantes encontrados.*", "ollama"
            else:
                raise Exception(f"Ollama error: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            # Fallback to local processing
            return await EnhancedAI.generate_response_local(query, context_chunks)

    @staticmethod
    async def generate_response_local(query: str, context_chunks: List[str]) -> tuple[str, str]:
        """Enhanced local AI response"""
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

    @staticmethod
    async def generate_response(query: str, context_chunks: List[str], mode: str = "auto") -> tuple[str, str]:
        """Generate enhanced response with multiple AI options"""
        
        # Gemini mode
        if mode == "gemini" and GOOGLE_API_KEY:
            try:
                context = "\n\n".join(context_chunks[:3])
                response = f"""**Resposta baseada nos documentos (Simulado Gemini):**

Baseado no contexto fornecido para "{query}":

{context[:800]}

Esta é uma resposta simulada do Gemini. Para usar o Gemini real, instale: `pip install google-generativeai`

💡 **Informação:** {len(context_chunks)} trechos relevantes encontrados."""
                return response, "gemini"
                
            except Exception as e:
                logger.error(f"Gemini error: {e}")
        
        # Ollama mode
        if mode == "ollama" or (mode == "auto" and EnhancedAI.check_ollama_available()):
            return await EnhancedAI.generate_response_ollama(query, context_chunks)
        
        # Local fallback
        return await EnhancedAI.generate_response_local(query, context_chunks)

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
    """Add document from URL with advanced Docling processing"""
    try:
        logger.info(f"Processing document from URL: {document.url}")
        
        # Download document
        response = requests.get(document.url, timeout=30)
        response.raise_for_status()
        
        # Extract filename
        filename = document.url.split('/')[-1] or "document.txt"
        
        # Extract and process text with Docling
        content = response.content
        extraction_result = EnhancedAI.extract_text_with_docling(content, filename)
        
        if not extraction_result["success"]:
            raise HTTPException(status_code=500, detail=f"Falha no processamento: {extraction_result.get('metadata', {}).get('error', 'Erro desconhecido')}")
        
        text = extraction_result["text"]
        chunks_data = extraction_result["chunks"]
        processing_metadata = extraction_result["metadata"]
        
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "content": text,
            "chunks": [chunk["text"] for chunk in chunks_data],
            "chunks_metadata": chunks_data,
            "metadata": {
                "title": document.title or processing_metadata.get("title", filename),
                "source_url": document.url,
                "document_id": doc_id,
                "filename": filename,
                "created_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "chunks_count": len(chunks_data),
                "processing_time": time.time(),
                "processing_method": processing_metadata.get("processing_method", "unknown"),
                "pages": processing_metadata.get("pages", 0),
                "tables": processing_metadata.get("tables", 0),
                "images": processing_metadata.get("images", 0)
            }
        }
        
        return {
            "message": "Documento processado e adicionado com sucesso!",
            "document_id": doc_id,
            "chunks_created": len(chunks_data),
            "file_size": len(content),
            "processing_time": time.time() - documents_db[doc_id]["metadata"]["processing_time"],
            "processing_method": processing_metadata.get("processing_method"),
            "pages": processing_metadata.get("pages", 0),
            "tables": processing_metadata.get("tables", 0),
            "images": processing_metadata.get("images", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@app.post("/upload-document", dependencies=[Depends(verify_token)])
async def upload_document(file: UploadFile = File(...), title: Optional[str] = Form(None)):
    """Upload and process document file with advanced Docling processing"""
    try:
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Extract and process text with Docling
        extraction_result = EnhancedAI.extract_text_with_docling(content, file.filename)
        
        if not extraction_result["success"]:
            raise HTTPException(status_code=500, detail=f"Falha no processamento: {extraction_result.get('metadata', {}).get('error', 'Erro desconhecido')}")
        
        text = extraction_result["text"]
        chunks_data = extraction_result["chunks"]
        processing_metadata = extraction_result["metadata"]
        
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "content": text,
            "chunks": [chunk["text"] for chunk in chunks_data],
            "chunks_metadata": chunks_data,
            "metadata": {
                "title": title or processing_metadata.get("title", file.filename),
                "source_file": file.filename,
                "document_id": doc_id,
                "filename": file.filename,
                "created_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "chunks_count": len(chunks_data),
                "content_type": file.content_type,
                "processing_time": time.time(),
                "processing_method": processing_metadata.get("processing_method", "unknown"),
                "pages": processing_metadata.get("pages", 0),
                "tables": processing_metadata.get("tables", 0),
                "images": processing_metadata.get("images", 0)
            }
        }
        
        return {
            "message": "Arquivo processado e adicionado com sucesso!",
            "document_id": doc_id,
            "chunks_created": len(chunks_data),
            "file_size": len(content),
            "processing_time": time.time() - documents_db[doc_id]["metadata"]["processing_time"],
            "processing_method": processing_metadata.get("processing_method"),
            "pages": processing_metadata.get("pages", 0),
            "tables": processing_metadata.get("tables", 0),
            "images": processing_metadata.get("images", 0)
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
    """List all processed documents with enhanced metadata"""
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
            "processing_method": metadata.get('processing_method', 'unknown'),
            "pages": metadata.get('pages', 0),
            "tables": metadata.get('tables', 0),
            "images": metadata.get('images', 0),
            "content_preview": doc_data.get('content', '')[:200] + "..." if len(doc_data.get('content', '')) > 200 else doc_data.get('content', '')
        })
    
    return {
        "documents": documents,
        "total_count": len(documents),
        "total_chunks": sum(doc.get('chunks_count', 0) for doc in documents)
    }

@app.get("/documents/{document_id}", dependencies=[Depends(verify_token)])
async def get_document(document_id: str):
    """Get specific document details"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc_data = documents_db[document_id]
    return {
        "id": document_id,
        "content": doc_data.get('content', ''),
        "chunks": doc_data.get('chunks', []),
        "chunks_metadata": doc_data.get('chunks_metadata', []),
        "metadata": doc_data.get('metadata', {})
    }

@app.delete("/documents/{document_id}", dependencies=[Depends(verify_token)])
async def delete_document(document_id: str):
    """Delete specific document"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc_metadata = documents_db[document_id].get('metadata', {})
    title = doc_metadata.get('title', 'Documento sem título')
    
    del documents_db[document_id]
    logger.info(f"Document deleted: {document_id} - {title}")
    
    return {
        "message": f"Documento '{title}' deletado com sucesso",
        "document_id": document_id
    }

@app.post("/documents/{document_id}/export", dependencies=[Depends(verify_token)])
async def export_single_document(document_id: str, export_request: ExportRequest):
    """Export single document"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc_data = documents_db[document_id]
    metadata = doc_data.get('metadata', {})
    
    # Create export data for single document
    export_data = {
        "export_info": {
            "created_at": datetime.now().isoformat(),
            "document_id": document_id,
            "document_title": metadata.get('title', 'Untitled'),
            "total_chunks": len(doc_data.get('chunks', [])),
            "format": export_request.format,
            "include_metadata": export_request.include_metadata
        },
        "document": {
            "id": document_id,
            "content": doc_data.get('content', ''),
            "chunks": doc_data.get('chunks', [])
        }
    }
    
    if export_request.include_metadata:
        export_data["document"]["metadata"] = metadata
        export_data["document"]["chunks_metadata"] = doc_data.get('chunks_metadata', [])
    
    # Create zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # JSON export
        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
        zip_file.writestr(f"{metadata.get('title', 'document')}_{document_id}.json", json_content)
        
        # Markdown export
        md_content = f"# {metadata.get('title', 'Documento')}\n\n"
        md_content += f"**ID:** {document_id}\n"
        md_content += f"**Exportado:** {export_data['export_info']['created_at']}\n"
        md_content += f"**Chunks:** {export_data['export_info']['total_chunks']}\n\n"
        
        if export_request.include_metadata:
            md_content += f"## Metadata\n\n```json\n{json.dumps(metadata, indent=2)}\n```\n\n"
        
        md_content += f"## Conteúdo\n\n{doc_data.get('content', '')}\n\n"
        
        md_content += f"## Chunks ({len(doc_data.get('chunks', []))})\n\n"
        for i, chunk in enumerate(doc_data.get('chunks', [])):
            md_content += f"### Chunk {i+1}\n\n{chunk}\n\n"
        
        zip_file.writestr(f"{metadata.get('title', 'document')}_{document_id}.md", md_content)
        
        # Individual chunks
        for i, chunk in enumerate(doc_data.get('chunks', [])):
            zip_file.writestr(f"chunks/chunk_{i+1}.txt", chunk)
    
    zip_buffer.seek(0)
    
    title_safe = "".join(c for c in metadata.get('title', 'document') if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={title_safe}_{document_id}.zip"}
    )

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
    """Get enhanced system statistics"""
    total_chunks = sum(len(doc.get('chunks', [])) for doc in documents_db.values())
    total_size = sum(doc.get('metadata', {}).get('size_bytes', 0) for doc in documents_db.values())
    
    # Count documents by processing method
    processing_methods = {}
    for doc in documents_db.values():
        method = doc.get('metadata', {}).get('processing_method', 'unknown')
        processing_methods[method] = processing_methods.get(method, 0) + 1
    
    # Check Ollama availability
    ollama_available = EnhancedAI.check_ollama_available()
    ollama_models = []
    if ollama_available:
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse ollama list output
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            ollama_models.append(parts[0])
        except Exception:
            pass
    
    return {
        "vector_storage": {
            "total_chunks": total_chunks,
            "collection_name": "rag_documents",
            "storage_path": str(DATA_PATH)
        },
        "documents": {
            "count": len(documents_db),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "processing_methods": processing_methods
        },
        "system": {
            "data_path": str(DATA_PATH),
            "gemini_configured": bool(GOOGLE_API_KEY),
            "local_ai_available": True,
            "ollama_available": ollama_available,
            "ollama_models": ollama_models
        },
        "ai_config": {
            "current_mode": current_ai_mode,
            "available_modes": ["auto", "gemini", "local", "ollama"],
            "gemini_configured": bool(GOOGLE_API_KEY),
            "ollama_available": ollama_available
        }
    }

@app.get("/ai-config", dependencies=[Depends(verify_token)])
async def get_ai_config():
    """Get AI configuration with Ollama support"""
    ollama_available = EnhancedAI.check_ollama_available()
    return {
        "current_mode": current_ai_mode,
        "available_modes": ["auto", "gemini", "local", "ollama"],
        "gemini_configured": bool(GOOGLE_API_KEY),
        "local_ai_available": True,
        "ollama_available": ollama_available
    }

@app.post("/ai-config", dependencies=[Depends(verify_token)])
async def set_ai_config(config: AIConfigRequest):
    """Set AI configuration with Ollama support"""
    global current_ai_mode
    
    if config.ai_mode not in ["auto", "gemini", "local", "ollama"]:
        raise HTTPException(status_code=400, detail="Modo de IA inválido")
    
    # Check if Ollama is available when trying to set it
    if config.ai_mode == "ollama" and not EnhancedAI.check_ollama_available():
        raise HTTPException(status_code=400, detail="Ollama não está disponível")
    
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
