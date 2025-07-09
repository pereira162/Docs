"""
Sistema Avançado de Extração Web com Transcrição de Vídeos
==========================================================

Este módulo implementa extração completa de sites com:
- Detecção automática de vídeos
- Download e transcrição usando Whisper
- Extração massiva de conteúdo
- Integração RAG com conteúdo de vídeo

Funcionalidades específicas para Autodesk:
- Detecção de vídeos com data-video-id
- Download de MP4/WebM
- Transcrição com timestamps
- Chunks de vídeo integrados ao RAG
"""

import os
import time
import json
import requests
import traceback
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
import subprocess
import tempfile
from bs4 import BeautifulSoup
import textstat

# Configurações específicas para vídeos Autodesk
AUTODESK_VIDEO_CONFIGS = {
    'video_selectors': [
        'video[data-video-id]',
        '.vjsalt-poster[style*="background-image"]',
        'div[data-video-id]',
        '[data-video-processed]'
    ],
    'video_url_patterns': [
        r'https://help\.autodesk\.com/videos/([^/]+)/video\.(mp4|webm)',
        r'data-video-id="([^"]+)"',
        r'background-image:\s*url\(["\']?([^"\']+poster[^"\']*)["\']?\)'
    ],
    'transcript_selectors': [
        '.video-transcript',
        '.captions',
        '.subtitles',
        '.transcript-content'
    ]
}

