# Especificações Técnicas - RAG Docling System

## 1. Arquitetura do Sistema Atualizada

### 1.1 Visão Geral
```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG DOCLING SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (GitHub Pages)     │    Backend (Railway)             │
│  ┌─────────────────────────┐ │  ┌─────────────────────────────┐ │
│  │ React 18 + TypeScript   │◄─┤  │ FastAPI + Python 3.11      │ │
│  │ Vite 7 Build System     │ │  │ Docling PDF Processing     │ │
│  │ Tailwind CSS            │ │  │ Google Gemini API          │ │
│  │ Progressive Web App     │ │  │ Sentence Transformers      │ │
│  └─────────────────────────┘ │  └─────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│              Local Storage (ChromaDB + File System)             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ./data/chromadb/     │ ./data/documents/ │ ./models/        │ │
│  │ Vector Database      │ Original Files    │ ML Models Cache  │ │
│  │ Unlimited Storage    │ PDF/DOCX/etc     │ Transformers     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Fluxo de Dados
```
URL Input → Docling Processing → Text Extraction → Chunking → 
Embeddings → ChromaDB Storage → Query Processing → Gemini Response
```

## 2. Especificações de Backend

### 2.1 FastAPI Application Structure
```python
# main.py - Core application
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from docling import DocumentConverter
from docling.datamodel.base_models import InputFormat
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import asyncio
import logging
```

### 2.2 Docling Integration
```python
class DocumentProcessor:
    def __init__(self):
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=PdfPipelineOptions(
                        do_ocr=True,                    # OCR for scanned PDFs
                        do_table_structure=True,       # Extract tables
                        table_structure_options=TableStructureOptions(
                            do_cell_matching=True
                        )
                    )
                ),
                InputFormat.DOCX: DocxFormatOption(),
                InputFormat.PPTX: PptxFormatOption(),
                InputFormat.HTML: HtmlFormatOption()
            }
        )
    
    async def process_document(self, file_path: str) -> Dict:
        """Process document with Docling - supports 100MB+ files"""
        try:
            result = self.converter.convert(file_path)
            
            # Extract structured content
            text_content = result.document.export_to_markdown()
            
            # Extract metadata
            metadata = {
                "title": result.document.title,
                "page_count": len(result.document.pages),
                "tables_found": len(result.document.tables),
                "images_found": len(result.document.images),
                "processing_time": result.processing_time
            }
            
            return {
                "text": text_content,
                "metadata": metadata,
                "structure": result.document.structure
            }
        except Exception as e:
            raise HTTPException(status_code=500, f"Document processing failed: {str(e)}")
```

### 2.3 ChromaDB Local Storage
```python
class VectorStorage:
    def __init__(self, data_path: str = "./data/chromadb"):
        self.client = chromadb.PersistentClient(
            path=data_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_document_chunks(self, chunks: List[str], metadata: List[Dict], doc_id: str):
        """Add document chunks to vector database"""
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadata,
            ids=chunk_ids
        )
    
    async def similarity_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar chunks"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "content": doc,
                "metadata": meta,
                "score": 1.0 - dist  # Convert distance to similarity score
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )
        ]
