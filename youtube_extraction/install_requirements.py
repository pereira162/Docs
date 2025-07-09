#!/usr/bin/env python3
"""
📦 REQUIREMENTS - YouTube Extraction Tool
========================================
Lista de dependências necessárias para o sistema de extração do YouTube
"""

# Dependências principais
REQUIRED_PACKAGES = [
    "yt-dlp>=2023.1.6",                    # Download de vídeos do YouTube
    "youtube-transcript-api>=0.6.0",      # Extração de transcrições
    "requests>=2.28.0",                   # Requisições HTTP
    "beautifulsoup4>=4.11.0",             # Parsing HTML
    "pandas>=1.5.0",                      # Manipulação de dados
    "sqlite3",                            # Banco de dados (built-in)
    "pathlib",                            # Manipulação de caminhos (built-in)
    "argparse",                           # CLI (built-in)
    "json",                               # JSON (built-in)
    "zipfile",                            # ZIP (built-in)
    "datetime",                           # Data/hora (built-in)
    "re",                                 # Regex (built-in)
    "os",                                 # Sistema operacional (built-in)
    "sys",                                # Sistema (built-in)
    "time",                               # Tempo (built-in)
    "subprocess",                         # Subprocessos (built-in)
    "typing",                             # Tipagem (built-in)
    "logging",                            # Logging (built-in)
]

def install_requirements():
    """Instala todas as dependências necessárias"""
    import subprocess
    import sys
    
    print("📦 Instalando dependências do YouTube Extraction Tool...")
    
    pip_packages = [
        "yt-dlp>=2023.1.6",
        "youtube-transcript-api>=0.6.0", 
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pandas>=1.5.0"
    ]
    
    for package in pip_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
    
    print("\n✅ Instalação concluída!")
    print("\nPara usar o sistema:")
    print("python youtube_extractor_cli.py --help")

if __name__ == "__main__":
    install_requirements()
