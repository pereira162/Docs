#!/usr/bin/env python3
"""
Debug test para identificar problemas com RAG Processor
"""

print("🔍 Iniciando debug...")

try:
    print("1. Testando importações básicas...")
    import os
    import json
    from pathlib import Path
    print("✅ Importações básicas OK")
    
    print("2. Testando docling...")
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import PdfFormatOption
    print("✅ Docling OK")
    
    print("3. Testando easyocr...")
    import easyocr
    print("✅ EasyOCR OK")
    
    print("4. Testando rag_processor...")
    from rag_processor import RAGProcessor
    print("✅ RAG Processor importado")
    
    print("5. Inicializando RAG Processor...")
    rag = RAGProcessor()
    print("✅ RAG Processor inicializado com sucesso!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
