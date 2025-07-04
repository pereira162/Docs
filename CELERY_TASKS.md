# Sistema RAG com Docling - Tarefas Celery

## Configuração Celery

### 1. Configuração Principal (app/core/celery_app.py)
```python
from celery import Celery
from app.core.config import settings

# Criar instância do Celery
celery_app = Celery(
    "rag_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.document_processing',
        'app.tasks.embedding_generation',
        'app.tasks.vector_indexing'
    ]
)

# Configurações
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Roteamento de tasks
celery_app.conf.task_routes = {
    'app.tasks.document_processing.*': {'queue': 'document_processing'},
    'app.tasks.embedding_generation.*': {'queue': 'embedding_generation'},
    'app.tasks.vector_indexing.*': {'queue': 'vector_indexing'},
}
```

### 2. Task de Processamento de Documentos (app/tasks/document_processing.py)
```python
import asyncio
from celery import current_task
from celery.utils.log import get_task_logger
from pathlib import Path
import tempfile
import time
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import DocumentLink, ProcessedDocument, ProcessingLog
from app.services.document_processor import DocumentProcessor
from app.services.storage_service import StorageService
from app.tasks.embedding_generation import generate_embeddings_task

logger = get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_link_id: str) -> Dict[str, Any]:
    """
    Task principal para processar um documento
    """
    start_time = time.time()
    db = SessionLocal()
    
    try:
        # 1. Buscar documento no banco
        document_link = db.query(DocumentLink).filter(
            DocumentLink.id == document_link_id
        ).first()
        
        if not document_link:
            raise ValueError(f"Document link {document_link_id} not found")
        
        # Atualizar status para processando
        document_link.status = "processing"
        db.commit()
        
        # Log início do processamento
        log_processing_step(db, document_link_id, "processing_started", "success", 
                          "Iniciando processamento do documento")
        
        # 2. Download do documento
        current_task.update_state(state='PROGRESS', meta={'step': 'downloading', 'progress': 10})
        download_result = asyncio.run(download_document_step(document_link))
        
        if not download_result['success']:
            raise Exception(f"Erro no download: {download_result['error']}")
        
        log_processing_step(db, document_link_id, "download", "success", 
                          f"Documento baixado: {download_result['file_size']} bytes")
        
        # 3. Processamento com Docling
        current_task.update_state(state='PROGRESS', meta={'step': 'extracting', 'progress': 30})
        extraction_result = asyncio.run(extract_content_step(download_result['file_path']))
        
        if not extraction_result['success']:
            raise Exception(f"Erro na extração: {extraction_result['error']}")
        
        log_processing_step(db, document_link_id, "content_extraction", "success", 
                          f"Conteúdo extraído: {len(extraction_result['text_content'])} caracteres")
        
        # 4. Criar chunks
        current_task.update_state(state='PROGRESS', meta={'step': 'chunking', 'progress': 50})
        chunks = create_chunks_step(extraction_result['text_content'])
        
        log_processing_step(db, document_link_id, "chunking", "success", 
                          f"Criados {len(chunks)} chunks")
        
        # 5. Salvar documento processado
        current_task.update_state(state='PROGRESS', meta={'step': 'saving', 'progress': 70})
        processed_doc = save_processed_document(
            db, document_link, download_result, extraction_result, chunks
        )
        
        # 6. Iniciar geração de embeddings
        current_task.update_state(state='PROGRESS', meta={'step': 'embeddings', 'progress': 80})
        generate_embeddings_task.delay(str(processed_doc.id))
        
        # 7. Finalizar
        processing_time = int((time.time() - start_time) * 1000)
        document_link.status = "completed"
        document_link.processed_at = func.now()
        db.commit()
        
        log_processing_step(db, document_link_id, "processing_completed", "success", 
                          f"Processamento concluído em {processing_time}ms")
        
        return {
            'success': True,
            'document_id': str(processed_doc.id),
            'processing_time_ms': processing_time,
            'chunk_count': len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Erro processando documento {document_link_id}: {str(e)}")
        
        # Atualizar status de erro
        if document_link:
            document_link.status = "failed"
            document_link.error_message = str(e)
            db.commit()
        
        log_processing_step(db, document_link_id, "processing_failed", "error", str(e))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {self.request.id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        db.close()

async def download_document_step(document_link: DocumentLink) -> Dict[str, Any]:
    """Step de download do documento"""
    processor = DocumentProcessor()
    storage = StorageService()
    
    # Criar diretório temporário
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Download
        download_result = await processor.download_document(document_link.url, temp_dir)
        
        if download_result['success']:
            # Upload para storage permanente
            storage_path = await storage.upload_file(
                download_result['file_path'],
                f"documents/{document_link.id}/original"
            )
            
            download_result['storage_path'] = storage_path
        
        return download_result
        
    finally:
        # Limpar arquivos temporários
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

async def extract_content_step(file_path: str) -> Dict[str, Any]:
    """Step de extração de conteúdo com Docling"""
    processor = DocumentProcessor()
    return await processor.process_with_docling(file_path)

def create_chunks_step(text_content: str) -> List[Dict[str, Any]]:
    """Step de criação de chunks"""
    from app.core.config import settings
    processor = DocumentProcessor()
    return processor.create_chunks(
        text_content, 
        chunk_size=settings.CHUNK_SIZE,
        overlap=settings.CHUNK_OVERLAP
    )

def save_processed_document(db, document_link, download_result, extraction_result, chunks):
    """Salvar documento processado no banco"""
    processed_doc = ProcessedDocument(
        document_link_id=document_link.id,
        original_path=download_result.get('storage_path'),
        text_content=extraction_result['text_content'],
        chunk_count=len(chunks),
        docling_metadata=extraction_result.get('metadata', {})
    )
    
    db.add(processed_doc)
    db.flush()  # Para obter o ID
    
    # Salvar chunks
    from app.models import DocumentChunk
    for chunk in chunks:
        db_chunk = DocumentChunk(
            document_id=processed_doc.id,
            chunk_index=chunk['index'],
            content=chunk['content'],
            token_count=chunk['token_count'],
            metadata=chunk
        )
        db.add(db_chunk)
    
    db.commit()
    return processed_doc

def log_processing_step(db, document_link_id, step, status, message):
    """Registrar log de processamento"""
    log_entry = ProcessingLog(
        document_link_id=document_link_id,
        step=step,
        status=status,
        message=message
    )
    db.add(log_entry)
    db.commit()
```

