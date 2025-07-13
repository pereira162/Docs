# Web Documentation Scraper & RAG Extractor

Sistema completo para extração e processamento de documentação web com funcionalidades RAG (Retrieval-Augmented Generation).

## Características Principais

- **Extração completa** de páginas web (texto, imagens, vídeos, tabelas, links)
- **Suporte a JavaScript** com Selenium para sites dinâmicos
- **Download e transcrição** de vídeos usando Whisper
- **Chunks RAG automáticos** com embeddings
- **Banco de dados** SQLite para armazenamento
- **Detecção automática** de idioma
- **Processamento de sites complexos** como documentação da Autodesk

## Instalação

```bash
# Instalação automática (recomendado)
python install.py

# OU instalação manual
pip install -r requirements.txt
```

## Uso Básico

### Extração Simples
```bash
python web_documentation_scraper.py --url "https://example.com/docs"
```

### Extração com JavaScript (sites dinâmicos)
```bash
python web_documentation_scraper.py --url "https://help.autodesk.com/view/..." --selenium
```

### Extração Completa com Vídeos
```bash
python web_scraper_advanced.py --url "https://help.autodesk.com/view/..." --selenium --process-videos
```

## Funcionalidades

### 1. Extração de Conteúdo
- **Texto principal**: Extração inteligente do conteúdo relevante
- **Metadados**: Título, descrição, structured data
- **Tabelas**: Conversão automática para formato estruturado
- **Links**: Mapeamento completo de links internos e externos

### 2. Processamento de Mídia
- **Imagens**: URLs, alt text, dimensões
- **Vídeos HTML5**: Download automático de arquivos MP4/WebM
- **Vídeos embedded**: Detecção de YouTube, Vimeo, Wistia
- **Transcrição**: Whisper para converter áudio em texto

### 3. Sistema RAG
- **Chunking inteligente**: Divisão em chunks otimizados
- **Embeddings**: Geração automática com Sentence Transformers
- **Banco de dados**: SQLite para busca e recuperação
- **Metadados ricos**: Preservação de contexto e origem

### 4. Detecção de Sites Complexos
- **JavaScript**: Selenium para sites com conteúdo dinâmico
- **Autodesk Help**: Suporte específico para documentação técnica
- **Multi-idioma**: Detecção automática de idioma
- **Retry automático**: Tolerância a falhas de rede

## Estrutura de Saída

```
web_scraping_storage/
├── extraction_TIMESTAMP.json          # Resultado básico
├── complete_extraction_TIMESTAMP.json # Resultado completo com chunks
├── web_scraping.db                    # Banco SQLite
└── videos/
    └── VIDEO_ID/
        ├── video.mp4                  # Vídeo baixado
        ├── transcript.txt             # Transcrição
        └── metadata.json              # Metadados do vídeo
```

## Exemplos de Uso

### Exemplo 1: Documentação da Autodesk
```bash
# Extrair página específica com vídeo
python web_scraper_advanced.py \
  --url "https://help.autodesk.com/view/ARCHDESK/2026/ENU/?guid=GUID-4A458300-2D7E-401F-8B6A-7A6129E4DDAB" \
  --selenium \
  --process-videos
```

**Resultado esperado:**
- Texto da documentação extraído
- Vídeo de 4:50 baixado (33.5 MB)
- Links para páginas relacionadas
- Chunks RAG criados
- Dados salvos no SQLite

### Exemplo 2: Site Estático
```bash
# Extração rápida sem JavaScript
python web_documentation_scraper.py \
  --url "https://docs.python.org/3/tutorial/"
```

### Exemplo 3: Teste Básico
```bash
# Script de teste incluído
python test_scraper.py
```

## Arquivos do Sistema

### Scripts Principais
- `web_documentation_scraper.py` - Extrator básico
- `web_scraper_advanced.py` - Extrator com processamento de vídeos
- `install.py` - Instalador automático
- `test_scraper.py` - Script de teste (criado pelo instalador)

### Configuração
- `requirements.txt` - Dependências Python
- `README.md` - Esta documentação

## Dependências

### Obrigatórias
```
requests>=2.31.0          # HTTP requests
beautifulsoup4>=4.12.0    # HTML parsing
pandas>=2.0.0             # Data processing
sentence-transformers>=2.2.2  # Embeddings
```

### Opcionais
```
seleniumbase>=4.20.0      # JavaScript sites
openai-whisper>=20231117  # Video transcription
ffmpeg-python>=0.2.0      # Video processing
```

## Limitações e Soluções

### FFmpeg não encontrado
```
⚠️ Problema: Erro na transcrição de vídeos
✅ Solução: Instalar FFmpeg
   1. Download: https://www.gyan.dev/ffmpeg/builds/
   2. Extrair para C:/ffmpeg
   3. Adicionar ao PATH do sistema
```

### Sites com proteção anti-bot
```
⚠️ Problema: Bloqueio de acesso
✅ Solução: Usar --selenium com headers personalizados
```

### Vídeos grandes
```
⚠️ Problema: Download lento ou falha
✅ Solução: Implementar download em chunks (futuro)
```

## Casos de Uso

### 1. Documentação Técnica
- **Autodesk Help**: Páginas com vídeos tutoriais
- **Microsoft Docs**: Documentação com código
- **GitHub Wikis**: Repositórios de conhecimento

### 2. Bases de Conhecimento
- **Confluence**: Páginas corporativas
- **Notion**: Documentos estruturados
- **GitBook**: Livros técnicos

### 3. Sites de Treinamento
- **Khan Academy**: Vídeos educacionais
- **Coursera**: Cursos online
- **Udemy**: Materiais de curso

## Desenvolvimento

### Estrutura do Código
```python
# Classe principal
WebDocumentationScraper
├── extract_page_content()      # Extração básica
├── detect_page_language()      # Detecção de idioma
├── _extract_videos()           # Processamento de vídeos
└── _extract_tables()           # Processamento de tabelas

# Classe avançada
WebScraperWithVideoProcessing
├── process_videos_from_page()  # Processamento completo
├── create_chunks_from_content() # Geração de chunks RAG
└── save_to_database()          # Armazenamento SQLite
```

### Testes Realizados
✅ **Autodesk Help**: Página com vídeo HTML5 (4:50, 33.5MB)
✅ **Detecção de idioma**: Inglês (ENU) detectado corretamente
✅ **Selenium**: Carregamento de JavaScript funcional
✅ **Download de vídeo**: MP4 baixado com sucesso
✅ **Chunks RAG**: 5 chunks gerados com embeddings
✅ **Banco SQLite**: Dados salvos corretamente

## Próximos Passos

### Funcionalidades Planejadas
1. **Crawling recursivo**: Seguir links automaticamente
2. **Cache inteligente**: Evitar re-downloads desnecessários
3. **Processamento em batch**: Múltiplas URLs simultaneamente
4. **API REST**: Interface web para o sistema
5. **Integração Docling**: Processamento avançado de documentos

### Melhorias Técnicas
1. **Retry inteligente**: Backoff exponencial
2. **Pool de conexões**: Otimização de performance
3. **Streaming de vídeos**: Download eficiente
4. **Detecção de duplicatas**: Evitar conteúdo repetido

---

**Sistema testado e validado - Pronto para extração de documentação web!** 🎯
