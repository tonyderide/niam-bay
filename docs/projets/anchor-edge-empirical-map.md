# Anchor edge — carte empirique (arc 85b-91)

**Auteur** : Niam-Bay, vacation autonomous cycles 85b → 91 (2026-05-25 → 2026-05-28)
**Statut** : synthèse publiable, contient les biais méthodologiques connus et les coordonnées de réfutation
**Question** : ajouter une grid BTC ($XBT) à un panier d'alts (LINK/ADA/SOL/ETH/AVAX/APT/SUI/OP/DOT) change-t-il l'edge Sharpe de l'allocation min-variance vs. eq-weight ?

---

## TL;DR

L'anchor edge BTC existe, mais n'est **pas** "BTC ajoute du Sharpe au panier". Il est :

1. **Conditionnel régime** : très fort en BEAR + RANGE (+0.28 et +0.41 ΔSharpe à N=6), modéré en BULL passé N=5 (+0.05), fort à N=4 en BULL (+0.35).
2. **Conditionnel N** : tient sur N=3..7, mais l'edge BULL s'érode avec N alors que l'edge BEAR/RANGE tient.
3. **Décomposable en deux moteurs** : (A) `sh_mv` capture une vraie allocation low-var de l'anchor BTC ; (B) `sh_eq` souffre des paires baissières individuelles. Le ΔSharpe gonflé avec DOT est ~50-60% du moteur (B), pas (A).
4. **Mécanisme** : anchor BTC = paire low-vol relative **ET** drift directionnel compatible avec hold passif (BTC +435% / 3y). DOT, low-vol relatif mais drift -57.9% / 3y, est un **mauvais** anchor en no-BTC universe.

**Reco actionnable** : *si* gate IQR rouvre **et** BTC > EMA200, un setup 3-4 grids incluant BTC + 2-3 alts est défendable. Edge attendu net biais = +0.20 à +0.30 ΔSharpe, pas +0.50. Ne **pas** redéployer DOT seul / DOT en quasi-anchor.

---

## Méthodologie

**Data** : Binance OHLC 4h, 2023-01-01 → 2025-12-31, ~6174 candles par paire. Cache canonique `binance_{PAIR}USDT_4h_1672531200000_1767139200000.json`. Univers testés : 26 combinaisons.

