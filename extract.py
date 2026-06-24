import json
import time
from playwright.sync_api import sync_playwright


def intercept_electricnow():
    print("[-] Iniciando navegador headless via Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        m3u_lines = ["#EXTM3U"]
        channels_map = {}

        # 1. Função interna para interceptar as respostas de rede
        def handle_response(response):
            # Captura a lista de canais da EPG para pegar metadados (como logos e slugs)
            if "/api/live/epg/" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if data.get("success") and "channels" in data:
                        print(
                            f"[+] EPG capturada! Mapeando {len(data['channels'])} canais..."
                        )
                        for chan in data["channels"]:
                            v_id = chan.get("video_id")
                            if v_id:
                                channels_map[v_id] = {
                                    "name": chan.get("name"),
                                    "slug": chan.get("slug"),
                                    "logo": chan.get("logo", ""),
                                }
                except Exception:
                    pass

            # Captura a URL final do streaming (.m3u8) retornada pela AWS/MediaTailor
            if "/api/live/stream/" in response.url and response.status == 200:
                try:
                    stream_json = response.json()
                    url_stream = stream_json.get("stream_url") or stream_json.get(
                        "url"
                    )

                    if (
                        not url_stream
                        and "data" in stream_json
                        and isinstance(stream_json["data"], dict)
                    ):
                        url_stream = stream_json["data"].get(
                            "stream_url"
                        ) or stream_json["data"].get("url")

                    if url_stream:
                        m3u8_clean = url_stream.split("?")[0]
                        v_id = response.url.split("/")[-1].split("?")[0]

                        # Associa com os metadados da EPG se houver correspondência
                        meta = channels_map.get(
                            v_id,
                            {
                                "name": f"Canal {v_id[:6]}",
                                "slug": v_id,
                                "logo": "",
                            },
                        )

                        print(f"    [+] Stream Link localizado -> {meta['name']}")

                        entry = f'#EXTINF:-1 tvg-id="{meta["slug"]}" tvg-name="{meta["name"]}" tvg-logo="{meta["logo"]}" group-title="ElectricNOW", {meta["name"]}\n{m3u8_clean}'
                        if entry not in m3u_lines:
                            m3u_lines.append(entry)
                except Exception:
                    pass

        # Ativa o listener de rede na página
        page.on("response", handle_response)

        # 2. Navega até a página principal onde o tráfego ocorre
        print("[-] Acessando a plataforma e aguardando tráfego de rede...")
        page.goto("https://www.electricnow.tv/live-tv/", wait_until="networkidle")

        # Aguarda 15 segundos para que o player execute o carregamento em lote dos canais
        print("[-] Aguardando o handshake dos streams internos...")
        time.sleep(15)

        # 3. Salva os resultados coletados
        if len(m3u_lines) > 1:
            m3u_content = "\n".join(m3u_lines) + "\n"
            with open("electricnow.m3u", "w", encoding="utf-8") as f:
                f.write(m3u_content)
            print(
                f"[+] Lista M3U gerada com sucesso contendo {len(m3u_lines)-1} canais!"
            )
        else:
            print("[!] Nenhuma URL de stream foi interceptada.")

        context.close()
        browser.close()


if __name__ == "__main__":
    intercept_electricnow()
