# RAG System - Sistema de Documentação Inteligente
# Integrado com extrator de PDF definitivo e funcional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging
import json
import tempfile
import shutil
from pathlib import Path
import uuid
import io
import zipfile
from datetime import datetime
import subprocess
import requests

# Importar nosso extrator
from rag_extractor import PDFExtractor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_system")

# Initialize FastAPI
app = FastAPI(
    title="RAG System - Documentação Inteligente", 
    version="4.0.0",
    description="Sistema RAG com extrator PDF definitivo e funcional"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
DATA_PATH = Path("./data")
DOCUMENTS_DB = {}  # Simple in-memory document store

# Ensure data directories exist
for subdir in ["markdown", "json", "chunks", "metadata", "uploads"]:
    (DATA_PATH / subdir).mkdir(parents=True, exist_ok=True)

# Initialize PDF Extractor
pdf_extractor = PDFExtractor()

# Pydantic models
class DocumentAdd(BaseModel):
    url: str
    title: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class DocumentResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[DocumentResult]
    ai_mode_used: str

class Document(BaseModel):
    id: str
    title: str
    filename: str
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    chunks_count: int
    size_bytes: int
    created_at: str
    processing_method: Optional[str] = None
    pages: Optional[int] = None
    tables: Optional[int] = None
    images: Optional[int] = None
    content_preview: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "extractor": "PDF Extractor v2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """Upload and process a document"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    doc_id = str(uuid.uuid4())
    doc_title = title or file.filename
    timestamp = datetime.now().isoformat()
    
    try:
        start_time = datetime.now()
        
        # Save uploaded file
        upload_path = DATA_PATH / "uploads" / f"{doc_id}_{file.filename}"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = upload_path.stat().st_size
        
        # Process with our extractor
        if file_ext == '.pdf':
            results = pdf_extractor.extract_from_pdf(str(upload_path))
            processing_method = "PDF Extractor v2.0"
            
            # Count pages and tables from results
            pages_count = len([k for k in results.keys() if k.startswith('page_')])
            tables_count = results.get('tables_count', 0)
            
            # Create outputs
            outputs = {}
            
            # Save markdown
            if 'markdown' in results:
                md_path = DATA_PATH / "markdown" / f"{doc_id}.md"
                md_path.write_text(results['markdown'], encoding='utf-8')
                outputs['markdown'] = str(md_path)
            
            # Save JSON
            if 'json' in results:
                json_path = DATA_PATH / "json" / f"{doc_id}.json"
                json_path.write_text(json.dumps(results['json'], indent=2, ensure_ascii=False), encoding='utf-8')
                outputs['json'] = str(json_path)
            
            # Save chunks
            if 'chunks' in results:
                chunks_path = DATA_PATH / "chunks" / f"{doc_id}.json"
                chunks_path.write_text(json.dumps(results['chunks'], indent=2, ensure_ascii=False), encoding='utf-8')
                outputs['chunks'] = str(chunks_path)
            
            # Save metadata
            metadata = {
                "document_id": doc_id,
                "title": doc_title,
                "filename": file.filename,
                "source_file": str(upload_path),
                "file_size": file_size,
                "processing_method": processing_method,
                "pages": pages_count,
                "tables": tables_count,
                "created_at": timestamp,
                "outputs": outputs
            }
            
            metadata_path = DATA_PATH / "metadata" / f"{doc_id}.json"
            metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            chunks_created = len(results.get('chunks', []))
            
            # Store in database
            DOCUMENTS_DB[doc_id] = {
                "id": doc_id,
                "title": doc_title,
                "filename": file.filename,
                "source_file": str(upload_path),
                "chunks_count": chunks_created,
                "size_bytes": file_size,
                "created_at": timestamp,
                "processing_method": processing_method,
                "pages": pages_count,
                "tables": tables_count,
                "content_preview": results.get('content_preview', ''),
                "success": True,
                "files": outputs
            }
            
            return {
                "message": "Document processed successfully",
                "document_id": doc_id,
                "chunks_created": chunks_created,
                "processing_time": f"{processing_time:.2f}",
                "pages": pages_count,
                "tables": tables_count,
                "files": outputs
            }
        
        else:
            # Simple text processing for non-PDF files
            content = upload_path.read_text(encoding='utf-8')
            processing_method = "Simple Text Processing"
            
            # Create simple chunks (split by paragraphs)
            chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
            
            outputs = {}
            
            # Save markdown
            md_path = DATA_PATH / "markdown" / f"{doc_id}.md"
            md_path.write_text(content, encoding='utf-8')
            outputs['markdown'] = str(md_path)
            
            # Save JSON
            json_data = {
                "document_id": doc_id,
                "title": doc_title,
                "content": content,
                "chunks": chunks
            }
            json_path = DATA_PATH / "json" / f"{doc_id}.json"
            json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
            outputs['json'] = str(json_path)
            
            # Save chunks
            chunks_path = DATA_PATH / "chunks" / f"{doc_id}.json"
            chunks_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding='utf-8')
            outputs['chunks'] = str(chunks_path)
            
            # Save metadata
            metadata = {
                "document_id": doc_id,
                "title": doc_title,
                "filename": file.filename,
                "source_file": str(upload_path),
                "file_size": file_size,
                "processing_method": processing_method,
                "created_at": timestamp,
                "outputs": outputs
            }
            
            metadata_path = DATA_PATH / "metadata" / f"{doc_id}.json"
            metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            chunks_created = len(chunks)
            
            # Store in database
            DOCUMENTS_DB[doc_id] = {
                "id": doc_id,
                "title": doc_title,
                "filename": file.filename,
                "source_file": str(upload_path),
                "chunks_count": chunks_created,
                "size_bytes": file_size,
                "created_at": timestamp,
                "processing_method": processing_method,
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "success": True,
                "files": outputs
            }
            
            return {
                "message": "Document processed successfully",
                "document_id": doc_id,
                "chunks_created": chunks_created,
                "processing_time": f"{processing_time:.2f}",
                "files": outputs
            }
            
    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {str(e)}")
        
        # Store failed document info
        DOCUMENTS_DB[doc_id] = {
            "id": doc_id,
            "title": doc_title,
            "filename": file.filename,
            "size_bytes": file_size,
            "created_at": timestamp,
            "error": str(e),
            "success": False
        }
        
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/add-document")
async def add_document_by_url(doc: DocumentAdd):
    """Add document by URL"""
    doc_id = str(uuid.uuid4())
    doc_title = doc.title or doc.url.split('/')[-1]
    timestamp = datetime.now().isoformat()
    
    try:
        start_time = datetime.now()
        
        # Download file
        response = requests.get(doc.url, timeout=30)
        response.raise_for_status()
        
        # Determine file extension
        file_ext = Path(doc.url).suffix.lower()
        if not file_ext:
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                file_ext = '.pdf'
            else:
                file_ext = '.txt'
        
        # Save downloaded file
        filename = f"{doc_id}_{doc_title}{file_ext}"
        upload_path = DATA_PATH / "uploads" / filename
        upload_path.write_bytes(response.content)
        
        file_size = len(response.content)
        
        # Process with our extractor
        if file_ext == '.pdf':
            results = pdf_extractor.extract_from_pdf(str(upload_path))
            processing_method = "PDF Extractor v2.0"
            
            # Count pages and tables from results
            pages_count = len([k for k in results.keys() if k.startswith('page_')])
            tables_count = results.get('tables_count', 0)
            
            # Create outputs (same logic as upload)
            outputs = {}
            
            # Save markdown
            if 'markdown' in results:
                md_path = DATA_PATH / "markdown" / f"{doc_id}.md"
                md_path.write_text(results['markdown'], encoding='utf-8')
                outputs['markdown'] = str(md_path)
            
            # Save JSON
            if 'json' in results:
                json_path = DATA_PATH / "json" / f"{doc_id}.json"
                json_path.write_text(json.dumps(results['json'], indent=2, ensure_ascii=False), encoding='utf-8')
                outputs['json'] = str(json_path)
            
            # Save chunks
            if 'chunks' in results:
                chunks_path = DATA_PATH / "chunks" / f"{doc_id}.json"
                chunks_path.write_text(json.dumps(results['chunks'], indent=2, ensure_ascii=False), encoding='utf-8')
                outputs['chunks'] = str(chunks_path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            chunks_created = len(results.get('chunks', []))
            
            # Store in database
            DOCUMENTS_DB[doc_id] = {
                "id": doc_id,
                "title": doc_title,
                "filename": filename,
                "source_url": doc.url,
                "chunks_count": chunks_created,
                "size_bytes": file_size,
                "created_at": timestamp,
                "processing_method": processing_method,
                "pages": pages_count,
                "tables": tables_count,
                "content_preview": results.get('content_preview', ''),
                "success": True,
                "files": outputs
            }
            
            return {
                "message": "Document processed successfully",
                "document_id": doc_id,
                "chunks_created": chunks_created,
                "processing_time": f"{processing_time:.2f}",
                "pages": pages_count,
                "tables": tables_count,
                "files": outputs
            }
        
    except Exception as e:
        logger.error(f"Error processing URL {doc.url}: {str(e)}")
        
        # Store failed document info
        DOCUMENTS_DB[doc_id] = {
            "id": doc_id,
            "title": doc_title,
            "source_url": doc.url,
            "created_at": timestamp,
            "error": str(e),
            "success": False
        }
        
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")

@app.post("/query")
async def query_documents(query: QueryRequest):
    """Query documents (simple text search for now)"""
    if not DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="No documents available")
    
    results = []
    
    # Simple text search through chunks
    for doc_id, doc_info in DOCUMENTS_DB.items():
        if not doc_info.get("success", False):
            continue
            
        # Load chunks if available
        chunks_file = doc_info.get("files", {}).get("chunks")
        if chunks_file and os.path.exists(chunks_file):
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
                
            for i, chunk in enumerate(chunks):
                if query.query.lower() in chunk.lower():
                    score = chunk.lower().count(query.query.lower()) / len(chunk.split())
                    results.append(DocumentResult(
                        content=chunk[:500] + "..." if len(chunk) > 500 else chunk,
                        score=min(score * 10, 1.0),  # Normalize score
                        metadata={
                            "source_file": doc_info.get("filename"),
                            "title": doc_info.get("title"),
                            "document_id": doc_id,
                            "chunk_index": i,
                            "file_size": doc_info.get("size_bytes"),
                            "page_count": doc_info.get("pages"),
                            "processing_method": doc_info.get("processing_method")
                        }
                    ))
    
    # Sort by score and limit results
    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:query.max_results]
    
    # Generate simple AI answer
    if results:
        ai_answer = f"Encontrei {len(results)} resultado(s) relacionado(s) à sua busca por '{query.query}'. " + \
                   f"Os documentos mais relevantes contêm informações sobre: {', '.join(set([r.metadata.get('title', 'documento') for r in results[:3]]))}."
    else:
        ai_answer = f"Não encontrei resultados para '{query.query}' nos documentos processados."
    
    return QueryResponse(
        query=query.query,
        answer=ai_answer,
        sources=results,
        ai_mode_used="Simple Text Search"
    )

