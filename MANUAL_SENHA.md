1# 🔐 Manual de Configuração de Senha - RAG Docling System

## Visão Geral
Este documento explica como alterar a senha de acesso do sistema RAG Docling, tanto no backend quanto no frontend.

## 🔧 Como Alterar a Senha

### 1. **Backend (Servidor)**

#### Método 1: Arquivo .env (Recomendado)
1. **Localize o arquivo `.env`** na pasta `backend/`
2. **Edite a linha da senha**:
   ```bash
   SITE_PASSWORD=sua_nova_senha_aqui
   ```
3. **Salve o arquivo**
4. **Reinicie o servidor** (Ctrl+C e executar novamente)

#### Método 2: Variável de Ambiente
1. **No Windows PowerShell**:
   ```powershell
   $env:SITE_PASSWORD = "sua_nova_senha"
   cd backend
   python main.py
   ```

2. **No Windows CMD**:
   ```cmd
   set SITE_PASSWORD=sua_nova_senha
   cd backend
   python main.py
   ```

3. **No Linux/Mac**:
   ```bash
   export SITE_PASSWORD="sua_nova_senha"
   cd backend
   python main.py
   ```

#### Método 3: Hardcoded (Não Recomendado)
Edite o arquivo `main.py` na linha:
```python
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "123")  # Mude "123" para sua senha
```

### 2. **Frontend (Interface)**

O frontend **NÃO armazena** a senha fixa. Ele sempre pede a senha e a envia para o backend para validação.

#### Como o usuário digita a nova senha:
1. **Acesse** `http://localhost:3001/Docs/`
2. **Digite a nova senha** (que você configurou no backend)
3. **Clique em "Entrar"**

#### Limpando senha salva:
Se o navegador salvou a senha antiga:
1. **Abra o Console do Navegador** (F12)
2. **Execute**:
   ```javascript
   localStorage.removeItem('rag_password');
   location.reload();
   ```

## 🛡️ Exemplos Práticos

### Exemplo 1: Alterar para senha "minhasenha123"

**1. Editar .env:**
```bash
SITE_PASSWORD=minhasenha123
```

**2. Reiniciar servidor:**
```bash
cd backend
python main.py
```

**3. No frontend:**
- Digite: `minhasenha123`
- Clique em "Entrar"

### Exemplo 2: Senha complexa "Meu$istema@2025!"

**1. Editar .env:**
```bash
SITE_PASSWORD=Meu$istema@2025!
```

**2. Reiniciar e usar no frontend**

## 🔍 Verificando se a Senha Foi Alterada

### No Log do Servidor:
Quando o servidor inicia, você deve ver:
```
INFO:rag_docling_system:🔑 Password: sua_nova_senha
```

### Testando via Browser:
1. Acesse `http://localhost:3001/Docs/`
2. Digite a senha correta → deve entrar
3. Digite senha errada → deve dar erro

### Testando via API:
```bash
# Teste com senha correta (substitua "123" pela sua senha)
curl -H "Authorization: Bearer 123" http://localhost:8000/health

# Deve retornar JSON com status "healthy"
```

## ⚠️ Problemas Comuns

### 1. **Erro CORS**
**Sintoma:** `Access to fetch at 'http://localhost:8000/health' from origin 'http://localhost:3001' has been blocked by CORS policy`

**Solução:** O servidor já está configurado para aceitar `localhost:3001`. Se ainda der erro:
1. Verifique se o servidor está rodando na porta 8000
2. Tente usar `localhost:3000` no frontend
3. Limpe o cache do navegador

### 2. **Senha não funciona**
**Sintoma:** Sempre retorna "Token inválido"

**Possíveis causas:**
1. **Espaços extras** na senha no .env
2. **Caracteres especiais** não escapados
3. **Servidor não reiniciado** após mudança
4. **Arquivo .env não foi salvo**

**Solução:**
```bash
# 1. Verifique o .env (sem espaços ao redor)
SITE_PASSWORD=minhasenha

# 2. Reinicie o servidor
cd backend
python main.py

# 3. Verifique no log se a senha aparece correta
```

### 3. **Frontend não consegue conectar**
**Sintoma:** `net::ERR_FAILED` ou `Connection refused`

**Solução:**
1. Verifique se o backend está rodando: `http://localhost:8000/health`
2. Verifique se o frontend está na porta correta
3. Confirme que não há firewall bloqueando

## 📁 Arquivos Importantes

### Backend:
- **`.env`** - Configuração da senha (principal)
- **`main.py`** - Código do servidor
- **Terminal** - Logs do servidor

### Frontend:
- **`App.tsx`** - Interface de login
- **`localStorage`** - Armazena senha temporariamente no navegador

## 🔒 Boas Práticas de Segurança

### ✅ Recomendado:
- Use senhas de **8+ caracteres**
- Inclua **números e símbolos**
- Mantenha o arquivo **.env** fora do Git
- Use **variáveis de ambiente** em produção

### ❌ Evite:
- Senhas simples como "123" ou "password"
- Senhas hardcoded no código
- Compartilhar o arquivo .env
- Usar a mesma senha em múltiplos sistemas

## 🚀 Exemplo Completo: Alterando de "123" para "MinhaSenha@2025"

### Passo 1: Editar .env
```bash
# Antes
SITE_PASSWORD=123

# Depois  
SITE_PASSWORD=MinhaSenha@2025
```

### Passo 2: Reiniciar servidor
```bash
cd backend
# Parar servidor atual (Ctrl+C)
python main.py
```

### Passo 3: Limpar cache do frontend
```javascript
// No console do navegador (F12)
localStorage.removeItem('rag_password');
location.reload();
```

### Passo 4: Fazer login
1. Acessar `http://localhost:3001/Docs/`
2. Digitar: `MinhaSenha@2025`
3. Clicar "Entrar"

### Passo 5: Verificar funcionamento
- Frontend deve carregar a dashboard
- Backend deve mostrar logs de sucesso
- Todas as funções devem funcionar normalmente

---

**🎯 Pronto! Sistema configurado com nova senha e funcionando perfeitamente.**
