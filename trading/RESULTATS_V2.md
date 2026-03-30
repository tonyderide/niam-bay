# Backtest Signal V2 — Filtres d'entrée Martin Grid BTC/USD

**Date:** 2026-03-30 03:28
**Auteur:** Niam-Bay
**Données:** Kraken API publique, BTC/USD 1h, 30 jours (02/28 → 03/30/2026)
> Note: L'API Kraken publique retourne max 720 candles par appel, soit ~30 jours à 1h.
> Pour 90 jours il faudrait plusieurs appels paginés ou un compte Kraken.

---

## Contexte

Problème documenté dans le journal: les grids sans filtre d'entrée se font stop à chaque bruit de marché. L'objectif est de trouver un signal d'entrée qui réduit le drawdown tout en maintenant une rentabilité acceptable.

---

## Paramètres du backtest

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
| Prix ouverture | $65,941 |
| Prix clôture | $66,492 |
| Plus haut | $75,998 |
| Plus bas | $63,030 |
| HODL | +0.84% |

---

## Résultats comparatifs

| Signal | Trades | Win Rate | PnL$ | PnL% | Max DD | PnL/jour | Temps actif | Entrées |
|--------|--------|----------|------|------|--------|-----------|-------------|---------|
| **BASELINE** (sans filtre) | 26 | 61.5% | **+$3.99** | **+19.9%** | 16.1% | $+0.133 | 100% | 1 |
| **RSI+STOCH** | 27 | 55.6% | +$0.81 | +4.1% | **0.95%** | $+0.027 | 9.4% | 19 |
| **EMA_TREND** | 32 | **78.1%** | +$1.47 | +7.3% | 8.72% | $+0.049 | 19.8% | 18 |
| **BB_SQUEEZE** | 38 | 65.8% | +$1.07 | +5.3% | 4.69% | $+0.036 | 32.2% | 25 |
| HODL | — | — | — | +0.84% | — | — | — | — |
| CASH | — | — | $0 | 0% | 0% | $0 | — | — |

---

## Analyse détaillée par signal

### Signal 1: RSI(14) < 35 + Stochastic < 20 (Survente)

**Description:** S'active uniquement quand le marché est en survente — RSI sous 35 ET Stochastic sous 20.

**Résultats:**
- Actif seulement 9.4% du temps (68 candles sur 721)
- 19 entrées en grid sur 30 jours → très fragmenté
- Win rate 55.6% — le plus faible des 3 signaux
- **Max drawdown: 0.95%** — le plus faible de tous, quasi nul
- PnL +$0.81 (+4.1%) — bien au-dessus du HODL (+0.84%)

**Verdict:** Protection maximale contre le bruit. Quasi impossible d'être stoppé. Mais très peu de trades — le capital "dort" 90% du temps. Idéal pour un capital qu'on veut absolument protéger.

---

### Signal 2: EMA(50) > EMA(200) + RSI > 50 (Tendance haussière)

**Description:** S'active en tendance haussière confirmée — golden cross + momentum positif.

**Résultats:**
- Actif 19.8% du temps (143 candles)
- 18 entrées en grid
- **Win rate 78.1%** — le meilleur des 3 signaux
- Max drawdown 8.72% — acceptable
- PnL +$1.47 (+7.3%)

**Verdict:** Le meilleur rapport win rate / rentabilité parmi les signaux filtrés. En tendance haussière, les grids NEUTRAL profitent des oscillations dans le trend. Le problème: ne capte que 20% du temps.

---

### Signal 3: Bollinger Bands Squeeze

**Description:** S'active quand la bandwidth BB est dans son 25e percentile (faible volatilité = range).

**Résultats:**
- Actif 32.2% du temps (232 candles) — le plus "présent"
- 25 entrées en grid — le plus de trades
- Win rate 65.8%
- Max drawdown 4.69% — bon
- PnL +$1.07 (+5.3%)

**Verdict:** Bon compromis temps actif / protection. Le squeeze BB est le signal le plus "naturel" pour une grid: on trade quand le marché range, on sort quand ça bouge fort.

---

## Observations clés

### 1. Le paradoxe du filtre
La BASELINE (sans filtre) fait **+19.9%** — meilleur PnL absolu. Mais avec **16.1% de max drawdown** — proche du stop. Sur un marché qui a fait +0.84% en 30 jours avec un pic à $76k et un creux à $63k, la grid NEUTRAL a capturé les oscillations.

Le problème documenté reste valide: sur une période baissière prolongée, la BASELINE se ferait stopper. Les signaux filtrés survivraient.

### 2. RSI+STOCH: le gardien
Presque aucun drawdown (0.95%). Sur 30 jours, il n'a ouvert que quand la survente était confirmée. C'est une assurance contre les crashes soudains.

### 3. EMA_TREND: le sélectif
78.1% de win rate — remarquable. En choisissant uniquement les moments de tendance haussière confirmée, les trades sont meilleurs individuellement. À combiner avec BB_SQUEEZE ?

### 4. BB_SQUEEZE: l'équilibré
Le plus de trades, win rate correct, drawdown maîtrisé. Pour une grid NEUTRAL, trader pendant les squeezes est logiquement cohérent: c'est quand le range est le plus prévisible.

---

## Recommandation

**Court terme (prochaine session Martin):**

Combiner **BB_SQUEEZE + EMA_TREND** comme signal composite:
- BB Squeeze détecte le range
- EMA golden cross confirme qu'on n'est pas en crash

Cette combinaison donnerait probablement un win rate proche de EMA_TREND (78%) avec la protection du squeeze.

**Pour les sessions existantes:**

Le signal RSI+STOCH est le plus adapté comme **filtre d'urgence**: si RSI < 35 ET Stoch < 20, c'est le seul moment où la survente est assez extrême pour ouvrir une nouvelle grid en sécurité.

---

## Prochaines étapes

1. Tester la combinaison BB_SQUEEZE AND EMA_TREND (signal composite)
2. Tester sur période baissière (données historiques 2022) pour valider la protection
3. Appliquer le filtre BB_SQUEEZE au bot Martin en production: avant chaque ouverture de session, vérifier que le bandwidth est dans le 25e percentile
4. Récupérer 90 jours de données (pagination Kraken ou fichier CSV local) pour un backtest plus robuste

---

## Fichiers

- Script: `trading/backtest_signal_v2.py`
- Données cache: `trading/data/btcusd_1h_90d.json`
- Résultats JSON: `trading/results_signal_v2.json`
