# Stack Tecnológica Atualizada - Sistema RAG 100% Gratuito

## Arquitetura Otimizada para Zero Custo (Atualizada)

```
Frontend (Vite+React) → GitHub Pages (Free) → Backend (FastAPI) → Railway/Local
                                                     ↓
                         Qdrant Local/ChromaDB + Docling + Google Gemini API
                                                     ↓
                              Armazenamento Local (Ilimitado)
```

## 1. Frontend - GitHub Pages Free

### Vite + React + TypeScript
- **Build Tool**: Vite 7.0.0 (extremamente rápido, HMR otimizado)
- **Framework**: React 18 com TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui
- **Estado**: Zustand (2KB vs 13KB do Redux)
- **Deploy**: GitHub Pages (builds automáticos via GitHub Actions)

**Recursos Gratuitos GitHub Pages:**
- CDN global automático
- HTTPS SSL incluído
- Deploy automático com GitHub Actions
- Custom domains suportados
- Builds ilimitados
- 1GB de armazenamento
- 100GB bandwidth/mês

**Configuração do Vite para GitHub Pages:**
```javascript
// vite.config.ts
export default defineConfig({
  base: '/nome-do-repositorio/', // Para GitHub Pages
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        }
      }
    }
  }
})
```

## 2. Backend - Opções Flexíveis

### FastAPI Otimizado + Docling
- **Runtime**: Python 3.11+ (até 25% mais rápido)
- **Framework**: FastAPI (20x mais rápido que Flask)
- **Document Processing**: Docling (suporte a PDFs até 100MB+)
- **Deploy**: Railway/Render (opção cloud) ou Local (desenvolvimento)

**Principais Mudanças:**
- **Suporte a arquivos grandes**: Docling processa PDFs de até 100MB+
- **Quantidade ilimitada**: Armazenamento local sem limites de Railway
- **Processamento avançado**: Docling extrai textos, tabelas, imagens
- **Cache inteligente**: Sistema de cache para reprocessamento rápido

### Docling Integration
```python
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat

# Configuração otimizada
converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF, InputFormat.HTML, InputFormat.DOCX],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=PdfPipelineOptions(
                do_ocr=True,  # OCR para PDFs escaneados
                do_table_structure=True,  # Extrair tabelas
                table_structure_options=TableStructureOptions(
                    do_cell_matching=True
                )
            )
        )
    }
)
```

## 3. Vector Database - Soluções Locais

### ChromaDB Local (Recomendado)
- **Storage**: Ilimitado (limitado apenas pelo disco local)
- **Performance**: Excelente para até 1M+ documentos
- **Recursos**: Embeddings automáticos, metadados, filtros
- **Backup**: Controle total dos dados

### Qdrant Local (Alternativa)
- **Storage**: Ilimitado localmente
- **Performance**: Produção-ready, muito rápido
- **Recursos**: Interface web, snapshots, sharding
- **Escalabilidade**: Fácil migração para cloud depois

### Configuração ChromaDB
```python
import chromadb
from chromadb.config import Settings

# Configuração persistente local
client = chromadb.PersistentClient(
    path="./chromadb_data",
    settings=Settings(
        anonymized_telemetry=False,
        is_persistent=True
    )
)

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
)
```

## 4. IA Generativa - Google Gemini API

### Google Gemini 2.0 Flash
- **Modelo**: gemini-2.0-flash-001 (mais recente)
- **Performance**: 2x mais rápido que GPT-4
- **Custo**: $0.075 por 1M tokens (muito competitivo)
- **Contexto**: 2M tokens (documentos longos)
- **Recursos**: Multimodal (texto, imagens, PDFs)

### Integração Python
```python
from google import genai

# Configuração simples
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Geração de texto
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=[
        'Com base nos documentos fornecidos, responda: ' + query,
        *relevant_chunks
    ],
    config=genai.types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1000,
        safety_settings=[
            genai.types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            )
        ]
    )
)
```

### Alternativas de IA Gratuitas
- **Ollama Local**: Llama 3.1, Mistral 7B, Phi-3 (100% gratuito)
- **Groq**: Llama 3.1 via API (tier gratuito generoso)
- **HuggingFace**: Transformers locais (gratuito, limitado)

## 5. Embeddings - 100% Local e Gratuito

### Sentence Transformers Otimizado
- **Modelo Primary**: all-MiniLM-L6-v2 (384 dim)
- **Modelo Multilingual**: paraphrase-multilingual-MiniLM-L12-v2
- **Modelo Large**: all-mpnet-base-v2 (768 dim, maior qualidade)
- **Performance**: ~1000 embeddings/segundo (CPU)
- **Cache**: Embeddings salvos localmente

