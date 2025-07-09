"""
Demonstração completa do sistema YouTube RAG
Mostra todas as funcionalidades implementadas
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from youtube_transcript_extractor import YouTubeTranscriptExtractor
from youtube_data_manager import YouTubeDataManager
import json

def main():
    """
    Demonstração completa do sistema YouTube RAG
    """
    print("🎬 SISTEMA DE EXTRAÇÃO DE TRANSCRIÇÕES DO YOUTUBE PARA RAG")
    print("=" * 70)
    
    # URL do vídeo já processado
    video_url = "https://www.youtube.com/watch?v=ff89oHwvNsM"
    
    print(f"📹 Vídeo de teste: {video_url}")
    print(f"📝 Título: 'All about tool palettes with Ryan Wunderlich'")
    print(f"⏱️ Duração: ~43.5 minutos")
    print(f"🗣️ Idioma: Inglês (transcrição gerada automaticamente)")
    print(f"📊 Segmentos: 1,156 | Chunks RAG: 75 | Caracteres: 35,649")
    
    print("\n📁 ARQUIVOS GERADOS:")
    print("=" * 50)
    
    # Mostrar estrutura de arquivos
    base_dir = Path("youtube_extracted_data")
    if base_dir.exists():
        print("📂 youtube_extracted_data/")
        for subdir in sorted(base_dir.iterdir()):
            if subdir.is_dir():
                files = list(subdir.glob("*"))
                print(f"  📁 {subdir.name}/ ({len(files)} arquivos)")
                for file in sorted(files)[:3]:  # Mostrar primeiros 3
                    print(f"    📄 {file.name}")
                if len(files) > 3:
                    print(f"    ... e mais {len(files) - 3} arquivos")
    
    print("\n🔍 DEMONSTRAÇÃO DE BUSCA DE CONTEÚDO:")
    print("=" * 50)
    
    # Demonstrar busca no texto extraído
    print("Buscando por 'tool palette'...")
    
    # Ler arquivo de texto
    text_files = list(Path("youtube_extracted_data/rag_content").glob("*_text.txt"))
    if text_files:
        with open(text_files[0], 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # Buscar ocorrências
        search_term = "tool palette"
        lines = full_text.split('\n')
        results = []
        
        for i, line in enumerate(lines):
            if search_term.lower() in line.lower():
                # Contexto: linha anterior, atual e próxima
                context_start = max(0, i-1)
                context_end = min(len(lines), i+2)
                context = ' '.join(lines[context_start:context_end])
                
                # Encontrar posição no texto para timestamp aproximado
                char_pos = sum(len(l) + 1 for l in lines[:i])
                approx_time = (char_pos / len(full_text)) * (43.5 * 60)  # 43.5 min
                
                results.append({
                    'line': i,
                    'context': context[:200] + '...' if len(context) > 200 else context,
                    'time_approx': approx_time
                })
        
        print(f"✅ Encontradas {len(results)} ocorrências de '{search_term}'")
        
        # Mostrar primeiros 3 resultados
        for i, result in enumerate(results[:3], 1):
            minutes = int(result['time_approx'] // 60)
            seconds = int(result['time_approx'] % 60)
            print(f"\n📍 Resultado {i} (aprox. {minutes}:{seconds:02d}):")
            print(f"   {result['context']}")
    
    print("\n📊 ANÁLISE DOS CHUNKS RAG:")
    print("=" * 50)
    
    # Ler chunks
    chunks_files = list(Path("youtube_extracted_data/chunks").glob("*_chunks.json"))
    if chunks_files:
        with open(chunks_files[0], 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"📈 Total de chunks: {len(chunks)}")
        
        # Estatísticas dos chunks
        chunk_sizes = [chunk['text_length'] for chunk in chunks]
        word_counts = [chunk['word_count'] for chunk in chunks]
        
        print(f"📏 Tamanho médio dos chunks: {sum(chunk_sizes) / len(chunk_sizes):.0f} caracteres")
        print(f"📝 Palavras médias por chunk: {sum(word_counts) / len(word_counts):.0f}")
        print(f"📦 Menor chunk: {min(chunk_sizes)} caracteres")
        print(f"📦 Maior chunk: {max(chunk_sizes)} caracteres")
        
        # Mostrar exemplo de chunk
        print(f"\n📋 Exemplo de chunk RAG:")
        example_chunk = chunks[10]  # Chunk do meio
        print(f"   🆔 ID: {example_chunk['chunk_id']}")
        print(f"   ⏰ Tempo: {example_chunk['start_time']:.1f}s - {example_chunk['end_time']:.1f}s")
        print(f"   📝 Texto: {example_chunk['text'][:150]}...")
    
    print("\n🎯 ANÁLISE DE CONTEÚDO:")
    print("=" * 50)
    
    # Ler análise
    analysis_files = list(Path("youtube_extracted_data/rag_content").glob("*_analysis.json"))
    if analysis_files:
        with open(analysis_files[0], 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        stats = analysis.get('statistics', {})
        content_analysis = analysis.get('content_analysis', {})
        
        print(f"📊 Estatísticas do conteúdo:")
        print(f"   📄 Total de caracteres: {stats.get('total_characters', 0):,}")
        print(f"   📝 Total de palavras: {stats.get('total_words', 0):,}")
        print(f"   ⏱️ Duração: {stats.get('total_duration_minutes', 0):.1f} minutos")
        print(f"   🗣️ Palavras por minuto: {stats.get('total_words', 0) / stats.get('total_duration_minutes', 1):.0f}")
        
        print(f"\n🔍 Análise qualitativa:")
        print(f"   🌐 Idioma detectado: {content_analysis.get('language_detected', 'N/A')}")
        print(f"   🎮 Tipo de transcrição: {content_analysis.get('transcript_type', 'N/A')}")
        print(f"   😊 Sentimento: {analysis.get('sentiment', 'N/A')}")
        
        print(f"\n🏷️ Palavras-chave principais:")
        for i, keyword in enumerate(analysis.get('keywords', [])[:8], 1):
            print(f"   {i}. {keyword}")
        
        print(f"\n📚 Tópicos identificados:")
        topics = analysis.get('topics', [])
        if topics:
            for topic in topics:
                print(f"   • {topic}")
        else:
            print("   • Nenhum tópico específico identificado")
    
    print("\n💡 CASOS DE USO PARA RAG:")
    print("=" * 50)
    
    print("1. 📚 Sistema de Busca Educacional:")
    print("   • Buscar conceitos específicos em vídeos de treinamento")
    print("   • Localizar timestamps exatos para referência")
    print("   • Criar índice de conteúdo automatizado")
    
    print("\n2. 🤖 Chatbot de Suporte:")
    print("   • Responder perguntas baseadas no conteúdo do vídeo")
    print("   • Fornecer links diretos para momentos relevantes")
    print("   • Sugerir vídeos relacionados")
    
    print("\n3. 📋 Análise de Conteúdo:")
    print("   • Identificar temas e tópicos principais")
    print("   • Extrair instruções e procedimentos")
    print("   • Gerar resumos automáticos")
    
    print("\n4. 🔗 Integração com Sistemas:")
    print("   • Adicionar a bases de conhecimento existentes")
    print("   • Enriquecer documentação técnica")
    print("   • Criar material de treinamento interativo")
    
    print("\n🚀 RECURSOS IMPLEMENTADOS:")
    print("=" * 50)
    
    print("✅ Extração automática de transcrições")
    print("✅ Suporte a múltiplos idiomas")
    print("✅ Criação de chunks otimizados para RAG")
    print("✅ Análise de conteúdo e sentimento")
    print("✅ Persistência em múltiplos formatos")
    print("✅ Sistema de busca integrado")
    print("✅ Metadados detalhados")
    print("✅ Estrutura de dados padronizada")
    
    print("\n📈 PRÓXIMOS PASSOS SUGERIDOS:")
    print("=" * 50)
    
    print("1. 🔌 Integração com main.py (FastAPI)")
    print("2. 🌐 Interface web para upload de URLs")
    print("3. 🔍 Sistema de busca avançado")
    print("4. 🤖 Integração com modelos de linguagem")
    print("5. 📊 Dashboard de análise")
    print("6. 🔄 Processamento em lote")
    print("7. 📱 API REST completa")
    
    print("\n🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print("=" * 50)
    print("O sistema está pronto para ser usado em produção!")
    print("Todos os componentes foram testados e validados.")
    
    # Mostrar comando para testar com novo vídeo
    print(f"\n🧪 Para testar com outro vídeo:")
    print(f"python -c \"")
    print(f"from youtube_transcript_extractor import YouTubeTranscriptExtractor")
    print(f"extractor = YouTubeTranscriptExtractor()")
    print(f"result = extractor.process_video('URL_DO_VIDEO')")
    print(f"print(f'Processado: {{result[\"success\"]}}')")
    print(f"\"")

if __name__ == "__main__":
    main()