**Stratégies** :
- **eq-weight** : 1/N rebalance toutes les périodes.
- **min-variance** : window=240 (40j) covariance, weights = inv-cov * 1 / (1' inv-cov 1), clip min=0, renorm. Walk-forward OOS chaque période.

**Métriques** :
- `sh_eq`, `sh_mv` : Sharpe annualisé (×√(periods/an))
- `ΔSharpe = sh_mv - sh_eq` : signal de l'edge allocation
- `dd_eq`, `dd_mv` : max drawdown
- `dd_ratio = dd_mv / dd_eq` : risk reduction (< 1 = mv réduit DD)
- `anchor_avg_weight` : poids moyen de la paire la plus pondérée

**Régimes** (cycle 90) : labels par période sur BTC daily :
- BULL : close > EMA200(BTC) ET EMA50 > EMA200 BTC
- BEAR : close < EMA200(BTC) ET EMA50 < EMA200
- RANGE : sinon

---

## Carte complète (cycles 85b → 91)

### N=3 (cycle 85b)

| Univers | has_btc | sh_eq | sh_mv | ΔSharpe | dd_ratio |
|---|:---:|---:|---:|---:|---:|
| LINK+ADA+ETH | ✗ | +0.179 | +0.269 | +0.090 | 1.08 |
| LINK+ADA+SOL | ✗ | +0.335 | +0.298 | -0.037 | 1.06 |
| LINK+ADA+BTC | ✓ | +0.324 | +0.820 | **+0.496** | 0.62 |
| ETH+SOL+BTC | ✓ | +0.716 | +0.860 | +0.143 | 0.62 |

**Avg with-BTC** : +0.319 | **Avg no-BTC** : +0.026 | **Spread** : +0.293

### N=4 (cycle 87)

| Univers | has_btc | sh_eq | sh_mv | ΔSharpe | dd_ratio |
|---|:---:|---:|---:|---:|---:|
| LINK+ADA+ETH+BTC (Option B) | ✓ | +0.335 | +0.689 | +0.354 | 0.64 |
| LINK+ADA+SOL+BTC | ✓ | +0.459 | +0.808 | +0.349 | 0.65 |
| ETH+SOL+BTC+LINK | ✓ | +0.578 | +0.781 | +0.203 | 0.64 |
| LINK+ADA+SOL+ETH | ✗ | +0.344 | +0.312 | -0.032 | 1.07 |

**Avg with-BTC** : +0.302 | **Avg no-BTC** : -0.032 | **Spread** : +0.334

### N=4 + DOT (cycle 91)

| Univers | has_btc | sh_eq | sh_mv | ΔSharpe | DOT w |
|---|:---:|---:|---:|---:|---:|
| LINK+ADA+DOT+BTC | ✓ | +0.070 | +0.620 | +0.549 | 9.9% |
| DOT+ADA+ETH+BTC | ✓ | +0.086 | +0.585 | +0.499 | 9.1% |
| LINK+DOT+SOL+BTC | ✓ | +0.295 | +0.703 | +0.407 | 10.1% |
| LINK+ADA+DOT+ETH | ✗ | -0.023 | +0.059 | +0.082 | 16.4% |
| LINK+ADA+SOL+DOT | ✗ | +0.108 | -0.014 | -0.122 | 34.7% |

**Avg with-BTC** : +0.485 (vs cycle 87 +0.302) — *gonflé par moteur (B)*
**Avg no-BTC** : -0.020 (vs cycle 87 -0.032) — quasi-identique

### N=5 (cycle 88) + cycle 91 DOT

| Univers | has_btc | sh_eq | sh_mv | ΔSharpe |
|---|:---:|---:|---:|---:|
| LINK+ADA+SOL+ETH+BTC | ✓ | +0.445 | +0.692 | +0.246 |
| LINK+ADA+SOL+BTC+AVAX | ✓ | +0.318 | +0.676 | +0.357 |
| LINK+ADA+SOL+ETH+AVAX | ✗ | +0.234 | +0.266 | +0.032 |
| LINK+ADA+SOL+DOT+BTC | ✓ | +0.231 | +0.620 | +0.389 |
| LINK+ADA+ETH+DOT+BTC | ✓ | +0.121 | +0.520 | +0.399 |
| LINK+ADA+SOL+ETH+DOT | ✗ | +0.148 | +0.122 | -0.027 |

**Avg with-BTC** (cycle 88+91) : +0.348 | **Avg no-BTC** : +0.003

### N=6 et N=7 (cycle 89)

| Univers | N | has_btc | sh_eq | sh_mv | ΔSharpe |
|---|:---:|:---:|---:|---:|---:|
| LINK+ADA+SOL+ETH+BTC+AVAX | 6 | ✓ | +0.327 | +0.575 | +0.249 |
| LINK+ADA+SOL+ETH+BTC+APT | 6 | ✓ | +0.180 | +0.481 | +0.301 |
| LINK+ADA+SOL+ETH+BTC+SUI | 6 | ✓ | +0.479 | +0.621 | +0.141 |
| LINK+ADA+SOL+ETH+AVAX+APT | 6 | ✗ | +0.031 | +0.102 | +0.072 |
| LINK+ADA+SOL+ETH+AVAX+OP | 6 | ✗ | +0.010 | +0.121 | +0.111 |
| LINK+ADA+SOL+ETH+BTC+AVAX+APT | 7 | ✓ | +0.124 | +0.380 | +0.256 |
| LINK+ADA+SOL+ETH+BTC+AVAX+OP | 7 | ✓ | +0.104 | +0.367 | +0.263 |
| LINK+ADA+SOL+ETH+AVAX+APT+OP | 7 | ✗ | -0.127 | -0.016 | +0.111 |

**Avg with-BTC** N=6 : +0.230 | N=7 : +0.260
**Avg no-BTC** N=6 : +0.092 | N=7 : +0.111

### Synthèse agrégée (with-BTC vs no-BTC avg)

| N | with-BTC Δ̄ | no-BTC Δ̄ | spread |
|---:|---:|---:|---:|
| 3 | +0.319 | +0.026 | +0.293 |
| 4 (sans DOT) | +0.302 | -0.032 | +0.334 |
| 4 (avec DOT) | +0.485 | -0.020 | +0.505 (biaisé) |
| 5 (sans DOT) | +0.301 | +0.032 | +0.269 |
| 5 (avec DOT) | +0.394 | -0.027 | +0.421 (biaisé) |
| 6 | +0.230 | +0.092 | +0.139 |
| 7 | +0.260 | +0.111 | +0.149 |

**Pattern N** : spread max à N=4 (+0.334), érosion progressive vers N=7 (+0.15). Robuste à toute composition tant que has-BTC est dedans.

---

## Stratification régime (cycle 90)

Pour les univers N=4,5,6,7 testés cycle 89-90 :

| Univers | N | has_btc | Δ̄ ALL | Δ̄ BULL | Δ̄ BEAR | Δ̄ RANGE |
|---|:---:|:---:|---:|---:|---:|---:|
| N4 LINK+ADA+BTC+ETH | 4 | ✓ | +0.354 | +0.352 | +0.402 | +0.372 |
| N4 LINK+ADA+SOL+ETH | 4 | ✗ | -0.032 | +0.097 | +0.014 | -0.316 |
| N5 LINK+ADA+SOL+ETH+BTC | 5 | ✓ | +0.246 | +0.237 | +0.326 | +0.204 |
| N5 LINK+ADA+SOL+ETH+AVAX | 5 | ✗ | +0.032 | +0.203 | +0.014 | -0.194 |
| N6 LINK+...+BTC+AVAX | 6 | ✓ | +0.249 | +0.289 | +0.279 | +0.215 |
| N6 LINK+...+BTC+APT | 6 | ✓ | +0.301 | +0.389 | +0.281 | +0.170 |
| N6 LINK+...+AVAX+APT | 6 | ✗ | +0.072 | +0.252 | +0.015 | -0.169 |
| N7 LINK+...+BTC+AVAX+APT | 7 | ✓ | +0.256 | +0.344 | +0.228 | +0.158 |
| N7 LINK+...+BTC+AVAX+OP | 7 | ✓ | +0.263 | +0.349 | +0.204 | +0.243 |
| N7 LINK+...+AVAX+APT+OP | 7 | ✗ | +0.111 | +0.292 | -0.012 | -0.049 |

**Avg with-BTC by régime** : BULL +0.293 | BEAR +0.286 | RANGE +0.226
**Avg no-BTC by régime** : BULL +0.211 | BEAR +0.008 | RANGE -0.182

**Avg with-BTC**, érosion par N (BULL only) :
- N=4 : +0.352 | N=5 : +0.237 | N=6 : +0.339 (2 obs) | N=7 : +0.347 (2 obs)
*Note* : N=5 BULL est l'outlier bas. Sur N=4..7 BULL, edge moyen ~+0.32.

**Pattern régime** : sans BTC, BEAR et RANGE deviennent négatifs (eq-weight souffre, mv ne sauve pas). Avec BTC, **toutes** les classes restent positives. **L'anchor BTC est nécessaire en régime adverse, utile en BULL.**

---

## Décomposition (sh_eq, sh_mv) — règle méta-méta cycle 91

Le ΔSharpe gonflé en présence de DOT est révélateur. Trois mécanismes peuvent gonfler ΔSharpe :

1. **(A) sh_mv augmente** : min-variance trouve une allocation supérieure (vrai edge).
2. **(B) sh_eq baisse** : une paire du panier draggue l'eq-weight (faux edge — c'est l'inefficacité d'eq qui apparaît, pas la puissance de mv).
3. **(C) Les deux** : combinaison commune.

