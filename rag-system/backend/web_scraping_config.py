"""
Configurações do Sistema de Web Scraping RAG
Autor: Assistant IA
Data: 2024

Este arquivo contém todas as configurações centralizadas do sistema.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WebScrapingConfig:
    """Configurações do sistema de web scraping"""
    
    # Diretórios
    BASE_OUTPUT_DIR: str = "web_scraping_data"
    DOWNLOADS_DIR: str = "downloads"
    SCREENSHOTS_DIR: str = "screenshots"
    EXPORTS_DIR: str = "exports"
    LOGS_DIR: str = "logs"
    
    # Configurações de scraping
    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_OVERLAP: int = 50
    DEFAULT_MAX_PAGES: int = 50
    DEFAULT_MAX_DEPTH: int = 3
    DEFAULT_DELAY_BETWEEN_REQUESTS: float = 2.0
    
    # Configurações do navegador
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 30
    PAGE_LOAD_TIMEOUT: int = 20
    SCREENSHOT_ON_ERROR: bool = True
    
    # Extensões de arquivo para download
    DOWNLOADABLE_EXTENSIONS: List[str] = None
    
    # Headers HTTP
    DEFAULT_HEADERS: Dict[str, str] = None
    
    # Configurações do banco de dados
    DATABASE_NAME: str = "web_scraping.db"
    MAX_CONNECTIONS: int = 5
    CONNECTION_TIMEOUT: int = 30
    
    # Configurações de busca
    TFIDF_MAX_FEATURES: int = 5000
    TFIDF_MIN_DF: int = 1
    TFIDF_MAX_DF: float = 0.95
    TFIDF_NGRAM_RANGE: tuple = (1, 2)
    
    # Configurações de análise de texto
    MIN_CONTENT_LENGTH: int = 50
    MIN_READABILITY_SCORE: float = 0.0
    MAX_KEYWORDS_EXTRACT: int = 20
    
    # Configurações da API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_RELOAD: bool = True
    API_LOG_LEVEL: str = "info"
    
    # Configurações de limpeza
    CLEANUP_DAYS_OLD: int = 30
    MAX_CACHE_SIZE: int = 1000
    
    def __post_init__(self):
        """Inicializa valores padrão após criação da instância"""
        if self.DOWNLOADABLE_EXTENSIONS is None:
            self.DOWNLOADABLE_EXTENSIONS = [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'zip', 'rar', '7z', 'tar', 'gz',
                'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
                'mp3', 'wav', 'ogg', 'flac',
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
                'txt', 'rtf', 'csv', 'json', 'xml'
            ]
        
        if self.DEFAULT_HEADERS is None:
            self.DEFAULT_HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }


# Instância global de configuração
config = WebScrapingConfig()


# Configurações específicas por domínio
DOMAIN_SPECIFIC_CONFIGS = {
    "help.autodesk.com": {
        "delay_between_requests": 3.0,
        "max_pages": 30,
        "max_depth": 2,
        "wait_for_element": "body",
        "scroll_pause_time": 2.0,
        "custom_selectors": {
            "main_content": ["main", ".content", ".help-content", "article"],
            "navigation": [".nav", ".navigation", ".breadcrumb"],
            "download_links": ["a[href$='.pdf']", "a[href*='download']"]
        }
    },
    
    "docs.autodesk.com": {
        "delay_between_requests": 2.5,
        "max_pages": 25,
        "max_depth": 3,
        "custom_selectors": {
            "main_content": [".docs-content", ".documentation", "main"],
            "code_blocks": ["pre", "code", ".highlight"]
        }
    },
    
    "knowledge.autodesk.com": {
        "delay_between_requests": 2.0,
        "max_pages": 20,
        "max_depth": 2,
        "custom_selectors": {
            "main_content": [".knowledge-content", ".article-content"],
            "related_links": [".related-articles", ".see-also"]
        }
    }
}


# Seletores CSS comuns para diferentes tipos de conteúdo
CONTENT_SELECTORS = {
    "main_content": [
        'main', '[role="main"]', '.main-content', '#main-content',
        '.content', '#content', '.post-content', '.article-content',
        '.page-content', '.entry-content', 'article', '.documentation',
        '.help-content', '.docs-content'
    ],
    
    "navigation": [
        'nav', '[role="navigation"]', '.nav', '.navigation',
        '.breadcrumb', '.breadcrumbs', '.menu', '.sidebar-nav'
    ],
    
    "download_links": [
        'a[href$=".pdf"]', 'a[href$=".doc"]', 'a[href$=".docx"]',
        'a[href$=".zip"]', 'a[href*="download"]', 'a[href*="attachment"]',
        '.download-link', '.file-download'
    ],
    
    "code_blocks": [
        'pre', 'code', '.highlight', '.codehilite', '.code-block',
        '.syntax-highlight', '.source-code'
    ],
    
    "images": [
        'img', '.image', '.figure', '.screenshot', '.diagram'
    ]
}


# Configurações de retry para diferentes tipos de erro
RETRY_CONFIGS = {
    "connection_error": {
        "max_retries": 3,
        "backoff_factor": 2.0,
        "retry_on_status": [500, 502, 503, 504]
    },
    
    "timeout_error": {
        "max_retries": 2,
        "backoff_factor": 1.5,
        "increase_timeout": True
    },
    
    "rate_limit": {
        "max_retries": 5,
        "backoff_factor": 3.0,
        "increase_delay": True
    }
}


# Configurações de análise de conteúdo
CONTENT_ANALYSIS_CONFIG = {
    "min_word_count": 10,
    "max_word_count": 50000,
    "min_sentence_count": 2,
    "languages_supported": ["pt", "en", "es", "fr"],
    "readability_thresholds": {
        "very_easy": 90,
        "easy": 80,
        "fairly_easy": 70,
        "standard": 60,
        "fairly_difficult": 50,
        "difficult": 30,
        "very_difficult": 0
    }
}


# Configurações de export
EXPORT_CONFIGS = {
    "csv": {
        "encoding": "utf-8",
        "delimiter": ",",
        "quotechar": '"',
        "max_cell_length": 32767  # Limite do Excel
    },
    
    "json": {
        "ensure_ascii": False,
        "indent": 2,
        "sort_keys": True
    },
    
    "txt": {
        "encoding": "utf-8",
        "line_separator": "\n",
        "chunk_separator": "\n\n---\n\n"
    }
}


def get_domain_config(url: str) -> Dict:
    """Retorna configuração específica para um domínio"""
    from urllib.parse import urlparse
    
    try:
        domain = urlparse(url).netloc.lower()
        
        # Procura configuração exata
        if domain in DOMAIN_SPECIFIC_CONFIGS:
            return DOMAIN_SPECIFIC_CONFIGS[domain]
        
        # Procura configuração por subdomínio
        for config_domain, config in DOMAIN_SPECIFIC_CONFIGS.items():
            if domain.endswith(config_domain):
                return config
        
        # Retorna configuração padrão
        return {}
        
    except Exception:
        return {}


def get_output_directory(base_dir: str = None) -> Path:
    """Retorna diretório de saída configurado"""
    if base_dir is None:
        base_dir = config.BASE_OUTPUT_DIR
    
    output_dir = Path(base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def validate_config() -> List[str]:
    """Valida configurações e retorna lista de erros"""
    errors = []
    
    # Valida valores numéricos
    if config.DEFAULT_CHUNK_SIZE < 100:
        errors.append("DEFAULT_CHUNK_SIZE deve ser >= 100")
    
    if config.DEFAULT_OVERLAP < 0:
        errors.append("DEFAULT_OVERLAP deve ser >= 0")
    
    if config.DEFAULT_OVERLAP >= config.DEFAULT_CHUNK_SIZE:
        errors.append("DEFAULT_OVERLAP deve ser menor que DEFAULT_CHUNK_SIZE")
    
    if config.DEFAULT_DELAY_BETWEEN_REQUESTS < 0.1:
        errors.append("DEFAULT_DELAY_BETWEEN_REQUESTS deve ser >= 0.1")
    
    if config.API_PORT < 1 or config.API_PORT > 65535:
        errors.append("API_PORT deve estar entre 1 e 65535")
    
    # Valida diretórios
    try:
        base_dir = Path(config.BASE_OUTPUT_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Não foi possível criar BASE_OUTPUT_DIR: {e}")
    
    return errors


def print_config_summary():
    """Imprime resumo das configurações"""
    print("\n📋 CONFIGURAÇÕES DO SISTEMA WEB SCRAPING RAG")
    print("="*60)
    
    print(f"📁 Diretório base: {config.BASE_OUTPUT_DIR}")
    print(f"🔢 Chunk size padrão: {config.DEFAULT_CHUNK_SIZE}")
    print(f"📄 Máximo de páginas: {config.DEFAULT_MAX_PAGES}")
    print(f"⏱️ Delay entre requests: {config.DEFAULT_DELAY_BETWEEN_REQUESTS}s")
    print(f"🌐 API Host:Port: {config.API_HOST}:{config.API_PORT}")
    print(f"🗄️ Banco de dados: {config.DATABASE_NAME}")
    
    print(f"\n🔧 Extensões para download: {len(config.DOWNLOADABLE_EXTENSIONS)} tipos")
    print(f"🎯 Domínios configurados: {len(DOMAIN_SPECIFIC_CONFIGS)}")
    
    # Valida configurações
    errors = validate_config()
    if errors:
        print(f"\n⚠️ ERROS DE CONFIGURAÇÃO:")
        for error in errors:
            print(f"   ❌ {error}")
    else:
        print(f"\n✅ Todas as configurações são válidas")


if __name__ == "__main__":
    print_config_summary()
