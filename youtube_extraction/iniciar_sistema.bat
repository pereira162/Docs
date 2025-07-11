@echo off
echo 🎬 YOUTUBE RAG EXTRACTOR v5.0 - SISTEMA COMPLETO
echo ===================================================
echo.
echo 🔧 Configurando FFmpeg...
set PATH=%PATH%;C:\ffmpeg
echo ✅ FFmpeg configurado!
echo.
echo ✨ FUNCIONALIDADES v5.0:
echo.
echo   � NUMERAÇÃO AUTOMÁTICA DE PLAYLISTS:
echo   python youtube_rag_extractor_final.py --playlist "URL_DA_PLAYLIST"
echo   Resultado: Pastas [1], [2], [3]... organizadas automaticamente
echo.
echo   🔧 MODO AVANÇADO (CHUNKS ALTA QUALIDADE):
echo   python youtube_rag_extractor_final.py --url "URL" --advanced-mode
echo   Configuração: 1000 chars, máximo 100 chunks (vs 500/30 básico)
echo.
echo   🔄 REUTILIZAÇÃO DE DADOS (3X MAIS RÁPIDO):
echo   python youtube_rag_extractor_final.py --playlist "URL" --reuse-data
echo   Reutiliza: transcrições, metadados e áudio de versões anteriores
echo.
echo   � ÁUDIO CONFIGURÁVEL:
echo   python youtube_rag_extractor_final.py --url "URL" --save-audio
echo   Padrão: temporário | Opção: permanente
echo.
echo   📁 ORGANIZAR PLAYLISTS EXISTENTES:
echo   python youtube_rag_extractor_final.py --organize-playlist "nome_pasta"
echo.
echo 🎯 COMANDOS COMBINADOS:
echo.
echo   � Máxima qualidade com reutilização:
echo   python youtube_rag_extractor_final.py --playlist "URL" --advanced-mode --reuse-data
echo.
echo   ⚡ Processamento rápido:
echo   python youtube_rag_extractor_final.py --playlist "URL" --reuse-data
echo.
echo   � Arquivo completo com áudio:
echo   python youtube_rag_extractor_final.py --playlist "URL" --save-audio
echo.
echo ✅ NOVIDADES v5.0:
echo   🔢 Numeração automática [1], [2], [3] em playlists
echo   🔧 Modo avançado configurável para melhor qualidade RAG
echo   🔄 Reutilização acelera processamento 3x
echo   💾 Áudio temporário por padrão (economia espaço)
echo   📁 Reorganização de playlists existentes
echo.
echo 🚀 Sistema v5.0 pronto para produção!
echo.
cmd /k