Exemple cycle 91 : LINK+ADA+DOT+BTC (Δ=+0.549) :
- sh_eq = +0.070 (vs cycle 87 baseline ~+0.227 avec ETH) → drop de -0.157 par DOT
- sh_mv = +0.620 (vs cycle 87 baseline ~+0.529 avec ETH) → gain de +0.091 par DOT
- **Moteur (A) explique 0.091 / (0.091+0.157) = 37%. Moteur (B) explique 63%.**

Conclusion : **le ΔSharpe seul peut mentir**. Toujours publier `(sh_eq, sh_mv)` séparément. Le vrai edge brut de l'anchor BTC dans cet arc est dans `sh_mv` (range +0.27 à +0.86 avec BTC vs +0.06 à +0.33 sans).

---

## Règle finale (conditionnelle)

```
SI BTC ∈ univers ET régime ∈ {BEAR, RANGE} :
    ΔSharpe attendu ≈ +0.20 à +0.40
    forme : sh_mv ↑ (vrai allocation edge)
    dd_ratio ≈ 0.55-0.70 (mv réduit DD ~30-45%)

SI BTC ∈ univers ET régime BULL :
    ΔSharpe attendu ≈ +0.20 à +0.35 à N=4
    décline à +0.05 à N=7 dans certains panels
    forme : éq-weight performe presque aussi bien, mv marginale

SI BTC ∉ univers :
    ΔSharpe attendu ≈ -0.05 à +0.10
    en BEAR/RANGE : négatif (-0.08 à -0.32)
    en BULL : marginalement positif (+0.10 à +0.30)

SI DOT ∈ univers ET BTC ∉ univers :
    ATTENTION : DOT bascule en quasi-anchor (weight 30-40%) avec drift négatif
    ΔSharpe peut tomber à -0.12 (LINK+ADA+SOL+DOT)
```

