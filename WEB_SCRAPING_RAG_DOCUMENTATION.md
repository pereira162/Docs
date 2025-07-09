# Sistema Avançado de Web Scraping para RAG

## 📖 Visão Geral

Este sistema implementa uma solução completa de web scraping para sites dinâmicos com capacidades de RAG (Retrieval-Augmented Generation). Ele foi especialmente projetado para extrair conteúdo de sites com JavaScript pesado, como a documentação da Autodesk.

## 🎯 Características Principais

### ✨ Capacidades de Extração
- **Sites Dinâmicos**: Usando SeleniumBase para lidar com JavaScript e conteúdo dinâmico
- **Navegação Inteligente**: Suporte a múltiplas abas e navegação complexa
- **Downloads Automáticos**: Extração de PDFs, vídeos, documentos e outros arquivos
- **Screenshots**: Captura automática de telas para documentação
- **Análise de Conteúdo**: Processamento inteligente de texto e metadados

### 🔍 Sistema RAG Integrado
- **Chunking Inteligente**: Divisão otimizada de texto em chunks com sobreposição
- **Busca Semântica**: Sistema TF-IDF para busca de conteúdo relevante
- **Análise de Legibilidade**: Avaliação automática da qualidade do conteúdo
- **Metadados Ricos**: Extração de informações contextuais detalhadas

### 🗄️ Persistência e Análise
- **Banco SQLite**: Armazenamento estruturado de todos os dados
- **Cache Inteligente**: Sistema de cache para busca rápida
- **Estatísticas Detalhadas**: Análise completa dos dados extraídos
- **Exportação**: Suporte a CSV, JSON e outros formatos

### 🌐 API REST Completa
- **Extração Assíncrona**: Processamento em background com status em tempo real
- **Busca Interativa**: Endpoints para busca semântica
- **Gerenciamento de Tarefas**: Controle completo de tarefas de extração
- **Documentação Swagger**: Interface web para testes

## 📂 Estrutura do Sistema

```
rag-system/backend/
├── web_scraper_extractor.py          # Extrator principal com SeleniumBase
├── web_scraping_data_manager.py      # Gerenciador de dados e busca
├── web_scraping_integration.py       # API REST FastAPI
├── web_scraping_config.py            # Configurações centralizadas
├── test_web_scraping_system.py       # Sistema de testes e demonstração
└── requirements.txt                   # Dependências atualizadas
```

## 🚀 Instalação e Configuração

### 1. Instalação de Dependências

```bash
# Entre no diretório backend
cd rag-system/backend

# Instale as dependências
pip install -r requirements.txt

# Instalar drivers do Selenium (automático via SeleniumBase)
seleniumbase install chromedriver
```

### 2. Configuração do Sistema

O sistema usa configurações centralizadas em `web_scraping_config.py`. As principais configurações incluem:

```python
# Configurações básicas
DEFAULT_CHUNK_SIZE = 512          # Tamanho dos chunks
DEFAULT_MAX_PAGES = 50            # Máximo de páginas por extração
DEFAULT_DELAY_BETWEEN_REQUESTS = 2.0  # Delay entre requisições

# Configurações da API
API_HOST = "0.0.0.0"
API_PORT = 8001
```

### 3. Teste do Sistema

```bash
# Execute o script de demonstração
python test_web_scraping_system.py

# Escolha a opção 1 para demonstração completa
```

## 💻 Uso Básico

### Extração Via Código Python

```python
from web_scraper_extractor import WebScraperExtractor

# Cria extrator
extractor = WebScraperExtractor(
    base_output_dir="minha_extracao",
    chunk_size=512,
    max_pages=20
)

# Executa extração
results = extractor.extract_from_website(
    start_url="https://help.autodesk.com/view/ARCHDESK/2024/ENU/",
    max_depth=2,
    same_domain_only=True
)

print(f"Páginas processadas: {results['extraction_summary']['total_pages_processed']}")
print(f"Chunks criados: {results['extraction_summary']['total_chunks_created']}")
```

### Gerenciamento de Dados

```python
from web_scraping_data_manager import WebScrapingDataManager

# Cria gerenciador
manager = WebScrapingDataManager("web_scraping_data")

# Busca conteúdo
results = manager.search_chunks("AutoCAD Architecture ferramentas", limit=5)

for result in results:
    print(f"Score: {result['similarity_score']:.3f}")
    print(f"Texto: {result['text'][:100]}...")
```

