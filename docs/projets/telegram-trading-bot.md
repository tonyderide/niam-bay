# Telegram Trading Bot

## Statut : READY (attend token)

## Quoi
Bot Telegram qui envoie des alertes en temps reel sur les trades Martin Grid.
- Fills (buy/sell avec prix, round-trips, profit)
- Grid stops (maxloss)
- Resume quotidien a 18h

## Ou
VM Oracle : `/home/ubuntu/telegram-bot.py`
Service systemd : `telegram-bot.service` (disabled)

## Comment activer
1. Creer bot via @BotFather sur Telegram
2. Editer `/home/ubuntu/.telegram-env` avec le token et chat_id
3. `sudo systemctl enable --now telegram-bot`

## Architecture
- Python 3, zero dependance externe (urllib only)
- Poll Martin API (`localhost:8081/api`) toutes les 30s
- Envoie via Bot API Telegram (HTTPS)
- Systemd avec restart auto

## Date
2026-03-23
