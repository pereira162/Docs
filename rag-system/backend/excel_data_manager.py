# Sistema de Persistência para Dados Extraídos do Excel
import json
import sqlite3
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from excel_extractor import ExcelExtractor

class ExcelDataManager:
    """
    Gerenciador para salvar e recuperar dados extraídos do Excel
    """
    
    def __init__(self, storage_dir: str = "extracted_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Diferentes formatos de armazenamento
        self.json_dir = self.storage_dir / "json"
        self.json_dir.mkdir(exist_ok=True)
        
        self.csv_dir = self.storage_dir / "csv"
        self.csv_dir.mkdir(exist_ok=True)
        
        self.pickle_dir = self.storage_dir / "pickle"
        self.pickle_dir.mkdir(exist_ok=True)
        
        self.db_path = self.storage_dir / "excel_data.db"
        self.init_database()
        
        print(f"📁 Sistema de persistência inicializado em: {self.storage_dir.absolute()}")
    
    def init_database(self):
        """Inicializa banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para metadados dos arquivos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS excel_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                original_path TEXT,
                extracted_at TIMESTAMP,
                file_size_mb REAL,
                total_worksheets INTEGER,
                total_rows INTEGER,
                total_columns INTEGER,
                processing_time REAL,
                json_path TEXT,
                csv_paths TEXT,
                pickle_path TEXT
            )
        """)
        
        # Tabela para planilhas individuais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS worksheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                worksheet_name TEXT,
                rows INTEGER,
                columns INTEGER,
                data_types TEXT,
                patterns TEXT,
                csv_path TEXT,
                FOREIGN KEY (file_id) REFERENCES excel_files (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_extracted_data(self, filename: str, results: Dict[Any, Any], processing_time: float = 0.0) -> Dict[str, str]:
        """
        Salva dados extraídos em múltiplos formatos
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(filename).stem
        file_id = f"{base_name}_{timestamp}"
        
        saved_paths = {}
        
        # 1. Salvar JSON completo
        json_path = self.json_dir / f"{file_id}_complete.json"
        self._save_json(results, json_path)
        saved_paths['json'] = str(json_path)
        
        # 2. Salvar cada planilha como CSV
        csv_paths = []
        for sheet_name, sheet_data in results['worksheets'].items():
            if 'raw_data' in sheet_data and sheet_data['raw_data']:
                csv_path = self.csv_dir / f"{file_id}_{sheet_name}.csv"
                self._save_csv(sheet_data['raw_data'], sheet_data['columns'], csv_path)
                csv_paths.append(str(csv_path))
        saved_paths['csv'] = csv_paths
        
        # 3. Salvar objeto completo com pickle (para recuperação total)
        pickle_path = self.pickle_dir / f"{file_id}_complete.pkl"
        self._save_pickle(results, pickle_path)
        saved_paths['pickle'] = str(pickle_path)
        
        # 4. Salvar metadados no banco
        self._save_to_database(filename, results, processing_time, saved_paths)
        
        # 5. Salvar RAG content separadamente
        rag_path = self.json_dir / f"{file_id}_rag_content.json"
        rag_data = {
            'filename': filename,
            'extraction_time': results['metadata']['extraction_timestamp'],
            'content_for_rag': results.get('content_for_rag', ''),
            'searchable_chunks': self._create_searchable_chunks(results),
            'metadata': results['metadata']
        }
        self._save_json(rag_data, rag_path)
        saved_paths['rag'] = str(rag_path)
        
        print(f"💾 Dados salvos em múltiplos formatos:")
        print(f"   📄 JSON: {json_path}")
        print(f"   📊 CSV: {len(csv_paths)} arquivos")
        print(f"   🔧 Pickle: {pickle_path}")
        print(f"   🤖 RAG: {rag_path}")
        print(f"   🗄️  Banco: {self.db_path}")
        
        return saved_paths
    
    def _save_json(self, data: Any, path: Path):
        """Salva dados em formato JSON"""
        # Converter dados não serializáveis
        serializable_data = self._make_serializable(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
    
    def _save_csv(self, data: List[Dict], columns: List[str], path: Path):
        """Salva dados de planilha em CSV"""
        try:
            df = pd.DataFrame(data, columns=columns)
            df.to_csv(path, index=False, encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Erro ao salvar CSV {path}: {e}")
    
    def _save_pickle(self, data: Any, path: Path):
        """Salva dados completos com pickle"""
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def _save_to_database(self, filename: str, results: Dict, processing_time: float, paths: Dict):
        """Salva metadados no banco SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Garantir que metadata existe
        if 'metadata' not in results:
            results['metadata'] = {}
        
        # Garantir que extraction_timestamp existe
        if 'extraction_timestamp' not in results['metadata']:
            results['metadata']['extraction_timestamp'] = datetime.now().isoformat()
        
        # Inserir arquivo principal
        cursor.execute("""
            INSERT OR REPLACE INTO excel_files 
            (filename, extracted_at, file_size_mb, total_worksheets, total_rows, total_columns, 
             processing_time, json_path, csv_paths, pickle_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            results['metadata']['extraction_timestamp'],
            results['file_info']['size_mb'],
            results['summary']['total_worksheets'],
            results['summary']['total_data_rows'],
            results['summary']['total_columns'],
            processing_time,
            paths['json'],
            json.dumps(paths['csv']),
            paths['pickle']
        ))
        
        file_id = cursor.lastrowid
        
        # Inserir planilhas
        for sheet_name, sheet_data in results['worksheets'].items():
            csv_path = next((p for p in paths['csv'] if sheet_name in p), None)
            cursor.execute("""
                INSERT INTO worksheets 
                (file_id, worksheet_name, rows, columns, data_types, patterns, csv_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                sheet_name,
                sheet_data['shape']['rows'],
                sheet_data['shape']['columns'],
                json.dumps(self._make_serializable(sheet_data.get('data_types', {}))),
                json.dumps(sheet_data['content_analysis'].get('patterns', [])),
                csv_path
            ))
        
        conn.commit()
        conn.close()
    
    def _create_searchable_chunks(self, results: Dict) -> List[Dict]:
        """Cria chunks otimizados para busca"""
        chunks = []
        
        for sheet_name, sheet_data in results['worksheets'].items():
            # Chunk com informações da planilha
            # Converter colunas para string
            columns_str = ', '.join([str(col) for col in sheet_data.get('columns', [])])
            
            chunks.append({
                'id': f"{sheet_name}_info",
                'type': 'worksheet_info',
                'source': sheet_name,
                'content': f"Planilha: {sheet_name}, Colunas: {columns_str}, Dimensões: {sheet_data['shape']['rows']}x{sheet_data['shape']['columns']}",
                'metadata': {
                    'worksheet': sheet_name,
                    'columns': [str(col) for col in sheet_data.get('columns', [])],
                    'shape': sheet_data['shape'],
                    'patterns': sheet_data['content_analysis'].get('patterns', [])
                }
            })
            
            # Chunks com dados (primeiras 10 linhas)
            if 'raw_data' in sheet_data and sheet_data['raw_data']:
                for i, row in enumerate(sheet_data['raw_data'][:10]):
                    try:
                        # Criar conteúdo do chunk com tratamento seguro
                        content_parts = []
                        for col in sheet_data.get('columns', []):
                            col_str = str(col)
                            value = row.get(col, '')
                            if pd.isna(value) or value is None:
                                value_str = ''
                            else:
                                value_str = str(value)
                            content_parts.append(f"{col_str}: {value_str}")
                        
                        chunks.append({
                            'id': f"{sheet_name}_row_{i}",
                            'type': 'data_row',
                            'source': sheet_name,
                            'content': ' | '.join(content_parts),
                            'metadata': {
                                'worksheet': sheet_name,
                                'row_index': i,
                                'data': self._make_serializable(row)
                            }
                        })
                    except Exception as e:
                        # Se houver erro, criar chunk básico
                        chunks.append({
                            'id': f"{sheet_name}_row_{i}",
                            'type': 'data_row',
                            'source': sheet_name,
                            'content': f"Linha {i} da planilha {sheet_name}",
                            'metadata': {
                                'worksheet': sheet_name,
                                'row_index': i,
                                'error': str(e)
                            }
                        })
        
        return chunks
    
    def _make_serializable(self, obj):
        """Converte objetos não serializáveis para JSON"""
        if isinstance(obj, dict):
            # Converter chaves para string também
            new_dict = {}
            for key, value in obj.items():
                # Converter chave para string se necessário
                if isinstance(key, (pd.Timestamp, datetime)):
                    new_key = str(key)
                elif not isinstance(key, (str, int, float, bool)) and key is not None:
                    new_key = str(key)
                else:
                    new_key = key
                new_dict[new_key] = self._make_serializable(value)
            return new_dict
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(self._make_serializable(item) for item in obj)
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return str(obj)
        elif hasattr(obj, 'dtype'):  # pandas/numpy objects
            if hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return str(obj)
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        elif isinstance(obj, type):  # Type objects
            return str(obj)
        elif hasattr(obj, '__dict__'):  # Custom objects
            return str(obj)
        elif obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            # Fallback para qualquer outro tipo
            try:
                return str(obj)
            except:
                return f"<non-serializable: {type(obj).__name__}>"
    
    def load_extracted_data(self, filename: str) -> Dict[Any, Any]:
        """Carrega dados extraídos salvos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT pickle_path FROM excel_files WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        conn.close()
        
        if result and Path(result[0]).exists():
            with open(result[0], 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError(f"Dados extraídos não encontrados para: {filename}")
    
    def list_extracted_files(self) -> List[Dict]:
        """Lista todos os arquivos processados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT filename, extracted_at, file_size_mb, total_worksheets, 
                   total_rows, total_columns, processing_time
            FROM excel_files 
            ORDER BY extracted_at DESC
        """)
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'filename': row[0],
                'extracted_at': row[1],
                'file_size_mb': row[2],
                'total_worksheets': row[3],
                'total_rows': row[4],
                'total_columns': row[5],
                'processing_time': row[6]
            })
        
        conn.close()
        return files
    
    def get_worksheet_data(self, filename: str, worksheet_name: str) -> pd.DataFrame:
        """Recupera dados de uma planilha específica como DataFrame"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT w.csv_path 
            FROM worksheets w
            JOIN excel_files f ON w.file_id = f.id
            WHERE f.filename = ? AND w.worksheet_name = ?
        """, (filename, worksheet_name))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and Path(result[0]).exists():
            return pd.read_csv(result[0])
        else:
            raise FileNotFoundError(f"Planilha {worksheet_name} não encontrada para {filename}")

def test_with_atividades_alunos():
    """Testa o sistema com o arquivo Atividades_alunos.xlsx"""
    print("="*80)
    print("🧪 TESTE AVANÇADO COM Atividades_alunos.xlsx")
    print("="*80)
    
    # Caminhos dos arquivos
    source_file = Path("../../Atividades_alunos.xlsx")
    local_file = Path("Atividades_alunos.xlsx")
    
    # Copiar arquivo se não existir localmente
    if source_file.exists() and not local_file.exists():
        import shutil
        shutil.copy2(source_file, local_file)
        print(f"📁 Arquivo copiado de: {source_file}")
    
    if not local_file.exists():
        print(f"❌ Arquivo não encontrado: {local_file}")
        print(f"   Tentativa em: {source_file}")
        return
    
    # Inicializar componentes
    extractor = ExcelExtractor()
    data_manager = ExcelDataManager()
    
    print(f"📊 Processando arquivo: {local_file}")
    print(f"📏 Tamanho: {local_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Extrair dados com medição de tempo
    start_time = datetime.now()
    results = extractor.extract_from_excel(str(local_file))
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"⏱️ Tempo de processamento: {processing_time:.2f} segundos")
    
    # Salvar dados
    print(f"\n💾 Salvando dados extraídos...")
    saved_paths = data_manager.save_extracted_data(
        filename=str(local_file),
        results=results,
        processing_time=processing_time
    )
    
    # Mostrar análise detalhada
    print(f"\n" + "="*60)
    print("📋 ANÁLISE DETALHADA DO ARQUIVO")
    print("="*60)
    
    print(f"\n📄 INFORMAÇÕES GERAIS:")
    print(f"   Nome: {results['file_info']['filename']}")
    print(f"   Tamanho: {results['file_info']['size_mb']:.2f} MB")
    print(f"   Planilhas: {results['summary']['total_worksheets']}")
    print(f"   Total de linhas: {results['summary']['total_data_rows']}")
    print(f"   Total de colunas: {results['summary']['total_columns']}")
    
    print(f"\n📊 PLANILHAS DETECTADAS:")
    for sheet_name, sheet_data in results['worksheets'].items():
        print(f"\n🔸 {sheet_name}:")
        print(f"   Dimensões: {sheet_data['shape']['rows']} × {sheet_data['shape']['columns']}")
        print(f"   Colunas: {', '.join(sheet_data['columns'][:5])}{'...' if len(sheet_data['columns']) > 5 else ''}")
        
        # Tipos de dados
        if sheet_data.get('data_types'):
            types_summary = {}
            for col, dtype in sheet_data['data_types'].items():
                dtype_simple = str(dtype).split('(')[0]
                types_summary[dtype_simple] = types_summary.get(dtype_simple, 0) + 1
            print(f"   Tipos: {dict(types_summary)}")
        
        # Padrões detectados
        patterns = sheet_data['content_analysis'].get('patterns', [])
        if patterns:
            print(f"   Padrões: {', '.join(patterns)}")
        
        # Amostra de dados
        if sheet_data.get('raw_data'):
            print(f"   Primeira linha: {list(sheet_data['raw_data'][0].values())[:3]}...")
    
    # Informações de persistência
    print(f"\n💾 DADOS SALVOS EM:")
    for format_type, paths in saved_paths.items():
        if isinstance(paths, list):
            print(f"   {format_type.upper()}: {len(paths)} arquivos")
        else:
            print(f"   {format_type.upper()}: {Path(paths).name}")
    
    # Mostrar conteúdo RAG
    print(f"\n🤖 CONTEÚDO RAG PREPARADO:")
    rag_content = results['content_for_rag']
    print(f"   Tamanho: {len(rag_content)} caracteres")
    print(f"   Preview: {rag_content[:200]}...")
    
    print(f"\n✅ TESTE COMPLETO FINALIZADO!")
    print(f"📁 Todos os dados salvos em: {data_manager.storage_dir.absolute()}")
    
    return results, saved_paths

if __name__ == "__main__":
    test_with_atividades_alunos()
