# 🎬 YouTube Extraction Tool - Sistema Organizado

Esta pasta contém todas as ferramentas para extração organizada de vídeos do YouTube. Todos os scripts, dados extraídos e documentação estão organizados aqui para fácil manutenção e desenvolvimento futuro.

## 📁 Estrutura

```
youtube_extraction/
├── youtube_extractor_cli.py          # ⭐ SCRIPT PRINCIPAL - Interface de linha de comando
├── youtube_transcript_extractor.py   # Extrator de transcrições (base)
├── youtube_integration.py            # Funções de integração com YouTube
├── youtube_demo.py                   # Scripts de demonstração
├── youtube_data_manager.py           # Gerenciador de dados extraídos
├── RESUMO_YOUTUBE_RAG.py             # Resumo e utilitários para RAG
├── storage/                          # 📦 PASTA DE ARMAZENAMENTO
│   ├── Video_Title_20_chars/         # Pasta individual do vídeo
│   │   ├── VIDEO_ID_metadata.json    # Metadados do vídeo
│   │   ├── VIDEO_ID_transcript.json  # Transcrição completa
│   │   ├── VIDEO_ID_text.txt         # Texto puro
│   │   ├── VIDEO_ID_thumbnail.jpg    # Thumbnail
│   │   └── VIDEO_ID_summary.json     # Resumo da extração
│   ├── Video_Title_20_chars_v2/      # Versão 2 (se extraído novamente)
│   ├── playlist_PLAYLIST_ID_report.json # Relatório de playlist
│   └── all_extracted_videos.zip     # 📦 ZIP com TODO conteúdo
└── README_YOUTUBE_EXTRACTION.md     # Este arquivo
```

## 🚀 Como Funciona

### 📹 **Extração Individual**
- Cada vídeo é salvo em sua própria subpasta
- Nome da pasta: primeiros 20 caracteres do título do vídeo
- Se extraído novamente: adiciona `_v2`, `_v3`, etc.

### 📋 **Extração de Playlist**
- Processa todos os vídeos da playlist individualmente
- Cada vídeo ganha sua própria pasta
- Gera relatório da playlist

### 📦 **Arquivo ZIP**
- Criado/atualizado automaticamente após cada extração
- Contém TODAS as pastas e arquivos extraídos
- Localizado em: `storage/all_extracted_videos.zip`

### 🗃️ **Controle de Versão**
- Se o mesmo vídeo for extraído múltiplas vezes
- Sistema cria pastas com versões: `_v2`, `_v3`, etc.
- Conteúdo interno permanece igual

## 💻 Uso via Terminal

### 1. 📦 **Instalar Dependências**

```bash
pip install yt-dlp youtube-transcript-api requests beautifulsoup4
```

### 2. 🎬 **Extrair Vídeo Individual**

```bash
cd youtube_extraction
python youtube_extractor_cli.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 3. 📋 **Extrair Playlist Completa**

```bash
python youtube_extractor_cli.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### 4. 📹 **Listar Vídeos Extraídos**

```bash
python youtube_extractor_cli.py --list
```

### 5. 📦 **Criar/Atualizar ZIP**

```bash
python youtube_extractor_cli.py --zip
```

### 6. 📁 **Especificar Pasta de Armazenamento**

```bash
python youtube_extractor_cli.py --url "URL" --storage "minha_pasta"
```

## 📊 Saída e Arquivos Gerados

### 🎬 **Para cada vídeo:**
- `VIDEO_ID_metadata.json` - Metadados completos (título, descrição, duração, etc.)
- `VIDEO_ID_transcript.json` - Transcrição com timestamps
- `VIDEO_ID_text.txt` - Texto puro da transcrição
- `VIDEO_ID_thumbnail.jpg` - Imagem de capa
- `VIDEO_ID_summary.json` - Resumo da extração

### 📋 **Para playlists:**
- `playlist_PLAYLIST_ID_report.json` - Relatório completo da playlist

### 📦 **Arquivo ZIP:**
- `storage/all_extracted_videos.zip` - TODO conteúdo extraído

## 🔧 Descrição dos Arquivos

### ⭐ **youtube_extractor_cli.py**
- **SCRIPT PRINCIPAL** - Interface de linha de comando completa
- Extração por vídeo ou playlist
- Organização automática em subpastas
- Controle de versão
- Geração/atualização de ZIP

### 📝 **youtube_transcript_extractor.py**
- Sistema base de extração de transcrições
- Análise de conteúdo e criação de chunks para RAG
- Múltiplos formatos de saída

### 🔗 **youtube_integration.py**
- Funções de integração com APIs do YouTube
- Download de metadados e thumbnails

### 💾 **youtube_data_manager.py**
- Gerenciamento e persistência de dados
- Banco de dados SQLite
- Exportação para CSV/JSON

### 📄 **RESUMO_YOUTUBE_RAG.py**
- Resumo e funções utilitárias
- Integração com sistema RAG

### 🧪 **youtube_demo.py**
- Scripts de demonstração e exemplos

## 🧪 Testes

- Todos os arquivos de teste e saídas temporárias são movidos para:
  `_arquivos_teste_antigos/youtube_extraction/`

## 💡 Exemplos Práticos

### Extrair vídeo específico:
```bash
python youtube_extractor_cli.py -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Extrair playlist completa:
```bash
python youtube_extractor_cli.py -p "https://www.youtube.com/playlist?list=PLyLLcCaRflgCTuP493CZuUOFdMdh-a_jc"
```

### Ver todos os vídeos extraídos:
```bash
python youtube_extractor_cli.py -l
```

## ⚠️ Observações Importantes

- ✅ **Sempre verifique a pasta `storage/` para seus dados extraídos**
- ✅ **O arquivo ZIP é atualizado automaticamente após cada extração**
- ✅ **Sistema de versão previne sobrescrita de dados**
- ✅ **Cada vídeo fica em sua própria pasta organizada**
- ✅ **Relatórios de playlist mantêm histórico completo**

## 🆘 Solução de Problemas

1. **Erro de dependências**: Execute `pip install -r requirements.txt`
2. **Vídeo sem transcrição**: Sistema continuará e salvará metadados
3. **Playlist muito grande**: Sistema processa com pausas para evitar rate limiting
4. **Espaço em disco**: Monitore o tamanho da pasta `storage/`

## 📈 Próximos Passos

- Integração com sistema RAG principal
- Interface web para visualização
- Análise automática de sentimentos
- Busca avançada por conteúdo
