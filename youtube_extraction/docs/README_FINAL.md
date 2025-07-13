# 🎬 YouTube RAG Extractor v5.0

Sistema completo para extração de vídeos do YouTube com funcionalidades RAG (Retrieval-Augmented Generation).

## 🚀 Instalação Rápida

```bash
pip install -r requirements.txt
```

## 📖 Uso Básico

### Vídeo Único
```bash
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Múltiplos Vídeos
```bash
python youtube_rag_extractor_final.py --url "URL1" "URL2" "URL3" --advanced-mode
```

### Playlist
```bash
python youtube_rag_extractor_final.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Vídeos de Membros
```bash
# 1. Extrair cookies manualmente (tutorial incluído)
python tutorial_cookies.py

# 2. Usar cookies
python youtube_rag_extractor_final.py --url "URL_MEMBRO" --cookies-file cookies.txt
```

## 🎯 Principais Funcionalidades

- ✅ **Extração completa** de vídeos e playlists
- ✅ **Transcrição automática** (múltiplos idiomas)
- ✅ **Chunking inteligente** para RAG
- ✅ **Vídeos de membros** (com cookies)
- ✅ **Modo avançado** otimizado
- ✅ **Gestão inteligente de memória**
- ✅ **Suporte a proxy/Tor**
- ✅ **Organização automática** de dados

## 📁 Estrutura de Saída

```
storage/pasta_especificada/
├── titulo_do_video/
│   ├── youtube_extracted_data/
│   │   ├── metadata/         # Informações do vídeo
│   │   ├── transcripts/      # Transcrições
│   │   ├── chunks/          # Chunks para RAG
│   │   ├── embeddings/      # Embeddings gerados
│   │   └── database/        # Banco SQLite
│   └── thumbnail.jpg
└── pasta_especificada.zip   # ZIP automático
```

## 🔧 Comandos Úteis

### Modo Avançado (Recomendado)
```bash
python youtube_rag_extractor_final.py --url "URL" --advanced-mode --save-audio
```

### Pasta Personalizada
```bash
python youtube_rag_extractor_final.py --url "URL" --folder "MinhaColecao" --advanced-mode
```

### Reutilizar Dados
```bash
python youtube_rag_extractor_final.py --url "URL" --reuse-data --advanced-mode
```

## 🛠️ Ferramentas Incluídas

- `tutorial_cookies.py` - Tutorial para cookies
- `testar_cookies.py` - Teste de cookies
- `fix_chunking_bug.py` - Correção de bugs

## 📊 Modos de Operação

| Recurso | Básico | Avançado |
|---------|--------|----------|
| Chunks | 500 chars | 1000 chars |
| Máximo | 30 chunks | 200 chunks |
| Qualidade | Boa | Excelente |

## 🚨 Solução Rápida de Problemas

### FFmpeg não encontrado
O sistema configura automaticamente. Se falhar, instale manualmente.

### Erro de memória
Use modo básico (sem `--advanced-mode`) ou reduza `--max-chunks`.

### Vídeo de membro
Execute `python tutorial_cookies.py` para instruções completas.

## 📋 Documentação Completa

Para documentação detalhada, consulte: `DOCUMENTACAO_FINAL.md`

---

**Sistema testado e validado - Pronto para uso profissional!**
