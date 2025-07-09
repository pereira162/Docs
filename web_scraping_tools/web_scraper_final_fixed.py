#!/usr/bin/env python3
"""
🎯 EXTRATOR WEB SIMPLIFICADO COM DETECÇÃO DE IDIOMA
==================================================
Sistema simplificado que:
1. Extrai conteúdo de sites usando requests
2. Detecta idioma automaticamente 
3. Baixa e transcreve vídeos com idioma correto
4. Gera chunks RAG unificados
"""

import json
import os
import re
import time
import requests
import subprocess
import sys
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib

# Imports para web scraping
try:
    from bs4 import BeautifulSoup
    import whisper
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Execute: pip install beautifulsoup4 openai-whisper")
    sys.exit(1)

class LanguageDetector:
    """
    🌍 Detector de idioma inteligente
    """
    
    @staticmethod
    def detect_page_language(url: str, html_content: str, page_title: str = "") -> str:
        """
        Detecta idioma da página usando múltiplas estratégias
        """
        language = "en"  # Padrão inglês
        
        # 1. Detecta pelo URL
        if "/ENU/" in url or "/en/" in url.lower() or "/en-us/" in url.lower():
            language = "en"
        elif "/PTB/" in url or "/pt/" in url.lower() or "/pt-br/" in url.lower():
            language = "pt"
        elif "/ESP/" in url or "/es/" in url.lower():
            language = "es"
        elif "/FRA/" in url or "/fr/" in url.lower():
            language = "fr"
        elif "/DEU/" in url or "/de/" in url.lower():
            language = "de"
        
        # 2. Detecta pelo HTML lang attribute
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                lang_attr = html_tag.get('lang').lower()
                if lang_attr.startswith('en'):
                    language = "en"
                elif lang_attr.startswith('pt'):
                    language = "pt"
                elif lang_attr.startswith('es'):
                    language = "es"
                elif lang_attr.startswith('fr'):
                    language = "fr"
                elif lang_attr.startswith('de'):
                    language = "de"
        except:
            pass
        
        print(f"🌍 Idioma detectado: {language} (URL: {url[:50]}...)")
        return language
    
    @staticmethod
    def get_whisper_language_code(detected_lang: str) -> str:
        """
        Converte código de idioma para formato Whisper
        """
        lang_map = {
            "en": "en",
            "pt": "pt", 
            "es": "es",
            "fr": "fr",
            "de": "de"
        }
        return lang_map.get(detected_lang, "en")

