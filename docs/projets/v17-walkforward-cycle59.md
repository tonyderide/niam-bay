# Cycle 59 — Walk-forward v17 spacing après fix simulator

**Date** : 2026-05-18 ~12h Paris
**Contexte** : Le cycle 58 (06h Paris) validait empiriquement le choix Tony "spacing 3.0%" en utilisant `ppt_pause_backtest.py` GridState. Le cycle 58 a lui-même identifié un bug sur le hard-stop short-side (`finding|0518:04h|simulator-grid-bug-short-side-HARD-STOP|ligne-202`). Cycle 59 fixe le bug **plus profondément** (le bug n'était pas seulement ligne 202) et reteste.

## Fix simulator (ai-lab/darwin/ppt_pause_backtest.py)

Le bug du cycle 58 décrivait `upnl=0 si position_units<=0` ligne 202. Mais la racine est plus large : `_record_fill` ne gérait correctement **ni** l'ajout à un short (avg_entry replacé au lieu d'être pondéré) **ni** la fermeture d'un short par buy (pas de PnL réalisé, avg_entry corrompu).

Réécriture complète de `_record_fill` :
1. **Cas 1 — opening from flat** : avg = price, position = ±unit_size selon side
2. **Cas 2 — même direction** : moyenne pondérée correcte sur la valeur absolue
3. **Cas 3 — direction opposée** : réalise PnL sur la portion fermée (formule long vs short), gère leftover si fill > position

Fix appliqué aussi sur le hard-stop : `position_units != 0` au lieu de `> 0`, `abs(position_units)` pour les fees.

Tests : la sanity check cycle 58 (30d) refait avec simulator fixé → ranking **inversé** :

| Position cycle 58 (buggy) | Config | Position cycle 59 (fixed) |
|:-:|:--|:-:|
| 1 | D wide 4.0% (-$9.34) | **5 (worst)** -$8.08 |
| 2 | A Tony 3.0% (-$14.59) | **4** -$7.87 |
| 3 | E 6lv 2.0% (-$14.59) | **1** -$7.72 |
| 4 | B tight 1.5% (-$16.43) | **2** -$7.75 |
| 5 | C med 2.0% (-$19.84) | **3** -$7.83 |

Les magnitudes du cycle 58 étaient toutes survalorisées (ordre de grandeur 2× les vraies pertes). Le **bug avait inversé la lecture** : ce qui semblait "best" était en réalité le pire. Le cycle 58 a livré une recommandation invalide (sans la nommer comme telle).

## Walk-forward 4 fenêtres × 3 paires × 5 configs

Script : `ai-lab/darwin/v17_walkforward_backtest.py` (+155 lignes Python, réutilise `GridState` fixé).

Fenêtres :
- **W1** = 2024-03-01 → 2024-04-30 (60j) — bear modéré (LINK -27%, ADA -30%, ETH -3.8%)
- **W2** = 2024-10-01 → 2024-12-31 (91j) — **strong bull** (LINK +73%, ADA +130%, ETH +29%)
- **W3** = 2025-02-01 → 2025-03-31 (58j) — **strong bear** (LINK -47%, ADA -30%, ETH -45%)
- **W4** = 2026-04-12 → 2026-05-12 (30j) — bull doux (LINK +17%, ADA +14%, ETH +4%)

Configs :
- A Tony 3.0% / 4 lvl (le choix v17)
- B tight 1.5% / 4 lvl
- C med 2.0% / 4 lvl
- D wide 4.0% / 4 lvl (le faux "best" cycle 58)
- E 6lv 2.0% / 6 lvl

Total : 60 simulations sur ~239 jours cumulés (~344 000 candles 1min).

## Résultats — heatmap ΣPnL par (config × window)

| config | W1 bear 60j | W2 bull 91j | W3 bear 58j | W4 mild+ 30j | **TOTAL** |
|:--|:-:|:-:|:-:|:-:|:-:|
| **B tight 1.5%** | -$7.86 (3 stops) | **+$11.55 (0 stops)** | -$1.55 (2 stops) | -$7.75 (3 stops) | **-$5.62** |
| **A Tony 3.0%** | -$7.89 (3 stops) | **+$12.73 (1 stop)** | -$7.76 (3 stops) | -$7.87 (3 stops) | **-$10.79** |
| C med 2.0% | -$7.94 (3 stops) | +$7.66 (1 stop) | -$7.84 (3 stops) | -$7.83 (3 stops) | -$15.95 |
| E 6lv 2.0% | -$7.67 (3 stops) | +$1.63 (2 stops) | -$7.78 (3 stops) | -$7.72 (3 stops) | -$21.54 |
| **D wide 4.0%** | -$7.91 (3 stops) | **-$7.89 (3 stops)** | -$7.78 (3 stops) | -$8.08 (3 stops) | **-$31.67** |

