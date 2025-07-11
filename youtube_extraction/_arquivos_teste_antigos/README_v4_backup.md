# 🎬 YouTube RAG Extractor - Sistema Completo com Controle de Memória

Sistema avançado para extração completa de dados RAG (Retrieval-Augmented Generation) de vídeos do YouTube, com funcionalidades de organização inteligente, processamento de playlists com controle de memória e prevenção de crashes.

## 🔧 Melhorias Recentes (v4.0)

### 🛡️ **Controle Anti-Crash Implementado**
- **Controle rigoroso de memória** durante processamento
- **Prevenção de shutdowns forçados** do sistema
- **Monitoramento em tempo real** com psutil
- **Limpeza automática de memória** entre vídeos
- **Limitação inteligente** de chunks e análises

### 🎯 **Processamento de Playlists Aprimorado**
- **Nomes reais de playlists** extraídos automaticamente
- **Versionamento automático** (v1, v2, v3...) 
- **Seleção de range** (--start X --end Y)
- **Pastas individuais** para cada vídeo da playlist
- **Estrutura idêntica** entre vídeo individual e playlist

### 🚀 **Whisper AI + Audio Download**
- **Transcrição local** com Whisper para vídeos sem legenda
- **Download de áudio** quando necessário
- **Controle de memória** específico para Whisper
- **Fallback inteligente** entre métodos

## 📁 Estrutura do Projeto

```
youtube_extraction/
├── youtube_rag_extractor_final.py  # ⭐ Script principal do sistema RAG
├── iniciar_sistema.bat            # 🚀 Launcher com exemplos de comandos
├── proxy_tester.py                # 🔗 Testador de proxy/Tor
├── requirements.txt               # 📦 Dependências necessárias
├── README.md                     # 📖 Este arquivo de documentação
├── storage/                      # 📁 Dados extraídos organizados
└── _arquivos_teste_antigos/      # 🗃️ Arquivos de desenvolvimento antigos
```

## ✨ Funcionalidades Principais

### 🎯 Extração RAG Completa
- **Metadados**: Título, descrição, duração, visualizações, likes, dados do canal
- **Transcrições**: Extração automática em múltiplos idiomas (PT, EN, ES) + Whisper AI
- **Análise de Conteúdo**: Keywords filtradas, sentimentos, tópicos, legibilidade
- **Chunks Inteligentes**: Segmentação otimizada com controle de memória (500 chars, overlap 100)
- **Banco SQLite**: Armazenamento estruturado para consultas eficientes
- **Arquivos de Texto**: Texto puro para processamento adicional

### 🗂️ Organização Avançada
- **Nomes de 30 caracteres**: Pastas organizadas com títulos limpos
- **Nomes reais de playlists**: Extração automática do nome verdadeiro
- **Subpastas de Playlist**: Organização automática por playlist com versionamento
- **Pastas Personalizadas**: Escolha onde salvar vídeos individuais via input interativo
- **Controle de Versão**: Evita sobrescrever dados existentes (v1, v2, v3...)
- **ZIPs Automáticos**: Compactação individual por playlist/pasta

### 🧠 Processamento Inteligente
- **Controle de Memória**: Monitoramento ativo para evitar crashes
- **Seleção de Range**: Processar apenas vídeos específicos (--start X --end Y)
- **Filtro de Keywords**: Remove conectivos PT/EN automaticamente
- **Análise Multilíngue**: Detecta idioma e adapta processamento
- **Chunks Limitados**: Máximo 30 chunks por vídeo para estabilidade
- **Limpeza Automática**: Garbage collection entre vídeos

### 🛡️ Recursos Anti-Crash
- **Monitoramento psutil**: Verificação de memória em tempo real
- **Pausas de estabilização**: 3 segundos entre vídeos para recuperação
- **Alertas visuais**: Indicadores de % de memória usado
- **Limitação de texto**: Máximo 30KB para análise por vídeo
- **Whisper otimizado**: Controle de memória específico para IA

## 🚀 Como Usar

### 📥 Instalação
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Verificar instalação
python youtube_rag_extractor_final.py --help

