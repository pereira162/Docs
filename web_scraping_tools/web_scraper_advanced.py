#!/usr/bin/env python3
"""
WEB DOCUMENTATION SCRAPER WITH VIDEO PROCESSING
===============================================
Sistema avançado que inclui download e transcrição de vídeos usando Whisper
"""

import os
import sys
import json
import subprocess
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime

# Importar o scraper base
from web_documentation_scraper import WebDocumentationScraper

class WebScraperWithVideoProcessing(WebDocumentationScraper):
    """
    Extensão do scraper base com processamento de vídeos
    """
    
    def __init__(self, storage_path: str = "web_scraping_storage"):
        super().__init__(storage_path)
        
        # Verificar se Whisper está disponível
        try:
            import whisper
            self.whisper_model = whisper.load_model("base")
            print("Modelo Whisper carregado para transcrição")
        except ImportError:
            self.whisper_model = None
            print("Whisper não disponível - sem transcrição de vídeos")
        
        # Verificar ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Verifica se FFmpeg está disponível"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            print("FFmpeg não encontrado - download de vídeos limitado")
            return False
    
    def process_videos_from_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa todos os vídeos encontrados em uma página
        
        Args:
            page_data: Dados da página extraída
            
        Returns:
            Dados atualizados com vídeos processados
        """
        if not page_data.get('videos'):
            return page_data
        
        processed_videos = []
        
        for video in page_data['videos']:
            try:
                processed_video = self._process_single_video(video, page_data['url'])
                processed_videos.append(processed_video)
            except Exception as e:
                print(f"Erro ao processar vídeo: {e}")
                processed_video = video.copy()
                processed_video['error'] = str(e)
                processed_videos.append(processed_video)
        
        page_data['videos'] = processed_videos
        return page_data
    
    def _process_single_video(self, video: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """
        Processa um único vídeo
        
        Args:
            video: Dados do vídeo
            page_url: URL da página
            
        Returns:
            Dados do vídeo processado
        """
        processed_video = video.copy()
        
        # Determinar URL do vídeo
        video_url = None
        if video['type'] == 'html5' and video.get('sources'):
            # Preferir MP4 sobre WebM
            for source in video['sources']:
                if source.endswith('.mp4'):
                    video_url = source
                    break
            if not video_url:
                video_url = video['sources'][0]
        
        elif video['type'] == 'embedded':
            video_url = video.get('url')
        
        if not video_url:
            processed_video['error'] = "URL do vídeo não encontrada"
            return processed_video
        
        # Criar identificador único para o vídeo
        video_id = hashlib.md5(video_url.encode()).hexdigest()[:12]
        
        # Pasta para o vídeo
        video_folder = self.storage_path / "videos" / video_id
        video_folder.mkdir(parents=True, exist_ok=True)
        
        processed_video['video_id'] = video_id
        processed_video['local_folder'] = str(video_folder)
        
        # Download do vídeo
        if video['type'] == 'html5':
            downloaded_file = self._download_video_file(video_url, video_folder)
            if downloaded_file:
                processed_video['local_file'] = str(downloaded_file)
                
                # Transcrever se possível
                if self.whisper_model and downloaded_file.exists():
                    transcript = self._transcribe_video(downloaded_file)
                    if transcript:
                        processed_video['transcript'] = transcript
                        
                        # Salvar transcrição
                        transcript_file = video_folder / "transcript.txt"
                        with open(transcript_file, 'w', encoding='utf-8') as f:
                            f.write(transcript)
                        processed_video['transcript_file'] = str(transcript_file)
        
        # Salvar metadados
        metadata_file = video_folder / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(processed_video, f, indent=2, ensure_ascii=False)
        
        return processed_video
    
    def _download_video_file(self, video_url: str, output_folder: Path) -> Optional[Path]:
        """
        Faz download de um arquivo de vídeo
        
        Args:
            video_url: URL do vídeo
            output_folder: Pasta de destino
            
        Returns:
            Caminho do arquivo baixado ou None
        """
        try:
            response = self.session.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Determinar extensão
            if video_url.endswith('.mp4'):
                ext = '.mp4'
            elif video_url.endswith('.webm'):
                ext = '.webm'
            else:
                ext = '.mp4'  # Padrão
            
            output_file = output_folder / f"video{ext}"
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Vídeo baixado: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Erro ao baixar vídeo {video_url}: {e}")
            return None
    
    def _transcribe_video(self, video_file: Path) -> Optional[str]:
        """
        Transcreve um arquivo de vídeo usando Whisper
        
        Args:
            video_file: Caminho do arquivo de vídeo
            
        Returns:
            Texto transcrito ou None
        """
        if not self.whisper_model:
            return None
        
        try:
            print(f"Transcrevendo vídeo: {video_file}")
            
            # Extrair áudio se necessário
            if video_file.suffix == '.mp4' and self.ffmpeg_available:
                audio_file = video_file.with_suffix('.wav')
                cmd = [
                    'ffmpeg', '-i', str(video_file), 
                    '-vn', '-acodec', 'pcm_s16le', 
                    '-ar', '16000', '-ac', '1', 
                    str(audio_file), '-y'
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                transcribe_file = audio_file
            else:
                transcribe_file = video_file
            
            # Transcrever
            result = self.whisper_model.transcribe(str(transcribe_file))
            
            # Limpar arquivo de áudio temporário
            if transcribe_file != video_file and transcribe_file.exists():
                transcribe_file.unlink()
            
            return result['text'].strip()
            
        except Exception as e:
            print(f"Erro na transcrição: {e}")
            return None
    
    def create_chunks_from_content(self, page_data: Dict[str, Any], chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Cria chunks RAG do conteúdo extraído
        
        Args:
            page_data: Dados da página
            chunk_size: Tamanho dos chunks
            
        Returns:
            Lista de chunks
        """
        chunks = []
        
        # Chunk do texto principal
        text_content = page_data.get('text_content', '')
        if text_content:
            text_chunks = self._split_text_into_chunks(text_content, chunk_size)
            for i, chunk_text in enumerate(text_chunks):
                chunk = {
                    'id': f"{page_data.get('url', 'unknown')}#text_{i}",
                    'type': 'text',
                    'content': chunk_text,
                    'source_url': page_data.get('url'),
                    'metadata': {
                        'title': page_data.get('title'),
                        'language': page_data.get('language'),
                        'chunk_index': i
                    }
                }
                
                # Gerar embedding se disponível
                if self.embedding_model:
                    try:
                        embedding = self.embedding_model.encode(chunk_text)
                        chunk['embedding'] = embedding.tolist()
                    except:
                        pass
                
                chunks.append(chunk)
        
        # Chunks de transcrições de vídeos
        for video in page_data.get('videos', []):
            if video.get('transcript'):
                video_chunks = self._split_text_into_chunks(video['transcript'], chunk_size)
                for i, chunk_text in enumerate(video_chunks):
                    chunk = {
                        'id': f"{page_data.get('url', 'unknown')}#video_{video.get('video_id', 'unknown')}_{i}",
                        'type': 'video_transcript',
                        'content': chunk_text,
                        'source_url': page_data.get('url'),
                        'video_id': video.get('video_id'),
                        'metadata': {
                            'title': page_data.get('title'),
                            'language': page_data.get('language'),
                            'chunk_index': i,
                            'video_sources': video.get('sources', [])
                        }
                    }
                    
                    # Gerar embedding se disponível
                    if self.embedding_model:
                        try:
                            embedding = self.embedding_model.encode(chunk_text)
                            chunk['embedding'] = embedding.tolist()
                        except:
                            pass
                    
                    chunks.append(chunk)
        
        return chunks
    
    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """
        Divide texto em chunks
        
        Args:
            text: Texto para dividir
            chunk_size: Tamanho máximo do chunk
            
        Returns:
            Lista de chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def save_to_database(self, page_data: Dict[str, Any], chunks: List[Dict[str, Any]]):
        """
        Salva dados no banco SQLite
        
        Args:
            page_data: Dados da página
            chunks: Chunks gerados
        """
        db_path = self.storage_path / "web_scraping.db"
        
        with sqlite3.connect(db_path) as conn:
            # Criar tabelas se não existirem
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE,
                    title TEXT,
                    language TEXT,
                    content TEXT,
                    extracted_at TEXT,
                    word_count INTEGER,
                    video_count INTEGER,
                    image_count INTEGER,
                    link_count INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    page_url TEXT,
                    type TEXT,
                    content TEXT,
                    embedding BLOB,
                    metadata TEXT
                )
            ''')
            
            # Inserir página
            conn.execute('''
                INSERT OR REPLACE INTO pages 
                (url, title, language, content, extracted_at, word_count, video_count, image_count, link_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page_data.get('url'),
                page_data.get('title'),
                page_data.get('language'),
                page_data.get('text_content'),
                page_data.get('extracted_at'),
                page_data.get('word_count', 0),
                len(page_data.get('videos', [])),
                len(page_data.get('images', [])),
                len(page_data.get('links', []))
            ))
            
            # Inserir chunks
            for chunk in chunks:
                embedding_blob = None
                if chunk.get('embedding'):
                    import numpy as np
                    embedding_blob = np.array(chunk['embedding']).tobytes()
                
                conn.execute('''
                    INSERT OR REPLACE INTO chunks
                    (id, page_url, type, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    chunk['id'],
                    chunk.get('source_url'),
                    chunk['type'],
                    chunk['content'],
                    embedding_blob,
                    json.dumps(chunk.get('metadata', {}))
                ))
            
            conn.commit()

def main():
    """Função principal para teste avançado"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Scraper with Video Processing')
    parser.add_argument('--url', required=True, help='URL para extrair')
    parser.add_argument('--selenium', action='store_true', help='Usar Selenium')
    parser.add_argument('--process-videos', action='store_true', help='Processar vídeos encontrados')
    parser.add_argument('--output', default='web_scraping_storage', help='Pasta de saída')
    
    args = parser.parse_args()
    
    # Criar scraper
    scraper = WebScraperWithVideoProcessing(args.output)
    
    # Extrair página
    print(f"Extraindo conteúdo de: {args.url}")
    page_data = scraper.extract_page_content(args.url, args.selenium)
    
    # Processar vídeos se solicitado
    if args.process_videos and page_data.get('videos'):
        print("Processando vídeos encontrados...")
        page_data = scraper.process_videos_from_page(page_data)
    
    # Criar chunks RAG
    print("Criando chunks RAG...")
    chunks = scraper.create_chunks_from_content(page_data)
    
    # Salvar no banco de dados
    print("Salvando no banco de dados...")
    scraper.save_to_database(page_data, chunks)
    
    # Salvar resultado completo
    output_file = scraper.storage_path / f"complete_extraction_{int(time.time())}.json"
    complete_data = {
        'page_data': page_data,
        'chunks': chunks,
        'summary': {
            'url': page_data.get('url'),
            'title': page_data.get('title'),
            'language': page_data.get('language'),
            'word_count': page_data.get('word_count', 0),
            'videos_found': len(page_data.get('videos', [])),
            'videos_processed': len([v for v in page_data.get('videos', []) if v.get('transcript')]),
            'chunks_created': len(chunks),
            'processing_time': datetime.now().isoformat()
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Extração completa concluída!")
    print(f"📄 Resultado salvo em: {output_file}")
    print(f"🎯 Resumo:")
    print(f"   - Título: {page_data.get('title', 'N/A')}")
    print(f"   - Idioma: {page_data.get('language', 'N/A')}")
    print(f"   - Palavras: {page_data.get('word_count', 0)}")
    print(f"   - Vídeos encontrados: {len(page_data.get('videos', []))}")
    print(f"   - Vídeos transcritos: {len([v for v in page_data.get('videos', []) if v.get('transcript')])}")
    print(f"   - Chunks criados: {len(chunks)}")
    print(f"   - Banco de dados: {scraper.storage_path / 'web_scraping.db'}")

if __name__ == "__main__":
    import time
    main()
