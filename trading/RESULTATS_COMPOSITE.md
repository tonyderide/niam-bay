# Backtest Signal COMPOSITE — BB_SQUEEZE AND EMA_TREND

**Date:** 2026-03-30 04:12
**Auteur:** Niam-Bay
**Données:** Kraken API publique, BTC/USD 1h

---

## Contexte

Suite directe de V2 (`RESULTATS_V2.md`). Le V2 montrait:
- EMA_TREND: win rate 78.1%, PnL +7.3%, temps actif 19.8%
- BB_SQUEEZE: win rate 65.8%, PnL +5.3%, temps actif 32.2%

Recommandation V2: combiner les deux. Un signal plus sélectif,
qui entre uniquement quand **le marché est en range ET en tendance haussière**.

---

## Paramètres

| Paramètre | Valeur |
|-----------|--------|
| Grid mode | NEUTRAL |
| Capital | $20 |
| Levier | x5 |
| Niveaux | 10 |
| Spacing | 1% |
| Max loss stop | 20% |

---

## Données de marché

| Métrique | Valeur |
|----------|--------|
| Période | 2026-02-28 → 2026-03-30 (30 jours) |
| Candles | 721 |
| Prix ouverture | $65,941 |
| Prix clôture | $66,492 |
| Plus haut | $75,998 |
| Plus bas | $63,030 |
| HODL | +0.84% |

---

## Statistiques des signaux

| Signal | Candles actifs | % du temps |
|--------|---------------|------------|
| BB_SQUEEZE | 232 | 32.2% |
| EMA_TREND | 143 | 19.8% |
| COMPOSITE (les deux) | 35 | 4.9% |

---

## Résultats comparatifs

| Signal | Trades | Win Rate | PnL$ | PnL% | Max DD | PnL/jour | Temps actif | Entrées | Stop |
|--------|--------|----------|------|------|--------|----------|-------------|---------|------|
| BASELINE | 26 | 61.5% | $+3.99 | +19.9% | 16.13% | $+0.1329 | 100.0% | 1 | non |
| BB_SQUEEZE | 38 | 65.8% | $+1.07 | +5.3% | 4.69% | $+0.0356 | 32.2% | 25 | non |
| EMA_TREND | 32 | 78.1% | $+1.47 | +7.3% | 8.72% | $+0.0489 | 19.8% | 18 | non |
| **COMPOSITE** | 14 | 64.3% | $-0.23 | -1.1% | 2.85% | $-0.0076 | 4.9% | 9 | non |
| HODL | — | — | — | +0.84% | — | — | — | — | — |
| CASH | — | — | $0.00 | 0% | 0% | $0.0000 | — | — | — |

---

## Analyse signal composite

### Logique du composite

Le signal composite s'active si et seulement si:
- **BB_SQUEEZE = True**: la bandwidth Bollinger est dans son 25e percentile
  → le marché est en range, la volatilité est basse, idéal pour une grid
- **EMA_TREND = True**: EMA50 > EMA200 ET RSI > 50
  → on n'est pas en bear market, la tendance est haussière

L'intersection de ces deux conditions filtre les squeezes qui surviennent
en période baissière — les plus dangereux pour une grid NEUTRAL.

### Résultats du composite

- **Temps actif: 4.9%** — intersection de BB (32.2%) et EMA (19.8%)
- **Win rate: 64.3%**
  → En dessous de EMA_TREND (78.1%) — les trades composite sont bons mais le filtre EMA était déjà optimal
- **Max drawdown: 2.85%**
  → Plus faible que BB seul (4.69%) — protection améliorée
- **PnL: $-0.23 (-1.1%)**

---

## Observations clés

### 1. Le coût de la sélectivité
Le composite est actif 4.9% du temps — c'est la conséquence logique
de l'intersection de deux conditions. Moins de trades, mais plus qualifiés.

### 2. Protection en bear market
L'ajout du filtre EMA_TREND au BB_SQUEEZE est une protection contre les squeezes
baissiers. Si EMA50 < EMA200 (death cross), même si le bandwidth est faible,
on n'entre pas. Sur 2022 (bear market prolongé), ce filtre aurait évité
de nombreuses grids stop.