```

### 2.4 Google Gemini Integration
```python
class GeminiLLM:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')
        
        # Configure safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    async def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using Gemini with context"""
        # Prepare context
        context = "\n\n".join([f"Documento {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Create prompt
        prompt = f"""Com base nos documentos fornecidos, responda à seguinte pergunta de forma clara e detalhada:

PERGUNTA: {query}

CONTEXTO DOS DOCUMENTOS:
{context}

INSTRUÇÕES:
1. Use apenas informações dos documentos fornecidos
2. Responda em português
3. Seja específico e cite os documentos quando relevante
4. Se não houver informação suficiente, indique claramente

RESPOSTA:"""

        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            # Fallback to simple concatenation
            return f"Com base nos documentos fornecidos: {' '.join(context_chunks[:500])}"
```

## 3. Especificações de Frontend

### 3.1 React Application Structure
```typescript
// App.tsx - Main application component
import React, { useState, useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { DocumentProvider } from './contexts/DocumentContext';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';
import { DocumentUpload } from './components/DocumentUpload';
import { QueryInterface } from './components/QueryInterface';

interface AppState {
  isAuthenticated: boolean;
  currentView: 'dashboard' | 'upload' | 'query';
  documents: Document[];
  loading: boolean;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    isAuthenticated: false,
    currentView: 'dashboard',
    documents: [],
    loading: false
  });

  return (
    <AuthProvider>
      <DocumentProvider>
        <div className="min-h-screen bg-gray-50">
          {!state.isAuthenticated ? (
            <LoginForm onLogin={() => setState(prev => ({ ...prev, isAuthenticated: true }))} />
          ) : (
            <MainInterface state={state} setState={setState} />
          )}
        </div>
      </DocumentProvider>
    </AuthProvider>
  );
};
```

### 3.2 Document Upload Component
```typescript
// components/DocumentUpload.tsx
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface DocumentUploadProps {
  onDocumentAdded: (document: Document) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onDocumentAdded }) => {
  const [uploadState, setUploadState] = useState<{
    status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
    progress: number;
    message: string;
  }>({
    status: 'idle',
    progress: 0,
    message: ''
  });

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      await processFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/html': ['.html'],
      'text/plain': ['.txt']
    },
    maxSize: 100 * 1024 * 1024, // 100MB limit
    multiple: true
  });

  const processFile = async (file: File) => {
    setUploadState({ status: 'uploading', progress: 0, message: 'Uploading file...' });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);

    try {
      const response = await fetch('/api/add-document', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');

      const result = await response.json();
      setUploadState({ 
        status: 'success', 
        progress: 100, 
        message: `Document processed: ${result.chunks_created} chunks created` 
      });
      
      onDocumentAdded(result.document);
    } catch (error) {
      setUploadState({ 
        status: 'error', 
        progress: 0, 
        message: `Error: ${error.message}` 
      });
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Add Documents</h2>
      
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div className="text-lg">
            {isDragActive ? (
              <p>Drop files here...</p>
            ) : (
              <p>Drag & drop files here, or <span className="text-blue-600">click to select</span></p>
            )}
          </div>
          <p className="text-sm text-gray-500">
            Supports PDF, DOCX, PPTX, HTML, TXT (up to 100MB each)
          </p>
        </div>
      </div>

      {uploadState.status !== 'idle' && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">{uploadState.message}</span>
            <span className="text-sm text-gray-600">{uploadState.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                uploadState.status === 'error' ? 'bg-red-500' : 
                uploadState.status === 'success' ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${uploadState.progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
```

### 3.3 Query Interface Component
```typescript
// components/QueryInterface.tsx
import React, { useState } from 'react';

interface QueryResult {
  content: string;
  metadata: {
    document: string;
    page?: number;
    source?: string;
  };
  score: number;
}

export const QueryInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{
    answer: string;
    sources: QueryResult[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [maxResults, setMaxResults] = useState(5);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          query: query.trim(),
          max_results: maxResults
        })
      });

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search error:', error);
      // Handle error state
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Ask Questions</h2>
      
      <div className="space-y-4">
        <div className="flex space-x-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your documents..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          
          <select
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          >
            {[3, 5, 7, 10].map(num => (
              <option key={num} value={num}>{num} results</option>
            ))}
          </select>
          
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {results && (
          <div className="space-y-6">
            {/* AI Generated Answer */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2">AI Response</h3>
              <div className="text-gray-700 whitespace-pre-wrap">{results.answer}</div>
            </div>

            {/* Source Documents */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3">Source Documents</h3>
              <div className="space-y-3">
                {results.sources.map((result, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-blue-600">
                        {result.metadata.document}
                      </span>
                      <span className="text-sm text-gray-500">
                        Relevance: {(result.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm">{result.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

## 4. Vite Configuration for GitHub Pages

### 4.1 vite.config.ts
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  
  // GitHub Pages configuration
  base: process.env.NODE_ENV === 'production' ? '/rag-docling-system/' : '/',
  
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react']
        }
      }
    }
  },

  // Environment variables
  define: {
    __API_URL__: JSON.stringify(
      process.env.NODE_ENV === 'production' 
        ? 'https://rag-docling-backend.railway.app'
        : 'http://localhost:8000'
    )
  },

  // Development server
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
## 5. Storage Architecture (Local)

### 5.1 Directory Structure
```
projeto/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── .env                   # Environment variables
│   └── data/                  # Local storage
│       ├── documents/         # Original files (PDF, DOCX, etc.)
│       ├── chromadb/         # Vector database files
│       │   ├── chroma.sqlite3 # SQLite metadata
│       │   └── index/         # HNSW index files
│       └── cache/            # Processing cache
├── frontend/
│   ├── src/                  # React source code
│   ├── dist/                 # Built files for deployment
│   ├── package.json          # Node.js dependencies
│   └── vite.config.ts        # Build configuration
└── models/                   # ML models cache
    ├── sentence-transformers/ # Embedding models
    └── tokenizers/           # Tokenizer cache
```

### 5.2 ChromaDB Configuration
```python
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class ChromaDBManager:
    def __init__(self, persist_directory: str = "./data/chromadb"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                persist_directory=persist_directory
            )
        )
        
        # Sentence transformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu"
        )
        
    def create_collection(self, name: str = "documents"):
        """Create or get collection for documents"""
        try:
            collection = self.client.get_collection(name)
        except ValueError:
            collection = self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16
                }
            )
        return collection
    
    def get_stats(self):
        """Get database statistics"""
        collections = self.client.list_collections()
        total_documents = sum(col.count() for col in collections)
        
        return {
            "collections": len(collections),
            "total_documents": total_documents,
            "storage_path": self.client._settings.persist_directory
        }
```

### 5.3 File Management
```python
import os
import shutil
from pathlib import Path
from typing import Dict, List
import hashlib

class FileManager:
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.documents_path = self.base_path / "documents"
        self.cache_path = self.base_path / "cache"
        
        # Create directories if they don't exist
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
    
    def save_document(self, file_content: bytes, filename: str) -> str:
        """Save document and return path"""
        # Generate unique filename using hash
        file_hash = hashlib.md5(file_content).hexdigest()
        file_extension = Path(filename).suffix
        unique_filename = f"{file_hash}{file_extension}"
        
        file_path = self.documents_path / unique_filename
        
        # Save file if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'wb') as f:
                f.write(file_content)
        
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get file information"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "extension": path.suffix,
            "exists": True
        }
    
    def cleanup_cache(self, max_age_days: int = 7):
        """Clean old cache files"""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        for cache_file in self.cache_path.glob("*"):
            if cache_file.stat().st_mtime < cutoff_time:
                cache_file.unlink()
    
    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "base_path": str(self.base_path)
        }
```

## 6. Chunking and Embedding Strategy

### 6.1 Advanced Text Chunking
```python
from typing import List, Dict
import re
from sentence_transformers import SentenceTransformer

class AdvancedChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.sentence_splitter = re.compile(r'[.!?]+')
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Advanced chunking with sentence boundaries"""
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for paragraph in paragraphs:
            # Check if paragraph fits in current chunk
            if current_size + len(paragraph) <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
                current_size += len(paragraph)
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append(self._create_chunk(current_chunk.strip(), metadata))
                
                # Start new chunk with overlap from previous
                if chunks:
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + paragraph + "\n\n"
                    current_size = len(current_chunk)
                else:
                    current_chunk = paragraph + "\n\n"
                    current_size = len(paragraph)
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk(current_chunk.strip(), metadata))
        
        return chunks
    
    def _create_chunk(self, text: str, metadata: Dict = None) -> Dict:
        """Create chunk with metadata"""
        return {
            "content": text,
            "char_count": len(text),
            "word_count": len(text.split()),
            "metadata": metadata or {}
        }
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.overlap:
            return text
        
        # Try to break at sentence boundary
        sentences = self.sentence_splitter.split(text)
        overlap_text = ""
        
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.overlap:
                overlap_text = sentence + overlap_text
            else:
                break
        
        return overlap_text

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            "name": self.model_name,
            "max_seq_length": self.model.max_seq_length,
            "dimension": self.model.get_sentence_embedding_dimension(),
            "device": str(self.model.device)
        }
```

## 7. API Security and Authentication

### 7.1 Simple Bearer Token Authentication
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Security scheme
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify bearer token against configured password"""
    expected_token = os.getenv("SITE_PASSWORD")
    
    if not expected_token:
        raise HTTPException(status_code=500, detail="Authentication not configured")
    
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return credentials.credentials

# Usage in endpoints
@app.post("/add-document")
async def add_document(
    document: DocumentRequest,
    token: str = Depends(verify_token)
):
    # Process document...
    pass
```

### 7.2 CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                    # Local development
        "https://usuario.github.io",               # GitHub Pages
        "https://rag-docling-system.pages.dev"     # Alternative domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### 7.3 Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limiting to endpoints
@app.post("/add-document")
@limiter.limit("5/minute")  # 5 documents per minute
async def add_document(request: Request, document: DocumentRequest):
    # Process document...
    pass

@app.post("/query")
@limiter.limit("30/minute")  # 30 queries per minute
async def query_documents(request: Request, query: QueryRequest):
    # Process query...
    pass
```

## 8. Error Handling and Logging

### 8.1 Structured Logging
```python
import logging
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory
logs_dir = Path("./logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("rag_system")

# Custom logger for document processing
doc_logger = logging.getLogger("document_processing")
doc_handler = logging.FileHandler(logs_dir / "documents.log")
doc_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
doc_logger.addHandler(doc_handler)
```

### 8.2 Error Handlers
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    error_id = str(uuid.uuid4())
    logger.error(f"Error {error_id}: {str(exc)} - {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 9. Performance Monitoring

### 9.1 Health Check Endpoint
```python
import psutil
import time
from datetime import datetime

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    start_time = time.time()
    
    # Check ChromaDB connection
    try:
        collections = vector_storage.client.list_collections()
        chromadb_status = "healthy"
        collection_count = len(collections)
    except Exception as e:
        chromadb_status = f"error: {str(e)}"
        collection_count = 0
    
    # Check Google Gemini API
    try:
        # Simple test request
        test_response = await gemini_llm.generate_response("test", ["test content"])
        gemini_status = "healthy"
    except Exception as e:
        gemini_status = f"error: {str(e)}"
    
    # System metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('./')
    
    response_time = (time.time() - start_time) * 1000  # ms
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": round(response_time, 2),
        "services": {
            "chromadb": {
                "status": chromadb_status,
                "collections": collection_count
            },
            "gemini_api": {
                "status": gemini_status
            }
        },
        "system": {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 2)
            }
        }
    }
```

### 9.2 Performance Metrics
```python
import time
from functools import wraps

def measure_time(operation_name: str):
    """Decorator to measure execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"{operation_name} completed in {execution_time:.2f}s")
            return result
        return wrapper
    return decorator

# Usage
@measure_time("Document Processing")
async def process_document(file_path: str):
    # Processing logic...
    pass

@measure_time("Vector Search")
async def search_vectors(query: str, n_results: int):
    # Search logic...
    pass
```

## 10. Development and Testing

### 10.1 Environment Configuration
```bash
# .env.example
# Copy this file to .env and fill in your values

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Authentication
SITE_PASSWORD=your_secure_password_here

# Storage paths
DATA_PATH=./data
MODELS_PATH=./models
CHROMA_DB_PATH=./data/chromadb

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Rate limiting
RATE_LIMIT_DOCUMENTS=5
RATE_LIMIT_QUERIES=30
```

### 10.2 Docker Configuration (Optional)
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/documents data/chromadb data/cache models logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 11. Production Deployment Checklist

### 11.1 Pre-deployment
- [ ] Environment variables configured
- [ ] Google Gemini API key validated
- [ ] Secure password set
- [ ] Storage paths created
- [ ] Dependencies installed
- [ ] CORS origins configured
- [ ] Rate limits set appropriately

### 11.2 Railway Deployment
- [ ] Repository connected to Railway
- [ ] Environment variables set in Railway dashboard
- [ ] Custom domain configured (optional)
- [ ] Health check endpoint responding
- [ ] Logs accessible and readable

### 11.3 GitHub Pages Deployment
- [ ] Repository configured for GitHub Pages
- [ ] GitHub Actions workflow created
- [ ] Vite build configuration updated
- [ ] API URL pointing to Railway backend
- [ ] HTTPS certificate active

### 11.4 Post-deployment Testing
- [ ] Authentication working
- [ ] Document upload successful
- [ ] PDF processing (small file < 10MB)
- [ ] PDF processing (large file > 10MB)
- [ ] Query responses with Gemini
- [ ] Error handling working
- [ ] Performance acceptable

---

**Esta especificação técnica fornece todos os detalhes necessários para implementar, deployar e manter o sistema RAG Docling com suporte a arquivos grandes e armazenamento local ilimitado.**
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
```

### 4.2 GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      pages: write
      id-token: write

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Build application
      run: |
        cd frontend
        npm run build
      env:
        NODE_ENV: production

    - name: Setup Pages
      uses: actions/configure-pages@v3

    - name: Upload artifact
      uses: actions/upload-pages-artifact@v2
      with:
        path: './frontend/dist'

    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v2
```
    processed_path TEXT,
    text_content TEXT,
    chunk_count INTEGER,
    processing_time_ms INTEGER,
    docling_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunks de texto para RAG
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES processed_documents(id),
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding_id VARCHAR(255), -- referência no vector DB
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs de processamento
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_link_id UUID REFERENCES document_links(id),
    step VARCHAR(100),
    status VARCHAR(50),
    message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. API Endpoints

### Autenticação
```
POST /auth/login
POST /auth/register
POST /auth/refresh
POST /auth/logout
```

### Gerenciamento de Links
```
GET    /api/v1/links              # Listar links
POST   /api/v1/links              # Adicionar novo link
GET    /api/v1/links/{id}         # Detalhes do link
PUT    /api/v1/links/{id}         # Atualizar link
DELETE /api/v1/links/{id}         # Remover link
POST   /api/v1/links/{id}/process # Processar manualmente
```

### Categorias
```
GET    /api/v1/categories         # Listar categorias
POST   /api/v1/categories         # Criar categoria
PUT    /api/v1/categories/{id}    # Atualizar categoria
DELETE /api/v1/categories/{id}    # Remover categoria
```

### Documentos
```
GET    /api/v1/documents          # Listar documentos processados
GET    /api/v1/documents/{id}     # Detalhes do documento
GET    /api/v1/documents/{id}/content # Conteúdo processado
GET    /api/v1/documents/{id}/chunks  # Chunks do documento
```

### RAG Query
```
POST   /api/v1/rag/query          # Consulta RAG
POST   /api/v1/rag/search         # Busca semântica
GET    /api/v1/rag/similar/{id}   # Documentos similares
```

### Monitoramento
```
GET    /api/v1/stats              # Estatísticas gerais
GET    /api/v1/health             # Health check
GET    /api/v1/logs               # Logs de sistema
```

## 3. Modelos Pydantic

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentLinkCreate(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None

class DocumentLink(BaseModel):
    id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    status: ProcessingStatus
    file_type: Optional[str]
    file_size: Optional[int]
    processed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

class RAGQuery(BaseModel):
    query: str
    max_results: int = 10
    threshold: float = 0.7
    category_filter: Optional[List[str]] = None

class RAGResponse(BaseModel):
    query: str
    results: List[dict]
    total_results: int
    processing_time: float
```

## 4. Configuração Docker

### docker-compose.yml
```yaml
version: '3.8'

services:
  # Backend API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
      - REDIS_URL=redis://redis:6379/0
      - VECTOR_DB_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - qdrant

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ragdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Qdrant Vector DB
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # Celery Worker
  worker:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  # Celery Flower (Monitoring)
  flower:
    build: ./backend
    command: celery -A app.celery flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # MinIO (S3 Compatible)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

## 5. Fluxo de Processamento

### Pipeline de Documentos
1. **Upload/Link**: Usuário adiciona URL
2. **Validação**: Verificar se URL é acessível
3. **Download**: Baixar arquivo para storage
4. **Processamento**: Usar Docling para extrair conteúdo
5. **Chunking**: Dividir texto em chunks otimizados
6. **Embedding**: Gerar embeddings dos chunks
7. **Indexação**: Armazenar no vector database
8. **Finalização**: Atualizar status e notificar usuário

### Código de Exemplo (Celery Task)
```python
from celery import Celery
import requests
from docling import DocumentProcessor

@celery.task
def process_document(document_link_id: str):
    # 1. Buscar link no banco
    link = get_document_link(document_link_id)
    
    # 2. Download do arquivo
    response = requests.get(link.url)
    file_path = save_to_storage(response.content, link.id)
    
    # 3. Processar com Docling
    processor = DocumentProcessor()
    result = processor.process(file_path)
    
    # 4. Criar chunks
    chunks = create_chunks(result.text, chunk_size=1024)
    
    # 5. Gerar embeddings
    embeddings = generate_embeddings(chunks)
    
    # 6. Armazenar no vector DB
    store_in_vector_db(chunks, embeddings, document_link_id)
    
    # 7. Atualizar status
    update_document_status(document_link_id, "completed")
```

## 6. Sistema RAG

### Configuração de Busca
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGSystem:
    def __init__(self):
        self.vector_client = QdrantClient("http://qdrant:6333")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def query(self, query: str, top_k: int = 10):
        # Gerar embedding da query
        query_embedding = self.embedder.encode([query])
        
        # Buscar no vector DB
        results = self.vector_client.search(
            collection_name="documents",
            query_vector=query_embedding[0],
            limit=top_k
        )
        
        # Recuperar contexto dos chunks
        context = self.build_context(results)
        
        return {
            "query": query,
            "context": context,
            "sources": [r.payload for r in results]
        }
```

Esta documentação fornece a base técnica completa para implementar o sistema. Agora vou usar o MCP Context7 para buscar as documentações mais atuais das tecnologias.
