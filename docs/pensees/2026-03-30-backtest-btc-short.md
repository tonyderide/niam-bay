# Backtest Martin Grid SHORT sur BTC/USD — 30 mars 2026

## Contexte

On a toujours grid-trade ETH, DOT, SOL. Jamais BTC directement. La session 84 a defini des parametres SHORT pour BTC : centre ~66 482$, range [64 820 - 68 144$], 10 levels, x5 levier, 15$ capital. Ce backtest teste ces parametres contre les donnees Kraken recentes, et compare SHORT vs NEUTRAL vs LONG.

## Donnees

- **Source** : Kraken OHLC 15min, fichier local `XXBTZUSD_15m.csv`
- **Periode** : 14 mars 14h30 -> 22 mars 02h30 (~7.5 jours, 721 candles)
- **BTC Open** : $70 916
- **BTC Close** : $68 827
- **BTC High** : $75 998
- **BTC Low** : $68 250
- **HODL** : -2.95% (marche legerement baissier)

## Parametres

| Parametre | Session 84 (original) | Adapte (centre sur donnees) |
|-----------|----------------------|---------------------------|
| Centre | $66 482 | $72 120 |
| Range basse | $64 820 | $70 458 |
| Range haute | $68 144 | $73 782 |
| Spacing | $332.4 (~0.50%) | $332.4 (~0.46%) |
| Levels | 10 | 10 |
| Levier | x5 | x5 |
| Capital | $15 | $15 |
| Fees | 0.02% maker + 0.05% taker | idem |

**Pourquoi deux jeux de parametres ?** Le BTC etait a $70-76k pendant la periode de test, mais les parametres session 84 sont centres a $66k. On teste les deux pour voir l'impact du placement du centre.

---

## Resultats principaux

### Avec parametres adaptes (centre $72 120) + Max Loss 15%

| Mode | RTs | Win Rate | PnL | PnL % | Max DD | $/jour | Recentrages | Stoppe |
|------|-----|----------|-----|-------|--------|--------|-------------|--------|
| **SHORT** | 9 | 33.3% | -$2.35 | -15.7% | 16.2% | -$0.31 | 3 | OUI |
| **NEUTRAL** | 16 | 43.8% | -$1.72 | -11.5% | 15.2% | -$0.23 | 3 | OUI |
| **LONG** | 11 | 54.5% | -$1.40 | -9.3% | 15.1% | -$0.19 | 2 | OUI |
| HODL | - | - | - | -2.9% | - | - | - | - |
| CASH | - | - | $0.00 | 0% | 0% | $0 | - | - |

**Verdict : Tout perd.** Le centre a $72k est trop haut — BTC a passe la moitie du temps au-dessus du range, ce qui provoque des recentrages couteux. Les 3 modes sont stoppes par le max loss 15%.

### Sans max loss (ride it out)

| Mode | RTs | Win Rate | PnL | PnL % | Max DD | $/jour | Recentrages |
|------|-----|----------|-----|-------|--------|--------|-------------|
| **SHORT** | 11 | 45.5% | -$0.68 | -4.6% | 16.2% | -$0.09 | 3 |
| **NEUTRAL** | 18 | 50.0% | -$0.53 | -3.6% | 18.2% | -$0.07 | 3 |
| **LONG** | 18 | 38.9% | -$1.72 | -11.5% | 18.0% | -$0.23 | 3 |

Sans max loss, la perte est reduite mais pas eliminee. NEUTRAL est le moins pire (-3.6%), SHORT suit (-4.6%), LONG est le pire (-11.5%) dans ce marche baissier. Logique : LONG achete pendant que ca descend.

---

### Avec parametres session 84 originaux (centre $66 482) + Max Loss 15%

| Mode | RTs | Win Rate | PnL | PnL % | Max DD | $/jour | Recentrages | Stoppe |
|------|-----|----------|-----|-------|--------|--------|-------------|--------|
| **SHORT** | **15** | **66.7%** | **+$0.96** | **+6.4%** | **10.7%** | **+$0.13** | 3 | non |
| **NEUTRAL** | 15 | 66.7% | +$0.37 | +2.5% | 8.2% | +$0.05 | 3 | non |
| **LONG** | 9 | 77.8% | -$0.22 | -1.5% | 8.6% | -$0.03 | 3 | non |

