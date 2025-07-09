#!/usr/bin/env python3
# Teste específico do PDF AutoCAD
from rag_processor import RAGProcessor
import os
from pathlib import Path

def test_autocad_pdf():
    print("🚀 SISTEMA RAG LOCAL-FIRST - TESTE COM PDF AUTOCAD")
    print("=" * 60)

    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Arquivo não encontrado: {pdf_file}")
        return
    
    print(f"📄 Arquivo: {pdf_file}")
    print(f"📏 Tamanho: {os.path.getsize(pdf_file)/1024/1024:.2f} MB")

    print("\n🔄 Inicializando RAG Processor...")
    try:
        rag = RAGProcessor()
        print("✅ RAG Processor inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar RAG: {e}")
        return

    print("⚡ Processando PDF com Docling avançado...")
    try:
        result = rag.process_source(
            source=pdf_file,
            source_type="file", 
            filename=pdf_file
        )
        
        print("\n📊 RESULTADO:")
        print(f"✅ Sucesso: {result.get('success', False)}")
        print(f"📝 Método: {result.get('method', 'N/A')}")
        print(f"🧩 Chunks: {result.get('chunks_count', 0)}")

        files = result.get("files", {})
        if files:
            print(f"\n📁 Arquivos gerados ({len(files)}):")
            for file_type, file_path in files.items():
                if os.path.exists(file_path):
                    size_kb = os.path.getsize(file_path) / 1024
                    print(f"  ✅ {file_type}: {Path(file_path).name} ({size_kb:.1f} KB)")
                    
                    # Mostrar primeiras linhas do arquivo markdown
                    if file_type == "markdown" and size_kb > 0:
                        print(f"    📝 Prévia do conteúdo:")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()[:5]
                                for i, line in enumerate(lines, 1):
                                    print(f"      {i}: {line.strip()[:100]}...")
                        except Exception as e:
                            print(f"    ⚠️ Erro ao ler arquivo: {e}")
                else:
                    print(f"  ❌ {file_type}: Arquivo não encontrado")
        else:
            print("❌ Nenhum arquivo gerado")

        if result.get("error"):
            print(f"\n⚠️ Erro: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")

if __name__ == "__main__":
    test_autocad_pdf()