class VideoTranscriptionExtractor:
    """
    🎤 Extrator de transcrição de vídeos com detecção de idioma
    """
    
    def __init__(self, output_dir: str = "videos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configuração do FFmpeg
        self.ffmpeg_path = self._find_ffmpeg()
        
        # Modelo Whisper
        self.whisper_model = None
        self._load_whisper()
        
        print(f"🎥 VideoTranscriptionExtractor inicializado")
        print(f"📁 Diretório de transcrições: {output_dir}")
    
    def _find_ffmpeg(self) -> str:
        """Encontra o executável do FFmpeg"""
        possible_paths = [
            "ffmpeg",
            r"C:\Users\lucas\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "-version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ FFmpeg encontrado: {path}")
                    return path
            except:
                continue
        
        print("❌ FFmpeg não encontrado!")
        return "ffmpeg"
    
    def _load_whisper(self):
        """Carrega modelo Whisper"""
        try:
            self.whisper_model = whisper.load_model("base")
            print(f"🎤 Whisper disponível: {self.whisper_model is not None}")
        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            self.whisper_model = None
    
    def transcribe_video(self, video_path: str, video_id: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """Transcreve vídeo usando Whisper com idioma específico"""
        if not self.whisper_model:
            print("❌ Whisper não disponível")
            return None
        
        transcript_file = os.path.join(self.output_dir, f"{video_id}_transcript.json")
        
        if os.path.exists(transcript_file):
            print(f"✅ Transcrição já existe: {transcript_file}")
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        try:
            print(f"🎤 Transcrevendo vídeo: {video_id}")
            print(f"🌍 Idioma: {language}")
            
            # Configura FFmpeg
            os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
            
            # Transcreve com idioma específico
            whisper_lang = LanguageDetector.get_whisper_language_code(language)
            result = self.whisper_model.transcribe(
                video_path, 
                language=whisper_lang,
                fp16=False
            )
            
            transcript_data = {
                "video_id": video_id,
                "text": result["text"],
                "language": result["language"],
                "detected_language": language,
                "segments": result["segments"],
                "transcribed_at": datetime.now().isoformat()
            }
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Transcrição concluída: {len(result['segments'])} segmentos")
            print(f"📝 Texto total: {len(result['text'])} caracteres")
            
            return transcript_data
            
        except Exception as e:
            print(f"❌ Erro na transcrição de {video_id}: {e}")
            return None

class SimpleWebScraperWithVideo:
    """
    🕷️ Web scraper simplificado com extração de vídeos
    """
    
    def __init__(self, output_dir: str = "autodesk_extraction_simple"):
        self.output_dir = output_dir
        self.videos_dir = os.path.join(output_dir, "videos")
        
        os.makedirs(self.videos_dir, exist_ok=True)
        
        self.video_extractor = VideoTranscriptionExtractor(self.videos_dir)
        self.extracted_pages = []
        self.all_chunks = []
        
        # Sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        print(f"🚀 SimpleWebScraperWithVideo inicializado")
        print(f"📁 Diretório: {output_dir}")
    
    def get_page_content(self, url: str) -> Tuple[str, str]:
        """Obtém conteúdo da página"""
        try:
            print(f"🌐 Acessando: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.get_text() if soup.title else ""
            
            return response.text, title
            
        except Exception as e:
            print(f"❌ Erro ao acessar {url}: {e}")
            return "", ""
    
    def extract_videos_from_page(self, html_content: str, page_url: str) -> List[Dict[str, Any]]:
        """Extrai informações de vídeos da página"""
        videos = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Padrões de vídeo Autodesk
        video_patterns = [
            {'selector': '[data-video-id]', 'attr': 'data-video-id', 'type': 'video_direct'},
            {'selector': '.vjsalt-poster[style*="background-image"]', 'attr': 'style', 'type': 'poster_detected'},
        ]
        
        for pattern in video_patterns:
            elements = soup.select(pattern['selector'])
            for element in elements:
                try:
                    if pattern['type'] == 'poster_detected':
                        style = element.get('style', '')
                        id_match = re.search(r'([a-f0-9-]{36})', style)
                        if id_match:
                            video_id = id_match.group(1)
                        else:
                            continue
                    else:
                        video_id = element.get(pattern['attr'])
                        if not video_id:
                            continue
                    
                    video_info = {
                        'video_id': video_id,
                        'source_url': page_url,
                        'detection_type': pattern['type']
                    }
                    
                    videos.append(video_info)
                    
                except Exception as e:
                    continue
        
        # Remove duplicatas
        unique_videos = []
        seen_ids = set()
        for video in videos:
            if video['video_id'] not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video['video_id'])
        
        return unique_videos
    
    def download_video(self, video_id: str) -> Optional[str]:
        """Baixa vídeo usando ID"""
        video_path = os.path.join(self.videos_dir, f"{video_id}.mp4")
        
        if os.path.exists(video_path):
            print(f"✅ Vídeo já existe: {video_path}")
            return video_path
        
        try:
            video_url = f"https://damassets.autodesk.net/content/dam/autodesk/www/videos/{video_id}.mp4"
            print(f"📥 Baixando vídeo: {video_id}")
            
            response = self.session.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(video_path)
            if file_size > 1000:
                print(f"✅ Vídeo baixado: {video_path} ({file_size / 1024 / 1024:.1f} MB)")
                return video_path
            else:
                os.remove(video_path)
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo {video_id}: {e}")
            return None
    
    def process_video_complete(self, video_info: Dict[str, Any], page_language: str) -> List[Dict[str, Any]]:
        """Processa vídeo completo: download + transcrição + chunks"""
        video_id = video_info['video_id']
        source_url = video_info['source_url']
        
        print(f"🎬 Processando vídeo: {video_id}")
        
        # Download
        video_path = self.download_video(video_id)
        if not video_path:
            return []
        
        # Transcrição com idioma da página
        transcript = self.video_extractor.transcribe_video(video_path, video_id, page_language)
        if not transcript:
            return []
        
        # Cria chunks
        chunks = []
        for i, segment in enumerate(transcript['segments']):
            chunk = {
                "id": f"{video_id}#video_segment_{i}",
                "text": segment['text'].strip(),
                "type": "video_transcript",
                "metadata": {
                    "video_id": video_id,
                    "source_url": source_url,
                    "segment_id": segment['id'],
                    "start_time": segment['start'],
                    "end_time": segment['end'],
                    "language": transcript['language'],
                    "detected_language": page_language,
                    "chunk_index": i,
                    "extracted_at": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        print(f"✅ Vídeo processado: {len(chunks)} chunks criados")
        return chunks
    
    def extract_text_content(self, html_content: str, url: str, title: str) -> List[Dict[str, Any]]:
        """Extrai e chunka conteúdo de texto"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove elementos desnecessários
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = re.sub(r'\s+', ' ', text_content)
        
        if len(text_content) < 100:
            return []
        
        # Chunking simples
        chunks = []
        paragraphs = text_content.split('. ')
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > 1000:
                if current_chunk:
                    chunk = {
                        "id": f"{url}#text_chunk_{chunk_index}",
                        "text": current_chunk.strip(),
                        "type": "text_content",
                        "metadata": {
                            "source_url": url,
                            "page_title": title,
                            "chunk_index": chunk_index,
                            "extracted_at": datetime.now().isoformat()
                        }
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = paragraph
            else:
                current_chunk += ". " + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunk = {
                "id": f"{url}#text_chunk_{chunk_index}",
                "text": current_chunk.strip(),
                "type": "text_content",
                "metadata": {
                    "source_url": url,
                    "page_title": title,
                    "chunk_index": chunk_index,
                    "extracted_at": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def extract_single_page(self, url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extrai uma única página"""
        try:
            print(f"📄 Processando: {url}")
            
            html_content, title = self.get_page_content(url)
            if not html_content:
                return [], []
            
            print(f"📊 HTML obtido: {len(html_content)} chars")
            
            # Detecta idioma
            page_language = LanguageDetector.detect_page_language(url, html_content, title)
            
            # Extrai vídeos
            videos_found = self.extract_videos_from_page(html_content, url)
            video_chunks = []
            
            print(f"🎥 Vídeos encontrados: {len(videos_found)}")
            for video in videos_found:
                print(f"   📹 {video['video_id']} ({video['detection_type']})")
            
            # Processa vídeos
            for video_info in videos_found:
                video_chunks.extend(
                    self.process_video_complete(video_info, page_language)
                )
            
            # Extrai texto
            text_chunks = self.extract_text_content(html_content, url, title)
            
            # Salva dados da página
            page_data = {
                "url": url,
                "title": title,
                "language": page_language,
                "videos": videos_found,
                "text_chunks_count": len(text_chunks),
                "video_chunks_count": len(video_chunks),
                "extracted_at": datetime.now().isoformat()
            }
            
            self.extracted_pages.append(page_data)
            
            print(f"✅ Página processada: {len(text_chunks)} texto + {len(video_chunks)} vídeo chunks")
            
            return text_chunks, video_chunks
            
        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")
            return [], []
    
    def extract_autodesk_pages(self, urls: List[str]):
        """Extrai múltiplas páginas do Autodesk"""
        print(f"🎯 EXTRAÇÃO AUTODESK COM DETECÇÃO DE IDIOMA")
        print("=" * 60)
        print(f"📄 Páginas para processar: {len(urls)}")
        
        start_time = time.time()
        
        for url in urls:
            text_chunks, video_chunks = self.extract_single_page(url)
            self.all_chunks.extend(text_chunks)
            self.all_chunks.extend(video_chunks)
        
        end_time = time.time()
        
        # Salva dados finais
        self.save_extraction_data(end_time - start_time)
        
        return {
            "pages": len(self.extracted_pages),
            "videos": sum(len(page['videos']) for page in self.extracted_pages),
            "text_chunks": len([c for c in self.all_chunks if c['type'] == 'text_content']),
            "video_chunks": len([c for c in self.all_chunks if c['type'] == 'video_transcript']),
            "total_chars": sum(len(c['text']) for c in self.all_chunks),
            "duration": end_time - start_time
        }
    
    def save_extraction_data(self, duration: float):
        """Salva dados extraídos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Dados finais
        final_data = {
            "extraction_info": {
                "timestamp": timestamp,
                "pages": len(self.extracted_pages),
                "total_chunks": len(self.all_chunks),
                "duration": duration
            },
            "pages": self.extracted_pages,
            "chunks": self.all_chunks
        }
        
        output_file = os.path.join(self.output_dir, f"extraction_complete_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dados salvos: {output_file}")

def main():
    """Teste do sistema"""
    print("🎯 TESTE SISTEMA CORRIGIDO COM DETECÇÃO DE IDIOMA")
    print("=" * 60)
    
    # URLs de teste (sites em inglês)
    test_urls = [
        "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-WhatsNew/files/GUID-B7040851-266C-48CB-9682-654F3A6B8086.htm",
        "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-WhatsNew/files/GUID-0E96BDF7-DE27-4C35-A78B-800F535DAA84.htm",
        "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-Architecture/files/GUID-87DAB120-05C8-414A-A6C0-1AC6BCCFDBEF.htm"
    ]
    
    # Remove dados antigos
    import shutil
    output_dir = "test_final_fixed"
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            print(f"🗑️ Dados antigos removidos")
        except:
            pass
    
    # Cria scraper
    scraper = SimpleWebScraperWithVideo(output_dir)
    
    # Executa extração
    results = scraper.extract_autodesk_pages(test_urls)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   📄 Páginas: {results['pages']}")
    print(f"   🎥 Vídeos: {results['videos']}")
    print(f"   📝 Chunks texto: {results['text_chunks']}")
    print(f"   🎬 Chunks vídeo: {results['video_chunks']}")
    print(f"   📊 Total chars: {results['total_chars']:,}")
    print(f"   ⏱️ Tempo: {results['duration']:.1f}s")

if __name__ == "__main__":
    main()
