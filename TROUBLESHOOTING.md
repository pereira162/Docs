# 🔧 Manual de Resolução de Problemas - RAG Docling System

## ✅ **STATUS ATUAL DO SISTEMA**

### 📁 **Arquivos Organizados:**
- ✅ **Backend:** `main.py` (único arquivo, sem duplicatas)
- ✅ **Frontend:** `App.tsx` (limpo, sem versões antigas)
- ✅ **Configuração:** `.env` com senha configurável

### 🌐 **Servidores Rodando:**
- ✅ **Backend:** `http://localhost:8000` (FastAPI)
- ✅ **Frontend:** `http://localhost:3002/Docs/` (React/Vite)
- ✅ **CORS:** Configurado para permitir todas as origens

### 🔐 **Autenticação:**
- ✅ **Senha padrão:** `123` (configurável no `.env`)
- ✅ **Token:** Bearer authentication
- ✅ **Manual:** `MANUAL_SENHA.md` criado

## 🚨 **PROBLEMAS IDENTIFICADOS E SOLUÇÕES**

### 1. **Erro CORS (Resolvido)**
**Problema:** `Access to fetch blocked by CORS policy`

**✅ Solução Aplicada:**
```python
# Em main.py - CORS configurado para aceitar todas as origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Aceita qualquer origem
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
```

### 2. **Múltiplas Portas Frontend**
**Problema:** Frontend mudando de porta (3000 → 3001 → 3002)

**✅ Solução:** CORS aceita qualquer porta com `"*"`

### 3. **Arquivos Duplicados (Limpo)**
**✅ Removidos:**
- `main_new.py`, `main_old.py`, `main_simple.py`
- `test_basic.py`, `test_server.py`
- `App_old.tsx`

## 🔄 **COMO REINICIAR SISTEMA COMPLETAMENTE**

### 1. **Parar Todos os Serviços:**
```bash
# No terminal do backend (Ctrl+C)
# No terminal do frontend (Ctrl+C)
```

### 2. **Limpar Cache:**
```bash
# No navegador (F12 → Console)
localStorage.removeItem('rag_password');
location.reload();
```

### 3. **Reiniciar Backend:**
```bash
cd backend
python main.py
```
**Aguarde ver:** `🚀 Starting RAG Docling System on 0.0.0.0:8000`

### 4. **Reiniciar Frontend:**
```bash
cd frontend
npm run dev
```
**Aguarde ver:** `Local: http://localhost:XXXX/Docs/`

### 5. **Testar Conexão:**
1. Acesse a URL do frontend
2. Digite senha: `123`
3. Clique "Entrar"

## 🛠️ **COMANDOS DE DIAGNÓSTICO**

### Verificar se Backend está respondendo:
```bash
# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Resultado esperado: Status 200 com JSON
```

### Verificar se Frontend está carregando:
```bash
# Abrir no navegador
http://localhost:3002/Docs/
```

### Verificar logs do servidor:
```bash
# No terminal do backend, deve aparecer:
INFO:rag_docling_system:🔑 Password: 123
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔐 **TESTE DE AUTENTICAÇÃO**

### Teste via Browser:
1. **Acesse:** `http://localhost:3002/Docs/`
2. **Digite:** `123`
3. **Resultado esperado:** Tela principal carrega
4. **Se der erro:** Verifique console do navegador (F12)

### Teste via API:
```bash
# Com senha correta
curl -H "Authorization: Bearer 123" http://localhost:8000/health

# Resultado esperado: JSON com "status": "healthy"
```

## 📝 **LOG DE PROBLEMAS COMUNS**

### **Erro:** "net::ERR_FAILED"
**Causa:** Backend não está rodando
**Solução:** Reiniciar backend com `python main.py`

### **Erro:** "Token inválido"
**Causa:** Senha incorreta ou não configurada
**Solução:** 
1. Verificar `.env`: `SITE_PASSWORD=123`
2. Reiniciar backend
3. Limpar cache do navegador

### **Erro:** "CORS policy"
**Causa:** Origem não permitida (já resolvido)
**Solução:** Já aplicada - CORS aceita todas as origens

### **Erro:** "Port in use"
**Causa:** Porta já ocupada
**Solução:** Sistema busca automaticamente próxima porta disponível

## 🔄 **FLUXO DE RESTART COMPLETO**

### Cenário: "Nada está funcionando"

```bash
# 1. Parar tudo (Ctrl+C em todos os terminais)

# 2. Navegar para o backend
cd "C:\Users\lucas\OneDrive\Área de Trabalho\LUCAS\ENGENHEIRO\WEB DESIGN\RAG Docling\Docs\rag-system\backend"

# 3. Verificar .env
type .env
# Deve mostrar: SITE_PASSWORD=123

# 4. Iniciar backend
python main.py
# Aguardar: "🚀 Starting RAG Docling System on 0.0.0.0:8000"

# 5. Abrir novo terminal para frontend
cd "C:\Users\lucas\OneDrive\Área de Trabalho\LUCAS\ENGENHEIRO\WEB DESIGN\RAG Docling\Docs\rag-system\frontend"

# 6. Iniciar frontend
npm run dev
# Aguardar: "Local: http://localhost:XXXX/Docs/"

# 7. Abrir navegador na URL mostrada

# 8. Digitar senha: 123

# 9. Testar upload de arquivo ou adicionar URL
```

## 📊 **CHECKLIST DE FUNCIONAMENTO**

### ✅ **Backend Funcionando:**
- [ ] Terminal mostra "Uvicorn running on http://0.0.0.0:8000"
- [ ] Senha aparece no log: "🔑 Password: 123"
- [ ] Gemini configurado: "🤖 Gemini configured: True"

### ✅ **Frontend Funcionando:**
- [ ] Terminal mostra "Local: http://localhost:XXXX/Docs/"
- [ ] Página abre no navegador
- [ ] Formulário de login aparece

### ✅ **Integração Funcionando:**
- [ ] Login com senha "123" funciona
- [ ] Dashboard carrega após login
- [ ] Estatísticas aparecem (mesmo que zeradas)
- [ ] Botões respondem

### ✅ **Funcionalidades Principais:**
- [ ] Upload de arquivo funciona
- [ ] Adicionar URL funciona
- [ ] Consulta com IA funciona
- [ ] Download Export funciona
- [ ] Lista de documentos aparece

## 🎯 **RESULTADO ESPERADO**

Após seguir este manual:
1. **Backend:** Rodando em `localhost:8000` sem erros
2. **Frontend:** Acessível em `localhost:300X/Docs/`
3. **Login:** Funciona com senha `123`
4. **Sistema:** Totalmente operacional
5. **Documentos:** Podem ser adicionados e consultados
6. **Export:** Funciona para uso externo com IA

---

**🚀 Sistema RAG Docling operacional e pronto para uso!**
