# H2H GG Bot

Versão completa inicial pronta para deploy no Railway.

## Conteúdo
- bot.py -> código principal
- requirements.txt -> dependências
- Procfile -> para Railway

## Como usar
1. Crie um repositório no GitHub (ex: `h2h-gg-bot`) e envie estes arquivos.
2. No Railway, conecte este repositório e faça deploy.
3. Defina variáveis de ambiente no Railway:
   - TELEGRAM_TOKEN (opcional para notificações)
   - CHAT_ID (opcional)
   - H2H_URL (opcional, padrão: https://h2hggl.com/en/esoccer)
   - POLL_INTERVAL (segundos, padrão 60)
4. Opcional: treine um modelo com CSV e use `--train your.csv`.

## Banco de dados
O bot usa SQLite (`bets_history.db`) por padrão. Você pode trocar para outro DB editando o código.

## Docker (exemplo)
Foi incluído um `Dockerfile` para construir uma imagem simples.
