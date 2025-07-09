"""
Integração FastAPI para Sistema de Web Scraping RAG - Versão 1.0
Autor: Assistant IA
Data: 2024

Este módulo fornece endpoints REST para o sistema de web scraping,
incluindo extração de sites, busca de conteúdo, download de arquivos
e análise de dados extraídos.
"""

import asyncio
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field

# Imports locais
from web_scraper_extractor import WebScraperExtractor
from web_scraping_data_manager import WebScrapingDataManager


# Modelos Pydantic
class WebScrapingRequest(BaseModel):
    """Modelo para requisição de web scraping"""
    start_url: HttpUrl = Field(..., description="URL inicial para extrair")
    max_depth: int = Field(default=2, ge=1, le=5, description="Profundidade máxima de navegação")
    max_pages: int = Field(default=20, ge=1, le=100, description="Número máximo de páginas")
    same_domain_only: bool = Field(default=True, description="Ficar apenas no mesmo domínio")
    delay_between_requests: float = Field(default=2.0, ge=0.5, le=10.0, description="Delay entre requisições")
    chunk_size: int = Field(default=512, ge=100, le=2000, description="Tamanho dos chunks")
    overlap: int = Field(default=50, ge=0, le=200, description="Sobreposição entre chunks")


class SearchRequest(BaseModel):
    """Modelo para requisição de busca"""
    query: str = Field(..., min_length=3, max_length=500, description="Texto de busca")
    limit: int = Field(default=10, ge=1, le=50, description="Número máximo de resultados")
    min_similarity: float = Field(default=0.1, ge=0.0, le=1.0, description="Similaridade mínima")