# 3. Usar launcher (recomendado para Windows)
iniciar_sistema.bat
```

### 🎬 Extrair Vídeo Individual
```bash
# Extração básica (pasta personalizada via input)
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# Com Tor/proxy se necessário
python youtube_rag_extractor_final.py --url "VIDEO_URL" --use-tor
```

### 📋 Extrair Playlist Completa
```bash
# Playlist completa com nome real + versionamento automático
python youtube_rag_extractor_final.py --url "https://www.youtube.com/playlist?list=PLAYLIST_ID" --playlist

# Seleção de range (recomendado para playlists grandes)
python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --start 1 --end 5
python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --start 6 --end 10

# Com Tor se necessário
python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --use-tor
```

### � Gerenciamento Avançado
```bash
# Listar todos os vídeos extraídos
python youtube_rag_extractor_final.py --list

# Criar ZIP de pasta específica
python youtube_rag_extractor_final.py --zip-folder "nome_da_pasta"

# Testar conectividade/proxy
python proxy_tester.py
```

## 📂 Estrutura de Dados Extraídos

### Para cada vídeo (individual ou em playlist):

```
storage/
├── pasta_video_30chars/              # Nome do vídeo (30 caracteres)
│   ├── youtube_extracted_data/       # Estrutura completa RAG
│   │   ├── metadata/                 # 📊 Metadados do vídeo
│   │   │   └── VIDEO_ID_timestamp_metadata.json
│   │   ├── transcripts/              # 📝 Transcrições completas
│   │   │   └── VIDEO_ID_timestamp_transcript.json
│   │   ├── chunks/                   # 🔗 Chunks para RAG (máx 30)
│   │   │   ├── VIDEO_ID_timestamp_chunks.json
│   │   │   └── VIDEO_ID_timestamp_chunks.csv
│   │   ├── rag_content/              # 🧠 Conteúdo processado
│   │   │   ├── VIDEO_ID_timestamp_text.txt
│   │   │   ├── VIDEO_ID_timestamp_analysis.json
│   │   │   └── VIDEO_ID_analysis.json
│   │   ├── database/                 # 💾 Banco SQLite
│   │   │   └── youtube_transcripts.db
│   │   └── VIDEO_ID_thumbnail.jpg    # 🖼️ Thumbnail
│   ├── metadata.json                 # Metadados principais
│   ├── transcript_VIDEO_ID.json      # Transcrição principal
│   ├── video_database.db            # Banco individual
│   └── VIDEO_ID_thumbnail.jpg       # Thumbnail principal
└── pasta_video_30chars.zip          # 📦 ZIP da pasta
```

### Para playlists:

```
storage/
└── Nome_Real_Da_Playlist_v1/         # Nome extraído automaticamente + versão
    ├── Video1_30chars/               # Cada vídeo em pasta individual
    │   └── youtube_extracted_data/   # Estrutura completa por vídeo
    ├── Video2_30chars/
    │   └── youtube_extracted_data/
    ├── playlist_metadata.json        # Metadados da playlist
    └── Nome_Real_Da_Playlist_v1.zip # ZIP da playlist completa
