# 📚 GUIA COMPLETO: RAG Document Extractor

## 🎯 **COMO USAR PARA QUALQUER ARQUIVO**

### 1️⃣ **Setup Inicial (Uma vez só)**

```bash
# Instalar dependências
pip install pdfplumber pathlib

# Copiar o arquivo rag_extractor_corrected.py para sua pasta
# Colocar seus PDFs na mesma pasta do script
```

### 2️⃣ **Extrair Qualquer PDF**

```python
# Método 1: Direto no script
python rag_extractor_corrected.py

# Método 2: Personalizado
from rag_extractor_corrected import CompletePDFExtractor

# Inicializar
extractor = CompletePDFExtractor(output_dir="./meus_outputs")

# Processar arquivo
results = extractor.process_pdf("meu_arquivo.pdf")
```

### 3️⃣ **Personalizar para Diferentes Tipos**

```python
# Para diferentes tipos de documento, modifique as funções:

def extract_complete_table_from_text(self, text: str, page_num: int):
    # Adicionar padrões específicos do seu documento
    if "Meu padrão específico" in text:
        # Lógica personalizada
        pass

def is_title(self, line: str):
    # Adicionar indicadores de título do seu tipo de documento
    my_indicators = ["Capítulo", "Seção", "Anexo"]
    return any(indicator in line for indicator in my_indicators)
```

---

## 🤖 **COMO USAR COM IA (AGENTES)**

### 📊 **Formatos Disponíveis**

Após extração, você terá 4 arquivos:

```
rag_outputs/
├── markdown/     # Para leitura humana
├── json/         # Para dados estruturados  
├── chunks/       # Para alimentar IA
└── metadata/     # Para estatísticas
```

### 🧩 **Chunks para IA (RECOMENDADO)**

```python
import json

# Carregar chunks otimizados para IA
with open('rag_outputs/chunks/arquivo_chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Cada chunk tem:
for chunk in chunks:
    print(f"ID: {chunk['chunk_id']}")
    print(f"Tipo: {chunk['type']}")        # 'text' ou 'table'
    print(f"Página: {chunk['page']}")
    print(f"Conteúdo: {chunk['content']}")  # Texto otimizado para IA
    
    if chunk['type'] == 'table':
        print(f"Tabela raw: {chunk['raw_table']}")  # Dados da tabela
```

### 🚀 **Integração com Agentes IA**

#### **OpenAI/ChatGPT:**
```python
import openai

# Carregar chunks
chunks_content = ""
for chunk in chunks:
    chunks_content += f"\\n\\n[{chunk['type'].upper()} - Página {chunk['page']}]\\n"
    chunks_content += chunk['content']

# Enviar para IA
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Você é um assistente especializado em análise de documentos."},
        {"role": "user", "content": f"Analise este documento:\\n{chunks_content}\\n\\nPergunta: [SUA PERGUNTA]"}
    ]
)
```

#### **Anthropic Claude:**
```python
import anthropic

client = anthropic.Anthropic(api_key="sua_key")

# Preparar contexto
context = "\\n\\n".join([
    f"[{chunk['type'].upper()} - Página {chunk['page']}] {chunk['content']}" 
    for chunk in chunks
])

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4000,
    messages=[
        {"role": "user", "content": f"Contexto: {context}\\n\\nPergunta: [SUA PERGUNTA]"}
    ]
)
```

#### **Agentes Locais (Ollama, LM Studio):**
```python
import requests

# Para Ollama
def query_ollama(chunks, question):
    context = "\\n".join([chunk['content'] for chunk in chunks])
    
    response = requests.post('http://localhost:11434/api/generate', 
        json={
            'model': 'llama2',
            'prompt': f"Contexto: {context}\\n\\nPergunta: {question}",
            'stream': False
        })
    
    return response.json()['response']
```

### 📋 **Estratégias de Uso Eficiente**

#### **1. Busca Semântica**
```python
# Filtrar chunks relevantes antes de enviar para IA
def find_relevant_chunks(chunks, keywords):
    relevant = []
    for chunk in chunks:
        if any(keyword.lower() in chunk['content'].lower() for keyword in keywords):
            relevant.append(chunk)
    return relevant

# Exemplo
autocad_chunks = find_relevant_chunks(chunks, ["AutoCAD", "Architecture", "productivity"])
```