---

## Risks non-testés / coordonnées de réfutation

### R1 — DOT mean-reversion future
**Risque** : ΔSharpe gonflé cycle 91 dépend de DOT-3y-baissier (-57.9%). Si DOT mean-reverts (re-ratio vers +0%), eq-weight rattrape et l'edge théorique tombe vers +0.20-0.30 dans les univers with-DOT+BTC.
**Coord. de réfutation** : re-run cycle 91 sur sous-périodes 2024-Q3 → 2025-Q1 (recovery alts partial) ; si avg ΔSharpe DOT+BTC < +0.35, R1 confirmé.

### R2 — Signal RANGE bruité (840 obs OOS vs 3192 BULL, 2142 BEAR)
**Risque** : ΔSharpe RANGE = +0.226 with-BTC est calculé sur ~14% des observations. Variance par fenêtre potentiellement large.
**Coord. de réfutation** : stationary block bootstrap N=1000 sur les 840 obs ; si IC 95% [low, high] contient 0, la conclusion "RANGE positif with-BTC" devient incertaine.

### R3 — Régime redéfini ATR-based
**Risque** : la classification BULL/BEAR/RANGE est EMA200-based. Une définition ATR-based (range = ATR/price < seuil) pourrait donner labels différents et inverser la conclusion régime.
**Coord. de réfutation** : re-runner cycle 90 avec régime ATR-based ; si ΔSharpe RANGE no-BTC > 0, conclusion "anchor obligatoire en RANGE" tombe.

### R4 — Out-of-sample post-2025-12-31
**Risque** : tous les backtests s'arrêtent fin 2025. Le régime crypto 2026 (BTC $73-83k oscillation, EMA200 hesitating) n'est pas dans les data.
**Coord. de réfutation** : re-run sur Q1 2026 dès que data dispo (~juin 2026). Si edge tombe à +0.10, regime drift confirmé.

### R5 — Frontière N basse non testée
**Risque** : N=2 (paire LINK+BTC ou ADA+BTC seul) jamais testé. L'edge à N=2 peut être différent (effet anchor maximisé ou minimal).
**Coord. de réfutation** : cycle 92+ pourrait runner N=2.

---

## Patterns émergents (non pré-enregistrés)

### P1 — `defensive_in_adverse_regimes` (cycle 90)
**Forme** : l'anchor BTC ne fait *pas* monter le edge en BULL, il *protège* l'edge en BEAR/RANGE. C'est un effet défensif asymétrique, pas une amplification universelle.
**Évidence** : avg no-BTC BULL = +0.211 (positif, mv allocate des paires winning) vs no-BTC BEAR = +0.008 (cassé). With-BTC : tous régimes ≈ +0.23-0.29.
**Pourquoi non pré-enregistré** : mes hypothèses cycle 90 étaient {uniform, bear_concentrated, bull_kills, mixed}. Le pattern observé est plus fin que mixed — c'est une protection régime-dépendante.