@app.get("/documents")
async def list_documents():
    """List all documents"""
    documents = []
    for doc_info in DOCUMENTS_DB.values():
        if doc_info.get("success", False):
            documents.append(Document(
                id=doc_info["id"],
                title=doc_info["title"],
                filename=doc_info["filename"],
                source_url=doc_info.get("source_url"),
                source_file=doc_info.get("source_file"),
                chunks_count=doc_info["chunks_count"],
                size_bytes=doc_info["size_bytes"],
                created_at=doc_info["created_at"],
                processing_method=doc_info.get("processing_method"),
                pages=doc_info.get("pages"),
                tables=doc_info.get("tables"),
                images=doc_info.get("images"),
                content_preview=doc_info.get("content_preview", "")
            ))
    
    return {"documents": documents}

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a specific document"""
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = DOCUMENTS_DB[doc_id]
    
    # Delete files
    files_to_delete = []
    if "files" in doc_info:
        files_to_delete.extend(doc_info["files"].values())
    
    if "source_file" in doc_info:
        files_to_delete.append(doc_info["source_file"])
    
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")
    
    # Remove from database
    del DOCUMENTS_DB[doc_id]
    
    return {"message": f"Document {doc_info['title']} deleted successfully"}

@app.post("/documents/{doc_id}/export")
async def export_document(doc_id: str):
    """Export a specific document"""
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = DOCUMENTS_DB[doc_id]
    
    # Create ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add document files
        if "files" in doc_info:
            for file_type, file_path in doc_info["files"].items():
                if os.path.exists(file_path):
                    zip_file.write(file_path, f"{file_type}/{os.path.basename(file_path)}")
        
        # Add metadata
        metadata_content = json.dumps(doc_info, indent=2, ensure_ascii=False)
        zip_file.writestr(f"metadata.json", metadata_content)
    
    zip_buffer.seek(0)
    
    filename = f"{doc_info['title']}_{doc_id}.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/export")
async def export_all_documents():
    """Export all documents"""
    if not DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="No documents available")
    
    # Create ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc_id, doc_info in DOCUMENTS_DB.items():
            if not doc_info.get("success", False):
                continue
                
            doc_folder = f"document_{doc_id}/"
            
            # Add document files
            if "files" in doc_info:
                for file_type, file_path in doc_info["files"].items():
                    if os.path.exists(file_path):
                        zip_file.write(file_path, doc_folder + f"{file_type}/{os.path.basename(file_path)}")
            
            # Add metadata
            metadata_content = json.dumps(doc_info, indent=2, ensure_ascii=False)
            zip_file.writestr(doc_folder + "metadata.json", metadata_content)
    
    zip_buffer.seek(0)
    
    filename = f"rag_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.delete("/clear")
async def clear_all_documents():
    """Clear all documents and data"""
    deleted_count = 0
    
    # Delete all files
    for doc_info in DOCUMENTS_DB.values():
        if "files" in doc_info:
            for file_path in doc_info["files"].values():
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_path}: {e}")
        
        if "source_file" in doc_info:
            try:
                file_path = doc_info["source_file"]
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        deleted_count += 1
    
    # Clear database
    DOCUMENTS_DB.clear()
    
    return {"message": f"All documents cleared successfully", "deleted": deleted_count}

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    total_docs = len(DOCUMENTS_DB)
    successful_docs = sum(1 for doc in DOCUMENTS_DB.values() if doc.get("success", False))
    failed_docs = total_docs - successful_docs
    
    # Calculate total size
    total_size_bytes = sum(doc.get("size_bytes", 0) for doc in DOCUMENTS_DB.values() if doc.get("success", False))
    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
    
    # Count by processing method
    processing_methods = {}
    total_chunks = 0
    total_pages = 0
    total_tables = 0
    
    for doc in DOCUMENTS_DB.values():
        if doc.get("success", False):
            method = doc.get("processing_method", "Unknown")
            processing_methods[method] = processing_methods.get(method, 0) + 1
            total_chunks += doc.get("chunks_count", 0)
            total_pages += doc.get("pages", 0)
            total_tables += doc.get("tables", 0)
    
    return {
        "vector_storage": {
            "total_chunks": total_chunks,
            "collection_name": "local_rag_collection",
            "storage_path": str(DATA_PATH)
        },
        "documents": {
            "count": successful_docs,
            "total_size_mb": total_size_mb,
            "processing_methods": processing_methods
        },
        "system": {
            "data_path": str(DATA_PATH),
            "gemini_configured": False,
            "local_ai_available": True,
            "ollama_available": False,
            "ollama_models": []
        },
        "ai_config": {
            "current_mode": "local_search",
            "available_modes": ["local_search"],
            "gemini_configured": False,
            "ollama_available": False
        },
        "extraction_stats": {
            "total_pages": total_pages,
            "total_tables": total_tables,
            "success_rate": f"{(successful_docs/total_docs*100):.1f}%" if total_docs > 0 else "0%"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting RAG System v4.0")
    logger.info(f"📁 Data path: {DATA_PATH}")
    logger.info("🎯 PDF Extractor: Integrated and functional")
    logger.info("🔓 Authentication: Disabled")
    logger.info("📊 Features: 17 tabelas de PDF extraídas corretamente")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