```

## 🔧 Funcionalidades Técnicas

### 🎯 Componentes RAG Extraídos
1. **Metadados**: JSON com informações completas do vídeo
2. **Transcrições**: Segmentos com timestamps e texto completo (API + Whisper AI)
3. **Análise**: Keywords, sentimentos, tópicos, estatísticas (análise leve)
4. **Chunks**: Segmentos otimizados para embeddings (máximo 30 por vídeo)
5. **Texto Puro**: Arquivo txt para processamento adicional
6. **Banco SQLite**: Tabelas relacionais para consultas
7. **Thumbnail**: Imagem do vídeo

### 🛡️ Controle de Memória Anti-Crash
- **Monitoramento psutil**: Verificação de % de memória em tempo real
- **Chunks limitados**: Máximo 30 chunks de 500 chars (vs 1000 antes)
- **Texto limitado**: Máximo 30KB por análise (vs ilimitado)
- **Limpeza robusta**: Garbage collection duplo entre vídeos
- **Pausas de estabilização**: 3 segundos entre processamentos
- **Alertas visuais**: Avisos quando memória >80%, crítico >90%

### 🔍 Filtros Inteligentes
- **Stop Words PT/EN**: Remove palavras irrelevantes
- **Conectivos**: Filtra preposições e artigos
- **Palavras Curtas**: Ignora palavras < 3 caracteres
- **Números**: Remove valores numéricos isolados
- **Keywords limitadas**: Máximo 15 palavras-chave por vídeo

### 📊 Análises Otimizadas
- **Estatísticas**: Caracteres, palavras, sentenças, duração
- **Processamento leve**: Limitado a 1000 palavras e 50 sentenças
- **Keywords filtradas**: Top 15 palavras relevantes
- **Análise rápida**: Otimizada para estabilidade
- **Limpeza imediata**: Liberação de memória após cada análise

### 🎬 Processamento de Playlists
- **Nomes reais**: Extração automática do nome verdadeiro da playlist
- **Versionamento**: Criação automática de versões (v1, v2, v3...)
- **Range de seleção**: --start X --end Y para processar subset
- **Pastas individuais**: Cada vídeo em sua própria subpasta
- **Controle de memória**: Verificação antes e depois de cada vídeo
- **ZIP automático**: Compactação da playlist completa

## 📝 Estrutura do Banco de Dados

### Tabelas criadas:
- **video_metadata**: Informações gerais do vídeo
- **transcript_segments**: Segmentos de transcrição com timestamps
- **content_chunks**: Chunks para RAG com posições
- **content_analysis**: Análises e estatísticas processadas

## 🎛️ Opções de Configuração

### Parâmetros principais:
- `--url`: URL de vídeo individual ou playlist
- `--playlist`: Flag para processar como playlist
- `--start`: Número do primeiro vídeo a processar (playlists)
- `--end`: Número do último vídeo a processar (playlists)
- `--use-tor`: Usar proxy Tor para contornar bloqueios
- `--storage`: Diretório de armazenamento (padrão: storage)
- `--list`: Listar extrações realizadas
- `--zip-folder`: Criar ZIP de pasta específica

### Entrada interativa:
- **Pasta personalizada**: O sistema pergunta onde salvar vídeos individuais
- **Confirmação visual**: Mostra a pasta escolhida antes de processar

## 🔍 Exemplos de Uso Avançado

### Extração com controle de memória:
```bash
# Vídeo individual com input de pasta
python youtube_rag_extractor_final.py --url "VIDEO_URL"
# Sistema perguntará: "Deseja usar uma pasta personalizada? (Enter para padrão):"

# Playlist em lotes seguros (recomendado)
python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --start 1 --end 5
python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --start 6 --end 10

# Com Tor para contornar bloqueios
python youtube_rag_extractor_final.py --url "VIDEO_URL" --use-tor
```

### Processamento seguro de playlists grandes:
```bash
# Método recomendado: processar em pequenos lotes
for i in range(1, 25, 5):
    python youtube_rag_extractor_final.py --url "PLAYLIST_URL" --playlist --start $i --end $(($i+4))
