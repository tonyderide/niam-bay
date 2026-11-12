# PREREG-75 — Cent stratégies contre la grille W5, avec correction du hasard

Écrit le 12/11/2026 à 06h17 (heure de Paris), **avant tout calcul des 100 stratégies**. Code : `ai-lab/cent-strategies/moteur.py` et `t75.py` (commités avec ce fichier). Résultat prévu : `ai-lab/cent-strategies/RESULTAT.md`, `t75.json`, `t75.log`.

## Pourquoi
Tony : « cherche encore une meilleure stratégie, 100 fois ». Essayer 100 stratégies et garder la meilleure, c'est presque sûr d'en trouver une « bonne » par chance. Ce protocole mesure combien vaut « la meilleure de 100 » quand il n'y a rien à trouver (prix mélangés), et ne retient une gagnante que si elle dépasse ce niveau **et** tient sur des données jamais vues.

## Ce qui a déjà été fait AVANT d'écrire (pré-vol, pas de résultat nouveau)
- Le moteur de grille `simg` est une copie de `t73.sim` avec des paramètres en plus. Réglages W5 : il redonne **+881,4 € (P1) / −245,0 € (P2)**, comme PREREG-73/74, et W5F redonne −90,7 € (PREREG-74 : −91 €). Ces chiffres étaient déjà connus.
- Le moteur directionnel `simd` : achat-conservation sans garde-fou sur LINK P1 = 785,6 € contre 786,5 € pour le prix seul (écart = frais). Contrôle de mécanique uniquement.
- Le tirage des 24 paires neuves (graine 75) a été fait : il ne regarde que la date de fin des données, pas les résultats.

## Données
- 4 paires en service SOL, LINK, ADA, DOT et 6 paires de PREREG-74 ATOM, AVAX, BCH, BNB, XRP, LTC : bougies 1 min Binance (les mêmes fichiers que t74 ; SOL = `dca-martingale/refait/donnees/SOLUSDT-1m.npy`, les autres = `m1/<X>.npy` dans le bloc-notes de la session Martin du 03/11, SHA-256 notés dans t75.log).
- 24 paires neuves tirées au sort dans le jeu 1 h (`dca-martingale/refait/donnees/`, 253 perpétuels Binance USDT cotés au 01/01/2024, morts compris, coupés après 48 h de prix figé). Exclues avant tirage : les 10 paires ci-dessus, DOGE (martingale en service), BTC, ETH (PREREG-30), USDC, BTCDOM, DEFI, FOOTBALL, BLUEBIRD (stable ou indices). Il reste 235 candidates. Graine `numpy.random.default_rng(75)` ; on garde, dans l'ordre du tirage, les 24 premières qui ont des données au moins jusqu'au 01/05/2024. Tirées : **QNT, GMX, 1000SHIB, MKR, POWR, CAKE, CKB, CYBER, LIT, STMX, LQTY, BEL, ICP, PYTH, BAND, CELR, MATIC, RSR, KNC, BNX, GMT, ONE, LOOM, BLZ**. Ces paires n'ont que des bougies 1 h : toutes les stratégies y tournent sur le moteur 1 h (W5 compris). Diagnostic rapporté : écart entre moteur 1 min et moteur 1 h sur les 4 paires en P1.
- Périodes : **P1** = 01/02/2024 → 31/12/2025 ; **P2** = 01/01 → 30/09/2026.
- Portage du financement : **exclu**. Le jeu n'a pas les taux de financement, et la famille est déjà jugée (PREREG-27, 40, 42, 43).

