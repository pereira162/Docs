# Análise detalhada dos dados extraídos
from excel_extractor import ExcelExtractor
import json

def analisar_excel_detalhado():
    extractor = ExcelExtractor()
    results = extractor.extract_from_excel("exemplo_dados_empresa.xlsx")
    
    print("="*80)
    print("📊 ANÁLISE DETALHADA DO ARQUIVO EXCEL")
    print("="*80)
    
    # Informações gerais do workbook
    print("\n📄 INFORMAÇÕES GERAIS:")
    print(f"  Nome do arquivo: {results['file_info']['filename']}")
    print(f"  Tamanho: {results['file_info']['size_mb']:.2f} MB")
    print(f"  Data de modificação: {results['file_info']['modified']}")
    print(f"  Total de planilhas: {results['summary']['total_worksheets']}")
    print(f"  Total de linhas de dados: {results['summary']['total_data_rows']}")
    print(f"  Total de colunas: {results['summary']['total_columns']}")
    
    # Análise de cada planilha
    print("\n" + "="*60)
    print("📋 ANÁLISE DETALHADA DAS PLANILHAS:")
    print("="*60)
    
    for sheet_name, sheet_data in results["worksheets"].items():
        print(f"\n🔸 PLANILHA: {sheet_name}")
        print(f"   Dimensões: {sheet_data['shape']['rows']} linhas × {sheet_data['shape']['columns']} colunas")
        
        # Colunas
        print(f"   📊 Colunas ({len(sheet_data['columns'])}):")
        for i, col in enumerate(sheet_data['columns']):
            print(f"      {i+1:2d}. {col}")
        
        # Tipos de dados detectados
        if sheet_data['content_analysis']['data_types']:
            print(f"   📈 Tipos de dados:")
            for dtype, count in sheet_data['content_analysis']['data_types'].items():
                print(f"      • {dtype}: {count} colunas")
        
        # Padrões detectados
        if sheet_data['content_analysis']['patterns']:
            print(f"   🔍 Padrões identificados:")
            for pattern in sheet_data['content_analysis']['patterns']:
                print(f"      • {pattern}")
        
        # Valores únicos em colunas categóricas
        if sheet_data['content_analysis']['categorical_summary']:
            print(f"   📂 Resumo categórico:")
            for col, values in sheet_data['content_analysis']['categorical_summary'].items():
                if len(values) <= 10:  # Só mostrar se poucos valores únicos
                    print(f"      • {col}: {', '.join(map(str, values))}")
                else:
                    print(f"      • {col}: {len(values)} valores únicos")
        
        # Preview dos dados
        print(f"   👁️  Preview dos dados (primeiras 3 linhas):")
        if sheet_data['sample_data']:
            for i, row in enumerate(sheet_data['sample_data'][:3], 1):
                print(f"      Linha {i}: {row}")
    
    # Conteúdo preparado para RAG
    print("\n" + "="*60)
    print("🤖 CONTEÚDO PREPARADO PARA RAG:")
    print("="*60)
    
    rag_content = results['rag_content']['text_content']
    
    # Mostrar início do conteúdo RAG
    print(f"\n📝 Texto preparado ({len(rag_content)} caracteres):")
    print("="*40)
    print(rag_content[:1000] + "..." if len(rag_content) > 1000 else rag_content)
    print("="*40)
    
    # Metadados para RAG
    print(f"\n🏷️  METADADOS RAG:")
    for key, value in results['rag_content']['metadata'].items():
        if isinstance(value, list):
            print(f"   • {key}: {len(value)} itens")
        else:
            print(f"   • {key}: {value}")
    
    # Chunks para RAG
    print(f"\n📦 CHUNKS PARA RAG:")
    chunks = results['rag_content']['chunks']
    print(f"   Total de chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:3], 1):  # Mostrar primeiros 3 chunks
        print(f"\n   📄 Chunk {i}:")
        print(f"      Fonte: {chunk['source']}")
        print(f"      Tipo: {chunk['chunk_type']}")
        print(f"      Tamanho: {len(chunk['content'])} caracteres")
        print(f"      Preview: {chunk['content'][:200]}{'...' if len(chunk['content']) > 200 else ''}")
    
    if len(chunks) > 3:
        print(f"\n   ... e mais {len(chunks) - 3} chunks")
    
    print(f"\n✅ ANÁLISE CONCLUÍDA!")
    print(f"📊 O arquivo Excel foi completamente processado e está pronto para integração RAG!")

if __name__ == "__main__":
    analisar_excel_detalhado()
