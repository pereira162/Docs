#!/usr/bin/env python3
"""
🎯 EXTRATOR WEB AVANÇADO COM VÍDEOS E DETECÇÃO DE IDIOMA
========================================================
Sistema completo que:
1. Extrai conteúdo de sites dinâmicos com SeleniumBase
2. Detecta vídeos embedded automaticamente
3. Baixa e transcreve vídeos com DETECÇÃO AUTOMÁTICA DE IDIOMA
4. Gera chunks RAG unificados para busca
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
    from seleniumbase import BaseCase
    from bs4 import BeautifulSoup
    import whisper
    # import ffmpeg  # Removido pois não é necessário importar diretamente
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Execute: pip install seleniumbase beautifulsoup4 openai-whisper ffmpeg-python")
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
        
        # 3. Detecta por palavras-chave no conteúdo
        content_lower = (html_content + " " + page_title).lower()
        
        # Palavras típicas em inglês
        english_words = ['the', 'and', 'for', 'with', 'this', 'that', 'help', 'guide', 'tutorial']
        english_count = sum(1 for word in english_words if word in content_lower)
        
        # Palavras típicas em português
        portuguese_words = ['para', 'com', 'sobre', 'como', 'esse', 'essa', 'ajuda', 'guia', 'tutorial']
        portuguese_count = sum(1 for word in portuguese_words if word in content_lower)
        
        if portuguese_count > english_count:
            language = "pt"
        
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
        """
        Inicializa o extrator de transcrições
        """
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
        """
        Encontra o executável do FFmpeg
        """
        # Caminhos possíveis do FFmpeg
        possible_paths = [
            "ffmpeg",  # Se estiver no PATH
            r"C:\Users\lucas\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "-version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ FFmpeg encontrado: {path}")
                    return path
            except:
                continue
        
        print("❌ FFmpeg não encontrado! Instale com: winget install Gyan.FFmpeg")
        return "ffmpeg"  # Fallback
    
    def _load_whisper(self):
        """
        Carrega modelo Whisper
        """
        try:
            self.whisper_model = whisper.load_model("base")
            print(f"🎤 Whisper disponível: {self.whisper_model is not None}")
        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            self.whisper_model = None
    
    def transcribe_video(self, video_path: str, video_id: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Transcreve vídeo usando Whisper com idioma específico
        """
        if not self.whisper_model:
            print("❌ Whisper não disponível")
            return None
        
        transcript_file = os.path.join(self.output_dir, f"{video_id}_transcript.json")
        
        # Verifica se já existe
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
            print(f"🔧 Usando FFmpeg: {self.ffmpeg_path}")
            
            # Configura FFmpeg no ambiente para Whisper
            os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
            
            # Transcreve com idioma específico
            whisper_lang = LanguageDetector.get_whisper_language_code(language)
            result = self.whisper_model.transcribe(
                video_path, 
                language=whisper_lang,
                fp16=False  # Para compatibilidade CPU
            )
            
            # Prepara dados da transcrição
            transcript_data = {
                "video_id": video_id,
                "text": result["text"],
                "language": result["language"],
                "detected_language": language,
                "segments": result["segments"],
                "transcribed_at": datetime.now().isoformat()
            }
            
            # Salva transcrição
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Transcrição concluída: {len(result['segments'])} segmentos")
            print(f"📝 Texto total: {len(result['text'])} caracteres")
            
            return transcript_data
            
        except Exception as e:
            print(f"❌ Erro na transcrição de {video_id}: {e}")
            return None

