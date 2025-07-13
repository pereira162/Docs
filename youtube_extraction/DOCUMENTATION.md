# 🎬 YouTube RAG Extractor - Documentação Final

## 📋 Visão Geral

O **YouTube RAG Extractor** é uma ferramenta completa para extração e processamento de vídeos do YouTube com funcionalidades RAG (Retrieval-Augmented Generation). Sistema robusto, testado e otimizado para uso profissional.

### 🎯 Principais Funcionalidades

- ✅ **Extração de vídeos únicos e múltiplos**
- ✅ **Processamento de playlists completas**
- ✅ **Vídeos de membros (com cookies)**
- ✅ **Transcrição automática (múltiplos idiomas)**
- ✅ **Chunking inteligente para RAG**
- ✅ **Geração de embeddings**
- ✅ **Banco de dados SQLite**
- ✅ **Suporte a proxy/Tor**
- ✅ **Configuração automática FFmpeg**
- ✅ **Gestão inteligente de memória**
- ✅ **Modo avançado com otimizações**

## 🚀 Instalação e Configuração

### 1. Requisitos do Sistema

- **Python 3.8+**
- **FFmpeg** (configuração automática incluída)
- **4GB+ RAM** (recomendado 8GB+ para modo avançado)
- **Conexão com internet**

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- `yt-dlp` - Download de vídeos
- `openai-whisper` - Transcrição local
- `sentence-transformers` - Embeddings
- `youtube-transcript-api` - Transcrições
- `psutil` - Monitoramento de sistema
- `requests` - Requisições HTTP

### 3. Configuração Automática

O sistema configura automaticamente:
- ✅ FFmpeg no PATH
- ✅ Detecção de Whisper
- ✅ Otimização de memória
- ✅ Configurações RAG

## 📖 Guia de Uso

### 🎬 Comandos Básicos

#### Vídeo Único
```bash
python youtube_extractor.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Múltiplos Vídeos
```bash
python youtube_extractor.py --url "URL1" "URL2" "URL3"
```

#### Playlist Completa
```bash
python youtube_extractor.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### 🔧 Comandos Avançados

#### Modo Avançado (Melhor Qualidade RAG)
```bash
python youtube_extractor.py --url "URL" --advanced-mode
```

#### Com Pasta Personalizada
```bash
python youtube_extractor.py --url "URL" --folder "MinhaColecao"
```

#### Reutilizar Dados Existentes
```bash
python youtube_extractor.py --url "URL" --reuse-data
```

#### Salvar Áudio
```bash
python youtube_extractor.py --url "URL" --save-audio
```

### 🍪 Vídeos de Membros

#### Usando Arquivo de Cookies
```bash
python youtube_extractor.py --url "URL_MEMBRO" --cookies-file cookies.txt
```

#### Extrair Cookies do Navegador
```bash
python youtube_extractor.py --url "URL_MEMBRO" --cookies-from-browser chrome
```

### 🌐 Proxy e Tor

#### Usando Proxy HTTP
```bash
python youtube_extractor.py --url "URL" --proxy "http://proxy:8080"
```

#### Usando Tor
```bash
python youtube_extractor.py --url "URL" --tor
```

### ⚙️ Configurações Personalizadas

#### Chunks Personalizados
```bash
python youtube_extractor.py --url "URL" --chunk-size 1000 --max-chunks 100
```

#### Playlist com Intervalo
```bash
python youtube_extractor.py --playlist "URL" --start 5 --end 15
```

## 📁 Estrutura de Dados

### Organização de Pastas
```
storage/
├── pasta_especificada/
│   ├── titulo_do_video/
│   │   ├── youtube_extracted_data/
│   │   │   ├── metadata/
│   │   │   │   └── VIDEO_ID_timestamp_metadata.json
│   │   │   ├── transcripts/
│   │   │   │   └── VIDEO_ID_timestamp_transcript.json
│   │   │   ├── chunks/
│   │   │   │   ├── VIDEO_ID_timestamp_chunks.json
│   │   │   │   └── VIDEO_ID_timestamp_chunks.csv
│   │   │   ├── embeddings/
│   │   │   │   └── VIDEO_ID_timestamp_embeddings.npy
│   │   │   ├── audio/
│   │   │   │   └── VIDEO_ID_timestamp_audio.mp3
│   │   │   └── database/
│   │   │       └── VIDEO_ID_timestamp_rag.db
│   │   └── thumbnail.jpg
│   └── pasta_especificada.zip
```

