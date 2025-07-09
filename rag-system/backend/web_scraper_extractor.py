"""
Sistema Avançado de Web Scraping para RAG - Versão 1.0
Autor: Assistant IA
Data: 2024

Este módulo implementa um sistema de web scraping avançado capaz de:
- Extrair conteúdo de sites dinâmicos com JavaScript pesado
- Lidar com múltiplas abas e navegação complexa
- Fazer download de arquivos (PDFs, vídeos, documentos)
- Extrair conteúdo de vídeos (quando possível)
- Integrar com o sistema RAG existente
- Processar sites como documentação da Autodesk
"""

import os
import json
import csv
import time
import asyncio
import requests
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd

# SeleniumBase para automação web avançada
from seleniumbase import BaseCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# BeautifulSoup para parsing avançado de HTML
from bs4 import BeautifulSoup, Comment

# Processamento de texto e chunking
import re
from textstat import flesch_reading_ease


class WebScraperExtractor:
    """
    Classe principal para extração avançada de conteúdo web com capacidades de site dinâmico
    """
    
    def __init__(self, base_output_dir: str = "web_scraping_data", 
                 chunk_size: int = 512, 
                 overlap: int = 50,
                 max_pages: int = 100,
                 delay_between_requests: float = 2.0):
        """
        Inicializa o WebScraperExtractor
        
        Args:
            base_output_dir: Diretório base para salvar dados
            chunk_size: Tamanho dos chunks de texto
            overlap: Sobreposição entre chunks
            max_pages: Máximo de páginas para processar
            delay_between_requests: Delay entre requisições em segundos
        """
        self.base_output_dir = Path(base_output_dir)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_pages = max_pages
        self.delay_between_requests = delay_between_requests
        
        # Dados extraídos
        self.extracted_data = []
        self.chunks = []
        self.downloaded_files = []
        self.processed_urls = set()
        self.failed_urls = []
        
        # Configurações de scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Extensões de arquivo para download
        self.downloadable_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'zip', 'rar', '7z', 'tar', 'gz',
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
            'mp3', 'wav', 'ogg', 'flac',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
            'txt', 'rtf', 'csv', 'json', 'xml'
        }
        
        self.setup_directories()
    
    def setup_directories(self):
        """Cria estrutura de diretórios necessária"""
        directories = [
            self.base_output_dir,
            self.base_output_dir / "extracted_content",
            self.base_output_dir / "chunks",
            self.base_output_dir / "downloads",
            self.base_output_dir / "screenshots",
            self.base_output_dir / "metadata",
            self.base_output_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Diretórios criados em: {self.base_output_dir}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitiza nome de arquivo para ser válido no sistema"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]  # Limita tamanho
    
    def extract_text_from_element(self, element) -> str:
        """Extrai texto limpo de um elemento HTML"""
        if not element:
            return ""
        
        # Remove scripts e styles
        for script in element(["script", "style", "noscript"]):
            script.decompose()
        
        # Remove comentários
        for comment in element(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extrai texto
        text = element.get_text()
        
        # Limpa texto
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def create_text_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cria chunks de texto com metadata"""
        if not text or len(text.strip()) < 50:
            return []
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) < 30:
                continue
            
            chunk_data = {
                'chunk_id': f"{metadata.get('page_id', 'unknown')}_{len(chunks)}",
                'text': chunk_text,
                'char_count': len(chunk_text),
                'word_count': len(chunk_words),
                'readability_score': flesch_reading_ease(chunk_text) if chunk_text else 0,
                'metadata': {
                    'source_url': metadata.get('url'),
                    'page_title': metadata.get('title'),
                    'extraction_timestamp': datetime.now().isoformat(),
                    'chunk_index': len(chunks),
                    'source_type': 'web_scraping'
                }
            }
            
            chunks.append(chunk_data)
        
        return chunks
    
    def download_file(self, url: str, filename: str) -> Optional[str]:
        """Faz download de arquivo e retorna o caminho local"""
        try:
            # Verifica se é uma URL válida
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                return None
            
            # Faz o download
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Define caminho do arquivo
            safe_filename = self.sanitize_filename(filename)
            file_path = self.base_output_dir / "downloads" / safe_filename
            
            # Salva arquivo
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_info = {
                'original_url': url,
                'local_path': str(file_path),
                'filename': safe_filename,
                'size_bytes': file_path.stat().st_size,
                'download_timestamp': datetime.now().isoformat()
            }
            
            self.downloaded_files.append(file_info)
            print(f"📥 Download concluído: {safe_filename}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Erro no download de {url}: {str(e)}")
            return None
    
    def should_download_file(self, url: str) -> bool:
        """Verifica se um arquivo deve ser baixado baseado na extensão"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            # Verifica extensão
            for ext in self.downloadable_extensions:
                if path.endswith(f'.{ext}'):
                    return True
            
            return False
        except:
            return False
    
    def extract_links_and_downloads(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """Extrai links de navegação e links para download"""
        navigation_links = []
        download_links = []
        
        # Encontra todos os links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
            
            # Converte para URL absoluta
            absolute_url = urljoin(base_url, href)
            
            # Filtra links válidos
            if not absolute_url.startswith(('http://', 'https://')):
                continue
            
            # Verifica se é download
            if self.should_download_file(absolute_url):
                download_links.append(absolute_url)
            else:
                # Link de navegação
                if absolute_url not in self.processed_urls:
                    navigation_links.append(absolute_url)
        
        return navigation_links, download_links
    
    def extract_page_content(self, driver, url: str) -> Dict[str, Any]:
        """Extrai conteúdo completo de uma página usando SeleniumBase"""
        try:
            print(f"🔍 Processando: {url}")
            
            # Navega para a página
            driver.open(url)
            
            # Aguarda carregamento dinâmico
            driver.sleep(3)
            
            # Aguarda elementos específicos se necessário
            try:
                driver.wait_for_element("body", timeout=10)
            except:
                pass
            
            # Extrai informações básicas
            title = driver.get_title()
            page_source = driver.get_page_source()
            current_url = driver.get_current_url()
            
            # Tira screenshot
            screenshot_path = self.base_output_dir / "screenshots" / f"{self.sanitize_filename(title)}.png"
            driver.save_screenshot(str(screenshot_path))
            
            # Processa HTML com BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove elementos indesejados
            for unwanted in soup(["script", "style", "nav", "header", "footer", "aside", "advertisement"]):
                unwanted.decompose()
            
            # Extrai conteúdo principal
            main_content = ""
            
            # Tenta encontrar área de conteúdo principal
            content_selectors = [
                'main', '[role="main"]', '.main-content', '#main-content',
                '.content', '#content', '.post-content', '.article-content',
                '.page-content', '.entry-content', 'article'
            ]
            
            main_element = None
            for selector in content_selectors:
                try:
                    main_element = soup.select_one(selector)
                    if main_element:
                        break
                except:
                    continue
            
            # Se não encontrou área específica, usa o body
            if not main_element:
                main_element = soup.find('body')
            
            if main_element:
                main_content = self.extract_text_from_element(main_element)
            
            # Extrai metadados
            metadata = {
                'url': current_url,
                'original_url': url,
                'title': title,
                'description': '',
                'keywords': '',
                'author': '',
                'publication_date': '',
                'language': 'pt',
                'content_length': len(main_content),
                'extraction_timestamp': datetime.now().isoformat(),
                'screenshot_path': str(screenshot_path)
            }
            
            # Tenta extrair metadados específicos
            try:
                # Description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    metadata['description'] = meta_desc.get('content', '')
                
                # Keywords
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                if meta_keywords:
                    metadata['keywords'] = meta_keywords.get('content', '')
                
                # Author
                meta_author = soup.find('meta', attrs={'name': 'author'})
                if meta_author:
                    metadata['author'] = meta_author.get('content', '')
                
                # Language
                html_lang = soup.find('html')
                if html_lang and html_lang.get('lang'):
                    metadata['language'] = html_lang.get('lang')
            except:
                pass
            
            # Extrai links
            navigation_links, download_links = self.extract_links_and_downloads(soup, current_url)
            
            # Processa downloads
            for download_url in download_links[:10]:  # Limita downloads
                filename = os.path.basename(urlparse(download_url).path)
                if not filename:
                    filename = f"download_{int(time.time())}"
                
                self.download_file(download_url, filename)
            
            # Cria chunks do conteúdo
            page_id = self.sanitize_filename(f"{urlparse(url).netloc}_{title}")
            metadata['page_id'] = page_id
            
            chunks = self.create_text_chunks(main_content, metadata)
            self.chunks.extend(chunks)
            
            page_data = {
                'page_id': page_id,
                'metadata': metadata,
                'content': main_content,
                'navigation_links': navigation_links[:20],  # Limita links
                'download_links': download_links,
                'chunks_count': len(chunks),
                'processing_timestamp': datetime.now().isoformat()
            }
            
            self.extracted_data.append(page_data)
            self.processed_urls.add(url)
            
            print(f"✅ Página processada: {title} ({len(chunks)} chunks)")
            return page_data
            
        except Exception as e:
            error_msg = f"Erro ao processar {url}: {str(e)}"
            print(f"❌ {error_msg}")
            self.failed_urls.append({'url': url, 'error': error_msg, 'timestamp': datetime.now().isoformat()})
            return None
    
    def extract_from_website(self, start_url: str, max_depth: int = 3, 
                           same_domain_only: bool = True) -> Dict[str, Any]:
        """
        Extrai conteúdo de um site completo usando SeleniumBase
        
        Args:
            start_url: URL inicial
            max_depth: Profundidade máxima de navegação
            same_domain_only: Se deve ficar apenas no mesmo domínio
        """
        
        class WebScrapingCase(BaseCase):
            def __init__(self, extractor_instance):
                super().__init__()
                self.extractor = extractor_instance
            
            def extract_website_content(self, start_url, max_depth, same_domain_only):
                """Método principal de extração"""
                start_domain = urlparse(start_url).netloc
                urls_to_process = [(start_url, 0)]  # (url, depth)
                processed_count = 0
                
                print(f"🚀 Iniciando extração de: {start_url}")
                print(f"📊 Configurações: max_depth={max_depth}, max_pages={self.extractor.max_pages}")
                
                while urls_to_process and processed_count < self.extractor.max_pages:
                    current_url, depth = urls_to_process.pop(0)
                    
                    # Verifica profundidade
                    if depth > max_depth:
                        continue
                    
                    # Verifica domínio
                    if same_domain_only:
                        current_domain = urlparse(current_url).netloc
                        if current_domain != start_domain:
                            continue
                    
                    # Verifica se já foi processada
                    if current_url in self.extractor.processed_urls:
                        continue
                    
                    # Processa página
                    page_data = self.extractor.extract_page_content(self, current_url)
                    
                    if page_data:
                        processed_count += 1
                        
                        # Adiciona novos links para processamento
                        if depth < max_depth:
                            for link in page_data.get('navigation_links', []):
                                if link not in self.extractor.processed_urls:
                                    urls_to_process.append((link, depth + 1))
                    
                    # Delay entre requisições
                    self.sleep(self.extractor.delay_between_requests)
                
                print(f"🎯 Extração concluída: {processed_count} páginas processadas")
        
        # Executa extração
        scraper_case = WebScrapingCase(self)
        
        try:
            # Configurações do navegador
            scraper_case.setUp()
            scraper_case.extract_website_content(start_url, max_depth, same_domain_only)
            
        except Exception as e:
            print(f"❌ Erro durante extração: {str(e)}")
            traceback.print_exc()
        
        finally:
            try:
                scraper_case.tearDown()
            except:
                pass
        
        # Salva resultados
        self.save_extracted_data()
        
        # Retorna resumo
        return self.get_extraction_summary()
    
    def save_extracted_data(self):
        """Salva todos os dados extraídos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salva dados principais
        main_data_file = self.base_output_dir / "extracted_content" / f"web_content_{timestamp}.json"
        with open(main_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
        
        # Salva chunks
        chunks_file = self.base_output_dir / "chunks" / f"web_chunks_{timestamp}.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        # Salva chunks em CSV
        if self.chunks:
            chunks_csv = self.base_output_dir / "chunks" / f"web_chunks_{timestamp}.csv"
            chunks_df = pd.DataFrame([
                {
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'char_count': chunk['char_count'],
                    'word_count': chunk['word_count'],
                    'readability_score': chunk['readability_score'],
                    'source_url': chunk['metadata']['source_url'],
                    'page_title': chunk['metadata']['page_title'],
                    'extraction_timestamp': chunk['metadata']['extraction_timestamp']
                }
                for chunk in self.chunks
            ])
            chunks_df.to_csv(chunks_csv, index=False, encoding='utf-8')
        
        # Salva informações de downloads
        if self.downloaded_files:
            downloads_file = self.base_output_dir / "metadata" / f"downloads_{timestamp}.json"
            with open(downloads_file, 'w', encoding='utf-8') as f:
                json.dump(self.downloaded_files, f, ensure_ascii=False, indent=2)
        
        # Salva URLs falhas
        if self.failed_urls:
            failures_file = self.base_output_dir / "logs" / f"failed_urls_{timestamp}.json"
            with open(failures_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dados salvos com timestamp: {timestamp}")
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Retorna resumo da extração"""
        total_chars = sum(len(chunk['text']) for chunk in self.chunks)
        avg_readability = sum(chunk['readability_score'] for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
        
        summary = {
            'extraction_summary': {
                'total_pages_processed': len(self.extracted_data),
                'total_chunks_created': len(self.chunks),
                'total_files_downloaded': len(self.downloaded_files),
                'total_characters_extracted': total_chars,
                'average_readability_score': round(avg_readability, 2),
                'failed_urls_count': len(self.failed_urls),
                'extraction_timestamp': datetime.now().isoformat(),
                'output_directory': str(self.base_output_dir)
            },
            'processed_pages': [
                {
                    'title': page['metadata']['title'],
                    'url': page['metadata']['url'],
                    'chunks_count': page['chunks_count'],
                    'content_length': page['metadata']['content_length']
                }
                for page in self.extracted_data
            ],
            'downloads': self.downloaded_files,
            'failed_urls': self.failed_urls
        }
        
        return summary


def main():
    """Função principal para testes"""
    # Exemplo de uso
    extractor = WebScraperExtractor(
        base_output_dir="web_scraping_autodesk",
        chunk_size=512,
        overlap=50,
        max_pages=20,
        delay_between_requests=3.0
    )
    
    # URL de exemplo (documentação Autodesk)
    start_url = "https://help.autodesk.com/view/ARCHDESK/2024/ENU/"
    
    # Executa extração
    results = extractor.extract_from_website(
        start_url=start_url,
        max_depth=2,
        same_domain_only=True
    )
    
    # Mostra resumo
    print("\n" + "="*80)
    print("RESUMO DA EXTRAÇÃO WEB")
    print("="*80)
    
    summary = results['extraction_summary']
    print(f"📄 Páginas processadas: {summary['total_pages_processed']}")
    print(f"🔥 Chunks criados: {summary['total_chunks_created']}")
    print(f"📥 Arquivos baixados: {summary['total_files_downloaded']}")
    print(f"📊 Total de caracteres: {summary['total_characters_extracted']:,}")
    print(f"📈 Legibilidade média: {summary['average_readability_score']}")
    print(f"❌ URLs com falha: {summary['failed_urls_count']}")
    print(f"📁 Dados salvos em: {summary['output_directory']}")
    
    return results


if __name__ == "__main__":
    main()
