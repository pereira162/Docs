"""
Sistema de Extração de Transcrições do YouTube para RAG
Sistema abrangente para extração e análise de transcrições do YouTube
"""

import json
import csv
import pickle
import sqlite3
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs
import hashlib

# Bibliotecas principais para YouTube
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import JSONFormatter, TextFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    print("WARNING: youtube-transcript-api não instalado. Execute: pip install youtube-transcript-api")
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("WARNING: requests não instalado. Execute: pip install requests")
    REQUESTS_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeTranscriptExtractor:
    """
    Extrator abrangente de transcrições do YouTube para sistema RAG
    """
    
    def __init__(self, output_dir: str = "youtube_extracted_data"):
        """
        Inicializa o extrator de transcrições do YouTube
        
        Args:
            output_dir: Diretório para salvar dados extraídos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Criar subdiretórios
        self.dirs = {
            'transcripts': self.output_dir / 'transcripts',
            'metadata': self.output_dir / 'metadata',
            'chunks': self.output_dir / 'chunks',
            'rag_content': self.output_dir / 'rag_content',
            'database': self.output_dir / 'database'
        }
        
        for directory in self.dirs.values():
            directory.mkdir(exist_ok=True)
        
        # Inicializar APIs
        if YOUTUBE_TRANSCRIPT_AVAILABLE:
            self.youtube_api = YouTubeTranscriptApi()
            self.json_formatter = JSONFormatter()
            self.text_formatter = TextFormatter()
        else:
            self.youtube_api = None
            logger.warning("YouTube Transcript API não disponível")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrai o ID do vídeo de uma URL do YouTube
        
        Args:
            url: URL do YouTube
            
        Returns:
            ID do vídeo ou None se inválido
        """
        try:
            # Diferentes formatos de URL do YouTube
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/v/([^&\n?#]+)',
                r'youtube\.com/watch\?.*v=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Se já for um ID (sem protocolo)
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair ID do vídeo: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Obtém metadados do vídeo usando YouTube Data API (básico)
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dicionário com metadados básicos
        """
        try:
            # Metadados básicos - pode ser expandido com YouTube Data API
            metadata = {
                'video_id': video_id,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'extraction_date': datetime.now().isoformat(),
                'extractor_version': '1.0.0'
            }
            
            # Tentar obter informações básicas da página
            if REQUESTS_AVAILABLE:
                try:
                    url = f'https://www.youtube.com/watch?v={video_id}'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    # Extrair título básico
                    title_match = re.search(r'<title>(.+?) - YouTube</title>', response.text)
                    if title_match:
                        metadata['title'] = title_match.group(1).strip()
                    
                    # Extrair descrição básica
                    desc_match = re.search(r'"description":{"simpleText":"([^"]+)"', response.text)
                    if desc_match:
                        metadata['description'] = desc_match.group(1)[:500]  # Primeiros 500 chars
                        
                except Exception as e:
                    logger.warning(f"Não foi possível obter metadados da página: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao obter metadados do vídeo: {e}")
            return {
                'video_id': video_id,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'extraction_date': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_available_transcripts(self, video_id: str) -> Dict[str, Any]:
        """
        Lista todas as transcrições disponíveis para um vídeo
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Informações sobre transcrições disponíveis
        """
        if not self.youtube_api:
            return {'error': 'YouTube Transcript API não disponível'}
        
        try:
            transcript_list = self.youtube_api.list(video_id)
            
            available_transcripts = []
            for transcript in transcript_list:
                transcript_info = {
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable,
                    'translation_languages': [lang.language_code for lang in transcript.translation_languages] if transcript.is_translatable else []
                }
                available_transcripts.append(transcript_info)
            
            return {
                'video_id': video_id,
                'total_transcripts': len(available_transcripts),
                'transcripts': available_transcripts,
                'has_manual': any(not t['is_generated'] for t in available_transcripts),
                'has_generated': any(t['is_generated'] for t in available_transcripts)
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar transcrições: {e}")
            return {'error': str(e), 'video_id': video_id}
    
    def extract_transcript(self, video_id: str, languages: List[str] = None, prefer_manual: bool = True) -> Dict[str, Any]:
        """
        Extrai transcrição de um vídeo
        
        Args:
            video_id: ID do vídeo
            languages: Lista de idiomas preferidos (ex: ['pt', 'en'])
            prefer_manual: Preferir transcrições manuais
            
        Returns:
            Dados da transcrição extraída
        """
        if not self.youtube_api:
            return {'error': 'YouTube Transcript API não disponível'}
        
        try:
            # Definir idiomas padrão se não especificado
            if languages is None:
                languages = ['pt', 'pt-BR', 'en', 'es']
            
            transcript_list = self.youtube_api.list(video_id)
            
            # Tentar encontrar transcrição preferida
            transcript = None
            transcript_info = None
            
            try:
                if prefer_manual:
                    # Tentar manual primeiro
                    try:
                        transcript = transcript_list.find_manually_created_transcript(languages)
                        transcript_info = {'type': 'manual', 'language': transcript.language_code}
                    except:
                        # Se não encontrar manual, tentar gerada
                        transcript = transcript_list.find_generated_transcript(languages)
                        transcript_info = {'type': 'generated', 'language': transcript.language_code}
                else:
                    # Tentar qualquer uma
                    transcript = transcript_list.find_transcript(languages)
                    transcript_info = {
                        'type': 'manual' if not transcript.is_generated else 'generated',
                        'language': transcript.language_code
                    }
            except:
                # Última tentativa: pegar qualquer transcrição disponível
                if transcript_list:
                    transcript = list(transcript_list)[0]
                    transcript_info = {
                        'type': 'manual' if not transcript.is_generated else 'generated',
                        'language': transcript.language_code
                    }
            
            if not transcript:
                return {'error': 'Nenhuma transcrição encontrada', 'video_id': video_id}
            
            # Obter dados da transcrição
            transcript_data = transcript.fetch()
            
            # Processar segmentos
            segments = []
            full_text = ""
            total_duration = 0
            
            for i, segment in enumerate(transcript_data):
                segment_info = {
                    'index': i,
                    'text': segment.text.strip(),
                    'start': segment.start,
                    'duration': segment.duration,
                    'end': segment.start + segment.duration
                }
                segments.append(segment_info)
                full_text += segment.text + " "
                total_duration = max(total_duration, segment_info['end'])
            
            # Compilar resultado
            result = {
                'video_id': video_id,
                'extraction_timestamp': datetime.now().isoformat(),
                'transcript_info': transcript_info,
                'total_segments': len(segments),
                'total_duration': total_duration,
                'full_text': full_text.strip(),
                'segments': segments,
                'text_length': len(full_text.strip()),
                'avg_segment_duration': total_duration / len(segments) if segments else 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao extrair transcrição: {e}")
            return {'error': str(e), 'video_id': video_id}
    
    def create_rag_chunks(self, transcript_data: Dict[str, Any], chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Cria chunks para RAG a partir da transcrição
        
        Args:
            transcript_data: Dados da transcrição
            chunk_size: Tamanho do chunk em caracteres
            overlap: Sobreposição entre chunks
            
        Returns:
            Lista de chunks para RAG
        """
        try:
            chunks = []
            full_text = transcript_data.get('full_text', '')
            segments = transcript_data.get('segments', [])
            video_id = transcript_data.get('video_id', 'unknown')
            
            if not full_text:
                return chunks
            
            # Dividir texto em chunks
            words = full_text.split()
            current_chunk = []
            current_length = 0
            chunk_index = 0
            
            for word in words:
                current_chunk.append(word)
                current_length += len(word) + 1  # +1 para espaço
                
                if current_length >= chunk_size:
                    # Criar chunk
                    chunk_text = ' '.join(current_chunk)
                    
                    # Encontrar segmentos correspondentes
                    chunk_segments = self._find_segments_for_text(chunk_text, segments)
                    
                    chunk_info = {
                        'chunk_id': f"{video_id}_chunk_{chunk_index}",
                        'video_id': video_id,
                        'chunk_index': chunk_index,
                        'text': chunk_text,
                        'text_length': len(chunk_text),
                        'word_count': len(current_chunk),
                        'segments_included': len(chunk_segments),
                        'start_time': chunk_segments[0]['start'] if chunk_segments else 0,
                        'end_time': chunk_segments[-1]['end'] if chunk_segments else 0,
                        'chunk_metadata': {
                            'language': transcript_data.get('transcript_info', {}).get('language', 'unknown'),
                            'transcript_type': transcript_data.get('transcript_info', {}).get('type', 'unknown'),
                            'extraction_date': transcript_data.get('extraction_timestamp', ''),
                            'chunk_creation_date': datetime.now().isoformat()
                        }
                    }
                    
                    chunks.append(chunk_info)
                    chunk_index += 1
                    
                    # Preparar próximo chunk com overlap
                    overlap_words = max(0, min(overlap // 10, len(current_chunk) // 4))  # Aproximação
                    current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                    current_length = sum(len(word) + 1 for word in current_chunk)
            
            # Chunk final se sobrar texto
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk_segments = self._find_segments_for_text(chunk_text, segments)
                
                chunk_info = {
                    'chunk_id': f"{video_id}_chunk_{chunk_index}",
                    'video_id': video_id,
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'text_length': len(chunk_text),
                    'word_count': len(current_chunk),
                    'segments_included': len(chunk_segments),
                    'start_time': chunk_segments[0]['start'] if chunk_segments else 0,
                    'end_time': chunk_segments[-1]['end'] if chunk_segments else 0,
                    'chunk_metadata': {
                        'language': transcript_data.get('transcript_info', {}).get('language', 'unknown'),
                        'transcript_type': transcript_data.get('transcript_info', {}).get('type', 'unknown'),
                        'extraction_date': transcript_data.get('extraction_timestamp', ''),
                        'chunk_creation_date': datetime.now().isoformat()
                    }
                }
                
                chunks.append(chunk_info)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Erro ao criar chunks RAG: {e}")
            return []
    
    def _find_segments_for_text(self, text: str, segments: List[Dict]) -> List[Dict]:
        """
        Encontra segmentos que correspondem a um texto específico
        """
        try:
            # Simplificação: assumir que chunks seguem ordem temporal
            # Em implementação mais sofisticada, poderia usar matching de texto
            words_in_text = len(text.split())
            segments_needed = max(1, words_in_text // 10)  # Aproximação
            
            return segments[:segments_needed] if segments else []
            
        except:
            return []
    
    def analyze_content(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa o conteúdo da transcrição
        
        Args:
            transcript_data: Dados da transcrição
            
        Returns:
            Análise do conteúdo
        """
        try:
            full_text = transcript_data.get('full_text', '')
            segments = transcript_data.get('segments', [])
            
            if not full_text:
                return {}
            
            # Análise básica de texto
            analysis = {
                'statistics': {
                    'total_characters': len(full_text),
                    'total_words': len(full_text.split()),
                    'total_sentences': len([s for s in full_text.split('.') if s.strip()]),
                    'average_words_per_segment': len(full_text.split()) / len(segments) if segments else 0,
                    'total_duration_minutes': transcript_data.get('total_duration', 0) / 60
                },
                'content_analysis': {
                    'language_detected': transcript_data.get('transcript_info', {}).get('language', 'unknown'),
                    'transcript_type': transcript_data.get('transcript_info', {}).get('type', 'unknown'),
                    'readability_score': self._calculate_readability(full_text)
                },
                'keywords': self._extract_keywords(full_text),
                'topics': self._identify_topics(full_text),
                'sentiment': self._basic_sentiment(full_text)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de conteúdo: {e}")
            return {'error': str(e)}
    
    def _calculate_readability(self, text: str) -> float:
        """Cálculo básico de legibilidade"""
        try:
            words = text.split()
            sentences = [s for s in text.split('.') if s.strip()]
            
            if not sentences:
                return 0.0
            
            avg_words_per_sentence = len(words) / len(sentences)
            # Fórmula simplificada (Flesch Reading Ease adaptada)
            score = 206.835 - (1.015 * avg_words_per_sentence)
            return max(0, min(100, score))
            
        except:
            return 0.0
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extração básica de palavras-chave"""
        try:
            # Remover stopwords básicas
            stopwords = {
                'o', 'a', 'e', 'é', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'não', 'que', 'se', 'os', 'as',
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about'
            }
            
            words = re.findall(r'\b\w+\b', text.lower())
            filtered_words = [w for w in words if len(w) > 3 and w not in stopwords]
            
            # Contar frequência
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Retornar top N
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:top_n]]
            
        except:
            return []
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identificação básica de tópicos"""
        try:
            # Tópicos baseados em palavras-chave comuns
            topic_keywords = {
                'tecnologia': ['tecnologia', 'computer', 'software', 'digital', 'internet', 'app'],
                'educação': ['educação', 'ensino', 'aprender', 'escola', 'universidade', 'curso'],
                'saúde': ['saúde', 'medicina', 'doença', 'tratamento', 'médico', 'hospital'],
                'negócios': ['negócio', 'empresa', 'vendas', 'marketing', 'cliente', 'mercado'],
                'ciência': ['ciência', 'pesquisa', 'estudo', 'descoberta', 'experimento', 'análise']
            }
            
            text_lower = text.lower()
            identified_topics = []
            
            for topic, keywords in topic_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score >= 2:  # Threshold mínimo
                    identified_topics.append(topic)
            
            return identified_topics
            
        except:
            return []
    
    def _basic_sentiment(self, text: str) -> str:
        """Análise básica de sentimento"""
        try:
            positive_words = ['bom', 'ótimo', 'excelente', 'fantástico', 'good', 'great', 'excellent', 'amazing']
            negative_words = ['ruim', 'péssimo', 'terrível', 'horrible', 'bad', 'terrible', 'awful']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except:
            return 'neutral'
    
    def save_data(self, video_id: str, transcript_data: Dict[str, Any], chunks: List[Dict[str, Any]], 
                  metadata: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Salva todos os dados extraídos em múltiplos formatos
        
        Args:
            video_id: ID do vídeo
            transcript_data: Dados da transcrição
            chunks: Chunks para RAG
            metadata: Metadados do vídeo
            analysis: Análise do conteúdo
            
        Returns:
            Caminhos dos arquivos salvos
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_prefix = f"{video_id}_{timestamp}"
            
            saved_files = {}
            
            # 1. Salvar transcrição completa (JSON)
            transcript_file = self.dirs['transcripts'] / f"{file_prefix}_transcript.json"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            saved_files['transcript_json'] = str(transcript_file)
            
            # 2. Salvar metadados
            metadata_file = self.dirs['metadata'] / f"{file_prefix}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            saved_files['metadata'] = str(metadata_file)
            
            # 3. Salvar chunks para RAG
            chunks_file = self.dirs['chunks'] / f"{file_prefix}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            saved_files['chunks'] = str(chunks_file)
            
            # 4. Salvar análise
            analysis_file = self.dirs['rag_content'] / f"{file_prefix}_analysis.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            saved_files['analysis'] = str(analysis_file)
            
            # 5. Salvar texto puro para RAG
            text_file = self.dirs['rag_content'] / f"{file_prefix}_text.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(transcript_data.get('full_text', ''))
            saved_files['text'] = str(text_file)
            
            # 6. Salvar chunks em CSV
            chunks_csv = self.dirs['chunks'] / f"{file_prefix}_chunks.csv"
            if chunks:
                with open(chunks_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=chunks[0].keys())
                    writer.writeheader()
                    writer.writerows(chunks)
                saved_files['chunks_csv'] = str(chunks_csv)
            
            # 7. Salvar em banco SQLite
            db_file = self.dirs['database'] / 'youtube_transcripts.db'
            self._save_to_database(db_file, video_id, transcript_data, chunks, metadata, analysis)
            saved_files['database'] = str(db_file)
            
            # 8. Criar arquivo de resumo
            summary_file = self.dirs['rag_content'] / f"{file_prefix}_summary.json"
            summary = {
                'video_id': video_id,
                'extraction_date': timestamp,
                'files_created': saved_files,
                'statistics': {
                    'total_segments': transcript_data.get('total_segments', 0),
                    'total_chunks': len(chunks),
                    'text_length': transcript_data.get('text_length', 0),
                    'duration_minutes': transcript_data.get('total_duration', 0) / 60
                },
                'metadata': metadata,
                'analysis_summary': analysis
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            saved_files['summary'] = str(summary_file)
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
            return {'error': str(e)}
    
    def _save_to_database(self, db_file: Path, video_id: str, transcript_data: Dict, 
                         chunks: List[Dict], metadata: Dict, analysis: Dict):
        """Salva dados no banco SQLite"""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Criar tabelas se não existirem
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    extraction_date TEXT,
                    total_segments INTEGER,
                    total_duration REAL,
                    text_length INTEGER,
                    language TEXT,
                    transcript_type TEXT,
                    metadata_json TEXT,
                    analysis_json TEXT
                )
            ''')
            
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
                    chunk_metadata_json TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Inserir dados do vídeo
            cursor.execute('''
                INSERT OR REPLACE INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                metadata.get('title', ''),
                metadata.get('url', ''),
                transcript_data.get('extraction_timestamp', ''),
                transcript_data.get('total_segments', 0),
                transcript_data.get('total_duration', 0),
                transcript_data.get('text_length', 0),
                transcript_data.get('transcript_info', {}).get('language', ''),
                transcript_data.get('transcript_info', {}).get('type', ''),
                json.dumps(metadata),
                json.dumps(analysis)
            ))
            
            # Inserir chunks
            for chunk in chunks:
                cursor.execute('''
                    INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk['chunk_id'],
                    chunk['video_id'],
                    chunk['chunk_index'],
                    chunk['text'],
                    chunk['text_length'],
                    chunk['word_count'],
                    chunk['start_time'],
                    chunk['end_time'],
                    json.dumps(chunk.get('chunk_metadata', {}))
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
    
    def process_video(self, url_or_id: str, languages: List[str] = None, 
                     prefer_manual: bool = True, chunk_size: int = 500) -> Dict[str, Any]:
        """
        Processa um vídeo completo: extrai transcrição, cria chunks RAG, analisa e salva
        
        Args:
            url_or_id: URL ou ID do vídeo
            languages: Idiomas preferidos
            prefer_manual: Preferir transcrições manuais
            chunk_size: Tamanho dos chunks
            
        Returns:
            Resultado completo do processamento
        """
        try:
            logger.info(f"Iniciando processamento do vídeo: {url_or_id}")
            
            # 1. Extrair ID do vídeo
            video_id = self.extract_video_id(url_or_id)
            if not video_id:
                return {'error': 'ID do vídeo inválido', 'input': url_or_id}
            
            logger.info(f"ID do vídeo extraído: {video_id}")
            
            # 2. Obter metadados
            logger.info("Obtendo metadados do vídeo...")
            metadata = self.get_video_metadata(video_id)
            
            # 3. Listar transcrições disponíveis
            logger.info("Listando transcrições disponíveis...")
            available_transcripts = self.get_available_transcripts(video_id)
            
            # 4. Extrair transcrição
            logger.info("Extraindo transcrição...")
            transcript_data = self.extract_transcript(video_id, languages, prefer_manual)
            
            if 'error' in transcript_data:
                return {
                    'video_id': video_id,
                    'error': transcript_data['error'],
                    'available_transcripts': available_transcripts,
                    'metadata': metadata
                }
            
            # 5. Criar chunks para RAG
            logger.info("Criando chunks para RAG...")
            chunks = self.create_rag_chunks(transcript_data, chunk_size)
            
            # 6. Analisar conteúdo
            logger.info("Analisando conteúdo...")
            analysis = self.analyze_content(transcript_data)
            
            # 7. Salvar todos os dados
            logger.info("Salvando dados...")
            saved_files = self.save_data(video_id, transcript_data, chunks, metadata, analysis)
            
            # 8. Compilar resultado final
            result = {
                'success': True,
                'video_id': video_id,
                'metadata': metadata,
                'available_transcripts': available_transcripts,
                'transcript_info': transcript_data.get('transcript_info', {}),
                'statistics': {
                    'total_segments': transcript_data.get('total_segments', 0),
                    'total_chunks': len(chunks),
                    'text_length': transcript_data.get('text_length', 0),
                    'duration_minutes': transcript_data.get('total_duration', 0) / 60,
                    'average_chunk_size': sum(c['text_length'] for c in chunks) / len(chunks) if chunks else 0
                },
                'analysis': analysis,
                'saved_files': saved_files,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processamento concluído com sucesso para vídeo {video_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento do vídeo: {e}")
            return {
                'error': str(e),
                'input': url_or_id,
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def search_content(self, query: str, video_id: str = None) -> List[Dict[str, Any]]:
        """
        Busca conteúdo nos chunks armazenados
        
        Args:
            query: Termo de busca
            video_id: ID específico do vídeo (opcional)
            
        Returns:
            Lista de chunks relevantes
        """
        try:
            db_file = self.dirs['database'] / 'youtube_transcripts.db'
            if not db_file.exists():
                return []
            
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Busca no texto dos chunks
            if video_id:
                cursor.execute('''
                    SELECT chunk_id, video_id, chunk_index, text, start_time, end_time
                    FROM chunks 
                    WHERE video_id = ? AND text LIKE ?
                    ORDER BY chunk_index
                ''', (video_id, f'%{query}%'))
            else:
                cursor.execute('''
                    SELECT chunk_id, video_id, chunk_index, text, start_time, end_time
                    FROM chunks 
                    WHERE text LIKE ?
                    ORDER BY video_id, chunk_index
                ''', (f'%{query}%',))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'chunk_id': row[0],
                    'video_id': row[1],
                    'chunk_index': row[2],
                    'text': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'video_url': f'https://www.youtube.com/watch?v={row[1]}&t={int(row[4])}s'
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de processamento
    extractor = YouTubeTranscriptExtractor()
    
    # URL de exemplo
    test_url = "https://www.youtube.com/watch?v=ff89oHwvNsM"
    
    # Processar vídeo
    result = extractor.process_video(test_url, languages=['pt', 'en'])
    
    if result.get('success'):
        print(f"✅ Processamento concluído!")
        print(f"📊 Estatísticas:")
        print(f"   - Segmentos: {result['statistics']['total_segments']}")
        print(f"   - Chunks RAG: {result['statistics']['total_chunks']}")
        print(f"   - Duração: {result['statistics']['duration_minutes']:.1f} minutos")
        print(f"   - Tamanho do texto: {result['statistics']['text_length']} caracteres")
        print(f"\n📁 Arquivos salvos: {len(result['saved_files'])}")
        for file_type, path in result['saved_files'].items():
            print(f"   - {file_type}: {path}")
    else:
        print(f"❌ Erro: {result.get('error')}")
