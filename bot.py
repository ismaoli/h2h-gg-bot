import time
import requests
import json
import os
import traceback
from datetime import datetime

# ----------------------------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------------------------
API_URL = "https://h2hggl.com/en/esoccer"
INTERVALO = 20  # segundos entre cada consulta
LOG = True

def log(msg):
    if LOG:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ----------------------------------------------------------
# FUNÇÃO PARA BUSCAR DADOS DO SITE
# ----------------------------------------------------------
def buscar_partidas():
    try:
        resposta = requests.get(API_URL, timeout=10)
        dados = resposta.text

        if "<html" in dados.lower():
            log("❌ Erro: O site retornou HTML (bloqueio ou mudança de layout).")
            return None

        log("✔ Dados coletados do site com sucesso.")
        return dados

    except Exception as e:
        log(f"❌ Erro ao buscar dados: {e}")
        return None

# ----------------------------------------------------------
# PROCESSAMENTO DO MODELO (Simples por enquanto)
# ----------------------------------------------------------
def processar_dados(bruto):
    """
    Aqui você coloca sua lógica real:
    - Extrair estatísticas
    - Calcular padrões
    - Encontrar valor
    - Ler odds
    - Criar predições
    """

    # Mock simples só para testar o loop
    try:
        log("🔎 Processando dados brutos… (mock)")
        return {"ok": True}

    except Exception as e:
        log(f"❌ Erro ao processar dados: {e}")
        return None

# ----------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------
def loop_bot():
    log("🚀 BOT INICIADO COM SUCESSO!")
    log("🔄 Rodando em loop contínuo...")

    while True:
        try:
            # 1. Buscar dados
            dados = buscar_partidas()

            if dados:
                # 2. Processar dados
                processar_dados(dados)

            # Aguardar próximo ciclo
            time.sleep(INTERVALO)

        except Exception as e:
            log("🔥 ERRO NO LOOP PRINCIPAL:")
            log(traceback.format_exc())
            time.sleep(5)

# ----------------------------------------------------------
# CLI
# ----------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--run", action="store_true", help="Executar loop principal")
    parser.add_argument("--train", type=str, help="Treinar modelo")
    parser.add_argument("--features", type=str, help="Dump de features")

    args = parser.parse_args()

    if args.run:
        loop_bot()
    else:
        print("Use: python bot.py --run")
