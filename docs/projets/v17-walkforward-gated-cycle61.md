# Cycle 61 — Walk-forward gated v17 avec W4 alimenté

**Date** : 2026-05-19 06h30 Paris
**Préc.** : [`v17-walkforward-gated-cycle60.md`](v17-walkforward-gated-cycle60.md)
**Question** : cycle 60 avait W4 vide (cache 4h s'arrête 2025-12-31). Cycle 61 étend le cache et mesure si la reco bouge.

## Contexte cycle 60 (rappel)

Sur 3 fenêtres valides (W1+W2+W3 = 209j) :

| Config | Cycle 60 PnL | Rank |
|---|---:|:-:|
| A Tony 3.0% | +$20.77 | **#1** |
| D wide 4.0% | +$15.43 | #2 |
| E 6lv 2.0% | +$10.44 | #3 |
| C med 2.0% | -$1.25 | #4 |
| B tight 1.5% | -$3.74 | #5 |

W4 (avril-mai 2026, 30j mild+) sortait UNKNOWN car les 4h candles 2026 manquaient.

## Étape 1 — Extension du cache 4h

Écriture `fetch_4h_2026_extension.py`. Binance public klines `/api/v3/klines?interval=4h`. Récupère le segment **2026-01-01 → 2026-05-19** pour 6 paires (BTC, ETH, LINK, ADA, DOT, SOL) et écrit `binance_{PAIR}USDT_4h_extended.json` (concat hist + 2026).

Résultat fetch :

```
BTCUSDT  : 7406 bars (6571 hist + 835 new)  2023-01-01 → 2026-05-19
ETHUSDT  : 7406 bars (idem)
LINKUSDT : 7406 bars (idem)
ADAUSDT  : 7406 bars (idem)
SOLUSDT  : 7406 bars (idem)
DOTUSDT  : 7406 bars (fetched full history depuis 0, fichier était manquant)
```

DOTUSDT 4h n'existait pas du tout dans le cache historique. Cycle 61 le crée.

## Étape 2 — Patch loader

`v17_walkforward_gated_backtest.py` ligne 71-90 :

```python
FOUR_H_EXTENDED_FILE = CACHE / "binance_{pair}USDT_4h_extended.json"
...
def load_4h_or_none(pair: str) -> List[List]:
    ext = Path(str(FOUR_H_EXTENDED_FILE).format(pair=pair))
    if ext.exists():
        return load_candles(ext)
    p = Path(str(FOUR_H_FILE).format(pair=pair))
    if not p.exists():
        return []
    return load_candles(p)
```

Préfère l'extended si présent, fallback historique sinon (compat pour scripts plus anciens).

## Étape 3 — Re-run

60 simulations (4 fenêtres × 3 paires × 5 configs). Run complet en ~3s.

### Résultat W4 (nouveau)

```
W4 mild+ 30j (start 2026-04-12)
  LINK 30j +17.0% | gate 4h bars 7368 | gate window 123/180 OPEN (68%)
     A Tony 3.0% : PnL=+$4.20  fills=5   maxDD=4.70%
     B tight 1.5%: PnL=+$3.99  fills=18  maxDD=9.41%
     C med 2.0%  : PnL=+$3.50  fills=12  maxDD=9.40%
     D wide 4.0% : PnL=+$1.31  fills=2   maxDD=2.95%
     E 6lv 2.0%  : PnL=+$2.33  fills=12  maxDD=6.26%
  ADA 30j +13.8% | gate window 137/180 OPEN (76%)
     A Tony 3.0% : PnL=-$0.31  fills=6   maxDD=9.76%
     B tight 1.5%: PnL=-$0.96  fills=15  maxDD=9.03%
     C med 2.0%  : PnL=+$0.59  fills=12  maxDD=8.63%
     D wide 4.0% : PnL=-$0.84  fills=3   maxDD=6.42%
     E 6lv 2.0%  : PnL=-$0.40  fills=13  maxDD=9.14%
  ETH 30j +3.6% | gate window 126/180 OPEN (70%)
     A Tony 3.0% : PnL=+$2.32  fills=7   maxDD=8.63%
     B tight 1.5%: PnL=-$6.86  fills=15  maxDD=9.73%
     C med 2.0%  : PnL=-$6.53  fills=12  maxDD=9.56%
     D wide 4.0% : PnL=+$0.01  fills=3   maxDD=5.19%
     E 6lv 2.0%  : PnL=-$3.58  fills=14  maxDD=9.58%
```

**Constat W4** :
- Gate OPEN 68-76% du temps en régime mild+ (vs 4-46% sur W1-W3 plus durs)
- ETH régime choppy : Tony 3.0% +$2.32 mais tight/med/6lv tous **-$3.6 à -$6.9** (overtrade dans whipsaws)
- LINK régime bullish franc : tous configs positifs
- ADA quasi-neutral : seul C med 2.0% positif

### Ranking total cycle 61 (4 fenêtres × 3 paires)

| Config | Cycle 60 (W1+W2+W3) | **Cycle 61 (W1+W2+W3+W4)** | Δ W4 | Rank 61 | meanRank |
|---|---:|---:|---:|:-:|:-:|
| **A Tony 3.0%** | +$20.77 | **+$26.98** | +$6.21 | **#1** | 1.75 |
| **D wide 4.0%** | +$15.43 | +$15.92 | +$0.48 | #2 | **1.50** ← le plus stable |
| E 6lv 2.0% | +$10.44 | +$8.79 | -$1.65 | #3 | 3.25 |
| C med 2.0% | -$1.25 | -$3.70 | -$2.45 | #4 | 3.75 |
| B tight 1.5% | -$3.74 | -$7.58 | -$3.84 | #5 | 4.75 |

### Stabilité par fenêtre (rank, 1=best)

| Config | W1 bear | W2 bull | W3 bear | W4 mild+ | meanRank |
|---|:-:|:-:|:-:|:-:|:-:|
| A Tony 3.0% | 2 | **1** | 3 | **1** | 1.75 |
| B tight 1.5% | 4 | 5 | 5 | 5 | 4.75 |
| C med 2.0% | 5 | 4 | 2 | 4 | 3.75 |
| D wide 4.0% | **1** | 2 | **1** | 2 | **1.50** |
| E 6lv 2.0% | 3 | 3 | 4 | 3 | 3.25 |

## Lecture honnête

### 1. Tony 3.0% confirmé #1 en magnitude

+$26.98 cumul vs +$15.92 D wide = **+$11.06 différentiel sur 239j**. W4 (mild+) ajoute +$6.21 favorables. La reco cycle 60 (garder v17) **se renforce**, n'est pas inversée.

### 2. D wide 4.0% gagne en stabilité — pas en magnitude

mean rank 1.50 (D wide) vs 1.75 (Tony 3.0%) — différence très faible (0.25 rank). Mais D wide ne domine **jamais en magnitude** sur W2 (+$3.74 contre Tony +$13.32 = 3.6x moins) et W4 (+$0.48 contre Tony +$6.21 = 13x moins).

**Trade-off** : D wide = "ne perd jamais beaucoup, ne gagne jamais beaucoup". Tony 3.0% = "capture franc en bull/mild+, accuse en bear".

Pour Martin live avec gate qui ferme en bear : **Tony 3.0% capture le upside où le gate ouvre, accepte l'underperformance W1/W3 que le gate filtre déjà**. Cohérent.

### 3. Tight 1.5% est désormais clairement le pire

-$7.58 cumul, mean rank 4.75, **dernier sur 3 des 4 fenêtres**. Bug Python cycle 59 (qui avait fait croire que tight gagnait en no-gate) avait masqué la médiocrité empirique. Cycle 60 a déjà invalidé la reco "switch v18 tight". Cycle 61 enfonce le clou : sur la 4e fenêtre la plus représentative du présent (mild+ avril-mai 2026), tight perd $3.84 supplémentaires.

### 4. 0 hard-stop sur 60 simulations gated (confirmation cycle 60)

Le gate IQR V4 (RSI[36,66] + ATR%[1.12,2.17]) filtre suffisamment pour qu'aucun grid ne touche le maxLoss 10% sur 239j × 3 paires × 5 configs. Le hard-stop reste un firewall théorique en backtest gated.

### 5. ETH whipsaw en mild+ — divergence config majeure

W4 ETH : Tony +$2.32 vs tight -$6.86 = **+$9.18 différentiel sur 30j 1 paire**. Le régime mild+ avec choppy bars sanctionne le spacing trop fin qui sur-trade les fausses cassures. Cohérent avec l'inertie observée live sur ETH.

## Reco finale cycle 61 pour Tony

**Confirmer v17 spacing 3.0%, ne pas dévier.**

3 cycles d'analyse convergent maintenant :
- Cycle 58 : Tony deploy v17 3.0% validé naïvement (bug masqué)
- Cycle 59 : bug trouvé, "tight wins en no-gate" — vrai mais hors prod
- Cycle 60 : gate modélisé → Tony 3.0% wins en prod (+$20.77 sur 209j)
- **Cycle 61 : W4 ajoutée → Tony 3.0% wins +$26.98 sur 239j**

D wide 4.0% est l'**alternative de prudence** (mean rank 1.50, moins de risque de mauvaise fenêtre) mais sacrifie 41% du upside cumul. Pas un argument pour switcher si Tony est confortable avec la magnitude actuelle.

## Findings cycle 61

- `[finding|0519:06h|cache-4h-2026-étendu|6-paires-incluant-DOTUSDT-créé|2023-01→2026-05|7406-bars-par-paire|fetch_4h_2026_extension.py]`
- `[finding|0519:06h|W4-mild+-30j-gate-OPEN-68-76%|vs-4-46%-W1-W3-bear/bull-stricts|régime-mild+-laisse-le-gate-plus-permissif]`
- `[finding|0519:06h|Tony-3.0%-+$26.98-cumul-239j-gated|+$11-vs-D-wide-4.0%|reco-cycle-60-renforcée-non-invalidée]`
- `[finding|0519:06h|D-wide-4.0%-meanRank-1.50-vs-Tony-1.75|stabilité-marginalement-meilleure-mais-magnitude-2x-inférieure|trade-off-pas-décisif]`
- `[finding|0519:06h|tight-1.5%-W4-ETH-perd-$6.86-en-30j|whipsaw-mild+-sanctionne-spacing-fin|Tony-3.0%-+$2.32-sur-même-data]`
- `[finding|0519:06h|0-hard-stop-sur-60-simulations-cycle-61|gate-V4-RSI+ATR-suffit-vérifié-sur-4-windows-cumul-239j]`
- `[lesson|0519:06h|3-cycles-consécutifs-convergent-sur-Tony-3.0%|58-naïve-59-faux-60-validé-61-renforcé|honnêteté-itérative-paie-2-fois]`
- `[pattern|0519:06h|extend-cache-debloque-window-=-pattern|toute-fenêtre-future-rebloque-au-fil-temps|à-refaire-tous-mois-pour-W5/W6/...]`

## Cycle 62 — pistes possibles

1. **Walk-forward gated avec auto-unstuck modélisé** — fermer la dernière abstraction live, encore plus proche du prod
2. **Audit Java reset `hasBuyFill` après trim** — fix mineur reporting (mentionné cycle 60)
3. **Backtest gated × DCA × BTC SHORT** — cycle 56→57 avait généré +$0.65, voir si la combo gate+DCA+short tient sur 239j
4. **Sortir du Martin** : reprendre angular-audit Step 1 playbook (revenue path)
5. **Skill autonome `extend-4h-cache`** — wrapper du fetcher pour usage récurrent

## Métriques cycle 61

- **Durée** : ~50min (wake + martin-monitor + lecture cycle 60 + analyse W4 vide + fetcher + 1 patch + run + analyse + doc)
- **Modif VM** : 0 (frontière tient 20 jours)
- **Modif Kraken** : 0
- **Modif code Martin** : 0
- **Fichiers niam-bay créés** : 2 (`fetch_4h_2026_extension.py`, ce fichier)
- **Fichiers niam-bay modifiés** : 1 (`v17_walkforward_gated_backtest.py` — 1 patch loader)
- **Caches créés** : 6 (`binance_{PAIR}_4h_extended.json`)
- **Simulations** : 60 backtests gated avec W4 désormais alimenté
- **Live state final** : Martin UP 1d 3h 35m, 2 grids LINK+ADA neuves ~3h, PV $126.85, 0 position, BTC $76,681 DOWNTREND
