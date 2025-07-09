"""
Sistema de Extração Web Avançado com SeleniumBase - Versão Corrigida
===================================================================

Este módulo implementa um extrator web robusto usando SeleniumBase para
sites dinâmicos com JavaScript, com fallback para requests em caso de problemas.

Funcionalidades:
- Extração de sites dinâmicos com JavaScript
- Download automático de arquivos
- Navegação inteligente entre páginas
- Captura de screenshots
- Configurações específicas por domínio
- Fallback para sites estáticos
"""

import os
import time
import json
import traceback
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import textstat

# Configurações por domínio
DOMAIN_CONFIGS = {
    'help.autodesk.com': {
        'content_selectors': [
            '.help-content',
            '.article-content', 
            '.content-main',
            'main',
            '.documentation'
        ],
        'title_selectors': [
            'h1',
            '.article-title',
            '.help-title',
            'title'
        ],
        'link_selectors': [
            'a[href*="/view/"]',
            'a[href*="/help/"]',
            '.nav-link',
            '.toc-link'
        ],
        'download_selectors': [
            'a[href$=".pdf"]',
            'a[href$=".zip"]', 
            'a[href$=".exe"]',
            'a[href*="download"]'
        ]
    },
    'default': {
        'content_selectors': [
            'main',
            '.content',
            '.main-content',
            'article',
            '.post-content'
        ],
        'title_selectors': [
            'h1',
            '.title',
            '.page-title',
            'title'
        ],
        'link_selectors': [
            'a[href]'
        ],
        'download_selectors': [
            'a[href$=".pdf"]',
            'a[href$=".doc"]',
            'a[href$=".docx"]',
            'a[href$=".zip"]',
            'a[href$=".exe"]'
        ]
    }
}

