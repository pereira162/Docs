#!/usr/bin/env python3
"""
🎯 DEMONSTRAÇÃO SISTEMA RAG COMPLETO COM VÍDEOS
===============================================
Mostra os dados extraídos do site Autodesk incluindo transcrições de vídeos
"""

import json
import os
import glob
from datetime import datetime

def find_extraction_data():
    """
    Encontra os dados de extração mais recentes
    """
    print("🔍 PROCURANDO DADOS DE EXTRAÇÃO")
    print("=" * 50)
    
    # Caminho específico onde sabemos que estão os dados
    test_dir = os.path.join("rag-system", "backend", "test_complete_autodesk")
    
    if os.path.exists(test_dir):
        print(f"📁 Diretório encontrado: {test_dir}")
        return test_dir
    
    # Fallback: procura em outros locais
    test_dirs = []
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    # Verifica diretório atual e pai
    for search_dir in [current_dir, parent_dir]:
        pattern = os.path.join(search_dir, "**/test*autodesk*")
        found_dirs = glob.glob(pattern, recursive=True)
        test_dirs.extend(found_dirs)
    
    if test_dirs:
        # Usa o mais recente
        latest_dir = max(test_dirs, key=os.path.getmtime)
        print(f"📁 Diretório encontrado: {latest_dir}")
        return latest_dir
    
    print("❌ Nenhum diretório de extração encontrado")
    return None

def analyze_extraction_data(extract_dir):
    """
    Analisa dados de extração
    """
    print(f"📊 ANALISANDO DADOS: {extract_dir}")
    print("=" * 60)
    
    # Arquivos de dados
    files_pattern = {
        'chunks': 'all_chunks_rag_*.json',
        'pages': 'pages_complete_*.json', 
        'videos': 'videos_complete_*.json'
    }
    
    data = {}
    
    for data_type, pattern in files_pattern.items():
        files = glob.glob(os.path.join(extract_dir, pattern))
        if files:
            latest_file = max(files, key=os.path.getmtime)
            print(f"📄 {data_type.capitalize()}: {os.path.basename(latest_file)}")
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data[data_type] = json.load(f)
            except Exception as e:
                print(f"❌ Erro ao carregar {data_type}: {e}")
                data[data_type] = None
        else:
            print(f"❌ Arquivo {data_type} não encontrado")
            data[data_type] = None
    
    return data

def show_statistics(data):
    """
    Mostra estatísticas dos dados
    """
    print("\n📊 ESTATÍSTICAS DE EXTRAÇÃO")
    print("=" * 50)
    
    if data.get('chunks'):
        chunks_data = data['chunks']
        # Verifica se é um dicionário com 'chunks' ou lista direta
        if isinstance(chunks_data, dict):
            chunks = chunks_data.get('chunks', [])
        else:
            chunks = chunks_data
        
        # Conta chunks por tipo usando o campo correto
        text_chunks = [c for c in chunks if c.get('type') == 'text_content']
        video_chunks = [c for c in chunks if c.get('type') == 'video_transcript']
        
        print(f"🔢 Total de chunks: {len(chunks)}")
        print(f"📄 Chunks de texto: {len(text_chunks)}")
        print(f"🎥 Chunks de vídeo: {len(video_chunks)}")
        
        if video_chunks:
            # Estatísticas de vídeos
            video_ids = set()
            total_duration = 0
            total_chars = 0
            
            for chunk in video_chunks:
                video_id = chunk.get('metadata', {}).get('video_id', '')
                video_ids.add(video_id)
                total_chars += len(chunk.get('text', ''))
                start_time = chunk.get('metadata', {}).get('start_time', 0)
                end_time = chunk.get('metadata', {}).get('end_time', 0)
                duration = end_time - start_time
                total_duration += duration
            
            print(f"🎬 Vídeos únicos: {len(video_ids)}")
            print(f"⏱️ Duração total: {total_duration:.1f}s ({total_duration/60:.1f}min)")
            print(f"📝 Caracteres transcritos: {total_chars:,}")
    
    if data.get('pages'):
        pages_data = data['pages']
        if isinstance(pages_data, dict):
            pages = pages_data.get('pages', [])
        else:
            pages = pages_data
        print(f"📄 Páginas extraídas: {len(pages)}")
    
    if data.get('videos'):
        videos_data = data['videos']
        if isinstance(videos_data, dict):
            videos = videos_data.get('videos', [])
        else:
            videos = videos_data
        print(f"🎥 Vídeos processados: {len(videos)}")

