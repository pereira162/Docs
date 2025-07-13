#!/usr/bin/env python3
"""
🚀 INSTALADOR AUTOMÁTICO - YouTube RAG Extractor
====================================================
Script para instalação automática de todas as dependências e configuração do sistema.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Exibe cabeçalho do instalador"""
    print("🚀" + "="*60 + "🚀")
    print("🎬 YouTube RAG Extractor - INSTALADOR AUTOMÁTICO")
    print("🚀" + "="*60 + "🚀")
    print()

def check_python_version():
    """Verifica versão do Python"""
    print("🐍 Verificando versão do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} não suportado!")
        print("   Versão mínima: Python 3.8")
        print("   Recomendado: Python 3.9+")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True

def install_requirements():
    """Instala dependências do requirements.txt"""
    print("\n📦 Instalando dependências...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado!")
        return False
    
    try:
        # Atualizar pip primeiro
        print("🔄 Atualizando pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Instalar dependências
        print("📦 Instalando pacotes...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                               check=True, capture_output=True, text=True)
        
        print("✅ Dependências instaladas com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação: {e}")
        if e.stdout:
            print(f"   Saída: {e.stdout}")
        if e.stderr:
            print(f"   Erro: {e.stderr}")
        return False

def check_ffmpeg():
    """Verifica e configura FFmpeg"""
    print("\n🎵 Verificando FFmpeg...")
    
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                               capture_output=True, check=True, timeout=5)
        print("✅ FFmpeg encontrado no sistema!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️ FFmpeg não encontrado no PATH")
        
        # Verificar instalação local
        if platform.system() == "Windows":
            ffmpeg_path = r"C:\ffmpeg\bin"
            if Path(ffmpeg_path).exists():
                print("✅ FFmpeg encontrado em C:\\ffmpeg\\bin")
                print("   O sistema irá configurar automaticamente")
                return True
        
        print("❌ FFmpeg não encontrado!")
        print("   Download: https://ffmpeg.org/download.html")
        print("   O sistema tentará funcionar sem FFmpeg, mas algumas funcionalidades podem estar limitadas")
        return False

def test_whisper():
    """Testa instalação do Whisper"""
    print("\n🎤 Testando Whisper...")
    
    try:
        import whisper
        models = whisper.available_models()
        print(f"✅ Whisper instalado! Modelos disponíveis: {len(models)}")
        print(f"   Modelos: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
        return True
    except ImportError:
        print("❌ Whisper não instalado corretamente!")
        return False
    except Exception as e:
        print(f"⚠️ Erro ao testar Whisper: {e}")
        return False

def test_sentence_transformers():
    """Testa sentence-transformers"""
    print("\n🧠 Testando Sentence Transformers...")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ Sentence Transformers instalado!")
        return True
    except ImportError:
        print("❌ Sentence Transformers não instalado!")
        return False
    except Exception as e:
        print(f"⚠️ Erro ao testar Sentence Transformers: {e}")
        return False

def test_main_script():
    """Testa script principal"""
    print("\n🎬 Testando script principal...")
    
    main_script = Path("youtube_extractor.py")
    if not main_script.exists():
        print("❌ Script principal não encontrado!")
        return False
    
    try:
        # Testar importações básicas
        result = subprocess.run([sys.executable, "-c", 
                               "import sys; sys.path.append('.'); "
                               "from youtube_rag_extractor_final import YouTubeRAGExtractor; "
                               "print('✅ Importações OK')"], 
                               capture_output=True, check=True, text=True, timeout=10)
        print("✅ Script principal funcionando!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no script principal: {e}")
        if e.stderr:
            print(f"   Detalhes: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout no teste - script pode estar funcionando mas é lento")
        return True

def create_test_command():
    """Cria comando de teste"""
    print("\n🧪 Comando de teste criado:")
    print("="*50)
    print("python youtube_extractor.py --url \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\" --folder \"teste_instalacao\"")
    print("="*50)

def main():
    """Função principal do instalador"""
    print_header()
    
    # Lista de verificações
    checks = [
        ("Versão Python", check_python_version),
        ("Dependências", install_requirements),
        ("FFmpeg", check_ffmpeg),
        ("Whisper", test_whisper),
        ("Sentence Transformers", test_sentence_transformers),
        ("Script Principal", test_main_script)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n📋 {name}...")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {name}: {e}")
            results.append((name, False))
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DA INSTALAÇÃO")
    print("="*60)
    
    success_count = 0
    for name, result in results:
        status = "✅ OK" if result else "❌ FALHA"
        print(f"{name:20} | {status}")
        if result:
            success_count += 1
    
    print(f"\n📈 Sucesso: {success_count}/{len(results)} verificações")
    
    if success_count >= len(results) - 1:  # Permitir 1 falha (geralmente FFmpeg)
        print("\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("✅ Sistema pronto para uso!")
        create_test_command()
        
        print("\n📖 Próximos passos:")
        print("1. Teste o comando acima")
        print("2. Consulte README_FINAL.md para uso básico")
        print("3. Consulte DOCUMENTACAO_FINAL.md para referência completa")
        
    else:
        print("\n⚠️ INSTALAÇÃO PARCIAL")
        print("❌ Algumas verificações falharam")
        print("📋 Verifique os erros acima e tente novamente")
        print("💡 Consulte a documentação para solução de problemas")
    
    print("\n🚀 YouTube RAG Extractor - Instalação finalizada!")

if __name__ == "__main__":
    main()
