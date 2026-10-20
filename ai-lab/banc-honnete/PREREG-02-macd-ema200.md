# Pré-enregistrement 02 : MACD + EMA200 (version YouTube classique)
Figé le 2026-10-20 vers 04h10, avant tout calcul.

- Bougies 1h Kraken « trade », sur BTC, ETH et SOL. Périodes : 2024-2025 et 2026-01-01 → 2026-10-16.
- Indicateurs : EMA200 sur le close ; MACD(12, 26, 9).
- **Long** : la ligne MACD croise sa ligne de signal vers le haut, ces deux lignes sont sous 0 au moment du croisement, et le close est au-dessus de l'EMA200.
- **Short** : c'est le miroir (croisement vers le bas, les deux lignes au-dessus de 0, close sous l'EMA200).
- Entrée à l'open de la bougie suivante.
- SL : au niveau de l'EMA200 à l'entrée, avec une distance minimale de 0,3 %.
- TP : 1,5 fois le risque.
- Si le SL et le TP sont touchés dans la même bougie, on compte le **SL**.
- Une seule position à la fois par marché.
- Frais : 0,10 % aller-retour.
- Hasard : 500 tirages, avec le même nombre de trades, la même distance de SL/TP (même distance relative que le trade réel), des instants aléatoires et un sens aléatoire.

GAGNE seulement si les quatre conditions sont réunies :
1. la somme nette est > 0 sur les deux périodes ;
2. au moins 2 marchés sur 3 sont positifs sur 2024-2025 ;
3. le résultat dépasse le 95e centile du hasard sur les deux périodes ;
4. il y a au moins 30 trades par période.

## Résultat (1020 04h20, t02.py → t02.log) : PERD
- 2024-2025 : BTC +1,3 %, ETH −39,8 %, SOL +15,1 % ; somme −23,4 %, hasard p95 +123 %.
- 2026 : somme +2,2 %, hasard p95 +87 %.
- Taux de gagnants réel : 34 à 49 %, contre « 86 % » annoncé.
