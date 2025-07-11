@echo off
echo 🎬 SISTEMA RAG YOUTUBE - VERSAO FINAL COM MELHORIAS
echo ====================================================
echo.
echo 🔧 Configurando FFmpeg...
set PATH=%PATH%;C:\ffmpeg
echo ✅ FFmpeg configurado!
echo.
echo 💡 COMANDOS DISPONÍVEIS:
echo.
echo   📹 Vídeo único:
echo   python youtube_rag_extractor_final.py --url "URL_DO_VIDEO"
echo.
echo   📺 Playlist completa:
echo   python youtube_rag_extractor_final.py --playlist "URL_DA_PLAYLIST"
echo.
echo   🎯 Playlist com range (ex: vídeos 3 até 15):
echo   python youtube_rag_extractor_final.py --playlist "URL" --start 3 --end 15
echo.
echo   📁 Vídeo com pasta personalizada:
echo   python youtube_rag_extractor_final.py --url "URL" --folder "MinhaPasta"
echo.
echo   🌐 Com proxy:
echo   python youtube_rag_extractor_final.py --url "URL" --proxy "http://proxy:port"
echo.
echo   🔍 Listar extrações:
echo   python youtube_rag_extractor_final.py --list
echo.
echo 🆕 MELHORIAS IMPLEMENTADAS:
echo   ✅ Nomes reais das playlists
echo   ✅ Versionamento automático (v1, v2, etc)
echo   ✅ Pastas individuais para cada vídeo da playlist
echo   ✅ Range de vídeos para playlists grandes
echo   ✅ Controle de memória (evita desligamentos)
echo   ✅ Opção de pasta personalizada via input
echo.
echo 🚀 Sistema pronto para uso!
echo.
cmd /k
