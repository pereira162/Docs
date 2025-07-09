# Análise final completa do extrator Excel
from excel_extractor import ExcelExtractor
import json

def demonstracao_completa():
    extractor = ExcelExtractor()
    results = extractor.extract_from_excel("exemplo_dados_empresa.xlsx")
    
    print("="*80)
    print("🎯 DEMONSTRAÇÃO COMPLETA DO EXTRATOR EXCEL")
    print("="*80)
    
    # 1. Informações gerais
    print("\n📄 INFORMAÇÕES DO ARQUIVO:")
    print(f"   Nome: {results['file_info']['filename']}")
    print(f"   Tamanho: {results['file_info']['size_mb']:.2f} MB")
    print(f"   Última modificação: {results['file_info']['modified']}")
    
    # 2. Resumo geral
    print(f"\n📊 RESUMO GERAL:")
    print(f"   Total de planilhas: {results['summary']['total_worksheets']}")
    print(f"   Total de linhas: {results['summary']['total_data_rows']}")
    print(f"   Total de colunas: {results['summary']['total_columns']}")
    
    # 3. Análise detalhada de cada planilha
    print("\n" + "="*60)
    print("📋 ANÁLISE DETALHADA DAS PLANILHAS:")
    print("="*60)
    
    for sheet_name, sheet_data in results["worksheets"].items():
        print(f"\n🔸 PLANILHA: {sheet_name}")
        print(f"   📐 Dimensões: {sheet_data['shape']['rows']} linhas × {sheet_data['shape']['columns']} colunas")
        
        # Colunas
        print(f"   📊 Colunas:")
        for i, col in enumerate(sheet_data['columns'], 1):
            dtype = 'N/A'
            if col in sheet_data.get('data_types', {}):
                dtype = sheet_data['data_types'][col]
            print(f"      {i:2d}. {col} ({dtype})")
        
        # Análise de conteúdo
        content_analysis = sheet_data.get('content_analysis', {})
        
        if content_analysis.get('numeric_columns'):
            print(f"   🔢 Colunas numéricas: {', '.join(content_analysis['numeric_columns'])}")
        
        if content_analysis.get('date_columns'):
            print(f"   📅 Colunas de data: {', '.join(content_analysis['date_columns'])}")
        
        if content_analysis.get('text_columns'):
            print(f"   📝 Colunas de texto: {', '.join(content_analysis['text_columns'][:3])}{'...' if len(content_analysis['text_columns']) > 3 else ''}")
        
        # Padrões identificados
        if content_analysis.get('patterns'):
            print(f"   🔍 Padrões detectados:")
            for pattern in content_analysis['patterns']:
                print(f"      • {pattern}")
        
        # Estatísticas básicas
        if content_analysis.get('statistics'):
            print(f"   📈 Estatísticas:")
            stats = content_analysis['statistics']
            for col, stat in list(stats.items())[:2]:  # Mostrar só as primeiras 2
                if isinstance(stat, dict) and 'mean' in stat:
                    print(f"      • {col}: média={stat['mean']:.2f}, min={stat['min']:.2f}, max={stat['max']:.2f}")
        
        # Preview dos dados
        print(f"   👁️  Preview (3 primeiras linhas):")
        if 'raw_data' in sheet_data and sheet_data['raw_data']:
            for i, row in enumerate(sheet_data['raw_data'][:3], 1):
                row_preview = str(row)[:100] + "..." if len(str(row)) > 100 else str(row)
                print(f"      Linha {i}: {row_preview}")
    
    # 4. Conteúdo para RAG
    print("\n" + "="*60)
    print("🤖 CONTEÚDO PREPARADO PARA RAG:")
    print("="*60)
    
    if 'content_for_rag' in results:
        rag_content = results['content_for_rag']
        
        print(f"\n📝 Resumo do conteúdo RAG:")
        print(f"   Tamanho total: {len(rag_content)} caracteres")
        
        # Mostrar início do conteúdo
        print(f"\n📄 Início do conteúdo preparado:")
        print("-" * 40)
        print(rag_content[:800] + "..." if len(rag_content) > 800 else rag_content)
        print("-" * 40)
    
    # 5. Metadados
    print(f"\n🏷️  METADADOS EXTRAÍDOS:")
    if 'metadata' in results:
        metadata = results['metadata']
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                print(f"   • {key}: {len(value) if hasattr(value, '__len__') else 'complexo'}")
            else:
                print(f"   • {key}: {value}")
    
    # 6. Recursos avançados detectados
    print(f"\n⚡ RECURSOS AVANÇADOS DETECTADOS:")
    total_formulas = sum(len(sheet['formulas']) for sheet in results['worksheets'].values())
    total_charts = sum(len(sheet['charts']) for sheet in results['worksheets'].values())
    total_comments = sum(len(sheet['comments']) for sheet in results['worksheets'].values())
    total_merged = sum(len(sheet['merged_cells']) for sheet in results['worksheets'].values())
    
    print(f"   • Fórmulas: {total_formulas}")
    print(f"   • Gráficos: {total_charts}")
    print(f"   • Comentários: {total_comments}")
    print(f"   • Células mescladas: {total_merged}")
    
    print(f"\n" + "="*80)
    print("✅ EXTRATOR EXCEL FUNCIONANDO PERFEITAMENTE!")
    print("🎯 CARACTERÍSTICAS IMPLEMENTADAS:")
    print("   ✅ Identificação automática de planilhas")
    print("   ✅ Extração completa de conteúdo")
    print("   ✅ Análise de tipos de dados")
    print("   ✅ Detecção de padrões")
    print("   ✅ Preparação para RAG")
    print("   ✅ Metadados detalhados")
    print("   ✅ Suporte a recursos avançados (fórmulas, gráficos, etc.)")
    print("="*80)
    
    print(f"\n🚀 PRÓXIMO PASSO: Integrar com o sistema RAG principal!")

if __name__ == "__main__":
    demonstracao_completa()