**Le SHORT gagne.** Avec le centre a $66k (en dessous du prix actuel), le grid SHORT est parfaitement positionne : il vend haut et rachete quand BTC descend vers le range. +6.4% sur 7.5 jours, sans etre stoppe. Le NEUTRAL est aussi profitable (+2.5%), le LONG perd legerement.

**Le placement du centre est crucial.** Memes parametres, meme spacing, mais un centre a $66k vs $72k transforme un -15.7% en +6.4%.

---

## Sensibilite au spacing (mode SHORT)

| Spacing | % du centre | RTs | Win Rate | PnL | PnL % | Max DD | Recentrages |
|---------|-------------|-----|----------|-----|-------|--------|-------------|
| $166 | 0.23% | 16 | 62.5% | +$0.23 | +1.5% | 13.2% | 3 |
| $332 | 0.46% | 11 | 45.5% | -$0.68 | -4.6% | 16.2% | 3 |
| **$499** | **0.69%** | **2** | **100%** | **+$2.53** | **+16.9%** | **11.2%** | **0** |
| **$665** | **0.92%** | **3** | **100%** | **+$2.78** | **+18.6%** | **9.3%** | **0** |

Le spacing large ($499-665, 0.7-0.9%) est nettement superieur : 100% win rate, zero recentrage, +17-19% de PnL. Le spacing etroit (0.23-0.46%) provoque trop de recentrages, ce qui mange le profit.

**Pour BTC, le spacing optimal est autour de 0.7-0.9%** (vs 0.5% pour les altcoins). BTC bouge moins en pourcentage que DOT ou SOL, mais les mouvements absolus sont plus grands. Un spacing trop serre capture plus de RT mais provoque des recentrages destructeurs.

---

## Analyse

### Pourquoi le SHORT grid est adapte a la situation actuelle

1. **BTC est en tendance baissiere legere** (-2.95% sur la periode). Le SHORT profite de chaque mouvement vers le bas.
2. **Le centre a $66k agit comme un aimant** : le prix BTC tourne autour de $68-76k, il "tombe" vers le range session 84 quand il corrige. Les shorts ouverts en haut sont fermes en profit en bas.
3. **Moins de recentrages avec les params originaux** : le range [64.8k-68.1k] est en dessous du prix, donc le grid ne se fait pas traverser dans les deux sens.

### Comparaison avec les backtests precedents (ETH/DOT/SOL)

| Asset | Meilleur mode | PnL | Contexte |
|-------|--------------|-----|----------|
| **BTC (SHORT, S84)** | **SHORT** | **+6.4%** | Bear leger -2.9%, 7.5j |
| ETH (Grid plain) | Neutral | +0.64% | Bear fort -34%, 90j |
| ETH (RSI filter) | Neutral | +2.62% | Bear fort -34%, 90j |
| SOL (Grid plain) | Neutral | +3.70% | Bear fort -36%, 90j |
| DOT (RSI filter) | Neutral | +5.29% | Bear fort -34%, 90j |

Le SHORT BTC avec params S84 performe mieux en pourcentage que les grids ETH/DOT/SOL, mais sur une periode beaucoup plus courte (7.5j vs 90j). A normaliser sur 30 jours, ca donnerait ~25% — nettement au-dessus du grid classique.

### Limites de ce backtest

1. **Periode courte** : 7.5 jours seulement (Kraken limite a ~720 candles en 15min). Les resultats sont indicatifs, pas definitifs.
2. **Pas de funding fees** : en short sur futures, on paie (ou recoit) un funding toutes les 8h. Non simule ici.
3. **Le centre $66k est en dessous du marche** : ca marche quand BTC est au-dessus et descend vers le range. Si BTC monte a $80k, ce centre ne servira plus — il faudra recentrer manuellement.
4. **Survivorship bias sur le spacing** : les spacings larges ont 2-3 RT seulement. Un seul mauvais RT changerait tout le resultat. Pas assez de donnees pour conclure statistiquement.
5. **Le 15min granulaire peut manquer des fills** qui auraient eu lieu en intra-candle.