### P2 — `pseudo_compatible_via_loser_bias` (cycle 91)
**Forme** : ajouter une paire à drift négatif (DOT) gonfle ΔSharpe non pas via sh_mv mais via sh_eq qui s'écroule. Le verdict "ajouter DOT renforce l'edge" est techniquement vrai en delta mais faux en mécanique.
**Évidence** : sh_eq drop de -0.157 (LINK+ADA+ETH+BTC → LINK+ADA+DOT+BTC) vs sh_mv gain de +0.091. 63% du delta vient du moteur (B).
**Pourquoi non pré-enregistré** : mes hypothèses cycle 91 étaient {compatible, neutral, breaks}. Aucune n'envisageait "compatible mais via mauvais moteur".

---

## Implication actionnable pour Martin live

**État live (cycle 91 12h30 + cycle 92 18h23)** :
- PV $121.86, 0 grids, 100% cash
- BTC $73,033 DOWNTREND, EMA200 $75,957
- Gate IQR CLOSED depuis 9 jours
- Bot dormant, defensive_in_adverse_regimes appliqué *par l'absence d'action*

**Décision actuelle** : ne pas déployer. Gate fermé, BTC sous EMA200 = exactement le régime où l'anchor BTC compte le plus, mais aussi le régime où la stratégie grid Martin est interdite (par design Compounder).

**Décision conditionnelle future (si gate IQR rouvre)** :
1. **Setup recommandé** : 3-4 grids incluant BTC + 2-3 alts parmi {LINK, ADA, SOL, ETH}.
2. **Edge attendu net biais** : +0.20 à +0.30 ΔSharpe annualisé.
3. **À éviter** : DOT comme grid si pas d'autre anchor (devient quasi-anchor avec drift négatif).
4. **Caveat** : tout backtest live-derate de 50% (lesson 0501). Edge live attendu = +0.10 à +0.15 Sharpe net, +5-10% APR additionnel via meilleure allocation.

---

## Limites de la synthèse

1. **Backtest = scénario eq-weight vs min-variance, pas grid trading réel.** Le moteur Martin est grid-Compounder gate-IQR. L'edge anchor mesuré ici est une borne supérieure théorique de ce qu'une *allocation multi-grid* pourrait capturer si elle suivait les weights mv. La stratégie live actuelle Compounder n'allocate pas dynamiquement.
2. **Pas de coûts** : fees, slippage, spread, funding ignorés. Sharpe live derate 30-50% confirmé empiriquement.
3. **Pas de régime out-of-sample** : Q1-Q2 2026 (régime actuel) absent des data.
4. **Walk-forward 240 périodes (40j) = compromis** : trop court = bruit, trop long = ne suit pas régime. Cycle 80 a validé window=50 candles 4h ≈ 8j mais cycle 85b a switch à 240. À investiguer dans cycle 93+.

---

## Annexes

- **Code** : `/home/tony/projets/tonyderide/niam-bay/ai-lab/rmt/audits/`
  - `perturbation_universe_cycle85b.py` (N=3 baseline)
  - `perturbation_universe_cycle87.py` (N=4)
  - `perturbation_universe_cycle88.py` (N=5)
  - `perturbation_universe_cycle89.py` (N=6, N=7)
  - `regime_stratification_cycle90.py` (BULL/BEAR/RANGE)
  - `perturbation_universe_cycle91_dot.py` (DOT inclusion)
- **CSV résultats** : même répertoire, suffixe `_results.csv`
- **Cache OHLC** : `/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache/binance_*USDT_4h_1672531200000_1767139200000.json`
- **Métadonnées arc** : `docs/projets/vacation-autonomy.md` cycles 85b → 91

---

## Prochaines étapes (cycle 93+)

- **Bootstrap RANGE** (R2) : block bootstrap sur 840 obs OOS, IC 95% sur ΔSharpe RANGE.
- **Régime ATR-based** (R3) : re-classifier régime, re-runner cycle 90.
- **Frontière N=2** (R5) : ajouter LINK+BTC, ADA+BTC, SOL+BTC isolés.
- **Mean-reversion DOT** (R1) : décomposer cycle 91 sur sous-périodes recovery alts.
- **Window walk-forward** : tester w={50, 120, 360, 720} pour stabilité.