```

### Launcher para Windows:
```batch
# Usar o arquivo iniciar_sistema.bat que contém:
# - Exemplos de comandos prontos
# - Configuração automática de PATH
# - Interface amigável para usuários
iniciar_sistema.bat
```

## ⚡ Performance e Limitações

### 🟢 Otimizações:
- **Controle de memória**: Monitoramento ativo para evitar crashes
- **Chunks limitados**: Máximo 30 chunks de 500 chars por vídeo
- **Análise leve**: Processamento otimizado para estabilidade
- **Limpeza automática**: Garbage collection entre vídeos
- **Pausas de estabilização**: Recuperação do sistema entre processamentos
- **Versionamento inteligente**: Evita sobrescrever dados existentes
- **Compressão ZIP eficiente**: Por pasta e playlist individual

### ⚠️ Limitações controladas:
- **Chunks por vídeo**: Máximo 30 (vs ilimitado antes)
- **Texto para análise**: Máximo 30KB por vídeo
- **Keywords**: Máximo 15 por vídeo (vs 50 antes)
- **Análise de texto**: Limitada a 1000 palavras e 50 sentenças
- **Processamento sequencial**: Não paralelo para estabilidade

### 🔧 Requisitos técnicos:
- **Memória RAM**: Recomendado 8GB+ para playlists grandes
- **Espaço em disco**: ~100MB por playlist de 10 vídeos
- **Conectividade**: Internet estável (Tor opcional para bloqueios)
- **Python**: 3.7+ com dependências instaladas

## 🛠️ Dependências

```
yt-dlp>=2023.1.6              # Extração de metadados YouTube
youtube-transcript-api>=0.6.0  # Transcrições automáticas
requests>=2.28.0              # Requisições HTTP
beautifulsoup4>=4.11.0        # Parsing HTML
pandas>=1.5.0                 # Manipulação de dados
textstat>=0.7.3               # Análise de legibilidade
nltk>=3.8.1                   # Processamento de linguagem natural
psutil>=7.0.0                 # Monitoramento de memória (NOVO)
openai-whisper>=20231117       # Transcrição AI local (NOVO)
ffmpeg-python>=0.2.0          # Processamento de áudio (NOVO)
PySocks>=1.7.1                # Suporte a proxy/Tor (NOVO)
```

## 📈 Versão e Atualizações

**Versão Atual**: 4.0.0 (Sistema Anti-Crash + Whisper AI)

### Funcionalidades implementadas:
- ✅ **Controle anti-crash**: Monitoramento de memória + prevenção de shutdowns
- ✅ **Whisper AI**: Transcrição local para vídeos sem legenda
- ✅ **Nomes reais de playlists**: Extração automática do nome verdadeiro
- ✅ **Versionamento**: Sistema v1, v2, v3... automático
- ✅ **Seleção de range**: --start X --end Y para playlists
- ✅ **Pastas individuais**: Cada vídeo da playlist em sua subpasta
- ✅ **Estrutura unificada**: Mesma organização entre vídeo individual e playlist
- ✅ **Suporte a Tor/proxy**: Contorno de bloqueios geográficos
- ✅ **Interface melhorada**: Input interativo para pastas personalizadas
- ✅ **Launcher Windows**: iniciar_sistema.bat com exemplos

### Melhorias de estabilidade:
- ✅ **Análise otimizada**: Processamento leve e rápido
- ✅ **Chunks controlados**: Limitação para evitar sobrecarga
- ✅ **Limpeza robusta**: Garbage collection automático
- ✅ **Monitoramento ativo**: psutil para controle de recursos
- ✅ **Pausas inteligentes**: Estabilização do sistema

## 🎯 Sistema RAG Pronto para Produção

Este sistema está **totalmente otimizado** para uso em aplicações RAG profissionais, fornecendo:

### 📊 **Dados Estruturados**
- **Chunks otimizados**: Segmentos de 500 chars para embeddings eficientes
- **Metadados completos**: Informações estruturadas para filtragem avançada  
- **Texto limpo**: Processamento pronto para análise semântica
- **Banco relacional**: SQLite para consultas complexas e rápidas
- **Análises pré-processadas**: Keywords, estatísticas e tópicos prontos

### 🛡️ **Estabilidade Garantida**
- **Zero crashes**: Sistema com controle rigoroso de memória
- **Processamento seguro**: Limitações inteligentes para estabilidade
- **Monitoramento ativo**: Verificação contínua de recursos do sistema
- **Recuperação automática**: Limpeza e pausas entre processamentos

### 🚀 **Casos de Uso Ideais**
- **Chatbots educacionais**: Base de conhecimento estruturada
- **Sistemas de busca semântica**: Embeddings otimizados
- **Análise de conteúdo**: Dados pré-processados para ML
- **Documentação automática**: Metadados e análises prontas
- **Treinamento de IA**: Datasets limpos e organizados

### 🔧 **Integração Simples**
```python
# Exemplo de uso dos dados extraídos
import json
import sqlite3

# Carregar dados de um vídeo
with open('storage/Video_Name/youtube_extracted_data/chunks/chunks.json') as f:
    chunks = json.load(f)

# Conectar ao banco para consultas
conn = sqlite3.connect('storage/Video_Name/video_database.db')
cursor = conn.execute("SELECT * FROM content_chunks WHERE char_count > 100")
```

**Sistema pronto para produção com garantia de estabilidade e dados de alta qualidade!** 🎉
