# Sistema RAG - Serviço de Busca e Query

## Implementação do Sistema RAG

### 1. Serviço RAG Core (app/services/rag_service.py)
```python
import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import DocumentLink, ProcessedDocument, DocumentChunk
from app.schemas.rag import RAGQuery, RAGResult, RAGResponse

class RAGService:
    def __init__(self):
        self.vector_client = QdrantClient(url=settings.QDRANT_URL)
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.collection_name = settings.QDRANT_COLLECTION
    
    async def query(self, query_request: RAGQuery, user_id: Optional[str] = None) -> RAGResponse:
        """
        Executar consulta RAG completa
        """
        start_time = time.time()
        
        # 1. Gerar embedding da query
        query_embedding = self.embedder.encode([query_request.query])[0]
        
        # 2. Buscar documentos similares
        search_results = await self._vector_search(
            query_embedding=query_embedding,
            limit=query_request.max_results,
            threshold=query_request.threshold,
            category_filter=query_request.category_filter,
            user_id=user_id
        )
        
        # 3. Enriquecer resultados com metadados
        enriched_results = await self._enrich_results(search_results)
        
        # 4. Construir contexto para LLM
        context = self._build_context(enriched_results)
        
        processing_time = time.time() - start_time
        
        return RAGResponse(
            query=query_request.query,
            results=enriched_results,
            context=context,
            total_results=len(enriched_results),
            processing_time=processing_time
        )
    
    async def _vector_search(
        self, 
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        category_filter: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar no vector database com filtros
        """
        # Construir filtros
        filters = []
        
        if user_id:
            # Filtrar por documentos do usuário
            filters.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            )
        
        if category_filter:
            # Filtrar por categorias
            filters.append(
                FieldCondition(
                    key="category_id",
                    match=MatchValue(any=category_filter)
                )
            )
        
        # Construir filtro final
        search_filter = Filter(must=filters) if filters else None
        
        # Executar busca
        search_results = self.vector_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit * 2,  # Buscar mais para filtrar por threshold
            with_payload=True,
            score_threshold=threshold,
            query_filter=search_filter
        )
        
        return [
            {
                'id': hit.id,
                'score': hit.score,
                'payload': hit.payload
            }
            for hit in search_results
            if hit.score >= threshold
        ][:limit]
    
    async def _enrich_results(self, search_results: List[Dict[str, Any]]) -> List[RAGResult]:
        """
        Enriquecer resultados com dados do banco
        """
        db = SessionLocal()
        enriched_results = []
        
        try:
            for result in search_results:
                payload = result['payload']
                
                # Buscar informações adicionais do documento
                chunk = db.query(DocumentChunk).filter(
                    DocumentChunk.id == result['id']
                ).first()
                
                if chunk:
                    processed_doc = db.query(ProcessedDocument).filter(
                        ProcessedDocument.id == chunk.document_id
                    ).first()
                    
                    if processed_doc:
                        document_link = db.query(DocumentLink).filter(
                            DocumentLink.id == processed_doc.document_link_id
                        ).first()
                        
                        enriched_result = RAGResult(
                            id=result['id'],
                            content=payload['content'],
                            score=result['score'],
                            chunk_index=payload['chunk_index'],
                            document_id=str(processed_doc.id),
                            document_link_id=str(document_link.id) if document_link else None,
                            document_title=document_link.title if document_link else None,
                            document_url=document_link.url if document_link else None,
                            metadata=payload.get('metadata', {})
                        )
                        
                        enriched_results.append(enriched_result)
            
            return enriched_results
            
        finally:
            db.close()
    
    def _build_context(self, results: List[RAGResult]) -> str:
        """
        Construir contexto consolidado para LLM
        """
        if not results:
            return ""
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            source_info = ""
            if result.document_title:
                source_info = f" (Fonte: {result.document_title})"
            elif result.document_url:
                source_info = f" (Fonte: {result.document_url})"
            
            context_parts.append(
                f"[{i}] {result.content}{source_info}"
            )
        
        return "\n\n".join(context_parts)
    
    async def search_similar_documents(
        self, 
        document_id: str, 
        limit: int = 5
    ) -> List[RAGResult]:
        """
        Encontrar documentos similares a um documento específico
        """
        db = SessionLocal()
        
        try:
            # Buscar chunks do documento original
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).limit(3).all()  # Usar primeiros chunks como referência
            
            if not chunks:
                return []
            
            # Combinar conteúdo dos chunks
            combined_content = " ".join([chunk.content for chunk in chunks])
            
            # Gerar embedding do conteúdo combinado
            query_embedding = self.embedder.encode([combined_content])[0]
            
            # Buscar documentos similares (excluindo o próprio documento)
            search_results = self.vector_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit * 2,
                with_payload=True
            )
            
            # Filtrar resultados do mesmo documento
            filtered_results = [
                result for result in search_results
                if result.payload['document_id'] != document_id
            ][:limit]
            
            return await self._enrich_results([
                {
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload
                }
                for hit in filtered_results
            ])
            
        finally:
            db.close()
    
    async def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Gerar resumo de um documento usando seus chunks principais
        """
        db = SessionLocal()
        
        try:
            # Buscar chunks do documento
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
            
            if not chunks:
                return {"error": "Documento não encontrado"}
            
            # Buscar informações do documento
            processed_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.id == document_id
            ).first()
            
            document_link = None
            if processed_doc:
                document_link = db.query(DocumentLink).filter(
                    DocumentLink.id == processed_doc.document_link_id
                ).first()
            
            # Calcular estatísticas
            total_tokens = sum(chunk.token_count for chunk in chunks)
            total_characters = sum(len(chunk.content) for chunk in chunks)
            
            # Selecionar chunks representativos (início, meio, fim)
            representative_chunks = []
            if len(chunks) >= 3:
                representative_chunks = [
                    chunks[0],  # Início
                    chunks[len(chunks) // 2],  # Meio
                    chunks[-1]  # Fim
                ]
            else:
                representative_chunks = chunks
            
            return {
                "document_id": document_id,
                "title": document_link.title if document_link else "Sem título",
                "url": document_link.url if document_link else None,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "total_characters": total_characters,
                "representative_content": [
                    {
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                    }
                    for chunk in representative_chunks
                ]
            }
            
        finally:
            db.close()
```

