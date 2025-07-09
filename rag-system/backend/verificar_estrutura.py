# Análise simples para verificar estrutura dos dados
from excel_extractor import ExcelExtractor
import json

def verificar_estrutura():
    extractor = ExcelExtractor()
    results = extractor.extract_from_excel("exemplo_dados_empresa.xlsx")
    
    print("="*60)
    print("🔍 ESTRUTURA DOS DADOS EXTRAÍDOS:")
    print("="*60)
    
    # Mostrar estrutura geral
    print("\n📋 Chaves principais:")
    for key in results.keys():
        print(f"  • {key}")
    
    # Verificar estrutura de uma planilha
    if 'worksheets' in results:
        primeira_planilha = list(results['worksheets'].keys())[0]
        sheet_data = results['worksheets'][primeira_planilha]
        
        print(f"\n📊 Estrutura da planilha '{primeira_planilha}':")
        for key in sheet_data.keys():
            print(f"  • {key}: {type(sheet_data[key])}")
            
        # Verificar content_analysis
        if 'content_analysis' in sheet_data:
            print(f"\n🔍 Estrutura do content_analysis:")
            for key in sheet_data['content_analysis'].keys():
                print(f"  • {key}: {type(sheet_data['content_analysis'][key])}")
    
    # Mostrar sample das informações básicas
    print(f"\n📄 RESUMO RÁPIDO:")
    print(f"  Total de planilhas: {len(results['worksheets'])}")
    for name, data in results['worksheets'].items():
        print(f"  • {name}: {data['shape']['rows']} × {data['shape']['columns']}")
        print(f"    Colunas: {', '.join(data['columns'][:5])}{'...' if len(data['columns']) > 5 else ''}")
        
        # Mostrar amostra de dados
        if data['sample_data']:
            print(f"    Primeira linha: {data['sample_data'][0]}")
    
    print(f"\n✅ Verificação concluída!")

if __name__ == "__main__":
    verificar_estrutura()