### 3. Task de Geração de Embeddings (app/tasks/embedding_generation.py)
```python
import time
from typing import List, Dict, Any
from celery.utils.log import get_task_logger
from sentence_transformers import SentenceTransformer

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models import ProcessedDocument, DocumentChunk
from app.tasks.vector_indexing import index_embeddings_task

logger = get_task_logger(__name__)

# Cache global do modelo de embedding
_embedding_model = None

def get_embedding_model():
    """Lazy loading do modelo de embedding"""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Carregando modelo de embedding: {settings.EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model

@celery_app.task(bind=True)
def generate_embeddings_task(self, processed_document_id: str) -> Dict[str, Any]:
    """
    Gerar embeddings para os chunks de um documento
    """
    start_time = time.time()
    db = SessionLocal()
    
    try:
        # Buscar documento processado
        processed_doc = db.query(ProcessedDocument).filter(
            ProcessedDocument.id == processed_document_id
        ).first()
        
        if not processed_doc:
            raise ValueError(f"Processed document {processed_document_id} not found")
        
        # Buscar chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == processed_document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        if not chunks:
            raise ValueError(f"No chunks found for document {processed_document_id}")
        
        logger.info(f"Gerando embeddings para {len(chunks)} chunks")
        
        # Preparar textos para embedding
        texts = [chunk.content for chunk in chunks]
        
        # Gerar embeddings em lotes
        model = get_embedding_model()
        embeddings = generate_embeddings_batch(model, texts)
        
        # Preparar dados para indexação
        embedding_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_data.append({
                'chunk_id': str(chunk.id),
                'document_id': processed_document_id,
                'document_link_id': str(processed_doc.document_link_id),
                'chunk_index': chunk.chunk_index,
                'content': chunk.content,
                'embedding': embedding.tolist(),
                'metadata': {
                    'token_count': chunk.token_count,
                    'chunk_metadata': chunk.metadata
                }
            })
            
            # Atualizar progresso
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': len(chunks),
                    'step': 'generating_embeddings'
                }
            )
        
        # Iniciar indexação no vector database
        index_embeddings_task.delay(embedding_data)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Embeddings gerados em {processing_time}ms")
        
        return {
            'success': True,
            'embeddings_count': len(embeddings),
            'processing_time_ms': processing_time
        }
        
    except Exception as e:
        logger.error(f"Erro gerando embeddings para documento {processed_document_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        db.close()

def generate_embeddings_batch(model: SentenceTransformer, texts: List[str], batch_size: int = 32) -> List:
    """
    Gerar embeddings em lotes para otimizar performance
    """
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch_texts, convert_to_tensor=False)
        embeddings.extend(batch_embeddings)
    
    return embeddings

@celery_app.task
def update_embeddings_task(document_link_id: str) -> Dict[str, Any]:
    """
    Atualizar embeddings de um documento (reprocessamento)
    """
    db = SessionLocal()
    
    try:
        # Buscar documento processado
        processed_doc = db.query(ProcessedDocument).join(
            ProcessedDocument.document_link
        ).filter(
            ProcessedDocument.document_link_id == document_link_id
        ).first()
        
        if processed_doc:
            return generate_embeddings_task(str(processed_doc.id))
        else:
            return {'success': False, 'error': 'Document not found'}
    
    finally:
        db.close()
```