#### **2. Análise por Tipo**
```python
# Separar texto de tabelas
text_chunks = [c for c in chunks if c['type'] == 'text']
table_chunks = [c for c in chunks if c['type'] == 'table']

# Perguntas diferentes para cada tipo
text_analysis = query_ai(text_chunks, "Resuma os principais pontos deste documento")
table_analysis = query_ai(table_chunks, "Analise os dados numéricos e crie insights")
```

#### **3. Análise Progressiva**
```python
# Quebrar em partes para evitar limite de tokens
def analyze_in_batches(chunks, batch_size=5):
    results = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        result = query_ai(batch, "Analise esta seção")
        results.append(result)
    return results
```

---

## ⚡ **EXEMPLOS PRÁTICOS**

### 📊 **Análise de Dados (Como AutoCAD)**
```python
# Extrair todas as tabelas
tables = [chunk for chunk in chunks if chunk['type'] == 'table']

# Analisar produtividade
productivity_question = """
Baseado nas tabelas extraídas:
1. Qual tarefa tem maior economia de tempo?
2. Qual a média de economia geral?
3. Que insights podemos extrair?
"""

response = query_ai(tables, productivity_question)
```

### 📖 **Resumo Executivo**
```python
# Pegar apenas texto das primeiras páginas
intro_chunks = [c for c in chunks if c['page'] <= 5 and c['type'] == 'text']

summary = query_ai(intro_chunks, "Crie um resumo executivo de 200 palavras")
```

### 🔍 **Busca Específica**
```python
def search_document(chunks, query):
    relevant_chunks = find_relevant_chunks(chunks, query.split())
    
    if relevant_chunks:
        context = "\\n\\n".join([c['content'] for c in relevant_chunks])
        return query_ai([{'content': context}], f"Responda: {query}")
    else:
        return "Informação não encontrada no documento"

# Exemplo
answer = search_document(chunks, "Como criar elevações no AutoCAD?")
```

---

## 🎯 **DICAS DE OTIMIZAÇÃO**

### 1. **Limite de Tokens**
- Monitore o tamanho dos chunks
- Use `char_count` e `word_count` para controlar envio
- Divida documentos grandes em batches

### 2. **Qualidade dos Prompts**
- Seja específico sobre o tipo de análise
- Inclua contexto sobre o tipo de documento
- Peça formatos específicos de resposta

### 3. **Cache de Resultados**
```python
import pickle

# Salvar chunks processados
with open('chunks_cache.pkl', 'wb') as f:
    pickle.dump(chunks, f)

# Carregar rapidamente
with open('chunks_cache.pkl', 'rb') as f:
    chunks = pickle.load(f)
```

### 4. **Validação de Extração**
```python
# Verificar qualidade da extração
def validate_extraction(results):
    print(f"✅ Páginas: {results['pages_processed']}/{results['total_pages']}")
    print(f"✅ Tabelas: {results['tables_found']}")
    
    if results['pages_processed'] < results['total_pages']:
        print("⚠️  Algumas páginas não foram processadas")
    
    if results['tables_found'] == 0:
        print("⚠️  Nenhuma tabela encontrada - verificar documento")
```

---

## 🔧 **TROUBLESHOOTING**

### ❌ **Problemas Comuns**

1. **Tabelas não extraídas:**
   - Verificar se tabelas estão em formato texto (não imagem)
   - Ajustar regex patterns na função `parse_table_row()`

2. **Páginas vazias:**
   - PDF pode ter páginas só com imagens
   - Usar OCR se necessário: `pip install pytesseract`

3. **Encoding errors:**
   - Sempre usar `encoding='utf-8'`
   - Verificar caracteres especiais

4. **Memória insuficiente:**
   - Processar PDFs grandes em lotes
   - Usar `pdfplumber` com configurações otimizadas

### 🛠️ **Customizações Avançadas**

```python
# Para documentos específicos, sobrescrever métodos:
class CustomExtractor(CompletePDFExtractor):
    def extract_complete_table_from_text(self, text, page_num):
        # Lógica personalizada para seu tipo de documento
        return super().extract_complete_table_from_text(text, page_num)
    
    def is_title(self, line):
        # Padrões específicos do seu documento
        return "MEU_PADRÃO" in line
```

---

## 🎉 **RESULTADO FINAL**

Com este sistema você pode:

✅ **Extrair qualquer PDF** com precisão  
✅ **Alimentar qualquer IA** com dados estruturados  
✅ **Automatizar análises** de documentos  
✅ **Criar agentes especializados** em seus documentos  
✅ **Escalar para milhares** de arquivos  

**O sistema RAG Local-First está pronto para produção! 🚀**