### FastEmbed (Qdrant)
```python
from fastembed import TextEmbedding

# Modelo otimizado
embedding_model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",  # SOTA
    cache_dir="./models"
)

# Embedding em batch
embeddings = embedding_model.embed(texts)
```

## 6. Storage - Local Ilimitado

### Armazenamento Local Estruturado
- **Documents**: ./data/documents/ (originais + cache)
- **Embeddings**: ChromaDB/Qdrant local
- **Models**: ./models/ (sentence-transformers cache)
- **Backup**: Git LFS para dados importantes

### Estrutura de Diretórios
```
projeto/
├── data/
│   ├── documents/          # PDFs e documentos originais
│   ├── chromadb/          # Vector database local
│   └── cache/             # Cache de processamento
├── models/                # Modelos de embedding
├── backend/               # FastAPI + Docling
└── frontend/              # React + Vite
```

## 7. Deploy Gratuito - GitHub Pages + Actions

### GitHub Actions Workflow
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install and Build
      run: |
        cd frontend
        npm ci
        npm run build
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./frontend/dist
```

### Configuração GitHub Pages
- **Source**: GitHub Actions
- **Custom Domain**: Opcional (gratuito)
- **HTTPS**: Forçado (segurança)
- **Branch Protection**: Main protegida

## 8. Limitações e Trade-offs da Nova Stack

### Armazenamento Local
**Vantagens:**
- ✅ Ilimitado (apenas limitado pelo HD)
- ✅ Sem custos de cloud storage
- ✅ Performance superior (acesso local)
- ✅ Privacidade total (dados não saem da máquina)

**Limitações:**
- ❌ Apenas single-user (não compartilhado)
- ❌ Backup manual necessário
- ❌ Não escalável para múltiplos usuários

### GitHub Pages Deploy
**Vantagens:**
- ✅ 100% gratuito (1GB storage, 100GB bandwidth/mês)
- ✅ CDN global (performance mundial)
- ✅ CI/CD automático com Actions
- ✅ Custom domain suportado

**Limitações:**
- ❌ Apenas sites estáticos
- ❌ Backend precisa ser hospedado separadamente
- ❌ Máximo 10 builds por hora

### Docling para Grandes Arquivos
**Vantagens:**
- ✅ Suporte até 100MB+ por arquivo
- ✅ OCR avançado para PDFs escaneados
- ✅ Extração de tabelas e estruturas
- ✅ Múltiplos formatos (PDF, DOCX, PPTX, HTML)

**Limitações:**
- ❌ Uso intensivo de CPU/RAM para arquivos grandes
- ❌ Processamento mais lento que text puro
- ❌ Dependências adicionais (IBM packages)

## 9. Migração da Stack Atual

### Etapas de Migração

**1. Backend - Docling Integration**
```python
# Substituir BeautifulSoup por Docling
from docling import DocumentConverter
from docling.datamodel.base_models import InputFormat

# Converter múltiplos formatos
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=PdfPipelineOptions(
                do_ocr=True,
                do_table_structure=True,
                table_structure_options=TableStructureOptions(
                    do_cell_matching=True
                )
            )
        )
    }
)

result = converter.convert("documento.pdf")
text_content = result.document.export_to_markdown()
```

**2. Vector Storage - ChromaDB Local**
```python
# Substituir Qdrant Cloud por ChromaDB local
import chromadb
from chromadb.config import Settings

# Cliente persistente local
client = chromadb.PersistentClient(
    path="./data/chromadb",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Collection para documentos
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}
)
```

**3. Frontend - GitHub Pages Config**
```typescript
// vite.config.ts - Configuração para GitHub Pages
import { defineConfig } from 'vite'

export default defineConfig({
  base: '/nome-do-repo/',  // Para GitHub Pages
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true
  },
  define: {
    __API_URL__: JSON.stringify(
      process.env.NODE_ENV === 'production' 
        ? 'https://backend-url.railway.app'
        : 'http://localhost:8000'
    )
  }
})
```

### Configuração de Environment Variables

**Backend (.env)**
```env
# Google Gemini API
GOOGLE_API_KEY=sua_api_key_aqui

# Autenticação
SITE_PASSWORD=sua_senha_segura

# Storage local
DATA_PATH=./data
MODELS_PATH=./models

# ChromaDB
CHROMA_DB_PATH=./data/chromadb

# Railway Deploy
PORT=8000
```

**Frontend (.env)**
```env
# Vite environment
VITE_API_URL=http://localhost:8000
VITE_SITE_NAME=RAG Docling System
```

## 10. Comandos e Scripts Úteis

### Desenvolvimento Local
```bash
# Backend setup e run
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python main.py

# Frontend setup e run
cd frontend
npm install
npm run dev

# Build para produção
npm run build
npm run preview
```

### GitHub Actions Setup
```bash
# Configurar repositório
git init
git remote add origin https://github.com/usuario/repo.git