### 4. Task de Indexação Vetorial (app/tasks/vector_indexing.py)
```python
import time
from typing import List, Dict, Any
from celery.utils.log import get_task_logger
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import DocumentChunk

logger = get_task_logger(__name__)

# Cache global do cliente Qdrant
_qdrant_client = None

def get_qdrant_client():
    """Lazy loading do cliente Qdrant"""
    global _qdrant_client
    if _qdrant_client is None:
        logger.info(f"Conectando ao Qdrant: {settings.QDRANT_URL}")
        _qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        
        # Garantir que a coleção existe
        ensure_collection_exists()
    
    return _qdrant_client

def ensure_collection_exists():
    """Garantir que a coleção do Qdrant existe"""
    client = get_qdrant_client()
    
    try:
        # Verificar se coleção existe
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if settings.QDRANT_COLLECTION not in collection_names:
            logger.info(f"Criando coleção {settings.QDRANT_COLLECTION}")
            
            # Criar coleção (assumindo embedding de 384 dimensões para all-MiniLM-L6-v2)
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=384,  # Ajustar conforme modelo usado
                    distance=Distance.COSINE
                )
            )
    
    except Exception as e:
        logger.error(f"Erro verificando/criando coleção: {str(e)}")
        raise

@celery_app.task(bind=True)
def index_embeddings_task(self, embedding_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Indexar embeddings no vector database
    """
    start_time = time.time()
    db = SessionLocal()
    
    try:
        client = get_qdrant_client()
        
        # Preparar pontos para indexação
        points = []
        for i, data in enumerate(embedding_data):
            point = PointStruct(
                id=data['chunk_id'],
                vector=data['embedding'],
                payload={
                    'document_id': data['document_id'],
                    'document_link_id': data['document_link_id'],
                    'chunk_index': data['chunk_index'],
                    'content': data['content'],
                    'metadata': data['metadata']
                }
            )
            points.append(point)
            
            # Atualizar progresso
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': len(embedding_data),
                    'step': 'indexing_vectors'
                }
            )
        
        # Indexar no Qdrant
        operation_info = client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points
        )
        
        # Atualizar embedding_id nos chunks do banco
        for data in embedding_data:
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.id == data['chunk_id']
            ).first()
            if chunk:
                chunk.embedding_id = data['chunk_id']
        
        db.commit()
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Indexados {len(points)} embeddings em {processing_time}ms")
        
        return {
            'success': True,
            'indexed_count': len(points),
            'processing_time_ms': processing_time,
            'operation_id': operation_info.operation_id if operation_info else None
        }
        
    except Exception as e:
        logger.error(f"Erro indexando embeddings: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        db.close()

@celery_app.task
def delete_document_embeddings_task(document_link_id: str) -> Dict[str, Any]:
    """
    Remover embeddings de um documento do vector database
    """
    try:
        client = get_qdrant_client()
        
        # Buscar e deletar pontos por document_link_id
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector={
                "filter": {
                    "must": [
                        {
                            "key": "document_link_id",
                            "match": {
                                "value": document_link_id
                            }
                        }
                    ]
                }
            }
        )
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Erro removendo embeddings do documento {document_link_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task
def search_similar_documents_task(query_embedding: List[float], limit: int = 10) -> Dict[str, Any]:
    """
    Buscar documentos similares no vector database
    """
    try:
        client = get_qdrant_client()
        
        search_result = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )
        
        results = []
        for hit in search_result:
            results.append({
                'id': hit.id,
                'score': hit.score,
                'payload': hit.payload
            })
        
        return {
            'success': True,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Erro na busca de similaridade: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
```

### 5. Monitoramento com Flower

Para monitorar as tasks do Celery, configure o Flower:

```bash
# Instalar Flower
pip install flower

# Executar Flower
celery -A app.core.celery_app flower --port=5555

# Acessar dashboard em http://localhost:5555
```

### 6. Comandos para Executar Workers

```bash
# Worker principal (todas as queues)
celery -A app.core.celery_app worker --loglevel=info

# Workers especializados
celery -A app.core.celery_app worker --loglevel=info -Q document_processing
celery -A app.core.celery_app worker --loglevel=info -Q embedding_generation
celery -A app.core.celery_app worker --loglevel=info -Q vector_indexing

# Beat scheduler (para tasks periódicas)
celery -A app.core.celery_app beat --loglevel=info
```

Esta implementação fornece um sistema robusto de processamento assíncrono de documentos com monitoramento, retry logic e logging detalhado.
