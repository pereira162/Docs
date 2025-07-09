# 🎬 YouTube RAG Extractor - Sistema Completo

Sistema avançado para extração completa de dados RAG (Retrieval-Augmented Generation) de vídeos do YouTube, com funcionalidades de organização inteligente e processamento de playlists.

## 📁 Estrutura do Projeto

```
youtube_extraction/
├── youtube_rag_extractor_final.py  # ⭐ Script principal do sistema RAG
├── requirements.txt                # 📦 Dependências necessárias
├── README.md                      # 📖 Este arquivo de documentação
├── storage/                       # 📁 Dados extraídos organizados
└── _arquivos_teste_antigos/       # 🗃️ Arquivos de teste e desenvolvimento
```

## ✨ Funcionalidades Principais

### 🎯 Extração RAG Completa
- **Metadados**: Título, descrição, duração, visualizações, likes, dados do canal
- **Transcrições**: Extração automática em múltiplos idiomas (PT, EN, ES)
- **Análise de Conteúdo**: Keywords filtradas, sentimentos, tópicos, legibilidade
- **Chunks Inteligentes**: Segmentação otimizada para RAG (1000 chars, overlap 200)
- **Banco SQLite**: Armazenamento estruturado para consultas eficientes
- **Arquivos de Texto**: Texto puro para processamento adicional

### 🗂️ Organização Avançada
- **Nomes de 30 caracteres**: Pastas organizadas com títulos limpos
- **Subpastas de Playlist**: Organização automática por playlist
- **Pastas Personalizadas**: Escolha onde salvar vídeos individuais
- **Controle de Versão**: Evita sobrescrever dados existentes
- **ZIPs Automáticos**: Compactação individual por playlist/pasta

### 🧠 Processamento Inteligente
- **Filtro de Keywords**: Remove conectivos PT/EN automaticamente
- **Análise Multilíngue**: Detecta idioma e adapta processamento
- **Chunks Otimizados**: Quebra respeitando sentenças e parágrafos
- **Estatísticas Completas**: Métricas detalhadas de cada extração

## 🚀 Como Usar

### 📥 Instalação
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Verificar instalação
python youtube_rag_extractor_final.py --help
```

### 🎬 Extrair Vídeo Individual
```bash
# Extração básica
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# Em pasta personalizada
python youtube_rag_extractor_final.py --url "VIDEO_URL" --folder "minha_pasta"
```

### 📋 Extrair Playlist Completa
```bash
# Cria subpasta automaticamente + ZIP individual
python youtube_rag_extractor_final.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### 📊 Gerenciamento
```bash
# Listar todos os vídeos extraídos
python youtube_rag_extractor_final.py --list

# Criar ZIP de pasta específica
python youtube_rag_extractor_final.py --zip-folder "nome_da_pasta"
```

## 📂 Estrutura de Dados Extraídos

### Para cada vídeo, o sistema cria:

```
storage/
├── pasta_video_30chars/              # Nome do vídeo (30 caracteres)
│   └── youtube_extracted_data/
│       ├── metadata/                 # 📊 Metadados do vídeo
│       │   └── VIDEO_ID_timestamp_metadata.json
│       ├── transcripts/              # 📝 Transcrições completas
│       │   └── VIDEO_ID_timestamp_transcript.json
│       ├── chunks/                   # 🔗 Chunks para RAG
│       │   ├── VIDEO_ID_timestamp_chunks.json
│       │   └── VIDEO_ID_timestamp_chunks.csv
│       ├── rag_content/              # 🧠 Conteúdo processado
│       │   ├── VIDEO_ID_timestamp_text.txt
│       │   ├── VIDEO_ID_timestamp_analysis.json
│       │   ├── VIDEO_ID_timestamp_summary.json
│       │   └── VIDEO_ID_thumbnail.jpg
│       └── database/                 # 💾 Banco SQLite
│           └── youtube_transcripts.db
└── pasta_video_30chars.zip          # 📦 ZIP da pasta
```

### Para playlists:

```
storage/
└── playlist_PLAYLIST_ID/
    ├── youtube_extracted_data/       # Estrutura igual para cada vídeo
    ├── playlist_PLAYLIST_ID_report.json
    └── playlist_PLAYLIST_ID.zip      # ZIP individual da playlist
```

## 🔧 Funcionalidades Técnicas

