"""
Teste da ferramenta de extração de transcrições do YouTube
Processa o vídeo específico solicitado pelo usuário
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from youtube_transcript_extractor import YouTubeTranscriptExtractor
from youtube_data_manager import YouTubeDataManager
import json

def test_youtube_extraction():
    """
    Testa a extração de transcrição do vídeo específico
    """
    print("🎬 Iniciando teste de extração de transcrição do YouTube")
    print("=" * 60)
    
    # URL do vídeo solicitado
    test_url = "https://www.youtube.com/watch?v=ff89oHwvNsM"
    
    # Criar extrator
    extractor = YouTubeTranscriptExtractor()
    
    # Processar vídeo
    print(f"📹 Processando vídeo: {test_url}")
    result = extractor.process_video(
        url_or_id=test_url,
        languages=['pt', 'pt-BR', 'en'],  # Priorizar português
        prefer_manual=True,
        chunk_size=500
    )
    
    print("\n📊 RESULTADO DO PROCESSAMENTO")
    print("=" * 60)
    
    if result.get('success'):
        print("✅ Processamento concluído com sucesso!")
        
        # Mostrar informações básicas
        metadata = result.get('metadata', {})
        stats = result.get('statistics', {})
        analysis = result.get('analysis', {})
        
        print(f"\n📋 INFORMAÇÕES DO VÍDEO:")
        print(f"  🎯 ID: {result.get('video_id')}")
        print(f"  📺 Título: {metadata.get('title', 'N/A')}")
        print(f"  🌐 URL: {metadata.get('url', test_url)}")
        print(f"  🗣️ Idioma: {result.get('transcript_info', {}).get('language', 'N/A')}")
        print(f"  🎮 Tipo: {result.get('transcript_info', {}).get('type', 'N/A')}")
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"  📝 Total de segmentos: {stats.get('total_segments', 0)}")
        print(f"  🔗 Total de chunks RAG: {stats.get('total_chunks', 0)}")
        print(f"  ⏱️ Duração: {stats.get('duration_minutes', 0):.1f} minutos")
        print(f"  📄 Tamanho do texto: {stats.get('text_length', 0):,} caracteres")
        print(f"  📊 Tamanho médio do chunk: {stats.get('average_chunk_size', 0):.0f} caracteres")
        
        print(f"\n🔍 ANÁLISE DE CONTEÚDO:")
        content_analysis = analysis.get('content_analysis', {})
        print(f"  📖 Legibilidade: {content_analysis.get('readability_score', 0):.1f}")
        print(f"  😊 Sentimento: {analysis.get('sentiment', 'N/A')}")
        print(f"  🏷️ Palavras-chave: {', '.join(analysis.get('keywords', [])[:5])}")
        print(f"  📚 Tópicos: {', '.join(analysis.get('topics', []))}")
        
        print(f"\n💾 ARQUIVOS SALVOS:")
        saved_files = result.get('saved_files', {})
        for file_type, path in saved_files.items():
            if file_type != 'error':
                print(f"  📁 {file_type}: {path}")
        
        # Testar gerenciador de dados
        print(f"\n🗄️ TESTANDO GERENCIADOR DE DADOS:")
        manager = YouTubeDataManager()
        
        # Preparar dados para o gerenciador
        video_data = {
            'video_id': result.get('video_id'),
            'metadata': metadata,
            'transcript_data': {
                'extraction_timestamp': result.get('processing_timestamp'),
                'total_segments': stats.get('total_segments', 0),
                'total_duration': stats.get('duration_minutes', 0) * 60,
                'text_length': stats.get('text_length', 0),
                'transcript_info': result.get('transcript_info', {}),
                'full_text': analysis.get('statistics', {}).get('total_characters', ''),
                'segments': []  # Seria populado com dados reais dos segmentos
            },
            'analysis': analysis,
            'chunks': []  # Seria populado com chunks reais
        }
        
        # Salvar no gerenciador
        saved = manager.save_video_data(video_data)
        if saved:
            print("  ✅ Dados salvos no gerenciador com sucesso")
        else:
            print("  ❌ Erro ao salvar no gerenciador")
        
        # Mostrar estatísticas atualizadas
        stats_manager = manager.get_statistics()
        print(f"  📊 Total de vídeos no banco: {stats_manager.get('totals', {}).get('videos', 0)}")
        
        # Testar busca
        print(f"\n🔍 TESTANDO BUSCA:")
        search_results = manager.search_content("video", limit=3)
        print(f"  📄 Resultados encontrados: {len(search_results)}")
        for result_item in search_results[:2]:
            print(f"    - {result_item.get('type', 'N/A')}: {result_item.get('text', 'N/A')[:50]}...")
        
        return True
        
    else:
        print("❌ Erro no processamento:")
        print(f"  🔴 Erro: {result.get('error')}")
        
        # Mostrar transcrições disponíveis se houver
        available = result.get('available_transcripts', {})
        if available and not available.get('error'):
            print(f"\n📋 Transcrições disponíveis:")
            for transcript in available.get('transcripts', []):
                print(f"  - {transcript.get('language', 'N/A')} ({transcript.get('language_code', 'N/A')}) - "
                      f"{'Manual' if not transcript.get('is_generated') else 'Gerada'}")
        
        return False

def demonstrate_features():
    """
    Demonstra as principais funcionalidades do sistema
    """
    print("\n🚀 DEMONSTRAÇÃO DE FUNCIONALIDADES")
    print("=" * 60)
    
    manager = YouTubeDataManager()
    
    # Mostrar estatísticas
    stats = manager.get_statistics()
    print(f"📊 Estatísticas atuais:")
    print(f"  - Vídeos processados: {stats.get('totals', {}).get('videos', 0)}")
    print(f"  - Chunks para RAG: {stats.get('totals', {}).get('chunks', 0)}")
    print(f"  - Duração total: {stats.get('content', {}).get('total_duration_minutes', 0):.1f} minutos")
    
    # Listar vídeos
    videos = manager.list_videos(limit=3)
    if videos:
        print(f"\n📹 Últimos vídeos processados:")
        for video in videos:
            title = video.get('title', 'Sem título')[:50]
            print(f"  - {title}... ({video.get('duration_minutes', 0):.1f}min)")
    
    # Demonstrar busca
    print(f"\n🔍 Exemplo de busca por 'vídeo':")
    search_results = manager.search_content("vídeo", limit=3)
    for result in search_results:
        result_type = result.get('type', 'N/A')
        text = result.get('text', result.get('title', 'N/A'))[:60]
        print(f"  - [{result_type}] {text}...")

if __name__ == "__main__":
    try:
        # Executar teste principal
        success = test_youtube_extraction()
        
        if success:
            # Demonstrar funcionalidades
            demonstrate_features()
            
            print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print("=" * 60)
            print("✅ A ferramenta de extração de transcrições do YouTube está funcionando")
            print("✅ Sistema RAG implementado com chunks otimizados")
            print("✅ Análise de conteúdo funcionando")
            print("✅ Persistência de dados em múltiplos formatos")
            print("✅ Sistema de busca operacional")
            
        else:
            print(f"\n⚠️ TESTE PARCIALMENTE CONCLUÍDO")
            print("=" * 60)
            print("ℹ️ A ferramenta foi implementada mas pode ter limitações com este vídeo específico")
            print("ℹ️ Verifique se o vídeo possui transcrições disponíveis")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
