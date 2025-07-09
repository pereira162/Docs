"""
Teste do novo sistema RAG
"""

import sys
sys.path.append('.')

from rag_processor import RAGProcessor

def test_basic_functionality():
    print("🧪 Testando o novo sistema RAG...")
    
    # Inicializar processador
    processor = RAGProcessor(output_dir="./test_outputs")
    
    # Testar com texto simples
    test_text = """
# Documento de Teste

Este é um documento de teste para validar o novo sistema RAG.

## Seção 1: Introdução

O objetivo é verificar se:
- A extração de texto funciona corretamente
- Os chunks são criados apropriadamente  
- Os arquivos são salvos no formato correto

## Seção 2: Dados de Exemplo

| Nome | Idade | Cidade |
|------|-------|--------|
| João | 30    | SP     |
| Maria| 25    | RJ     |

## Conclusão

O sistema deve gerar arquivos Markdown e JSON estruturados.
"""
    
    # Processar texto
    result = processor.process_source(
        source=test_text.encode('utf-8'),
        source_type="file",
        filename="teste_basico.md"
    )
    
    print("📊 Resultado do processamento:")
    print(f"✅ Sucesso: {result.get('success')}")
    print(f"📄 Método: {result.get('processing_method')}")
    print(f"🧩 Chunks: {len(result.get('chunks', []))}")
    print(f"📁 Arquivos salvos: {result.get('files_saved')}")
    
    # Listar documentos processados
    docs = processor.get_processed_documents()
    print(f"📚 Total de documentos: {len(docs)}")
    
    return result.get('success', False)

if __name__ == "__main__":
    success = test_basic_functionality()
    print(f"\n{'✅ TESTE PASSOU' if success else '❌ TESTE FALHOU'}")
