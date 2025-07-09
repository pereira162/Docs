#!/usr/bin/env python3
"""
Teste do Sistema RAG com PDF AutoCAD - Versão Simplificada
"""

import os
import sys
from pathlib import Path
from rag_processor_simple import RAGProcessor

def test_autocad_pdf():
    """
    Testa o processamento do PDF AutoCAD
    """
    print("🚀 SISTEMA RAG LOCAL-FIRST - TESTE COM PDF AUTOCAD (VERSÃO SIMPLIFICADA)")
    print("=" * 70)
    
    # Verificar se o arquivo existe
    pdf_file = "AutoCAD Architecture Toolset Productivity Study (EN).pdf"
    
    if not Path(pdf_file).exists():
        print(f"❌ Arquivo não encontrado: {pdf_file}")
        print("📁 Arquivos disponíveis:")
        for file in Path('.').glob('*.pdf'):
            print(f"  - {file.name}")
        return False
    
    # Informações do arquivo
    file_size = Path(pdf_file).stat().st_size / (1024*1024)
    print(f"📄 Arquivo: {pdf_file}")
    print(f"📏 Tamanho: {file_size:.2f} MB")
    print()
    
    try:
        # Inicializar RAG Processor
        print("🔄 Inicializando RAG Processor...")
        rag = RAGProcessor(output_dir="./rag_outputs_autocad")
        print("✅ RAG Processor inicializado!")
        print()
        
        # Processar o arquivo
        print("📖 Processando PDF...")
        result = rag.process_source(pdf_file)
        
        if result['status'] == 'success':
            print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"🆔 ID do arquivo: {result['file_id']}")
            print(f"📄 Páginas processadas: {result['pages_processed']}")
            print(f"📦 Blocos de conteúdo: {result['content_blocks']}")
            print()
            
            # Verificar arquivos gerados
            print("📁 ARQUIVOS GERADOS:")
            output_dir = Path("./rag_outputs_autocad")
            
            for subdir in ['markdown', 'json', 'chunks', 'metadata']:
                dir_path = output_dir / subdir
                if dir_path.exists():
                    files = list(dir_path.glob('*'))
                    print(f"  📂 {subdir}/")
                    for file in files:
                        file_size_kb = file.stat().st_size / 1024
                        print(f"    📄 {file.name} ({file_size_kb:.1f} KB)")
            
            print()
            
            # Mostrar preview do markdown
            markdown_file = output_dir / "markdown" / f"{result['file_id']}.md"
            if markdown_file.exists():
                print("📝 PREVIEW DO MARKDOWN (primeiras linhas):")
                print("-" * 50)
                content = markdown_file.read_text(encoding='utf-8')
                lines = content.split('\\n')[:20]  # Primeiras 20 linhas
                for line in lines:
                    print(line)
                if len(content.split('\\n')) > 20:
                    print("...")
                    print(f"(+ {len(content.split('\\n')) - 20} linhas)")
                print("-" * 50)
            
            return True
            
        else:
            print(f"❌ ERRO NO PROCESSAMENTO: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_autocad_pdf()
    
    if success:
        print()
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ O sistema RAG Local-First está funcionando corretamente")
        print("📊 Verificar os arquivos na pasta rag_outputs_autocad/")
    else:
        print()
        print("❌ TESTE FALHOU")
        print("🔧 Verificar logs de erro acima")
