#!/usr/bin/env python3
"""
INSTALADOR AUTOMÁTICO - Web Documentation Scraper
=================================================
Instala todas as dependências e configura o sistema
"""

import os
import sys
import subprocess
import platform
import zipfile
import requests
from pathlib import Path

def print_header():
    """Exibe cabeçalho do instalador"""
    print("🚀" + "="*60 + "🚀")
    print("📄 WEB DOCUMENTATION SCRAPER - INSTALADOR AUTOMÁTICO")
    print("🚀" + "="*60 + "🚀")
    print()

def check_python_version():
    """Verifica versão do Python"""
    print("🐍 Verificando versão do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} não suportado!")
        print("   Versão mínima: Python 3.8")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True

def install_requirements():
    """Instala dependências do requirements.txt"""
    print("\n📦 Instalando dependências...")
    
    try:
        # Atualizar pip
        print("🔄 Atualizando pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Instalar dependências
        print("📦 Instalando pacotes...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        
        print("✅ Dependências instaladas com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def setup_ffmpeg():
    """Configura FFmpeg automaticamente no Windows"""
    print("\n🎵 Configurando FFmpeg...")
    
    if platform.system() != "Windows":
        print("ℹ️ Configuração automática de FFmpeg apenas para Windows")
        print("   No Linux/Mac, instale com: sudo apt install ffmpeg ou brew install ffmpeg")
        return True
    
    # Verificar se FFmpeg já está disponível
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg já está instalado e disponível")
        return True
    except:
        pass
    
    # Tentar configurar FFmpeg
    ffmpeg_path = Path("C:/ffmpeg")
    ffmpeg_exe = ffmpeg_path / "ffmpeg.exe"
    
    if ffmpeg_exe.exists():
        # FFmpeg já existe, adicionar ao PATH
        current_path = os.environ.get('PATH', '')
        if str(ffmpeg_path) not in current_path:
            os.environ['PATH'] = current_path + ';' + str(ffmpeg_path)
        print("✅ FFmpeg configurado no PATH")
        return True
    
    print("⚠️ FFmpeg não encontrado")
    print("   Para funcionalidade completa de vídeo, instale FFmpeg:")
    print("   1. Baixe de: https://www.gyan.dev/ffmpeg/builds/")
    print("   2. Extraia para C:/ffmpeg")
    print("   3. Adicione C:/ffmpeg ao PATH do sistema")
    
    return False

def test_system():
    """Testa se o sistema está funcionando"""
    print("\n🧪 Testando sistema...")
    
    try:
        # Testar imports principais
        import requests
        import bs4
        print("✅ Bibliotecas básicas: OK")
        
        # Testar Selenium
        try:
            from seleniumbase import Driver
            print("✅ SeleniumBase: OK")
        except ImportError:
            print("⚠️ SeleniumBase: Não disponível")
        
        # Testar Whisper
        try:
            import whisper
            print("✅ Whisper: OK")
        except ImportError:
            print("⚠️ Whisper: Não disponível")
        
        # Testar modelo de embeddings
        try:
            from sentence_transformers import SentenceTransformer
            print("✅ Sentence Transformers: OK")
        except ImportError:
            print("⚠️ Sentence Transformers: Não disponível")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def create_test_script():
    """Cria script de teste"""
    test_script = '''#!/usr/bin/env python3
"""
Script de teste rápido do Web Documentation Scraper
"""

from web_documentation_scraper import WebDocumentationScraper

def test_basic_extraction():
    """Teste básico de extração"""
    print("🧪 Testando extração básica...")
    
    scraper = WebDocumentationScraper("test_storage")
    
    # Testar com uma página simples
    test_url = "https://httpbin.org/html"
    
    try:
        result = scraper.extract_page_content(test_url)
        
        print(f"✅ Teste concluído!")
        print(f"   - URL: {result.get('url')}")
        print(f"   - Título: {result.get('title', 'N/A')}")
        print(f"   - Palavras: {result.get('word_count', 0)}")
        print(f"   - Links: {len(result.get('links', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    test_basic_extraction()
'''
    
    with open("test_scraper.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ Script de teste criado: test_scraper.py")

def main():
    """Função principal do instalador"""
    print_header()
    
    # Verificar Python
    if not check_python_version():
        print("❌ Instalação cancelada devido à versão do Python")
        return False
    
    # Instalar dependências
    if not install_requirements():
        print("❌ Instalação cancelada devido a erro nas dependências")
        return False
    
    # Configurar FFmpeg
    setup_ffmpeg()
    
    # Testar sistema
    if not test_system():
        print("⚠️ Sistema instalado mas com limitações")
    
    # Criar script de teste
    create_test_script()
    
    print("\n🎉 INSTALAÇÃO CONCLUÍDA!")
    print("="*50)
    print("✅ Web Documentation Scraper instalado com sucesso!")
    print("\n📖 Próximos passos:")
    print("1. Execute: python test_scraper.py (teste básico)")
    print("2. Execute: python web_documentation_scraper.py --url URL_TESTE")
    print("3. Para vídeos: python web_scraper_advanced.py --url URL --process-videos")
    print("\n📚 Documentação:")
    print("- web_documentation_scraper.py: Extração básica")
    print("- web_scraper_advanced.py: Com processamento de vídeos")
    print("- requirements.txt: Dependências")
    
    return True

if __name__ == "__main__":
    main()