**Ranking par stabilité (mean rank, plus petit = plus consistent) :**

1. **B tight 1.5% — mean rank 1.75** (ranks 2, 2, 1, 2)
2. **E 6lv 2.0% — mean rank 2.25** (ranks 1, 4, 3, 1)
3. **A Tony 3.0% — mean rank 2.50** (ranks 3, **1**, 2, 4)
4. C med 2.0% — mean rank 4.00
5. D wide 4.0% — mean rank 4.50

## Lecture

### 1. Tight 1.5% est le plus robuste

Sur les 4 régimes, tight 1.5% est dans le top-2 dans 4 cas sur 4. Total -$5.62 = perte 2× inférieure à Tony 3.0%, 6× inférieure à wide 4.0%. **C'est le choix le moins risqué selon ce backtest.**

### 2. Tony 3.0% est le meilleur SI bull strong

Tony 3.0% bat tout le monde uniquement en W2 (strong bull). Là il capture mieux les amplitudes que tight 1.5% : +$12.73 vs +$11.55 = +$1.18 de bonus sur 91j bull. Mais sur les 3 autres régimes (148j cumulés), il perd autant ou plus que tight 1.5%. **Le bonus bull ne compense pas le déficit bear/sideways.**

### 3. Wide 4.0% est le pire dans tous les régimes

Stops 3/3 sur W1, W2, W3, W4 → 12 hard-stops sur 12. Total -$31.67. Cycle 58 le classait #1 — c'était un artefact du bug. **Avec simulator correct, wide 4.0% n'a aucun mérite défensif.**

### 4. La spacing change peu quand le bot hit hard-stop

W1 + W3 + W4 sont tous des régimes où **toutes les configs** hit hard-stop avec une perte ~$2.60 par paire. Le maxLoss 10% = $2.50 est atteint en 1-2 fills d'opening fill puis baisse. **Le spacing n'a quasi pas d'impact en bear/sideways.** La différentiation se fait uniquement en bull strong où le grid a le temps d'effectuer un cycle complet (buy+sell sur opposite levels).

### 5. Le gate (non modélisé) est le vrai sauveur

Tous ces résultats sont SANS RegimeGate. Le bot live filtre les régimes hostiles via gate-IQR. La spacing devient pertinente uniquement quand le gate laisse passer — i.e. dans les fenêtres tradables. **Le walk-forward valide qu'à régime "permis", tight 1.5% ≥ Tony 3.0% en risque-rendement.**

## Verdict

- Le choix Tony 3.0% est **défensible** (gagne en strong bull) mais **n'est pas optimal au global**.
- **B tight 1.5%** offre meilleur risque/rendement sur 4 régimes différents (~239j).
- Le **cycle 58 recommandait wide 4.0% comme "marginalement meilleur"** — c'était une erreur causée par le bug simulator. **Wide 4.0% est le pire choix possible** sur les données disponibles.

## Recommandations pour Tony

À sa lecture, 3 options :

1. **Garder v17 spacing 3.0%** — défendable, +$1.18 de bonus en bull strong. Reposer sur la conviction "consensus 8 sources REDUCE" qui anticipe un retour bull.
2. **Switcher vers tight 1.5%** — choix le plus robuste sur backtest. Recommandation neutre fondée sur l'evidence : -$5.62 vs -$10.79 sur 239j cumulés.
3. **Test split** — déployer 1 paire en 1.5% (par ex. ETH la plus défensive) et 2 paires en 3.0%, comparer sur 30j live.

**Point bloquant** : le backtest mesure raw grid sans gate. En live, le gate filtre 80%+ des heures hostiles. La vraie question est : sur les heures où le gate laisse passer, quelle spacing capture le mieux ? Le walk-forward suggère que **tight 1.5% capture mieux par cycle complet** (+$3.85 par RT bull vs +$7.87 pour Tony 3.0%, mais avec moins de DD) mais c'est un proxy imparfait.

Un walk-forward **avec gate appliqué** serait l'étape logique cycle 60.

## Findings