### API REST

```bash
# Inicia o servidor
python web_scraping_integration.py

# Ou usando uvicorn
uvicorn web_scraping_integration:app --host 0.0.0.0 --port 8001 --reload
```

## 🌐 Endpoints da API

### Extração de Conteúdo

```http
POST /extract
Content-Type: application/json

{
  "start_url": "https://help.autodesk.com/view/ARCHDESK/2024/ENU/",
  "max_depth": 2,
  "max_pages": 20,
  "same_domain_only": true,
  "delay_between_requests": 2.0,
  "chunk_size": 512,
  "overlap": 50
}
```

**Resposta:**
```json
{
  "task_id": "webscraping_1703123456_1234",
  "status": "queued",
  "message": "Tarefa de extração iniciada",
  "start_url": "https://help.autodesk.com/view/ARCHDESK/2024/ENU/"
}
```

### Status da Tarefa

```http
GET /tasks/{task_id}
```

**Resposta:**
```json
{
  "status": "running",
  "progress": 45,
  "message": "Processando página 9 de 20...",
  "start_time": "2024-01-01T10:00:00",
  "results": null
}
```

### Busca de Conteúdo

```http
POST /search
Content-Type: application/json

{
  "query": "AutoCAD Architecture tools design",
  "limit": 10,
  "min_similarity": 0.1
}
```

**Resposta:**
```json
{
  "query": "AutoCAD Architecture tools design",
  "total_results": 3,
  "results": [
    {
      "chunk_id": "page_001_chunk_0",
      "text": "AutoCAD Architecture oferece ferramentas especializadas...",
      "similarity_score": 0.856,
      "source_url": "https://help.autodesk.com/...",
      "page_title": "Ferramentas de Desenho"
    }
  ],
  "search_timestamp": "2024-01-01T10:05:00"
}
```

### Estatísticas

```http
GET /statistics
```

**Resposta:**
```json
{
  "timestamp": "2024-01-01T10:00:00",
  "statistics": {
    "database_stats": {
      "total_pages": 45,
      "total_chunks": 1250,
      "total_downloads": 12,
      "total_content_length": 125000,
      "average_readability": 65.2
    },
    "top_domains": [
      {"domain": "help.autodesk.com", "count": 30},
      {"domain": "docs.autodesk.com", "count": 15}
    ]
  }
}
```

## 🔧 Configurações Avançadas

### Configurações por Domínio

O sistema permite configurações específicas por domínio em `web_scraping_config.py`:

```python
DOMAIN_SPECIFIC_CONFIGS = {
    "help.autodesk.com": {
        "delay_between_requests": 3.0,
        "max_pages": 30,
        "max_depth": 2,
        "custom_selectors": {
            "main_content": ["main", ".content", ".help-content"],
            "download_links": ["a[href$='.pdf']", "a[href*='download']"]
        }
    }
}
```

### Seletores CSS Personalizados

```python
CONTENT_SELECTORS = {
    "main_content": [
        'main', '[role="main"]', '.main-content',
        '.documentation', '.help-content'
    ],
    "download_links": [
        'a[href$=".pdf"]', 'a[href*="download"]'
    ]
}
```

## 📊 Monitoramento e Análise

### Estrutura do Banco de Dados

O sistema cria automaticamente as seguintes tabelas:

- **web_pages**: Páginas extraídas com metadados
- **web_chunks**: Chunks de texto para RAG
- **downloads**: Arquivos baixados
- **extracted_links**: Links encontrados
- **content_analysis**: Análises de conteúdo

### Exportação de Dados

```python
# Via código
manager = WebScrapingDataManager()
exported_files = manager.export_to_csv("exports")

# Via API
GET /export/csv
```

### Limpeza de Dados Antigos

```python
# Remove dados com mais de 30 dias
deleted_count = manager.cleanup_old_data(days_old=30)
```

## 🎯 Casos de Uso

### 1. Documentação Técnica (Autodesk)