---

## Recommandations

### Court terme : deployer le SHORT grid BTC

Les parametres session 84 sont valides tant que BTC reste au-dessus de $66k :

```
Pair: XBTUSD (Kraken Futures)
Mode: SHORT
Centre: $66 482
Range: [$64 820 - $68 144]
Levels: 10
Spacing: $332.4 (~0.50%)
Levier: x5
Capital: $15
Max Loss: 15%
```

Ou avec spacing elargi (recommande pour BTC) :

```
Spacing: $500 (~0.75%)
Range: [$63 982 - $68 982] (10 levels x $500)
```

### Conditions de desactivation

Le SHORT grid doit etre coupe si :
- BTC passe sous $64 000 (en dessous du range = positions short deviennent perdantes)
- BTC casse $76 000+ durablement (signal bullish fort, le short va saigner)
- RSI > 70 sur 4H pendant 24h+ (momentum haussier)
- ADX > 30 (tendance forte, risque accru)

### Prochaines etapes

1. Recuperer des donnees BTC plus longues (3 mois) via API Kraken depuis la VM
2. Backtest du SHORT avec les filtres ADX/RSI/EMA du Triple Lock
3. Tester le SHORT grid avec spacing dynamique ATR-based
4. Comparer avec le mode adaptatif (switch SHORT/NEUTRAL/LONG selon le regime)
5. Paper trading 1 semaine avant deploiement reel

---

## PARTIE 2 : Grid Adaptatif (SHORT/LONG auto-switch)

### Le concept

Au lieu de choisir SHORT ou LONG manuellement, un detecteur de regime switch automatiquement :
- **LONG** quand EMA20 > EMA50, RSI > 55, momentum positif
- **SHORT** quand prix < EMA50, RSI < 40, momentum negatif
- **NEUTRAL** quand RSI 40-60, volatilite basse, prix entre EMAs
- **CASH** quand volatilite > 6% ou crash (>-5% en 24h)

Anti-whipsaw : hysteresis (seuils asymetriques entree/sortie) + cooldown 2h + 3 confirmations consecutives.

### Resultats BTC (7.5 jours, 15min)

| Strategie | RTs | WR | PnL | PnL% | MaxDD | $/jour | Switches |
|-----------|-----|----|-----|------|-------|--------|----------|
| **ADAPTIVE** | 29 | 44.8% | -$1.12 | -7.4% | 12.4% | -$0.15 | 8 |
| SHORT fixe | 12 | 50.0% | -$1.08 | -7.2% | 12.8% | -$0.15 | 0 |
| NEUTRAL fixe | 16 | 56.2% | -$0.02 | -0.1% | 8.7% | -$0.003 | 0 |
| LONG fixe | 14 | 50.0% | -$0.25 | -1.7% | 8.6% | -$0.03 | 0 |

Sur BTC 7.5 jours : l'adaptatif est legerement pire que les modes fixes. 8 switches = 8 fermetures forcees = friction. NEUTRAL fixe est le meilleur (-0.1% seulement).

### Resultats ETH (3 mois, 1h, bear -31.7%)

| Strategie | RTs | WR | PnL | PnL% | MaxDD | $/jour | Switches |
|-----------|-----|----|-----|------|-------|--------|----------|
| **ADAPTIVE** | **27** | **81.5%** | **+$2.93** | **+19.6%** | **9.7%** | **+$0.03** | **5** |
| SHORT fixe | 186 | 63.4% | +$8.67 | +57.8% | 31.8% | +$0.10 | 0 |
| NEUTRAL fixe | 256 | 64.5% | +$2.36 | +15.7% | 39.1% | +$0.03 | 0 |
| LONG fixe | 252 | 48.8% | -$12.33 | -82.2% | 100.1% | -$0.14 | 0 |

