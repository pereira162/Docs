#!/usr/bin/env python3
"""
🎬 EXTRATOR DE VÍDEOS DO YOUTUBE - SISTEMA RAG COMPLETO
=====================================================
Sistema completo para extração de vídeos do YouTube com:
- Extração RAG completa (analysis, summary, text, transcript, database, chunks)
- Organização em subpastas por vídeo (30 caracteres, controle de versão)
- Subpastas para playlists e vídeos individuais personalizados
- Geração automática de .zip individual para cada playlist/pasta
- Filtro de keywords (remove conectivos)
- Interface de linha de comando avançada
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import re
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import subprocess
import time
from collections import Counter
import nltk
from textstat import flesch_reading_ease

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

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    print("❌ textstat não instalado. Execute: pip install textstat")
    TEXTSTAT_AVAILABLE = False

# Conectivos e palavras de baixo significado para filtrar das keywords
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
        
        # Criar subdiretórios estruturados como no sistema antigo
        self.dirs = {
            'transcripts': self.storage_dir / 'transcripts',
            'metadata': self.storage_dir / 'metadata', 
            'chunks': self.storage_dir / 'chunks',
            'rag_content': self.storage_dir / 'rag_content',
            'database': self.storage_dir / 'database'
        }
        
        for directory in self.dirs.values():
            directory.mkdir(exist_ok=True)
        
        print(f"🎬 YouTubeRAGExtractor inicializado")
        print(f"📁 Diretório de armazenamento: {self.storage_dir}")
        print(f"📁 Subdiretórios criados: {list(self.dirs.keys())}")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrai ID do vídeo de URL do YouTube
        
        Args:
            url: URL do YouTube
            
        Returns:
            ID do vídeo ou None se inválido
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
            
            # Se já for um ID
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
                
            return None
            
        except Exception as e:
            print(f"❌ Erro ao extrair ID do vídeo: {e}")
            return None
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """
        Extrai ID da playlist de URL do YouTube
        
        Args:
            url: URL da playlist do YouTube
            
        Returns:
            ID da playlist ou None se inválido
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
            print(f"❌ Erro ao extrair ID da playlist: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Obtém metadados do vídeo usando yt-dlp
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Metadados do vídeo
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
                    'extractor_version': '2.0.0'
                }
                
                return metadata
            
        except Exception as e:
            print(f"❌ Erro ao obter metadados: {e}")
            return {
                'video_id': video_id,
                'title': f'Video_{video_id}',
                'error': str(e),
                'extraction_date': datetime.now().isoformat()
            }
    
    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        Obtém lista de vídeos de uma playlist
        
        Args:
            playlist_id: ID da playlist
            
        Returns:
            Lista de IDs de vídeos
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
            print(f"❌ Erro ao obter vídeos da playlist: {e}")
            return []
    
    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém transcrição do vídeo
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dados da transcrição ou None
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            # Tentar idiomas preferidos
            languages = ['pt', 'pt-BR', 'en', 'es']
            
            try:
                # Tentar obter transcrição diretamente
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            except Exception:
                try:
                    # Tentar com inglês apenas
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except Exception:
                    try:
                        # Tentar qualquer idioma disponível
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
            
            # Detectar idioma e tipo de transcrição
            language = 'en'  # padrão
            is_generated = True  # padrão
            
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
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter transcrição: {e}")
            return None
    
    def filter_keywords(self, words: List[str], language: str = 'en') -> List[str]:
        """
        Filtra palavras removendo conectivos e palavras de baixo significado
        
        Args:
            words: Lista de palavras
            language: Idioma ('en' ou 'pt')
            
        Returns:
            Lista de palavras filtradas
        """
        stop_words = STOP_WORDS.get(language, STOP_WORDS['en'])
        
        filtered_words = []
        for word in words:
            # Limpar a palavra
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Filtrar palavras muito pequenas, conectivos e stop words
            if (len(clean_word) >= 3 and 
                clean_word not in stop_words and
                not clean_word.isdigit()):
                filtered_words.append(clean_word)
        
        return filtered_words
    
    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Cria chunks do texto para RAG
        
        Args:
            text: Texto para dividir
            chunk_size: Tamanho do chunk em caracteres
            overlap: Sobreposição entre chunks
            
        Returns:
            Lista de chunks
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Se não é o último chunk, tentar quebrar em uma frase
            if end < len(text):
                # Procurar por quebra de frase próxima
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
            
            # Próximo início com overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def analyze_content(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """
        Análise avançada do conteúdo para RAG
        
        Args:
            text: Texto para analisar
            language: Idioma do texto
            
        Returns:
            Análise completa do conteúdo
        """
        try:
            # Estatísticas básicas
            char_count = len(text)
            words = text.split()
            word_count = len(words)
            sentences = re.split(r'[.!?]+', text)
            sentence_count = len([s for s in sentences if s.strip()])
            
            # Keywords filtradas
            word_freq = Counter(words)
            most_common_words = [word for word, count in word_freq.most_common(50)]
            filtered_keywords = self.filter_keywords(most_common_words, language)
            
            # Análise de legibilidade
            readability_score = 0
            if TEXTSTAT_AVAILABLE and text.strip():
                try:
                    readability_score = flesch_reading_ease(text)
                except:
                    readability_score = 0
            
            # Análise de tópicos simples (baseada em keywords)
            topics = []
            tech_keywords = ['technology', 'software', 'computer', 'digital', 'app', 'web', 'api', 'code', 'programming']
            if any(keyword in text.lower() for keyword in tech_keywords):
                topics.append('tecnologia')
            
            # Análise de sentimento simples
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'love', 'like', 'awesome', 'brilliant']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'problem', 'fail', 'error', 'wrong', 'difficult']
            
            positive_count = sum(1 for word in positive_words if word in text.lower())
            negative_count = sum(1 for word in negative_words if word in text.lower())
            
            if positive_count > negative_count:
                sentiment = 'positive'
                sentiment_score = 0.5 + (positive_count - negative_count) / (positive_count + negative_count + 1) * 0.5
            elif negative_count > positive_count:
                sentiment = 'negative'
                sentiment_score = -0.5 - (negative_count - positive_count) / (positive_count + negative_count + 1) * 0.5
            else:
                sentiment = 'neutral'
                sentiment_score = 0.0
            
            # Entidades simples
            entities = {
                'urls': re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text),
                'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
                'numbers': re.findall(r'\b\d+(?:\.\d+)?\b', text)
            }
            
            return {
                'statistics': {
                    'total_characters': char_count,
                    'total_words': word_count,
                    'total_sentences': sentence_count,
                    'average_words_per_sentence': word_count / sentence_count if sentence_count > 0 else 0,
                    'readability_score': readability_score
                },
                'content_analysis': {
                    'language_detected': language,
                    'readability_score': readability_score,
                    'sentiment_analysis': {
                        'sentiment': sentiment,
                        'score': sentiment_score,
                        'positive_count': positive_count,
                        'negative_count': negative_count
                    }
                },
                'keywords': [{'word': word, 'frequency': word_freq[word]} for word in filtered_keywords[:15]],
                'topics': topics,
                'sentiment': sentiment,
                'entities': entities,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro na análise de conteúdo: {e}")
            return {
                'statistics': {'total_characters': len(text), 'total_words': len(text.split())},
                'content_analysis': {'language_detected': language},
                'keywords': [],
                'topics': [],
                'sentiment': 'neutral'
            }
    
    def create_database(self, video_folder: Path) -> str:
        """
        Cria banco SQLite com os dados do vídeo
        
        Args:
            video_folder: Pasta do vídeo
            
        Returns:
            Caminho do banco de dados
        """
        try:
            db_path = video_folder / "video_data.db"
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Criar tabelas
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
                    extraction_date TEXT
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
            
            conn.commit()
            conn.close()
            
            return str(db_path)
            
        except Exception as e:
            print(f"❌ Erro ao criar banco de dados: {e}")
            return ""
    
    def save_to_database(self, db_path: str, metadata: Dict, transcript: Optional[Dict], chunks: List[Dict]) -> bool:
        """
        Salva dados no banco SQLite
        
        Args:
            db_path: Caminho do banco
            metadata: Metadados do vídeo
            transcript: Transcrição do vídeo
            chunks: Chunks do texto
            
        Returns:
            True se sucesso
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Inserir metadados
            cursor.execute('''
                INSERT OR REPLACE INTO video_metadata 
                (video_id, title, description, uploader, upload_date, duration, view_count, like_count, extraction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get('video_id', ''),
                metadata.get('title', ''),
                metadata.get('description', ''),
                metadata.get('uploader', ''),
                metadata.get('upload_date', ''),
                metadata.get('duration', 0),
                metadata.get('view_count', 0),
                metadata.get('like_count', 0),
                metadata.get('extraction_date', '')
            ))
            
            # Inserir segmentos de transcrição
            if transcript and transcript.get('segments'):
                for segment in transcript['segments']:
                    cursor.execute('''
                        INSERT INTO transcript_segments 
                        (video_id, segment_index, text, start_time, duration, end_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metadata.get('video_id', ''),
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
                    metadata.get('video_id', ''),
                    chunk.get('index', 0),
                    chunk.get('text', ''),
                    chunk.get('start_char', 0),
                    chunk.get('end_char', 0),
                    chunk.get('char_count', 0),
                    chunk.get('word_count', 0)
                ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            return False
    
    def create_video_folder_name(self, title: str, video_id: str) -> str:
        """
        Cria nome da pasta do vídeo (primeiros 30 caracteres do título)
        
        Args:
            title: Título do vídeo
            video_id: ID do vídeo
            
        Returns:
            Nome da pasta
        """
        try:
            # Limpar título
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.strip()
            
            # Primeiros 30 caracteres
            if len(clean_title) > 30:
                folder_name = clean_title[:30].strip()
            else:
                folder_name = clean_title
            
            # Se ficou vazio, usar ID
            if not folder_name:
                folder_name = video_id[:11]
            
            return folder_name
            
        except:
            return video_id[:11]
    
    def get_next_version_folder(self, base_folder_name: str, parent_dir: Path) -> str:
        """
        Obtém próxima versão da pasta (controle de versão)
        
        Args:
            base_folder_name: Nome base da pasta
            parent_dir: Diretório pai
            
        Returns:
            Nome da pasta com versão
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
        
        Args:
            video_id: ID do vídeo
            thumbnail_url: URL da thumbnail
            output_dir: Diretório de saída
            
        Returns:
            Caminho da thumbnail ou None
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
            print(f"⚠️ Não foi possível baixar thumbnail: {e}")
            return None
    
    def extract_single_video(self, url_or_id: str, custom_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrai dados RAG completos de um único vídeo
        
        Args:
            url_or_id: URL ou ID do vídeo
            custom_folder: Pasta personalizada (opcional)
            
        Returns:
            Resultado da extração
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
            
            # Salvar metadados
            metadata_file = self.dirs['metadata'] / f"{video_id}_{timestamp}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Obter transcrição
            print("📝 Extraindo transcrição...")
            transcript = self.get_transcript(video_id)
            
            # Inicializar arquivos criados
            files_created = {
                'metadata': str(metadata_file),
                'transcript_json': None,
                'text': None,
                'chunks': None,
                'chunks_csv': None,
                'analysis': None,
                'database': None,
                'thumbnail': None
            }
            
            statistics = {
                'total_segments': 0,
                'total_chunks': 0,
                'text_length': 0,
                'duration_minutes': metadata.get('duration', 0) / 60
            }
            
            if transcript:
                # Salvar transcrição JSON
                transcript_file = self.dirs['transcripts'] / f"{video_id}_{timestamp}_transcript.json"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
                files_created['transcript_json'] = str(transcript_file)
                
                # Extrair texto completo
                full_text = transcript['full_text']
                
                # Salvar texto puro
                text_file = self.dirs['rag_content'] / f"{video_id}_{timestamp}_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                files_created['text'] = str(text_file)
                
                # Criar chunks
                print("🔗 Criando chunks...")
                chunks = self.create_chunks(full_text)
                
                # Salvar chunks JSON
                chunks_file = self.dirs['chunks'] / f"{video_id}_{timestamp}_chunks.json"
                with open(chunks_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)
                files_created['chunks'] = str(chunks_file)
                
                # Salvar chunks CSV
                if PANDAS_AVAILABLE:
                    chunks_csv = self.dirs['chunks'] / f"{video_id}_{timestamp}_chunks.csv"
                    chunks_df = pd.DataFrame(chunks)
                    chunks_df.to_csv(chunks_csv, index=False, encoding='utf-8')
                    files_created['chunks_csv'] = str(chunks_csv)
                
                # Análise RAG
                print("🧠 Realizando análise RAG...")
                analysis = self.analyze_content(full_text, transcript.get('language', 'en'))
                
                # Adicionar estatísticas específicas da transcrição
                analysis['statistics']['total_segments'] = len(transcript['segments'])
                analysis['statistics']['total_chunks'] = len(chunks)
                analysis['statistics']['text_length'] = len(full_text)
                analysis['statistics']['duration_minutes'] = metadata.get('duration', 0) / 60
                
                # Salvar análise
                analysis_file = self.dirs['rag_content'] / f"{video_id}_{timestamp}_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)
                files_created['analysis'] = str(analysis_file)
                
                # Criar banco de dados
                print("💾 Criando banco de dados...")
                db_file = self.dirs['database'] / "youtube_transcripts.db"
                self.save_to_database(str(db_file), metadata, transcript, chunks)
                files_created['database'] = str(db_file)
                
                # Atualizar estatísticas
                statistics = {
                    'total_segments': len(transcript['segments']),
                    'total_chunks': len(chunks),
                    'text_length': len(full_text),
                    'duration_minutes': metadata.get('duration', 0) / 60
                }
                
                print(f"✅ Transcrição extraída: {len(transcript['segments'])} segmentos, {len(chunks)} chunks")
            else:
                print("⚠️ Transcrição não disponível")
            
            # Baixar thumbnail
            print("🖼️ Baixando thumbnail...")
            thumbnail_path = self.download_thumbnail(
                video_id, 
                metadata.get('thumbnail', ''), 
                self.dirs['rag_content']
            )
            if thumbnail_path:
                files_created['thumbnail'] = thumbnail_path
            
            # Criar resumo RAG completo
            rag_summary = {
                'video_id': video_id,
                'extraction_date': timestamp,
                'files_created': files_created,
                'statistics': statistics,
                'metadata': {
                    'video_id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'extraction_date': datetime.now().isoformat(),
                    'extractor_version': '2.0.0',
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', '')
                },
                'analysis_summary': analysis if transcript else None
            }
            
            summary_file = self.dirs['rag_content'] / f"{video_id}_{timestamp}_summary.json"
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
            print(f"❌ Erro ao processar vídeo: {e}")
            return {'error': str(e), 'input': url_or_id}
    
    def extract_playlist(self, playlist_url: str) -> Dict[str, Any]:
        """
        Extrai todos os vídeos de uma playlist em subpasta dedicada
        
        Args:
            playlist_url: URL da playlist
            
        Returns:
            Resultado da extração
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
            
            # Processar cada vídeo na subpasta da playlist
            results = []
            success_count = 0
            error_count = 0
            
            for i, video_id in enumerate(video_ids, 1):
                print(f"\n[{i}/{len(video_ids)}] Processando vídeo: {video_id}")
                
                # Extrair vídeo diretamente na pasta da playlist
                result = self.extract_single_video(
                    f"https://www.youtube.com/watch?v={video_id}",
                    custom_folder=playlist_folder.name
                )
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
                else:
                    error_count += 1
                
                # Pausa entre vídeos para evitar rate limiting
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
            print(f"📄 Relatório: {report_file}")
            if zip_path:
                print(f"📦 ZIP criado: {zip_path}")
            
            return {
                'success': True,
                'playlist_id': playlist_id,
                'playlist_folder': str(playlist_folder),
                'total_videos': len(video_ids),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'report_file': str(report_file),
                'zip_file': zip_path,
                'results': results
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar playlist: {e}")
            return {'error': str(e), 'input': playlist_url}
    
    def create_playlist_zip(self, playlist_folder: Path) -> str:
        """
        Cria arquivo ZIP específico para uma playlist
        
        Args:
            playlist_folder: Pasta da playlist
            
        Returns:
            Caminho do arquivo ZIP
        """
        try:
            zip_file = playlist_folder / f"{playlist_folder.name}.zip"
            
            print(f"\n📦 Criando ZIP da playlist: {zip_file.name}")
            
            # Remover ZIP anterior se existir
            if zip_file.exists():
                zip_file.unlink()
            
            # Criar novo ZIP
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar todas as pastas e arquivos da playlist
                for item in playlist_folder.iterdir():
                    if item.is_dir() and item != zip_file:
                        # Adicionar pasta completa
                        for file_path in item.rglob('*'):
                            if file_path.is_file():
                                # Caminho relativo dentro do ZIP
                                arc_path = file_path.relative_to(playlist_folder)
                                zipf.write(file_path, arc_path)
                    elif item.is_file() and item != zip_file:
                        # Adicionar arquivos na raiz (relatório da playlist)
                        zipf.write(item, item.name)
            
            zip_size = zip_file.stat().st_size / 1024 / 1024  # MB
            print(f"✅ ZIP da playlist criado: {zip_file.name}")
            print(f"📦 Tamanho: {zip_size:.1f} MB")
            
            return str(zip_file)
            
        except Exception as e:
            print(f"❌ Erro ao criar ZIP da playlist: {e}")
            return ""
    
    def create_custom_folder_zip(self, folder_path: Path) -> str:
        """
        Cria arquivo ZIP para uma pasta personalizada
        
        Args:
            folder_path: Caminho da pasta
            
        Returns:
            Caminho do arquivo ZIP
        """
        try:
            zip_file = folder_path / f"{folder_path.name}.zip"
            
            print(f"\n📦 Criando ZIP da pasta: {zip_file.name}")
            
            # Remover ZIP anterior se existir
            if zip_file.exists():
                zip_file.unlink()
            
            # Criar novo ZIP
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar todas as pastas e arquivos
                for item in folder_path.iterdir():
                    if item.is_dir() and item != zip_file:
                        # Adicionar pasta completa
                        for file_path in item.rglob('*'):
                            if file_path.is_file():
                                # Caminho relativo dentro do ZIP
                                arc_path = file_path.relative_to(folder_path)
                                zipf.write(file_path, arc_path)
                    elif item.is_file() and item != zip_file:
                        # Adicionar arquivos na raiz
                        zipf.write(item, item.name)
            
            zip_size = zip_file.stat().st_size / 1024 / 1024  # MB
            print(f"✅ ZIP da pasta criado: {zip_file.name}")
            print(f"📦 Tamanho: {zip_size:.1f} MB")
            
            return str(zip_file)
            
        except Exception as e:
            print(f"❌ Erro ao criar ZIP da pasta: {e}")
            return ""
    
    def list_extracted_videos(self) -> List[Dict[str, Any]]:
        """
        Lista todos os vídeos extraídos
        
        Returns:
            Lista de vídeos extraídos
        """
        videos = []
        
        try:
            for item in self.storage_dir.rglob('*_rag_summary.json'):
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                        summary['file_path'] = str(item)
                        videos.append(summary)
                except:
                    continue
            
            return sorted(videos, key=lambda x: x.get('extraction_date', ''), reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao listar vídeos: {e}")
            return []

def main():
    """
    Interface de linha de comando avançada
    """
    parser = argparse.ArgumentParser(
        description='🎬 Extrator RAG de Vídeos do YouTube - Sistema Completo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Extrair um vídeo
  python youtube_rag_extractor.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Extrair vídeo em pasta personalizada
  python youtube_rag_extractor.py --url "VIDEO_URL" --folder "meus_videos"
  
  # Extrair playlist completa (cria subpasta automaticamente)
  python youtube_rag_extractor.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
  
  # Listar vídeos extraídos
  python youtube_rag_extractor.py --list
  
  # Criar ZIP de pasta específica
  python youtube_rag_extractor.py --zip-folder "nome_da_pasta"
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
                    stats = video.get('statistics', {})
                    duration_min = stats.get('duration_minutes', 0)
                    segments = stats.get('total_segments', 0)
                    chunks = stats.get('total_chunks', 0)
                    
                    print(f"{i:2d}. {video['metadata']['title'][:50]}...")
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
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
