#!/usr/bin/env python3
"""
🔍 DEMONSTRAÇÃO DE BUSCA RAG COM VÍDEOS TRANSCRITOS
==================================================
Sistema de busca semântica que combina:
- Texto extraído de páginas web
- Transcrições completas de vídeos
- Busca unificada por similaridade semântica
"""

import json
import numpy as np
import datetime
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

class VideoRAGSearchEngine:
    """
    🔍 Motor de busca RAG com suporte a conteúdo de vídeo
    """
    
    def __init__(self, chunks_file: str):
        """
        Inicializa o motor de busca com chunks de texto e vídeo
        """
        print("🔍 INICIALIZANDO MOTOR DE BUSCA RAG")
        print("=" * 50)
        
        # Carrega chunks
        self.chunks_file = chunks_file
        self.chunks = self._load_chunks()
        
        # Inicializa modelo de embedding
        print("🤖 Carregando modelo de embeddings...")
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Pré-computa embeddings
        print("🧠 Computando embeddings dos chunks...")
        self.embeddings = self._compute_embeddings()
        
        # Estatísticas
        text_chunks = len([c for c in self.chunks if c['type'] == 'text'])
        video_chunks = len([c for c in self.chunks if c['type'] == 'video'])
        
        print(f"✅ Sistema inicializado:")
        print(f"   📄 Chunks de texto: {text_chunks}")
        print(f"   🎥 Chunks de vídeo: {video_chunks}")
        print(f"   🔢 Total: {len(self.chunks)}")
        print(f"   🧠 Embeddings: {self.embeddings.shape}")
        print()
    
    def _load_chunks(self) -> List[Dict[str, Any]]:
        """
        Carrega chunks do arquivo JSON
        """
        if not os.path.exists(self.chunks_file):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.chunks_file}")
        
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('chunks', [])
    
    def _compute_embeddings(self) -> np.ndarray:
        """
        Computa embeddings para todos os chunks
        """
        texts = []
        for chunk in self.chunks:
            if chunk['type'] == 'text':
                texts.append(chunk['content'])
            elif chunk['type'] == 'video':
                # Para vídeos, usa título + transcrição
                video_text = f"{chunk['title']}: {chunk['content']}"
                texts.append(video_text)
        
        embeddings = self.model.encode(texts)
        return embeddings
    
    def search(self, query: str, top_k: int = 5, content_type: str = 'all') -> List[Dict[str, Any]]:
        """
        Busca semântica nos chunks
        
        Args:
            query: Consulta de busca
            top_k: Número de resultados
            content_type: 'all', 'text', 'video'
        """
        print(f"🔍 BUSCA: '{query}'")
        print(f"📊 Tipo: {content_type} | Top: {top_k}")
        print("-" * 50)
        
        # Computa embedding da query
        query_embedding = self.model.encode([query])
        
        # Calcula similaridades
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Filtra por tipo de conteúdo
        filtered_indices = []
        for i, chunk in enumerate(self.chunks):
            if content_type == 'all' or chunk['type'] == content_type:
                filtered_indices.append(i)
        
        # Ordena por similaridade
        filtered_similarities = [(i, similarities[i]) for i in filtered_indices]
        filtered_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retorna top_k resultados
        results = []
        for i, (chunk_idx, similarity) in enumerate(filtered_similarities[:top_k]):
            chunk = self.chunks[chunk_idx].copy()
            chunk['similarity'] = similarity
            chunk['rank'] = i + 1
            results.append(chunk)
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]]):
        """
        Exibe resultados formatados
        """
        for result in results:
            icon = "🎥" if result['type'] == 'video' else "📄"
            similarity_percent = result['similarity'] * 100
            
            print(f"{icon} RESULTADO #{result['rank']} - {similarity_percent:.1f}% similaridade")
            print(f"   📍 Fonte: {result['source']}")
            
            if result['type'] == 'video':
                print(f"   🎬 Vídeo: {result['video_id']}")
                print(f"   ⏰ Tempo: {result['start_time']:.1f}s - {result['end_time']:.1f}s")
                print(f"   🎯 Título: {result['title']}")
            
            # Limita o conteúdo exibido
            content = result['content']
            if len(content) > 200:
                content = content[:200] + "..."
            
            print(f"   💬 Conteúdo: {content}")
            print()
    
    def demo_searches(self):
        """
        Demonstração com várias buscas
        """
        queries = [
            "como criar um projeto de arquitetura",
            "workflow de trabalho no AutoCAD",
            "personalização de interface",
            "comandos básicos de desenho",
            "ferramentas de dimensionamento"
        ]
        
        for query in queries:
            print("🎯 DEMONSTRAÇÃO DE BUSCA")
            print("=" * 60)
            
            # Busca geral
            results = self.search(query, top_k=3)
            self.print_results(results)
            
            # Busca só em vídeos
            print("🎥 RESULTADOS APENAS DE VÍDEOS:")
            print("-" * 40)
            video_results = self.search(query, top_k=2, content_type='video')
            if video_results:
                self.print_results(video_results)
            else:
                print("❌ Nenhum vídeo encontrado para esta busca")
            
            print("\n" + "="*60 + "\n")
    
    def interactive_search(self):
        """
        Busca interativa
        """
        print("🔍 BUSCA INTERATIVA RAG")
        print("=" * 40)
        print("Digite suas consultas (ou 'quit' para sair):")
        print()
        
        while True:
            query = input("🔍 Busca: ").strip()
            
            if query.lower() in ['quit', 'sair', 'exit']:
                print("👋 Encerrando busca...")
                break
            
            if not query:
                continue
            
            try:
                results = self.search(query, top_k=5)
                self.print_results(results)
            except Exception as e:
                print(f"❌ Erro na busca: {e}")

def main():
    """
    Função principal de demonstração
    """
    print("🎯 DEMONSTRAÇÃO SISTEMA RAG COM VÍDEOS")
    print("=" * 60)
    print("Sistema que combina busca em texto e transcrições de vídeo")
    print()
    
    # Encontra o arquivo de chunks mais recente
    chunks_files = []
    for file in os.listdir('.'):
        if file.startswith('test_complete_autodesk') and os.path.isdir(file):
            for subfile in os.listdir(file):
                if subfile.startswith('all_chunks_rag_') and subfile.endswith('.json'):
                    chunks_files.append(os.path.join(file, subfile))
    
    if not chunks_files:
        print("❌ Nenhum arquivo de chunks encontrado!")
        print("Execute primeiro o web_scraper_video_extractor.py")
        return
    
    # Usa o arquivo mais recente
    chunks_file = max(chunks_files, key=os.path.getmtime)
    print(f"📁 Usando chunks: {chunks_file}")
    print()
    
    try:
        # Inicializa motor de busca
        search_engine = VideoRAGSearchEngine(chunks_file)
        
        # Demonstração automática
        search_engine.demo_searches()
        
        # Busca interativa
        search_engine.interactive_search()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
