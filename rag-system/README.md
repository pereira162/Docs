# 🤖 Sistema RAG - MVP Gratuito

Sistema de documentação inteligente que processa documentos via URL e responde perguntas usando IA.

## ✨ Features

- 📄 **Processamento Automático**: Adiciona documentos via URL
- 🔍 **Busca Inteligente**: Perguntas em linguagem natural
- 🆓 **100% Gratuito**: Usando tiers gratuitos
- 🔐 **Autenticação Simples**: Senha única configurável
- ⚡ **Deploy Rápido**: 5 minutos para estar online

## 🛠️ Stack Tecnológica

### Backend
- **FastAPI**: API REST rápida
- **Sentence Transformers**: Embeddings locais
- **Qdrant Cloud**: Banco vetorial (1GB grátis)
- **Railway**: Hosting backend (512MB grátis)

### Frontend
- **React + Vite**: Interface moderna
- **TypeScript**: Tipagem estática
- **Tailwind CSS**: Styling responsivo
- **Vercel**: Hosting frontend (grátis)

## 🚀 Deploy em 5 Minutos

### 1. Qdrant Cloud
```bash
1. https://cloud.qdrant.io → Criar conta
2. Novo cluster (free tier)
3. Copiar URL e API Key
```

### 2. Backend (Railway)
```bash
1. https://railway.app → Conectar GitHub
2. Deploy pasta /backend
3. Adicionar env vars:
   SITE_PASSWORD=suasenha
   QDRANT_URL=https://xyz.qdrant.tech:6333
   QDRANT_API_KEY=sua_api_key
```

### 3. Frontend (Vercel)
```bash
1. https://vercel.com → Import repo
2. Root: /frontend
3. Framework: Vite
4. Env var: VITE_API_URL=https://sua-app.railway.app
```

## 📱 Como Usar

1. **Acesso**: Abrir URL do Vercel
2. **Login**: Senha configurada no Railway
3. **Adicionar**: URLs de documentos/artigos
4. **Perguntar**: Qualquer questão sobre o conteúdo

## 🧪 Teste Local

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Editar com credenciais
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

## 📊 Exemplo de Uso

### URLs para testar:
- https://docs.python.org/3/tutorial/
- https://fastapi.tiangolo.com/
- Qualquer artigo do Medium/Blog

### Perguntas exemplo:
- "Como criar uma função em Python?"
- "O que é FastAPI?"
- "Principais conceitos sobre X?"

## ⚠️ Limitações Free Tier

- **Railway**: 512MB RAM, dorme após inatividade
- **Qdrant**: 1GB storage (~1000 documentos)
- **Processamento**: ~50k caracteres por documento
- **Resposta**: Pode levar alguns segundos

## 🔧 Estrutura do Projeto

```
rag-system/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Dependencies
│   └── .env.example        # Config template
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # React app
│   │   └── main.tsx        # Entry point
│   ├── package.json        # Dependencies
│   └── vite.config.ts      # Build config
└── DEPLOY.md               # Deploy guide
```

## 🎯 Funcionalidades Implementadas

- ✅ Extração de texto de URLs
- ✅ Chunking inteligente de documentos
- ✅ Embeddings com sentence-transformers
- ✅ Busca vetorial com Qdrant
- ✅ Interface React responsiva
- ✅ Autenticação simples
- ✅ Deploy automático

## 📈 Roadmap

### Próximas melhorias:
- 📄 Suporte real a PDFs (pypdf2)
- 🔄 Cache de embeddings
- 📊 Analytics de uso
- 🎨 Interface aprimorada
- 🔍 Busca híbrida (texto + vetor)

### Scaling futuro:
- 💰 Upgrade para tiers pagos
- 🚀 Otimizações de performance
- 🔐 Sistema de usuários
- 📱 App mobile

## 🤝 Contribuindo

1. Fork o projeto
2. Crie feature branch
3. Commit mudanças
4. Push para branch
5. Abra Pull Request

## 📝 Licença

MIT License - veja LICENSE para detalhes.

## 🆘 Suporte

- 📧 Issues no GitHub
- 📱 Documentação completa em `/docs`
- 🔧 Troubleshooting em `DEPLOY.md`

---

**🎉 Pronto para usar! Deploy em minutos, documentação inteligente em funcionamento.**
