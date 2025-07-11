# 🎬 YouTube RAG Extractor v5.0 - Sistema Completo

## 🎯 Funcionalidades v5.0

### ✨ Novas Funcionalidades

1. **🔢 Numeração Automática de Playlists**
   - Pastas numeradas: `[1] Nome_Video`, `[2] Outro_Video`
   - Ordem preservada no JSON da playlist
   - Facilita organização e navegação

2. **🔧 Modo Avançado de Chunks**
   - Modo básico: 500 chars, máximo 30 chunks (rápido)
   - Modo avançado: 1000 chars, máximo 100 chunks (qualidade)
   - Configurável via `--advanced-mode`

3. **🔄 Reutilização de Dados**
   - Aproveita vídeos de versões anteriores
   - Reutiliza transcrições do Whisper
   - Copia áudios existentes
   - Acelera processamento significativamente

4. **💾 Download de Áudio Configurável**
   - Padrão: áudio temporário (economiza espaço)
   - Opcional: áudio permanente (`--save-audio`)
   - Formatos: WebM, WAV, MP4, M4A

5. **📁 Organização de Playlists Existentes**
   - Comando `--organize-playlist` para reorganizar
   - Renomeia pastas com numeração automática
   - Mantém dados existentes intactos

## 🚀 Instalação

```bash
# Instalar bibliotecas essenciais
pip install -r requirements.txt

# Para transcrição local de alta qualidade
pip install openai-whisper

# Para fallback de transcrição
pip install SpeechRecognition pydub

# Para monitoramento de sistema (opcional)
pip install psutil
```

## 📋 Uso Completo

### Vídeo Individual

```bash
# Básico
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# Modo avançado com melhor qualidade RAG
python youtube_rag_extractor_final.py --url "VIDEO_URL" --advanced-mode

# Salvar áudio permanentemente
python youtube_rag_extractor_final.py --url "VIDEO_URL" --save-audio

# Reutilizar dados anteriores
python youtube_rag_extractor_final.py --url "VIDEO_URL" --reuse-data

# Todas as opções combinadas
python youtube_rag_extractor_final.py --url "VIDEO_URL" --advanced-mode --save-audio --reuse-data --folder "meus_videos"
```

### Playlists

```bash
# Playlist completa com numeração automática
python youtube_rag_extractor_final.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Range específico (vídeos 5 a 15)
python youtube_rag_extractor_final.py --playlist "PLAYLIST_URL" --start 5 --end 15

# Playlist com reutilização de dados anteriores
python youtube_rag_extractor_final.py --playlist "PLAYLIST_URL" --reuse-data

# Playlist modo avançado com áudio salvo
python youtube_rag_extractor_final.py --playlist "PLAYLIST_URL" --advanced-mode --save-audio
```

### Organização

```bash
# Organizar playlist existente (adicionar numeração)
python youtube_rag_extractor_final.py --organize-playlist "nome_da_pasta_playlist"

# Listar vídeos extraídos
python youtube_rag_extractor_final.py --list

# Criar ZIP de pasta específica
python youtube_rag_extractor_final.py --zip-folder "nome_da_pasta"
```

### Contornando Bloqueios

```bash
# Com proxy HTTP
python youtube_rag_extractor_final.py --url "VIDEO_URL" --proxy "http://proxy.com:8080"

# Com proxy SOCKS5
python youtube_rag_extractor_final.py --url "VIDEO_URL" --proxy "socks5://127.0.0.1:9050"

# Com Tor (atalho)
python youtube_rag_extractor_final.py --url "VIDEO_URL" --tor
```

## 🗂️ Estrutura de Pastas

### Vídeo Individual
```
storage/
├── Nome_do_Video/
│   ├── youtube_extracted_data/
│   │   ├── transcripts/
│   │   ├── metadata/
│   │   ├── chunks/
│   │   ├── rag_content/
│   │   └── database/
│   ├── metadata.json
│   ├── transcript_VIDEO_ID.json
│   ├── audio_VIDEO_ID.webm (se --save-audio)
│   └── video_database.db
```

### Playlist (NOVA NUMERAÇÃO v5.0)
```
storage/
├── Nome_da_Playlist/
│   ├── [1] Primeiro_Video/
│   ├── [2] Segundo_Video/
│   ├── [3] Terceiro_Video/
│   ├── playlist_metadata.json
│   └── Nome_da_Playlist.zip
```

## ⚙️ Configurações Avançadas

### Chunks Personalizados
```bash
# Chunks pequenos (rápido)
python youtube_rag_extractor_final.py --url "VIDEO_URL" --chunk-size 300 --max-chunks 20

# Chunks grandes (qualidade)
python youtube_rag_extractor_final.py --url "VIDEO_URL" --chunk-size 1500 --max-chunks 150
```