### 🎯 Componentes RAG Extraídos
1. **Metadados**: JSON com informações completas do vídeo
2. **Transcrições**: Segmentos com timestamps e texto completo
3. **Análise**: Keywords, sentimentos, tópicos, estatísticas
4. **Chunks**: Segmentos otimizados para embeddings
5. **Texto Puro**: Arquivo txt para processamento adicional
6. **Banco SQLite**: Tabelas relacionais para consultas
7. **Thumbnail**: Imagem do vídeo

### 🔍 Filtros Inteligentes
- **Stop Words PT/EN**: Remove palavras irrelevantes
- **Conectivos**: Filtra preposições e artigos
- **Palavras Curtas**: Ignora palavras < 3 caracteres
- **Números**: Remove valores numéricos isolados

### 📊 Análises Disponíveis
- **Estatísticas**: Caracteres, palavras, sentenças, duração
- **Legibilidade**: Score de facilidade de leitura
- **Sentimentos**: Positivo, negativo, neutro
- **Tópicos**: Detecção automática de categorias
- **Keywords**: Top 10 palavras relevantes filtradas

## 📝 Estrutura do Banco de Dados

### Tabelas criadas:
- **video_metadata**: Informações gerais do vídeo
- **transcript_segments**: Segmentos de transcrição com timestamps
- **content_chunks**: Chunks para RAG com posições
- **content_analysis**: Análises e estatísticas processadas

## 🎛️ Opções de Configuração

### Parâmetros disponíveis:
- `--url`: URL de vídeo individual
- `--playlist`: URL de playlist completa
- `--folder`: Pasta personalizada para vídeo
- `--storage`: Diretório de armazenamento (padrão: storage)
- `--list`: Listar extrações realizadas
- `--zip-folder`: Criar ZIP de pasta específica

## 🔍 Exemplos de Uso Avançado

### Extração com organização:
```bash
# Vídeo em pasta específica
python youtube_rag_extractor_final.py --url "VIDEO_URL" --folder "curso_python"

# Playlist educacional
python youtube_rag_extractor_final.py --playlist "PLAYLIST_URL"

# Listar e revisar extrações
python youtube_rag_extractor_final.py --list
```

### Processamento em lote:
```bash
# Múltiplas playlists (executar separadamente)
python youtube_rag_extractor_final.py --playlist "PLAYLIST1_URL"
python youtube_rag_extractor_final.py --playlist "PLAYLIST2_URL"
```

## ⚡ Performance e Limitações

### 🟢 Otimizações:
- Chunks inteligentes respeitando sentenças
- Filtros de keywords multilíngues
- Controle de versão automático
- Compressão ZIP eficiente
- Cache de metadados

### ⚠️ Limitações:
- Vídeos sem transcrição disponível
- Limites de API do YouTube
- Dependente de conectividade de rede
- Processamento sequencial (não paralelo)

## 🛠️ Dependências

```
yt-dlp>=2023.1.6          # Extração de metadados YouTube
youtube-transcript-api>=0.6.0  # Transcrições automáticas
requests>=2.28.0          # Requisições HTTP
beautifulsoup4>=4.11.0    # Parsing HTML
pandas>=1.5.0             # Manipulação de dados
textstat>=0.7.3           # Análise de legibilidade
nltk>=3.8.1               # Processamento de linguagem natural
```

## 📈 Versão e Atualizações

**Versão Atual**: 3.0.0 (Sistema RAG Completo)

### Funcionalidades implementadas:
- ✅ Extração RAG completa (7 componentes)
- ✅ Organização inteligente com nomes de 30 caracteres
- ✅ Subpastas automáticas para playlists
- ✅ Pastas personalizadas para vídeos individuais
- ✅ ZIPs individuais por playlist/pasta
- ✅ Filtro inteligente de keywords PT/EN
- ✅ Banco SQLite com estrutura relacional
- ✅ Interface CLI avançada
- ✅ Controle de versão automático
- ✅ Relatórios detalhados

## 🎯 Sistema RAG Pronto

Este sistema está **totalmente pronto** para uso em aplicações RAG, fornecendo:
- Chunks otimizados para embeddings
- Metadados estruturados para filtragem
- Texto limpo para processamento
- Banco relacional para consultas complexas
- Análises semânticas pré-processadas

**Ideal para**: Chatbots, sistemas de busca semântica, análise de conteúdo, documentação automática, e qualquer aplicação que necessite de dados estruturados de vídeos do YouTube.
