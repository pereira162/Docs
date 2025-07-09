#!/usr/bin/env python3
"""
🎬 EXTRATOR RAG COMPLETO - YOUTUBE
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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from collections import Counter

# Imports para YouTube
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    print("❌ yt-dlp não instalado. Execute: pip install yt-dlp")
    YT_DLP_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    print("❌ youtube-transcript-api não instalado. Execute: pip install youtube-transcript-api")
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    print("❌ requests/beautifulsoup4 não instalados. Execute: pip install requests beautifulsoup4")
    WEB_SCRAPING_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("❌ pandas não instalado. Execute: pip install pandas")
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
    🎬 Extrator RAG completo de vídeos do YouTube
    """
    
    def __init__(self, storage_dir: str = "storage"):
        """
        Inicializa o extrator RAG de vídeos do YouTube
        
        Args:
            storage_dir: Diretório principal de armazenamento
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Configurar estrutura de diretórios baseada no sistema antigo
        self.setup_directory_structure()
        
        print(f"🎬 YouTubeRAGExtractor inicializado")
        print(f"📁 Diretório de armazenamento: {self.storage_dir}")
    
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
        Obtém metadados do vídeo usando yt-dlp
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
                    'extractor_version': '3.0.0'
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
    
    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        Obtém lista de vídeos de uma playlist
        """
        if not YT_DLP_AVAILABLE:
            return []
        
        try:
            url = f'https://www.youtube.com/playlist?list={playlist_id}'
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                
                video_ids = []
                for entry in playlist_info.get('entries', []):
                    if entry and entry.get('id'):
                        video_ids.append(entry['id'])
                
                print(f"📋 Playlist {playlist_id}: {len(video_ids)} vídeos encontrados")
                return video_ids
        
        except Exception as e:
            logger.error(f"Erro ao obter vídeos da playlist: {e}")
            return []
    
    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém transcrição do vídeo
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            # Tentar idiomas preferidos
            languages = ['pt', 'pt-BR', 'en', 'es']
            
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            except Exception:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except Exception:
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        available_transcripts = list(transcript_list)
                        if available_transcripts:
                            transcript = available_transcripts[0]
                            transcript_data = transcript.fetch()
                        else:
                            return None
                    except Exception:
                        return None
            
            if not transcript_data:
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
                }
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
    
    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Cria chunks do texto para RAG baseado no sistema antigo
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
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
                        'overlap': overlap
                    }
                }
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def analyze_content(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise avançada do conteúdo para RAG baseada no sistema antigo
        """
        try:
            full_text = transcript_data.get('full_text', '')
            segments = transcript_data.get('segments', [])
            
            if not full_text:
                return {}
            
            # Análise básica de texto
            words = full_text.split()
            sentences = [s for s in full_text.split('.') if s.strip()]
            
            # Keywords filtradas
            word_freq = Counter(words)
            most_common_words = [word for word, count in word_freq.most_common(50)]
            language = transcript_data.get('language', 'en')
            filtered_keywords = self.filter_keywords(most_common_words, language)
            
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
    
    def create_video_folder_name(self, title: str, video_id: str) -> str:
        """
        Cria nome da pasta do vídeo (30 caracteres)
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
        Extrai dados RAG completos de um único vídeo baseado no sistema antigo
        """
        try:
            print(f"\n🎬 Processando vídeo: {url_or_id}")
            
            # Extrair ID do vídeo
            video_id = self.extract_video_id(url_or_id)
            if not video_id:
                return {'error': 'ID do vídeo inválido', 'input': url_or_id}
            
            print(f"📹 ID do vídeo: {video_id}")
            
            # Timestamp para arquivos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Obter metadados
            print("📊 Obtendo metadados...")
            metadata = self.get_video_metadata(video_id)
            
            if 'error' in metadata:
                return {'error': f"Erro ao obter metadados: {metadata['error']}", 'video_id': video_id}
            
            # Determinar pasta de trabalho
            if custom_folder:
                work_dir = self.storage_dir / custom_folder
                work_dir.mkdir(exist_ok=True)
                # Usar a estrutura de dados dentro da pasta personalizada
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
            else:
                dirs = self.dirs
            
            # Salvar metadados
            metadata_file = dirs['metadata'] / f"{video_id}_{timestamp}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Obter transcrição
            print("📝 Extraindo transcrição...")
            transcript = self.get_transcript(video_id)
            
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
                
                # Criar chunks
                print("🔗 Criando chunks...")
                chunks = self.create_chunks(full_text)
                
                # Salvar chunks JSON
                chunks_file = dirs['chunks'] / f"{video_id}_{timestamp}_chunks.json"
                with open(chunks_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)
                files_created['chunks'] = str(chunks_file)
                
                # Salvar chunks CSV
                if PANDAS_AVAILABLE:
                    chunks_csv = dirs['chunks'] / f"{video_id}_{timestamp}_chunks.csv"
                    chunks_df = pd.DataFrame(chunks)
                    chunks_df.to_csv(chunks_csv, index=False, encoding='utf-8')
                    files_created['chunks_csv'] = str(chunks_csv)
                
                # Análise RAG
                print("🧠 Realizando análise RAG...")
                analysis = self.analyze_content(transcript)
                
                # Adicionar estatísticas específicas
                analysis['statistics']['total_segments'] = len(transcript['segments'])
                analysis['statistics']['total_chunks'] = len(chunks)
                analysis['statistics']['text_length'] = len(full_text)
                
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
                
                print(f"✅ Transcrição extraída: {len(transcript['segments'])} segmentos, {len(chunks)} chunks")
            else:
                print("⚠️ Transcrição não disponível")
            
            # Criar banco de dados
            print("💾 Criando banco de dados...")
            db_path = self.create_database() if not custom_folder else None
            if custom_folder:
                # Criar banco na pasta personalizada
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
                db_path = str(db_path)
            
            if db_path:
                self.save_to_database(db_path, video_id, metadata, transcript, chunks, analysis)
                files_created['database'] = db_path
            
            # Baixar thumbnail
            print("🖼️ Baixando thumbnail...")
            thumbnail_path = self.download_thumbnail(
                video_id, 
                metadata.get('thumbnail', ''), 
                dirs['rag_content']
            )
            if thumbnail_path:
                files_created['thumbnail'] = thumbnail_path
            
            # Criar resumo RAG completo baseado no sistema antigo
            rag_summary = {
                'video_id': video_id,
                'extraction_date': timestamp,
                'files_created': files_created,
                'statistics': statistics,
                'metadata': {
                    'video_id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'extraction_date': datetime.now().isoformat(),
                    'extractor_version': '3.0.0',
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', '')
                },
                'analysis_summary': analysis if transcript else None
            }
            
            # Salvar resumo
            summary_file = dirs['rag_content'] / f"{video_id}_{timestamp}_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(rag_summary, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Vídeo processado com sucesso!")
            print(f"📊 Duração: {metadata.get('duration', 0) / 60:.1f} minutos")
            if transcript:
                print(f"📝 Segmentos: {len(transcript['segments'])}")
                print(f"🔗 Chunks: {len(chunks)}")
            
            return {
                'success': True,
                'video_id': video_id,
                'custom_folder': custom_folder,
                'rag_summary': rag_summary,
                'files_created': files_created
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {e}")
            return {'error': str(e), 'input': url_or_id}
    
    def extract_playlist(self, playlist_url: str) -> Dict[str, Any]:
        """
        Extrai todos os vídeos de uma playlist em subpasta dedicada
        """
        try:
            print(f"\n📋 Processando playlist: {playlist_url}")
            
            # Extrair ID da playlist
            playlist_id = self.extract_playlist_id(playlist_url)
            if not playlist_id:
                return {'error': 'ID da playlist inválido', 'input': playlist_url}
            
            print(f"📋 ID da playlist: {playlist_id}")
            
            # Criar subpasta para a playlist
            playlist_folder = self.storage_dir / f"playlist_{playlist_id}"
            playlist_folder.mkdir(exist_ok=True)
            
            print(f"📁 Subpasta da playlist: {playlist_folder.name}")
            
            # Obter vídeos da playlist
            video_ids = self.get_playlist_videos(playlist_id)
            if not video_ids:
                return {'error': 'Nenhum vídeo encontrado na playlist', 'playlist_id': playlist_id}
            
            print(f"🎬 {len(video_ids)} vídeos para processar")
            
            # Processar cada vídeo
            results = []
            success_count = 0
            error_count = 0
            
            for i, video_id in enumerate(video_ids, 1):
                print(f"\n[{i}/{len(video_ids)}] Processando vídeo: {video_id}")
                
                result = self.extract_single_video(
                    f"https://www.youtube.com/watch?v={video_id}",
                    custom_folder=playlist_folder.name
                )
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
                else:
                    error_count += 1
                
                # Pausa entre vídeos
                if i < len(video_ids):
                    time.sleep(1)
            
            # Salvar relatório da playlist
            playlist_report = {
                'playlist_id': playlist_id,
                'playlist_url': playlist_url,
                'playlist_folder': str(playlist_folder),
                'total_videos': len(video_ids),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'extraction_date': datetime.now().isoformat(),
                'video_results': results
            }
            
            report_file = playlist_folder / f"playlist_{playlist_id}_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_report, f, ensure_ascii=False, indent=2)
            
            # Criar ZIP da playlist
            zip_path = self.create_playlist_zip(playlist_folder)
            
            print(f"\n✅ Playlist processada!")
            print(f"📊 Sucessos: {success_count}")
            print(f"❌ Erros: {error_count}")
            print(f"📁 Pasta: {playlist_folder.name}")
            if zip_path:
                print(f"📦 ZIP criado: {zip_path}")
            
            return {
                'success': True,
                'playlist_id': playlist_id,
                'playlist_folder': str(playlist_folder),
                'total_videos': len(video_ids),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'zip_file': zip_path,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar playlist: {e}")
            return {'error': str(e), 'input': playlist_url}
    
    def create_playlist_zip(self, playlist_folder: Path) -> str:
        """
        Cria arquivo ZIP específico para uma playlist
        """
        try:
            zip_file = playlist_folder / f"{playlist_folder.name}.zip"
            
            print(f"\n📦 Criando ZIP da playlist: {zip_file.name}")
            
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
            print(f"✅ ZIP da playlist criado: {zip_file.name}")
            print(f"📦 Tamanho: {zip_size:.1f} MB")
            
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
            
            print(f"\n📦 Criando ZIP da pasta: {zip_file.name}")
            
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
            print(f"✅ ZIP da pasta criado: {zip_file.name}")
            print(f"📦 Tamanho: {zip_size:.1f} MB")
            
            return str(zip_file)
            
        except Exception as e:
            logger.error(f"Erro ao criar ZIP da pasta: {e}")
            return ""
    
    def list_extracted_videos(self) -> List[Dict[str, Any]]:
        """
        Lista todos os vídeos extraídos
        """
        videos = []
        
        try:
            for item in self.storage_dir.rglob('*_summary.json'):
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

def main():
    """
    Interface de linha de comando avançada
    """
    parser = argparse.ArgumentParser(
        description='🎬 Extrator RAG Completo de Vídeos do YouTube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Extrair um vídeo
  python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Extrair vídeo em pasta personalizada
  python youtube_rag_extractor_final.py --url "VIDEO_URL" --folder "meus_videos"
  
  # Extrair playlist completa (cria subpasta automaticamente)
  python youtube_rag_extractor_final.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
  
  # Listar vídeos extraídos
  python youtube_rag_extractor_final.py --list
  
  # Criar ZIP de pasta específica
  python youtube_rag_extractor_final.py --zip-folder "nome_da_pasta"
"""
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', '-u', help='URL do vídeo do YouTube')
    group.add_argument('--playlist', '-p', help='URL da playlist do YouTube')
    group.add_argument('--list', '-l', action='store_true', help='Listar vídeos extraídos')
    group.add_argument('--zip-folder', '-z', help='Criar ZIP de uma pasta específica')
    
    parser.add_argument('--storage', '-s', default='storage', help='Diretório de armazenamento (padrão: storage)')
    parser.add_argument('--folder', '-f', help='Pasta personalizada para vídeo individual')
    
    args = parser.parse_args()
    
    # Criar extrator
    extractor = YouTubeRAGExtractor(args.storage)
    
    try:
        if args.url:
            # Extrair vídeo único
            result = extractor.extract_single_video(args.url, args.folder)
            
            if result.get('success'):
                print(f"\n🎉 Extração RAG concluída com sucesso!")
                
                # Criar ZIP da pasta personalizada se especificada
                if args.folder:
                    folder_path = extractor.storage_dir / args.folder
                    if folder_path.exists():
                        zip_path = extractor.create_custom_folder_zip(folder_path)
                        if zip_path:
                            print(f"📦 ZIP da pasta criado: {zip_path}")
            else:
                print(f"\n❌ Erro na extração: {result.get('error')}")
                sys.exit(1)
        
        elif args.playlist:
            # Extrair playlist (cria subpasta e ZIP automaticamente)
            result = extractor.extract_playlist(args.playlist)
            
            if result.get('success'):
                print(f"\n🎉 Playlist extraída com sucesso!")
                print(f"📊 {result['successful_extractions']}/{result['total_videos']} vídeos processados")
                print(f"📁 Pasta da playlist: {result['playlist_folder']}")
                if result.get('zip_file'):
                    print(f"📦 ZIP da playlist: {result['zip_file']}")
            else:
                print(f"\n❌ Erro na extração da playlist: {result.get('error')}")
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
                    print(f"    📁 {Path(video['file_path']).parent.name}")
                    print(f"    ⏱️ {duration_min:.1f}min | 📝 {segments} segmentos | 🔗 {chunks} chunks")
                    print(f"    📅 {video.get('extraction_date', '')}")
                    print()
            else:
                print("\n📹 Nenhum vídeo extraído ainda.")
        
        elif args.zip_folder:
            # Criar ZIP de pasta específica
            folder_path = extractor.storage_dir / args.zip_folder
            
            if not folder_path.exists():
                print(f"\n❌ Pasta não encontrada: {args.zip_folder}")
                sys.exit(1)
            
            zip_path = extractor.create_custom_folder_zip(folder_path)
            
            if zip_path:
                print(f"\n✅ ZIP criado: {zip_path}")
            else:
                print(f"\n❌ Erro ao criar ZIP")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