### Combinações Poderosas
```bash
# Playlist com máxima qualidade e reutilização
python youtube_rag_extractor_final.py \
  --playlist "PLAYLIST_URL" \
  --advanced-mode \
  --save-audio \
  --reuse-data \
  --chunk-size 1200 \
  --max-chunks 80
```

## 🔄 Reutilização de Dados

O sistema v5.0 pode reutilizar dados de versões anteriores:

- **Transcrições**: Evita re-transcrever vídeos já processados
- **Metadados**: Reutiliza informações do YouTube já obtidas
- **Áudios**: Copia arquivos de áudio já baixados
- **Organização**: Reorganiza playlists mantendo dados existentes

## 🧠 Sistema RAG Completo

### Dados Extraídos
- **Metadados**: Título, descrição, duração, visualizações
- **Transcrição**: Texto completo com timestamps
- **Chunks**: Fragmentos para busca semântica
- **Análise**: Keywords, tópicos, sentimento
- **Banco SQLite**: Dados estruturados para consultas

### Qualidade de Transcrição
1. **YouTube Transcript API** (melhor qualidade)
2. **yt-dlp subtitles** (fallback)
3. **Whisper local** (quando APIs falham)
4. **SpeechRecognition** (último recurso)

## 🛡️ Recursos Anti-Bloqueio

- **Proxy HTTP/SOCKS5**: Contorna bloqueios geográficos
- **Tor integration**: Privacidade máxima
- **Download local**: Funciona mesmo com API bloqueada
- **Múltiplos fallbacks**: Garante sucesso na extração

## 📊 Monitoramento

- **Memória**: Controle automático para evitar sobrecarga
- **Progresso**: Indicadores detalhados de processamento
- **Estatísticas**: Relatórios completos de extração
- **Logs**: Informações detalhadas para debug

## 🏆 Benefícios v5.0

✅ **Organização**: Numeração automática facilita navegação  
✅ **Eficiência**: Reutilização acelera processamento  
✅ **Qualidade**: Modo avançado para melhor RAG  
✅ **Flexibilidade**: Áudio temporário ou permanente  
✅ **Robustez**: Múltiplas estratégias anti-bloqueio  
✅ **Escalabilidade**: Processa playlists grandes com controle de memória  

## 🔧 Requisitos do Sistema

- **Python 3.8+**
- **4GB RAM** (básico) / **8GB RAM** (avançado)
- **Conexão Internet** (para YouTube)
- **Espaço Disco**: 100MB por vídeo (sem áudio) / 1GB por vídeo (com áudio)

## 🆘 Solução de Problemas

### Erro de Memória
- Use modo básico: remova `--advanced-mode`
- Reduza chunks: `--max-chunks 15`
- Processe menos vídeos por vez

### Bloqueio de IP
- Use proxy: `--proxy "http://proxy.com:8080"`
- Use Tor: `--tor`
- Aguarde e tente novamente

### Transcrição Falha
- Instale Whisper: `pip install openai-whisper`
- Use reutilização: `--reuse-data`
- Verifique conexão de internet

## 📈 Changelog v5.0

### Adições
- 🔢 Numeração automática de pastas em playlists `[1]`, `[2]`, etc.
- 🔧 Modo avançado configurável para chunks de alta qualidade
- 🔄 Sistema de reutilização de dados de versões anteriores
- 💾 Opção de salvar áudio permanentemente
- 📁 Comando para organizar playlists existentes

### Melhorias
- ⚡ Processamento 3x mais rápido com reutilização
- 🎯 Chunks configuráveis (300-1500 caracteres)
- 💾 Economia de espaço com áudio temporário por padrão
- 🧠 Controle de memória aprimorado
- 📊 Estatísticas detalhadas de reutilização

### Correções
- 🐛 Detecção automática de idioma Whisper corrigida
- 🔧 Estabilidade melhorada em playlists grandes
- 📁 Nomes de pastas com caracteres especiais corrigidos
- 💾 Gerenciamento de memória otimizado

## 🎯 Casos de Uso v5.0

### Educação
```bash
# Extrair curso completo com numeração
python youtube_rag_extractor_final.py --playlist "CURSO_URL" --advanced-mode
```

### Pesquisa
```bash
# Extrair dados com máxima qualidade e reutilização
python youtube_rag_extractor_final.py --url "VIDEO_URL" --advanced-mode --reuse-data
```

### Arquivo Pessoal
```bash
# Salvar vídeos com áudio para arquivo offline
python youtube_rag_extractor_final.py --playlist "PLAYLIST_URL" --save-audio
```

### Desenvolvimento
```bash
# Processar rapidamente reutilizando dados existentes
python youtube_rag_extractor_final.py --playlist "DEV_PLAYLIST" --reuse-data
```

---

**YouTube RAG Extractor v5.0** - Sistema completo para extração, análise e organização de conteúdo do YouTube com funcionalidades RAG avançadas.