class WebScraperExtractorV2:
    """
    Extrator web avançado com suporte a SeleniumBase e fallback
    """
    
    def __init__(self, output_dir="web_extraction", chunk_size=512, chunk_overlap=50):
        """
        Inicializa o extrator
        
        Args:
            output_dir: Diretório para salvar dados extraídos
            chunk_size: Tamanho dos chunks em caracteres
            chunk_overlap: Sobreposição entre chunks
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.delay_between_requests = 2.0
        self.max_pages_per_extraction = 50
        
        # Dados da extração
        self.extracted_data = []
        self.downloaded_files = []
        self.processed_urls = set()
        self.failed_urls = set()
        
        # Configurações
        self.use_selenium = True
        self.take_screenshots = True
        
        print(f"✅ WebScraperExtractorV2 inicializado")
        print(f"📁 Diretório de saída: {self.output_dir}")
        print(f"🔢 Tamanho do chunk: {self.chunk_size}")
    
    def extract_from_website(self, start_url, max_depth=3, max_pages=20, same_domain_only=True):
        """
        Extrai conteúdo de um website
        
        Args:
            start_url: URL inicial
            max_depth: Profundidade máxima de navegação
            max_pages: Número máximo de páginas
            same_domain_only: Ficar apenas no mesmo domínio
            
        Returns:
            dict: Resumo da extração
        """
        print(f"🌐 Iniciando extração de: {start_url}")
        print(f"📊 Configurações: depth={max_depth}, max_pages={max_pages}")
        
        self.start_time = time.time()
        self.start_url = start_url
        self.processed_urls.clear()
        self.failed_urls.clear()
        self.extracted_data.clear()
        self.downloaded_files.clear()
        
        # Tentar com SeleniumBase primeiro
        try:
            if self.use_selenium:
                print("🚀 Tentando com SeleniumBase...")
                self._extract_with_selenium(start_url, max_depth, max_pages, same_domain_only)
            else:
                raise Exception("SeleniumBase desabilitado")
                
        except Exception as e:
            print(f"⚠️ SeleniumBase falhou: {str(e)}")
            print("🔄 Usando fallback com requests...")
            self._extract_with_requests(start_url, max_depth, max_pages, same_domain_only)
        
        # Salvar resultados
        self.save_extracted_data()
        
        return self.get_extraction_summary()
    
    def _extract_with_selenium(self, start_url, max_depth, max_pages, same_domain_only):
        """Extração usando SeleniumBase"""
        try:
            from seleniumbase import SB
            
            # Configurações corretas para SeleniumBase
            with SB(headless=True) as sb:
                self._crawl_with_selenium(sb, start_url, max_depth, max_pages, same_domain_only)
                
        except ImportError:
            raise Exception("SeleniumBase não está instalado corretamente")
        except Exception as e:
            raise Exception(f"Erro no SeleniumBase: {str(e)}")
    
    def _crawl_with_selenium(self, sb, start_url, max_depth, max_pages, same_domain_only):
        """Crawling usando instância do SeleniumBase"""
        url_queue = [(start_url, 0)]
        processed_count = 0
        
        while url_queue and processed_count < max_pages:
            current_url, depth = url_queue.pop(0)
            
            if current_url in self.processed_urls or depth > max_depth:
                continue
            
            print(f"📄 Processando [{depth}]: {current_url}")
            
            try:
                # Navegar para página
                sb.open(current_url)
                
                # Aguardar carregamento do JavaScript
                sb.sleep(5)  # Aguardar mais tempo para sites dinâmicos
                
                # Tentar aguardar elementos específicos carregarem
                try:
                    sb.wait_for_element('body', timeout=10)
                except:
                    pass
                
                # Obter conteúdo
                page_source = sb.get_page_source()
                page_title = sb.get_title()
                
                print(f"📊 Conteúdo obtido: {len(page_source)} chars, título: {page_title}")
                
                # Processar página
                page_data = self._process_page_content(current_url, page_source, page_title)
                
                if page_data:
                    self.extracted_data.append(page_data)
                    self.processed_urls.add(current_url)
                    processed_count += 1
                    
                    # Capturar screenshot se habilitado
                    if self.take_screenshots:
                        self._save_screenshot(sb, current_url)
                    
                    # Buscar links para próximas páginas
                    if depth < max_depth:
                        new_links = self._extract_links_selenium(sb, current_url, same_domain_only)
                        print(f"🔗 Encontrados {len(new_links)} links para próximo nível")
                        for link in new_links[:10]:  # Limitar a 10 links por página
                            if link not in self.processed_urls:
                                url_queue.append((link, depth + 1))
                else:
                    print(f"⚠️ Nenhum conteúdo válido extraído de {current_url}")
                
                time.sleep(self.delay_between_requests)
                
            except Exception as e:
                print(f"❌ Erro ao processar {current_url}: {str(e)}")
                self.failed_urls.add(current_url)
    
    def _extract_with_requests(self, start_url, max_depth, max_pages, same_domain_only):
        """Fallback usando requests"""
        print("🔄 Usando requests para extração...")
        
        url_queue = [(start_url, 0)]
        processed_count = 0
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        while url_queue and processed_count < max_pages:
            current_url, depth = url_queue.pop(0)
            
            if current_url in self.processed_urls or depth > max_depth:
                continue
            
            print(f"📄 Processando [{depth}]: {current_url}")
            
            try:
                response = session.get(current_url, timeout=30)
                response.raise_for_status()
                
                # Processar página
                page_data = self._process_page_content(current_url, response.text, None)
                
                if page_data:
                    self.extracted_data.append(page_data)
                    self.processed_urls.add(current_url)
                    processed_count += 1
                    
                    # Buscar links
                    if depth < max_depth:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        new_links = self._extract_links_soup(soup, current_url, same_domain_only)
                        for link in new_links:
                            if link not in self.processed_urls:
                                url_queue.append((link, depth + 1))
                
                time.sleep(self.delay_between_requests)
                
            except Exception as e:
                print(f"❌ Erro ao processar {current_url}: {str(e)}")
                self.failed_urls.add(current_url)
    
    def _process_page_content(self, url, html_content, page_title):
        """Processa conteúdo de uma página"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Obter configurações para o domínio
            domain = urlparse(url).netloc
            config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS['default'])
            
            # Extrair título
            title = page_title or self._extract_title(soup, config)
            
            # Extrair conteúdo principal
            content = self._extract_main_content(soup, config)
            
            if not content or len(content.strip()) < 100:
                print(f"⚠️ Conteúdo insuficiente em {url}")
                return None
            
            # Extrair metadados
            metadata = self._extract_metadata(soup, url)
            
            # Detectar links de download
            download_links = self._extract_download_links(soup, url, config)
            
            # Criar chunks do conteúdo
            chunks = self._create_chunks(content)
            
            page_data = {
                'url': url,
                'title': title,
                'content': content,
                'metadata': metadata,
                'download_links': download_links,
                'chunks': chunks,
                'extracted_at': datetime.now().isoformat(),
                'content_length': len(content),
                'readability_score': textstat.flesch_reading_ease(content) if content else 0
            }
            
            print(f"✅ Extraído: {title[:50]}... ({len(content)} chars, {len(chunks)} chunks)")
            
            return page_data
            
        except Exception as e:
            print(f"❌ Erro ao processar conteúdo de {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup, config):
        """Extrai título da página"""
        for selector in config['title_selectors']:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return "Título não encontrado"
    
    def _extract_main_content(self, soup, config):
        """Extrai conteúdo principal da página"""
        content_parts = []
        
        for selector in config['content_selectors']:
            elements = soup.select(selector)
            for element in elements:
                # Remover scripts e estilos
                for script in element(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                
                text = element.get_text(separator=' ', strip=True)
                if text and len(text) > 50:
                    content_parts.append(text)
        
        # Se não encontrou com seletores específicos, usar body
        if not content_parts:
            body = soup.find('body')
            if body:
                for script in body(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                content_parts.append(body.get_text(separator=' ', strip=True))
        
        return '\n\n'.join(content_parts)
    
    def _extract_metadata(self, soup, url):
        """Extrai metadados da página"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc
        }
        
        # Meta tags
        meta_tags = {
            'description': soup.find('meta', attrs={'name': 'description'}),
            'keywords': soup.find('meta', attrs={'name': 'keywords'}),
            'author': soup.find('meta', attrs={'name': 'author'}),
            'og:title': soup.find('meta', attrs={'property': 'og:title'}),
            'og:description': soup.find('meta', attrs={'property': 'og:description'})
        }
        
        for key, tag in meta_tags.items():
            if tag:
                content = tag.get('content')
                if content:
                    metadata[key] = content.strip()
        
        return metadata
    
    def _extract_download_links(self, soup, base_url, config):
        """Extrai links de download"""
        download_links = []
        
        for selector in config['download_selectors']:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    download_links.append({
                        'url': full_url,
                        'text': link.get_text().strip(),
                        'type': self._get_file_type(full_url)
                    })
        
        return download_links
    
    def _get_file_type(self, url):
        """Determina tipo de arquivo pela extensão"""
        extension = Path(urlparse(url).path).suffix.lower()
        
        type_map = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.zip': 'Archive',
            '.rar': 'Archive',
            '.exe': 'Executable',
            '.msi': 'Installer',
            '.mp4': 'Video',
            '.avi': 'Video',
            '.jpg': 'Image',
            '.png': 'Image',
            '.gif': 'Image'
        }
        
        return type_map.get(extension, 'Unknown')
    
    def _create_chunks(self, content):
        """Cria chunks do conteúdo"""
        if not content:
            return []
        
        chunks = []
        words = content.split()
        
        # Estimar palavras por chunk (aproximadamente 4 chars por palavra)
        words_per_chunk = self.chunk_size // 4
        overlap_words = self.chunk_overlap // 4
        
        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 50:  # Mínimo de 50 caracteres
                chunks.append({
                    'text': chunk_text,
                    'start_index': i,
                    'word_count': len(chunk_words),
                    'char_count': len(chunk_text)
                })
        
        return chunks
    
    def _extract_links_selenium(self, sb, base_url, same_domain_only):
        """Extrai links usando SeleniumBase"""
        links = set()
        
        try:
            link_elements = sb.find_elements('a[href]')
            
            for element in link_elements[:30]:  # Limitar a 30 links
                href = element.get_attribute('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_url(full_url, base_url, same_domain_only):
                        links.add(full_url)
        
        except Exception as e:
            print(f"⚠️ Erro ao extrair links: {str(e)}")
        
        return list(links)
    
    def _extract_links_soup(self, soup, base_url, same_domain_only):
        """Extrai links usando BeautifulSoup"""
        links = set()
        
        try:
            for link in soup.find_all('a', href=True)[:30]:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_url(full_url, base_url, same_domain_only):
                        links.add(full_url)
        
        except Exception as e:
            print(f"⚠️ Erro ao extrair links: {str(e)}")
        
        return list(links)
    
    def _is_valid_url(self, url, base_url, same_domain_only):
        """Valida se URL deve ser processada"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Verificar esquema
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Verificar domínio se necessário
            if same_domain_only and parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Evitar arquivos que não são páginas
            excluded_extensions = ['.jpg', '.png', '.gif', '.pdf', '.zip', '.exe', '.css', '.js']
            if any(url.lower().endswith(ext) for ext in excluded_extensions):
                return False
            
            # Evitar URLs com parâmetros complexos
            if len(parsed_url.query) > 100:
                return False
            
            return True
            
        except:
            return False
    
    def _save_screenshot(self, sb, url):
        """Salva screenshot da página"""
        try:
            # Nome do arquivo baseado na URL
            url_hash = str(hash(url))[-8:]
            filename = f"screenshot_{url_hash}.png"
            filepath = self.output_dir / "screenshots" / filename
            
            # Criar diretório se não existir
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Salvar screenshot
            sb.save_screenshot(str(filepath))
            print(f"📸 Screenshot salvo: {filename}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar screenshot: {str(e)}")
    
    def save_extracted_data(self):
        """Salva dados extraídos em arquivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar dados completos
        data_file = self.output_dir / f"extracted_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_info': {
                    'start_url': self.start_url,
                    'timestamp': timestamp,
                    'pages_processed': len(self.extracted_data),
                    'pages_failed': len(self.failed_urls)
                },
                'pages': self.extracted_data,
                'failed_urls': list(self.failed_urls)
            }, f, ensure_ascii=False, indent=2)
        
        # Salvar apenas chunks para integração RAG
        chunks_file = self.output_dir / f"chunks_{timestamp}.json"
        all_chunks = []
        
        for page in self.extracted_data:
            for i, chunk in enumerate(page.get('chunks', [])):
                all_chunks.append({
                    'id': f"{page['url']}#chunk_{i}",
                    'text': chunk['text'],
                    'metadata': {
                        'source_url': page['url'],
                        'page_title': page['title'],
                        'chunk_index': i,
                        'extracted_at': page['extracted_at'],
                        **page.get('metadata', {})
                    }
                })
        
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dados salvos:")
        print(f"   📄 Dados completos: {data_file}")
        print(f"   🔥 Chunks RAG: {chunks_file}")
    
    def get_extraction_summary(self):
        """Retorna resumo da extração"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        total_chunks = sum(len(page.get('chunks', [])) for page in self.extracted_data)
        total_chars = sum(page.get('content_length', 0) for page in self.extracted_data)
        total_downloads = sum(len(page.get('download_links', [])) for page in self.extracted_data)
        
        return {
            'start_url': self.start_url,
            'duration_seconds': round(duration, 2),
            'pages_processed': len(self.extracted_data),
            'pages_failed': len(self.failed_urls),
            'total_chunks': total_chunks,
            'total_characters': total_chars,
            'download_links_found': total_downloads,
            'processed_urls': list(self.processed_urls),
            'failed_urls': list(self.failed_urls)
        }

# Função de teste rápido
def test_extractor():
    """Teste rápido do extrator"""
    print("🧪 TESTE RÁPIDO DO WEB SCRAPER EXTRACTOR V2")
    print("=" * 60)
    
    extractor = WebScraperExtractorV2("test_extraction")
    
    # Teste com uma URL simples primeiro
    test_url = "https://httpbin.org/html"
    print(f"🌐 Testando com: {test_url}")
    
    result = extractor.extract_from_website(
        test_url,
        max_depth=1,
        max_pages=1,
        same_domain_only=True
    )
    
    print("\n📊 RESULTADO DO TESTE:")
    print(f"   ✅ Páginas processadas: {result['pages_processed']}")
    print(f"   ❌ Páginas com erro: {result['pages_failed']}")
    print(f"   🔥 Total de chunks: {result['total_chunks']}")
    print(f"   📊 Total de caracteres: {result['total_characters']}")
    print(f"   ⏱️ Duração: {result['duration_seconds']}s")
    
    if result['pages_processed'] > 0:
        print("✅ TESTE APROVADO! O extrator está funcionando.")
    else:
        print("❌ TESTE FALHOU! Verifique a configuração.")

if __name__ == "__main__":
    test_extractor()
