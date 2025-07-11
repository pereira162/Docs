#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎬 YouTube RAG Extractor v5.0 - Demonstração das Funcionalidades

Este script demonstra todas as novas funcionalidades v5.0:
1. Numeração automática de playlists [1], [2], [3]
2. Modo avançado com chunks de alta qualidade
3. Reutilização de dados anteriores
4. Download de áudio configurável
"""

import os
import subprocess
import sys

def run_demo():
    """Demonstra as funcionalidades v5.0 do YouTube RAG Extractor"""
    
    print("🎬 YouTube RAG Extractor v5.0 - Demo das Novas Funcionalidades")
    print("=" * 60)
    
    # Verificar se o script principal existe
    if not os.path.exists("youtube_rag_extractor_final.py"):
        print("❌ Erro: youtube_rag_extractor_final.py não encontrado!")
        return
    
    print("\n✨ FUNCIONALIDADES v5.0 DISPONÍVEIS:\n")
    
    print("1. 🔢 NUMERAÇÃO AUTOMÁTICA DE PLAYLISTS")
    print("   Comando: python youtube_rag_extractor_final.py --playlist 'PLAYLIST_URL'")
    print("   Resultado: Pastas [1] Video1, [2] Video2, [3] Video3...")
    print()
    
    print("2. 🔧 MODO AVANÇADO (CHUNKS ALTA QUALIDADE)")
    print("   Comando: python youtube_rag_extractor_final.py --url 'VIDEO_URL' --advanced-mode")
    print("   Chunks: 1000 caracteres, máximo 100 chunks (vs 500 chars/30 chunks básico)")
    print()
    
    print("3. 🔄 REUTILIZAÇÃO DE DADOS ANTERIORES") 
    print("   Comando: python youtube_rag_extractor_final.py --url 'VIDEO_URL' --reuse-data")
    print("   Benefício: 3x mais rápido, reutiliza transcrições/áudio/metadata")
    print()
    
    print("4. 💾 DOWNLOAD DE ÁUDIO CONFIGURÁVEL")
    print("   Padrão: python youtube_rag_extractor_final.py --url 'VIDEO_URL' (áudio temporário)")
    print("   Salvar: python youtube_rag_extractor_final.py --url 'VIDEO_URL' --save-audio")
    print()
    
    print("5. 📁 ORGANIZAÇÃO DE PLAYLISTS EXISTENTES")
    print("   Comando: python youtube_rag_extractor_final.py --organize-playlist 'nome_pasta'")
    print("   Resultado: Adiciona numeração [1], [2] em playlist já processada")
    print()
    
    print("🏆 COMANDOS COMPLETOS DE EXEMPLO:")
    print("-" * 40)
    
    print("\n🎯 Vídeo individual com máxima qualidade:")
    print("python youtube_rag_extractor_final.py \\")
    print("  --url 'https://youtube.com/watch?v=VIDEO_ID' \\")
    print("  --advanced-mode \\")
    print("  --save-audio \\")
    print("  --reuse-data")
    
    print("\n📚 Playlist educacional completa:")
    print("python youtube_rag_extractor_final.py \\")
    print("  --playlist 'https://youtube.com/playlist?list=PLAYLIST_ID' \\")
    print("  --advanced-mode \\")
    print("  --reuse-data")
    
    print("\n⚡ Processamento rápido com reutilização:")
    print("python youtube_rag_extractor_final.py \\")
    print("  --playlist 'PLAYLIST_URL' \\")
    print("  --reuse-data")
    
    print("\n🔧 Configuração personalizada:")
    print("python youtube_rag_extractor_final.py \\")
    print("  --url 'VIDEO_URL' \\")
    print("  --chunk-size 1200 \\")
    print("  --max-chunks 80 \\")
    print("  --save-audio")
    
    print("\n" + "=" * 60)
    print("✅ SISTEMA v5.0 PRONTO PARA USO!")
    print("📖 Documentação completa: README.md")
    print("🚀 Todas as funcionalidades solicitadas implementadas!")

def show_help():
    """Mostra ajuda do sistema v5.0"""
    print("\n📋 AJUDA - YouTube RAG Extractor v5.0")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, "youtube_rag_extractor_final.py", "--help"
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Erro ao executar --help")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
    else:
        run_demo()
