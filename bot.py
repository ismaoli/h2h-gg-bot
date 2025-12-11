import requests
import json
from time import sleep
from datetime import datetime

# ===============================
# CONFIGURAÇÕES DO BOT
# ===============================

API_URL = "https://mgxdwsgbyepaasqjf6cao4qnq40zjpih.lambda-url.eu-west-1.on.aws/fifa?limit=15"
INTERVALO = 30  # segundos entre cada consulta


# ===============================
# SISTEMA DE LOG
# ===============================

def log(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {msg}", flush=True)


# ===============================
# BUSCAR PARTIDAS DA API
# ===============================

def buscar_partidas():
    try:
        resposta = requests.get(API_URL, timeout=10, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })

        # Verifica se a resposta é JSON
        content_type = resposta.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            log("⚠️ Alerta: A resposta não é JSON (instabilidade no site). Tentando novamente em 60s…")
            sleep(60)
            return None

        dados = resposta.json()
        log("✔ Dados coletados com sucesso.")
        return dados

    except Exception as e:
        log(f"❌ Erro ao buscar dados: {e}")
        sleep(60)
        return None


# ===============================
# ANALISAR PARTIDAS
# ===============================

def analisar_partidas(dados):
    try:
        if not isinstance(dados, list):
            log("⚠️ Formato inesperado de dados. Aguardando...")
            return

        for partida in dados:
            home = partida.get("home")
            away = partida.get("away")
            score_home = partida.get("home_score")
            score_away = partida.get("away_score")

            log(f"📊 {home} {score_home} x {score_away} {away}")

    except Exception as e:
        log(f"❌ Erro ao analisar partidas: {e}")


# ===============================
# LOOP PRINCIPAL DO BOT
# ===============================

def loop_principal():
    log("🚀 BOT INICIADO COM SUCESSO!")
    log("🔄 Rodando em loop contínuo...\n")

    while True:
        dados = buscar_partidas()
        
        if dados:
            analisar_partidas(dados)

        sleep(INTERVALO)


# ===============================
# INICIAR BOT
# ===============================

if __name__ == "__main__":
    loop_principal()