## Règles communes (exécutables par Martin)
- Perpétuels, 1 000 € par paire, levier ≤ 10.
- Frais Kraken : taker 0,05 % (marché, stops), maker 0,02 % (limites).
- Mêmes garde-fous R+ partout : fermeture si l'équité tombe à 85 % de celle du départ de la grille ou de l'entrée du trade (sauf les 2 variantes qui changent ce seuil), pause 24 h, paire arrêtée si le cash passe sous 600 €.
- Grilles : moteur 1 min de t73 (W5 = écart 5 %, 5 niveaux, notionnel 1 000 € par niveau, plafond 5×, disjoncteur RSI<25, protection 15 min, recentrage).
- Directionnelles : signal sur la bougie 1 h **close**, exécution au marché à l'ouverture de l'heure suivante. Stops et objectifs dans la bougie, ordre pessimiste (bougie haussière O→B→H→C, baissière O→H→B→C ; le stop est testé avant l'objectif). ATR journalier = celui de la dernière journée close. Levier par défaut 2. Pas de financement (comme t73/t74).

## Les 100 stratégies (liste exacte, figée)
Familles : grilles W 1-50 ; suivi de tendance 51-78 ; retour à la moyenne 79-90 ; sens EMA PREREG-30 91-99 ; référence 100.
| n° | Nom | Règle |
|---|---|---|
| 1 | W5 | grille en service (témoin) : écart 5 %, 5 niveaux, plafond 5× |
| 2 | W3 | écart 3 % |
| 3 | W4 | écart 4 % |
| 4 | W6 | écart 6 % |
| 5 | W8 | écart 8 % |
| 6 | W12 | écart 12 % |
| 7 | W15 | écart 15 % |
| 8 | W5-N3 | 5 %, 3 niveaux, plafond 3× |
| 9 | W5-N7 | 5 %, 7 niveaux, plafond 7× |
| 10 | W5-N9 | 5 %, 9 niveaux, plafond 9× |
| 11 | W3-N7 | 3 %, 7 niveaux, plafond 7× |
| 12 | W5-x0.5 | 5 %, demi-taille par niveau (plafond 2,5×) |
| 13 | W5-x2 | 5 %, double taille par niveau (plafond 10×) |
| 14 | W5-cap2 | 5 %, plafond d'exposition 2× |
| 15 | W5-cap3 | 5 %, plafond 3× |
| 16 | W3-x2 | 3 %, double taille (plafond 10×) |
| 17 | W5-L | 5 %, long seul |
| 18 | W5-S | 5 %, short seul |
| 19 | W3-L | 3 %, long seul |
| 20 | W3-S | 3 %, short seul |
| 21 | W8-L | 8 %, long seul |
| 22 | W8-S | 8 %, short seul |
| 23 | W3-F | 3 %, filtre de sens EMA50/200 1 h |
| 24 | W8-F | 8 %, filtre EMA50/200 |
| 25 | W5-F20 | 5 %, filtre de sens EMA20/100 1 h |
| 26 | W5-F200 | 5 %, sens = clôture 1 h vs EMA200 |
| 27 | W5-A20 | 5 %, entrées seulement si ADX14 1 h < 20 |
| 28 | W5-A25 | 5 %, ADX < 25 |
| 29 | W5-A30 | 5 %, ADX < 30 |
| 30 | W3-A25 | 3 %, ADX < 25 |
| 31 | W5-calme | 5 %, entrées seulement si vol. 24 h < médiane 30 j |
| 32 | W5-agité | 5 %, entrées seulement si vol. 24 h > médiane 30 j |
| 33 | W3-calme | 3 %, vol. calme |
| 34 | W5-L-hausse | 5 %, long seul, entrées seulement si EMA50 > EMA200 |
| 35 | W3-L-hausse | 3 %, long seul, EMA50 > EMA200 |
| 36 | W-ATR1 | écart = 1 × ATR14 journalier |
| 37 | W-ATR2 | écart = 2 × ATR journalier |
| 38 | W-ATR3 | écart = 3 × ATR journalier |
| 39 | W5-sansDJ | 5 %, sans disjoncteur RSI<25 |
| 40 | W5-sansProt | 5 %, sans protection SL/TP 15 min |
| 41 | W5-gf80 | 5 %, garde-fou à −20 % |
| 42 | W5-gf90 | 5 %, garde-fou à −10 % |
| 43 | W5-miroir | 5 %, 3 achats / 2 ventes |
| 44 | W3-miroir | 3 %, 3 achats / 2 ventes |
| 45 | W5-A25-F | 5 %, ADX < 25 + filtre EMA50/200 |
| 46 | W8-N7 | 8 %, 7 niveaux, plafond 7× |
| 47 | W5-S-baisse | 5 %, short seul, entrées seulement si EMA50 < EMA200 |
| 48 | W12-x2 | 12 %, double taille (plafond 10×) |
| 49 | W4-L | 4 %, long seul |
| 50 | W6-A25 | 6 %, ADX < 25 |
| 51 | X12/26 | croisement EMA 12/26 h, toujours en position |
| 52 | X20/50 | croisement EMA 20/50 h |
| 53 | X50/200 | croisement EMA 50/200 h |
| 54 | X10/30 | croisement EMA 10/30 h |
| 55 | X20/50-L | EMA 20/50, long seul |
| 56 | X50/200-L | EMA 50/200, long seul |
| 57 | X20/50-ATR | EMA 20/50 + stop suiveur 3 ATR jour |
| 58 | X50/200-ATR | EMA 50/200 + stop suiveur 3 ATR jour |
| 59 | X20/50-L5 | EMA 20/50, levier 5 |
| 60 | X50/200-L1 | EMA 50/200, levier 1 |
| 61 | DC24 | cassure Donchian 24 h, sortie canal 12 h |
| 62 | DC72 | Donchian 72 h / 36 h |
| 63 | DC168 | Donchian 168 h / 84 h |
| 64 | DC480 | Donchian 480 h / 240 h |
| 65 | DC168-ATR3 | Donchian 168 h + stop suiveur 3 ATR jour |
| 66 | DC72-ATR2 | Donchian 72 h + stop suiveur 2 ATR jour |
| 67 | DC168-L | Donchian 168 h, long seul |
| 68 | DC480-L1 | Donchian 480 h, levier 1 |
| 69 | DC480-L5 | Donchian 480 h, levier 5 |
| 70 | DC168-SL5TP10 | Donchian 168 h, SL 5 %, TP 10 % |
| 71 | ST2 | stop-and-reverse 2 ATR jour (supertrend) |
| 72 | ST3 | supertrend 3 ATR jour |
| 73 | TSM7 | momentum 7 jours (signe), revu chaque jour |
| 74 | TSM30 | momentum 30 jours |
| 75 | TSM7-L | momentum 7 jours, long seul |
| 76 | MACD | MACD 48/104/36 h, toujours en position |
| 77 | MACD-L200 | MACD, long seul au-dessus de l'EMA200 h |
| 78 | VB3 | mouvement horaire > 3 ATR h : suivre 24 h, SL 3 % |
| 79 | RSI30/70 | RSI14 h < 30 achat, > 70 vente, sortie à 50, SL 5 % |
| 80 | RSI30-L | RSI14 h < 30 achat seul, SL 5 % |
| 81 | RSI20/80 | RSI 20/80, SL 5 % |
| 82 | RSI30/70-E200 | RSI 30/70 dans le sens de l'EMA200 h, SL 5 % |
| 83 | RSI30/70-L5 | RSI 30/70, levier 5, SL 5 % |
| 84 | BB20/2 | Bollinger 20 h 2σ : contre la sortie de bande, sortie à la moyenne, SL 5 % |
| 85 | BB20/3 | Bollinger 20 h 3σ, SL 5 % |
| 86 | BB20/2-L | Bollinger 20/2, long seul, SL 5 % |
| 87 | BB20/2.5-E200 | Bollinger 20/2,5 dans le sens de l'EMA200 h, SL 5 % |
| 88 | BB20/2-L5 | Bollinger 20/2, levier 5, SL 5 % |
| 89 | BBX20/2 | Bollinger 20/2 en cassure (dans le sens), sortie à la moyenne |
| 90 | BB480/2 | Bollinger lent 480 h 2σ, SL 8 % |
| 91 | E30-L1 | PREREG-30 figé : EMA50 h, SL 5 %, trailing +3 %/1 %, levier 1 |
| 92 | E30-L2 | PREREG-30 figé, levier 2 |
| 93 | E30-L5 | PREREG-30 figé, levier 5 |
| 94 | E30-EMA20 | PREREG-30, EMA20 |
| 95 | E30-EMA200 | PREREG-30, EMA200 |
| 96 | E30-3/2/1 | PREREG-30, SL 3 %, trailing +2 %/1 % |
| 97 | E30-8/5/2 | PREREG-30, SL 8 %, trailing +5 %/2 % |
| 98 | E30-mart | PREREG-30 + martingale ×2 plafonnée à 3 doublements (base levier 1) |
| 99 | E30-ADX25 | PREREG-30, seulement si ADX14 h > 25 |
| 100 | BH | achat-conservation, levier 1 (mêmes garde-fous) |

Déjà jugées ailleurs dans le registre, refaites ici dans un cadre nouveau (4 paires, garde-fous R+, frais Kraken) : la famille EMA (dont PREREG-30, n° 91, le témoin de cette famille), MACD (PREREG-02), stop suiveur (04), supertrend (03). W5 (n° 1) est le témoin du banc. W7, W10, W5R, W5P et W5F (PREREG-74) ne sont pas refaits.

## Protocole
1. **Choix sur P1 seulement**, 4 paires en service. X\* = la stratégie au total P1 le plus élevé parmi celles **sans paire arrêtée ou liquidée et avec une baisse du portefeuille meilleure que −30 %** (règle de PREREG-74). W5 est candidate.
2. **Témoin hasard (correction des essais multiples)** : 50 répétitions (graine 7500). À chaque fois, les 4 paires de 01/2024 à 12/2025 sont mélangées. Les bougies 1 min sont permutées en gardant leur forme (haut, bas, clôture par rapport à l'ouverture), après retrait de la dérive moyenne. La volatilité reste, la tendance et toute structure temporelle partent. Les 100 stratégies tournent sur P1 mélangée et on note **le maximum des 100 totaux**, sans filtre d'éligibilité, ce qui est plus sévère. Seuil = 95e centile de ces 50 maxima.
3. **Contrôles, une seule fois**, sur X\* (et W5 pour comparaison) :
   - P2, 4 paires ;
   - les 30 paires neuves (6 + 24), P1 et P2.

## Critère de victoire (pré-écrit)
- **C1** : X\* ≠ W5.
- **C2** : total P1 de X\* > 95e centile du « meilleur de 100 » sous hasard.
- **C3** : P2, 4 paires : total de X\* > 0 **et** > celui de W5.
- **C4** : paires neuves, P1 + P2 cumulés sur les 30 paires : total de X\* > 0, > celui de W5, et au moins la moitié des paires positives (P1 + P2 cumulés par paire).

**Verdicts :**
- **TIENT** si le témoin est bon et que C1 à C4 passent. Même dans ce cas, je ne recommande rien en réel : c'est Tony qui décide.
- **MIEUX QUE W5 SANS PREUVE** si X\* ≠ W5 et bat W5 sur P2 (4 paires) et sur les paires neuves, sans tout passer.
- **NON** sinon. Si X\* = W5 : « NON, W5 reste la meilleure sur P1 », et on dit si W5 elle-même dépasse le seuil du hasard.
- **NON CONCLUANT** si W5 ne redonne pas +881,4 / −245,0.

Rapporté aussi, pour information et sans verdict : le tableau des 100 sur P1, le top 10 de P1 avec leur tenue hors échantillon, la meilleure hors échantillon (à ne pas croire : elle est choisie après coup), le diagnostic 1 min / 1 h.

## Prédiction
- X\* est une grille ou une stratégie à levier élevé : X20/50-L5, DC480-L5 ou W5-x2.
- X\* ne dépasse pas le 95e centile du hasard.
- Sur P2 et les paires neuves, le top 10 de P1 est à peu près au hasard.
- Verdict prédit : **NON** (ou MIEUX QUE W5 SANS PREUVE, sans plus).
- Le « meilleur de 100 » sous hasard sera positif, de quelques centaines d'euros, alors que la médiane sera négative à cause des frais.

## Relecture d'équité (faite avant le calcul)
- **Coûts égaux** : mêmes frais taker et maker pour toutes, mêmes garde-fous, même capital, levier ≤ 10. Le financement est ignoré pour toutes ; il aurait favorisé ou pénalisé les positions tenues longtemps.
- **Ordre pessimiste dans la bougie** : les grilles gardent la règle de t73. Pour les directionnelles, le stop passe avant l'objectif. Le trailing ne monte qu'avec la jambe favorable et n'est testé qu'à la jambe défavorable suivante.
- **Pas de fuite du futur** : indicateurs calculés sur des heures ou des jours clos avant la décision. Les filtres de grille lisent l'heure close précédente (`prev`), les signaux directionnels sont exécutés à l'ouverture suivante, et les paires neuves sont tirées sans regarder les résultats.
- **Biais connus** :
  - Les grilles sont simulées à la minute, les directionnelles à l'heure, avec ordre pessimiste : léger désavantage pour les directionnelles qui ont des stops serrés.
  - Les 24 paires 1 h passent toutes par le moteur 1 h.
  - Données Binance, pas Kraken.
  - Le témoin hasard retire la tendance. Une stratégie qui gagne seulement grâce à la dérive (achat-conservation en hausse) peut donc dépasser le seuil sans « talent ». C'est pour ça que C3 et C4 (hors échantillon) sont exigés en plus de C2.
- Budget : hasard 50 × 100 × 4 paires, environ 1 h de calcul sur 2 cœurs (`taskset -c 0,1`).
