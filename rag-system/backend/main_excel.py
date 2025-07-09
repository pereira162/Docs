# Integração do extrator Excel com o sistema RAG principal
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import tempfile
import os
from pathlib import Path
import shutil
from excel_extractor import ExcelExtractor
import json

app = FastAPI(title="RAG System with Excel Support", version="1.0.0")

# Servir arquivos estáticos
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância do extrator
excel_extractor = ExcelExtractor()

@app.get("/")
async def root():
    return {
        "message": "RAG System with Excel Support - Running!",
        "features": [
            "PDF extraction (docling)",
            "Excel extraction (.xlsx/.xls)",
            "RAG content preparation",
            "Search functionality"
        ],
        "version": "1.0.0",
        "interface": "/excel-ui"
    }

@app.get("/excel-ui", response_class=HTMLResponse)
async def excel_interface():
    """
    Interface web para upload e extração de Excel
    """
    try:
        html_file = static_dir / "excel_interface.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
                <html>
                    <body>
                        <h1>Interface não encontrada</h1>
                        <p>Arquivo excel_interface.html não encontrado em /static</p>
                        <p>Use os endpoints da API diretamente:</p>
                        <ul>
                            <li>POST /extract-excel - Upload de arquivo</li>
                            <li>POST /test-excel - Teste com exemplo</li>
                            <li>GET /excel-info - Informações</li>
                        </ul>
                    </body>
                </html>
            """)
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Erro: {str(e)}</h1></body></html>")

@app.post("/extract-excel")
async def extract_excel(file: UploadFile = File(...)):
    """
    Extrai dados de um arquivo Excel e prepara para RAG
    """
    try:
        # Validar arquivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Formato não suportado. Use .xlsx ou .xls"
            )
        
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Extrair dados
            results = excel_extractor.extract_from_excel(tmp_path)
            
            # Preparar resposta
            response = {
                "status": "success",
                "message": f"Arquivo '{file.filename}' processado com sucesso",
                "file_info": results["file_info"],
                "summary": results["summary"],
                "worksheets": {
                    name: {
                        "name": data["name"],
                        "shape": data["shape"],
                        "columns": data["columns"],
                        "data_types": data["data_types"],
                        "patterns": data["content_analysis"]["patterns"],
                        "sample_data": data["raw_data"][:3] if data["raw_data"] else []
                    }
                    for name, data in results["worksheets"].items()
                },
                "rag_content": {
                    "text_size": len(results["content_for_rag"]),
                    "metadata": results["metadata"],
                    "ready_for_search": True
                }
            }
            
            return response
            
        finally:
            # Limpar arquivo temporário
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/extract-excel-detailed")
async def extract_excel_detailed(file: UploadFile = File(...)):
    """
    Extrai dados completos de um arquivo Excel incluindo conteúdo para RAG
    """
    try:
        # Validar arquivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Formato não suportado. Use .xlsx ou .xls"
            )
        
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Extrair dados completos
            results = excel_extractor.extract_from_excel(tmp_path)
            
            # Retornar dados completos
            return {
                "status": "success",
                "filename": file.filename,
                "full_results": results
            }
            
        finally:
            # Limpar arquivo temporário
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.get("/excel-info")
async def excel_info():
    """
    Informações sobre as capacidades do extrator Excel
    """
    return {
        "supported_formats": [".xlsx", ".xls"],
        "features": {
            "worksheet_detection": "Identifica automaticamente todas as planilhas",
            "data_analysis": "Análise de tipos de dados (numérico, texto, data)",
            "pattern_recognition": "Detecção de padrões (financeiro, transacional, etc.)",
            "content_extraction": "Extração completa de dados",
            "rag_preparation": "Preparação de conteúdo para RAG",
            "metadata_extraction": "Metadados detalhados",
            "advanced_features": "Suporte a fórmulas, gráficos, comentários"
        },
        "processing_engine": "pandas + openpyxl",
        "output_formats": ["structured_data", "text_content", "searchable_chunks"]
    }

@app.post("/test-excel")
async def test_excel():
    """
    Cria e testa um arquivo Excel de exemplo
    """
    try:
        # Verificar se arquivo de exemplo existe
        example_file = "exemplo_dados_empresa.xlsx"
        if not os.path.exists(example_file):
            return {
                "status": "error",
                "message": "Arquivo de exemplo não encontrado. Execute criar_exemplo_excel.py primeiro."
            }
        
        # Processar arquivo de exemplo
        results = excel_extractor.extract_from_excel(example_file)
        
        return {
            "status": "success",
            "message": "Teste realizado com sucesso",
            "test_results": {
                "file": example_file,
                "worksheets_found": len(results["worksheets"]),
                "total_rows": results["summary"]["total_data_rows"],
                "worksheets": list(results["worksheets"].keys()),
                "rag_content_size": len(results["content_for_rag"]),
                "extraction_time": results["metadata"]["extraction_timestamp"]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro no teste: {str(e)}"
        }

if __name__ == "__main__":
    print("🚀 Iniciando RAG System with Excel Support...")
    print("📊 Recursos disponíveis:")
    print("   • Extração de PDF (docling)")
    print("   • Extração de Excel (.xlsx/.xls)")
    print("   • Preparação para RAG")
    print("   • API REST completa")
    print("\n🌐 Endpoints disponíveis:")
    print("   • POST /extract-excel - Extração básica")
    print("   • POST /extract-excel-detailed - Extração completa")
    print("   • GET /excel-info - Informações do extrator")
    print("   • POST /test-excel - Teste com arquivo exemplo")
    print("\n📡 Servidor iniciando em http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
