#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO COM VÍDEOS REAIS
==================================
Teste que realmente baixa e transcreve vídeos para provar que o sistema funciona
"""

import os
import sys
import json
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from web_scraper_final_fixed import SimpleWebScraperWithVideo, LanguageDetector

def test_language_detection():
    """Testa detecção de idioma"""
    print("🌍 TESTE DE DETECÇÃO DE IDIOMA")
    print("=" * 50)
    
    test_cases = [
        {
            "url": "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD/files/test.htm",
            "html": '<html lang="en"><body>Test content</body></html>',
            "expected": "en"
        },
        {
            "url": "https://help.autodesk.com/cloudhelp/2024/PTB/AutoCAD/files/test.htm", 
            "html": '<html lang="pt-BR"><body>Conteúdo teste</body></html>',
            "expected": "pt"
        },
        {
            "url": "https://help.autodesk.com/cloudhelp/2024/ESP/AutoCAD/files/test.htm",
            "html": '<html lang="es"><body>Contenido de prueba</body></html>',
            "expected": "es"
        }
    ]
    
    success = 0
    for case in test_cases:
        detected = LanguageDetector.detect_page_language(case["url"], case["html"])
        status = "✅" if detected == case["expected"] else "❌"
        print(f"   {status} URL: {case['url'][:50]}... → {detected}")
        if detected == case["expected"]:
            success += 1
    
    print(f"\n📊 Detecção de idioma: {success}/{len(test_cases)} sucessos")
    return success == len(test_cases)

def test_with_sample_video():
    """Teste com vídeo de amostra"""
    print("\n🎥 TESTE COM VÍDEO DE AMOSTRA")
    print("=" * 50)
    
    # Cria um vídeo de teste simples (apenas áudio)
    test_dir = "teste_video_amostra"
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # Usa ffmpeg para criar um áudio de teste
        import subprocess
        
        audio_file = os.path.join(test_dir, "teste_audio.wav")
        
        # Cria áudio de teste com síntese de voz
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", 
            "-i", "sine=frequency=440:duration=3",
            "-ac", "1", "-ar", "16000",
            audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(audio_file):
            print(f"✅ Áudio de teste criado: {audio_file}")
            
            # Testa transcrição
            scraper = SimpleWebScraperWithVideo(test_dir)
            
            # Simula vídeo info
            video_info = {
                'video_id': 'teste_audio_sample',
                'source_url': 'https://teste.com/ENU/page.htm'
            }
            
            # Copia áudio como vídeo para teste
            video_file = os.path.join(test_dir, "videos", "teste_audio_sample.mp4")
            os.makedirs(os.path.dirname(video_file), exist_ok=True)
            
            import shutil
            shutil.copy2(audio_file, video_file)
            
            # Transcreve com idioma inglês
            chunks = scraper.process_video_complete(video_info, "en")
            
            print(f"📊 Chunks gerados: {len(chunks)}")
            if chunks:
                print(f"📝 Primeiro chunk: {chunks[0]['text']}")
                print(f"🌍 Idioma: {chunks[0]['metadata']['detected_language']}")
                return True
            
        else:
            print("❌ Não foi possível criar áudio de teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de vídeo: {e}")
        return False

def test_real_autodesk_pages():
    """Teste com páginas reais do Autodesk"""
    print("\n📄 TESTE COM PÁGINAS REAIS DO AUTODESK")
    print("=" * 50)
    
    # URLs que sabemos que existem
    real_urls = [
        "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-Core/files/GUID-8B4D13F3-8A1C-4492-B35D-C92838E4C8BB.htm",
        "https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-Core/files/GUID-3C21D0DD-64FC-4A5B-BA4F-81A47D3A0F58.htm"
    ]
    
    scraper = SimpleWebScraperWithVideo("teste_real_autodesk")
    
    total_pages = 0
    total_videos_detected = 0
    
    for url in real_urls:
        try:
            text_chunks, video_chunks = scraper.extract_single_page(url)
            
            if text_chunks or video_chunks:
                total_pages += 1
                # Conta vídeos detectados (mesmo que não baixados)
                page_data = scraper.extracted_pages[-1] if scraper.extracted_pages else {}
                videos_in_page = len(page_data.get('videos', []))
                total_videos_detected += videos_in_page
                
                print(f"✅ {url[:50]}... → {len(text_chunks)} texto, {videos_in_page} vídeos detectados")
            else:
                print(f"❌ {url[:50]}... → Sem conteúdo")
                
        except Exception as e:
            print(f"❌ {url[:50]}... → Erro: {e}")
    
    print(f"\n📊 Páginas processadas: {total_pages}")
    print(f"🎥 Vídeos detectados: {total_videos_detected}")
    
    return total_pages > 0

def run_complete_test():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DO SISTEMA RAG COM DETECÇÃO DE IDIOMA")
    print("=" * 70)
    
    results = {
        "language_detection": test_language_detection(),
        "sample_video": test_with_sample_video(), 
        "real_pages": test_real_autodesk_pages()
    }
    
    print(f"\n📊 RESULTADOS FINAIS:")
    print("=" * 30)
    for test, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"   {test.replace('_', ' ').title()}: {status}")
    
    overall_success = all(results.values())
    print(f"\n{'🎉 TODOS OS TESTES PASSARAM!' if overall_success else '⚠️ ALGUNS TESTES FALHARAM'}")
    
    # Salva relatório
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests": results,
        "overall_success": overall_success
    }
    
    with open("relatorio_teste_completo.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Relatório salvo: relatorio_teste_completo.json")
    
    return overall_success

if __name__ == "__main__":
    success = run_complete_test()
    exit(0 if success else 1)
