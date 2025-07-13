#!/usr/bin/env python3
"""
 EXTRATOR RAG COMPLETO - YOUTUBE
=================================
Sistema completo para extração de vídeos do YouTube com funcionalidade RAG completa baseado no sistema antigo funcionando.
Inclui todas as funcionalidades: analysis, summary, text, transcript, database, chunks, filtro de keywords, organização avançada.
"""

import os
import sys
import json
import csv
import sqlite3
import shutil
import zipfile
import argparse
import re
import logging
import time
import subprocess
from pathlib import Path
from datetime import datetime

#  CONFIGURAÇÃO AUTOMÁTICA DO FFMPEG
def auto_configure_ffmpeg():
    """Configura FFmpeg automaticamente no PATH se não estiver disponível"""
    try:
        # Testar se FFmpeg já está disponível
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=3)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # FFmpeg não está no PATH, tentar configurar automaticamente
        ffmpeg_path = r"C:\ffmpeg"
        if os.path.exists(os.path.join(ffmpeg_path, 'ffmpeg.exe')):
            # Adicionar ao PATH da sessão atual
            current_path = os.environ.get('PATH', '')
            if ffmpeg_path not in current_path:
                os.environ['PATH'] = current_path + ';' + ffmpeg_path
                print("FFmpeg configurado automaticamente no PATH")
            
            # Testar novamente
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=3)
                return True
            except:
                return False
        return False

# Configurar FFmpeg automaticamente na inicialização
auto_configure_ffmpeg()
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from collections import Counter

# Imports para YouTube
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    print(" yt-dlp não instalado. Execute: pip install yt-dlp")
    YT_DLP_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    print(" youtube-transcript-api não instalado. Execute: pip install youtube-transcript-api")
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

# Tentar importar bibliotecas para transcrição local
try:
    import whisper
    WHISPER_AVAILABLE = True
    print("Whisper disponivel para transcricao local")
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
    print("SpeechRecognition disponivel")
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    print(" requests/beautifulsoup4 não instalados. Execute: pip install requests beautifulsoup4")
    WEB_SCRAPING_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print(" pandas não instalado. Execute: pip install pandas")
    PANDAS_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stop words para filtro de keywords
STOP_WORDS = {
    'en': {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'a', 'an', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 
        'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 
        'his', 'her', 'its', 'our', 'their', 'here', 'there', 'where', 'when', 
        'why', 'how', 'what', 'who', 'which', 'can', 'just', 'now', 'then',
        'so', 'very', 'too', 'much', 'many', 'some', 'any', 'all', 'no', 'not'
    },
    'pt': {
        'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'e', 'ou', 'mas', 'em', 
        'no', 'na', 'nos', 'nas', 'para', 'por', 'com', 'sem', 'de', 'do', 'da', 
        'dos', 'das', 'é', 'são', 'foi', 'foram', 'ser', 'estar', 'ter', 'haver',
        'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 
        'aquele', 'aquela', 'aqueles', 'aquelas', 'eu', 'tu', 'ele', 'ela', 
        'nós', 'vós', 'eles', 'elas', 'me', 'te', 'se', 'nos', 'vos', 'lhe', 
        'lhes', 'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas',
        'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas',
        'que', 'quem', 'qual', 'quais', 'onde', 'quando', 'como', 'por que',
        'porque', 'então', 'assim', 'muito', 'pouco', 'mais', 'menos', 'bem',
        'mal', 'já', 'ainda', 'sempre', 'nunca', 'aqui', 'aí', 'ali', 'lá',
        'hoje', 'ontem', 'amanhã', 'agora', 'depois', 'antes', 'sim', 'não'
    }
}

