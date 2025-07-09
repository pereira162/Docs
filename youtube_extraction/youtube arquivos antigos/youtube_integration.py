"""
Integração do sistema YouTube com FastAPI
Adiciona endpoints para processamento de vídeos do YouTube
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
import logging
from pathlib import Path

from youtube_transcript_extractor import YouTubeTranscriptExtractor
from youtube_data_manager import YouTubeDataManager

logger = logging.getLogger(__name__)

# Modelos Pydantic
class YouTubeVideoRequest(BaseModel):
    """Requisição para processar vídeo do YouTube"""
    url: HttpUrl
    languages: Optional[List[str]] = ['pt', 'pt-BR', 'en']
    prefer_manual: Optional[bool] = True
    chunk_size: Optional[int] = 500

class YouTubeSearchRequest(BaseModel):
    """Requisição para busca de conteúdo"""
    query: str
    video_id: Optional[str] = None
    search_type: Optional[str] = 'all'  # all, chunks, segments, videos
    limit: Optional[int] = 50

class YouTubeVideoResponse(BaseModel):
    """Resposta do processamento de vídeo"""
    success: bool
    video_id: str
    message: str
    processing_time: Optional[float] = None
    statistics: Optional[Dict[str, Any]] = None
    files_created: Optional[Dict[str, str]] = None

# Inicializar sistemas
youtube_extractor = YouTubeTranscriptExtractor()
youtube_manager = YouTubeDataManager()

def add_youtube_routes(app: FastAPI):
    """
    Adiciona rotas do YouTube ao FastAPI app
    """
    
    @app.post("/api/youtube/process", response_model=YouTubeVideoResponse)
    async def process_youtube_video(request: YouTubeVideoRequest, background_tasks: BackgroundTasks):
        """
        Processa um vídeo do YouTube e extrai transcrição para RAG
        """
        try:
            logger.info(f"Processando vídeo do YouTube: {request.url}")
            
            # Executar processamento em background
            result = await asyncio.to_thread(
                youtube_extractor.process_video,
                str(request.url),
                request.languages,
                request.prefer_manual,
                request.chunk_size
            )
            
            if result.get('success'):
                # Salvar no gerenciador de dados em background
                background_tasks.add_task(save_to_manager, result)
                
                return YouTubeVideoResponse(
                    success=True,
                    video_id=result.get('video_id'),
                    message="Vídeo processado com sucesso",
                    statistics=result.get('statistics'),
                    files_created=result.get('saved_files')
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Erro no processamento: {result.get('error')}"
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/videos")
    async def list_youtube_videos(limit: int = 10, order_by: str = 'created_at DESC'):
        """
        Lista vídeos processados
        """
        try:
            videos = await asyncio.to_thread(youtube_manager.list_videos, limit, order_by)
            return {"videos": videos, "total": len(videos)}
        except Exception as e:
            logger.error(f"Erro ao listar vídeos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/videos/{video_id}")
    async def get_youtube_video(video_id: str):
        """
        Obtém dados completos de um vídeo específico
        """
        try:
            video_data = await asyncio.to_thread(youtube_manager.get_video_data, video_id)
            if video_data:
                return video_data
            else:
                raise HTTPException(status_code=404, detail="Vídeo não encontrado")
        except Exception as e:
            logger.error(f"Erro ao obter vídeo: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/youtube/search")
    async def search_youtube_content(request: YouTubeSearchRequest):
        """
        Busca conteúdo nos vídeos processados
        """
        try:
            results = await asyncio.to_thread(
                youtube_manager.search_content,
                request.query,
                request.search_type,
                request.limit
            )
            
            return {
                "query": request.query,
                "results": results,
                "total_found": len(results)
            }
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/statistics")
    async def get_youtube_statistics():
        """
        Obtém estatísticas dos dados do YouTube
        """
        try:
            stats = await asyncio.to_thread(youtube_manager.get_statistics)
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/export/csv")
    async def export_youtube_csv():
        """
        Exporta dados do YouTube para CSV
        """
        try:
            csv_file = await asyncio.to_thread(youtube_manager.export_to_csv)
            if csv_file and Path(csv_file).exists():
                return FileResponse(
                    csv_file,
                    media_type='text/csv',
                    filename=f"youtube_data_{Path(csv_file).stem}.csv"
                )
            else:
                raise HTTPException(status_code=500, detail="Erro ao gerar arquivo CSV")
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/export/json")
    async def export_youtube_json():
        """
        Exporta dados do YouTube para JSON
        """
        try:
            json_file = await asyncio.to_thread(youtube_manager.export_to_json)
            if json_file and Path(json_file).exists():
                return FileResponse(
                    json_file,
                    media_type='application/json',
                    filename=f"youtube_data_{Path(json_file).stem}.json"
                )
            else:
                raise HTTPException(status_code=500, detail="Erro ao gerar arquivo JSON")
        except Exception as e:
            logger.error(f"Erro ao exportar JSON: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/youtube/backup")
    async def create_youtube_backup():
        """
        Cria backup completo dos dados do YouTube
        """
        try:
            backup_file = await asyncio.to_thread(youtube_manager.create_backup)
            if backup_file:
                return {
                    "success": True,
                    "backup_file": backup_file,
                    "message": "Backup criado com sucesso"
                }
            else:
                raise HTTPException(status_code=500, detail="Erro ao criar backup")
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/transcripts/{video_id}")
    async def get_video_transcript(video_id: str):
        """
        Obtém transcrição completa de um vídeo
        """
        try:
            # Buscar arquivo de transcrição
            transcript_files = list(Path("youtube_extracted_data/transcripts").glob(f"{video_id}_*_transcript.json"))
            
            if transcript_files:
                return FileResponse(
                    transcript_files[0],
                    media_type='application/json',
                    filename=f"{video_id}_transcript.json"
                )
            else:
                raise HTTPException(status_code=404, detail="Transcrição não encontrada")
        except Exception as e:
            logger.error(f"Erro ao obter transcrição: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/youtube/chunks/{video_id}")
    async def get_video_chunks(video_id: str):
        """
        Obtém chunks RAG de um vídeo
        """
        try:
            # Buscar arquivo de chunks
            chunks_files = list(Path("youtube_extracted_data/chunks").glob(f"{video_id}_*_chunks.json"))
            
            if chunks_files:
                return FileResponse(
                    chunks_files[0],
                    media_type='application/json',
                    filename=f"{video_id}_chunks.json"
                )
            else:
                raise HTTPException(status_code=404, detail="Chunks não encontrados")
        except Exception as e:
            logger.error(f"Erro ao obter chunks: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def save_to_manager(processing_result: Dict[str, Any]):
    """
    Salva resultado do processamento no gerenciador de dados
    """
    try:
        # Preparar dados para o gerenciador
        video_data = {
            'video_id': processing_result.get('video_id'),
            'metadata': processing_result.get('metadata', {}),
            'transcript_data': processing_result.get('transcript_data', {}),
            'analysis': processing_result.get('analysis', {}),
            'chunks': processing_result.get('chunks', [])
        }
        
        # Salvar no gerenciador
        success = await asyncio.to_thread(youtube_manager.save_video_data, video_data)
        
        if success:
            logger.info(f"Dados salvos no gerenciador para vídeo {processing_result.get('video_id')}")
        else:
            logger.warning(f"Falha ao salvar dados no gerenciador para vídeo {processing_result.get('video_id')}")
            
    except Exception as e:
        logger.error(f"Erro ao salvar no gerenciador: {e}")

# Função para usar em main.py
def setup_youtube_integration(app: FastAPI):
    """
    Configura integração completa do YouTube com FastAPI
    """
    add_youtube_routes(app)
    
    # Adicionar middleware ou configurações específicas se necessário
    logger.info("Integração YouTube configurada com sucesso")
    
    return {
        'extractor': youtube_extractor,
        'manager': youtube_manager
    }