class WebScrapingResponse(BaseModel):
    """Modelo para resposta de web scraping"""
    task_id: str
    status: str
    message: str
    start_url: str
    extraction_summary: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Modelo para resposta de busca"""
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    search_timestamp: str


# FastAPI App
app = FastAPI(
    title="Web Scraping RAG API",
    description="API para extração e busca de conteúdo web com capacidades RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias globais
data_manager = WebScrapingDataManager("web_scraping_data")
active_tasks = {}


@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    print("🚀 Iniciando Web Scraping RAG API...")
    print(f"📂 Diretório de dados: {data_manager.data_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """Encerramento da aplicação"""
    print("🛑 Encerrando Web Scraping RAG API...")


def run_web_scraping_task(task_id: str, request_data: WebScrapingRequest):
    """
    Executa tarefa de web scraping em background
    """
    try:
        active_tasks[task_id] = {
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'progress': 0,
            'message': 'Iniciando extração...'
        }
        
        # Cria extrator
        extractor = WebScraperExtractor(
            base_output_dir=f"web_scraping_data/tasks/{task_id}",
            chunk_size=request_data.chunk_size,
            overlap=request_data.overlap,
            max_pages=request_data.max_pages,
            delay_between_requests=request_data.delay_between_requests
        )
        
        # Atualiza status
        active_tasks[task_id]['message'] = 'Extraindo conteúdo...'
        active_tasks[task_id]['progress'] = 10
        
        # Executa extração
        results = extractor.extract_from_website(
            start_url=str(request_data.start_url),
            max_depth=request_data.max_depth,
            same_domain_only=request_data.same_domain_only
        )
        
        # Atualiza status
        active_tasks[task_id]['message'] = 'Armazenando dados...'
        active_tasks[task_id]['progress'] = 80
        
        # Armazena no banco de dados
        for page_data in extractor.extracted_data:
            data_manager.store_web_page(page_data)
            
            # Analisa conteúdo
            if page_data.get('content'):
                data_manager.analyze_content(
                    page_data['page_id'], 
                    page_data['content']
                )
        
        # Armazena chunks
        if extractor.chunks:
            data_manager.store_chunks(extractor.chunks)
        
        # Armazena downloads
        if extractor.downloaded_files:
            data_manager.store_downloads(extractor.downloaded_files)
        
        # Finaliza tarefa
        active_tasks[task_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Extração concluída com sucesso!',
            'end_time': datetime.now().isoformat(),
            'results': results
        })
        
        print(f"✅ Tarefa {task_id} concluída com sucesso")
        
    except Exception as e:
        error_msg = f"Erro na tarefa {task_id}: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        
        active_tasks[task_id].update({
            'status': 'failed',
            'progress': 0,
            'message': error_msg,
            'end_time': datetime.now().isoformat(),
            'error': str(e)
        })


# Endpoints

@app.get("/", tags=["Status"])
async def root():
    """Endpoint raiz com informações da API"""
    stats = data_manager.get_statistics()
    return {
        "message": "Web Scraping RAG API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "database_stats": stats.get('database_stats', {}),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "extract": "/extract",
            "search": "/search",
            "tasks": "/tasks",
            "statistics": "/statistics"
        }
    }


@app.get("/health", tags=["Status"])
async def health_check():
    """Verificação de saúde da API"""
    try:
        stats = data_manager.get_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_accessible": True,
            "active_tasks": len(active_tasks),
            "total_pages": stats.get('database_stats', {}).get('total_pages', 0),
            "total_chunks": stats.get('database_stats', {}).get('total_chunks', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/extract", response_model=WebScrapingResponse, tags=["Web Scraping"])
async def extract_website(
    request: WebScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia extração de conteúdo de um website
    """
    try:
        # Gera ID único para a tarefa
        task_id = f"webscraping_{int(datetime.now().timestamp())}_{hash(str(request.start_url)) % 10000}"
        
        # Valida URL
        parsed_url = urlparse(str(request.start_url))
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="URL inválida")
        
        # Inicia tarefa em background
        background_tasks.add_task(run_web_scraping_task, task_id, request)
        
        # Inicializa status da tarefa
        active_tasks[task_id] = {
            'status': 'queued',
            'start_time': datetime.now().isoformat(),
            'progress': 0,
            'message': 'Tarefa adicionada à fila...',
            'request_data': request.dict()
        }
        
        return WebScrapingResponse(
            task_id=task_id,
            status="queued",
            message="Tarefa de extração iniciada",
            start_url=str(request.start_url)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar extração: {str(e)}")


@app.get("/tasks/{task_id}", tags=["Web Scraping"])
async def get_task_status(task_id: str):
    """
    Obtém status de uma tarefa de extração
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    return active_tasks[task_id]


@app.get("/tasks", tags=["Web Scraping"])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de tarefas")
):
    """
    Lista tarefas de extração
    """
    tasks = list(active_tasks.items())
    
    # Filtra por status se especificado
    if status:
        tasks = [(tid, tdata) for tid, tdata in tasks if tdata.get('status') == status]
    
    # Ordena por tempo de início (mais recente primeiro)
    tasks.sort(key=lambda x: x[1].get('start_time', ''), reverse=True)
    
    # Limita resultados
    tasks = tasks[:limit]
    
    return {
        "total_tasks": len(active_tasks),
        "filtered_tasks": len(tasks),
        "tasks": [
            {
                "task_id": tid,
                "status": tdata.get('status'),
                "start_time": tdata.get('start_time'),
                "progress": tdata.get('progress', 0),
                "message": tdata.get('message', '')
            }
            for tid, tdata in tasks
        ]
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_content(request: SearchRequest):
    """
    Busca conteúdo nos dados extraídos
    """
    try:
        # Realiza busca
        results = data_manager.search_chunks(
            query=request.query,
            limit=request.limit,
            min_similarity=request.min_similarity
        )
        
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            search_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@app.get("/search", tags=["Search"])
async def search_content_get(
    q: str = Query(..., min_length=3, max_length=500, description="Texto de busca"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    min_similarity: float = Query(0.1, ge=0.0, le=1.0, description="Similaridade mínima")
):
    """
    Busca conteúdo via GET (para facilitar testes)
    """
    request = SearchRequest(query=q, limit=limit, min_similarity=min_similarity)
    return await search_content(request)


@app.get("/statistics", tags=["Analytics"])
async def get_statistics():
    """
    Obtém estatísticas do banco de dados
    """
    try:
        stats = data_manager.get_statistics()
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "active_tasks_count": len(active_tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.get("/export/csv", tags=["Export"])
async def export_to_csv():
    """
    Exporta dados para CSV
    """
    try:
        exported_files = data_manager.export_to_csv()
        return {
            "message": "Exportação concluída",
            "timestamp": datetime.now().isoformat(),
            "exported_files": exported_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exportação: {str(e)}")


@app.get("/downloads/{filename}", tags=["Files"])
async def download_file(filename: str):
    """
    Download de arquivo extraído
    """
    try:
        # Procura arquivo nos diretórios de download
        download_dirs = [
            data_manager.data_dir / "downloads",
            data_manager.data_dir / "exports"
        ]
        
        file_path = None
        for download_dir in download_dirs:
            potential_path = download_dir / filename
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no download: {str(e)}")


@app.delete("/tasks/{task_id}", tags=["Web Scraping"])
async def cancel_task(task_id: str):
    """
    Cancela ou remove uma tarefa
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    task_data = active_tasks[task_id]
    
    if task_data.get('status') == 'running':
        # Para tarefas em execução, marca como cancelada
        active_tasks[task_id].update({
            'status': 'cancelled',
            'end_time': datetime.now().isoformat(),
            'message': 'Tarefa cancelada pelo usuário'
        })
    else:
        # Remove tarefa da lista
        del active_tasks[task_id]
    
    return {
        "message": f"Tarefa {task_id} cancelada/removida",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/cleanup", tags=["Maintenance"])
async def cleanup_old_data(days_old: int = Query(30, ge=1, le=365)):
    """
    Remove dados antigos do banco
    """
    try:
        deleted_count = data_manager.cleanup_old_data(days_old)
        return {
            "message": f"Limpeza concluída",
            "deleted_records": deleted_count,
            "days_old_threshold": days_old,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")


@app.get("/pages", tags=["Analytics"])
async def list_pages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Lista páginas extraídas
    """
    try:
        import sqlite3
        
        with sqlite3.connect(data_manager.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT page_id, title, url, content_length, chunks_count,
                       extraction_timestamp, description
                FROM web_pages
                ORDER BY extraction_timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            pages = []
            for row in cursor.fetchall():
                pages.append({
                    'page_id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'content_length': row[3],
                    'chunks_count': row[4],
                    'extraction_timestamp': row[5],
                    'description': row[6]
                })
            
            # Conta total
            cursor.execute('SELECT COUNT(*) FROM web_pages')
            total_pages = cursor.fetchone()[0]
            
            return {
                "total_pages": total_pages,
                "returned_pages": len(pages),
                "offset": offset,
                "limit": limit,
                "pages": pages
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar páginas: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_scraping_integration:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
