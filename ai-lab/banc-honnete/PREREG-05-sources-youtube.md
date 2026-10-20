# Pré-enregistrement 05 : 3 stratégies dont la source est vérifiable (1021, vers 00h50, avant tout calcul)
Méthode du banc (`banc.py`) : BTC, ETH et SOL ; périodes 2024-2025 et 2026 ; frais de 0,05 % par côté ; comparaison à 500 tirages au hasard.
GAGNE seulement si, sur les DEUX périodes : somme > 0, au moins 2 marchés positifs sur 3, résultat au-dessus du 95e centile du hasard, et au moins 30 trades.

## 05a. Bollinger + EMA200, chaîne YouTube « Trading Strategy Testing »
Source : script TradingView « TST Signals & Alerts » (https://cn.tradingview.com/script/nBlORgme-TST-Signals-Alerts). Le script annonce 52 % de gagnants sur 100 trades, en EURUSD 15 min, avec un ratio gain/risque de 1,5.
- Long : close > EMA200 et plus bas < bande de Bollinger basse (20, 2). Short : le miroir.
- SL et TP ne sont pas donnés en %. Je fixe un SL de 1 % et un TP de 1,5 %, ce qui respecte leur ratio de 1,5.
- Bougies de 15 min.

## 05b. ADX + EMA200, même source
Le script annonce 56 % de gagnants sur 100 trades, en 5 min, avec un ratio de 1,2.
- Long : close > EMA200 et ADX(14) qui passe au-dessus de 25. Short : close < EMA200 et ADX qui passe au-dessus de 25.
- SL 1 %, TP 1,2 %. Bougies de 15 min, car le 5 min sur 3 ans représente trop de données pour une première passe.

## 05c. RSI-2 de Connors (règles publiées par Larry Connors, version classique)
- Long seulement : close > SMA200 et RSI(2) < 10. Sortie quand close > SMA5.
- Bougies de 1 jour, comme dans l'original.
- L'étude indépendante dev.to/tessen (13 stratégies, crypto) trouve −3,7 points de base par trade après frais pour cette stratégie.

Écarts avec les sources, assumés : les marchés diffèrent (crypto au lieu du forex), et j'ai dû fixer moi-même les SL/TP qui n'étaient pas précisés.
