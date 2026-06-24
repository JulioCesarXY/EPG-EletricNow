import json
import re
import requests
from datetime import datetime, timedelta, timezone


def extract_all_electricnow_m3u8():
    session = requests.Session()

    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.electricnow.tv",
        "Referer": "https://www.electricnow.tv/live-tv/",
    }
    session.headers.update(base_headers)

    main_url = "https://www.electricnow.tv/live-tv/"
    print("[-] Conectando à página principal do ElectricNOW...")

    try:
        main_res = session.get(main_url, timeout=15)
        if main_res.status_code != 200:
            print(
                f"[!] Erro ao carregar a página principal: Status {main_res.status_code}"
            )
            return

        jwt_match = re.search(
            r'window\.EMBEDDED_JWT\s*=\s*"([^"]+)"', main_res.text
        )
        company_match = re.search(
            r'window\.COMPANY_ID\s*=\s*"([^"]+)"', main_res.text
        )

        jwt_token = (
            jwt_match.group(1)
            if jwt_match
            else "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJjb21wYW55X3N1YmRvbWFpbiI6ImVsZWN0cmljbm93IiwiZXhwIjoxNzgyMzA3NzMyLCJpYXQiOjE3ODIzMDQxMzJ9.LVxEvmnFTnE6MgoYMS9GvAmpyqD5BSErE11ZIv5iiFc"
        )
        company_id = (
            company_match.group(1) if company_match else "68e42982e052240074037638"
        )

        session.headers.update(
            {
                "Authorization": f"Bearer {jwt_token}",
                "X-Company-Id": company_id,
                "company_id": company_id,
            }
        )
        print(f"[+] Autenticação injetada nos cabeçalhos.")

    except Exception as e:
        print(f"[!] Falha na conexão inicial: {e}")
        return

    now_utc = datetime.now(timezone.utc)
    start_time = now_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time = (now_utc + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    epg_url = "https://www.electricnow.tv/api/live/epg/US"
    epg_params = {"start_time": start_time, "end_time": end_time}

    print("[-] Solicitando grade de canais ao vivo (EPG)...")

    try:
        epg_res = session.get(epg_url, params=epg_params, timeout=15)
        print(f"[i] Status HTTP da EPG: {epg_res.status_code}")

        if epg_res.status_code != 200:
            print(f"[!] Falha na EPG. Resposta do servidor:\n{epg_res.text}")
            return

        epg_data = epg_res.json()
        channels = epg_data.get("channels", [])
        print(f"[+] {len(channels)} canais localizados na grade.")

        m3u_content = "#EXTM3U\n"

        for channel in channels:
            channel_name = channel.get("name")
            video_id = channel.get("video_id")
            channel_slug = channel.get("slug")
            channel_logo = channel.get("logo", "")

            if not video_id:
                continue

            print(f"[-] Requisitando link do canal: {channel_name}...")

            stream_url = (
                f"https://www.electricnow.tv/api/live/stream/{video_id}"
            )
            stream_params = {"company_id": company_id, "device_type": "web"}

            stream_res = session.get(
                stream_url, params=stream_params, timeout=15
            )

            if stream_res.status_code == 200:
                stream_data = stream_res.json()
                m3u8_link = None

                possible_keys = [
                    "stream_url",
                    "url",
                    "hls_url",
                    "manifest_url",
                ]
                for key in possible_keys:
                    if key in stream_data:
                        m3u8_link = stream_data[key]
                        break
                    elif (
                        "data" in stream_data
                        and isinstance(stream_data["data"], dict)
                        and key in stream_data["data"]
                    ):
                        m3u8_link = stream_data["data"][key]
                        break

                if m3u8_link:
                    m3u8_link_clean = m3u8_link.split("?")[0]
                    m3u_content += f'#EXTINF:-1 tvg-id="{channel_slug}" tvg-name="{channel_name}" tvg-logo="{channel_logo}" group-title="ElectricNOW", {channel_name}\n'
                    m3u_content += f"{m3u8_link_clean}\n"
                    print(f"    [+] Link extraído com sucesso.")
                else:
                    print(
                        f"    [!] Estrutura do JSON modificada: {stream_data}"
                    )
            else:
                print(
                    f"    [!] Erro na API do Stream {video_id}: {stream_res.status_code}"
                )

        with open("electricnow.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print("[+] Arquivo 'electricnow.m3u' gerado com sucesso!")

    except Exception as e:
        print(f"[!] Erro de execução: {e}")


if __name__ == "__main__":
    extract_all_electricnow_m3u8()
