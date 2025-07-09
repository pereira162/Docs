#!/usr/bin/env python3
"""
🧪 TESTE DIRETO DE TRANSCRIÇÃO COM VÍDEO EXISTENTE
==================================================
Teste com vídeo que sabemos que existe
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from web_scraper_final_fixed import SimpleWebScraperWithVideo

def test_with_existing_video():
    """Teste com vídeo que existe"""
    print("🧪 TESTE COM VÍDEO EXISTENTE")
    print("=" * 50)
    
    # Cria scraper
    scraper = SimpleWebScraperWithVideo("test_video_exists")
    
    # Simula dados de vídeo existente
    video_info = {
        'video_id': '84a711e0-a331-11ed-a98a-599257d1f9b8',
        'source_url': 'https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-WhatsNew/files/GUID-B7040851-266C-48CB-9682-654F3A6B8086.htm'
    }
    
    # Primeiro, vamos baixar do diretório onde sabemos que existe
    old_video_path = r"test_complete_autodesk_fixed\videos\84a711e0-a331-11ed-a98a-599257d1f9b8.mp4"
    new_video_path = r"test_video_exists\videos\84a711e0-a331-11ed-a98a-599257d1f9b8.mp4"
    
    if os.path.exists(old_video_path):
        print(f"📹 Copiando vídeo existente...")
        import shutil
        os.makedirs(os.path.dirname(new_video_path), exist_ok=True)
        shutil.copy2(old_video_path, new_video_path)
        print(f"✅ Vídeo copiado para: {new_video_path}")
        
        # Agora testa transcrição com idioma correto (inglês)
        chunks = scraper.process_video_complete(video_info, "en")
        
        print(f"\n📊 RESULTADO:")
        print(f"   🎬 Chunks gerados: {len(chunks)}")
        if chunks:
            print(f"   📝 Primeiro chunk: {chunks[0]['text'][:100]}...")
            print(f"   🌍 Idioma detectado: {chunks[0]['metadata']['detected_language']}")
            print(f"   🎤 Idioma Whisper: {chunks[0]['metadata']['language']}")
            
        return len(chunks) > 0
    else:
        print(f"❌ Vídeo não encontrado em: {old_video_path}")
        return False

if __name__ == "__main__":
    success = test_with_existing_video()
    print(f"\n{'✅ SUCESSO!' if success else '❌ FALHOU'}")