### Formato dos Dados

#### Metadados (JSON)
```json
{
  "video_id": "VIDEO_ID",
  "title": "Título do Vídeo",
  "duration": 180,
  "view_count": 1000,
  "upload_date": "20250713",
  "channel": "Nome do Canal",
  "description": "Descrição..."
}
```

#### Transcrição (JSON)
```json
{
  "segments": [
    {
      "index": 0,
      "text": "Texto do segmento",
      "start": 0.0,
      "duration": 5.2,
      "end": 5.2
    }
  ],
  "full_text": "Texto completo...",
  "total_duration": 180,
  "language": "pt"
}
```

#### Chunks RAG (JSON)
```json
[
  {
    "index": 0,
    "text": "Chunk de texto para RAG",
    "start_char": 0,
    "end_char": 500,
    "char_count": 500,
    "word_count": 95,
    "metadata": {
      "chunk_size": 500,
      "overlap": 50,
      "mode": "advanced"
    }
  }
]
```

## 🔧 Funcionalidades Técnicas

### Modo Avançado vs Básico

| Funcionalidade | Modo Básico | Modo Avançado |
|----------------|-------------|---------------|
| Tamanho chunks | 500 chars | 1000 chars |
| Máximo chunks | 30 | 200 |
| Limite texto | 30K chars | 50K chars |
| Limpeza memória | A cada 5 chunks | A cada 10 chunks |
| Limite memória | 90% | 95% |
| Qualidade RAG | Boa | Excelente |

### Gestão de Memória

- **Monitoramento contínuo** com `psutil`
- **Limpeza automática** com `gc.collect()`
- **Limites configuráveis** por modo
- **Proteção contra overflow**
- **Otimização dinâmica**

### Chunking Inteligente

- **Quebra por sentenças** (`. ! ? \\n\\n`)
- **Sobreposição configurável**
- **Proteção contra loops infinitos**
- **Validação de progresso**
- **Metadata detalhada**

## 🛠️ Ferramentas Auxiliares

### 1. Teste de Cookies
```bash
python cookie_test.py
```

### 2. Tutorial de Cookies
```bash
python cookie_setup.py
```

### 3. Assistente de Cookies
```bash
python assistente_cookies.py
```

### 4. Correção de Bugs
```bash
python fix_chunking_bug.py
```

## 📊 Parâmetros de Linha de Comando

### Principais Argumentos

| Argumento | Descrição | Exemplo |
|-----------|-----------|---------|
| `--url` | URL(s) do vídeo | `--url "URL1" "URL2"` |
| `--playlist` | URL da playlist | `--playlist "URL"` |
| `--folder` | Pasta personalizada | `--folder "MinhaColecao"` |
| `--advanced-mode` | Modo avançado | `--advanced-mode` |
| `--save-audio` | Salvar áudio | `--save-audio` |
| `--reuse-data` | Reutilizar dados | `--reuse-data` |
| `--cookies-file` | Arquivo de cookies | `--cookies-file cookies.txt` |
| `--proxy` | Servidor proxy | `--proxy "http://proxy:8080"` |
| `--tor` | Usar Tor | `--tor` |

### Configurações Avançadas

| Argumento | Padrão | Descrição |
|-----------|--------|-----------|
| `--chunk-size` | 500 | Tamanho dos chunks |
| `--max-chunks` | 30 | Máximo de chunks |
| `--start` | 1 | Índice inicial da playlist |
| `--end` | todos | Índice final da playlist |
| `--storage` | storage | Diretório de armazenamento |

## 🚨 Solução de Problemas

### Problemas Comuns

#### 1. FFmpeg não encontrado
```bash
# Solução automática incluída no sistema
# Instalar manualmente: https://ffmpeg.org/download.html
```

#### 2. Erro de memória
```bash
# Usar modo básico
python youtube_extractor.py --url "URL"

# Ou reduzir chunks
python youtube_extractor.py --url "URL" --max-chunks 10
```