class AdvancedWebScraperWithVideo:
    """
    🕷️ Web scraper avançado com extração de vídeos e detecção de idioma
    """
    
    def __init__(self, output_dir: str = "autodesk_extraction"):
        """
        Inicializa o scraper
        """
        self.output_dir = output_dir
        self.pages_dir = os.path.join(output_dir, "pages")
        self.videos_dir = os.path.join(output_dir, "videos")
        
        # Cria diretórios
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        
        # Componentes
        self.video_extractor = VideoTranscriptionExtractor(self.videos_dir)
        
        # Dados
        self.extracted_pages = []
        self.extracted_videos = []
        self.all_chunks = []
        
        # Inicializa browser
        self.browser = None
        self._init_browser()
        
        print(f"🚀 AdvancedWebScraperWithVideo inicializado")
        print(f"📁 Diretório principal: {output_dir}")
        print(f"📄 Páginas: {self.pages_dir}")
        print(f"🎥 Vídeos: {self.videos_dir}")
    
    def _init_browser(self):
        """
        Inicializa browser SeleniumBase
        """
        from seleniumbase import Driver
        
        try:
            self.browser = Driver(
                browser="chrome",
                headless=True,
                incognito=True,
                block_images=True,
                ad_block_on=True
            )
            print("🌐 Browser inicializado")
        except Exception as e:
            print(f"❌ Erro ao inicializar browser: {e}")
            self.browser = None
    
    def get_page_content(self, url: str) -> Tuple[str, str]:
        """
        Obtém conteúdo da página
        """
        if not self.browser:
            raise Exception("Browser não inicializado")
        
        try:
            self.browser.get(url)
            time.sleep(2)
            
            html_content = self.browser.page_source
            title = self.browser.title
            
            return html_content, title
            
        except Exception as e:
            print(f"❌ Erro ao acessar {url}: {e}")
            return "", ""
    
    def extract_videos_from_page(self, html_content: str, page_url: str) -> List[Dict[str, Any]]:
        """
        Extrai informações de vídeos da página
        """
        videos = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Padrões de vídeo Autodesk
        video_patterns = [
            # Video direto com data-video-id
            {'selector': '[data-video-id]', 'attr': 'data-video-id', 'type': 'video_direct'},
            # Poster com background-image
            {'selector': '.vjsalt-poster[style*="background-image"]', 'attr': 'style', 'type': 'poster_detected'},
            # Player de vídeo
            {'selector': '.video-player[data-video-id]', 'attr': 'data-video-id', 'type': 'video_player'},
        ]
        
        for pattern in video_patterns:
            elements = soup.select(pattern['selector'])
            for element in elements:
                try:
                    if pattern['type'] == 'poster_detected':
                        # Extrai ID do style background-image
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
                        'detection_type': pattern['type'],
                        'element': str(element)[:200]
                    }
                    
                    videos.append(video_info)
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar vídeo: {e}")
                    continue
        
        # Remove duplicatas por video_id
        unique_videos = []
        seen_ids = set()
        for video in videos:
            if video['video_id'] not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video['video_id'])
        
        return unique_videos
    
    def download_video(self, video_id: str) -> Optional[str]:
        """
        Baixa vídeo usando ID
        """
        video_path = os.path.join(self.videos_dir, f"{video_id}.mp4")
        
        # Verifica se já existe
        if os.path.exists(video_path):
            print(f"✅ Vídeo já existe: {video_path}")
            return video_path
        
        try:
            # URL do vídeo Autodesk
            video_url = f"https://damassets.autodesk.net/content/dam/autodesk/www/videos/{video_id}.mp4"
            
            print(f"📥 Baixando vídeo: {video_id}")
            
            # Baixa vídeo
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Salva arquivo
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verifica tamanho
            file_size = os.path.getsize(video_path)
            if file_size > 1000:  # Pelo menos 1KB
                print(f"✅ Vídeo baixado: {video_path} ({file_size / 1024 / 1024:.1f} MB)")
                return video_path
            else:
                os.remove(video_path)
                print(f"❌ Arquivo muito pequeno, removido: {video_path}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo {video_id}: {e}")
            return None
    
    def process_video_complete(self, video_info: Dict[str, Any], page_language: str) -> List[Dict[str, Any]]:
        """
        Processa vídeo completo: download + transcrição + chunks
        """
        video_id = video_info['video_id']
        source_url = video_info['source_url']
        
        print(f"🎬 Processando vídeo completo: {video_id}")
        
        # 1. Baixa vídeo
        video_path = self.download_video(video_id)
        if not video_path:
            return []
        
        # 2. Transcreve vídeo com idioma da página
        transcript = self.video_extractor.transcribe_video(video_path, video_id, page_language)
        if not transcript:
            return []
        
        # 3. Cria chunks de vídeo
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
                    "video_file": os.path.basename(video_path),
                    "extracted_at": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        print(f"✅ Vídeo processado: {len(chunks)} chunks criados")
        return chunks
    
    def extract_text_content(self, html_content: str, url: str, title: str) -> List[Dict[str, Any]]:
        """
        Extrai e chunka conteúdo de texto
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove elementos desnecessários
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Extrai texto
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = re.sub(r'\s+', ' ', text_content)
        
        if len(text_content) < 100:
            return []
        
        # Chunking simples por parágrafos
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
                            "chunk_type": "text",
                            "extracted_at": datetime.now().isoformat(),
                            "url": url,
                            "title": title,
                            "domain": urlparse(url).netloc,
                            "content_length": len(text_content),
                            "readability_score": len(text_content.split()) / len(text_content) * 1000
                        }
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = paragraph
            else:
                current_chunk += ". " + paragraph if current_chunk else paragraph
        
        # Adiciona último chunk
        if current_chunk:
            chunk = {
                "id": f"{url}#text_chunk_{chunk_index}",
                "text": current_chunk.strip(),
                "type": "text_content",
                "metadata": {
                    "source_url": url,
                    "page_title": title,
                    "chunk_index": chunk_index,
                    "chunk_type": "text",
                    "extracted_at": datetime.now().isoformat(),
                    "url": url,
                    "title": title,
                    "domain": urlparse(url).netloc,
                    "content_length": len(text_content),
                    "readability_score": len(text_content.split()) / len(text_content) * 1000
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def extract_single_page(self, url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extrai uma única página (texto + vídeos)
        """
        try:
            print(f"📄 Processando [{len(self.extracted_pages)}]: {url}")
            
            # Obtém conteúdo
            html_content, title = self.get_page_content(url)
            if not html_content:
                return [], []
            
            print(f"📊 HTML obtido: {len(html_content)} chars")
            
            # Detecta idioma da página
            page_language = LanguageDetector.detect_page_language(url, html_content, title)
            
            # Extrai vídeos
            videos_found = self.extract_videos_from_page(html_content, url)
            video_chunks = []
            
            print(f"🎥 Vídeos encontrados na página: {len(videos_found)}")
            for video in videos_found:
                print(f"   📹 {video['video_id']} ({video['detection_type']})")
            
            # Processa cada vídeo
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
                "text_content": BeautifulSoup(html_content, 'html.parser').get_text(separator=' ', strip=True),
                "text_chunks": [
                    {
                        "text": chunk["text"],
                        "start_index": 0,
                        "word_count": len(chunk["text"].split()),
                        "char_count": len(chunk["text"]),
                        "chunk_type": "text_content"
                    } for chunk in text_chunks
                ],
                "videos": videos_found,
                "video_chunks": [
                    {
                        "video_id": chunk["metadata"]["video_id"],
                        "text": chunk["text"],
                        "start_time": chunk["metadata"]["start_time"],
                        "end_time": chunk["metadata"]["end_time"],
                        "chunk_type": "video_transcript"
                    } for chunk in video_chunks
                ],
                "extracted_at": datetime.now().isoformat()
            }
            
            self.extracted_pages.append(page_data)
            
            print(f"✅ Página processada: {len(text_chunks)} chunks texto + {len(videos_found)} vídeos")
            
            return text_chunks, video_chunks
            
        except Exception as e:
            print(f"❌ Erro ao processar página {url}: {e}")
            return [], []
    
    def find_links(self, url: str) -> List[str]:
        """
        Encontra links na página atual
        """
        try:
            if not self.browser:
                return []
            
            # Encontra todos os links
            links = self.browser.find_elements("tag name", "a")
            found_links = []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        full_url = urljoin(url, href)
                        # Filtra apenas links relevantes do Autodesk
                        if ("help.autodesk.com" in full_url and 
                            "cloudhelp" in full_url and
                            full_url != url):
                            found_links.append(full_url)
                except:
                    continue
            
            # Remove duplicatas
            unique_links = list(set(found_links))
            print(f"🔗 Encontrados {len(unique_links)} links")
            
            return unique_links
            
        except Exception as e:
            print(f"❌ Erro ao encontrar links: {e}")
            return []
    
    def quit(self):
        """
        Fecha o browser
        """
        if self.browser:
            try:
                self.browser.quit()
                print("🔒 Browser fechado")
            except:
                pass
    
    def crawl_autodesk_site(self, start_url: str, max_pages: int = 15, depth: int = 2):
        """
        Crawling completo do site Autodesk
        """
        print(f"🎯 EXTRAÇÃO COMPLETA DO SITE AUTODESK")
        print("=" * 60)
        print(f"🌐 URL inicial: {start_url}")
        print(f"📊 Configurações: depth={depth}, max_pages={max_pages}")
        print(f"🎥 Transcrição de vídeos: True")
        
        start_time = time.time()
        
        # Fila de URLs para processar
        urls_to_process = [start_url]
        processed_urls = set()
        
        current_depth = 0
        
        while urls_to_process and len(self.extracted_pages) < max_pages and current_depth < depth:
            current_urls = urls_to_process.copy()
            urls_to_process = []
            
            for url in current_urls:
                if url in processed_urls or len(self.extracted_pages) >= max_pages:
                    continue
                
                # Processa página
                text_chunks, video_chunks = self.extract_single_page(url)
                
                # Adiciona chunks
                self.all_chunks.extend(text_chunks)
                self.all_chunks.extend(video_chunks)
                
                processed_urls.add(url)
                
                # Encontra novos links se ainda não atingiu profundidade máxima
                if current_depth < depth - 1:
                    new_links = self.find_links(url)
                    for link in new_links:
                        if link not in processed_urls:
                            urls_to_process.append(link)
            
            current_depth += 1
        
        end_time = time.time()
        
        print(f"🎯 Crawling concluído: {len(self.extracted_pages)} páginas processadas")
        
        # Salva dados
        self.save_extraction_data(start_url, end_time - start_time)
        
        return {
            "pages": len(self.extracted_pages),
            "videos": len([v for page in self.extracted_pages for v in page['videos']]),
            "text_chunks": len([c for c in self.all_chunks if c['type'] == 'text_content']),
            "video_chunks": len([c for c in self.all_chunks if c['type'] == 'video_transcript']),
            "total_chars": sum(len(c['text']) for c in self.all_chunks),
            "duration": end_time - start_time
        }
    
    def save_extraction_data(self, start_url: str, duration: float):
        """
        Salva todos os dados extraídos
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Dados das páginas
        pages_data = {
            "extraction_info": {
                "start_url": start_url,
                "timestamp": timestamp,
                "pages_processed": len(self.extracted_pages),
                "videos_processed": len([v for page in self.extracted_pages for v in page['videos']]),
                "total_duration": duration
            },
            "pages": self.extracted_pages
        }
        
        pages_file = os.path.join(self.output_dir, f"pages_complete_{timestamp}.json")
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)
        
        # Dados dos vídeos
        all_videos = []
        for page in self.extracted_pages:
            for video in page['videos']:
                video['source_page'] = page['url']
                video['page_title'] = page['title']
                video['page_language'] = page.get('language', 'en')
                all_videos.append(video)
        
        videos_data = {
            "extraction_info": {
                "timestamp": timestamp,
                "total_videos": len(all_videos)
            },
            "videos": all_videos
        }
        
        videos_file = os.path.join(self.output_dir, f"videos_complete_{timestamp}.json")
        with open(videos_file, 'w', encoding='utf-8') as f:
            json.dump(videos_data, f, ensure_ascii=False, indent=2)
        
        # Chunks RAG unificados
        chunks_data = {
            "extraction_info": {
                "timestamp": timestamp,
                "total_chunks": len(self.all_chunks),
                "text_chunks": len([c for c in self.all_chunks if c['type'] == 'text_content']),
                "video_chunks": len([c for c in self.all_chunks if c['type'] == 'video_transcript'])
            },
            "chunks": self.all_chunks
        }
        
        chunks_file = os.path.join(self.output_dir, f"all_chunks_rag_{timestamp}.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"💾 DADOS SALVOS:")
        print(f"   📄 Páginas completas: {pages_file}")
        print(f"   🎥 Vídeos completos: {videos_file}")
        print(f"   🔥 Chunks RAG unificados: {chunks_file}")

def main():
    """
    Teste do sistema completo
    """
    print("🎯 TESTE DO EXTRATOR COMPLETO COM VÍDEOS E DETECÇÃO DE IDIOMA")
    print("=" * 70)
    
    # Configuração
    output_dir = "test_complete_autodesk_fixed"
    
    # Remove diretório anterior se existir
    import shutil
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"🗑️ Diretório anterior removido: {output_dir}")
    
    # Cria scraper
    scraper = AdvancedWebScraperWithVideo(output_dir)
    
    try:
        # Executa crawling
        results = scraper.crawl_autodesk_site(
            start_url="https://help.autodesk.com/view/ARCHDESK/2024/ENU/",
            max_pages=15,
            depth=2
        )
        
        print(f"\n📊 RESULTADO COMPLETO:")
        print(f"   📄 Páginas: {results['pages']}")
        print(f"   🎥 Vídeos: {results['videos']}")
        print(f"   🔥 Chunks texto: {results['text_chunks']}")
        print(f"   🎬 Chunks vídeo: {results['video_chunks']}")
        print(f"   📊 Total chars: {results['total_chars']:,}")
        print(f"   🕒 Tempo total: {results['duration']:.1f}s")
        
    finally:
        scraper.quit()

if __name__ == "__main__":
    main()
