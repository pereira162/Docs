---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

# Contexto do Projeto e Diretrizes para Assistente de IA

## Visão Geral
Este projeto nasceu de uma necessidade prática: criar um sistema online (site) para processar e consultar documentos (links de arquivos ou sites) de forma eficiente, usando técnicas de RAG (Retrieval-Augmented Generation) e IA generativa. O objetivo é permitir que qualquer pessoa possa adicionar documentos via URL e fazer perguntas sobre o conteúdo, recebendo respostas contextualizadas, sem custos e com deploy 100% online.

## Evolução da Discussão
- **Fase 1:** Inicialmente, discutimos uma arquitetura robusta (FastAPI, Next.js, PostgreSQL, Qdrant, Docker, etc.), mas percebemos que seria caro e complexo para o objetivo de uso pessoal/protótipo.
- **Fase 2:** O foco mudou para uma solução totalmente gratuita, simples e fácil de hospedar, mesmo que com limitações de armazenamento e performance.
- **Fase 3:** Documentamos toda a arquitetura, stack, fluxos e limitações, e partimos para a implementação de um MVP funcional, priorizando:
  - Deploy rápido (Railway, Vercel, Qdrant Cloud)
  - Autenticação simples (senha única)
  - Processamento temporário (sem necessidade de banco relacional)
  - Facilidade de uso e manutenção

## Stack e Arquitetura
- **Backend:** FastAPI (Python), embeddings com sentence-transformers, armazenamento vetorial no Qdrant Cloud, deploy no Railway.
- **Frontend:** React (Vite, TypeScript, Tailwind), deploy no Vercel.
- **Fluxo:**
  1. Usuário adiciona URL de documento
  2. Backend extrai texto, faz chunking e gera embeddings
  3. Chunks são armazenados no Qdrant
  4. Usuário faz perguntas; backend busca chunks relevantes e retorna para o frontend

## Limitações e Decisões
- **100% gratuito:** Todas as ferramentas em tier free (Railway, Qdrant, Vercel)
- **Sem login complexo:** Apenas senha fixa para acesso
- **Armazenamento temporário:** Não há persistência longa nem banco relacional
- **Documentação detalhada:** Todos os passos, comandos e decisões estão documentados em `README.md` e `DEPLOY.md`

## Como o Assistente de IA deve atuar
- **Seguir a arquitetura e fluxos já definidos** (não sugerir upgrades pagos ou complexidade desnecessária)
- **Priorizar simplicidade e baixo custo**
- **Respeitar as limitações dos tiers gratuitos**
- **Ajudar a evoluir o MVP de forma incremental** (ex: suporte a PDF, melhorias de UX, otimizações)
- **Referenciar sempre os arquivos principais:**
  - `backend/main.py` (API e lógica)
  - `frontend/src/App.tsx` (interface)
  - `DEPLOY.md` (deploy e troubleshooting)
  - `README.md` (visão geral e exemplos)

## Exemplos de perguntas que podem surgir
- Como adicionar um novo tipo de documento?
- Como melhorar a extração de texto?
- Como escalar para mais documentos?
- Como personalizar a interface?

## Resumo
O objetivo é manter o sistema simples, funcional e gratuito, com deploy fácil e documentação clara. O assistente de IA deve sempre contextualizar suas respostas com base nessas premissas e nos arquivos do projeto.

---

**Qualquer dúvida ou sugestão de melhoria, consulte a documentação e mantenha o foco na simplicidade e viabilidade gratuita.**


# Copilot Instructions for AI Agents

## Project Overview
- **Purpose:** RAG (Retrieval-Augmented Generation) system for processing documents via URL and answering questions using AI.
- **Architecture:**
  - **Backend:** FastAPI (Python), sentence-transformers for embeddings, Qdrant Cloud for vector storage, deployed on Railway.
  - **Frontend:** React (Vite, TypeScript, Tailwind), deployed on Vercel.
  - **Data Flow:** User submits document URL → Backend extracts & chunks text → Embeddings generated → Chunks stored in Qdrant → User queries → Backend retrieves relevant chunks → Results shown in frontend.

## Key Files & Directories
- `backend/main.py`: FastAPI app, all API endpoints, Qdrant integration, embedding logic, authentication.
- `backend/requirements.txt`: Python dependencies (FastAPI, Qdrant, sentence-transformers, etc).
- `frontend/src/App.tsx`: Main React app, handles authentication, document upload, querying, and result display.
- `frontend/package.json`: Frontend dependencies and scripts.
- `DEPLOY.md`: Step-by-step deploy and troubleshooting guide.
- `README.md`: Project summary, stack, and usage examples.

## Developer Workflows
- **Backend:**
  - Run locally: `python main.py` (after installing requirements and setting env vars)
  - Deploy: Railway (env vars: `SITE_PASSWORD`, `QDRANT_URL`, `QDRANT_API_KEY`, `PORT`)
- **Frontend:**
  - Run locally: `npm run dev` (Vite)
  - Deploy: Vercel (env var: `VITE_API_URL`)
- **Environment:**
  - All secrets/configs via environment variables (see `.env.example`)
  - Password-based auth (single password, no user accounts)

## Project-Specific Patterns & Conventions
- **Chunking:** Documents are split into ~500-word overlapping chunks before embedding.
- **Embeddings:** Uses `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors).
- **Qdrant:** Each chunk stored as a vector with metadata (content, source_url, title, chunk_index, timestamp).
- **Endpoints:**
  - `/add-document`: Add document by URL
  - `/query`: Query for relevant chunks
  - `/stats`: System stats
  - `/clear`: Clear all data (dev only)
- **Frontend:**
  - Auth state stored in `localStorage`
  - API base URL set via `VITE_API_URL` env var
  - All API calls require Bearer token (password)

## Integration Points
- **Qdrant Cloud:** External vector DB, free tier (1GB)
- **Railway:** Backend hosting, free tier (512MB RAM)
- **Vercel:** Frontend hosting

## Examples
- Add document: POST `/add-document` with `{ url, title? }` and Bearer token
- Query: POST `/query` with `{ query, max_results }` and Bearer token

## Non-Obvious Details
- **No user accounts:** Only a single password for access (set via env var)
- **Document size limit:** ~50k characters per document
- **Free tier constraints:** Backend may sleep, Qdrant storage is limited
- **PDF support:** Basic (HTML preferred); for advanced PDF, extend backend

---
For more, see `DEPLOY.md` and `README.md`. When in doubt, check `main.py` (backend) and `App.tsx` (frontend) for real usage patterns.
