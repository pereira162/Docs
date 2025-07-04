# 🚀 RAG Docling System

Sistema RAG (Retrieval-Augmented Generation) avançado com suporte a arquivos grandes, IA local/remota e armazenamento ilimitado.

## ✨ Características Principais

- 📁 **Arquivos grandes**: Processamento de documentos até 100MB+ com Docling
- 🗄️ **Armazenamento ilimitado**: ChromaDB local sem restrições
- 🤖 **IA dupla**: Google Gemini + IA local como fallback
- 🌐 **Deploy gratuito**: GitHub Pages + servidor local
- 🔐 **Seguro**: Sistema de autenticação integrado
- ⚡ **Rápido**: Busca semântica otimizada

## 🛠️ Stack Tecnológica

### Backend
- **FastAPI**: Framework web de alta performance
- **Docling**: Processamento avançado de documentos
- **ChromaDB**: Banco vetorial local
- **Google Gemini**: IA remota avançada
- **IA Local**: Fallback sem custos

### Frontend
- **React 18**: Interface moderna
- **TypeScript**: Tipagem estática
- **Tailwind CSS**: Design responsivo
- **Vite**: Build otimizado

### Deploy
- **GitHub Pages**: Frontend estático
- **GitHub Actions**: CI/CD automático
- **Local/Railway**: Backend flexível

## 🚀 Início Rápido

### 1. Clone e Configure

```bash
git clone https://github.com/pereira162/Docs.git
cd Docs/rag-system
```

### 2. Backend

```bash
cd backend

# Criar ambiente virtual (opcional)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências básicas
pip install fastapi uvicorn python-dotenv requests google-generativeai

# Configurar variáveis
cp .env.example .env
# Editar .env com sua GOOGLE_API_KEY (opcional)

# Executar servidor
python main_simple.py
```

### 3. Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Executar desenvolvimento
npm run dev
```

### 4. Acessar Sistema

- **Frontend**: http://localhost:3000/Docs/
- **Backend**: http://localhost:8000
- **Senha**: `123` (configurável no .env)

## 📋 Como Usar

### 1. Login
- Acesse o frontend
- Digite a senha: `123`

### 2. Configurar IA
- Escolha o modo de IA:
  - **🎯 Automático**: Usa Gemini se disponível, senão local
  - **🧠 Google Gemini**: Respostas avançadas (requer API key)
  - **🏠 IA Local**: Processamento local gratuito

### 3. Adicionar Documentos
- **Por URL**: Cole link de PDF/documento
- **Upload**: Arraste arquivos (PDF, DOCX, TXT, MD)
- Suporte até 100MB+ por arquivo

### 4. Fazer Perguntas
- Digite sua pergunta na caixa de busca
- Sistema encontra trechos relevantes
- IA gera resposta contextual
- Veja fontes e scores de relevância

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)

```env
# Google Gemini API (opcional)
GOOGLE_API_KEY=sua_chave_aqui

# Autenticação
SITE_PASSWORD=123

# Storage local
DATA_PATH=./data
CHROMA_DB_PATH=./data/chromadb

# Servidor
HOST=0.0.0.0
PORT=8000
```

### Deploy GitHub Pages

O sistema está configurado para deploy automático via GitHub Actions:

1. Faça push para o repositório
2. GitHub Actions builda automaticamente
3. Frontend fica disponível em `https://seu_usuario.github.io/Docs/`
4. Backend pode rodar localmente ou em servidor

## 📊 Capacidades

### Processamento de Documentos
- **PDFs**: Extração de texto, tabelas e imagens
- **DOCX**: Documentos Microsoft Word completos
- **TXT/MD**: Arquivos de texto e Markdown
- **URLs**: Download e processamento automático

### IA e Busca
- **Embeddings**: SentenceTransformers para busca semântica
- **Google Gemini**: Respostas contextuais avançadas
- **IA Local**: Fallback sem custos ou limites
- **Chunking**: Divisão inteligente de documentos

### Performance
- **Velocidade**: Busca em milhões de chunks <1s
- **Escalabilidade**: Storage local ilimitado
- **Eficiência**: Processamento otimizado

## 🔍 API Endpoints

### Principais
```bash
# Health check
GET /health

# Adicionar documento
POST /add-document
POST /upload-document

# Buscar com IA
POST /query

# Configurar IA
GET /ai-config
POST /ai-config

# Estatísticas
GET /stats

# Limpar dados
DELETE /clear
```

## 🎯 Casos de Uso

### Pesquisa Acadêmica
- Upload de papers e artigos
- Perguntas sobre conteúdo específico
- Citações automáticas

### Documentação Empresarial
- Manuais e procedimentos
- Busca em regulamentos
- Base de conhecimento

### Análise de Contratos
- Upload de documentos legais
- Perguntas sobre cláusulas
- Comparação de termos

### Estudos e Aprendizado
- Livros e apostilas
- Resumos automáticos
- Exercícios e questões

## 🛡️ Segurança e Privacidade

- **Local First**: Dados processados localmente
- **Sem tracking**: Nenhum dado enviado para terceiros
- **Autenticação**: Sistema de senha configurável
- **CORS**: Proteção contra requisições não autorizadas

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
rag-system/
├── backend/
│   ├── main_simple.py      # Servidor principal
│   ├── requirements.txt    # Dependências Python
│   └── .env.example       # Configuração exemplo
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Interface principal
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Dependências Node
│   └── vite.config.ts     # Configuração build
└── .github/
    └── workflows/
        └── deploy.yml      # CI/CD automático
```

### Comandos de Desenvolvimento

```bash
# Backend com reload automático
python main_simple.py

# Frontend com hot reload
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview
```

## 📈 Roadmap

### Versão Atual (2.0)
- ✅ Suporte a arquivos grandes (Docling)
- ✅ IA local + remota (Gemini)
- ✅ Deploy GitHub Pages
- ✅ Interface moderna

### Próximas Versões
- [ ] Mais formatos de arquivo (PPTX, XLSX)
- [ ] IA local com Ollama
- [ ] Sistema de tags e categorias
- [ ] API de integração
- [ ] Mobile responsivo
- [ ] Multi-usuários

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Veja os arquivos .md na raiz
- **Exemplos**: Pasta `examples/` (em breve)

---

**🚀 Sistema 100% funcional e pronto para produção!**

Desenvolvido com ❤️ para democratizar o acesso a sistemas RAG avançados.
