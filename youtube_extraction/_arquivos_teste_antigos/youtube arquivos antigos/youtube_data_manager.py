"""
Gerenciador de Dados para YouTube Transcripts
Sistema de gerenciamento e persistência de dados extraídos do YouTube
"""

import json
import csv
import pickle
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class YouTubeDataManager:
    """
    Gerenciador completo de dados para transcrições do YouTube
    """
    
    def __init__(self, base_dir: str = "youtube_extracted_data"):
        """
        Inicializa o gerenciador de dados do YouTube
        
        Args:
            base_dir: Diretório base para armazenamento
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Estrutura de diretórios
        self.dirs = {
            'transcripts': self.base_dir / 'transcripts',
            'metadata': self.base_dir / 'metadata', 
            'chunks': self.base_dir / 'chunks',
            'rag_content': self.base_dir / 'rag_content',
            'database': self.base_dir / 'database',
            'exports': self.base_dir / 'exports',
            'backups': self.base_dir / 'backups'
        }
        
        for directory in self.dirs.values():
            directory.mkdir(exist_ok=True)
        
        # Arquivo principal do banco
        self.db_file = self.dirs['database'] / 'youtube_transcripts.db'
        self._init_database()
    
    def _init_database(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Tabela principal de vídeos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    url TEXT,
                    extraction_date TEXT,
                    total_segments INTEGER,
                    total_duration REAL,
                    text_length INTEGER,
                    language TEXT,
                    transcript_type TEXT,
                    word_count INTEGER,
                    duration_minutes REAL,
                    readability_score REAL,
                    sentiment TEXT,
                    keywords_json TEXT,
                    topics_json TEXT,
                    metadata_json TEXT,
                    analysis_json TEXT,
                    created_at TEXT DEFAULT '',
                    updated_at TEXT DEFAULT ''
                )
            ''')
            
            # Tabela de chunks para RAG
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    video_id TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    text_length INTEGER,
                    word_count INTEGER,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    language TEXT,
                    chunk_metadata_json TEXT,
                    created_at TEXT DEFAULT '',
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Tabela de segmentos individuais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id TEXT PRIMARY KEY,
                    video_id TEXT,
                    segment_index INTEGER,
                    text TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    word_count INTEGER,
                    created_at TEXT DEFAULT '',
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Tabela de análises de conteúdo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_analysis (
                    analysis_id TEXT PRIMARY KEY,
                    video_id TEXT,
                    analysis_type TEXT,
                    analysis_data_json TEXT,
                    confidence_score REAL,
                    created_at TEXT DEFAULT '',
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_video_id ON chunks(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks(text)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_segments_video_id ON segments(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_language ON videos(language)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)')
            
            conn.commit()
            conn.close()
            
            logger.info("Base de dados inicializada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    def save_video_data(self, video_data: Dict[str, Any]) -> bool:
        """
        Salva dados completos de um vídeo no banco
        
        Args:
            video_data: Dados completos do vídeo processado
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Extrair informações principais
            video_id = video_data.get('video_id')
            metadata = video_data.get('metadata', {})
            transcript_data = video_data.get('transcript_data', {})
            analysis = video_data.get('analysis', {})
            chunks = video_data.get('chunks', [])
            segments = transcript_data.get('segments', [])
            
            # Inserir dados do vídeo
            cursor.execute('''
                INSERT OR REPLACE INTO videos VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                metadata.get('title', ''),
                metadata.get('description', ''),
                metadata.get('url', ''),
                transcript_data.get('extraction_timestamp', ''),
                transcript_data.get('total_segments', 0),
                transcript_data.get('total_duration', 0),
                transcript_data.get('text_length', 0),
                transcript_data.get('transcript_info', {}).get('language', ''),
                transcript_data.get('transcript_info', {}).get('type', ''),
                len(transcript_data.get('full_text', '').split()),
                transcript_data.get('total_duration', 0) / 60,
                analysis.get('content_analysis', {}).get('readability_score', 0),
                analysis.get('sentiment', 'neutral'),
                json.dumps(analysis.get('keywords', [])),
                json.dumps(analysis.get('topics', [])),
                json.dumps(metadata),
                json.dumps(analysis),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Inserir chunks
            for chunk in chunks:
                cursor.execute('''
                    INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk['chunk_id'],
                    chunk['video_id'],
                    chunk['chunk_index'],
                    chunk['text'],
                    chunk['text_length'],
                    chunk['word_count'],
                    chunk['start_time'],
                    chunk['end_time'],
                    chunk['end_time'] - chunk['start_time'],
                    chunk.get('chunk_metadata', {}).get('language', ''),
                    json.dumps(chunk.get('chunk_metadata', {})),
                    datetime.now().isoformat()
                ))
            
            # Inserir segmentos
            for segment in segments:
                segment_id = f"{video_id}_segment_{segment['index']}"
                cursor.execute('''
                    INSERT OR REPLACE INTO segments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    segment_id,
                    video_id,
                    segment['index'],
                    segment['text'],
                    segment['start'],
                    segment['end'],
                    segment['duration'],
                    len(segment['text'].split()),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Dados do vídeo {video_id} salvos com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados do vídeo: {e}")
            return False
    
    def get_video_data(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados completos de um vídeo
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dados do vídeo ou None se não encontrado
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Buscar dados do vídeo
            cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
            video_row = cursor.fetchone()
            
            if not video_row:
                return None
            
            # Buscar chunks
            cursor.execute('SELECT * FROM chunks WHERE video_id = ? ORDER BY chunk_index', (video_id,))
            chunks_rows = cursor.fetchall()
            
            # Buscar segmentos
            cursor.execute('SELECT * FROM segments WHERE video_id = ? ORDER BY segment_index', (video_id,))
            segments_rows = cursor.fetchall()
            
            conn.close()
            
            # Montar estrutura de dados
            video_data = {
                'video_id': video_row[0],
                'title': video_row[1],
                'description': video_row[2],
                'url': video_row[3],
                'extraction_date': video_row[4],
                'total_segments': video_row[5],
                'total_duration': video_row[6],
                'text_length': video_row[7],
                'language': video_row[8],
                'transcript_type': video_row[9],
                'word_count': video_row[10],
                'duration_minutes': video_row[11],
                'readability_score': video_row[12],
                'sentiment': video_row[13],
                'keywords': json.loads(video_row[14] or '[]'),
                'topics': json.loads(video_row[15] or '[]'),
                'metadata': json.loads(video_row[16] or '{}'),
                'analysis': json.loads(video_row[17] or '{}'),
                'created_at': video_row[18],
                'updated_at': video_row[19]
            }
            
            # Adicionar chunks
            chunks = []
            for chunk_row in chunks_rows:
                chunks.append({
                    'chunk_id': chunk_row[0],
                    'video_id': chunk_row[1],
                    'chunk_index': chunk_row[2],
                    'text': chunk_row[3],
                    'text_length': chunk_row[4],
                    'word_count': chunk_row[5],
                    'start_time': chunk_row[6],
                    'end_time': chunk_row[7],
                    'duration': chunk_row[8],
                    'language': chunk_row[9],
                    'chunk_metadata': json.loads(chunk_row[10] or '{}'),
                    'created_at': chunk_row[11]
                })
            
            # Adicionar segmentos
            segments = []
            for segment_row in segments_rows:
                segments.append({
                    'segment_id': segment_row[0],
                    'video_id': segment_row[1],
                    'segment_index': segment_row[2],
                    'text': segment_row[3],
                    'start_time': segment_row[4],
                    'end_time': segment_row[5],
                    'duration': segment_row[6],
                    'word_count': segment_row[7],
                    'created_at': segment_row[8]
                })
            
            video_data['chunks'] = chunks
            video_data['segments'] = segments
            
            return video_data
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados do vídeo: {e}")
            return None
    
    def list_videos(self, limit: int = None, order_by: str = 'created_at DESC') -> List[Dict[str, Any]]:
        """
        Lista vídeos armazenados
        
        Args:
            limit: Número máximo de resultados
            order_by: Campo para ordenação
            
        Returns:
            Lista de vídeos
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            query = f'SELECT * FROM videos ORDER BY {order_by}'
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            conn.close()
            
            videos = []
            for row in rows:
                videos.append({
                    'video_id': row[0],
                    'title': row[1],
                    'description': row[2][:200] + '...' if len(row[2] or '') > 200 else row[2],
                    'url': row[3],
                    'extraction_date': row[4],
                    'total_segments': row[5],
                    'duration_minutes': row[11],
                    'text_length': row[7],
                    'language': row[8],
                    'transcript_type': row[9],
                    'sentiment': row[13],
                    'created_at': row[18]
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Erro ao listar vídeos: {e}")
            return []
    
    def search_content(self, query: str, search_type: str = 'all', limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca conteúdo nos dados armazenados
        
        Args:
            query: Termo de busca
            search_type: Tipo de busca ('chunks', 'segments', 'videos', 'all')
            limit: Número máximo de resultados
            
        Returns:
            Lista de resultados da busca
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            results = []
            
            if search_type in ['all', 'chunks']:
                # Buscar em chunks
                cursor.execute('''
                    SELECT c.chunk_id, c.video_id, c.chunk_index, c.text, c.start_time, c.end_time,
                           v.title, v.url, v.language
                    FROM chunks c
                    JOIN videos v ON c.video_id = v.video_id
                    WHERE c.text LIKE ?
                    ORDER BY c.video_id, c.chunk_index
                    LIMIT ?
                ''', (f'%{query}%', limit))
                
                for row in cursor.fetchall():
                    results.append({
                        'type': 'chunk',
                        'chunk_id': row[0],
                        'video_id': row[1],
                        'chunk_index': row[2],
                        'text': row[3],
                        'start_time': row[4],
                        'end_time': row[5],
                        'video_title': row[6],
                        'video_url': row[7],
                        'language': row[8],
                        'youtube_url_with_time': f'{row[7]}&t={int(row[4])}s'
                    })
            
            if search_type in ['all', 'segments']:
                # Buscar em segmentos
                cursor.execute('''
                    SELECT s.segment_id, s.video_id, s.segment_index, s.text, s.start_time, s.end_time,
                           v.title, v.url, v.language
                    FROM segments s
                    JOIN videos v ON s.video_id = v.video_id
                    WHERE s.text LIKE ?
                    ORDER BY s.video_id, s.segment_index
                    LIMIT ?
                ''', (f'%{query}%', limit // 2))
                
                for row in cursor.fetchall():
                    results.append({
                        'type': 'segment',
                        'segment_id': row[0],
                        'video_id': row[1],
                        'segment_index': row[2],
                        'text': row[3],
                        'start_time': row[4],
                        'end_time': row[5],
                        'video_title': row[6],
                        'video_url': row[7],
                        'language': row[8],
                        'youtube_url_with_time': f'{row[7]}&t={int(row[4])}s'
                    })
            
            if search_type in ['all', 'videos']:
                # Buscar em vídeos
                cursor.execute('''
                    SELECT video_id, title, description, url, language, duration_minutes, sentiment
                    FROM videos
                    WHERE title LIKE ? OR description LIKE ? OR keywords_json LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit // 4))
                
                for row in cursor.fetchall():
                    results.append({
                        'type': 'video',
                        'video_id': row[0],
                        'title': row[1],
                        'description': row[2][:200] + '...' if len(row[2] or '') > 200 else row[2],
                        'url': row[3],
                        'language': row[4],
                        'duration_minutes': row[5],
                        'sentiment': row[6]
                    })
            
            conn.close()
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
    
    def export_to_csv(self, output_file: str = None) -> str:
        """
        Exporta todos os dados para CSV
        
        Args:
            output_file: Arquivo de saída (opcional)
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.dirs['exports'] / f'youtube_data_export_{timestamp}.csv'
            
            conn = sqlite3.connect(self.db_file)
            
            # Exportar dados principais com chunks
            query = '''
                SELECT 
                    v.video_id,
                    v.title,
                    v.description,
                    v.url,
                    v.language,
                    v.transcript_type,
                    v.duration_minutes,
                    v.text_length,
                    v.word_count,
                    v.readability_score,
                    v.sentiment,
                    v.keywords_json,
                    v.topics_json,
                    c.chunk_id,
                    c.chunk_index,
                    c.text as chunk_text,
                    c.start_time,
                    c.end_time,
                    c.duration as chunk_duration,
                    v.created_at
                FROM videos v
                LEFT JOIN chunks c ON v.video_id = c.video_id
                ORDER BY v.created_at DESC, c.chunk_index
            '''
            
            df = pd.read_sql_query(query, conn)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            conn.close()
            
            logger.info(f"Dados exportados para: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return ""
    
    def export_to_json(self, output_file: str = None) -> str:
        """
        Exporta todos os dados para JSON
        
        Args:
            output_file: Arquivo de saída (opcional)
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.dirs['exports'] / f'youtube_data_export_{timestamp}.json'
            
            videos = self.list_videos()
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_videos': len(videos),
                'videos': []
            }
            
            for video in videos:
                video_data = self.get_video_data(video['video_id'])
                if video_data:
                    export_data['videos'].append(video_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dados exportados para: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Erro ao exportar JSON: {e}")
            return ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos dados armazenados
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute('SELECT COUNT(*) FROM videos')
            total_videos = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM chunks')
            total_chunks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM segments')
            total_segments = cursor.fetchone()[0]
            
            # Estatísticas de conteúdo
            cursor.execute('SELECT SUM(duration_minutes), AVG(duration_minutes) FROM videos')
            duration_stats = cursor.fetchone()
            
            cursor.execute('SELECT SUM(text_length), AVG(text_length) FROM videos')
            text_stats = cursor.fetchone()
            
            # Estatísticas por idioma
            cursor.execute('SELECT language, COUNT(*) FROM videos GROUP BY language')
            language_stats = dict(cursor.fetchall())
            
            # Estatísticas por sentimento
            cursor.execute('SELECT sentiment, COUNT(*) FROM videos GROUP BY sentiment')
            sentiment_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'totals': {
                    'videos': total_videos,
                    'chunks': total_chunks,
                    'segments': total_segments
                },
                'content': {
                    'total_duration_minutes': duration_stats[0] or 0,
                    'average_duration_minutes': duration_stats[1] or 0,
                    'total_text_length': text_stats[0] or 0,
                    'average_text_length': text_stats[1] or 0
                },
                'languages': language_stats,
                'sentiments': sentiment_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def create_backup(self) -> str:
        """
        Cria backup completo dos dados
        
        Returns:
            Caminho do arquivo de backup
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.dirs['backups'] / f'youtube_backup_{timestamp}.json'
            
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'statistics': self.get_statistics(),
                'data': {
                    'videos': []
                }
            }
            
            videos = self.list_videos()
            for video in videos:
                video_data = self.get_video_data(video['video_id'])
                if video_data:
                    backup_data['data']['videos'].append(video_data)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Backup criado: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return ""

# Exemplo de uso
if __name__ == "__main__":
    # Criar gerenciador
    manager = YouTubeDataManager()
    
    # Mostrar estatísticas
    stats = manager.get_statistics()
    print("📊 Estatísticas dos dados:")
    print(f"  - Total de vídeos: {stats.get('totals', {}).get('videos', 0)}")
    print(f"  - Total de chunks: {stats.get('totals', {}).get('chunks', 0)}")
    print(f"  - Duração total: {stats.get('content', {}).get('total_duration_minutes', 0):.1f} minutos")
    
    # Listar vídeos
    videos = manager.list_videos(limit=5)
    print(f"\n📹 Últimos vídeos processados:")
    for video in videos:
        print(f"  - {video['title'][:50]}... ({video['duration_minutes']:.1f}min)")