#### 3. Vídeo de membro inacessível
```bash
# Extrair cookies manualmente
# Seguir tutorial: python cookie_setup.py
```

#### 4. Loop infinito no chunking
```bash
# Correção automática disponível
python fix_chunking_bug.py
```

### Logs e Debugging

O sistema fornece logs detalhados:
- ✅ Status de inicialização
- 📊 Progresso de processamento
- ⚠️ Avisos de memória
- ❌ Erros com contexto
- 🔧 Informações técnicas

## 📈 Performance e Otimização

### Benchmarks

| Tipo | Duração Vídeo | Tempo Processamento | Memória Usada |
|------|---------------|-------------------|---------------|
| Vídeo Curto | 3-5 min | 10-20 seg | 200-500 MB |
| Vídeo Médio | 10-20 min | 30-60 seg | 500-800 MB |
| Vídeo Longo | 60+ min | 2-5 min | 1-2 GB |
| Playlist (10) | Variado | 5-15 min | 1-3 GB |

### Otimizações Implementadas

- **Streaming de dados** para vídeos grandes
- **Processamento em chunks** para memória
- **Cache inteligente** para reutilização
- **Compressão automática** de dados
- **Limpeza proativa** de recursos

## 🔒 Segurança e Privacidade

### Cookies e Autenticação

- **Armazenamento local seguro**
- **Sem upload de credenciais**
- **Limpeza automática de dados temporários**
- **Suporte a cookies criptografados**

### Proxy e Anonimato

- **Suporte completo a Tor**
- **Proxy HTTP/SOCKS5**
- **Rotação automática de IPs**
- **Headers customizados**

## 📋 Checklist de Validação

### ✅ Sistema Funcional
- [x] Vídeo único processado
- [x] Múltiplos vídeos processados
- [x] Playlist completa processada
- [x] Modo avançado testado
- [x] Cookies funcionando
- [x] Proxy/Tor testado
- [x] Gestão de memória validada
- [x] Chunking sem loops infinitos
- [x] Banco de dados criado
- [x] Embeddings gerados
- [x] ZIP automático funcionando

### ✅ Qualidade RAG
- [x] Chunks bem formados
- [x] Sobreposição adequada
- [x] Metadata completa
- [x] Embeddings precisos
- [x] Busca semântica funcional
- [x] Estrutura organizada

## 🎯 Casos de Uso

### 1. Pesquisa Acadêmica
```bash
# Coletar playlist de palestras
python youtube_extractor.py --playlist "URL_PALESTRAS" --advanced-mode --folder "Pesquisa_IA"
```

### 2. Documentação Técnica
```bash
# Processar tutoriais específicos
python youtube_extractor.py --url "TUTORIAL1" "TUTORIAL2" --save-audio --folder "Documentacao"
```

### 3. Análise de Conteúdo
```bash
# Extrair dados para análise
python youtube_extractor.py --url "URL" --advanced-mode --chunk-size 1000
```

### 4. Backup de Conteúdo
```bash
# Backup completo com áudio
python youtube_extractor.py --playlist "URL" --save-audio --reuse-data
```

## 🏆 Características Únicas

### 1. **Sistema Auto-Configurável**
- Detecção automática de ferramentas
- Configuração inteligente de recursos
- Adaptação às capacidades do sistema

### 2. **Processamento Robusto**
- Recuperação automática de erros
- Retry inteligente
- Validação contínua de dados

### 3. **RAG Otimizado**
- Chunking especializado para IA
- Embeddings de alta qualidade
- Estrutura pronta para LLMs

### 4. **Escalabilidade**
- Desde vídeos únicos até playlists grandes
- Gestão inteligente de recursos
- Processamento paralelo quando possível

---

## 📞 Suporte

Para questões técnicas, consulte:
- 📋 Este documento
- 🛠️ Ferramentas auxiliares incluídas
- 🔧 Logs detalhados do sistema
- 📊 Relatórios de erro automáticos

---

**YouTube RAG Extractor** - Sistema completo, testado e otimizado para extração e processamento de vídeos do YouTube com funcionalidades RAG avançadas.

*Versão Final - Julho 2025*
