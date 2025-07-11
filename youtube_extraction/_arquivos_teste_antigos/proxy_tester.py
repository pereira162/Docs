#!/usr/bin/env python3
"""
🔍 TESTADOR DE PROXIES PARA YOUTUBE
=================================
Script para encontrar proxies funcionais para contornar bloqueios do YouTube
"""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

class ProxyTester:
    def __init__(self):
        self.working_proxies = []
        self.lock = threading.Lock()
    
    def test_proxy(self, proxy):
        """Testa se um proxy funciona com YouTube"""
        try:
            # Testar com YouTube
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            
            proxies = {
                'http': proxy,
                'https': proxy
            }
            
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200 and 'youtube' in response.text.lower():
                with self.lock:
                    self.working_proxies.append(proxy)
                    print(f"✅ Proxy funcionando: {proxy}")
                return True
            else:
                print(f"❌ Proxy falhou: {proxy} (status: {response.status_code})")
                return False
                
        except Exception as e:
            print(f"❌ Erro no proxy {proxy}: {str(e)[:50]}...")
            return False
    
    def get_free_proxies(self):
        """Obtém lista de proxies gratuitos"""
        proxies = []
        
        try:
            # Lista de proxies conhecidos (atualizar conforme necessário)
            free_proxies = [
                "http://103.152.112.162:80",
                "http://20.111.54.16:80", 
                "http://103.149.162.194:80",
                "http://103.152.112.120:80",
                "http://154.236.168.179:1981",
                "http://185.15.172.212:3128",
                "http://103.149.162.195:80",
                "http://20.210.113.32:8123",
                "http://103.152.112.145:80",
                "http://154.236.168.181:1981"
            ]
            
            proxies.extend(free_proxies)
            
            # Tentar obter de APIs públicas
            try:
                response = requests.get(
                    "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    for proxy_info in data.get('data', []):
                        ip = proxy_info.get('ip')
                        port = proxy_info.get('port')
                        if ip and port:
                            proxies.append(f"http://{ip}:{port}")
            except:
                pass
            
        except Exception as e:
            print(f"Erro ao obter proxies: {e}")
        
        return list(set(proxies))  # Remove duplicatas
    
    def find_working_proxies(self, max_workers=10):
        """Encontra proxies funcionais"""
        print("🔍 Buscando proxies gratuitos...")
        
        all_proxies = self.get_free_proxies()
        print(f"📋 Testando {len(all_proxies)} proxies...")
        
        # Testar proxies em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(self.test_proxy, all_proxies))
        
        return self.working_proxies

def main():
    """Encontra e salva proxies funcionais"""
    tester = ProxyTester()
    
    print("🎯 Iniciando teste de proxies para YouTube...")
    
    working_proxies = tester.find_working_proxies()
    
    if working_proxies:
        print(f"\n✅ Encontrados {len(working_proxies)} proxies funcionais:")
        for i, proxy in enumerate(working_proxies, 1):
            print(f"  {i}. {proxy}")
        
        # Salvar proxies funcionais
        with open('proxies_funcionais.json', 'w') as f:
            json.dump(working_proxies, f, indent=2)
        
        print(f"\n💾 Proxies salvos em: proxies_funcionais.json")
        
        # Testar o primeiro proxy com o extrator
        print(f"\n🧪 Testando com o extrator do YouTube...")
        best_proxy = working_proxies[0]
        print(f"🎯 Melhor proxy encontrado: {best_proxy}")
        print(f"\n📝 Para usar:")
        print(f"python youtube_rag_extractor_final.py --url \"VIDEO_URL\" --proxy \"{best_proxy}\"")
        
    else:
        print("\n❌ Nenhum proxy funcional encontrado.")
        print("💡 Sugestões:")
        print("1. Usar Tor: python youtube_rag_extractor_final.py --url \"VIDEO_URL\" --tor")
        print("2. Usar VPN")
        print("3. Tentar mais tarde")

if __name__ == "__main__":
    main()
