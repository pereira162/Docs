#!/usr/bin/env python3
"""
RAG Processor Simplificado - Compatibilidade com Docling 2.39.0
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGProcessor:
    """
    Processador simplificado para documentos
    """
    
    def __init__(self, output_dir: str = "./rag_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Criar estrutura de diretórios
        self.directories = {
            'markdown': self.output_dir / "markdown",
            'json': self.output_dir / "json", 
            'chunks': self.output_dir / "chunks",
            'metadata': self.output_dir / "metadata"
        }
        
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True)
        
        logger.info("✅ RAG Processor inicializado")
    
    def process_source(self, source_path: str) -> Dict[str, Any]:
        """
        Processa um documento usando pdfplumber (mais simples e confiável)
        """
        try:
            source_path = Path(source_path)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
            
            logger.info(f"📄 Processando: {source_path.name}")
            
            # Usar pdfplumber para PDFs (mais estável)
            if source_path.suffix.lower() == '.pdf':
                return self._process_pdf_with_pdfplumber(source_path)
            else:
                # Para outros formatos, retornar estrutura básica
                return self._process_generic_file(source_path)
                
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'source': str(source_path)
            }
    
    def _process_pdf_with_pdfplumber(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Processa PDF usando pdfplumber (biblioteca estável)
        """
        try:
            import pdfplumber
            
            content = []
            metadata = {
                'filename': pdf_path.name,
                'size_mb': round(pdf_path.stat().st_size / (1024*1024), 2),
                'processed_at': datetime.now().isoformat(),
                'pages': 0
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata['pages'] = len(pdf.pages)
                logger.info(f"📖 PDF com {len(pdf.pages)} páginas")
                
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            content.append({
                                'page': i + 1,
                                'content': text.strip(),
                                'type': 'text'
                            })
                        
                        # Extrair tabelas se existirem
                        tables = page.extract_tables()
                        for j, table in enumerate(tables):
                            if table:
                                content.append({
                                    'page': i + 1,
                                    'content': str(table),
                                    'type': 'table',
                                    'table_id': j
                                })
                                
                    except Exception as e:
                        logger.warning(f"⚠️ Erro na página {i+1}: {e}")
                        continue
            
            # Salvar arquivos
            file_id = pdf_path.stem
            self._save_results(file_id, content, metadata)
            
            return {
                'status': 'success',
                'file_id': file_id,
                'pages_processed': metadata['pages'],
                'content_blocks': len(content),
                'metadata': metadata
            }
            
        except ImportError:
            logger.error("❌ pdfplumber não está instalado")
            return {'status': 'error', 'error': 'pdfplumber não encontrado'}
        except Exception as e:
            logger.error(f"❌ Erro no processamento PDF: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _process_generic_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Processamento básico para outros tipos de arquivo
        """
        try:
            metadata = {
                'filename': file_path.name,
                'size_mb': round(file_path.stat().st_size / (1024*1024), 2),
                'processed_at': datetime.now().isoformat(),
                'format': file_path.suffix
            }
            
            content = [{
                'content': f"Arquivo: {file_path.name}\\nTamanho: {metadata['size_mb']} MB",
                'type': 'metadata'
            }]
            
            file_id = file_path.stem
            self._save_results(file_id, content, metadata)
            
            return {
                'status': 'success',
                'file_id': file_id,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _save_results(self, file_id: str, content: List[Dict], metadata: Dict):
        """
        Salva os resultados nos diretórios apropriados
        """
        try:
            # Salvar markdown
            markdown_content = self._convert_to_markdown(content, metadata)
            markdown_file = self.directories['markdown'] / f"{file_id}.md"
            markdown_file.write_text(markdown_content, encoding='utf-8')
            
            # Salvar JSON
            json_data = {
                'metadata': metadata,
                'content': content,
                'generated_at': datetime.now().isoformat()
            }
            json_file = self.directories['json'] / f"{file_id}.json"
            json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
            
            # Salvar chunks (simplificado)
            chunks = self._create_chunks(content)
            chunks_file = self.directories['chunks'] / f"{file_id}_chunks.json"
            chunks_file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding='utf-8')
            
            # Salvar metadata
            metadata_file = self.directories['metadata'] / f"{file_id}_metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            logger.info(f"✅ Arquivos salvos para {file_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar: {e}")
    
    def _convert_to_markdown(self, content: List[Dict], metadata: Dict) -> str:
        """
        Converte conteúdo para Markdown
        """
        md_lines = [
            f"# {metadata['filename']}",
            "",
            f"**Processado em:** {metadata['processed_at']}",
            f"**Tamanho:** {metadata.get('size_mb', 0)} MB",
            ""
        ]
        
        if 'pages' in metadata:
            md_lines.append(f"**Páginas:** {metadata['pages']}")
            md_lines.append("")
        
        for item in content:
            if item['type'] == 'text':
                md_lines.append(f"## Página {item['page']}")
                md_lines.append("")
                md_lines.append(item['content'])
                md_lines.append("")
            elif item['type'] == 'table':
                md_lines.append(f"### Tabela (Página {item['page']})")
                md_lines.append("")
                md_lines.append("```")
                md_lines.append(item['content'])
                md_lines.append("```")
                md_lines.append("")
        
        return "\\n".join(md_lines)
    
    def _create_chunks(self, content: List[Dict]) -> List[Dict]:
        """
        Cria chunks simples do conteúdo
        """
        chunks = []
        
        for i, item in enumerate(content):
            if item['type'] == 'text' and len(item['content']) > 100:
                # Dividir texto em chunks de ~500 caracteres
                text = item['content']
                chunk_size = 500
                
                for j in range(0, len(text), chunk_size):
                    chunk_text = text[j:j+chunk_size]
                    chunks.append({
                        'chunk_id': f"chunk_{i}_{j//chunk_size}",
                        'content': chunk_text,
                        'source_page': item.get('page', 1),
                        'type': item['type'],
                        'char_start': j,
                        'char_end': min(j+chunk_size, len(text))
                    })
        
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos arquivos processados
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'files_by_type': {},
            'last_processed': None
        }
        
        try:
            for metadata_file in self.directories['metadata'].glob("*.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    stats['total_files'] += 1
                    stats['total_size_mb'] += metadata.get('size_mb', 0)
                    
                    file_ext = Path(metadata['filename']).suffix
                    stats['files_by_type'][file_ext] = stats['files_by_type'].get(file_ext, 0) + 1
                    
                    if not stats['last_processed'] or metadata['processed_at'] > stats['last_processed']:
                        stats['last_processed'] = metadata['processed_at']
        
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
        
        return stats

if __name__ == "__main__":
    # Teste básico
    processor = RAGProcessor()
    print("✅ RAG Processor inicializado com sucesso!")