```python
extractor = WebScraperExtractor(
    max_pages=50,
    delay_between_requests=3.0
)

results = extractor.extract_from_website(
    "https://help.autodesk.com/view/ARCHDESK/2024/ENU/",
    max_depth=3,
    same_domain_only=True
)
```

### 2. Site de E-commerce

```python
extractor = WebScraperExtractor(
    max_pages=100,
    delay_between_requests=1.0
)

results = extractor.extract_from_website(
    "https://example-store.com/products/",
    max_depth=2,
    same_domain_only=False
)
```

### 3. Portal de Notícias

```python
extractor = WebScraperExtractor(
    chunk_size=256,  # Chunks menores para notícias
    max_pages=200
)

results = extractor.extract_from_website(
    "https://news-portal.com/",
    max_depth=2
)
```

## 🛠️ Personalização

### Adicionando Novos Seletores

```python
# Em web_scraping_config.py
CONTENT_SELECTORS["custom_content"] = [
    '.my-custom-selector',
    '#specific-id',
    '[data-content="main"]'
]
```

### Configurando Novos Tipos de Download

```python
# Adicione extensões à configuração
config.DOWNLOADABLE_EXTENSIONS.extend(['dwg', 'dxf', 'rvt'])
```

### Processamento Pós-Extração

```python
class CustomWebScrapingDataManager(WebScrapingDataManager):
    def store_web_page(self, page_data):
        # Processamento customizado
        page_data = self.custom_preprocessing(page_data)
        return super().store_web_page(page_data)
    
    def custom_preprocessing(self, page_data):
        # Sua lógica aqui
        return page_data
```

## 🚨 Tratamento de Erros

O sistema inclui tratamento robusto de erros:

- **Timeouts**: Retry automático com backoff exponencial
- **Rate Limiting**: Delay adaptativo baseado na resposta do servidor
- **Conexão**: Tentativas múltiplas com diferentes estratégias
- **Parsing**: Fallbacks para diferentes formatos de conteúdo

## 📈 Performance

### Otimizações Implementadas

- **Cache de Chunks**: Busca rápida em memória
- **Índices de Banco**: Otimização de queries
- **Lazy Loading**: Carregamento sob demanda
- **Batch Processing**: Processamento em lotes

### Monitoramento

```python
# Estatísticas de performance
stats = manager.get_statistics()
print(f"Cache hits: {stats['cache_info']['chunks_cached']}")
print(f"TF-IDF initialized: {stats['cache_info']['tfidf_initialized']}")
```

## 🔒 Considerações de Segurança

- **Rate Limiting**: Respeita limites dos servidores
- **User Agents**: Headers realistas para evitar bloqueios
- **Robots.txt**: Verificação opcional (configurável)
- **Sanitização**: Limpeza de nomes de arquivos e URLs

## 📝 Logs e Debug

O sistema gera logs detalhados em várias categorias:

- **Extração**: Progress e erros de scraping
- **Banco de Dados**: Operações SQL e performance
- **API**: Requisições e respostas
- **Cache**: Hit/miss ratios e operações

## 🤝 Integração com Outros Sistemas

### Com Sistema RAG Existente

```python
# Integrar chunks com ChromaDB existente
chunks = manager.search_chunks("query", limit=10)
for chunk in chunks:
    # Adicionar ao ChromaDB
    collection.add(
        documents=[chunk['text']],
        metadatas=[chunk['metadata']],
        ids=[chunk['chunk_id']]
    )
```

### Com Sistema de Processamento de Documentos

```python
# Processar downloads automaticamente
for download in manager.downloaded_files:
    if download['filename'].endswith('.pdf'):
        # Processar PDF com docling
        process_pdf(download['local_path'])
```

## 🎉 Conclusão

Este sistema oferece uma solução completa para extração de conteúdo web com capacidades avançadas de RAG. Ele foi projetado para ser:

- **Escalável**: Processa sites grandes com eficiência
- **Flexível**: Configurável para diferentes tipos de sites
- **Robusto**: Tratamento abrangente de erros
- **Integrável**: APIs claras para integração
- **Mantível**: Código bem estruturado e documentado

Para suporte ou contribuições, consulte a documentação da API em `/docs` quando o servidor estiver executando.

---

**Versão**: 1.0.0  
**Última Atualização**: 2024  
**Autor**: Assistant IA  
**Licença**: MIT
