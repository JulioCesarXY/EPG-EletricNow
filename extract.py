import time
import json
from playwright.sync_api import sync_playwright

def intercept_stream():
    with sync_playwright() as p:
        # Iniciamos o navegador
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Esta função intercepta as requisições que buscam o manifesto de vídeo
        def log_request(intercepted_request):
            if "mediatailor.us-west-2.amazonaws.com" in intercepted_request.url and "m3u8" in intercepted_request.url:
                print(f"\n[!!!] STREAM ENCONTRADO [!!!]")
                print(f"URL: {intercepted_request.url}")
                # Aqui você pode salvar essa URL em um arquivo

        page.on("request", log_request)

        print("[-] Acessando site e esperando player carregar...")
        page.goto("https://www.electricnow.tv/live-tv/")
        
        # O segredo: esperar o player carregar o vídeo. 
        # Sites desse tipo carregam o vídeo após uns 10-15 segundos.
        time.sleep(20) 
        
        browser.close()

if __name__ == "__main__":
    intercept_stream()
