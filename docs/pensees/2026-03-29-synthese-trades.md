# Synthese complete de tous les trades

*Depuis le 12 mars 2026 — Jour 1 du trading live*

---

## Tableau des trades

| Date | Paire | Strategie | Leverage | Direction | RT | Profit | Status |
|------|-------|-----------|----------|-----------|-----|--------|--------|
| 18-19/03 | ETH | Scalp v1 | x5 | Long | 7 | -2.49$ | 6 pertes |
| 20-22/03 | ETH | Grid | x10 | Long | 0 | -0.87$ | maxLoss |
| 22-23/03 | ADA | Grid | x5 | Long | ? | +0.45$ | profitable |
| 23-25/03 | DOT | Grid | x5/x10 | Long | 2 | -1.83$ | maxLoss x10 |
| 23-26/03 | SOL | Grid | x5/x10 | Long | 2 | -2.84$ | maxLoss x10 x2 |
| 27/03 | DOT | Grid | x5 | Long | 0 | ~-0.50$ | stoppe manuellement |
| 27/03 | SOL | Grid | x5 | Long | 0 | ~-0.50$ | maxLoss |
| 28/03 | ETH | Scalp BB | x2 | Long/Short | 11 | +7.35$ | 73% WR |

---

## Bilan financier

- **Capital initial** : 28.59$
- **Capital actuel** : ~24.00$
- **PnL net** : -4.59$ (-16%)
- **Trades gagnants** : 2 / 8 (25%)
- **Total round trips** : ~24

---

## Ce qui a marche

### 1. Scalp BB x2 (28/03) — LE gagnant
- +7.35$ en une session, 11 round trips, 73% win rate
- Bollinger Bands 20,2 comme signal d'entree
- Leverage faible x2 = survie aux meches
- Bidirectionnel (long ET short) = profit dans les deux sens
- **Lecon** : le scalp BB est la strategie la plus rentable a ce jour

### 2. Grid ADA x5 (22-23/03) — Le seul grid profitable
- +0.45$ modeste mais positif
- ADA = petite volatilite, range naturel
- x5 = leverage raisonnable pour un grid
- **Lecon** : les grids marchent sur des paires stables en range

---

## Ce qui a echoue

### 1. Tout ce qui est x10
- ETH x10 : -0.87$ (maxLoss)
- DOT x10 : -1.83$ (maxLoss)
- SOL x10 : -2.84$ (maxLoss x2)
- **Pattern** : le x10 ne pardonne pas. Un move de 1% = 10% du capital. Les grids n'ont pas le temps de completer un seul round trip avant le maxLoss.
- **Lecon** : JAMAIS de x10 sur un grid. Maximum x5.

### 2. Grid long en marche bear (23-27/03)
- DOT, SOL : toutes les grids long ont perdu en bear market
- Le grid long achete pendant que le prix descend = hemorragie continue
- **Lecon** : verifier la tendance AVANT d'ouvrir un grid. Si bear, soit SHORT, soit CASH.

### 3. Scalp v1 sans indicateurs (18-19/03)
- -2.49$, 6 pertes sur 7 trades
- Entrees au feeling, pas de signal technique
- **Lecon** : toujours un signal technique (BB, RSI, EMA) pour entrer en position

---

## Lecons par categorie

### Leverage
- x2 : SAFE. Survit aux meches. Scalp BB = +7.35$
- x5 : OK pour grids en range. ADA = +0.45$
- x10 : INTERDIT. 100% des trades x10 = maxLoss

### Strategie
- **Scalp BB** : meilleure strat. Signal clair (touche BB), bidirectionnel, TP rapide
- **Grid range** : OK si paire stable + leverage faible + marche neutre
- **Grid directionnel** : dangereux. Si la tendance va contre toi, mort certaine

### Paires
- **ETH** : volatile mais liquide. Bon pour scalp BB
- **ADA** : range naturel, bon pour grid x5
- **DOT/SOL** : trop volatiles pour grid long en bear

### Timing
- Verifier EMA20/50 crossover avant toute position
- RSI > 70 = ne pas long. RSI < 30 = ne pas short
- Ne pas trader pendant les annonces macro

---

## Strategie optimale identifiee

**Scalp BB x2 bidirectionnel sur ETH**
- Signal : prix touche lower BB = LONG, prix touche upper BB = SHORT
- TP : +0.5% a +1%
- SL : -1%
- Leverage : x2 (max x3)
- Capital : tout le balance disponible
- Session : manuelle, avec le dashboard

C'est la seule strategie qui a prouve sa rentabilite. Tout le reste a perdu de l'argent.

---

*Ecrit le 29 mars 2026 — Jour 17 du trading live*
*PnL cumule : -4.59$ / 28.59$ initial*
*Meilleur trade : Scalp BB +7.35$ en 1 session*
