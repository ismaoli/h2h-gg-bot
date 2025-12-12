import requests
import time
from datetime import datetime, timedelta
import os

# ================= CONFIGURAÇÃO =================
TELEGRAM_TOKEN = "8352928985:AAFbZ8nQ3lKLkybp01givi4zHT4kkf0k4mw"
CHAT_ID = "1855511248"  # SEU CHAT_ID do Telegram

# URL da API H2H GG
API_URL = "https://mgxdwsgbyepaasqjf6cao4qnq40zjpih.lambda-url.eu-west-1.on.aws/fifa?limit=50"

# ================= FUNÇÕES =================

# Envia mensagem para Telegram
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# Busca partidas da API
def get_matches():
    try:
        r = requests.get(API_URL, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Erro ao buscar partidas: {e}")
        return []

# Verifica se a partida começa em X minutos
def match_starts_soon(match, minutes=5):
    start = datetime.fromisoformat(match["start_time"].replace("Z", "+00:00"))
    now = datetime.utcnow()
    diff = start - now
    return 0 <= diff.total_seconds() <= (minutes*60)

# Analisa a partida e define a melhor entrada
def analyze_match(match):
    home, away = match["home"], match["away"]

    # ================== LÓGICA DE ANÁLISE ==================
    # Aqui você pode expandir usando histórico real ou estatísticas
    # Por enquanto valores simulados:
    btts = 77      # chance de Ambas Marcam (%)
    over_1_5 = 65  # chance de over 1.5 (%)
    under_2_5 = 100 - over_1_5

    # Escolhe melhor entrada
    melhor = "Ambas Marcam" if btts > over_1_5 else "Over 1,5"

    # Monta mensagem
    msg = (
        f"⚽ Partida em 5 min!\n"
        f"{home} x {away}\n"
        f"⏱ Início: {match['start_time']}\n"
        f"📊 Ambas Marcam: {btts}%\n"
        f"📊 Over 1,5: {over_1_5}%\n"
        f"📊 Under 2,5: {under_2_5}%\n"
        f"✅ MELHOR ENTRADA: {melhor}"
    )
    return msg

# ================= LOOP PRINCIPAL =================
def main():
    notified = set()
    send_telegram("🤖 Bot iniciado e monitorando próximas partidas...")

    while True:
        matches = get_matches()
        for m in matches:
            mid = m.get("external_id")
            if mid in notified:
                continue

            if match_starts_soon(m):
                msg = analyze_match(m)
                send_telegram(msg)
                notified.add(mid)

        time.sleep(60)  # checa a cada minuto

# ================= INÍCIO =================
if __name__ == "__main__":
    main()
