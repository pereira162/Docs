#!/usr/bin/env python3
"""
🍪 Tutorial Completo - Cookies para Vídeos de Membros YouTube
"""

def tutorial_completo():
    """Tutorial passo a passo"""
    
    print("🍪" + "=" * 70 + "🍪")
    print("🎯 TUTORIAL COMPLETO - VÍDEOS DE MEMBROS YOUTUBE")
    print("🍪" + "=" * 70 + "🍪")
    print()
    
    print("📋 PROBLEMA IDENTIFICADO:")
    print("-" * 30)
    print("❌ Chrome/Edge: Criptografia DPAPI")
    print("❌ Firefox: Perfil não encontrado") 
    print("❌ Todos navegadores: Políticas de segurança")
    print()
    
    print("✅ SOLUÇÃO DEFINITIVA:")
    print("-" * 30)
    print("📌 Use extensão do navegador para extrair cookies")
    print()
    
    print("🔧 PASSO A PASSO:")
    print("-" * 30)
    
    steps = [
        {
            "num": "1️⃣",
            "title": "INSTALAR EXTENSÃO",
            "details": [
                "• Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc",
                "• Firefox: https://addons.mozilla.org/firefox/addon/cookies-txt/",
                "• Edge: https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locall/hhojkbnpncmdlokkjcmjpfgkepnlnapl"
            ]
        },
        {
            "num": "2️⃣", 
            "title": "FAZER LOGIN NO YOUTUBE",
            "details": [
                "• Abra YouTube no navegador",
                "• Faça login na sua conta",
                "• Certifique-se de estar logado"
            ]
        },
        {
            "num": "3️⃣",
            "title": "ACESSAR VÍDEO DE MEMBRO",
            "details": [
                "• Vá para: https://www.youtube.com/watch?v=MU_Xy8ppbEg",
                "• Ou qualquer vídeo de membro que você tenha acesso",
                "• Confirme que você pode ver o vídeo"
            ]
        },
        {
            "num": "4️⃣",
            "title": "EXTRAIR COOKIES",
            "details": [
                "• Clique no ícone da extensão na barra de ferramentas",
                "• Clique em 'Current Site' ou 'youtube.com'",
                "• Baixe o arquivo (geralmente 'youtube.com_cookies.txt')",
                "• Salve na pasta do projeto"
            ]
        },
        {
            "num": "5️⃣",
            "title": "TESTAR COOKIES",
            "details": [
                "• Renomeie o arquivo para 'cookies.txt' (se necessário)",
                "• Execute: python testar_cookies.py",
                "• Verifique se os cookies funcionam"
            ]
        },
        {
            "num": "6️⃣",
            "title": "USAR NO SISTEMA",
            "details": [
                "• Execute: python youtube_rag_extractor_final.py",
                "• Use: --cookies-file cookies.txt",
                "• Exemplo completo abaixo"
            ]
        }
    ]
    
    for step in steps:
        print(f"\n{step['num']} {step['title']}:")
        for detail in step['details']:
            print(f"   {detail}")
    
    print("\n🚀 COMANDOS PRONTOS:")
    print("-" * 30)
    
    commands = [
        {
            "desc": "🧪 Testar cookies",
            "cmd": "python testar_cookies.py"
        },
        {
            "desc": "🎬 Vídeo único",
            "cmd": "python youtube_rag_extractor_final.py --url 'https://www.youtube.com/watch?v=MU_Xy8ppbEg' --cookies-file cookies.txt --folder 'teste_membros'"
        },
        {
            "desc": "🚀 Modo avançado",
            "cmd": "python youtube_rag_extractor_final.py --url 'https://www.youtube.com/watch?v=MU_Xy8ppbEg' --cookies-file cookies.txt --advanced-mode --reuse-data --folder 'membros_premium'"
        },
        {
            "desc": "🎵 Com áudio",
            "cmd": "python youtube_rag_extractor_final.py --url 'https://www.youtube.com/watch?v=MU_Xy8ppbEg' --cookies-file cookies.txt --save-audio --folder 'membros_audio'"
        },
        {
            "desc": "📚 Múltiplos vídeos",
            "cmd": "python youtube_rag_extractor_final.py --url 'URL1' 'URL2' 'URL3' --cookies-file cookies.txt --advanced-mode --folder 'serie_membros'"
        }
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. {cmd['desc']}:")
        print(f"   {cmd['cmd']}")
    
    print("\n💡 DICAS IMPORTANTES:")
    print("-" * 30)
    
    tips = [
        "🔑 Certifique-se de ter acesso ao canal como membro",
        "🌐 Alguns vídeos podem ter restrições regionais",
        "⏰ Cookies podem expirar, re-extraia se necessário", 
        "🔒 Mantenha o arquivo cookies.txt privado",
        "🆕 Use sempre a versão mais recente da extensão",
        "🔄 Se falhar, tente fechar/abrir o navegador e re-extrair"
    ]
    
    for tip in tips:
        print(f"   {tip}")

def main():
    tutorial_completo()
    
    print("\n🍪" + "=" * 70 + "🍪")
    print("✅ RESUMO: Instale extensão → Extraia cookies → Use --cookies-file")
    print("🎯 Link direto Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
    print("🍪" + "=" * 70 + "🍪")

if __name__ == "__main__":
    main()
