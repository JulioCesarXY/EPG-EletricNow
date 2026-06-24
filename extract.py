import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Lista para armazenar os links encontrados
        streams = {}

        # Monitora todas as requisições de rede que terminam em m3u8
        def on_response(response):
            if "m3u8" in response.url and "master" in response.url:
                # O slug do canal geralmente está na URL ou podemos inferir
                channel_name = response.url.split('/')[-4] # Ajuste conforme a estrutura
                streams[channel_name] = response.url
                print(f"[+] Stream capturado: {response.url}")

        page.on("response", on_response)

        print("[-] Acessando a página de canais...")
        page.goto("https://www.electricnow.tv/live-tv/")

        # A interação é necessária para o player carregar o stream
        print("[-] Simulando seleção de canais...")
        try:
            # Espera o carregamento inicial
            page.wait_for_load_state("networkidle")
            # Clica no botão/link de canal (ajuste o seletor se necessário)
            # Geralmente são elementos de lista ou links com a classe de canal
            page.wait_for_selector(".channel-item", timeout=10000)
            items = page.query_selector_all(".channel-item")
            for item in items[:5]: # Clica nos primeiros 5 para forçar o carregamento
                item.click()
                time.sleep(3) 
        except Exception as e:
            print(f"[!] Erro na interação: {e}")

        # Salva o resultado
        if streams:
            with open("streams.txt", "w") as f:
                for name, url in streams.items():
                    f.write(f"{name}: {url}\n")
            print("[+] Lista de streams salva em streams.txt")
        else:
            print("[!] Nenhum stream foi capturado.")
            
        browser.close()

if __name__ == "__main__":
    run()
