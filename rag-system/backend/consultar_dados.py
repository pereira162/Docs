# Sistema de Consulta dos Dados Extraídos
from excel_data_manager import ExcelDataManager
import pandas as pd
import sqlite3
from pathlib import Path

def consultar_dados_salvos():
    """Demonstra como acessar e consultar os dados extraídos"""
    
    print("="*80)
    print("🔍 CONSULTANDO DADOS EXTRAÍDOS DO Atividades_alunos.xlsx")
    print("="*80)
    
    # Inicializar manager
    manager = ExcelDataManager()
    
    # 1. Listar arquivos processados
    print("\n📁 ARQUIVOS PROCESSADOS:")
    files = manager.list_extracted_files()
    for file in files:
        print(f"   📄 {file['filename']}")
        print(f"      Processado em: {file['extracted_at']}")
        print(f"      Planilhas: {file['total_worksheets']}")
        print(f"      Linhas: {file['total_rows']}")
        print(f"      Tempo: {file['processing_time']:.2f}s")
    
    # 2. Carregar dados completos
    try:
        print(f"\n📊 CARREGANDO DADOS COMPLETOS...")
        data = manager.load_extracted_data("Atividades_alunos.xlsx")
        
        print(f"✅ Dados carregados com sucesso!")
        print(f"   Planilhas: {len(data['worksheets'])}")
        print(f"   Nomes: {list(data['worksheets'].keys())}")
        
        # 3. Examinar uma planilha específica
        print(f"\n🔍 EXAMINANDO PLANILHA '1E' (Turma 1E):")
        try:
            df_1e = manager.get_worksheet_data("Atividades_alunos.xlsx", "1E")
            print(f"   Dimensões: {df_1e.shape}")
            print(f"   Colunas: {list(df_1e.columns[:5])}{'...' if len(df_1e.columns) > 5 else ''}")
            
            # Mostrar primeiras linhas
            print(f"\n   Primeiras 3 linhas:")
            for i, row in df_1e.head(3).iterrows():
                print(f"      Linha {i+1}: {list(row.values[:3])}...")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao carregar planilha 1E: {e}")
        
        # 4. Consultar banco SQLite
        print(f"\n🗄️ CONSULTANDO BANCO DE DADOS:")
        conn = sqlite3.connect(manager.db_path)
        
        # Consulta de metadados
        cursor = conn.cursor()
        cursor.execute("""
            SELECT worksheet_name, rows, columns 
            FROM worksheets w
            JOIN excel_files f ON w.file_id = f.id
            WHERE f.filename = 'Atividades_alunos.xlsx'
            ORDER BY worksheet_name
        """)
        
        print(f"   📋 Planilhas no banco:")
        for row in cursor.fetchall():
            name, rows, cols = row
            print(f"      {name}: {rows} × {cols}")
        
        conn.close()
        
        # 5. Analisar conteúdo RAG
        rag_file = Path(manager.storage_dir) / "json" / [f for f in Path(manager.json_dir).glob("*rag_content.json") if "Atividades_alunos" in f.name]
        
        if rag_file:
            import json
            rag_file = rag_file[0] if isinstance(rag_file, list) else rag_file
            
            if rag_file.exists():
                print(f"\n🤖 CONTEÚDO RAG PREPARADO:")
                with open(rag_file, 'r', encoding='utf-8') as f:
                    rag_data = json.load(f)
                
                print(f"   Chunks de busca: {len(rag_data.get('searchable_chunks', []))}")
                print(f"   Metadados: {len(rag_data.get('metadata', {}))}")
                
                # Mostrar alguns chunks
                chunks = rag_data.get('searchable_chunks', [])
                if chunks:
                    print(f"\n   📝 Primeiros 3 chunks:")
                    for i, chunk in enumerate(chunks[:3], 1):
                        print(f"      {i}. Tipo: {chunk.get('type', 'N/A')}")
                        print(f"         Fonte: {chunk.get('source', 'N/A')}")
                        print(f"         Conteúdo: {chunk.get('content', '')[:100]}...")
        
        # 6. Buscar por padrões específicos
        print(f"\n🔍 BUSCA POR PADRÕES:")
        
        # Buscar turmas de programação
        prog_turmas = []
        for nome, planilha in data['worksheets'].items():
            colunas_texto = ' '.join([str(col) for col in planilha.get('columns', [])])
            if 'programação' in colunas_texto.lower() or 'computacional' in colunas_texto.lower():
                prog_turmas.append(nome)
        
        if prog_turmas:
            print(f"   🖥️ Turmas com Programação: {', '.join(prog_turmas)}")
        
        # Buscar turmas de matemática
        math_turmas = []
        for nome, planilha in data['worksheets'].items():
            colunas_texto = ' '.join([str(col) for col in planilha.get('columns', [])])
            if 'matemática' in colunas_texto.lower():
                math_turmas.append(nome)
        
        if math_turmas:
            print(f"   📐 Turmas com Matemática: {', '.join(math_turmas)}")
        
        # 7. Estatísticas gerais
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        total_alunos = 0
        turmas_por_serie = {}
        
        for nome, planilha in data['worksheets'].items():
            linhas = planilha['shape']['rows']
            total_alunos += max(0, linhas - 2)  # Subtrair cabeçalhos
            
            # Agrupar por série
            serie = nome[0] if nome and nome[0].isdigit() else 'Outros'
            if serie not in turmas_por_serie:
                turmas_por_serie[serie] = []
            turmas_por_serie[serie].append(nome)
        
        print(f"   👥 Total aproximado de alunos: {total_alunos}")
        print(f"   📚 Turmas por série:")
        for serie, turmas in turmas_por_serie.items():
            print(f"      {serie}ª série: {len(turmas)} turmas ({', '.join(turmas)})")
        
        print(f"\n✅ CONSULTA COMPLETA FINALIZADA!")
        print(f"💾 Todos os dados estão persistidos e acessíveis!")
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        import traceback
        traceback.print_exc()

def exemplo_busca_inteligente():
    """Exemplo de como fazer busca inteligente nos dados RAG"""
    
    print("\n" + "="*60)
    print("🤖 EXEMPLO DE BUSCA INTELIGENTE")
    print("="*60)
    
    manager = ExcelDataManager()
    
    # Carregar dados RAG
    rag_files = list(Path(manager.json_dir).glob("*rag_content.json"))
    
    if rag_files:
        import json
        
        with open(rag_files[0], 'r', encoding='utf-8') as f:
            rag_data = json.load(f)
        
        chunks = rag_data.get('searchable_chunks', [])
        
        print(f"📊 Total de chunks disponíveis: {len(chunks)}")
        
        # Exemplos de busca
        queries = [
            "programação",
            "matemática", 
            "alunos",
            "1E",
            "P5.js"
        ]
        
        for query in queries:
            print(f"\n🔍 Buscando por: '{query}'")
            resultados = []
            
            for chunk in chunks:
                content = chunk.get('content', '').lower()
                if query.lower() in content:
                    resultados.append(chunk)
            
            print(f"   Encontrados: {len(resultados)} resultados")
            
            if resultados:
                for i, resultado in enumerate(resultados[:2], 1):  # Mostrar só os 2 primeiros
                    print(f"   {i}. {resultado.get('source', 'N/A')}: {resultado.get('content', '')[:80]}...")

if __name__ == "__main__":
    consultar_dados_salvos()
    exemplo_busca_inteligente()