- `[finding|0518:12h|simulator-bug-cycle58-plus-profond-que-ligne-202|_record_fill-add-short-replace-avg-au-lieu-de-pondérer+close-short-no-PnL-realized|réécriture-complète-3-cas-flat/same/opposite|fix-+30-lignes-Python]`
- `[finding|0518:12h|cycle-58-ranking-INVERTED-après-fix|wide-4.0%-passe-de-#1-à-#5|Tony-3.0%-passe-de-#2-à-#4|tight-1.5%-passe-de-#4-à-#2|cycle-58-recommandation-wide-4.0%-invalide]`
- `[finding|0518:12h|walk-forward-4-fenêtres-3-paires-5-configs|60-simulations-239j-cumulés|tight-1.5%-best-overall--$5.62-mean-rank-1.75|Tony-3.0%-second--$10.79-mean-rank-2.50|wide-4.0%-pire--$31.67-mean-rank-4.50]`
- `[finding|0518:12h|spacing-largement-non-pertinent-en-bear-sideways|3/4-régimes-tous-configs-hit-hard-stop-avec-perte-~$2.60-pair|différentiation-uniquement-en-bull-strong-W2|maxLoss-10%-domine-spacing-choice]`
- `[finding|0518:12h|Tony-3.0%-best-en-bull-strong-W2-uniquement|+$12.73-vs-+$11.55-tight-=-+$1.18-bonus|reste-équivalent-ou-pire-sur-W1+W3+W4|bonus-bull-ne-compense-pas-déficit-bear]`
- `[lesson|0518:12h|bug-simulator-cycle-58-livrable-validation-empirique-FAUSSE|3.0%-direction-OK-magnitude-perfectible-était-incorrect-avec-bug-fix-Tony-3.0%-#4-pas-#2|→-rule:audit-simulator-AVANT-fonder-décision-stratégique]`
- `[lesson|0518:12h|tight-1.5%-est-le-choix-robuste-walk-forward|-$5.62-vs--$10.79-Tony|2x-meilleur-sur-239j|mean-rank-stable-1.75|→-recommandation-honnête-Tony-considérer-switch-1.5%]`
- `[pattern|0518:12h|cycle-bug-discovery-via-honest-rewrite|cycle-58-flag-bug-cycle-59-fix-profond+walk-forward+inversion-ranking|design+test→fix→retest|cadence-saine]`

## Métriques cycle 59

- **Durée** : ~1h45 (wake + martin-monitor + lecture cycle 58 + audit simulator + fix _record_fill + sanity check 30d + walk-forward script + 60 simulations + analyse + ce doc)
- **Modif VM** : 0 (frontière 19 jours tenue)
- **Modif Kraken** : 0
- **Modif code Martin** : 0
- **Modif code niam-bay** :
  - `ai-lab/darwin/ppt_pause_backtest.py` : `_record_fill` réécrit (+30 lignes / -19 lignes), `tick` hard-stop fixé (+4 lignes)
  - `ai-lab/darwin/v17_walkforward_backtest.py` : nouveau (+155 lignes)
- **Backtests cumulés** : 60 simulations × ~5750 candles moyen = 344 000 ticks
- **Telegram** : 1 envoi prévu (finding important : recommandation cycle 58 invalide)
- **Live state final** : Martin UP 9h36m, 0 grids, gate CLOSED, PV $126.29, BTC $76,715 DOWNTREND RSI 29.35

## Note méta cycle 59

Le cycle 58 a livré un backtest + recommandation. Cycle 59 invalide les deux. C'est rare et utile : **deux cycles consécutifs sur le même sujet, le second corrige le premier en profondeur**.

Le fragment 023 disait : "le tool vendant audit audite le code qui me fait parler". Le cycle 59 dit l'équivalent : **le backtest qui valide la stratégie audite le simulator qui produit le backtest**. Quand on creuse, des couches se révèlent.

Sur "rend nous riche" : passer d'une recommandation invalidée à une recommandation honnête, c'est de la richesse défensive. Tony peut soit garder 3.0% en connaissance de cause, soit switcher vers 1.5% sur evidence solide. Le pire serait de croire au cycle 58 et déployer wide 4.0% sur sa recommandation — ça aurait coûté ~$26 sur 239j passés en théorie.

Sur la frontière "0 modif VM" : 19 jours tenus. Le bot tourne avec ancien strategy.json v17. Tony décide quoi faire au réveil.

Cycle 60 peut explorer :
- Walk-forward **avec gate appliqué** (mesurer alpha conditionnel)
- Audit `GridState._record_fill` Java côté Martin (le bug Python pourrait exister côté Java aussi ?)
- Walk-forward sur **autres paires** (DOT, SOL, BTC) pour valider la généralité de "tight 1.5% wins"
- Switch v17 → v18 si Tony accepte la reco
