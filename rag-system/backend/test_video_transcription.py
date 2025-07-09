"""
Teste de Transcrição de Vídeo com Whisper + FFmpeg
=================================================
"""

import os
from pathlib import Path
from web_scraper_video_extractor import VideoTranscriptionExtractor

def test_video_transcription():
    """Teste simples de transcrição de vídeo"""
    print("🎤 TESTE DE TRANSCRIÇÃO DE VÍDEO")
    print("=" * 50)
    
    # Diretório com vídeos baixados
    videos_dir = Path("test_complete_autodesk/videos")
    
    if not videos_dir.exists():
        print("❌ Diretório de vídeos não encontrado")
        return
    
    # Listar vídeos disponíveis
    video_files = list(videos_dir.glob("*.mp4"))
    print(f"📁 Vídeos encontrados: {len(video_files)}")
    
    if not video_files:
        print("❌ Nenhum vídeo encontrado")
        return
    
    # Testar com primeiro vídeo (menor)
    video_files.sort(key=lambda x: x.stat().st_size)
    test_video = video_files[0]
    
    print(f"🎥 Testando com: {test_video.name}")
    print(f"📊 Tamanho: {test_video.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Extrair ID do nome do arquivo
    video_id = test_video.stem
    
    # Inicializar extrator
    extractor = VideoTranscriptionExtractor("test_transcriptions")
    
    # Tentar transcrever
    result = extractor.transcribe_video(str(test_video), video_id)
    
    if result:
        print(f"✅ TRANSCRIÇÃO CONCLUÍDA!")
        print(f"📝 Texto: {len(result['text'])} caracteres")
        print(f"🎬 Segmentos: {len(result['segments'])}")
        print(f"🗣️ Idioma detectado: {result['language']}")
        
        # Mostrar primeiros 200 caracteres
        preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
        print(f"💬 Preview: {preview}")
        
        # Mostrar alguns segmentos
        print(f"\n📋 PRIMEIROS SEGMENTOS:")
        for i, segment in enumerate(result['segments'][:3]):
            start = segment['start']
            end = segment['end']
            text = segment['text'].strip()
            print(f"   {i+1}. [{start:.1f}s - {end:.1f}s]: {text}")
        
        return True
    else:
        print("❌ Falha na transcrição")
        return False

def test_complete_workflow():
    """Teste do workflow completo"""
    print("\n🎯 TESTE DO WORKFLOW COMPLETO")
    print("=" * 50)
    
    # URL de teste específica com vídeo
    test_url = "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-WhatsNew/files/GUID-0E96BDF7-DE27-4C35-A78B-800F535DAA84.htm"
    
    print(f"🌐 URL de teste: {test_url}")
    print("📄 Esta página tem o vídeo ID: 456a54d0-8b7e-11ed-9908-f35030c405cf")
    
    from web_scraper_video_extractor import AdvancedWebScraperWithVideo
    
    # Criar extrator
    extractor = AdvancedWebScraperWithVideo("test_single_page")
    
    # Testar apenas 1 página
    result = extractor.extract_autodesk_complete(
        test_url,
        max_depth=1,
        max_pages=1
    )
    
    print(f"\n📊 RESULTADO:")
    print(f"   📄 Páginas: {result['pages_processed']}")
    print(f"   🎥 Vídeos: {result['videos_processed']}")
    print(f"   🔥 Chunks texto: {result['total_text_chunks']}")
    print(f"   🎬 Chunks vídeo: {result['total_video_chunks']}")
    
    return result

if __name__ == "__main__":
    # Primeiro testar transcrição com vídeo já baixado
    transcription_success = test_video_transcription()
    
    if transcription_success:
        print("\n🎉 Transcrição funcionando! Testando workflow completo...")
        test_complete_workflow()
    else:
        print("\n❌ Transcrição não funcionou. Verificar configuração FFmpeg.")