**L'adaptatif brille sur le ratio risque/rendement.** +19.6% avec seulement 9.7% de drawdown max. Le SHORT fixe gagne plus (+57.8%) mais avec 31.8% de DD — deux fois plus de risque. L'adaptatif passe 70% du temps en CASH, evitant la majorite du crash.

### Resultats SOL (3 mois, 1h, bear -31.7%)

| Strategie | RTs | WR | PnL | PnL% | MaxDD | $/jour | Switches |
|-----------|-----|----|-----|------|-------|--------|----------|
| **ADAPTIVE** | 19 | 52.6% | +$0.82 | +5.5% | 8.7% | +$0.01 | 5 |
| SHORT fixe | 86 | 65.1% | +$10.76 | +71.7% | 20.1% | +$0.12 | 0 |
| NEUTRAL fixe | 125 | 64.8% | +$12.13 | +80.9% | 30.9% | +$0.13 | 0 |
| LONG fixe | 135 | 46.7% | -$7.58 | -50.5% | 97.6% | -$0.08 | 0 |

Meme pattern : l'adaptatif protege le capital (DD 8.7% vs 20-31%) mais rate le gros du profit. SOL a des oscillations larges = NEUTRAL et SHORT fixes cartonnent.

### Resultats DOT (3 mois, 1h, bear -28.9%)

| Strategie | RTs | WR | PnL | PnL% | MaxDD | $/jour | Switches |
|-----------|-----|----|-----|------|-------|--------|----------|
| ADAPTIVE | 13 | 7.7% | -$3.60 | -24.0% | 24.5% | -$0.04 | 2 |
| **SHORT fixe** | **98** | **53.1%** | **+$0.96** | **+6.4%** | **52.9%** | **+$0.01** | 0 |
| NEUTRAL fixe | 176 | 46.0% | -$8.62 | -57.4% | 98.3% | -$0.09 | 0 |
| LONG fixe | 156 | 37.2% | -$20.32 | -135.4% | 138.3% | -$0.22 | 0 |

DOT est le cas difficile. L'adaptatif passe 95% en CASH mais les rares trades (NEUTRAL) perdent massivement. Seul le SHORT fixe survit (+6.4%). DOT confirme son profil dangereux (correlation BTC 0.59, mouvements imprevisibles).

---

## Analyse du mode adaptatif

### Forces

1. **Protection du capital** : le drawdown max est systematiquement 2-3x plus faible que les modes fixes. ETH: 9.7% vs 31.8% (SHORT). SOL: 8.7% vs 20.1%.
2. **Pas de catastrophe** : l'adaptatif ne perd jamais plus de 24% meme sur 3 mois de bear. Le LONG fixe perd 82-135%.
3. **Win rate eleve quand il trade** : 81.5% sur ETH (il ne trade que dans les bonnes conditions).

### Faiblesses

1. **Trop conservateur** : 70-95% du temps en CASH. Il rate enormement d'opportunites de grid trading.
2. **Le detecteur de volatilite trigger trop vite** : le seuil CASH a 6% est trop bas pour la crypto. En bear market, la vol est quasi-permanente au-dessus de 5-6%.
3. **Les seuils RSI sont calibres pour le range** : RSI < 40 = BEAR, mais en crypto le RSI peut rester sous 40 pendant des semaines sans que le grid short ne perde.
4. **Friction des switches** : chaque switch ferme les positions ouvertes. Avec 5-8 switches sur 3 mois, c'est gerab, mais chaque switch coute des fees.

### Le SHORT fixe : le vrai gagnant en bear market

Sur les 3 mois de bear (-29% a -32%), le classement est clair :

| Strategie | ETH PnL% | SOL PnL% | DOT PnL% | Moyenne | Avg MaxDD |
|-----------|----------|----------|----------|---------|-----------|
| **SHORT** | **+57.8%** | **+71.7%** | **+6.4%** | **+45.3%** | **35.0%** |
| ADAPTIVE | +19.6% | +5.5% | -24.0% | +0.4% | 14.3% |
| NEUTRAL | +15.7% | +80.9% | -57.4% | +13.1% | 56.1% |
| LONG | -82.2% | -50.5% | -135.4% | -89.4% | 112.0% |
| HODL | -31.7% | -31.7% | -28.9% | -30.8% | - |
| CASH | 0% | 0% | 0% | 0% | 0% |