### 2. Schemas Pydantic (app/schemas/rag.py)
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RAGQuery(BaseModel):
    query: str = Field(..., description="Texto da consulta")
    max_results: int = Field(default=10, ge=1, le=50, description="Máximo de resultados")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Threshold de similaridade")
    category_filter: Optional[List[str]] = Field(default=None, description="Filtro por categorias")
    include_context: bool = Field(default=True, description="Incluir contexto consolidado")

class RAGResult(BaseModel):
    id: str
    content: str
    score: float
    chunk_index: int
    document_id: str
    document_link_id: Optional[str] = None
    document_title: Optional[str] = None
    document_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

class RAGResponse(BaseModel):
    query: str
    results: List[RAGResult]
    context: Optional[str] = None
    total_results: int
    processing_time: float

class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class DocumentSimilarityQuery(BaseModel):
    document_id: str
    limit: int = Field(default=5, ge=1, le=20)

class AdvancedRAGQuery(RAGQuery):
    """Query RAG avançada com mais opções"""
    rerank: bool = Field(default=False, description="Re-rankar resultados")
    expand_query: bool = Field(default=False, description="Expandir query com sinônimos")
    hybrid_search: bool = Field(default=False, description="Busca híbrida (vetor + texto)")
    user_context: Optional[str] = Field(default=None, description="Contexto adicional do usuário")
```

### 3. API Endpoints (app/api/v1/rag.py)
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import time

from app.services.rag_service import RAGService
from app.schemas.rag import (
    RAGQuery, RAGResponse, SearchQuery, DocumentSimilarityQuery,
    AdvancedRAGQuery
)
from app.core.auth import get_current_user
from app.models import User

router = APIRouter()

@router.post("/query", response_model=RAGResponse)
async def query_rag(
    query: RAGQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Executar consulta RAG
    """
    try:
        rag_service = RAGService()
        result = await rag_service.query(query, user_id=str(current_user.id))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced-query", response_model=RAGResponse)
async def advanced_query_rag(
    query: AdvancedRAGQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta RAG avançada com mais opções
    """
    try:
        rag_service = RAGService()
        
        # Por enquanto, usar a mesma implementação base
        # TODO: Implementar funcionalidades avançadas (rerank, hybrid search, etc.)
        base_query = RAGQuery(
            query=query.query,
            max_results=query.max_results,
            threshold=query.threshold,
            category_filter=query.category_filter
        )
        
        result = await rag_service.query(base_query, user_id=str(current_user.id))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Busca simples por similaridade
    """
    try:
        rag_service = RAGService()
        
        query = RAGQuery(
            query=search_query.query,
            max_results=search_query.limit,
            threshold=search_query.threshold,
            include_context=False
        )
        
        result = await rag_service.query(query, user_id=str(current_user.id))
        return result.results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{document_id}")
async def get_similar_documents(
    document_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    """
    Encontrar documentos similares
    """
    try:
        rag_service = RAGService()
        results = await rag_service.search_similar_documents(document_id, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}/summary")
async def get_document_summary(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obter resumo de um documento
    """
    try:
        rag_service = RAGService()
        summary = await rag_service.get_document_summary(document_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-query")
async def batch_query_rag(
    queries: List[str],
    max_results: int = Query(default=10, ge=1, le=50),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user)
):
    """
    Executar múltiplas consultas RAG em lote
    """
    try:
        rag_service = RAGService()
        results = []
        
        for query_text in queries:
            query = RAGQuery(
                query=query_text,
                max_results=max_results,
                threshold=threshold
            )
            result = await rag_service.query(query, user_id=str(current_user.id))
            results.append(result)
        
        return {
            "queries": queries,
            "results": results,
            "total_queries": len(queries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rag_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Estatísticas do sistema RAG
    """
    try:
        rag_service = RAGService()
        
        # Obter estatísticas do Qdrant
        collection_info = rag_service.vector_client.get_collection(
            collection_name=rag_service.collection_name
        )
        
        return {
            "total_vectors": collection_info.vectors_count,
            "collection_status": collection_info.status,
            "indexed_vectors": collection_info.indexed_vectors_count,
            "embedding_model": rag_service.embedder.get_sentence_embedding_dimension(),
            "vector_size": collection_info.config.params.vectors.size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Melhorias Avançadas do RAG

#### Hybrid Search (app/services/hybrid_search.py)
```python
from typing import List, Dict, Any
from elasticsearch import Elasticsearch
import asyncio