# Ativar GitHub Pages
# Settings > Pages > Source: GitHub Actions

# Commit e push
git add .
git commit -m "Initial commit with new stack"
git push -u origin main
```

### Backup e Restore
```bash
# Backup dados locais
tar -czf backup_$(date +%Y%m%d).tar.gz data/ models/

# Restore dados
tar -xzf backup_20241201.tar.gz

# Git LFS para arquivos grandes (opcional)
git lfs track "*.pdf"
git lfs track "data/documents/*"
```

## 11. Performance e Otimizações

### Backend Otimizations
- **Async Processing**: FastAPI + asyncio para I/O não-bloqueante
- **Batch Embeddings**: Processar múltiplos chunks em paralelo
- **Model Caching**: Carregar modelos uma vez na inicialização
- **Compression**: gzip para responses grandes

### Frontend Optimizations
- **Vite Code Splitting**: Chunks automáticos por rota
- **Lazy Loading**: Components carregados sob demanda
- **PWA**: Service Workers para cache offline
- **Bundle Analysis**: vite-bundle-analyzer

### Storage Optimizations
- **Chunk Size**: 500-1000 tokens (balanceio performance/qualidade)
- **Index Tuning**: ChromaDB HNSW parameters
- **Compression**: LZ4 para embeddings
- **Cleanup**: Rotina de limpeza de dados antigos

## 12. Monitoramento e Debug

### Logs e Métricas
```python
# Logging estruturado
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Métricas de performance
def track_processing_time(func):
    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds()
        logging.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### Health Checks
```python
# Endpoint de saúde
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "storage": {
            "chromadb": check_chromadb_connection(),
            "disk_space": get_disk_usage()
        },
        "models": {
            "embedding_model": check_embedding_model(),
            "gemini_api": check_gemini_connection()
        }
    }
```

---

## Próximos Passos

1. **✅ Atualizar documentação completa**
2. **🔄 Modificar protótipo atual:**
   - Integrar Docling para processamento de PDFs grandes
   - Trocar Qdrant Cloud por ChromaDB local
   - Adicionar Google Gemini API para respostas
   - Configurar Vite para GitHub Pages deploy
3. **⏳ Testes locais:**
   - Testar processamento de arquivos >10MB
   - Validar storage ilimitado local
   - Confirmar deploy GitHub Pages
4. **⏳ Deploy em produção:**
   - GitHub Actions workflow
   - Railway backend update
   - Documentação final

**Esta stack mantém 100% dos custos zerados enquanto remove todas as limitações de storage e tamanho de arquivo!**
├── models/                # Modelos de embedding
├── backend/               # FastAPI + Docling
└── frontend/              # React + Vite
```

## 7. Deploy Gratuito - GitHub Pages + Actions

### GitHub Actions Workflow
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install and Build
      run: |
        cd frontend
        npm ci
        npm run build
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./frontend/dist
```

### Configuração GitHub Pages
- **Source**: GitHub Actions
- **Custom Domain**: Opcional (gratuito)
- **HTTPS**: Forçado (segurança)
- **Branch Protection**: Main protegida

## 8. Monitoramento Básico Gratuito

### Health Checks Simples
- **Uptime**: UptimeRobot (gratuito)
- **Logs**: Railway dashboard
- **Metrics**: Vercel analytics
- **Errors**: Print statements + Railway logs

## Limitações Conhecidas

### Performance
- **Cold Start**: 2-3s após sleep
- **Concurrent**: ~50 usuários simultâneos
- **Processing**: 1 documento por vez
- **Memory**: 512MB total (backend)

### Capacidade
- **Documents**: ~2.6M chunks (Qdrant 1GB)
- **Daily Requests**: ~10k (Railway free)
- **File Size**: Max 10MB por documento
- **Uptime**: 99% (com sleep mode)

## Custo Total: $0.00/mês

### Breakdown de Recursos Gratuitos
- **Vercel**: $0 (100GB bandwidth)
- **Railway**: $0 (512MB RAM, sleep mode)
- **Qdrant Cloud**: $0 (1GB storage)
- **Domain**: Subdominio gratuito (.vercel.app)
- **SSL**: Incluído em tudo
- **CDN**: Global (Vercel)

### Upgrade Path (Se Necessário)
- **Railway Pro**: $5/mês (sempre ativo)
- **Qdrant Cloud**: $25/mês (4GB)
- **Vercel Pro**: $20/mês (mais functions)
- **Custom Domain**: $10-15/ano

## Próximos Passos Implementação

1. **Setup Vite + React** (30 min)
2. **FastAPI mínimo** (45 min)
3. **Qdrant Cloud setup** (15 min)
4. **Deploy Railway** (20 min)
5. **Deploy Vercel** (10 min)
6. **Teste completo** (30 min)

**Total**: ~2.5 horas para MVP funcional