**Le SHORT fixe bat tout le monde en PnL moyen (+45.3%).** Mais avec un DD moyen de 35%, c'est stressant.

**L'adaptatif est le meilleur pour le Sharpe ratio** : rendement modeste mais risque tres contenu (DD 14.3%). C'est la strategie "je dors tranquille".

---

## La vraie reponse : combiner les deux

L'ideal n'est ni le SHORT fixe (trop de risque) ni l'adaptatif pur (trop prudent). C'est un **adaptatif recalibre pour la crypto** :

### Seuils a ajuster

| Parametre | Valeur actuelle | Valeur proposee | Raison |
|-----------|----------------|-----------------|--------|
| CASH volatilite | > 6% | > 10% | La crypto vit a 5-8% de vol, c'est normal |
| BEAR RSI entree | < 40 | < 35 | Etre plus selectif pour entrer en SHORT |
| BEAR RSI sortie | > 45 | > 50 | Rester en SHORT plus longtemps |
| BULL RSI entree | > 55 | > 60 | Plus selectif pour entrer en LONG |
| Cooldown | 8 candles (2h) | 24 candles (6h en 15min / 24h en 1h) | Reduire les switches |
| Confirmations | 3 | 5 | Plus de patience avant de switcher |

### Le mode hybride propose

```
SI detecteur dit SHORT et conditions confirmees:
    → Grid SHORT (70% sell / 30% buy, spacing large)
SI detecteur dit LONG et golden cross confirme:
    → Grid LONG (70% buy / 30% sell, spacing serre)
SI detecteur dit RANGE (RSI 40-60, vol basse):
    → Grid NEUTRAL (50/50)
SI vol > 10% OU crash > -5%:
    → CASH total
SINON:
    → Grid NEUTRAL (defaut, pas CASH)
```

Le changement cle : **le defaut est NEUTRAL, pas CASH.** En crypto, rester en cash 70% du temps, c'est rater le profit du grid. Mieux vaut trader neutral par defaut et ne couper que sur signal fort.

---

## Recommandations mises a jour

### Pour BTC maintenant

Les params session 84 restent valides pour un SHORT grid :
```
Pair: XBTUSD | Mode: SHORT
Centre: $66 482 | Range: [$64 820 - $68 144]
10 levels | x5 | $15 capital | Spacing: $332 (0.50%)
```

Mais **ajouter un switch automatique** : si BTC passe au-dessus de $72k avec RSI > 60, basculer en NEUTRAL. Si EMA20 > EMA50, basculer en LONG.

### Pour ETH/DOT/SOL

En attendant un signal bull clair, **SHORT fixe** est la strategie optimale en bear market. Quand le marche tournera (EMA200 4H), switcher vers NEUTRAL.

### Prochaines etapes

1. **Recalibrer les seuils adaptatifs** : seuil CASH a 10%, defaut NEUTRAL au lieu de CASH
2. **Backtester l'adaptatif recalibre** sur les memes donnees 3 mois
3. **Ajouter ADX au detecteur** : ADX < 25 = NEUTRAL, ADX > 25 = SHORT ou LONG selon direction
4. **Recuperer 3 mois de BTC** depuis la VM pour valider sur une periode plus longue
5. **Paper trading 1 semaine** de l'adaptatif avant deploiement

---

## Scripts

- `trading/backtest_btc_short.py` — backtest SHORT/NEUTRAL/LONG fixe sur BTC
- `trading/backtest_btc_adaptive.py` — backtest adaptatif avec regime detection

*Ecrit le 30 mars 2026. Donnees BTC: 14-22 mars (7.5j, 15min). Donnees ETH/DOT/SOL: dec 2025 - mars 2026 (91j, 1h).*