class HybridSearchService:
    """
    Combinar busca vetorial (semântica) com busca textual (lexical)
    """
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200"):
        self.es_client = Elasticsearch([elasticsearch_url])
        self.index_name = "documents_text"
    
    async def hybrid_search(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        limit: int = 10,
        alpha: float = 0.7  # Peso da busca vetorial vs textual
    ) -> List[Dict[str, Any]]:
        """
        Combinar resultados de busca vetorial e textual
        """
        # Busca textual no Elasticsearch
        text_results = await self._text_search(query, limit * 2)
        
        # Combinar e re-rankar resultados
        combined_results = self._combine_results(
            vector_results, text_results, alpha
        )
        
        return combined_results[:limit]
    
    async def _text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Busca textual usando Elasticsearch
        """
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "title", "description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": limit,
            "_source": ["chunk_id", "content", "document_id"]
        }
        
        try:
            response = self.es_client.search(
                index=self.index_name,
                body=search_body
            )
            
            return [
                {
                    "id": hit["_source"]["chunk_id"],
                    "score": hit["_score"],
                    "content": hit["_source"]["content"],
                    "type": "text"
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"Erro na busca textual: {e}")
            return []
    
    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        alpha: float
    ) -> List[Dict[str, Any]]:
        """
        Combinar e re-rankar resultados usando Reciprocal Rank Fusion
        """
        # Normalizar scores
        vector_scores = {r["id"]: r["score"] for r in vector_results}
        text_scores = {r["id"]: r["score"] for r in text_results}
        
        # Aplicar Reciprocal Rank Fusion
        all_ids = set(vector_scores.keys()) | set(text_scores.keys())
        combined_scores = {}
        
        for doc_id in all_ids:
            vector_score = vector_scores.get(doc_id, 0) * alpha
            text_score = text_scores.get(doc_id, 0) * (1 - alpha)
            combined_scores[doc_id] = vector_score + text_score
        
        # Ordenar por score combinado
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [{"id": doc_id, "score": score} for doc_id, score in sorted_results]
```

### 5. Query Expansion (app/services/query_expansion.py)
```python
import nltk
from nltk.corpus import wordnet
from typing import List, Set

class QueryExpansionService:
    """
    Expandir queries com sinônimos e termos relacionados
    """
    
    def __init__(self):
        # Baixar recursos do NLTK se necessário
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
    
    def expand_query(self, query: str, max_synonyms: int = 3) -> str:
        """
        Expandir query com sinônimos
        """
        words = query.lower().split()
        expanded_words = set(words)
        
        for word in words:
            synonyms = self._get_synonyms(word, max_synonyms)
            expanded_words.update(synonyms)
        
        # Construir query expandida
        original_query = query
        synonym_query = " ".join(expanded_words - set(words))
        
        if synonym_query:
            return f"{original_query} {synonym_query}"
        else:
            return original_query
    
    def _get_synonyms(self, word: str, max_count: int) -> Set[str]:
        """
        Obter sinônimos de uma palavra usando WordNet
        """
        synonyms = set()
        
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym != word and len(synonyms) < max_count:
                    synonyms.add(synonym)
        
        return synonyms
```

Este sistema RAG fornece funcionalidades avançadas de busca semântica, híbrida e expansão de queries, proporcionando resultados mais precisos e relevantes para os assistentes de IA.