def show_video_samples(data):
    """
    Mostra amostras de transcrições de vídeo
    """
    print("\n🎥 AMOSTRAS DE TRANSCRIÇÕES")
    print("=" * 60)
    
    if not data.get('chunks'):
        print("❌ Dados de chunks não disponíveis")
        return
    
    chunks_data = data['chunks']
    if isinstance(chunks_data, dict):
        chunks = chunks_data.get('chunks', [])
    else:
        chunks = chunks_data
    
    video_chunks = [c for c in chunks if c.get('type') == 'video_transcript']
    
    if not video_chunks:
        print("❌ Nenhuma transcrição de vídeo encontrada")
        return
    
    # Mostra amostras dos primeiros vídeos
    video_samples = {}
    for chunk in video_chunks[:15]:  # Primeiros 15 chunks
        video_id = chunk.get('metadata', {}).get('video_id', 'unknown')
        if video_id not in video_samples:
            video_samples[video_id] = []
        video_samples[video_id].append(chunk)
    
    for i, (video_id, segments) in enumerate(video_samples.items()):
        if i >= 3:  # Mostra apenas 3 vídeos
            break
            
        print(f"\n🎬 VÍDEO {i+1}: {video_id}")
        print("-" * 40)
        
        # Mostra primeiros segmentos
        for j, segment in enumerate(segments[:3]):
            metadata = segment.get('metadata', {})
            start_time = metadata.get('start_time', 0)
            end_time = metadata.get('end_time', 0)
            content = segment.get('text', '')[:100] + "..." if len(segment.get('text', '')) > 100 else segment.get('text', '')
            
            print(f"   {j+1}. [{start_time:.1f}s - {end_time:.1f}s]: {content}")
        
        if len(segments) > 3:
            print(f"   ... e mais {len(segments)-3} segmentos")

def show_search_example(data):
    """
    Mostra exemplo de busca simples
    """
    print("\n🔍 EXEMPLO DE BUSCA SIMPLES")
    print("=" * 50)
    
    if not data.get('chunks'):
        print("❌ Dados de chunks não disponíveis")
        return
    
    chunks_data = data['chunks']
    if isinstance(chunks_data, dict):
        chunks = chunks_data.get('chunks', [])
    else:
        chunks = chunks_data
    
    # Busca por palavra-chave simples
    keywords = ['AutoCAD', 'architecture', 'customization', 'drawing', 'design']
    
    for keyword in keywords:
        print(f"\n🔍 Buscando por: '{keyword}'")
        print("-" * 30)
        
        matches = []
        for chunk in chunks:
            content = chunk.get('text', '').lower()
            if keyword.lower() in content:
                matches.append(chunk)
        
        if matches:
            print(f"✅ {len(matches)} resultados encontrados")
            
            # Mostra primeiro resultado
            first_match = matches[0]
            content = first_match.get('text', '')[:150] + "..." if len(first_match.get('text', '')) > 150 else first_match.get('text', '')
            
            icon = "🎥" if first_match.get('type') == 'video_transcript' else "📄"
            print(f"{icon} Tipo: {first_match.get('type', 'unknown')}")
            metadata = first_match.get('metadata', {})
            print(f"📍 Fonte: {metadata.get('source_url', 'unknown')}")
            print(f"💬 Conteúdo: {content}")
        else:
            print(f"❌ Nenhum resultado para '{keyword}'")

def main():
    """
    Função principal
    """
    print("🎯 DEMONSTRAÇÃO SISTEMA RAG AUTODESK")
    print("=" * 60)
    print("Sistema de extração completa com vídeos transcritos")
    print()
    
    # Encontra dados
    extract_dir = find_extraction_data()
    if not extract_dir:
        print("\n💡 INSTRUÇÕES:")
        print("Execute primeiro: python web_scraper_video_extractor.py")
        return
    
    # Analisa dados
    data = analyze_extraction_data(extract_dir)
    
    # Mostra estatísticas
    show_statistics(data)
    
    # Mostra amostras de vídeos
    show_video_samples(data)
    
    # Exemplo de busca
    show_search_example(data)
    
    print("\n🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print("✅ Sistema de extração funcionando com vídeos transcritos")
    print("💡 Para busca semântica avançada, use sentence-transformers")

if __name__ == "__main__":
    main()
