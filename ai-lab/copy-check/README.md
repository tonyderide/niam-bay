# copy-check

Avant de déposer dans un vault Hyperliquid (ou de copier un trader), regarde **comment** il gagne, pas seulement combien.
Lecture seule, API publique, aucune clé. `python3 copycheck.py 0xADRESSE`

Indicateurs (sur les 2000 derniers fills, la limite de l'API) : win rate, payoff, net de frais, part du profit faite par 5 trades,
« une seule perte efface N gains typiques », part long, part maker, creux bootstrap, **perte latente ouverte** (invisible dans tout win rate).

## Premier passage (2026-10-17) : 15 vaults ouverts > 100k TVL, classés par APR affiché
- **5 / 15 sont perdants** sur leurs trades clos récents, alors qu'ils affichent 216 % à 378 % d'APR.
- « DailyTradeAI **Low risk** » : APR affiché 378 %, -58,7k réalisés sur 160 jours, -168k latents ouverts. Une seule perte y efface ~1400 gains typiques.
- « Bitcoin Moving Average Long/Short » (2,3 M TVL) : -835k réalisés sur 173 jours, +415k latents.
- 9 / 15 ont une perte unique qui efface plus de 100 gains typiques : le win rate élevé est le décor, la queue est le vrai risque.
- 1 seul sans drapeau (« Fund Inception »), ce qui ne prouve pas qu'il continuera.

Limites : l'APR affiché n'a pas la même fenêtre que les fills ; le PnL clos ignore dépôts/retraits ; les 2000 fills couvrent de 14 à 173 jours selon le vault. C'est un juge de **comportement**, pas une prédiction.
Détail brut : `vaults_top_apr.json`.
