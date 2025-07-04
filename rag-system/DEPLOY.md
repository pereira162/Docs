# Deploy Instructions

## ⚡ Deploy Rápido (5 minutos)

### 1. Qdrant Cloud Setup
1. Acesse: https://cloud.qdrant.io
2. Crie conta gratuita
3. Criar novo cluster (Free tier: 1GB)
4. Copiar:
   - Cluster URL (ex: `https://xyz.qdrant.tech:6333`)
   - API Key

### 2. Backend Deploy (Railway)
1. Acesse: https://railway.app
2. Conectar GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Selecionar pasta `/backend`
5. Adicionar Environment Variables:
   ```
   SITE_PASSWORD=sua_senha_aqui
   QDRANT_URL=https://xyz.qdrant.tech:6333
   QDRANT_API_KEY=sua_api_key_aqui
   PORT=8000
   ```
6. Deploy automático

### 3. Frontend Deploy (Vercel)
1. Acesse: https://vercel.com
2. "New Project"
3. Import GitHub repo
4. Root Directory: `frontend`
5. Framework: Vite
6. Environment Variables:
   ```
   VITE_API_URL=https://sua-app.railway.app
   ```
7. Deploy automático

## 🧪 Teste Local

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Editar .env com suas credenciais
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📱 Como Usar

1. **Acesso**: Abrir URL do Vercel
2. **Login**: Usar senha configurada
3. **Adicionar Documento**: 
   - Colar URL de artigo/PDF
   - Aguardar processamento
4. **Consultar**: 
   - Fazer pergunta
   - Ver resultados contextualizados

## 🎯 URLs de Teste

### Documentos para testar:
- https://docs.python.org/3/tutorial/
- https://fastapi.tiangolo.com/tutorial/
- https://react.dev/learn
- Qualquer artigo do Medium
- PDFs públicos

### Perguntas de exemplo:
- "Como criar uma função em Python?"
- "O que é FastAPI?"
- "Explique React hooks"
- "Resumo sobre IA"

## ⚠️ Limitações Free Tier

- **Railway**: 512MB RAM, sleep após inatividade
- **Qdrant Cloud**: 1GB storage
- **Vercel**: 100GB bandwidth/mês
- **Processamento**: ~50k caracteres por documento

## 🔧 Troubleshooting

### Backend não inicia:
1. Verificar variáveis ambiente
2. Testar conexão Qdrant
3. Verificar logs Railway

### Frontend erro CORS:
1. Verificar URL do backend
2. Aguardar backend acordar (Railway)
3. Limpar cache browser

### Documento não processa:
1. Verificar se URL é pública
2. Testar com URL simples primeiro
3. Verificar tamanho do documento

## 🚀 Próximos Passos

1. ✅ **MVP Funcionando**
2. 🔄 **Melhorias**:
   - Suporte PDF real (pypdf2)
   - Cache de embeddings
   - Interface melhorada
3. 📈 **Scaling**:
   - Upgrade paid tiers
   - Otimizações performance
   - Features avançadas