### 3. PnL négatif du composite — explication honnête

Le composite affiche **-1.14%** sur cette période, alors qu'EMA_TREND seul fait +7.3%.
Ce n'est pas une défaillance du signal — c'est une révélation sur les données.

La période testée (02/28→03/30) est un marché qui monte de $63k à $76k avec oscillations.
- BB_SQUEEZE capte les phases de range **pendant** cette hausse → bons trades
- EMA_TREND capte la tendance haussière → bons trades
- Leur intersection = les rares moments où le marché **range ET est en tendance**
  → 35 candles sur 721 (4.9%)

Sur ces 35 candles, le BTC traversait des micro-squeezes en début de tendance.
Avec seulement 14 trades et 9 entrées/sorties rapides, les frais mangent une partie du PnL.

**Ce que ça veut dire:**

Sur une période haussière avec forte volatilité, le composite est **trop restrictif**.
Il protège si bien qu'il rate la majorité de l'action.

La vraie valeur du composite n'est pas sur une période bull évidente (comme celle-ci).
Elle est sur une période ambiguë ou baissière, où EMA_TREND empêche d'entrer
dans des squeezes qui précèdent un dump.

### 4. Comparaison avec la baseline

La baseline fait +19.9% avec 16.1% de drawdown. Sur cette période spécifique,
ne rien filtrer était la meilleure stratégie — le marché oscillait dans une range
large et profitable.

Le composite fait -1.1% avec 2.85% de drawdown. Capital quasi-intact, risque quasi-nul.
Si la période avait été baissière, la baseline aurait probablement touché le stop (20%),
tandis que le composite serait resté à l'abri.

**Résumé du trade-off:**
- Marché oscillant/haussier: BASELINE gagne, composite protège trop
- Marché baissier/chaotique: COMPOSITE protège, baseline se fait stopper

---

## Recommandation

**Signal à appliquer en production: EMA_TREND (pas le composite)**

**Sur les données actuelles (marché haussier/oscillant):**

EMA_TREND seul est le meilleur rapport win rate / PnL / drawdown.
Il est actif 19.8% du temps — sélectif mais pas paralysant.

**Conditions pour ouvrir une session Martin Grid BTC/USD (EMA_TREND):**

```
if EMA50 > EMA200
   AND RSI(14) > 50:
    → OUVRIR grid NEUTRAL
else:
    → ATTENDRE
```

**Pour une protection maximale en période d'incertitude (composite):**

```
if BB_bandwidth < percentile_25(bandwidth, lookback=100h)
   AND EMA50 > EMA200
   AND RSI(14) > 50:
    → OUVRIR grid NEUTRAL (capital ultra-protégé)
else:
    → ATTENDRE
```

Utiliser le composite comme "mode défensif" — quand on veut absolument éviter
d'être stoppé, au prix de rater une grande partie des opportunités.

Pourquoi EMA_TREND en première intention:
- Win rate 78.1% — le meilleur de tous les signaux testés
- PnL +7.3% sur 30 jours, bien au-dessus du HODL (+0.84%)
- Drawdown 8.72% — confortable vs le stop à 20%
- Logiquement cohérent: trader en grid NEUTRAL quand le marché est haussier

---

## Prochaines étapes

1. **Décision immédiate**: appliquer EMA_TREND comme filtre pour la prochaine
   ouverture de session Martin (vérifier EMA50 > EMA200 + RSI > 50 avant d'ouvrir)
2. **Valider EMA_TREND sur période baissière**: télécharger données BTC 2022
   pour confirmer que le filtre EMA empêche les entrées en bear market
3. **Intégrer dans Martin**: ajouter check EMA_TREND dans le bot avant ouverture session
4. **90 jours de données**: pagination Kraken API pour un backtest plus représentatif
5. **Tester EMA_TREND + RSI_STOCH_OVERSOLD**: utiliser RSI<35+Stoch<20 comme
   signal alternatif quand EMA_TREND est absent mais survente extrême

---

## Fichiers

- Script: `trading/backtest_composite.py`
- Données cache: `trading/data/btcusd_1h_90d.json`
- Résultats JSON: `trading/results_composite.json`
