#!/usr/bin/env python3
"""
Script de teste para verificar a detecção automática de idioma do Whisper
"""

import json
from pathlib import Path

def test_language_detection():
    """Testar detecção de idioma comparando dados antigos vs novos"""
    
    # Caminhos para os dados de teste
    storage_path = Path("storage")
    
    # Dado original (correto) - v3
    good_transcript_path = storage_path / "AutoCAD Architecture 2023 Tutorial" / "5 THINGS TO KNOW! Before You S" / "transcript_f1jFFxBPjDY.json"
    
    # Dado problemático - v3 (português incorreto)
    bad_transcript_path = storage_path / "AutoCAD Architecture 2023 Tutorial_v3" / "DETAILING Part 5" / "transcript_f1jFFxBPjDY.json"
    
    print("🧪 TESTE DE DETECÇÃO DE IDIOMA - WHISPER")
    print("=" * 50)
    
    # Verificar dados originais (corretos)
    if good_transcript_path.exists():
        with open(good_transcript_path, 'r', encoding='utf-8') as f:
            good_data = json.load(f)
        
        print(f"✅ DADOS CORRETOS encontrados:")
        print(f"   📂 Arquivo: {good_transcript_path}")
        print(f"   🌍 Idioma detectado: {good_data.get('language', 'N/A')}")
        print(f"   📝 Fonte: {good_data.get('source', 'N/A')}")
        print(f"   🔢 Segmentos: {len(good_data.get('segments', []))}")
        
        # Mostrar primeiros 200 caracteres do texto
        full_text = good_data.get('full_text', '')
        print(f"   📄 Texto (primeiros 200 chars): {full_text[:200]}...")
        print()
    else:
        print(f"❌ Arquivo de dados corretos não encontrado: {good_transcript_path}")
    
    # Verificar dados problemáticos
    if bad_transcript_path.exists():
        with open(bad_transcript_path, 'r', encoding='utf-8') as f:
            bad_data = json.load(f)
        
        print(f"❌ DADOS PROBLEMÁTICOS encontrados:")
        print(f"   📂 Arquivo: {bad_transcript_path}")
        print(f"   🌍 Idioma detectado: {bad_data.get('language', 'N/A')}")
        print(f"   📝 Fonte: {bad_data.get('source', 'N/A')}")
        print(f"   🔢 Segmentos: {len(bad_data.get('segments', []))}")
        
        # Mostrar primeiros 200 caracteres do texto
        full_text = bad_data.get('full_text', '')
        print(f"   📄 Texto (primeiros 200 chars): {full_text[:200]}...")
        print()
    else:
        print(f"❌ Arquivo de dados problemáticos não encontrado: {bad_transcript_path}")
    
    print("🔧 SOLUÇÃO IMPLEMENTADA:")
    print("   • Whisper agora usa language=None para detecção automática")
    print("   • Arquivos de áudio são salvos na pasta do vídeo para verificação")
    print("   • Idioma detectado é retornado nos metadados da transcrição")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("   1. Testar com novo vídeo quando IP não estiver bloqueado")
    print("   2. Verificar se arquivos de áudio são salvos corretamente")
    print("   3. Comparar qualidade da transcrição em inglês vs português")

if __name__ == "__main__":
    test_language_detection()
