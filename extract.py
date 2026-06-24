import json
import time
from playwright.sync_api import sync_playwright

def intercept_electricnow():
    print("[-] Iniciando navegador headless...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Contexto que força a emulação de um dispositivo real
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Armazena os links encontrados
        stream_links = {}

        def handle_response(response):
            # A API que retorna a URL do stream
            if "/api/live/stream/" in response.url:
                try:
                    data = response.json()
                    # Busca a URL dentro de possíveis campos de resposta da API
                    stream_url = data.get("stream_url") or data.get("url")
                    
                    if stream_url:
                        # Extrai o ID do canal da URL para identificar
                        channel_id = response.url.split("/")[-1]
                        if channel_id not in stream_links:
                            stream_links[channel_id] = stream_url.split("?")[0]
                            print(f"[+] Stream capturado para ID {channel_id}: {stream_links[channel_id]}")
                except:
                    pass

        page.on("response", handle_response)

        print("[-] Navegando para o site...")
        # Aumentamos o tempo de espera para o carregamento do React
        page.goto("https://www.electricnow.tv/live-tv/", wait_until="networkidle")

        print("[-] Aguardando carregamento dinâmico dos assets...")
        # Aumentamos o tempo de espera para o player inicializar automaticamente
        time.sleep(30) 

        if stream_links:
            print(f"\n[+] Total de streams capturados: {len(stream_links)}")
            with open("lista_canais.txt", "w") as f:
                for cid, url in stream_links.items():
                    f.write(f"{cid} | {url}\n")
        else:
            print("[!] Nenhum stream capturado. O site pode estar bloqueando automação ou usando WebSockets.")

        context.close()
        browser.close()

if __name__ == "__main__":
    intercept_electricnow()
