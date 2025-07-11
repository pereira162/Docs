# 🧅 GUIA RÁPIDO: INSTALAR E USAR TOR

## 📥 **INSTALAÇÃO DO TOR**

### **Windows (Mais Fácil):**

1. **Baixar Tor Browser:**
   - Ir em: https://www.torproject.org/download/
   - Baixar "Tor Browser for Windows"
   - Instalar normalmente

2. **Executar Tor Browser:**
   - Abrir o Tor Browser
   - Aguardar conectar à rede Tor
   - ✅ Tor estará rodando na porta 9050

### **Windows (Apenas Serviço):**

1. **Baixar Tor Expert Bundle:**
   - Ir em: https://www.torproject.org/download/tor/
   - Baixar "Expert Bundle"
   - Extrair em C:\tor

2. **Executar Tor:**
   ```cmd
   cd C:\tor
   tor.exe
   ```

### **Linux/Ubuntu:**
```bash
# Instalar Tor
sudo apt update
sudo apt install tor

# Iniciar Tor
sudo systemctl start tor
sudo systemctl enable tor

# Verificar se está rodando
sudo systemctl status tor
```

### **macOS:**
```bash
# Via Homebrew
brew install tor

# Executar
tor
```

## ✅ **VERIFICAR SE TOR ESTÁ FUNCIONANDO**

### **Método 1: Teste Web**
```bash
curl --socks5 127.0.0.1:9050 http://check.torproject.org/api/ip
```

### **Método 2: Teste Python**
```python
import requests

proxies = {
    'http': 'socks5://127.0.0.1:9050',
    'https': 'socks5://127.0.0.1:9050'
}

response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())
```

## 🎬 **USAR COM O EXTRATOR**

### **Comando Simples:**
```bash
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=ff89oHwvNsM" --tor
```

### **Comando Completo:**
```bash
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=ff89oHwvNsM" --proxy "socks5://127.0.0.1:9050" --folder "teste_tor"
```

## 🚀 **TESTE RÁPIDO AGORA**

1. **Abrir Tor Browser (deixar rodando)**
2. **Executar:**
```bash
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=ff89oHwvNsM" --tor --folder "teste_tor_funcionando"
```

## 📱 **ALTERNATIVAS MÓVEIS**

### **Orbot (Android):**
- Instalar Orbot do Google Play
- Ativar "VPN Mode"
- Usar normalmente

### **Onion Browser (iOS):**
- Instalar da App Store
- Conectar e usar

## ⚡ **SOLUÇÃO MAIS RÁPIDA (SEM INSTALAR NADA)**

Use um dos serviços VPN gratuitos:

### **1. ProtonVPN (Grátis):**
- Criar conta em: protonvpn.com
- Baixar app
- Conectar servidor grátis
- Usar extrator normalmente

### **2. Windscribe (10GB grátis/mês):**
- Criar conta em: windscribe.com
- Baixar app
- Conectar
- Usar extrator

### **3. TunnelBear (500MB grátis/mês):**
- Criar conta em: tunnelbear.com
- Conectar VPN
- Usar extrator

## 🔧 **TROUBLESHOOTING**

### **Tor não conecta:**
```bash
# Verificar se porta 9050 está ocupada
netstat -an | findstr 9050

# Matar processos Tor
taskkill /f /im tor.exe

# Reiniciar Tor
tor.exe
```

### **Erro de proxy:**
```bash
# Verificar se Tor está rodando
curl --socks5 127.0.0.1:9050 http://check.torproject.org/

# Se não funcionar, tentar porta 9150 (Tor Browser)
python youtube_rag_extractor_final.py --proxy "socks5://127.0.0.1:9150" --url "VIDEO"
```

### **Lento demais:**
- Tor é naturalmente mais lento
- Para velocidade, usar VPN comercial
- Aguardar alguns segundos entre vídeos

## 💡 **DICAS IMPORTANTES**

1. **Tor é GRÁTIS mas LENTO** - Seja paciente
2. **Deixar Tor Browser aberto** durante o uso
3. **VPNs são mais rápidas** que Tor
4. **Não usar Tor para atividades comerciais intensas**
5. **Para uso pessoal/teste, Tor é perfeito**

---

**🎯 COMANDO PARA TESTAR AGORA:**
```bash
# 1. Abrir Tor Browser
# 2. Executar:
python youtube_rag_extractor_final.py --url "https://www.youtube.com/watch?v=ff89oHwvNsM" --tor --folder "meu_teste_tor"
```
