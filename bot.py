#!/usr/bin/env python3
"""H2H GG Bot - completo (versão inicial)

Funcionalidades:
- Busca HTML do site indicado (h2hggl) e tenta extrair estatísticas relevantes
- Extrai features para mercado H2H GG (Ambas Marcam)
- Possui estrutura de modelo (treino a partir de CSV) e previsão
- Calcula EV, Kelly e stake recomendado
- Registra apostas e resultados em SQLite
- Envia alertas via Telegram
- Arquivo pensado para deploy em Railway (Procfile já incluído)

ATENÇÃO: Adaptar selectors de scraping conforme a estrutura real do site.
"""
import os
import time
import math
import sqlite3
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
DATABASE = os.getenv('DB_PATH', 'bets_history.db')
H2H_URL = os.getenv('H2H_URL', 'https://h2hggl.com/en/esoccer')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '60'))

# ----------------- DB -----------------
def init_db(db_path=DATABASE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, selection TEXT, odds REAL, implied_prob REAL,
                  model_prob REAL, ev REAL, kelly_fraction REAL, stake REAL, note TEXT, timestamp INTEGER, result INTEGER)''')
    conn.commit()
    return conn

# ----------------- dataclass -----------------
@dataclass
class BetRecommendation:
    event_id: str
    selection: str
    odds: float
    implied_prob: float
    model_prob: float
    ev: float
    kelly_fraction: float
    stake: float
    note: Optional[str] = None

# ----------------- Agent core -----------------
class BettingAgent:
    def __init__(self, bankroll: float = 1000.0, kelly_fraction: float = 0.3, db_path: str = DATABASE):
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.model = None
        self.model_features = []
        self.conn = init_db(db_path)

    @staticmethod
    def decimal_odds_to_prob(odds: float) -> float:
        if odds <= 0:
            return 0.0
        return 1.0 / odds

    @staticmethod
    def expected_value(model_prob: float, odds: float, stake: float) -> float:
        payout = (odds - 1) * stake
        ev = model_prob * payout - (1 - model_prob) * stake
        return ev

    def kelly(self, model_prob: float, odds: float) -> float:
        b = odds - 1
        p = model_prob
        q = 1 - p
        if b <= 0:
            return 0.0
        f_star = (b * p - q) / b
        if f_star <= 0:
            return 0.0
        return f_star * self.kelly_fraction

    def train_model_from_csv(self, csv_path: str, feature_cols: list, target_col: str = 'won'):
        df = pd.read_csv(csv_path)
        X = df[feature_cols].values
        y = df[target_col].values
        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)
        self.model = model
        self.model_features = feature_cols
        return model

    def predict_prob(self, features: Dict[str, float]) -> float:
        if self.model is None or not self.model_features:
            raise RuntimeError('Model not trained')
        x = np.array([[features.get(c, 0.0) for c in self.model_features]])
        prob = self.model.predict_proba(x)[0][1]
        return float(prob)

    def evaluate_h2h_gg(self, event_id: str, odds_gg: float, features_for_model: Optional[Dict[str, float]] = None, min_ev_threshold: float = 0.0) -> BetRecommendation:
        implied_prob = self.decimal_odds_to_prob(odds_gg)
        if features_for_model is not None and self.model is not None:
            try:
                model_prob = self.predict_prob(features_for_model)
            except Exception:
                model_prob = implied_prob
        else:
            model_prob = implied_prob
        ev_unit = self.expected_value(model_prob, odds_gg, stake=1.0)
        kelly_fraction = self.kelly(model_prob, odds_gg)
        recommended_stake = round(kelly_fraction * self.bankroll, 2)
        note = None
        if ev_unit < min_ev_threshold:
            note = f'EV ({ev_unit:.4f}) < min threshold -> Skip'
            recommended_stake = 0.0
        elif recommended_stake <= 0:
            note = 'No positive Kelly stake.'
        return BetRecommendation(event_id=event_id, selection='H2H_GG', odds=odds_gg, implied_prob=implied_prob, model_prob=model_prob, ev=ev_unit, kelly_fraction=kelly_fraction, stake=recommended_stake, note=note)

    def record_bet(self, rec: BetRecommendation):
        c = self.conn.cursor()
        c.execute('''INSERT INTO bets (event_id, selection, odds, implied_prob, model_prob, ev, kelly_fraction, stake, note, timestamp, result)
                     VALUES (?,?,?,?,?,?,?,?,?,?,NULL)''', (rec.event_id, rec.selection, rec.odds, rec.implied_prob, rec.model_prob, rec.ev, rec.kelly_fraction, rec.stake, rec.note, int(time.time())))
        self.conn.commit()

# ----------------- scraping helpers -----------------
def fetch_html(url: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_h2hggl_html(html: str) -> dict:
    """
    Tentativa genérica de extrair alguns números que costumam aparecer em páginas H2H/BTTS.
    Os seletores podem precisar de ajuste conforme a estrutura real do site.
    Retorna um dicionário com estatísticas básicas.
    """
    soup = BeautifulSoup(html, 'html.parser')
    data = {}
    # Exemplo: procurar por textos que contenham 'Both teams to score' ou 'BTTS' e extrair percentuais
    txt = soup.get_text(separator='|')
    # heurística simples: procurar padrões numéricos próximos de 'BTTS' ou 'Both teams'
    if 'BTTS' in txt or 'Both' in txt:
        # esta heurística é frágil — ideal adaptar conforme HTML
        pass
    # Também podemos tentar encontrar tabelas
    tables = soup.find_all('table')
    if tables:
        data['tables_found'] = len(tables)
    # Placeholder: retornar o texto reduzido para inspeção manual
    data['raw_excerpt'] = txt[:2000]
    return data

def extract_h2h_gg_features(matches_stats: Dict[str, Any]) -> Dict[str, float]:
    a = matches_stats.get('teamA', {})
    b = matches_stats.get('teamB', {})
    features = {
        'a_atk_gf': float(a.get('avg_goals_for', 0.0)),
        'a_def_ga': float(a.get('avg_goals_against', 0.0)),
        'b_atk_gf': float(b.get('avg_goals_for', 0.0)),
        'b_def_ga': float(b.get('avg_goals_against', 0.0)),
        'head2head_btts': float(matches_stats.get('head2head_btts_pct', 0.0)),
        'recent_btts': float(matches_stats.get('recent_games_btts_pct', 0.0)),
    }
    features['expected_btts'] = (features['a_atk_gf'] + features['b_atk_gf']) / 2.0
    return features

# ----------------- Telegram -----------------
def send_telegram(msg: str):
    token = TELEGRAM_TOKEN
    chat_id = CHAT_ID
    if not token or not chat_id:
        print('Telegram not configured. Message would be:\n', msg)
        return
    try:
        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        print('Erro ao enviar Telegram:', e)

# ----------------- main loop -----------------
def main_loop(poll_interval=POLL_INTERVAL):
    agent = BettingAgent()
    send_telegram('🔵 H2H GG Bot iniciado')
    while True:
        try:
            html = fetch_html(H2H_URL)
            parsed = parse_h2hggl_html(html)
            # Para demonstração, pegamos um odds fictício e calculamos recomendação
            # Em produção, adapte o parser para extrair odds reais da página ou usar API de odds
            odds_example = 1.85
            # Tentativa de extrair algumas features (placeholder)
            matches_stats = {
                'teamA': {'avg_goals_for': 1.4, 'avg_goals_against': 1.1, 'btts_pct': 0.62},
                'teamB': {'avg_goals_for': 1.2, 'avg_goals_against': 1.3, 'btts_pct': 0.55},
                'head2head_btts_pct': 0.68,
                'recent_games_btts_pct': 0.70
            }
            features = extract_h2h_gg_features(matches_stats)
            rec = agent.evaluate_h2h_gg(event_id='sample_event', odds_gg=odds_example, features_for_model=features, min_ev_threshold=0.01)
            agent.record_bet(rec)
            msg = f"Recomendação: {rec.selection} | odds={rec.odds} | model_prob={rec.model_prob:.3f} | ev={rec.ev:.3f} | stake={rec.stake}"
            send_telegram(msg)
        except Exception as e:
            print('Erro no loop principal:', e)
            send_telegram(f'Erro no bot: {e}')
        time.sleep(poll_interval)

# ----------------- CLI support -----------------
def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', help='Run main loop')
    parser.add_argument('--train', help='Train model from CSV: --train path/to/historical.csv')
    parser.add_argument('--features', help='Dump feature extractor example')
    args = parser.parse_args()
    if args.train:
        agent = BettingAgent()
        print('Treinando modelo (exemplo)...')
        # Expected CSV format: features columns matching extract_h2h_gg_features and 'won' column
        feature_cols = ['a_atk_gf','b_atk_gf','expected_btts','head2head_btts','recent_btts']
        agent.train_model_from_csv(args.train, feature_cols)
        print('Modelo treinado.')
    elif args.features:
        print(json.dumps(extract_h2h_gg_features(json.loads(args.features)), indent=2))
    elif args.run:
        main_loop()
    else:
        parser.print_help()

if __name__ == '__main__':
    cli()
