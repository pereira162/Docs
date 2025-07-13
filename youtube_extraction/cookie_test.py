#!/usr/bin/env python3
"""
🧪 Testador de Cookies para YouTube
"""

import os
import sys
from pathlib import Path

def test_cookies_file(cookies_file="cookies.txt"):
    """Testa se o arquivo de cookies funciona"""
    
    print("🧪 TESTADOR DE COOKIES YOUTUBE")
    print("=" * 50)
    
    # Verificar se arquivo existe
    if not Path(cookies_file).exists():
        print(f"❌ Arquivo não encontrado: {cookies_file}")
        print("\n📝 Para criar o arquivo:")
        print("1. Instale extensão: Get cookies.txt LOCALLY")
        print("2. Vá para YouTube e faça login")
        print("3. Extraia cookies e salve como 'cookies.txt'")
        print("\n🔗 Link da extensão:")
        print("Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        return False
    
    print(f"✅ Arquivo encontrado: {cookies_file}")
    
    # Verificar conteúdo
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        print(f"📄 Tamanho do arquivo: {len(content)} caracteres")
        print(f"📝 Número de linhas: {len(lines)}")
        
        # Contar cookies válidos
        cookie_lines = [line for line in lines if line.strip() and not line.startswith('#')]
        print(f"🍪 Cookies encontrados: {len(cookie_lines)}")
        
        if len(cookie_lines) == 0:
            print("⚠️  Nenhum cookie válido encontrado!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    # Testar com yt-dlp
    test_url = "https://www.youtube.com/watch?v=MU_Xy8ppbEg"
    print(f"\n🎯 Testando com vídeo de membro...")
    print(f"   URL: {test_url}")
    
    cmd = f'yt-dlp --cookies "{cookies_file}" --no-download --print title "{test_url}"'
    print(f"\n🔧 Comando de teste:")
    print(f"   {cmd}")
    
    print(f"\n⏳ Executando teste...")
    result = os.system(cmd)
    
    if result == 0:
        print("✅ SUCESSO! Cookies estão funcionando!")
        print("\n🚀 Agora você pode usar:")
        print(f'   python youtube_rag_extractor_final.py --url "{test_url}" --cookies-file {cookies_file} --folder "teste_membros"')
        return True
    else:
        print("❌ FALHA! Cookies não funcionaram.")
        print("\n🔍 Possíveis problemas:")
        print("   • Cookies expirados ou inválidos")
        print("   • Não está logado no YouTube")
        print("   • Não tem acesso ao vídeo como membro")
        print("   • Restrições regionais")
        print("\n💡 Soluções:")
        print("   • Re-extraia os cookies")
        print("   • Verifique se está logado no YouTube")
        print("   • Teste com outro vídeo público primeiro")
        return False

def test_public_video(cookies_file="cookies.txt"):
    """Testa com vídeo público primeiro"""
    
    print("\n🔬 TESTE COM VÍDEO PÚBLICO")
    print("-" * 30)
    
    public_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
    print(f"📹 Testando com vídeo público: {public_url}")
    
    cmd = f'yt-dlp --cookies "{cookies_file}" --no-download --print title "{public_url}"'
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Vídeo público funcionou!")
        print("   Os cookies estão válidos, problema pode ser:")
        print("   • Acesso ao vídeo de membro")
        print("   • Permissões específicas do canal")
        return True
    else:
        print("❌ Vídeo público falhou!")
        print("   Problema nos cookies básicos")
        return False

def main():
    """Função principal"""
    
    cookies_files = ["cookies.txt", "youtube.com_cookies.txt", "youtube_cookies.txt"]
    
    for cookies_file in cookies_files:
        if Path(cookies_file).exists():
            print(f"🍪 Encontrado arquivo: {cookies_file}")
            
            # Teste principal
            if test_cookies_file(cookies_file):
                print(f"\n🎉 TUDO FUNCIONANDO!")
                break
            
            # Teste com vídeo público
            test_public_video(cookies_file)
            print("-" * 50)
    else:
        print("❌ Nenhum arquivo de cookies encontrado!")
        print("\n📋 Arquivos procurados:")
        for f in cookies_files:
            print(f"   • {f}")
        
        print("\n💡 Execute o tutorial:")
        print("   python tutorial_cookies.py")

if __name__ == "__main__":
    main()
