"""
Sistema de Gerenciamento de Dados Web Scraping - Versão 1.0
Autor: Assistant IA
Data: 2024

Este módulo gerencia todos os dados extraídos pelo sistema de web scraping,
incluindo persistência, busca, análise e integração com o sistema RAG.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import hashlib
import pickle
from dataclasses import dataclass

# Processamento de texto
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Para análise de conteúdo
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter
import re


@dataclass
class WebScrapingRecord:
    """Classe para representar um registro de web scraping"""
    page_id: str
    title: str
    url: str
    content: str
    metadata: Dict[str, Any]
    chunks_count: int
    extraction_timestamp: str
    file_path: str


@dataclass
class ChunkRecord:
    """Classe para representar um chunk de texto"""
    chunk_id: str
    page_id: str
    text: str
    char_count: int
    word_count: int
    readability_score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class WebScrapingDataManager:
    """
    Gerenciador de dados para sistema de web scraping
    """
    
    def __init__(self, data_dir: str = "web_scraping_data"):
        """
        Inicializa o gerenciador de dados
        
        Args:
            data_dir: Diretório base dos dados
        """
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "web_scraping.db"
        
        # Cria diretórios se não existirem
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializa banco de dados
        self.init_database()
        
        # Cache para embeddings e vetorizador TF-IDF
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.chunks_cache = []
        
        print(f"📂 WebScrapingDataManager inicializado em: {self.data_dir}")
    
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela principal de páginas web
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS web_pages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        page_id TEXT UNIQUE NOT NULL,
                        title TEXT,
                        url TEXT,
                        original_url TEXT,
                        content TEXT,
                        content_length INTEGER,
                        description TEXT,
                        keywords TEXT,
                        author TEXT,
                        language TEXT,
                        publication_date TEXT,
                        extraction_timestamp TEXT,
                        screenshot_path TEXT,
                        chunks_count INTEGER DEFAULT 0,
                        file_path TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de chunks
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS web_chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chunk_id TEXT UNIQUE NOT NULL,
                        page_id TEXT,
                        text TEXT,
                        char_count INTEGER,
                        word_count INTEGER,
                        readability_score REAL,
                        chunk_index INTEGER,
                        source_url TEXT,
                        page_title TEXT,
                        source_type TEXT DEFAULT 'web_scraping',
                        extraction_timestamp TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (page_id) REFERENCES web_pages (page_id)
                    )
                ''')
                
                # Tabela de downloads
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_url TEXT,
                        local_path TEXT,
                        filename TEXT,
                        size_bytes INTEGER,
                        file_type TEXT,
                        download_timestamp TEXT,
                        associated_page_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (associated_page_id) REFERENCES web_pages (page_id)
                    )
                ''')
                
                # Tabela de links extraídos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_page_id TEXT,
                        target_url TEXT,
                        link_text TEXT,
                        link_type TEXT, -- 'navigation', 'download', 'external'
                        is_processed BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_page_id) REFERENCES web_pages (page_id)
                    )
                ''')
                
                # Tabela de análises de conteúdo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        page_id TEXT,
                        word_count INTEGER,
                        unique_words INTEGER,
                        avg_sentence_length REAL,
                        readability_score REAL,
                        complexity_grade REAL,
                        top_keywords TEXT, -- JSON array
                        language_detected TEXT,
                        sentiment_score REAL,
                        analysis_timestamp TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (page_id) REFERENCES web_pages (page_id)
                    )
                ''')
                
                # Índices para performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_web_pages_page_id ON web_pages(page_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_web_pages_url ON web_pages(url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_web_chunks_page_id ON web_chunks(page_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_web_chunks_chunk_id ON web_chunks(chunk_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_page_id ON downloads(associated_page_id)')
                
                conn.commit()
                print("✅ Banco de dados inicializado com sucesso")
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
            raise
    
    def store_web_page(self, page_data: Dict[str, Any]) -> bool:
        """
        Armazena dados de uma página web
        
        Args:
            page_data: Dados da página extraída
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metadata = page_data.get('metadata', {})
                
                # Insere página principal
                cursor.execute('''
                    INSERT OR REPLACE INTO web_pages 
                    (page_id, title, url, original_url, content, content_length,
                     description, keywords, author, language, publication_date,
                     extraction_timestamp, screenshot_path, chunks_count, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    page_data['page_id'],
                    metadata.get('title', ''),
                    metadata.get('url', ''),
                    metadata.get('original_url', ''),
                    page_data.get('content', ''),
                    metadata.get('content_length', 0),
                    metadata.get('description', ''),
                    metadata.get('keywords', ''),
                    metadata.get('author', ''),
                    metadata.get('language', 'pt'),
                    metadata.get('publication_date', ''),
                    metadata.get('extraction_timestamp', ''),
                    metadata.get('screenshot_path', ''),
                    page_data.get('chunks_count', 0),
                    ""  # file_path será preenchido depois
                ))
                
                # Armazena links de navegação
                for link in page_data.get('navigation_links', []):
                    cursor.execute('''
                        INSERT OR IGNORE INTO extracted_links 
                        (source_page_id, target_url, link_type)
                        VALUES (?, ?, ?)
                    ''', (page_data['page_id'], link, 'navigation'))
                
                # Armazena links de download
                for link in page_data.get('download_links', []):
                    cursor.execute('''
                        INSERT OR IGNORE INTO extracted_links 
                        (source_page_id, target_url, link_type)
                        VALUES (?, ?, ?)
                    ''', (page_data['page_id'], link, 'download'))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao armazenar página {page_data.get('page_id', 'unknown')}: {e}")
            return False
    
    def store_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Armazena chunks de texto
        
        Args:
            chunks: Lista de chunks
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for chunk in chunks:
                    metadata = chunk.get('metadata', {})
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO web_chunks 
                        (chunk_id, page_id, text, char_count, word_count,
                         readability_score, chunk_index, source_url, page_title,
                         source_type, extraction_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        chunk['chunk_id'],
                        chunk['chunk_id'].split('_')[0],  # Extrai page_id do chunk_id
                        chunk['text'],
                        chunk['char_count'],
                        chunk['word_count'],
                        chunk['readability_score'],
                        metadata.get('chunk_index', 0),
                        metadata.get('source_url', ''),
                        metadata.get('page_title', ''),
                        metadata.get('source_type', 'web_scraping'),
                        metadata.get('extraction_timestamp', '')
                    ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao armazenar chunks: {e}")
            return False
    
    def store_downloads(self, downloads: List[Dict[str, Any]], page_id: str = None) -> bool:
        """
        Armazena informações de downloads
        
        Args:
            downloads: Lista de downloads
            page_id: ID da página associada
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for download in downloads:
                    # Determina tipo de arquivo
                    filename = download.get('filename', '')
                    file_extension = Path(filename).suffix.lower().lstrip('.')
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO downloads 
                        (original_url, local_path, filename, size_bytes,
                         file_type, download_timestamp, associated_page_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        download.get('original_url', ''),
                        download.get('local_path', ''),
                        filename,
                        download.get('size_bytes', 0),
                        file_extension,
                        download.get('download_timestamp', ''),
                        page_id
                    ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao armazenar downloads: {e}")
            return False
    
    def analyze_content(self, page_id: str, content: str) -> Dict[str, Any]:
        """
        Analisa conteúdo de uma página
        
        Args:
            page_id: ID da página
            content: Conteúdo textual
            
        Returns:
            Dados da análise
        """
        if not content or len(content.strip()) < 10:
            return {}
        
        try:
            # Análise básica
            words = content.split()
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Estatísticas básicas
            word_count = len(words)
            unique_words = len(set(word.lower() for word in words if word.isalpha()))
            avg_sentence_length = word_count / len(sentences) if sentences else 0
            
            # Análise de legibilidade
            readability_score = flesch_reading_ease(content) if content else 0
            complexity_grade = flesch_kincaid_grade(content) if content else 0
            
            # Palavras mais frequentes
            word_freq = Counter(word.lower() for word in words if word.isalpha() and len(word) > 3)
            top_keywords = [word for word, _ in word_freq.most_common(20)]
            
            analysis = {
                'page_id': page_id,
                'word_count': word_count,
                'unique_words': unique_words,
                'avg_sentence_length': avg_sentence_length,
                'readability_score': readability_score,
                'complexity_grade': complexity_grade,
                'top_keywords': json.dumps(top_keywords),
                'language_detected': 'pt',  # Por enquanto fixo
                'sentiment_score': 0.0,  # Implementar depois
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Armazena no banco
            self.store_content_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erro na análise de conteúdo para {page_id}: {e}")
            return {}
    
    def store_content_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Armazena análise de conteúdo no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO content_analysis 
                    (page_id, word_count, unique_words, avg_sentence_length,
                     readability_score, complexity_grade, top_keywords,
                     language_detected, sentiment_score, analysis_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis['page_id'],
                    analysis['word_count'],
                    analysis['unique_words'],
                    analysis['avg_sentence_length'],
                    analysis['readability_score'],
                    analysis['complexity_grade'],
                    analysis['top_keywords'],
                    analysis['language_detected'],
                    analysis['sentiment_score'],
                    analysis['analysis_timestamp']
                ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao armazenar análise: {e}")
            return False
    
    def search_chunks(self, query: str, limit: int = 10, 
                     min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """
        Busca chunks similares usando TF-IDF
        
        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            min_similarity: Similaridade mínima
            
        Returns:
            Lista de chunks relevantes
        """
        try:
            # Carrega chunks se necessário
            if not self.chunks_cache:
                self.load_chunks_cache()
            
            if not self.chunks_cache:
                return []
            
            # Inicializa TF-IDF se necessário
            if self.tfidf_vectorizer is None:
                self.init_tfidf_search()
            
            # Vetoriza query
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calcula similaridades
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Ordena por similaridade
            chunk_scores = list(zip(self.chunks_cache, similarities))
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Filtra e formata resultados
            results = []
            for chunk, score in chunk_scores[:limit]:
                if score >= min_similarity:
                    results.append({
                        'chunk_id': chunk['chunk_id'],
                        'text': chunk['text'],
                        'similarity_score': float(score),
                        'source_url': chunk.get('source_url', ''),
                        'page_title': chunk.get('page_title', ''),
                        'char_count': chunk.get('char_count', 0),
                        'readability_score': chunk.get('readability_score', 0)
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def load_chunks_cache(self):
        """Carrega chunks no cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chunk_id, text, source_url, page_title,
                           char_count, readability_score
                    FROM web_chunks
                    WHERE LENGTH(text) > 50
                    ORDER BY id
                ''')
                
                self.chunks_cache = []
                for row in cursor.fetchall():
                    self.chunks_cache.append({
                        'chunk_id': row[0],
                        'text': row[1],
                        'source_url': row[2],
                        'page_title': row[3],
                        'char_count': row[4],
                        'readability_score': row[5]
                    })
                
                print(f"📚 {len(self.chunks_cache)} chunks carregados no cache")
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao carregar chunks: {e}")
    
    def init_tfidf_search(self):
        """Inicializa busca TF-IDF"""
        if not self.chunks_cache:
            return
        
        try:
            # Extrai textos
            texts = [chunk['text'] for chunk in self.chunks_cache]
            
            # Inicializa TF-IDF
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words=None,  # Poderia usar stop words em português
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            
            # Treina e transforma
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            print(f"🔍 TF-IDF inicializado com {self.tfidf_matrix.shape[0]} documentos")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar TF-IDF: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estatísticas de páginas
                cursor.execute('SELECT COUNT(*) FROM web_pages')
                total_pages = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM web_chunks')
                total_chunks = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM downloads')
                total_downloads = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(content_length) FROM web_pages')
                total_content_length = cursor.fetchone()[0] or 0
                
                cursor.execute('SELECT AVG(readability_score) FROM content_analysis')
                avg_readability = cursor.fetchone()[0] or 0
                
                # Top domínios
                cursor.execute('''
                    SELECT 
                        SUBSTR(url, 1, INSTR(url, '/', 9) - 1) as domain,
                        COUNT(*) as count
                    FROM web_pages
                    WHERE url LIKE 'http%'
                    GROUP BY domain
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                top_domains = cursor.fetchall()
                
                # Estatísticas de downloads por tipo
                cursor.execute('''
                    SELECT file_type, COUNT(*) as count, SUM(size_bytes) as total_size
                    FROM downloads
                    GROUP BY file_type
                    ORDER BY count DESC
                ''')
                download_stats = cursor.fetchall()
                
                return {
                    'database_stats': {
                        'total_pages': total_pages,
                        'total_chunks': total_chunks,
                        'total_downloads': total_downloads,
                        'total_content_length': total_content_length,
                        'average_readability': round(avg_readability, 2)
                    },
                    'top_domains': [{'domain': d[0], 'count': d[1]} for d in top_domains],
                    'download_stats': [
                        {'file_type': d[0], 'count': d[1], 'total_size': d[2]} 
                        for d in download_stats
                    ],
                    'cache_info': {
                        'chunks_cached': len(self.chunks_cache),
                        'tfidf_initialized': self.tfidf_vectorizer is not None
                    }
                }
                
        except sqlite3.Error as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def export_to_csv(self, output_dir: str = None) -> Dict[str, str]:
        """Exporta dados para CSV"""
        if output_dir is None:
            output_dir = self.data_dir / "exports"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Exporta páginas
                pages_df = pd.read_sql_query('''
                    SELECT page_id, title, url, content_length, description,
                           author, language, extraction_timestamp, chunks_count
                    FROM web_pages
                    ORDER BY extraction_timestamp DESC
                ''', conn)
                
                pages_file = output_dir / f"web_pages_{timestamp}.csv"
                pages_df.to_csv(pages_file, index=False, encoding='utf-8')
                exported_files['pages'] = str(pages_file)
                
                # Exporta chunks
                chunks_df = pd.read_sql_query('''
                    SELECT chunk_id, page_id, text, char_count, word_count,
                           readability_score, source_url, page_title
                    FROM web_chunks
                    ORDER BY chunk_id
                ''', conn)
                
                chunks_file = output_dir / f"web_chunks_{timestamp}.csv"
                chunks_df.to_csv(chunks_file, index=False, encoding='utf-8')
                exported_files['chunks'] = str(chunks_file)
                
                # Exporta downloads
                downloads_df = pd.read_sql_query('''
                    SELECT original_url, filename, size_bytes, file_type,
                           download_timestamp, associated_page_id
                    FROM downloads
                    ORDER BY download_timestamp DESC
                ''', conn)
                
                if not downloads_df.empty:
                    downloads_file = output_dir / f"downloads_{timestamp}.csv"
                    downloads_df.to_csv(downloads_file, index=False, encoding='utf-8')
                    exported_files['downloads'] = str(downloads_file)
                
                print(f"📊 Dados exportados para: {output_dir}")
                return exported_files
                
        except Exception as e:
            print(f"❌ Erro na exportação: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Remove dados antigos do banco"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove chunks antigos primeiro (chave estrangeira)
                cursor.execute('''
                    DELETE FROM web_chunks 
                    WHERE extraction_timestamp < ?
                ''', (cutoff_iso,))
                chunks_deleted = cursor.rowcount
                
                # Remove páginas antigas
                cursor.execute('''
                    DELETE FROM web_pages 
                    WHERE extraction_timestamp < ?
                ''', (cutoff_iso,))
                pages_deleted = cursor.rowcount
                
                # Remove downloads órfãos
                cursor.execute('''
                    DELETE FROM downloads 
                    WHERE associated_page_id NOT IN (
                        SELECT page_id FROM web_pages
                    )
                ''')
                downloads_deleted = cursor.rowcount
                
                conn.commit()
                
                total_deleted = pages_deleted + chunks_deleted + downloads_deleted
                print(f"🧹 Limpeza concluída: {total_deleted} registros removidos")
                
                return total_deleted
                
        except sqlite3.Error as e:
            print(f"❌ Erro na limpeza: {e}")
            return 0


def main():
    """Função principal para testes"""
    # Testa o gerenciador
    manager = WebScrapingDataManager("web_scraping_test")
    
    # Estatísticas
    stats = manager.get_statistics()
    print("\n📊 ESTATÍSTICAS DO BANCO:")
    for key, value in stats.get('database_stats', {}).items():
        print(f"  {key}: {value}")
    
    # Busca de exemplo
    if stats.get('database_stats', {}).get('total_chunks', 0) > 0:
        results = manager.search_chunks("autodesk architecture design", limit=5)
        print(f"\n🔍 BUSCA DE EXEMPLO: {len(results)} resultados encontrados")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['chunk_id'][:50]}... (score: {result['similarity_score']:.3f})")


if __name__ == "__main__":
    main()
