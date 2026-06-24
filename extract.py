import re
import requests

def fetch_streams():
    # 1. Obter um novo token diretamente do HTML
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://www.electricnow.tv/live-tv/"
    }
    
    print("[-] Obtendo token atualizado do servidor...")
    response = session.get("https://www.electricnow.tv/live-tv/", headers=headers)
    
    # Regex para capturar o JWT no código fonte
    token_match = re.search(r'window\.EMBEDDED_JWT\s*=\s*"([^"]+)"', response.text)
    if not token_match:
        print("[!] Não foi possível encontrar o token JWT no HTML.")
        return
    
    token = token_match.group(1)
    print("[+] Token capturado com sucesso.")

    # 2. Configurar headers com o token fresco
    headers.update({
        "Authorization": f"Bearer {token}",
        "x-access-token": token,
        "Content-Type": "application/json"
    })

    # 3. Consultar a EPG com o token
    epg_url = "https://www.electricnow.tv/api/live/epg/US"
    # Adicionamos start_time e end_time como o site faz
    params = {
        "start_time": "2026-06-24T12:00:00.000Z",
        "end_time": "2026-06-25T12:00:00.000Z"
    }
    
    res = session.get(epg_url, headers=headers, params=params)
    
    if res.status_code != 200:
        print(f"[!] Erro ao acessar EPG: {res.status_code} - {res.text}")
        return

    channels = res.json().get("channels", [])
    
    # 4. Loop para extrair streams
    for ch in channels:
        video_id = ch.get("video_id")
        if video_id:
            stream_url = f"https://www.electricnow.tv/api/live/stream/{video_id}"
            stream_res = session.get(stream_url, headers=headers, params={"company_id": "68e42982e052240074037638"})
            
            if stream_res.status_code == 200:
                data = stream_res.json()
                final_link = data.get("stream_url") or data.get("url")
                print(f"[+] {ch['name']}: {final_link}")
            else:
                print(f"[!] Erro ao capturar stream do canal {ch['name']}")

if __name__ == "__main__":
    fetch_streams()