class VideoTranscriptionExtractor:
    """Classe para transcrição de vídeos usando Whisper"""
    
    def __init__(self, output_dir="video_transcripts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verificar se Whisper está disponível
        self.whisper_available = self._check_whisper_installation()
        
        print(f"🎥 VideoTranscriptionExtractor inicializado")
        print(f"📁 Diretório de transcrições: {self.output_dir}")
        print(f"🎤 Whisper disponível: {self.whisper_available}")
    
    def _check_whisper_installation(self):
        """Verifica se o Whisper está instalado"""
        try:
            import whisper
            return True
        except ImportError:
            print("⚠️ Whisper não encontrado. Instalando...")
            try:
                subprocess.run(['pip', 'install', 'openai-whisper'], check=True, capture_output=True)
                import whisper
                return True
            except Exception as e:
                print(f"❌ Erro ao instalar Whisper: {e}")
                return False
    
    def download_video(self, video_url, video_id):
        """Download de vídeo"""
        try:
            print(f"📥 Baixando vídeo: {video_id}")
            
            # Arquivo de destino
            video_file = self.output_dir / f"{video_id}.mp4"
            
            if video_file.exists():
                print(f"✅ Vídeo já existe: {video_file}")
                return str(video_file)
            
            # Download
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Salvar vídeo
            with open(video_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Vídeo baixado: {video_file} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
            return str(video_file)
            
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo {video_id}: {e}")
            return None
    
    def transcribe_video(self, video_file_path, video_id):
        """Transcreve vídeo usando Whisper"""
        try:
            if not self.whisper_available:
                print(f"⚠️ Whisper não disponível para transcrever {video_id}")
                return None
            
            print(f"🎤 Transcrevendo vídeo: {video_id}")
            
            # Arquivo de transcrição
            transcript_file = self.output_dir / f"{video_id}_transcript.json"
            
            if transcript_file.exists():
                print(f"✅ Transcrição já existe: {transcript_file}")
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Configurar FFmpeg path se necessário
            import whisper
            
            # Tentar encontrar FFmpeg
            ffmpeg_paths = [
                r"C:\Users\lucas\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe",
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
            ]
            
            ffmpeg_path = None
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    ffmpeg_path = path
                    break
            
            if ffmpeg_path:
                print(f"🔧 Usando FFmpeg: {ffmpeg_path}")
                # Configurar temporariamente o PATH
                old_path = os.environ.get('PATH', '')
                ffmpeg_dir = str(Path(ffmpeg_path).parent)
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + old_path
            
            # Carregar modelo (usar modelo pequeno para velocidade)
            model = whisper.load_model("base")
            
            # Transcrever
            result = model.transcribe(video_file_path, language='pt')
            
            # Restaurar PATH
            if ffmpeg_path:
                os.environ['PATH'] = old_path
            
            # Preparar dados da transcrição
            transcript_data = {
                'video_id': video_id,
                'text': result['text'],
                'language': result['language'],
                'segments': [],
                'transcribed_at': datetime.now().isoformat()
            }
            
            # Processar segmentos com timestamps
            for segment in result['segments']:
                transcript_data['segments'].append({
                    'id': segment['id'],
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip(),
                    'tokens': segment.get('tokens', []),
                    'temperature': segment.get('temperature', 0),
                    'avg_logprob': segment.get('avg_logprob', 0),
                    'compression_ratio': segment.get('compression_ratio', 0),
                    'no_speech_prob': segment.get('no_speech_prob', 0)
                })
            
            # Salvar transcrição
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Transcrição concluída: {len(transcript_data['segments'])} segmentos")
            print(f"📝 Texto total: {len(transcript_data['text'])} caracteres")
            
            return transcript_data
            
        except Exception as e:
            print(f"❌ Erro ao transcrever vídeo {video_id}: {e}")
            traceback.print_exc()
            return None
    
    def process_video_complete(self, video_url, video_id, metadata=None):
        """Processo completo: download + transcrição"""
        try:
            print(f"🎬 Processando vídeo completo: {video_id}")
            
            # 1. Download do vídeo
            video_file = self.download_video(video_url, video_id)
            if not video_file:
                return None
            
            # 2. Transcrição
            transcript = self.transcribe_video(video_file, video_id)
            if not transcript:
                return None
            
            # 3. Criar chunks do vídeo para RAG
            video_chunks = self._create_video_chunks(transcript, metadata)
            
            # 4. Resultado completo
            result = {
                'video_id': video_id,
                'video_url': video_url,
                'video_file': video_file,
                'transcript': transcript,
                'chunks': video_chunks,
                'metadata': metadata or {},
                'processed_at': datetime.now().isoformat()
            }
            
            print(f"✅ Vídeo processado: {len(video_chunks)} chunks criados")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento completo: {e}")
            return None
    
    def _create_video_chunks(self, transcript, metadata=None, chunk_duration=30):
        """Cria chunks do vídeo baseado em duração"""
        chunks = []
        
        if not transcript or not transcript.get('segments'):
            return chunks
        
        current_chunk = {
            'start_time': 0,
            'end_time': 0,
            'text': '',
            'segment_ids': []
        }
        
        for segment in transcript['segments']:
            # Se o chunk atual ficaria muito longo, criar novo chunk
            if current_chunk['text'] and (segment['start'] - current_chunk['start_time']) > chunk_duration:
                # Finalizar chunk atual
                chunks.append(self._finalize_video_chunk(current_chunk, transcript, metadata))
                
                # Iniciar novo chunk
                current_chunk = {
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'text': segment['text'],
                    'segment_ids': [segment['id']]
                }
            else:
                # Adicionar ao chunk atual
                if not current_chunk['text']:
                    current_chunk['start_time'] = segment['start']
                
                current_chunk['end_time'] = segment['end']
                current_chunk['text'] += ' ' + segment['text']
                current_chunk['segment_ids'].append(segment['id'])
        
        # Finalizar último chunk
        if current_chunk['text']:
            chunks.append(self._finalize_video_chunk(current_chunk, transcript, metadata))
        
        return chunks
    
    def _finalize_video_chunk(self, chunk_data, transcript, metadata):
        """Finaliza um chunk de vídeo com metadados"""
        chunk_text = chunk_data['text'].strip()
        
        return {
            'text': chunk_text,
            'start_time': chunk_data['start_time'],
            'end_time': chunk_data['end_time'],
            'duration': chunk_data['end_time'] - chunk_data['start_time'],
            'segment_ids': chunk_data['segment_ids'],
            'word_count': len(chunk_text.split()),
            'char_count': len(chunk_text),
            'video_id': transcript['video_id'],
            'language': transcript.get('language', 'unknown'),
            'chunk_type': 'video_transcript',
            'metadata': metadata or {}
        }

class AdvancedWebScraperWithVideo:
    """Web Scraper avançado com suporte a extração de vídeos"""
    
    def __init__(self, output_dir="advanced_extraction"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdiretórios
        self.pages_dir = self.output_dir / "pages"
        self.videos_dir = self.output_dir / "videos"
        self.pages_dir.mkdir(exist_ok=True)
        self.videos_dir.mkdir(exist_ok=True)
        
        # Extrator de vídeo
        self.video_extractor = VideoTranscriptionExtractor(self.videos_dir)
        
        # Dados da extração
        self.extracted_pages = []
        self.extracted_videos = []
        self.processed_urls = set()
        self.failed_urls = set()
        
        # Configurações
        self.delay_between_requests = 2.0
        self.chunk_size = 512
        self.chunk_overlap = 50
        
        print(f"🚀 AdvancedWebScraperWithVideo inicializado")
        print(f"📁 Diretório principal: {self.output_dir}")
        print(f"📄 Páginas: {self.pages_dir}")
        print(f"🎥 Vídeos: {self.videos_dir}")
    
    def extract_autodesk_complete(self, start_url, max_depth=4, max_pages=100):
        """Extração completa do site Autodesk com vídeos"""
        print(f"🎯 EXTRAÇÃO COMPLETA DO SITE AUTODESK")
        print("=" * 60)
        print(f"🌐 URL inicial: {start_url}")
        print(f"📊 Configurações: depth={max_depth}, max_pages={max_pages}")
        print(f"🎥 Transcrição de vídeos: {self.video_extractor.whisper_available}")
        
        self.start_time = time.time()
        self.start_url = start_url
        
        try:
            # Usar SeleniumBase para sites dinâmicos
            from seleniumbase import SB
            
            with SB(headless=True) as sb:
                self._crawl_autodesk_with_videos(sb, start_url, max_depth, max_pages)
                
        except Exception as e:
            print(f"⚠️ Erro com SeleniumBase: {e}")
            print("🔄 Tentando com requests...")
            self._crawl_autodesk_fallback(start_url, max_depth, max_pages)
        
        # Salvar resultados
        self._save_complete_extraction()
        
        return self._get_extraction_summary()
    
    def _crawl_autodesk_with_videos(self, sb, start_url, max_depth, max_pages):
        """Crawling completo com extração de vídeos"""
        url_queue = [(start_url, 0)]
        processed_count = 0
        
        while url_queue and processed_count < max_pages:
            current_url, depth = url_queue.pop(0)
            
            if current_url in self.processed_urls or depth > max_depth:
                continue
            
            print(f"\n📄 Processando [{depth}]: {current_url}")
            
            try:
                # Navegar para página
                sb.open(current_url)
                sb.sleep(3)  # Aguardar carregamento
                
                # Aguardar elementos específicos
                try:
                    sb.wait_for_element('body', timeout=10)
                except:
                    pass
                
                # Obter conteúdo da página
                page_source = sb.get_page_source()
                page_title = sb.get_title()
                
                print(f"📊 HTML obtido: {len(page_source)} chars")
                
                # Processar página (texto + vídeos)
                page_data = self._process_page_with_videos(sb, current_url, page_source, page_title)
                
                if page_data:
                    self.extracted_pages.append(page_data)
                    self.processed_urls.add(current_url)
                    processed_count += 1
                    
                    print(f"✅ Página processada: {len(page_data.get('chunks', []))} chunks texto + {len(page_data.get('videos', []))} vídeos")
                    
                    # Buscar links para próximas páginas
                    if depth < max_depth:
                        new_links = self._extract_autodesk_links(sb, current_url)
                        print(f"🔗 Encontrados {len(new_links)} links")
                        
                        for link in new_links[:20]:  # Limitar a 20 links por página
                            if link not in self.processed_urls:
                                url_queue.append((link, depth + 1))
                
                time.sleep(self.delay_between_requests)
                
            except Exception as e:
                print(f"❌ Erro ao processar {current_url}: {e}")
                self.failed_urls.add(current_url)
        
        print(f"\n🎯 Crawling concluído: {processed_count} páginas processadas")
    
    def _process_page_with_videos(self, sb, url, html_content, page_title):
        """Processa página extraindo texto e vídeos"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Extrair conteúdo de texto (como antes)
            text_content = self._extract_text_content(soup, url, page_title)
            
            # 2. Extrair vídeos da página
            videos = self._extract_videos_from_page(sb, soup, url)
            
            # 3. Combinar dados
            page_data = {
                'url': url,
                'title': page_title,
                'text_content': text_content.get('content', ''),
                'text_chunks': text_content.get('chunks', []),
                'videos': videos,
                'video_chunks': [],
                'total_chunks': len(text_content.get('chunks', [])),
                'total_videos': len(videos),
                'extracted_at': datetime.now().isoformat(),
                'metadata': text_content.get('metadata', {})
            }
            
            # 4. Processar vídeos encontrados
            for video in videos:
                video_result = self._process_video_complete(video)
                if video_result:
                    self.extracted_videos.append(video_result)
                    page_data['video_chunks'].extend(video_result.get('chunks', []))
            
            page_data['total_chunks'] = len(page_data['text_chunks']) + len(page_data['video_chunks'])
            
            return page_data
            
        except Exception as e:
            print(f"❌ Erro ao processar página {url}: {e}")
            return None
    
    def _extract_videos_from_page(self, sb, soup, page_url):
        """Extrai informações de vídeos da página"""
        videos = []
        
        try:
            # 1. Buscar elementos de vídeo diretos
            video_elements = soup.find_all('video', {'data-video-id': True})
            
            for video_elem in video_elements:
                video_id = video_elem.get('data-video-id')
                if video_id:
                    # Buscar sources do vídeo
                    sources = video_elem.find_all('source')
                    video_urls = []
                    
                    for source in sources:
                        src = source.get('src')
                        if src and ('mp4' in src or 'webm' in src):
                            video_urls.append({
                                'url': src,
                                'type': source.get('type', 'unknown')
                            })
                    
                    if video_urls:
                        videos.append({
                            'video_id': video_id,
                            'sources': video_urls,
                            'poster': video_elem.get('poster'),
                            'page_url': page_url,
                            'element_type': 'video_direct'
                        })
            
            # 2. Buscar posters de vídeo (que podem indicar vídeos)
            poster_elements = soup.find_all('div', class_='vjsalt-poster')
            
            for poster_elem in poster_elements:
                style = poster_elem.get('style', '')
                if 'background-image' in style and 'poster' in style:
                    # Extrair ID do vídeo da URL do poster
                    import re
                    video_id_match = re.search(r'videos/([^/]+)/poster', style)
                    if video_id_match:
                        video_id = video_id_match.group(1)
                        
                        # Construir URLs do vídeo baseado no padrão Autodesk
                        video_base_url = f"https://help.autodesk.com/videos/{video_id}"
                        
                        videos.append({
                            'video_id': video_id,
                            'sources': [
                                {'url': f"{video_base_url}/video.mp4", 'type': 'video/mp4'},
                                {'url': f"{video_base_url}/video.webm", 'type': 'video/webm'}
                            ],
                            'poster': f"{video_base_url}/poster",
                            'page_url': page_url,
                            'element_type': 'poster_detected'
                        })
            
            # 3. Tentar clicar em vídeos para ativar (SeleniumBase)
            try:
                video_buttons = sb.find_elements('.vjsalt-poster')
                for i, button in enumerate(video_buttons[:5]):  # Máximo 5 vídeos por página
                    try:
                        button.click()
                        sb.sleep(2)
                        
                        # Buscar elemento de vídeo ativado
                        active_video = sb.find_element('video[data-video-id]')
                        if active_video:
                            video_id = active_video.get_attribute('data-video-id')
                            
                            # Verificar se já foi encontrado
                            if not any(v['video_id'] == video_id for v in videos):
                                sources = sb.find_elements('video[data-video-id] source')
                                video_urls = []
                                
                                for source in sources:
                                    src = source.get_attribute('src')
                                    type_attr = source.get_attribute('type')
                                    if src:
                                        video_urls.append({'url': src, 'type': type_attr})
                                
                                if video_urls:
                                    videos.append({
                                        'video_id': video_id,
                                        'sources': video_urls,
                                        'poster': active_video.get_attribute('poster'),
                                        'page_url': page_url,
                                        'element_type': 'clicked_activated'
                                    })
                    except:
                        continue
            except:
                pass
            
            print(f"🎥 Vídeos encontrados na página: {len(videos)}")
            for video in videos:
                print(f"   📹 {video['video_id']} ({video['element_type']})")
            
            return videos
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair vídeos: {e}")
            return []
    
    def _process_video_complete(self, video_info):
        """Processa um vídeo completamente (download + transcrição)"""
        try:
            video_id = video_info['video_id']
            
            # Escolher melhor source (preferir MP4)
            best_source = None
            for source in video_info['sources']:
                if 'mp4' in source['type'] or 'mp4' in source['url']:
                    best_source = source
                    break
            
            if not best_source and video_info['sources']:
                best_source = video_info['sources'][0]
            
            if not best_source:
                print(f"⚠️ Nenhuma fonte de vídeo válida para {video_id}")
                return None
            
            # Metadata do vídeo
            metadata = {
                'page_url': video_info['page_url'],
                'poster_url': video_info.get('poster'),
                'element_type': video_info['element_type'],
                'source_type': best_source['type']
            }
            
            # Processar vídeo completo
            result = self.video_extractor.process_video_complete(
                best_source['url'], 
                video_id, 
                metadata
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao processar vídeo: {e}")
            return None
    
    def _extract_text_content(self, soup, url, page_title):
        """Extrai conteúdo de texto da página"""
        try:
            # Configurações para Autodesk
            content_selectors = [
                '.help-content',
                '.article-content',
                '.content-main',
                'main',
                '.documentation',
                '.video-description',
                '.transcript-content'
            ]
            
            content_parts = []
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # Remover scripts e estilos
                    for script in element(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    
                    text = element.get_text(separator=' ', strip=True)
                    if text and len(text) > 50:
                        content_parts.append(text)
            
            # Se não encontrou com seletores, usar body
            if not content_parts:
                body = soup.find('body')
                if body:
                    for script in body(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    content_parts.append(body.get_text(separator=' ', strip=True))
            
            content = '\n\n'.join(content_parts)
            
            # Criar chunks
            chunks = self._create_text_chunks(content)
            
            # Metadata
            metadata = {
                'url': url,
                'title': page_title,
                'domain': urlparse(url).netloc,
                'content_length': len(content),
                'readability_score': textstat.flesch_reading_ease(content) if content else 0
            }
            
            return {
                'content': content,
                'chunks': chunks,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"❌ Erro ao extrair texto: {e}")
            return {'content': '', 'chunks': [], 'metadata': {}}
    
    def _create_text_chunks(self, content):
        """Cria chunks de texto"""
        if not content:
            return []
        
        chunks = []
        words = content.split()
        words_per_chunk = self.chunk_size // 4
        overlap_words = self.chunk_overlap // 4
        
        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 50:
                chunks.append({
                    'text': chunk_text,
                    'start_index': i,
                    'word_count': len(chunk_words),
                    'char_count': len(chunk_text),
                    'chunk_type': 'text_content'
                })
        
        return chunks
    
    def _extract_autodesk_links(self, sb, base_url):
        """Extrai links específicos da Autodesk"""
        links = set()
        
        try:
            # Seletores específicos para Autodesk
            link_selectors = [
                'a[href*="/view/"]',
                'a[href*="/help/"]',
                'a[href*="/cloudhelp/"]',
                '.nav-link',
                '.toc-link',
                '.related-link'
            ]
            
            for selector in link_selectors:
                try:
                    elements = sb.find_elements(selector)
                    for element in elements[:30]:  # Limitar por seletor
                        href = element.get_attribute('href')
                        if href:
                            full_url = urljoin(base_url, href)
                            if self._is_valid_autodesk_url(full_url, base_url):
                                links.add(full_url)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Erro ao extrair links: {e}")
        
        return list(links)
    
    def _is_valid_autodesk_url(self, url, base_url):
        """Valida URLs específicas da Autodesk"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Mesmo domínio
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # URLs válidas da Autodesk
            valid_patterns = [
                '/view/',
                '/help/',
                '/cloudhelp/',
                '/ENU/',
                'ARCHDESK',
                'AutoCAD'
            ]
            
            if not any(pattern in url for pattern in valid_patterns):
                return False
            
            # Evitar arquivos não úteis
            excluded_extensions = ['.jpg', '.png', '.gif', '.css', '.js', '.xml']
            if any(url.lower().endswith(ext) for ext in excluded_extensions):
                return False
            
            return True
            
        except:
            return False
    
    def _crawl_autodesk_fallback(self, start_url, max_depth, max_pages):
        """Fallback usando requests (sem vídeos)"""
        print("🔄 Usando fallback requests (sem extração de vídeos)")
        
        # Implementação básica similar ao extrator anterior
        # mas sem processamento de vídeos
        pass
    
    def _save_complete_extraction(self):
        """Salva todos os dados extraídos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Dados completos das páginas
        pages_file = self.output_dir / f"pages_complete_{timestamp}.json"
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_info': {
                    'start_url': self.start_url,
                    'timestamp': timestamp,
                    'pages_processed': len(self.extracted_pages),
                    'videos_processed': len(self.extracted_videos),
                    'total_duration': time.time() - self.start_time
                },
                'pages': self.extracted_pages,
                'failed_urls': list(self.failed_urls)
            }, f, ensure_ascii=False, indent=2)
        
        # 2. Dados dos vídeos
        videos_file = self.output_dir / f"videos_complete_{timestamp}.json"
        with open(videos_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_info': {
                    'total_videos': len(self.extracted_videos),
                    'timestamp': timestamp
                },
                'videos': self.extracted_videos
            }, f, ensure_ascii=False, indent=2)
        
        # 3. Chunks unificados para RAG (texto + vídeo)
        chunks_file = self.output_dir / f"all_chunks_rag_{timestamp}.json"
        all_chunks = []
        
        # Chunks de texto
        for page in self.extracted_pages:
            for i, chunk in enumerate(page.get('text_chunks', [])):
                all_chunks.append({
                    'id': f"{page['url']}#text_chunk_{i}",
                    'text': chunk['text'],
                    'type': 'text_content',
                    'metadata': {
                        'source_url': page['url'],
                        'page_title': page['title'],
                        'chunk_index': i,
                        'chunk_type': 'text',
                        'extracted_at': page['extracted_at'],
                        **page.get('metadata', {})
                    }
                })
            
            # Chunks de vídeo
            for i, chunk in enumerate(page.get('video_chunks', [])):
                all_chunks.append({
                    'id': f"{chunk['video_id']}#video_chunk_{i}",
                    'text': chunk['text'],
                    'type': 'video_transcript',
                    'metadata': {
                        'source_url': page['url'],
                        'page_title': page['title'],
                        'video_id': chunk['video_id'],
                        'start_time': chunk['start_time'],
                        'end_time': chunk['end_time'],
                        'duration': chunk['duration'],
                        'chunk_type': 'video_transcript',
                        'language': chunk['language'],
                        **chunk.get('metadata', {})
                    }
                })
        
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 DADOS SALVOS:")
        print(f"   📄 Páginas completas: {pages_file}")
        print(f"   🎥 Vídeos completos: {videos_file}")
        print(f"   🔥 Chunks RAG unificados: {chunks_file}")
    
    def _get_extraction_summary(self):
        """Resumo da extração completa"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        total_text_chunks = sum(len(page.get('text_chunks', [])) for page in self.extracted_pages)
        total_video_chunks = sum(len(page.get('video_chunks', [])) for page in self.extracted_pages)
        total_chars = sum(page.get('text_content', 0) if isinstance(page.get('text_content'), int) else len(page.get('text_content', '')) for page in self.extracted_pages)
        total_video_duration = sum(video.get('transcript', {}).get('segments', [])[-1].get('end', 0) if video.get('transcript', {}).get('segments') else 0 for video in self.extracted_videos)
        
        return {
            'start_url': self.start_url,
            'duration_seconds': round(duration, 2),
            'pages_processed': len(self.extracted_pages),
            'videos_processed': len(self.extracted_videos),
            'total_text_chunks': total_text_chunks,
            'total_video_chunks': total_video_chunks,
            'total_chunks': total_text_chunks + total_video_chunks,
            'total_characters': total_chars,
            'total_video_duration_seconds': round(total_video_duration, 2),
            'pages_failed': len(self.failed_urls),
            'whisper_available': self.video_extractor.whisper_available
        }

def test_complete_extractor():
    """Teste do extrator completo"""
    print("🎯 TESTE DO EXTRATOR COMPLETO COM VÍDEOS")
    print("=" * 60)
    
    extractor = AdvancedWebScraperWithVideo("test_complete_autodesk")
    
    # URL da Autodesk
    autodesk_url = "https://help.autodesk.com/view/ARCHDESK/2024/ENU/"
    
    result = extractor.extract_autodesk_complete(
        autodesk_url,
        max_depth=2,
        max_pages=15  # Teste com menos páginas primeiro
    )
    
    print(f"\n📊 RESULTADO COMPLETO:")
    print(f"   📄 Páginas: {result['pages_processed']}")
    print(f"   🎥 Vídeos: {result['videos_processed']}")
    print(f"   🔥 Chunks texto: {result['total_text_chunks']}")
    print(f"   🎬 Chunks vídeo: {result['total_video_chunks']}")
    print(f"   📊 Total chars: {result['total_characters']:,}")
    print(f"   ⏱️ Duração vídeos: {result['total_video_duration_seconds']:.1f}s")
    print(f"   🕒 Tempo total: {result['duration_seconds']:.1f}s")
    
    return result

if __name__ == "__main__":
    test_complete_extractor()
