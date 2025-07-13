#!/usr/bin/env python3
"""
WEB DOCUMENTATION SCRAPER & RAG EXTRACTOR
=========================================
Sistema completo para extração e processamento de documentação web com funcionalidades RAG.
Inclui suporte a sites dinâmicos, vídeos, imagens, tabelas e links.
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
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports principais
try:
    from bs4 import BeautifulSoup
    import pandas as pd
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import sqlite3
    import nltk
    from textstat import flesch_reading_ease
    print("Bibliotecas principais carregadas com sucesso")
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Execute: pip install beautifulsoup4 pandas numpy sentence-transformers nltk textstat")
    sys.exit(1)

# Imports opcionais para funcionalidades avançadas
try:
    from seleniumbase import Driver
    SELENIUM_AVAILABLE = True
    print("Selenium disponível para sites dinâmicos")
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium não disponível - apenas sites estáticos")

try:
    import whisper
    WHISPER_AVAILABLE = True
    print("Whisper disponível para transcrição de vídeos")
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper não disponível - sem transcrição de vídeos")

try:
    import docling
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
    print("Docling disponível para processamento avançado")
except ImportError:
    DOCLING_AVAILABLE = False
    print("Docling não disponível - processamento básico")

class WebDocumentationScraper:
    """
    Sistema completo para extração de documentação web com funcionalidades RAG
    """
    
    def __init__(self, storage_path: str = "web_scraping_storage"):
        """
        Inicializa o scraper de documentação web
        
        Args:
            storage_path: Caminho para armazenamento dos dados
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Configurar sessão HTTP com retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers para evitar bloqueios
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Inicializar modelo de embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Modelo de embeddings carregado")
        except Exception as e:
            print(f"Erro ao carregar modelo de embeddings: {e}")
            self.embedding_model = None
        
        # Dados coletados
        self.extracted_data = {
            'pages': [],
            'videos': [],
            'images': [],
            'links': [],
            'tables': [],
            'downloads': [],
            'chunks': [],
            'metadata': {}
        }
    
    def detect_page_language(self, url: str, html_content: str) -> str:
        """
        Detecta o idioma da página
        
        Args:
            url: URL da página
            html_content: Conteúdo HTML
            
        Returns:
            Código do idioma detectado
        """
        # Detectar pelo URL
        if "/ENU/" in url or "/en/" in url.lower():
            return "en"
        elif "/PTB/" in url or "/pt/" in url.lower():
            return "pt"
        elif "/ESP/" in url or "/es/" in url.lower():
            return "es"
        elif "/FRA/" in url or "/fr/" in url.lower():
            return "fr"
        elif "/DEU/" in url or "/de/" in url.lower():
            return "de"
        
        # Detectar pelo HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verificar atributo lang
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag.get('lang').lower()
            if lang.startswith('en'):
                return "en"
            elif lang.startswith('pt'):
                return "pt"
            elif lang.startswith('es'):
                return "es"
            elif lang.startswith('fr'):
                return "fr"
            elif lang.startswith('de'):
                return "de"
        
        # Detectar por meta tags
        meta_lang = soup.find('meta', attrs={'name': 'language'})
        if meta_lang and meta_lang.get('content'):
            return meta_lang.get('content').lower()[:2]
        
        return "en"  # Padrão inglês
    
    def extract_page_content(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """
        Extrai conteúdo completo de uma página
        
        Args:
            url: URL da página
            use_selenium: Se deve usar Selenium para JavaScript
            
        Returns:
            Dicionário com conteúdo extraído
        """
        logger.info(f"Extraindo conteúdo de: {url}")
        
        try:
            if use_selenium and SELENIUM_AVAILABLE:
                html_content = self._extract_with_selenium(url)
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detectar idioma
            language = self.detect_page_language(url, html_content)
            
            # Extrair informações básicas
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "Sem título"
            
            # Extrair texto principal
            text_content = self._extract_text_content(soup)
            
            # Extrair tabelas
            tables = self._extract_tables(soup)
            
            # Extrair imagens
            images = self._extract_images(soup, url)
            
            # Extrair vídeos
            videos = self._extract_videos(soup, url)
            
            # Extrair links
            links = self._extract_links(soup, url)
            
            # Extrair metadados
            metadata = self._extract_metadata(soup)
            
            page_data = {
                'url': url,
                'title': title_text,
                'language': language,
                'text_content': text_content,
                'tables': tables,
                'images': images,
                'videos': videos,
                'links': links,
                'metadata': metadata,
                'extracted_at': datetime.now().isoformat(),
                'word_count': len(text_content.split()),
                'char_count': len(text_content)
            }
            
            return page_data
            
        except Exception as e:
            logger.error(f"Erro ao extrair {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_with_selenium(self, url: str) -> str:
        """
        Extrai conteúdo usando Selenium para sites dinâmicos
        
        Args:
            url: URL da página
            
        Returns:
            HTML da página após carregar JavaScript
        """
        try:
            driver = Driver(uc=True, headless=True)
            driver.get(url)
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Scroll para carregar conteúdo lazy-loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html_content = driver.page_source
            driver.quit()
            
            return html_content
            
        except Exception as e:
            logger.error(f"Erro com Selenium: {e}")
            raise
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extrai texto principal da página
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Texto limpo da página
        """
        # Remover scripts, estilos e elementos desnecessários
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Priorizar áreas de conteúdo
        content_areas = soup.find_all(['article', 'main', 'div'], 
                                     class_=re.compile(r'content|main|article|body', re.I))
        
        if content_areas:
            text_parts = []
            for area in content_areas:
                text_parts.append(area.get_text(separator=' ', strip=True))
            text_content = ' '.join(text_parts)
        else:
            text_content = soup.get_text(separator=' ', strip=True)
        
        # Limpar texto
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return text_content
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrai tabelas da página
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Lista de tabelas extraídas
        """
        tables = []
        
        for i, table in enumerate(soup.find_all('table')):
            try:
                # Converter tabela para DataFrame
                df = pd.read_html(str(table))[0]
                
                # Limpar dados
                df = df.dropna(how='all').fillna('')
                
                table_data = {
                    'index': i,
                    'data': df.to_dict('records'),
                    'headers': df.columns.tolist(),
                    'rows': len(df),
                    'columns': len(df.columns),
                    'html': str(table)
                }
                
                tables.append(table_data)
                
            except Exception as e:
                logger.warning(f"Erro ao processar tabela {i}: {e}")
        
        return tables
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrai informações de imagens
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver links relativos
            
        Returns:
            Lista de imagens encontradas
        """
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
            
            # Resolver URL completa
            img_url = urljoin(base_url, src)
            
            image_data = {
                'url': img_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'class': img.get('class', []),
                'id': img.get('id', '')
            }
            
            images.append(image_data)
        
        return images
    
    def _extract_videos(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrai vídeos embeddeds
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base
            
        Returns:
            Lista de vídeos encontrados
        """
        videos = []
        
        # Vídeos HTML5
        for video in soup.find_all('video'):
            sources = []
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    sources.append(urljoin(base_url, src))
            
            video_data = {
                'type': 'html5',
                'sources': sources,
                'poster': video.get('poster', ''),
                'controls': video.has_attr('controls'),
                'autoplay': video.has_attr('autoplay')
            }
            
            videos.append(video_data)
        
        # iframes (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and any(domain in src for domain in ['youtube', 'vimeo', 'wistia', 'brightcove']):
                video_data = {
                    'type': 'embedded',
                    'url': src,
                    'width': iframe.get('width', ''),
                    'height': iframe.get('height', ''),
                    'title': iframe.get('title', '')
                }
                
                videos.append(video_data)
        
        return videos
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrai todos os links da página
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base
            
        Returns:
            Lista de links encontrados
        """
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            link_data = {
                'url': absolute_url,
                'text': link.get_text().strip(),
                'title': link.get('title', ''),
                'class': link.get('class', []),
                'is_external': urlparse(absolute_url).netloc != urlparse(base_url).netloc
            }
            
            links.append(link_data)
        
        return links
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrai metadados da página
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Dicionário com metadados
        """
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
        
        # Título e descrição
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text().strip()
        
        # Schema.org structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                structured_data = json.loads(script.string)
                metadata['structured_data'] = structured_data
                break
            except:
                continue
        
        return metadata

def main():
    """Função principal para teste"""
    parser = argparse.ArgumentParser(description='Web Documentation Scraper & RAG Extractor')
    parser.add_argument('--url', required=True, help='URL para extrair')
    parser.add_argument('--selenium', action='store_true', help='Usar Selenium para JavaScript')
    parser.add_argument('--output', default='web_scraping_storage', help='Pasta de saída')
    
    args = parser.parse_args()
    
    # Criar scraper
    scraper = WebDocumentationScraper(args.output)
    
    # Extrair página
    result = scraper.extract_page_content(args.url, args.selenium)
    
    # Salvar resultado
    output_file = scraper.storage_path / f"extraction_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Extração concluída! Resultado salvo em: {output_file}")
    print(f"Título: {result.get('title', 'N/A')}")
    print(f"Idioma: {result.get('language', 'N/A')}")
    print(f"Palavras: {result.get('word_count', 0)}")
    print(f"Vídeos: {len(result.get('videos', []))}")
    print(f"Imagens: {len(result.get('images', []))}")
    print(f"Links: {len(result.get('links', []))}")

if __name__ == "__main__":
    main()