class YouTubeRAGExtractor:
    """
     Extrator RAG completo de vídeos do YouTube
    """
    
    def __init__(self, storage_dir: str = "storage", proxy: Optional[str] = None, use_tor: bool = False,
                 advanced_mode: bool = False, save_audio: bool = False, reuse_data: bool = False,
                 chunk_size: int = 500, max_chunks: int = 30, cookies_from_browser: Optional[str] = None,
                 cookies_file: Optional[str] = None):
        """
        Inicializa o extrator RAG de videos do YouTube
        
        Args:
            storage_dir: Diretório principal de armazenamento
            proxy: Proxy no formato 'http://host:port' ou 'socks5://host:port'
            use_tor: Se True, tenta usar Tor (porta 9050)
            advanced_mode: Modo avançado com mais chunks para melhor qualidade
            save_audio: Salvar arquivos de áudio permanentemente
            reuse_data: Reutilizar dados de versões anteriores
            chunk_size: Tamanho dos chunks (padrão 500, avançado 1000)
            max_chunks: Número máximo de chunks (padrão 30, avançado 100)
            cookies_from_browser: Navegador do qual extrair cookies (chrome, firefox, edge, etc.)
            cookies_file: Arquivo de cookies (.txt) para vídeos de membros
            cookies_file: Caminho para arquivo de cookies no formato Netscape
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Configurar proxy
        self.proxy = proxy
        self.use_tor = use_tor
        if use_tor and not proxy:
            self.proxy = "socks5://127.0.0.1:9050"  # Tor padrão
        
        # NOVAS CONFIGURAÇÕES v5.0
        self.advanced_mode = advanced_mode
        self.save_audio = save_audio
        self.reuse_data = reuse_data
        
        #  CONFIGURAÇÕES DE COOKIES PARA VÍDEOS RESTRITOS A MEMBROS
        self.cookies_from_browser = cookies_from_browser
        self.cookies_file = cookies_file
        self.cookies_file = cookies_file
        
        # Configurações de chunks baseadas no modo
        if advanced_mode:
            self.chunk_size = max(chunk_size, 1000)  # Modo avançado: mínimo 1000
            self.max_chunks = max(max_chunks, 200)   # Modo avançado: mínimo 200 chunks
            print(" MODO AVANÇADO ativado: Chunks maiores para melhor qualidade RAG")
        else:
            self.chunk_size = min(chunk_size, 500)   # Modo básico: máximo 500
            self.max_chunks = min(max_chunks, 30)    # Modo básico: máximo 30
            print(" MODO BÁSICO ativado: Chunks menores para processamento rápido")
        
        # Configurar estrutura de diretórios baseada no sistema antigo
        self.setup_directory_structure()
        
        print(f" YouTubeRAGExtractor v5.0 inicializado")
        print(f" Diretório de armazenamento: {self.storage_dir}")
        print(f" Tamanho dos chunks: {self.chunk_size}")
        print(f" Máximo de chunks: {self.max_chunks}")
        print(f" Salvar áudio: {'SIM' if self.save_audio else 'NÃO (temporário)'}")
        print(f" Reutilizar dados: {'SIM' if self.reuse_data else 'NÃO'}")
        if self.proxy:
            print(f" Usando proxy: {self.proxy}")
        elif self.use_tor:
            print(f"🧅 Tentando usar Tor")
    
    def setup_directory_structure(self):
        """
        Configura a estrutura de diretórios baseada no sistema antigo
        """
        # Estrutura base para dados extraídos (similar ao sistema antigo)
        self.data_dir = self.storage_dir / "youtube_extracted_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Subdiretórios especializados
        self.dirs = {
            'transcripts': self.data_dir / 'transcripts',
            'metadata': self.data_dir / 'metadata', 
            'chunks': self.data_dir / 'chunks',
            'rag_content': self.data_dir / 'rag_content',
            'database': self.data_dir / 'database'
        }
        
        # Criar todos os diretórios
        for directory in self.dirs.values():
            directory.mkdir(exist_ok=True)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrai ID do vídeo de URL do YouTube
        """
        try:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/v/([^&\n?#]+)',
                r'youtube\.com/watch\?.*v=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair ID do vídeo: {e}")
            return None
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """
        Extrai ID da playlist de URL do YouTube
        """
        try:
            patterns = [
                r'list=([^&\n?#]+)',
                r'playlist\?list=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
                    
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair ID da playlist: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Obtém metadados do vídeo usando yt-dlp com suporte a proxy
        """
        if not YT_DLP_AVAILABLE:
            return {'error': 'yt-dlp não disponível'}
        
        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            # Adicionar configuração de cookies para vídeos de membros
            if self.cookies_from_browser:
                ydl_opts['cookiesfrom_browser'] = self.cookies_from_browser
                print(f" yt-dlp usando cookies do navegador: {self.cookies_from_browser}")
            elif self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
                print(f" yt-dlp usando arquivo de cookies: {self.cookies_file}")
            
            # Adicionar configuração de proxy se disponível
            if self.proxy:
                ydl_opts['proxy'] = self.proxy
                print(f" yt-dlp usando proxy: {self.proxy}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                metadata = {
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url,
                    'extraction_date': datetime.now().isoformat(),
                    'extractor_version': '3.0.0',
                    'proxy_used': self.proxy if self.proxy else None
                }
                
                return metadata
            
        except Exception as e:
            logger.error(f"Erro ao obter metadados: {e}")
            return {
                'video_id': video_id,
                'title': f'Video_{video_id}',
                'error': str(e),
                'extraction_date': datetime.now().isoformat()
            }
    
    def get_playlist_info(self, playlist_id: str) -> Dict[str, Any]:
        """
        Obtém informações completas da playlist incluindo nome
        """
        if not YT_DLP_AVAILABLE:
            return {}
        
        try:
            url = f'https://www.youtube.com/playlist?list={playlist_id}'
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False  # Extrair metadados completos
            }
            
            # Adicionar configuração de cookies para vídeos de membros
            if self.cookies_from_browser:
                ydl_opts['cookiesfrom_browser'] = self.cookies_from_browser
                print(f" yt-dlp playlist usando cookies do navegador: {self.cookies_from_browser}")
            elif self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
                print(f" yt-dlp playlist usando arquivo de cookies: {self.cookies_file}")
            
            # Adicionar configuração de proxy se disponível
            if self.proxy:
                ydl_opts['proxy'] = self.proxy
                print(f" yt-dlp playlist usando proxy: {self.proxy}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                
                # Extrair informações da playlist
                playlist_data = {
                    'id': playlist_id,
                    'title': playlist_info.get('title', f'playlist_{playlist_id}'),
                    'uploader': playlist_info.get('uploader', 'Unknown'),
                    'description': playlist_info.get('description', ''),
                    'video_count': len(playlist_info.get('entries', [])),
                    'url': url,
                    'extraction_timestamp': datetime.now().isoformat()
                }
                
                # Extrair IDs dos vídeos
                video_ids = []
                for entry in playlist_info.get('entries', []):
                    if entry and entry.get('id'):
                        video_ids.append(entry['id'])
                
                playlist_data['video_ids'] = video_ids
                
                print(f" Playlist: '{playlist_data['title']}' ({len(video_ids)} vídeos)")
                return playlist_data
        
        except Exception as e:
            logger.error(f"Erro ao obter informações da playlist: {e}")
            # Fallback para método antigo
            return {
                'id': playlist_id,
                'title': f'playlist_{playlist_id}',
                'video_ids': self.get_playlist_videos(playlist_id)
            }

    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        Obtém lista de vídeos de uma playlist com suporte a proxy (método simplificado)
        """
        playlist_info = self.get_playlist_info(playlist_id)
        return playlist_info.get('video_ids', [])
    
    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém transcrição do vídeo com suporte a proxy/Tor
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            # Configurar proxy se disponível
            import os
            original_proxies = {}
            
            if self.proxy:
                if self.proxy.startswith('socks'):
                    # Para SOCKS, precisamos configurar diferente
                    print(f" Usando proxy SOCKS: {self.proxy}")
                    # Configurar via environment variables
                    original_proxies = {
                        'http_proxy': os.environ.get('http_proxy'),
                        'https_proxy': os.environ.get('https_proxy'),
                        'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
                        'HTTPS_PROXY': os.environ.get('HTTPS_PROXY')
                    }
                    os.environ['http_proxy'] = self.proxy
                    os.environ['https_proxy'] = self.proxy
                    os.environ['HTTP_PROXY'] = self.proxy
                    os.environ['HTTPS_PROXY'] = self.proxy
                else:
                    print(f" Usando proxy HTTP: {self.proxy}")
                    original_proxies = {
                        'http_proxy': os.environ.get('http_proxy'),
                        'https_proxy': os.environ.get('https_proxy')
                    }
                    os.environ['http_proxy'] = self.proxy
                    os.environ['https_proxy'] = self.proxy
            
            # Tentar múltiplas estratégias para contornar bloqueios
            transcript_data = None
            errors = []
            
            # Estratégia 1: Idiomas preferidos
            languages = ['pt', 'pt-BR', 'en', 'es']
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                print(" Transcrição obtida com idiomas preferidos")
            except Exception as e:
                errors.append(f"Idiomas preferidos: {str(e)}")
                
                # Estratégia 2: Apenas inglês
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                    print(" Transcrição obtida em inglês")
                except Exception as e2:
                    errors.append(f"Inglês: {str(e2)}")
                    
                    # Estratégia 3: Listar e pegar qualquer disponível
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        available_transcripts = list(transcript_list)
                        if available_transcripts:
                            transcript = available_transcripts[0]
                            transcript_data = transcript.fetch()
                            print(f" Transcrição obtida: {transcript.language}")
                        else:
                            errors.append("Nenhuma transcrição disponível")
                    except Exception as e3:
                        errors.append(f"Lista de transcrições: {str(e3)}")
            
            # Restaurar configurações de proxy
            if self.proxy:
                for key, value in original_proxies.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            
            if not transcript_data:
                print(f" Não foi possível obter transcrição após múltiplas tentativas:")
                for error in errors:
                    print(f"   - {error}")
                return None
            
            # Processar segmentos
            segments = []
            full_text = ""
            total_duration = 0
            
            for i, segment in enumerate(transcript_data):
                segment_info = {
                    'index': i,
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['duration'],
                    'end': segment['start'] + segment['duration']
                }
                segments.append(segment_info)
                full_text += segment['text'] + " "
                total_duration = max(total_duration, segment_info['end'])
            
            # Detectar idioma e tipo
            language = 'en'
            is_generated = True
            
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    language = transcript.language_code
                    is_generated = transcript.is_generated
                    break
            except:
                pass
            
            return {
                'video_id': video_id,
                'language': language,
                'is_generated': is_generated,
                'segments': segments,
                'full_text': full_text.strip(),
                'total_segments': len(segments),
                'total_duration': total_duration,
                'extraction_timestamp': datetime.now().isoformat(),
                'transcript_info': {
                    'language': language,
                    'type': 'generated' if is_generated else 'manual'
                },
                'proxy_used': self.proxy if self.proxy else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter transcrição: {e}")
            return None
    
    def create_video_folder_name(self, title: str, video_id: str) -> str:
        """
        Cria nome da pasta do vídeo (30 caracteres) - método original
        """
        try:
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.strip()
            
            if len(clean_title) > 30:
                folder_name = clean_title[:30].strip()
            else:
                folder_name = clean_title
            
            if not folder_name:
                folder_name = video_id[:11]
            
            return folder_name
            
        except:
            return video_id[:11]

    def find_existing_video_data(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados existentes de um vídeo em versões anteriores (NOVA FUNCIONALIDADE v5.0)
        """
        if not self.reuse_data:
            return None
        
        try:
            print(f" Buscando dados existentes para {video_id}...")
            
            # Buscar em todas as pastas do storage
            for folder in self.storage_dir.rglob("*"):
                if not folder.is_dir():
                    continue
                
                # Buscar arquivos de transcrição
                transcript_files = list(folder.rglob(f"*{video_id}*transcript*.json"))
                metadata_files = list(folder.rglob(f"*{video_id}*metadata*.json"))
                audio_files = list(folder.rglob(f"*{video_id}*audio*"))
                
                if transcript_files or metadata_files:
                    existing_data = {
                        'folder': str(folder),
                        'transcript_files': [str(f) for f in transcript_files],
                        'metadata_files': [str(f) for f in metadata_files],
                        'audio_files': [str(f) for f in audio_files],
                        'has_transcript': len(transcript_files) > 0,
                        'has_metadata': len(metadata_files) > 0,
                        'has_audio': len(audio_files) > 0
                    }
                    
                    print(f" Dados encontrados em: {folder.name}")
                    if existing_data['has_transcript']:
                        print(f"    Transcrições: {len(transcript_files)}")
                    if existing_data['has_metadata']:
                        print(f"    Metadados: {len(metadata_files)}")
                    if existing_data['has_audio']:
                        print(f"    Áudios: {len(audio_files)}")
                    
                    return existing_data
            
            print(f"ℹ️ Nenhum dado existente encontrado para {video_id}")
            return None
            
        except Exception as e:
            print(f" Erro ao buscar dados existentes: {e}")
            return None

    def load_existing_transcript(self, video_id: str, existing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Carrega transcrição existente de versões anteriores
        """
        try:
            if not existing_data.get('has_transcript'):
                return None
            
            transcript_files = existing_data.get('transcript_files', [])
            if not transcript_files:
                return None
            
            # Usar o arquivo mais recente
            latest_file = max(transcript_files, key=lambda x: Path(x).stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            
            # Adicionar informação de reutilização
            transcript['reused_from'] = latest_file
            transcript['reused_timestamp'] = datetime.now().isoformat()
            
            print(f" Transcrição reutilizada de: {Path(latest_file).parent.name}")
            return transcript
            
        except Exception as e:
            print(f" Erro ao carregar transcrição existente: {e}")
            return None

    def load_existing_metadata(self, video_id: str, existing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Carrega metadados existentes de versões anteriores
        """
        try:
            if not existing_data.get('has_metadata'):
                return None
            
            metadata_files = existing_data.get('metadata_files', [])
            if not metadata_files:
                return None
            
            # Usar o arquivo mais recente
            latest_file = max(metadata_files, key=lambda x: Path(x).stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Adicionar informação de reutilização
            metadata['reused_from'] = latest_file
            metadata['reused_timestamp'] = datetime.now().isoformat()
            
            print(f" Metadados reutilizados de: {Path(latest_file).parent.name}")
            return metadata
            
        except Exception as e:
            print(f" Erro ao carregar metadados existentes: {e}")
            return None

    def copy_existing_audio(self, video_id: str, existing_data: Dict[str, Any], target_folder: Path) -> bool:
        """
        Copia áudio existente de versões anteriores
        """
        try:
            if not existing_data.get('has_audio') or not self.save_audio:
                return False
            
            audio_files = existing_data.get('audio_files', [])
            if not audio_files:
                return False
            
            # Usar o arquivo mais recente
            latest_audio = max(audio_files, key=lambda x: Path(x).stat().st_mtime)
            audio_path = Path(latest_audio)
            
            if not audio_path.exists():
                return False
            
            # Copiar para pasta atual
            target_audio = target_folder / f"audio_{video_id}{audio_path.suffix}"
            import shutil
            shutil.copy2(audio_path, target_audio)
            
            print(f" Áudio reutilizado de: {audio_path.parent.name}")
            return True
            
        except Exception as e:
            print(f" Erro ao copiar áudio existente: {e}")
            return False

    def organize_existing_playlist(self, playlist_folder_name: str) -> Dict[str, Any]:
        """
        Organiza playlist existente reorganizando arquivos (NOVA FUNCIONALIDADE v5.0)
        """
        try:
            playlist_folder = self.storage_dir / playlist_folder_name
            
            if not playlist_folder.exists():
                return {'error': f'Pasta não encontrada: {playlist_folder_name}'}
            
            print(f" Organizando playlist existente: {playlist_folder_name}")
            
            # Buscar todas as pastas de vídeos
            video_folders = [f for f in playlist_folder.iterdir() if f.is_dir()]
            
            if not video_folders:
                return {'error': 'Nenhuma pasta de vídeo encontrada'}
            
            # Tentar carregar metadata da playlist
            playlist_metadata_file = playlist_folder / 'playlist_metadata.json'
            if playlist_metadata_file.exists():
                with open(playlist_metadata_file, 'r', encoding='utf-8') as f:
                    playlist_info = json.load(f)
                
                video_ids = playlist_info.get('playlist_info', {}).get('video_ids', [])
                
                print(f" Reorganizando {len(video_folders)} pastas com base em {len(video_ids)} vídeos da playlist")
                
                # Reorganizar pastas com numeração
                reorganized = 0
                for i, video_id in enumerate(video_ids, 1):
                    # Buscar pasta correspondente
                    matching_folder = None
                    for folder in video_folders:
                        if video_id in folder.name:
                            matching_folder = folder
                            break
                    
                    if matching_folder:
                        # Buscar metadados para obter título
                        metadata_files = list(matching_folder.rglob(f"*{video_id}*metadata*.json"))
                        if metadata_files:
                            try:
                                with open(metadata_files[0], 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                video_title = metadata.get('title', f'Video_{video_id}')
                                
                                # Criar novo nome numerado
                                new_name = self.create_numbered_video_folder_name(video_title, video_id, i)
                                new_path = playlist_folder / new_name
                                
                                if matching_folder.name != new_name and not new_path.exists():
                                    matching_folder.rename(new_path)
                                    print(f" Renomeado: {matching_folder.name} → {new_name}")
                                    reorganized += 1
                                
                            except Exception as e:
                                print(f" Erro ao renomear {matching_folder.name}: {e}")
                
                return {
                    'success': True,
                    'playlist_folder': playlist_folder_name,
                    'total_folders': len(video_folders),
                    'reorganized': reorganized,
                    'message': f'Reorganização concluída: {reorganized} pastas renomeadas'
                }
            
            else:
                return {'error': 'Arquivo playlist_metadata.json não encontrado'}
                
        except Exception as e:
            return {'error': f'Erro ao organizar playlist: {e}'}

    def download_audio_and_transcribe(self, video_id: str, video_folder: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Baixa áudio do vídeo e faz transcrição local - SOLUÇÃO DEFINITIVA PARA BLOQUEIO IP
        """
        import tempfile
        import os
        
        try:
            print(" Baixando áudio do vídeo...")
            
            url = f'https://www.youtube.com/watch?v={video_id}'
            
            # Criar diretório temporário para áudio
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_file = os.path.join(temp_dir, f"{video_id}.%(ext)s")
                
                # Configurar yt-dlp para baixar apenas áudio (sem pós-processamento)
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': audio_file,
                    'quiet': True,
                    'no_warnings': True
                }
                
                # Adicionar configuração de cookies para vídeos de membros
                if self.cookies_from_browser:
                    ydl_opts['cookiesfrom_browser'] = self.cookies_from_browser
                    print(f" Download de áudio usando cookies do navegador: {self.cookies_from_browser}")
                elif self.cookies_file:
                    ydl_opts['cookiefile'] = self.cookies_file
                    print(f" Download de áudio usando arquivo de cookies: {self.cookies_file}")
                
                # Configurar proxy se disponível
                if self.proxy:
                    ydl_opts['proxy'] = self.proxy
                    print(f" Download usando proxy: {self.proxy}")
                
                # Baixar áudio
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        ydl.download([url])
                        print(" Áudio baixado com sucesso")
                        
                        # Encontrar arquivo de áudio baixado
                        audio_files = [f for f in os.listdir(temp_dir) if f.startswith(video_id) and (f.endswith('.wav') or f.endswith('.webm') or f.endswith('.m4a') or f.endswith('.mp4'))]
                        
                        if not audio_files:
                            print(" Arquivo de áudio não encontrado")
                            print(f" Arquivos no diretório: {os.listdir(temp_dir)}")
                            return None
                        
                        audio_path = os.path.join(temp_dir, audio_files[0])
                        print(f" Arquivo de áudio: {audio_files[0]}")
                        print(f" Caminho completo: {audio_path}")
                        
                        # Verificar se o arquivo existe
                        if not os.path.exists(audio_path):
                            print(f" Arquivo não existe: {audio_path}")
                            return None
                        
                        # Salvar cópia do áudio na pasta do vídeo para verificação (FUNCIONALIDADE v5.0)
                        if video_folder and self.save_audio:
                            try:
                                import shutil
                                video_folder.mkdir(exist_ok=True)
                                saved_audio_path = video_folder / f"audio_{video_id}{os.path.splitext(audio_files[0])[1]}"
                                shutil.copy2(audio_path, saved_audio_path)
                                print(f" Áudio salvo permanentemente em: {saved_audio_path}")
                            except Exception as e:
                                print(f" Erro ao salvar áudio: {e}")
                        elif video_folder:
                            print(f"ℹ️ Áudio não será salvo permanentemente (use --save-audio para salvar)")
                        
                        # Converter para WAV se necessário (opcional, Whisper suporta webm)
                        if PYDUB_AVAILABLE and not audio_files[0].endswith('.wav'):
                            try:
                                audio = AudioSegment.from_file(audio_path)
                                wav_path = os.path.join(temp_dir, f"{video_id}.wav")
                                audio.export(wav_path, format='wav')
                                audio_path = wav_path
                                print(" Convertido para WAV")
                                
                                # Salvar versão WAV também se o video_folder estiver disponível (FUNCIONALIDADE v5.0)
                                if video_folder and self.save_audio:
                                    try:
                                        wav_saved_path = video_folder / f"audio_{video_id}.wav"
                                        shutil.copy2(wav_path, wav_saved_path)
                                        print(f" Áudio WAV salvo permanentemente em: {wav_saved_path}")
                                    except Exception as e:
                                        print(f" Erro ao salvar áudio WAV: {e}")
                            except Exception as e:
                                print(f" Erro na conversão para WAV: {e}")
                                print(" Usando arquivo original")
                        else:
                            print(" Usando arquivo de áudio diretamente")
                        
                        # Tentar transcrição com Whisper (melhor qualidade)
                        if WHISPER_AVAILABLE:
                            return self.transcribe_with_whisper(video_id, audio_path)
                        
                        # Fallback: SpeechRecognition
                        elif SPEECH_RECOGNITION_AVAILABLE and PYDUB_AVAILABLE:
                            return self.transcribe_with_speech_recognition(video_id, audio_path)
                        
                        else:
                            print(" Nenhuma biblioteca de transcrição disponível")
                            print("💡 Instale: pip install openai-whisper")
                            print("💡 Ou: pip install SpeechRecognition pydub")
                            return None
                    
                    except Exception as e:
                        print(f" Erro no download: {e}")
                        return None
        
        except Exception as e:
            print(f" Erro no processo de download/transcrição: {e}")
            return None
    
    def transcribe_with_whisper(self, video_id: str, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcreve áudio usando Whisper (OpenAI) - COM CONTROLE DE MEMÓRIA
        """
        try:
            print(" Transcrevendo com Whisper...")
            
            # Verificar se arquivo existe
            if not os.path.exists(audio_path):
                print(f" Arquivo não encontrado: {audio_path}")
                return None
            
            print(f" Transcrevendo arquivo: {audio_path}")
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            print(f" Tamanho do arquivo: {file_size_mb:.2f} MB")
            
            # CONTROLE DE MEMÓRIA - Evitar sobrecarga que causa desligamento
            import gc
            import torch
            
            # Limpar cache antes de começar
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Usar modelo mais leve para arquivos grandes
            model_size = "tiny" if file_size_mb > 10 else "base"
            print(f" Usando modelo Whisper: {model_size}")
            
            # Carregar modelo com configurações otimizadas
            model = whisper.load_model(model_size, device="cpu")  # Forçar CPU para estabilidade
            
            # Transcrever com detecção automática de idioma
            print(" Detectando idioma automaticamente...")
            result = model.transcribe(
                audio_path,
                language=None,  # Detecção automática de idioma
                fp16=False,     # Usar FP32 no CPU
                verbose=False,  # Menos verbose
                beam_size=1,    # Reduzir beam search para economizar memória
                best_of=1,      # Reduzir número de tentativas
                temperature=0   # Determinístico
            )
            
            detected_language = result.get('language', 'unknown')
            print(f"🌍 Idioma detectado: {detected_language}")
            
            # Limpar modelo da memória imediatamente
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print("🧹 Memória limpa após transcrição")
            
            # Processar resultado
            segments = []
            full_text = result.get('text', '')
            
            # Whisper retorna segmentos com timestamps
            for i, segment in enumerate(result.get('segments', [])):
                segment_info = {
                    'index': i,
                    'text': segment.get('text', '').strip(),
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'duration': segment.get('end', 0) - segment.get('start', 0)
                }
                segments.append(segment_info)
            
            # Se não há segmentos mas há texto, criar um segmento único
            if not segments and full_text.strip():
                segments = [{
                    'index': 0,
                    'text': full_text.strip(),
                    'start': 0,
                    'end': 180,  # Aproximar 3 minutos
                    'duration': 180
                }]
            
            print(f" Whisper: {len(segments)} segmentos transcritos")
            print(f" Texto: {full_text[:100]}..." if len(full_text) > 100 else f" Texto: {full_text}")
            
            return {
                'video_id': video_id,
                'language': detected_language,
                'is_generated': True,
                'segments': segments,
                'full_text': full_text.strip(),
                'total_segments': len(segments),
                'total_duration': segments[-1]['end'] if segments else 0,
                'extraction_timestamp': datetime.now().isoformat(),
                'transcript_info': {
                    'language': detected_language,
                    'type': 'whisper_local',
                    'model_size': model_size
                },
                'source': 'whisper_audio_download',
                'quality': 'high'
            }
        
        except Exception as e:
            print(f" Erro no Whisper: {e}")
            print(f" Tipo do erro: {type(e)}")
            import traceback
            print(f" Traceback: {traceback.format_exc()}")
            return None
    
    def transcribe_with_speech_recognition(self, video_id: str, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcreve áudio usando SpeechRecognition - FALLBACK
        """
        try:
            print("🎤 Transcrevendo com SpeechRecognition...")
            
            # Converter áudio para WAV se necessário
            audio = AudioSegment.from_file(audio_path)
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            audio.export(wav_path, format='wav')
            
            # Configurar recognizer
            recognizer = sr.Recognizer()
            
            # Dividir áudio em chunks para processamento
            chunk_duration = 30000  # 30 segundos por chunk
            chunks = []
            full_text = ""
            
            for i, chunk_start in enumerate(range(0, len(audio), chunk_duration)):
                chunk_end = min(chunk_start + chunk_duration, len(audio))
                chunk = audio[chunk_start:chunk_end]
                
                # Salvar chunk temporário
                chunk_path = f"{wav_path}_chunk_{i}.wav"
                chunk.export(chunk_path, format='wav')
                
                try:
                    # Transcrever chunk
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data, language='pt-BR')
                        
                        if text.strip():
                            chunk_info = {
                                'index': i,
                                'text': text.strip(),
                                'start': chunk_start / 1000,  # Converter para segundos
                                'end': chunk_end / 1000,
                                'duration': (chunk_end - chunk_start) / 1000
                            }
                            chunks.append(chunk_info)
                            full_text += text + " "
                
                except sr.UnknownValueError:
                    # Chunk sem fala reconhecível
                    pass
                except sr.RequestError as e:
                    print(f" Erro no Google Speech API: {e}")
                
                # Limpar chunk temporário
                try:
                    os.remove(chunk_path)
                except:
                    pass
            
            # Limpar arquivo WAV temporário
            try:
                os.remove(wav_path)
            except:
                pass
            
            if chunks:
                print(f" SpeechRecognition: {len(chunks)} chunks transcritos")
                
                return {
                    'video_id': video_id,
                    'language': 'pt-BR',
                    'is_generated': True,
                    'segments': chunks,
                    'full_text': full_text.strip(),
                    'total_segments': len(chunks),
                    'total_duration': chunks[-1]['end'] if chunks else 0,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'transcript_info': {
                        'language': 'pt-BR',
                        'type': 'speech_recognition_local'
                    },
                    'source': 'speech_recognition_audio_download',
                    'quality': 'medium'
                }
            else:
                print(" Nenhum texto reconhecido")
                return None
        
        except Exception as e:
            print(f" Erro no SpeechRecognition: {e}")
            return None

    def get_transcript_with_fallbacks(self, video_id: str, video_folder: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Tenta múltiplas estratégias para obter transcrição - INCLUINDO DOWNLOAD LOCAL
        """
        try:
            # Estratégia 1: youtube-transcript-api direto
            print(" Tentando: youtube-transcript-api direto...")
            transcript = self.get_transcript(video_id)
            if transcript and transcript.get('segments'):
                print(" Sucesso com youtube-transcript-api direto")
                transcript['source'] = 'youtube_transcript_api_direct'
                return transcript
            
            print(" Falhou: youtube-transcript-api direto")
            
            # Estratégia 2: youtube-transcript-api com proxy
            if self.proxy:
                print(" Tentando: youtube-transcript-api com proxy...")
                transcript = self.get_transcript(video_id)
                if transcript and transcript.get('segments'):
                    print(" Sucesso com youtube-transcript-api + proxy")
                    transcript['source'] = 'youtube_transcript_api_proxy'
                    return transcript
                
                print(" Falhou: youtube-transcript-api com proxy")
            
            # Estratégia 3: yt-dlp subtitles
            print(" Tentando: yt-dlp subtitles...")
            transcript = self.extract_subtitles_with_ydl(video_id)
            if transcript and transcript.get('segments'):
                print(" Sucesso com yt-dlp subtitles")
                transcript['source'] = 'ytdlp_subtitles'
                return transcript
            
            print(" Falhou: yt-dlp subtitles")
            
            # Estratégia 4: DOWNLOAD DE ÁUDIO + TRANSCRIÇÃO LOCAL (SOLUÇÃO DEFINITIVA)
            print(" Tentando: Download de áudio + transcrição local...")
            transcript = self.download_audio_and_transcribe(video_id, video_folder)
            if transcript and transcript.get('segments'):
                print(" Sucesso com download de áudio + transcrição local")
                return transcript
            
            print(" Falhou: Download de áudio + transcrição local")
            
            print(" Todas as estratégias falharam para:", video_id)
            return None
        
        except Exception as e:
            print(f" Erro em get_transcript_with_fallbacks: {e}")
            return None
    
    def extract_subtitles_with_ydl(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Extrai legendas usando yt-dlp como fallback
        """
        import tempfile
        import os
        
        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            
            # Criar diretório temporário
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = os.path.join(temp_dir, f"{video_id}.%(ext)s")
                
                ydl_opts = {
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'skip_download': True,
                    'outtmpl': output_template,
                    'quiet': True,
                    'no_warnings': True,
                    'subtitleslangs': ['pt', 'pt-BR', 'en'],
                    'subtitlesformat': 'vtt'
                }
                
                # Adicionar configuração de cookies para vídeos de membros
                if self.cookies_from_browser:
                    ydl_opts['cookiesfrom_browser'] = self.cookies_from_browser
                    print(f" Transcrição usando cookies do navegador: {self.cookies_from_browser}")
                elif self.cookies_file:
                    ydl_opts['cookiefile'] = self.cookies_file
                    print(f" Transcrição usando arquivo de cookies: {self.cookies_file}")
                
                if self.proxy:
                    ydl_opts['proxy'] = self.proxy
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        # Extrair informações e baixar legendas
                        info = ydl.extract_info(url, download=False)
                        
                        # Verificar quais legendas estão disponíveis
                        subtitles = info.get('subtitles', {})
                        automatic_captions = info.get('automatic_captions', {})
                        
                        all_subs = {**subtitles, **automatic_captions}
                        
                        # Tentar baixar legendas na ordem de preferência
                        for lang in ['pt', 'pt-BR', 'en']:
                            if lang in all_subs:
                                print(f"🔽 Baixando legenda em {lang}...")
                                
                                # Baixar só essa legenda específica
                                ydl_opts_specific = ydl_opts.copy()
                                ydl_opts_specific['subtitleslangs'] = [lang]
                                
                                with yt_dlp.YoutubeDL(ydl_opts_specific) as ydl_specific:
                                    ydl_specific.download([url])
                                
                                # Procurar arquivo de legenda baixado
                                vtt_file = os.path.join(temp_dir, f"{video_id}.{lang}.vtt")
                                if os.path.exists(vtt_file):
                                    with open(vtt_file, 'r', encoding='utf-8') as f:
                                        vtt_content = f.read()
                                    
                                    return self.parse_vtt_content(video_id, vtt_content, lang)
                        
                        # Se não conseguiu com idiomas específicos, tentar qualquer um
                        for lang_code in all_subs.keys():
                            print(f"🔽 Tentando baixar legenda em {lang_code}...")
                            
                            ydl_opts_any = ydl_opts.copy()
                            ydl_opts_any['subtitleslangs'] = [lang_code]
                            
                            with yt_dlp.YoutubeDL(ydl_opts_any) as ydl_any:
                                try:
                                    ydl_any.download([url])
                                    
                                    vtt_file = os.path.join(temp_dir, f"{video_id}.{lang_code}.vtt")
                                    if os.path.exists(vtt_file):
                                        with open(vtt_file, 'r', encoding='utf-8') as f:
                                            vtt_content = f.read()
                                        
                                        return self.parse_vtt_content(video_id, vtt_content, lang_code)
                                except:
                                    continue
                    
                    except Exception as e:
                        print(f"Erro ao extrair com yt-dlp: {e}")
        
        except Exception as e:
            print(f"Erro no método yt-dlp: {e}")
        
        return None
    
    def parse_vtt_content(self, video_id: str, vtt_content: str, language: str) -> Dict[str, Any]:
        """
        Parseia conteúdo VTT e retorna estrutura de transcrição
        """
        try:
            segments = []
            full_text = ""
            lines = vtt_content.split('\n')
            
            current_segment = None
            segment_index = 0
            
            for line in lines:
                line = line.strip()
                
                # Pular linhas vazias e cabeçalhos
                if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                    continue
                
                # Linha de tempo: 00:00:01.000 --> 00:00:05.000
                if '-->' in line:
                    try:
                        times = line.split('-->')
                        start_time = self.parse_vtt_time(times[0].strip())
                        end_time = self.parse_vtt_time(times[1].strip())
                        
                        current_segment = {
                            'index': segment_index,
                            'start': start_time,
                            'end': end_time,
                            'duration': end_time - start_time,
                            'text': ''
                        }
                    except:
                        continue
                
                # Texto da legenda
                elif line and current_segment is not None:
                    # Remover tags HTML e formatação
                    clean_text = re.sub(r'<[^>]+>', '', line)
                    clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    clean_text = clean_text.strip()
                    
                    if clean_text:
                        if current_segment['text']:
                            current_segment['text'] += ' ' + clean_text
                        else:
                            current_segment['text'] = clean_text
                
                # Linha vazia indica fim do segmento
                elif not line and current_segment is not None and current_segment['text']:
                    segments.append(current_segment)
                    full_text += current_segment['text'] + ' '
                    segment_index += 1
                    current_segment = None
            
            # Adicionar último segmento se necessário
            if current_segment is not None and current_segment['text']:
                segments.append(current_segment)
                full_text += current_segment['text'] + ' '
            
            if segments:
                print(f" Extraídos {len(segments)} segmentos via yt-dlp")
                
                return {
                    'video_id': video_id,
                    'language': language,
                    'is_generated': True,
                    'segments': segments,
                    'full_text': full_text.strip(),
                    'total_segments': len(segments),
                    'total_duration': segments[-1]['end'] if segments else 0,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'transcript_info': {
                        'language': language,
                        'type': 'ydl_extracted'
                    },
                    'source': 'yt-dlp_subtitles'
                }
        
        except Exception as e:
            print(f"Erro ao parsear VTT: {e}")
        
        return None
    
    def parse_vtt_time(self, time_str: str) -> float:
        """
        Converte timestamp VTT para segundos
        """
        try:
            # Remove espaços e normaliza
            time_str = time_str.strip().replace(',', '.')
            
            # Formato: HH:MM:SS.mmm ou MM:SS.mmm
            parts = time_str.split(':')
            
            if len(parts) == 3:  # HH:MM:SS.mmm
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS.mmm
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(parts[0])
        except:
            return 0.0
        """
        Obtém transcrição do vídeo com suporte a proxy/Tor
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            # Configurar proxy se disponível
            import os
            original_proxies = {}
            
            if self.proxy:
                if self.proxy.startswith('socks'):
                    # Para SOCKS, precisamos configurar diferente
                    print(f" Usando proxy SOCKS: {self.proxy}")
                    # Configurar via environment variables
                    original_proxies = {
                        'http_proxy': os.environ.get('http_proxy'),
                        'https_proxy': os.environ.get('https_proxy'),
                        'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
                        'HTTPS_PROXY': os.environ.get('HTTPS_PROXY')
                    }
                    os.environ['http_proxy'] = self.proxy
                    os.environ['https_proxy'] = self.proxy
                    os.environ['HTTP_PROXY'] = self.proxy
                    os.environ['HTTPS_PROXY'] = self.proxy
                else:
                    print(f" Usando proxy HTTP: {self.proxy}")
                    original_proxies = {
                        'http_proxy': os.environ.get('http_proxy'),
                        'https_proxy': os.environ.get('https_proxy')
                    }
                    os.environ['http_proxy'] = self.proxy
                    os.environ['https_proxy'] = self.proxy
            
            # Tentar múltiplas estratégias para contornar bloqueios
            transcript_data = None
            errors = []
            
            # Estratégia 1: Idiomas preferidos
            languages = ['pt', 'pt-BR', 'en', 'es']
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                print(" Transcrição obtida com idiomas preferidos")
            except Exception as e:
                errors.append(f"Idiomas preferidos: {str(e)}")
                
                # Estratégia 2: Apenas inglês
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                    print(" Transcrição obtida em inglês")
                except Exception as e2:
                    errors.append(f"Inglês: {str(e2)}")
                    
                    # Estratégia 3: Listar e pegar qualquer disponível
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        available_transcripts = list(transcript_list)
                        if available_transcripts:
                            transcript = available_transcripts[0]
                            transcript_data = transcript.fetch()
                            print(f" Transcrição obtida: {transcript.language}")
                        else:
                            errors.append("Nenhuma transcrição disponível")
                    except Exception as e3:
                        errors.append(f"Lista de transcrições: {str(e3)}")
            
            # Restaurar configurações de proxy
            if self.proxy:
                for key, value in original_proxies.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            
            if not transcript_data:
                print(f" Não foi possível obter transcrição após múltiplas tentativas:")
                for error in errors:
                    print(f"   - {error}")
                return None
            
            # Processar segmentos
            segments = []
            full_text = ""
            total_duration = 0
            
            for i, segment in enumerate(transcript_data):
                segment_info = {
                    'index': i,
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['duration'],
                    'end': segment['start'] + segment['duration']
                }
                segments.append(segment_info)
                full_text += segment['text'] + " "
                total_duration = max(total_duration, segment_info['end'])
            
            # Detectar idioma e tipo
            language = 'en'
            is_generated = True
            
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    language = transcript.language_code
                    is_generated = transcript.is_generated
                    break
            except:
                pass
            
            return {
                'video_id': video_id,
                'language': language,
                'is_generated': is_generated,
                'segments': segments,
                'full_text': full_text.strip(),
                'total_segments': len(segments),
                'total_duration': total_duration,
                'extraction_timestamp': datetime.now().isoformat(),
                'transcript_info': {
                    'language': language,
                    'type': 'generated' if is_generated else 'manual'
                },
                'proxy_used': self.proxy if self.proxy else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter transcrição: {e}")
            return None
    
    def filter_keywords(self, words: List[str], language: str = 'en') -> List[str]:
        """
        Filtra palavras removendo conectivos e palavras de baixo significado
        """
        stop_words = STOP_WORDS.get(language, STOP_WORDS['en'])
        
        filtered_words = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if (len(clean_word) >= 3 and 
                clean_word not in stop_words and
                not clean_word.isdigit()):
                filtered_words.append(clean_word)
        
        return filtered_words
    
    def extract_text_from_segments(self, segments: List[Dict]) -> str:
        """
        Extrai texto simples dos segmentos de transcrição
        """
        if not segments:
            return ""
        
        text_parts = []
        for segment in segments:
            if isinstance(segment, dict):
                text = segment.get('text', '') or segment.get('content', '')
            else:
                text = str(segment)
            
            if text.strip():
                text_parts.append(text.strip())
        
        return "\n".join(text_parts)
    
    def create_chunks(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Cria chunks do texto para RAG com configurações personalizáveis
        """
        import gc
        
        # Usar configurações da instância se não especificadas
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = min(100, chunk_size // 5)  # 20% do tamanho do chunk
        
        max_chunks = self.max_chunks
        
        # Verificar memória disponível
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 85 and not self.advanced_mode:
                print(" Memória alta detectada, reduzindo tamanho dos chunks")
                chunk_size = min(chunk_size, 300)
                overlap = 50
                max_chunks = min(max_chunks, 20)
        except ImportError:
            pass  # Se psutil não estiver disponível, usar valores padrão
        except:
            pass  # Se psutil falhar, continuar com valores padrão
        
        chunks = []
        start = 0
        chunk_index = 0
        
        # Limitar texto se muito grande (exceto no modo avançado)
        text_limit = 50000 if self.advanced_mode else 30000
        if len(text) > text_limit:
            if not self.advanced_mode:
                print(f" Texto muito grande ({len(text)} chars), truncando para {text_limit} chars")
                text = text[:text_limit]
            else:
                print(f" Modo avançado: processando texto completo ({len(text)} chars)")
        
        print(f"🔗 Criando chunks: tamanho={chunk_size}, sobreposição={overlap}, máximo={max_chunks}")
        
        try:
            while start < len(text) and chunk_index < max_chunks:
                end = start + chunk_size
                
                if end < len(text):
                    sentence_breaks = ['. ', '! ', '? ', '\n\n']
                    best_break = end
                    
                    for break_char in sentence_breaks:
                        break_pos = text.rfind(break_char, start, end + 100)
                        if break_pos > start:
                            best_break = break_pos + len(break_char)
                            break
                    
                    end = best_break
                
                chunk_text = text[start:end].strip()
                
                if chunk_text:
                    chunk = {
                        'index': chunk_index,
                        'text': chunk_text,
                        'start_char': start,
                        'end_char': end,
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split()),
                        'metadata': {
                            'chunk_size': chunk_size,
                            'overlap': overlap,
                            'mode': 'advanced' if self.advanced_mode else 'basic'
                        }
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Calcular próximo início com proteção contra loop infinito
                next_start = end - overlap
                
                # Proteção contra loop infinito
                if next_start <= start:
                    next_start = start + 1
                
                # Se chegamos ao final do texto, parar
                if next_start >= len(text):
                    break
                    
                start = next_start
                
                # Limpeza de memória a cada 10 chunks (5 no modo básico)
                cleanup_interval = 10 if self.advanced_mode else 5
                if chunk_index % cleanup_interval == 0:
                    gc.collect()
                    try:
                        import psutil
                        memory = psutil.virtual_memory()
                        memory_limit = 95 if self.advanced_mode else 90
                        if memory.percent > memory_limit:
                            print(f" Memória crítica ({memory.percent}%), parando criação de chunks (limite: {memory_limit}%)")
                            break
                    except ImportError:
                        pass  # psutil não disponível
                    except:
                        pass
            
            mode_str = "avançado" if self.advanced_mode else "básico"
            print(f" Chunks criados: {len(chunks)} (modo {mode_str}, máximo permitido: {max_chunks})")
            return chunks
            
        except Exception as e:
            print(f" Erro na criação de chunks: {e}")
            gc.collect()
            return []
    
    def analyze_content(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise leve do conteúdo para RAG com controle de memória
        """
        try:
            import gc
            
            full_text = transcript_data.get('full_text', '')
            segments = transcript_data.get('segments', [])
            
            if not full_text:
                return {}
            
            # Limitar tamanho do texto para análise
            if len(full_text) > 20000:  # 20KB limite
                print(" Texto muito grande para análise, truncando...")
                full_text = full_text[:20000]
            
            # Análise básica e leve
            words = full_text.split()[:1000]  # Limitar palavras analisadas
            sentences = [s for s in full_text.split('.')[:50] if s.strip()]  # Limitar sentenças
            
            # Keywords filtradas (limitado)
            word_freq = Counter(words)
            most_common_words = [word for word, count in word_freq.most_common(20)]  # Reduzido de 50 para 20
            language = transcript_data.get('language', 'en')
            filtered_keywords = self.filter_keywords(most_common_words, language)
            
            # Análise simplificada
            analysis = {
                'summary': {
                    'total_words': len(words),
                    'total_sentences': len(sentences),
                    'avg_words_per_sentence': len(words) / max(len(sentences), 1),
                    'language': language
                },
                'keywords': filtered_keywords[:15],  # Limitado a 15 keywords
                'metadata': {
                    'analysis_version': '2.0_light',
                    'timestamp': datetime.now().isoformat(),
                    'processing_mode': 'memory_optimized'
                }
            }
            
            # Limpeza imediata
            words = None
            sentences = None
            word_freq = None
            most_common_words = None
            filtered_keywords = None
            gc.collect()
            
            return analysis
            
        except Exception as e:
            print(f" Erro na análise: {e}")
            import gc
            gc.collect()
            return {
                'error': str(e),
                'metadata': {
                    'analysis_version': '2.0_light',
                    'timestamp': datetime.now().isoformat(),
                    'processing_mode': 'error_fallback'
                }
            }
            
            # Análise de legibilidade
            readability_score = 0
            if sentences:
                avg_words_per_sentence = len(words) / len(sentences)
                readability_score = max(0, min(100, 206.835 - (1.015 * avg_words_per_sentence)))
            
            # Identificação de tópicos
            topics = []
            tech_keywords = ['technology', 'software', 'computer', 'digital', 'app', 'web', 'api', 'code', 'programming',
                           'tecnologia', 'software', 'computador', 'digital', 'aplicativo', 'código', 'programação']
            if any(keyword.lower() in full_text.lower() for keyword in tech_keywords):
                topics.append('tecnologia')
            
            # Análise de sentimento
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect',
                            'bom', 'ótimo', 'excelente', 'fantástico', 'maravilhoso']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'problem',
                            'ruim', 'péssimo', 'terrível', 'horrível', 'pior', 'ódio', 'problema']
            
            positive_count = sum(1 for word in positive_words if word.lower() in full_text.lower())
            negative_count = sum(1 for word in negative_words if word.lower() in full_text.lower())
            
            if positive_count > negative_count:
                sentiment = 'positive'
            elif negative_count > positive_count:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'statistics': {
                    'total_characters': len(full_text),
                    'total_words': len(words),
                    'total_sentences': len(sentences),
                    'average_words_per_segment': len(words) / len(segments) if segments else 0,
                    'total_duration_minutes': transcript_data.get('total_duration', 0) / 60
                },
                'content_analysis': {
                    'language_detected': language,
                    'transcript_type': transcript_data.get('transcript_info', {}).get('type', 'unknown'),
                    'readability_score': readability_score
                },
                'keywords': filtered_keywords[:10],
                'topics': topics,
                'sentiment': sentiment
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de conteúdo: {e}")
            return {'error': str(e)}
    
    def create_database(self) -> str:
        """
        Cria banco SQLite com estrutura baseada no sistema antigo
        """
        try:
            db_path = self.dirs['database'] / "youtube_transcripts.db"
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Tabela de metadados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_metadata (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    uploader TEXT,
                    upload_date TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    like_count INTEGER,
                    extraction_date TEXT,
                    extractor_version TEXT
                )
            ''')
            
            # Tabela de segmentos de transcrição
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    segment_index INTEGER,
                    text TEXT,
                    start_time REAL,
                    duration REAL,
                    end_time REAL,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            # Tabela de chunks para RAG
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    start_char INTEGER,
                    end_char INTEGER,
                    char_count INTEGER,
                    word_count INTEGER,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            # Tabela de análises
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_analysis (
                    video_id TEXT PRIMARY KEY,
                    language_detected TEXT,
                    transcript_type TEXT,
                    total_characters INTEGER,
                    total_words INTEGER,
                    total_segments INTEGER,
                    keywords TEXT,
                    topics TEXT,
                    sentiment TEXT,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            return str(db_path)
            
        except Exception as e:
            logger.error(f"Erro ao criar banco de dados: {e}")
            return ""
    
    def save_to_database(self, db_path: str, video_id: str, metadata: Dict, transcript: Optional[Dict], 
                        chunks: List[Dict], analysis: Dict) -> bool:
        """
        Salva dados no banco SQLite
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Inserir metadados
            cursor.execute('''
                INSERT OR REPLACE INTO video_metadata 
                (video_id, title, description, uploader, upload_date, duration, view_count, like_count, extraction_date, extractor_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                metadata.get('title', ''),
                metadata.get('description', ''),
                metadata.get('uploader', ''),
                metadata.get('upload_date', ''),
                metadata.get('duration', 0),
                metadata.get('view_count', 0),
                metadata.get('like_count', 0),
                metadata.get('extraction_date', ''),
                metadata.get('extractor_version', '3.0.0')
            ))
            
            # Inserir segmentos de transcrição
            if transcript and transcript.get('segments'):
                for segment in transcript['segments']:
                    cursor.execute('''
                        INSERT INTO transcript_segments 
                        (video_id, segment_index, text, start_time, duration, end_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        video_id,
                        segment.get('index', 0),
                        segment.get('text', ''),
                        segment.get('start', 0),
                        segment.get('duration', 0),
                        segment.get('end', 0)
                    ))
            
            # Inserir chunks
            for chunk in chunks:
                cursor.execute('''
                    INSERT INTO content_chunks 
                    (video_id, chunk_index, text, start_char, end_char, char_count, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_id,
                    chunk.get('index', 0),
                    chunk.get('text', ''),
                    chunk.get('start_char', 0),
                    chunk.get('end_char', 0),
                    chunk.get('char_count', 0),
                    chunk.get('word_count', 0)
                ))
            
            # Inserir análise
            if analysis:
                cursor.execute('''
                    INSERT OR REPLACE INTO content_analysis 
                    (video_id, language_detected, transcript_type, total_characters, total_words, total_segments, keywords, topics, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_id,
                    analysis.get('content_analysis', {}).get('language_detected', ''),
                    analysis.get('content_analysis', {}).get('transcript_type', ''),
                    analysis.get('statistics', {}).get('total_characters', 0),
                    analysis.get('statistics', {}).get('total_words', 0),
                    analysis.get('statistics', {}).get('total_segments', 0),
                    json.dumps(analysis.get('keywords', [])),
                    json.dumps(analysis.get('topics', [])),
                    analysis.get('sentiment', 'neutral')
                ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
            return False
    
    def create_numbered_video_folder_name(self, title: str, video_id: str, video_index: int) -> str:
        """
        Cria nome da pasta do vídeo com numeração para playlists (NOVA FUNCIONALIDADE v5.0)
        Formato: [1] Nome_do_Video (30 caracteres)
        """
        try:
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.strip()
            
            # Formato: [N] Título
            prefix = f"[{video_index}] "
            available_chars = 30 - len(prefix)
            
            if len(clean_title) > available_chars:
                folder_name = prefix + clean_title[:available_chars].strip()
            else:
                folder_name = prefix + clean_title
            
            if len(folder_name.replace(prefix, "").strip()) == 0:
                folder_name = f"[{video_index}] {video_id[:11]}"
            
            return folder_name
            
        except:
            return f"[{video_index}] {video_id[:11]}"
    
    def get_next_version_folder(self, base_folder_name: str, parent_dir: Path) -> str:
        """
        Obtém próxima versão da pasta (controle de versão)
        """
        version = 1
        folder_name = base_folder_name
        
        while (parent_dir / folder_name).exists():
            version += 1
            folder_name = f"{base_folder_name}_v{version}"
        
        return folder_name
    
    def create_playlist_folder_name(self, playlist_title: str, playlist_id: str) -> str:
        """
        Cria nome da pasta da playlist baseado no título real
        """
        try:
            # Limpar caracteres especiais
            clean_title = re.sub(r'[<>:"/\\|?*]', '', playlist_title)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            
            # Limitar a 50 caracteres para playlists (mais espaço que vídeos individuais)
            if len(clean_title) > 50:
                folder_name = clean_title[:50].strip()
            else:
                folder_name = clean_title
            
            # Fallback se não há título válido
            if not folder_name:
                folder_name = f"playlist_{playlist_id}"
            
            return folder_name
            
        except:
            return f"playlist_{playlist_id}"
    
    def get_versioned_playlist_folder(self, base_name: str, storage_dir: Path) -> str:
        """
        Cria pasta da playlist com versionamento se já existir
        """
        base_path = storage_dir / base_name
        
        if not base_path.exists():
            return base_name
        
        # Se existe, criar versão numerada
        version = 1
        while True:
            versioned_name = f"{base_name}_v{version}"
            versioned_path = storage_dir / versioned_name
            
            if not versioned_path.exists():
                print(f" Pasta da playlist já existe, criando: {versioned_name}")
                return versioned_name
            
            version += 1
            
            # Segurança
            if version > 100:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{base_name}_{timestamp}"
    
    def download_thumbnail(self, video_id: str, thumbnail_url: str, output_dir: Path) -> Optional[str]:
        """
        Baixa thumbnail do vídeo
        """
        if not WEB_SCRAPING_AVAILABLE or not thumbnail_url:
            return None
        
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            
            thumbnail_path = output_dir / f"{video_id}_thumbnail.jpg"
            
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.warning(f"Não foi possível baixar thumbnail: {e}")
            return None
    
    def extract_single_video(self, url_or_id: str, custom_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrai dados RAG completos de um único vídeo v5.0 com reutilização de dados
        """
        try:
            print(f"\n Processando vídeo: {url_or_id}")
            
            # Extrair ID do vídeo
            video_id = self.extract_video_id(url_or_id)
            if not video_id:
                return {'error': 'ID do vídeo inválido', 'input': url_or_id}
            
            print(f"📹 ID do vídeo: {video_id}")
            
            # NOVA FUNCIONALIDADE v5.0: Buscar dados existentes
            existing_data = self.find_existing_video_data(video_id) if self.reuse_data else None
            reused_transcript = False
            reused_metadata = False
            reused_audio = False
            
            # Timestamp para arquivos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Obter metadados (reutilizar se disponível)
            print(" Obtendo metadados...")
            if existing_data:
                metadata = self.load_existing_metadata(video_id, existing_data)
                if metadata:
                    reused_metadata = True
                    print(" Metadados reutilizados de versão anterior")
                else:
                    metadata = self.get_video_metadata(video_id)
            else:
                metadata = self.get_video_metadata(video_id)
            
            if 'error' in metadata:
                return {'error': f"Erro ao obter metadados: {metadata['error']}", 'video_id': video_id}
            
            # Criar nome da pasta do vídeo (30 caracteres baseado no título)
            video_title = metadata.get('title', f'Video_{video_id}')
            folder_name = self.create_video_folder_name(video_title, video_id)
            
            # Determinar pasta de trabalho
            if custom_folder:
                work_dir = self.storage_dir / custom_folder / folder_name
            else:
                work_dir = self.storage_dir / folder_name
            
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Tentar copiar áudio existente se necessário
            if existing_data and self.save_audio:
                reused_audio = self.copy_existing_audio(video_id, existing_data, work_dir)
            
            # Criar estrutura de dados dentro da pasta do vídeo
            data_dir = work_dir / "youtube_extracted_data"
            data_dir.mkdir(exist_ok=True)
            
            dirs = {
                'transcripts': data_dir / 'transcripts',
                'metadata': data_dir / 'metadata',
                'chunks': data_dir / 'chunks', 
                'rag_content': data_dir / 'rag_content',
                'database': data_dir / 'database'
            }
            
            for directory in dirs.values():
                directory.mkdir(exist_ok=True)
            
            print(f" Pasta do vídeo: {folder_name}")
            if self.reuse_data:
                print(f" Modo reutilização ativado")
            
            # Salvar metadados
            metadata_file = dirs['metadata'] / f"{video_id}_{timestamp}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Obter transcrição (reutilizar se disponível)
            print(" Extraindo transcrição...")
            if existing_data:
                transcript = self.load_existing_transcript(video_id, existing_data)
                if transcript:
                    reused_transcript = True
                    print(" Transcrição reutilizada de versão anterior")
                else:
                    transcript = self.get_transcript_with_fallbacks(video_id, work_dir)
            else:
                transcript = self.get_transcript_with_fallbacks(video_id, work_dir)
            
            # Inicializar estrutura de arquivos
            files_created = {
                'transcript_json': None,
                'metadata': str(metadata_file),
                'chunks': None,
                'analysis': None,
                'text': None,
                'chunks_csv': None,
                'database': None,
                'thumbnail': None
            }
            
            statistics = {
                'total_segments': 0,
                'total_chunks': 0,
                'text_length': 0,
                'duration_minutes': metadata.get('duration', 0) / 60
            }
            
            chunks = []
            analysis = {}
            
            if transcript:
                print(f" Transcrição encontrada: {len(transcript['segments'])} segmentos")
                
                # Salvar transcrição JSON
                transcript_file = dirs['transcripts'] / f"{video_id}_{timestamp}_transcript.json"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
                files_created['transcript_json'] = str(transcript_file)
                
                # Extrair texto completo
                full_text = transcript['full_text']
                
                # Salvar texto puro
                text_file = dirs['rag_content'] / f"{video_id}_{timestamp}_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                files_created['text'] = str(text_file)
                
                # Criar chunks com configurações personalizadas
                print("🔗 Criando chunks para RAG...")
                chunks = self.create_chunks(full_text)
                
                # Salvar chunks JSON
                chunks_file = dirs['chunks'] / f"{video_id}_{timestamp}_chunks.json"
                with open(chunks_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)
                files_created['chunks'] = str(chunks_file)
                
                # Salvar chunks CSV
                if PANDAS_AVAILABLE and chunks:
                    chunks_csv = dirs['chunks'] / f"{video_id}_{timestamp}_chunks.csv"
                    chunks_df = pd.DataFrame(chunks)
                    chunks_df.to_csv(chunks_csv, index=False, encoding='utf-8')
                    files_created['chunks_csv'] = str(chunks_csv)
                
                # Análise RAG completa
                print(" Realizando análise RAG...")
                analysis = self.analyze_content(transcript)
                
                # Salvar análise
                analysis_file = dirs['rag_content'] / f"{video_id}_{timestamp}_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)
                files_created['analysis'] = str(analysis_file)
                
                # Atualizar estatísticas
                statistics.update({
                    'total_segments': len(transcript['segments']),
                    'total_chunks': len(chunks),
                    'text_length': len(full_text)
                })
                
                mode_info = "avançado" if self.advanced_mode else "básico"
                print(f" Dados extraídos (modo {mode_info}): {len(transcript['segments'])} segmentos, {len(chunks)} chunks, {len(full_text)} caracteres")
            else:
                print(" Transcrição não disponível")
                # Criar análise mínima mesmo sem transcrição
                analysis = {
                    'statistics': {
                        'total_characters': 0,
                        'total_words': 0,
                        'total_segments': 0,
                        'duration_minutes': metadata.get('duration', 0) / 60
                    },
                    'content_analysis': {
                        'language_detected': 'unknown',
                        'transcript_type': 'unavailable'
                    },
                    'keywords': [],
                    'topics': [],
                    'sentiment': 'neutral'
                }
                
                analysis_file = dirs['rag_content'] / f"{video_id}_{timestamp}_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)
                files_created['analysis'] = str(analysis_file)
            
            # Criar banco de dados
            print(" Criando banco de dados...")
            db_path = dirs['database'] / "youtube_transcripts.db"
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Criar estrutura completa do banco
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_metadata (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    uploader TEXT,
                    upload_date TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    like_count INTEGER,
                    extraction_date TEXT,
                    extractor_version TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    segment_index INTEGER,
                    text TEXT,
                    start_time REAL,
                    duration REAL,
                    end_time REAL,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    start_char INTEGER,
                    end_char INTEGER,
                    char_count INTEGER,
                    word_count INTEGER,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_analysis (
                    video_id TEXT PRIMARY KEY,
                    language_detected TEXT,
                    transcript_type TEXT,
                    total_characters INTEGER,
                    total_words INTEGER,
                    total_segments INTEGER,
                    keywords TEXT,
                    topics TEXT,
                    sentiment TEXT,
                    FOREIGN KEY (video_id) REFERENCES video_metadata (video_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Salvar dados no banco
            self.save_to_database(str(db_path), video_id, metadata, transcript, chunks, analysis)
            files_created['database'] = str(db_path)
            
            # Baixar thumbnail
            print("🖼️ Baixando thumbnail...")
            thumbnail_path = self.download_thumbnail(
                video_id, 
                metadata.get('thumbnail', ''), 
                dirs['rag_content']
            )
            if thumbnail_path:
                files_created['thumbnail'] = thumbnail_path
            
            # Criar resumo RAG completo com informações de reutilização
            rag_summary = {
                'video_id': video_id,
                'video_title': video_title,
                'folder_name': folder_name,
                'extraction_date': timestamp,
                'files_created': files_created,
                'statistics': statistics,
                'metadata': metadata,
                'analysis_summary': analysis,
                'extractor_version': '5.0',  # NOVA FUNCIONALIDADE v5.0
                'features_used': {
                    'advanced_mode': self.advanced_mode,
                    'save_audio': self.save_audio,
                    'reuse_data': self.reuse_data
                },
                'reused_data': {  # NOVA FUNCIONALIDADE v5.0
                    'transcript': reused_transcript,
                    'metadata': reused_metadata,
                    'audio': reused_audio
                }
            }
            
            # Salvar resumo
            summary_file = dirs['rag_content'] / f"{video_id}_{timestamp}_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(rag_summary, f, ensure_ascii=False, indent=2)
            
            print(f" Vídeo processado: '{video_title[:50]}...'")
            print(f" Pasta: {folder_name}")
            print(f" Duração: {metadata.get('duration', 0) / 60:.1f} minutos")
            if transcript:
                print(f" Segmentos: {len(transcript['segments'])}")
                print(f"🔗 Chunks: {len(chunks)}")
                print(f" Caracteres: {len(transcript['full_text'])}")
            
            # Informar sobre reutilização
            if reused_transcript or reused_metadata or reused_audio:
                reuse_info = []
                if reused_transcript: reuse_info.append("transcrição")
                if reused_metadata: reuse_info.append("metadados")
                if reused_audio: reuse_info.append("áudio")
                print(f" Dados reutilizados: {', '.join(reuse_info)}")
            
            return {
                'success': True,
                'video_id': video_id,
                'video_title': video_title,
                'folder_name': folder_name,
                'custom_folder': custom_folder,
                'rag_summary': rag_summary,
                'files_created': files_created,
                'reused_data': {  # NOVA FUNCIONALIDADE v5.0
                    'transcript': reused_transcript,
                    'metadata': reused_metadata,
                    'audio': reused_audio
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {e}")
            return {'error': str(e), 'input': url_or_id}
    
    def extract_playlist(self, playlist_url: str, start_index: int = 1, end_index: int = None) -> Dict[str, Any]:
        """
        Extrai playlist com melhorias v5.0:
        -  Numeração automática [1], [2], etc.
        -  Reutilização de dados anteriores
        -  Nome real da playlist
        -  Versionamento de pastas
        -  Range de vídeos (ex: do 3 ao 15)
        -  Pastas individuais para cada vídeo
        -  Controle de memória
        """
        try:
            print(f"\n Processando playlist: {playlist_url}")
            
            # Extrair ID da playlist
            playlist_id = self.extract_playlist_id(playlist_url)
            if not playlist_id:
                return {'error': 'ID da playlist inválido', 'input': playlist_url}
            
            print(f" ID da playlist: {playlist_id}")
            
            # Obter informações completas da playlist
            playlist_info = self.get_playlist_info(playlist_id)
            playlist_title = playlist_info.get('title', f'playlist_{playlist_id}')
            video_ids = playlist_info.get('video_ids', [])
            
            if not video_ids:
                return {'error': 'Nenhum vídeo encontrado na playlist', 'playlist_id': playlist_id}
            
            print(f" Playlist: '{playlist_title}' ({len(video_ids)} vídeos)")
            
            # Criar nome da pasta baseado no título real
            playlist_folder_name = self.create_playlist_folder_name(playlist_title, playlist_id)
            
            # Aplicar versionamento se pasta já existir
            versioned_folder_name = self.get_versioned_playlist_folder(playlist_folder_name, self.storage_dir)
            
            # Criar subpasta para a playlist
            playlist_folder = self.storage_dir / versioned_folder_name
            playlist_folder.mkdir(exist_ok=True)
            
            print(f" Pasta da playlist: {versioned_folder_name}")
            if self.reuse_data:
                print(f" Modo reutilização ativado: buscando dados anteriores")
            
            # Aplicar range de vídeos se especificado
            if end_index is None:
                end_index = len(video_ids)
            
            # Validar índices
            start_index = max(1, start_index)
            end_index = min(len(video_ids), end_index)
            
            if start_index > end_index:
                return {'error': f'Índice inicial ({start_index}) maior que final ({end_index})'}
            
            # Selecionar vídeos do range especificado
            selected_videos = video_ids[start_index-1:end_index]
            print(f" Processando vídeos {start_index} até {end_index} ({len(selected_videos)} vídeos)")
            
            # Salvar informações da playlist incluindo ordem para numeração
            playlist_metadata = {
                'playlist_info': playlist_info,
                'selected_range': {'start': start_index, 'end': end_index},
                'total_videos': len(video_ids),
                'selected_videos': len(selected_videos),
                'extraction_timestamp': datetime.now().isoformat(),
                'video_order': [(i, video_id) for i, video_id in enumerate(video_ids, 1)],  # NOVA FUNCIONALIDADE v5.0
                'extractor_version': '5.0',
                'features_used': {
                    'advanced_mode': self.advanced_mode,
                    'save_audio': self.save_audio,
                    'reuse_data': self.reuse_data
                }
            }
            
            with open(playlist_folder / 'playlist_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(playlist_metadata, f, indent=2, ensure_ascii=False)
            
            # Processar cada vídeo selecionado com numeração
            results = []
            success_count = 0
            error_count = 0
            reused_count = 0
            
            for i, video_id in enumerate(selected_videos, start_index):
                print(f"\n[{i}/{end_index}] Processando vídeo: {video_id}")
                
                # Controle de memória antes de cada vídeo
                import gc
                
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    print(f" Memória atual: {memory.percent:.1f}% usada")
                    
                    if memory.percent > 80:
                        print(" Memória alta detectada, forçando limpeza...")
                        gc.collect()
                        import time
                        time.sleep(2)  # Dar tempo para limpeza
                        
                        memory = psutil.virtual_memory()
                        memory_limit = 95 if self.advanced_mode else 90
                        if memory.percent > memory_limit:
                            print(f" MEMÓRIA CRÍTICA! Pausando processamento... ({memory.percent}% > {memory_limit}%)")
                            time.sleep(5)
                            gc.collect()
                except ImportError:
                    print(" psutil não disponível, continuando sem monitoramento de memória")
                except Exception:
                    pass  # Se psutil falhar, continuar
                
                try:
                    # NOVA FUNCIONALIDADE v5.0: Buscar dados existentes
                    existing_data = self.find_existing_video_data(video_id) if self.reuse_data else None
                    reused_transcript = False
                    reused_metadata = False
                    reused_audio = False
                    
                    # Tentar carregar metadados existentes primeiro
                    if existing_data:
                        metadata = self.load_existing_metadata(video_id, existing_data)
                        if metadata:
                            reused_metadata = True
                        else:
                            metadata = self.get_video_metadata(video_id)
                    else:
                        metadata = self.get_video_metadata(video_id)
                    
                    video_title = metadata.get('title', f'Video_{video_id}')
                    
                    # NOVA FUNCIONALIDADE v5.0: Nome da pasta com numeração [N]
                    video_folder_name = self.create_numbered_video_folder_name(video_title, video_id, i)
                    
                    # Criar pasta individual para o vídeo dentro da playlist
                    video_folder = playlist_folder / video_folder_name
                    video_folder.mkdir(exist_ok=True)
                    
                    print(f" Pasta do vídeo: {playlist_folder.name}/{video_folder_name}")
                    
                    # Tentar copiar áudio existente se necessário
                    if existing_data and self.save_audio:
                        reused_audio = self.copy_existing_audio(video_id, existing_data, video_folder)
                    
                    # Tentar carregar transcrição existente
                    if existing_data:
                        transcript = self.load_existing_transcript(video_id, existing_data)
                        if transcript:
                            reused_transcript = True
                        else:
                            transcript = self.get_transcript_with_fallbacks(video_id, video_folder)
                    else:
                        transcript = self.get_transcript_with_fallbacks(video_id, video_folder)
                    
                    if transcript:
                        # Análise RAG (combinar metadata com transcript para análise)
                        transcript_with_metadata = transcript.copy()
                        transcript_with_metadata.update(metadata)
                        analysis = self.analyze_content(transcript_with_metadata)
                        
                        # Salvar dados na pasta individual do vídeo
                        self.save_video_data(video_folder, video_id, metadata, transcript, analysis)
                        
                        result = {
                            'success': True,
                            'video_id': video_id,
                            'title': video_title,
                            'folder': f"{versioned_folder_name}/{video_folder_name}",
                            'segments': len(transcript.get('segments', [])),
                            'source': transcript.get('source', 'unknown'),
                            'reused_data': {  # NOVA FUNCIONALIDADE v5.0
                                'transcript': reused_transcript,
                                'metadata': reused_metadata,
                                'audio': reused_audio
                            }
                        }
                        success_count += 1
                        if reused_transcript or reused_metadata or reused_audio:
                            reused_count += 1
                            reuse_info = []
                            if reused_transcript: reuse_info.append("transcrição")
                            if reused_metadata: reuse_info.append("metadados")
                            if reused_audio: reuse_info.append("áudio")
                            print(f" [{i}/{end_index}] Vídeo extraído (reutilizado: {', '.join(reuse_info)}): {video_folder_name}")
                        else:
                            print(f" [{i}/{end_index}] Vídeo extraído: {video_folder_name}")
                    else:
                        result = {
                            'success': False,
                            'video_id': video_id,
                            'title': video_title,
                            'error': 'Transcrição não disponível',
                            'reused_data': {
                                'transcript': reused_transcript,
                                'metadata': reused_metadata,
                                'audio': reused_audio
                            }
                        }
                        error_count += 1
                        print(f" [{i}/{end_index}] Falha na transcrição: {video_folder_name}")
                    
                    results.append(result)
                    
                    # Limpeza de memória robusta entre vídeos para evitar sobrecarga
                    import gc
                    import time
                    
                    print("🧹 Limpando memória...")
                    
                    # Liberar variáveis grandes
                    transcript = None
                    transcript_with_metadata = None
                    analysis = None
                    metadata = None
                    existing_data = None
                    
                    # Forçar limpeza do garbage collector
                    gc.collect()
                    gc.collect()  # Duas vezes para garantir
                    
                    # Pausa entre vídeos para estabilizar sistema
                    time.sleep(3)
                    
                    try:
                        import psutil
                        memory = psutil.virtual_memory()
                        print(f" Memória após limpeza: {memory.percent:.1f}% usada")
                    except ImportError:
                        print(" Limpeza de memória concluída")
                    except:
                        pass
                    
                except Exception as e:
                    error_result = {
                        'success': False,
                        'video_id': video_id,
                        'error': str(e),
                        'reused_data': {
                            'transcript': False,
                            'metadata': False,
                            'audio': False
                        }
                    }
                    results.append(error_result)
                    error_count += 1
                    print(f" [{i}/{end_index}] Erro no vídeo {video_id}: {e}")
            
            # Criar ZIP da playlist
            zip_path = self.create_playlist_zip(playlist_folder)
            
            final_result = {
                'success': True,
                'playlist_id': playlist_id,
                'playlist_title': playlist_title,
                'folder_name': versioned_folder_name,
                'range_processed': f"{start_index}-{end_index}",
                'total_videos': len(selected_videos),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'reused_videos': reused_count,  # NOVA FUNCIONALIDADE v5.0
                'zip_file': zip_path,
                'results': results,
                'features_used': {  # NOVA FUNCIONALIDADE v5.0
                    'numbered_folders': True,
                    'data_reuse': self.reuse_data,
                    'advanced_mode': self.advanced_mode,
                    'audio_saving': self.save_audio
                }
            }
            
            print(f"\n🎉 Playlist processada!")
            print(f" Pasta: {versioned_folder_name}")
            print(f" Sucessos: {success_count}/{len(selected_videos)}")
            print(f" Falhas: {error_count}/{len(selected_videos)}")
            if reused_count > 0:
                print(f" Reutilizados: {reused_count}/{len(selected_videos)}")
            print(f" ZIP: {zip_path}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Erro ao extrair playlist: {e}")
            return {'error': str(e), 'playlist_url': playlist_url}

    def save_video_data(self, video_folder: Path, video_id: str, metadata: Dict, transcript: Dict, analysis: Dict):
        """
        Salva todos os dados do vídeo na pasta individual
        """
        try:
            # Criar pasta youtube_extracted_data igual ao vídeo individual
            extracted_folder = video_folder / 'youtube_extracted_data'
            extracted_folder.mkdir(exist_ok=True)
            
            # Criar subpastas organizadas
            chunks_folder = extracted_folder / 'chunks'
            database_folder = extracted_folder / 'database'
            metadata_folder = extracted_folder / 'metadata'
            rag_folder = extracted_folder / 'rag_content'
            transcripts_folder = extracted_folder / 'transcripts'
            
            for folder in [chunks_folder, database_folder, metadata_folder, rag_folder, transcripts_folder]:
                folder.mkdir(exist_ok=True)
            
            # Gerar timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{video_id}_{timestamp}"
            
            # Salvar metadados (formato principal e formato com timestamp)
            with open(video_folder / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            metadata_file = metadata_folder / f'{base_filename}_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Salvar transcrição (formato principal e formato com timestamp)
            transcript_file = video_folder / f'transcript_{video_id}.json'
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
                
            transcript_file_ts = transcripts_folder / f'{base_filename}_transcript.json'
            with open(transcript_file_ts, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
            
            # Salvar análise RAG (ambos locais)
            analysis_file = rag_folder / f'{video_id}_analysis.json'
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
                
            analysis_file_ts = rag_folder / f'{base_filename}_analysis.json'
            with open(analysis_file_ts, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            # Salvar texto puro da transcrição
            text_content = self.extract_text_from_segments(transcript.get('segments', []))
            text_file = rag_folder / f'{base_filename}_text.txt'
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Criar chunks se possível
            try:
                import gc
                print("🔗 Iniciando criação de chunks com controle de memória...")
                
                # Forçar limpeza antes de criar chunks
                gc.collect()
                
                chunks = self.create_chunks(text_content)
                if chunks:
                    chunks_file_json = chunks_folder / f'{base_filename}_chunks.json'
                    with open(chunks_file_json, 'w', encoding='utf-8') as f:
                        json.dump(chunks, f, indent=2, ensure_ascii=False)
                        
                    # Salvar chunks em CSV também (versão mais leve)
                    chunks_file_csv = chunks_folder / f'{base_filename}_chunks.csv'
                    import csv
                    with open(chunks_file_csv, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['chunk_id', 'content'])
                        for chunk in chunks:
                            writer.writerow([chunk.get('index', ''), chunk.get('text', '')])
                    
                    print(f" Chunks salvos: {len(chunks)} chunks")
                else:
                    print(" Nenhum chunk foi criado")
                
                # Limpeza imediata após chunks
                chunks = None  # Liberar referência
                gc.collect()
                
            except Exception as e:
                print(f" Erro ao criar chunks: {e}")
                # Forçar limpeza em caso de erro
                import gc
                gc.collect()
            
            # Criar banco de dados
            db_path = self.create_database()
            if db_path:
                # Mover banco para pasta do vídeo e para database folder
                import shutil
                target_db = video_folder / 'video_database.db'
                shutil.copy2(db_path, target_db)
                
                target_db_ts = database_folder / 'youtube_transcripts.db'
                shutil.copy2(db_path, target_db_ts)
            
            # Baixar thumbnail
            thumbnail_url = metadata.get('thumbnail')
            if thumbnail_url:
                # Thumbnail na pasta principal
                thumbnail_main = video_folder / f'{video_id}_thumbnail.jpg'
                downloaded_thumb = self.download_thumbnail(video_id, thumbnail_url, video_folder)
                
                # Copiar para pasta extracted também
                if downloaded_thumb and Path(downloaded_thumb).exists():
                    import shutil
                    shutil.copy2(downloaded_thumb, extracted_folder / f'{video_id}_thumbnail.jpg')
            
            print(f" Dados salvos em: {video_folder.name}")
            
        except Exception as e:
            print(f" Erro ao salvar dados do vídeo {video_id}: {e}")
    
    def create_playlist_zip(self, playlist_folder: Path) -> str:
        """
        Cria arquivo ZIP específico para uma playlist
        """
        try:
            zip_file = playlist_folder / f"{playlist_folder.name}.zip"
            
            print(f"\n Criando ZIP da playlist: {zip_file.name}")
            
            if zip_file.exists():
                zip_file.unlink()
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in playlist_folder.iterdir():
                    if item.is_dir() and item != zip_file:
                        for file_path in item.rglob('*'):
                            if file_path.is_file():
                                arc_path = file_path.relative_to(playlist_folder)
                                zipf.write(file_path, arc_path)
                    elif item.is_file() and item != zip_file:
                        zipf.write(item, item.name)
            
            zip_size = zip_file.stat().st_size / 1024 / 1024
            print(f" ZIP da playlist criado: {zip_file.name}")
            print(f" Tamanho: {zip_size:.1f} MB")
            
            return str(zip_file)
            
        except Exception as e:
            logger.error(f"Erro ao criar ZIP da playlist: {e}")
            return ""
    
    def create_custom_folder_zip(self, folder_path: Path) -> str:
        """
        Cria arquivo ZIP para uma pasta personalizada
        """
        try:
            zip_file = folder_path / f"{folder_path.name}.zip"
            
            print(f"\n Criando ZIP da pasta: {zip_file.name}")
            
            if zip_file.exists():
                zip_file.unlink()
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in folder_path.iterdir():
                    if item.is_dir() and item != zip_file:
                        for file_path in item.rglob('*'):
                            if file_path.is_file():
                                arc_path = file_path.relative_to(folder_path)
                                zipf.write(file_path, arc_path)
                    elif item.is_file() and item != zip_file:
                        zipf.write(item, item.name)
            
            zip_size = zip_file.stat().st_size / 1024 / 1024
            print(f" ZIP da pasta criado: {zip_file.name}")
            print(f" Tamanho: {zip_size:.1f} MB")
            return zip_file
            
        except Exception as e:
            logger.error(f"Erro ao criar ZIP: {e}")
            return None
    
    def list_extracted_videos(self) -> List[Dict[str, Any]]:
        """Lista todos os vídeos extraídos no storage"""
        try:
            videos = []
            
            for item in self.storage_dir.rglob('video_metadata.json'):
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                        summary['file_path'] = str(item)
                        videos.append(summary)
                except:
                    continue
            
            return sorted(videos, key=lambda x: x.get('extraction_date', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao listar vídeos: {e}")
            return []
            
        except Exception as e:
            logger.error(f"Erro ao listar vídeos: {e}")
            return []

def main():
    """
     SISTEMA RAG YOUTUBE - VERSÃO FINAL v5.0
    =============================================
    
     FUNCIONALIDADES IMPLEMENTADAS:
    
    1. 🔢 NUMERAÇÃO DE PLAYLISTS: Pastas numeradas [1], [2], etc.
    2.  MODO AVANÇADO: Escolha entre chunks rápidos ou completos
    3.  REUTILIZAÇÃO: Aproveita vídeos e transcrições anteriores
    4.  DOWNLOAD ÁUDIO: Opção de salvar áudio permanentemente
    
     INSTALAÇÃO DE BIBLIOTECAS:
    pip install openai-whisper SpeechRecognition pydub pyaudio
    
     RECURSOS COMPLETOS:
    -  Proxy/Tor para contornar bloqueio IP
    -  Download de áudio + transcrição local
    -  Múltiplas estratégias de fallback
    -  Sistema RAG completo com controle de chunks
    -  Reutilização inteligente de dados anteriores
    -  Numeração automática de playlists
    """
    parser = argparse.ArgumentParser(
        description='YouTube RAG Extractor - Sistema completo de extracao',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Extrair um vídeo (modo básico)
  python youtube_extractor.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Extrair múltiplos vídeos em um comando
  python youtube_extractor.py --url "https://www.youtube.com/watch?v=ff89oHwvNsM" "https://www.youtube.com/watch?v=cpO27YOO5bw" --folder "AutoCAD_docs"
  
  # Extrair múltiplos vídeos com modo avançado e reutilização
  python youtube_extractor.py --url "URL1" "URL2" "URL3" --advanced-mode --reuse-data --save-audio
  
  # Extrair com modo avançado (mais chunks, melhor qualidade)
  python youtube_extractor.py --url "VIDEO_URL" --advanced-mode
  
  # Extrair com download permanente de áudio
  python youtube_extractor.py --url "VIDEO_URL" --save-audio
  
  # Extrair reutilizando dados anteriores
  python youtube_extractor.py --url "VIDEO_URL" --reuse-data
  
  # Extrair vídeo em pasta personalizada
  python youtube_extractor.py --url "VIDEO_URL" --folder "meus_videos"
  
  # Extrair múltiplos vídeos de uma vez
  python youtube_extractor.py --url "URL1" "URL2" "URL3" --advanced-mode --reuse-data
  
  # Extrair múltiplos vídeos em pasta personalizada
  python youtube_extractor.py --url "URL1" "URL2" --folder "serie_videos" --save-audio
  
  # Extrair vídeos restritos a membros usando cookies do navegador
  python youtube_extractor.py --url "VIDEO_URL" --cookies-from-browser chrome
  python youtube_extractor.py --url "VIDEO_URL" --cookies-from-browser firefox
  
  # Extrair com proxy HTTP/SOCKS5/Tor
  python youtube_extractor.py --url "VIDEO_URL" --proxy "http://proxy.com:8080"
  python youtube_extractor.py --url "VIDEO_URL" --tor
  
  # Extrair playlist com numeração automática
  python youtube_extractor.py --playlist "https://www.youtube.com/playlist?list=ID"
  
  # Extrair playlist com reutilização de dados anteriores
  python youtube_extractor.py --playlist "PLAYLIST_URL" --reuse-data
  
  # Organizar playlist existente (apenas reorganizar arquivos)
  python youtube_extractor.py --organize-playlist "nome_da_pasta"
  
  # Listar vídeos extraídos
  python youtube_extractor.py --list
"""
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', '-u', nargs='+', help='URL(s) do(s) vídeo(s) do YouTube - pode especificar múltiplos vídeos')
    group.add_argument('--playlist', '-p', help='URL da playlist do YouTube')
    group.add_argument('--list', '-l', action='store_true', help='Listar vídeos extraídos')
    group.add_argument('--zip-folder', '-z', help='Criar ZIP de uma pasta específica')
    group.add_argument('--organize-playlist', '-o', help='Organizar playlist existente (reorganizar arquivos)')
    
    parser.add_argument('--storage', '-s', default='storage', help='Diretório de armazenamento (padrão: storage)')
    parser.add_argument('--folder', '-f', help='Pasta personalizada para vídeo individual')
    parser.add_argument('--proxy', help='Proxy: http://host:port ou socks5://host:port')
    parser.add_argument('--tor', action='store_true', help='Usar Tor (equivale a --proxy socks5://127.0.0.1:9050)')
    parser.add_argument('--cookies-from-browser', choices=['chrome', 'firefox', 'edge', 'safari', 'opera', 'brave'], 
                       help=' Extrair cookies do navegador para vídeos de membros (chrome, firefox, edge, etc.)')
    parser.add_argument('--cookies-file', 
                       help=' Arquivo de cookies (.txt) para vídeos de membros (alternativa ao --cookies-from-browser)')
    
    # Novos argumentos para playlist
    parser.add_argument('--start', type=int, default=1, help='Índice inicial da playlist (padrão: 1)')
    parser.add_argument('--end', type=int, help='Índice final da playlist (padrão: todos os vídeos)')
    
    # NOVAS FUNCIONALIDADES v5.0
    parser.add_argument('--advanced-mode', action='store_true', 
                       help=' Modo avançado: mais chunks para melhor qualidade RAG')
    parser.add_argument('--save-audio', action='store_true',
                       help=' Salvar arquivos de áudio permanentemente (padrão: temporário)')
    parser.add_argument('--reuse-data', action='store_true',
                       help=' Reutilizar vídeos/transcrições de versões anteriores')
    parser.add_argument('--chunk-size', type=int, default=500,
                       help=' Tamanho dos chunks (padrão: 500, avançado: 1000)')
    parser.add_argument('--max-chunks', type=int, default=30,
                       help=' Número máximo de chunks (padrão: 30, avançado: 100)')
    
    args = parser.parse_args()
    
    # Configurações modo avançado automáticas
    if args.advanced_mode:
        if args.chunk_size == 500:  # Se é valor padrão, aumentar
            args.chunk_size = 1000
        if args.max_chunks == 30:  # Se é valor padrão, aumentar para 200
            args.max_chunks = 200
        print(" MODO AVANÇADO: Configurações otimizadas para melhor qualidade RAG")
    
    # Criar extrator com novas configurações v5.0
    extractor = YouTubeRAGExtractor(
        args.storage, 
        proxy=args.proxy, 
        use_tor=args.tor,
        advanced_mode=args.advanced_mode,
        save_audio=args.save_audio,
        reuse_data=args.reuse_data,
        chunk_size=args.chunk_size,
        max_chunks=args.max_chunks,
        cookies_from_browser=args.cookies_from_browser,
        cookies_file=args.cookies_file
    )
    
    # Opção de pasta personalizada via input se não foi especificada via argumento
    if args.url and not args.folder:
        try:
            custom_folder = input("\n  Deseja usar uma pasta personalizada? (Enter para padrão): ").strip()
            if custom_folder:
                args.folder = custom_folder
                print(f" Pasta personalizada: {custom_folder}")
        except (KeyboardInterrupt, EOFError):
            print("\n⏭️  Usando pasta padrão")
    
    try:
        if args.url:
            # Determinar se há múltiplas URLs
            urls = args.url if isinstance(args.url, list) else [args.url]
            
            if len(urls) == 1:
                # Extrair vídeo único
                print(f" Processando vídeo único...")
                result = extractor.extract_single_video(urls[0], args.folder)
                
                if result.get('success'):
                    print(f"\n🎉 Extração RAG concluída com sucesso!")
                    
                    # Informações sobre reutilização de dados
                    reused_data = result.get('reused_data', {})
                    if any(reused_data.values()):
                        reuse_info = []
                        if reused_data.get('transcript'): reuse_info.append("transcrição")
                        if reused_data.get('metadata'): reuse_info.append("metadados")
                        if reused_data.get('audio'): reuse_info.append("áudio")
                        print(f" Dados reutilizados: {', '.join(reuse_info)}")
                    
                    # Informações sobre modo de processamento
                    extractor_settings = []
                    if extractor.advanced_mode:
                        extractor_settings.append("modo avançado")
                    if extractor.save_audio:
                        extractor_settings.append("áudio salvo")
                    if extractor.reuse_data:
                        extractor_settings.append("reutilização ativa")
                    
                    if extractor_settings:
                        print(f"⚙️ Configurações: {', '.join(extractor_settings)}")
                    
                    # Criar ZIP da pasta personalizada se especificada
                    if args.folder:
                        folder_path = extractor.storage_dir / args.folder
                        if folder_path.exists():
                            zip_path = extractor.create_custom_folder_zip(folder_path)
                            if zip_path:
                                print(f" ZIP da pasta criado: {zip_path}")
                else:
                    print(f"\n Erro na extração: {result.get('error')}")
                    sys.exit(1)
                    
            else:
                # Extrair múltiplos vídeos
                print(f" Processando {len(urls)} vídeos...")
                
                successful_extractions = 0
                failed_extractions = 0
                total_reused_data = {'transcript': 0, 'metadata': 0, 'audio': 0}
                
                for i, url in enumerate(urls, 1):
                    print(f"\n📹 [{i}/{len(urls)}] Processando: {url}")
                    
                    result = extractor.extract_single_video(url, args.folder)
                    
                    if result.get('success'):
                        successful_extractions += 1
                        print(f" Vídeo {i} extraído com sucesso!")
                        
                        # Contar dados reutilizados
                        reused_data = result.get('reused_data', {})
                        for key in total_reused_data:
                            if reused_data.get(key):
                                total_reused_data[key] += 1
                    else:
                        failed_extractions += 1
                        print(f" Erro no vídeo {i}: {result.get('error')}")
                
                # Resumo final
                print(f"\n🎉 Processamento de múltiplos vídeos concluído!")
                print(f" {successful_extractions}/{len(urls)} vídeos processados com sucesso")
                
                if failed_extractions > 0:
                    print(f"  {failed_extractions} vídeos falharam")
                
                # Informações sobre reutilização de dados
                if any(total_reused_data.values()):
                    reuse_info = []
                    if total_reused_data['transcript'] > 0: 
                        reuse_info.append(f"transcrição ({total_reused_data['transcript']})")
                    if total_reused_data['metadata'] > 0: 
                        reuse_info.append(f"metadados ({total_reused_data['metadata']})")
                    if total_reused_data['audio'] > 0: 
                        reuse_info.append(f"áudio ({total_reused_data['audio']})")
                    print(f" Dados reutilizados: {', '.join(reuse_info)}")
                
                # Informações sobre modo de processamento
                extractor_settings = []
                if extractor.advanced_mode:
                    extractor_settings.append("modo avançado")
                if extractor.save_audio:
                    extractor_settings.append("áudio salvo")
                if extractor.reuse_data:
                    extractor_settings.append("reutilização ativa")
                
                if extractor_settings:
                    print(f"⚙️ Configurações: {', '.join(extractor_settings)}")
                
                # Criar ZIP da pasta personalizada se especificada
                if args.folder:
                    folder_path = extractor.storage_dir / args.folder
                    if folder_path.exists():
                        zip_path = extractor.create_custom_folder_zip(folder_path)
                        if zip_path:
                            print(f" ZIP da pasta criado: {zip_path}")
                
                # Falhar se todos falharam
                if successful_extractions == 0:
                    sys.exit(1)
        
        elif args.playlist:
            # Extrair playlist com range opcional e numeração automática
            if args.start > 1 or args.end:
                print(f" Processando playlist do vídeo {args.start} até {args.end}")
            
            result = extractor.extract_playlist(args.playlist, args.start, args.end)
            
            if result.get('success'):
                print(f"\n🎉 Playlist extraída com sucesso!")
                print(f" {result['successful_extractions']}/{result['total_videos']} vídeos processados")
                if result.get('reused_videos', 0) > 0:
                    print(f"� {result['reused_videos']} vídeos reutilizaram dados anteriores")
                print(f"� Pasta da playlist: {result.get('folder_name', result.get('playlist_folder', 'N/A'))}")
                print(f"🔢 Pastas numeradas: [1], [2], [3]... para organização")
                if result.get('zip_file'):
                    print(f" ZIP da playlist: {result['zip_file']}")
            else:
                print(f"\n Erro na extração da playlist: {result.get('error')}")
                sys.exit(1)
        
        elif args.organize_playlist:
            # NOVA FUNCIONALIDADE v5.0: Organizar playlist existente
            result = extractor.organize_existing_playlist(args.organize_playlist)
            
            if result.get('success'):
                print(f"\n🎉 Playlist organizada com sucesso!")
                print(f" Pasta: {result['playlist_folder']}")
                print(f" {result['reorganized']}/{result['total_folders']} pastas reorganizadas")
                print(f"🔢 Pastas agora numeradas: [1], [2], [3]...")
                print(f"💡 {result['message']}")
            else:
                print(f"\n Erro na organização: {result.get('error')}")
                sys.exit(1)
        
        elif args.list:
            # Listar vídeos
            videos = extractor.list_extracted_videos()
            
            if videos:
                print(f"\n📹 Vídeos extraídos ({len(videos)} total):")
                print("=" * 80)
                
                for i, video in enumerate(videos, 1):
                    metadata = video.get('metadata', {})
                    stats = video.get('statistics', {})
                    duration_min = stats.get('duration_minutes', 0)
                    segments = stats.get('total_segments', 0)
                    chunks = stats.get('total_chunks', 0)
                    title = metadata.get('title', 'Título não encontrado')
                    
                    print(f"{i:2d}. {title[:50]}...")
                    print(f"     {Path(video['file_path']).parent.name}")
                    print(f"    ⏱️ {duration_min:.1f}min |  {segments} segmentos | 🔗 {chunks} chunks")
                    print(f"    📅 {video.get('extraction_date', '')}")
                    print()
            else:
                print("\n📹 Nenhum vídeo extraído ainda.")
        
        elif args.zip_folder:
            # Criar ZIP de pasta específica
            folder_path = extractor.storage_dir / args.zip_folder
            
            if not folder_path.exists():
                print(f"\n Pasta não encontrada: {args.zip_folder}")
                sys.exit(1)
            
            zip_path = extractor.create_custom_folder_zip(folder_path)
            
            if zip_path:
                print(f"\n ZIP criado: {zip_path}")
            else:
                print(f"\n Erro ao criar ZIP")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
