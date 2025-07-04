# Stack Tecnológica Simplificada - Sistema RAG 100% Gratuito

## Arquitetura Otimizada para Zero Custo

```
Frontend (Vite+React) → Vercel (Free) → Backend (FastAPI) → Railway (Free)
                                              ↓
                        Qdrant Cloud (1GB Free) + Embeddings Locais (Free)
                                              ↓
                                    Docling + Cache Temporário
```

## 1. Frontend - Vercel Free Tier

### Vite + React + TypeScript
- **Build Tool**: Vite (30-50% mais rápido que Next.js)
- **Framework**: React 18 com TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui
- **Estado**: Zustand (2KB vs 13KB do Redux)
- **Deploy**: Vercel (100GB bandwidth, builds ilimitados)

**Recursos Gratuitos Vercel:**
- CDN global automático
- HTTPS SSL incluído
- Preview deployments
- Custom domains
- 1000 serverless functions/dia

## 2. Backend - Railway/Render Free

### FastAPI Otimizado
- **Runtime**: Python 3.11 (até 25% mais rápido)
- **Framework**: FastAPI (20x mais rápido que Flask)
- **Deploy**: Railway (512MB RAM, sleep após 30min)
- **Fallback**: Render (similar free tier)

**Free Tier Features:**
- 512MB RAM (suficiente para FastAPI + embeddings)
- Sleep mode (wake em ~2 segundos)
- PostgreSQL incluído (Railway)
- HTTPS automático

## 3. Vector Database - Qdrant Cloud Free

### Qdrant Cloud (1GB Gratuito)
- **Storage**: 1GB vetores (≈ 2.6M documentos de 384 dim)
- **API**: REST + gRPC incluído
- **Client**: qdrant-client Python oficial
- **Backup**: Snapshot automático
- **Monitoramento**: Dashboard web incluído

**Alternativas Gratuitas:**
- **ChromaDB**: 100% local, sem limites
- **Weaviate Cloud**: Free tier 10GB/mês
- **In-Memory**: Dict Python para protótipos

## 4. Embeddings - 100% Local e Gratuito

### Sentence Transformers
- **Modelo**: all-MiniLM-L6-v2 (384 dimensões)
- **Tamanho**: ~23MB download
- **Performance**: ~1000 embeddings/segundo
- **Qualidade**: 85-90% da OpenAI ada-002

**Alternativas:**
```python
# FastEmbed (Qdrant) - mais rápido
from fastembed import TextEmbedding
model = TextEmbedding()

# HuggingFace Transformers
from transformers import AutoModel, AutoTokenizer

# Ollama (local LLMs)
import ollama
ollama.embeddings(model='nomic-embed-text', prompt='text')
```

## 5. Storage - Temporário e Gratuito

### SQLite + Cache em Memória
- **Metadados**: SQLite (local no Railway)
- **Cache**: Redis local ou dict Python
- **Arquivos**: Processamento temporário (sem storage)
- **Backup**: Não necessário (dados temporários)

**Fluxo Simplificado:**
1. URL → Download temporário
2. Docling → Extração
3. Embeddings → Qdrant Cloud
4. Cleanup → Remove arquivo local

## 6. Autenticação - Senha Fixa

### Simple Auth
```python
# Sem JWT, sem banco de usuários
SITE_PASSWORD = "sua-senha-aqui"

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api"):
        auth = request.headers.get("authorization")
        if auth != f"Bearer {SITE_PASSWORD}":
            return Response("Unauthorized", status_code=401)
    return await call_next(request)
```

## 7. Deploy Gratuito - Zero Configuração

### Vercel (Frontend)
```bash
# Automatic deployment
git push origin main
# Vercel detecta Vite automaticamente
```

### Railway (Backend)
```bash
# Dockerfile simples
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

**Railway Auto-Deploy:**
- Connect GitHub repo
- Auto-detect Python
- Environment variables via UI
- Custom domain gratuito

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
