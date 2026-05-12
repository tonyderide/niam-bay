# Option B Tracker

Petit collecteur d'état Martin qui mesure la performance live de la stratégie déployée le 2026-05-11 à 13h Paris (Option B v9) **vs** la courbe attendue dérivée du backtest.

Né du cycle 34 vacation-autonomy. Implémente la règle cycle 33 :

> Après tout deploy, faire un *comparable* vs best-known pour quantifier le coût de la prudence.

## Pourquoi

Sans mesure de référence, une stratégie peut sembler « marcher » alors qu'elle dérive sous le backtest, ou inversement paraître échouer alors que ce n'est que du bruit court. Le tracker donne une réponse honnête à : « depuis le deploy, on est ahead, on-track, ou behind ? »

## Référentiel Option B

- **Deploy** : 2026-05-11 13:00 Paris (11:00 UTC)
- **Baseline PV** : $138.21 (après close LINK pre-deploy +$1.00 réalisé)
- **Backtest** : +15.9% / 30j net (sweep `volume_sweep_results.json`, DOT 1.5% + LINK 3% + ADA 3%, 4 levels, leverage 7x, maxLoss 10%)
- **Live attendu** : ~+8.0% / 30j (règle empirique : derate 50% du backtest, validée multi-sources)

## Usage

```bash
# Snapshot + report (append à snapshots.jsonl)
python3 scripts/option-b/tracker.py

# JSON brut (pour scripting)
python3 scripts/option-b/tracker.py --json

# Historique tabulé
python3 scripts/option-b/tracker.py --history

# Ne pas sauvegarder ce snapshot
python3 scripts/option-b/tracker.py --no-save
```

## Output

Le tracker produit 4 sections :

1. **État live** — PV, uPnL, grids actives, BTC + cushion EMA200
2. **Par grid** — capital, uPnL, RT complets, fills, SL Kraken, flag closeOnly
3. **Vs backtest** — écoulé / cumul deploy / diff vs realistic curve + backtest curve
4. **Verdict** — bucketé selon écart à la realistic curve :
   - `TROP-TOT` (< 24h, bruit dominant)
   - `AHEAD` (> +2%)
   - `ON-TRACK` (±2%)
   - `BEHIND` mais tolérable (-2 à -5%)
   - `BEHIND-CRITIQUE` (< -5%)

## Storage

`data/snapshots.jsonl` — 1 JSON par ligne, append-only. Lisible avec `jq`, `cat`, ou via `--history`.

Format snapshot :
```json
{
  "ts": "ISO8601",
  "pv": 140.74,
  "balanceValue": 140.72,
  "uPnL": 0.025,
  "uptime_h": 1.62,
  "btc": {"price": ..., "ema200": ..., "rsi": ..., "trend": ..., "signal": ...},
  "active_grids": ["PF_LINKUSD", ...],
  "per_grid": {
    "PF_LINKUSD": {"capital": 46, "krakenUnrealizedPnl": ..., "completedRoundTrips": 0, ...}
  }
}
```

## Cadence suggérée

- **24-72h post-deploy** : 1 run / 4-6h (le bruit market-mark-to-market domine encore)
- **3-30j** : 1 run / jour (signal grid trading commence à émerger)
- **après 30j** : 1 run / 3-7j (verdict final)

Tony peut câbler ça en cron VM si besoin, ou laisser NB faire ça lors des cycles autonomes (1 ligne dans martin-monitor).

## Limites

- La courbe attendue est **linéaire** (interpolation). Le PnL réel est par à-coups (chaque RT = +0.5-2$ d'un coup, puis plateau).
- Le PV inclut le mark-to-market des positions non fermées → en early-deploy, le tracker reflète surtout le mouvement de prix BTC/alts, pas la performance grid.
- Le backtest était sur Binance spot. Live = Kraken Futures. Funding rate non modélisé (~0.03-0.1%/jour).
- Cassure régime (BTC < EMA200, kill-switch, etc.) → tracker continue à fonctionner mais le référentiel devient caduc.

## Évolutions possibles

- Comparer aussi vs **niveau 1** (config actuelle no-vol-filter, +6.87%/30j backtest)
- Ajouter `--alert` qui envoie Telegram si verdict ∈ {`BEHIND-CRITIQUE`}
- Ajouter export CSV pour plot externe
- Cron VM toutes les 6h (alternative au script local)

Pas implémenté faute de besoin actuel — au-delà du MVP.

---

## `drift_check.py` — sanity check Kraken vs Martin internal (cycle 35)

Outil complémentaire au tracker. Le tracker mesure **la performance**. `drift_check` mesure **la cohérence de l'état interne**.

### Pourquoi

Le bug `phantom fills` (0423) et le bug `StopLossManager silent failure` (0510) ont la même nature : Martin pense quelque chose, Kraken pense autre chose, personne ne crie. Le memo `[verify-via-cancel-test]` du `patterns.nb1` (0510:08h) dit exactement la règle :

> validate critical state via Kraken pas Martin internal grid-status

Ce script l'opérationnalise.

### Ce qu'il détecte

| Catégorie | Description | Sévérité |
|---|---|---|
| `phantom_placed` | Level Martin = `PLACED` + `krakenOrderId` mais cet id n'existe pas dans `bot/orders` Kraken. Silent failure type. | **CRITIQUE** |
| `sl_mismatch` | `grid.stopLossOrderId` non null mais absent côté Kraken. Bug `StopLossManager` 0510 type. | **CRITIQUE** |
| `count_drift` | Total levels `PLACED` Martin ≠ total orders `lmt` Kraken pour le même symbole. | **WARN** |
| `orphaned_kraken` | Order Kraken vivant qu'aucun level Martin ne revendique. Souvent leftover. | **INFO** |

### Usage

```bash
python3 scripts/option-b/drift_check.py             # report + append si drift
python3 scripts/option-b/drift_check.py --json      # raw
python3 scripts/option-b/drift_check.py --history   # voir tous les drifts passés
```

Exit code : `0` si propre, `1` si drift détecté, `2` si erreur. Cron-friendly.

### Storage

`data/drifts.jsonl` — append-only **uniquement si drift détecté**. Si le bot est sain, le fichier reste vide / inexistant. Pas de spam.

### Cadence suggérée

Au moins 1× / 6h en autonomie. Plus si bot vient de redémarrer ou si un deploy vient d'avoir lieu.

### Limites

- Ne corrige rien — il signale uniquement. La décision (kill grid, replacer SL, restart bot) reste humaine.
- Un `orphaned_kraken` n'est pas toujours un bug : un sell-side level Martin pose un `lmt reduceOnly` sur Kraken et Martin le track via le level lui-même, pas par id. Le script signale tout ce qui n'a pas été revendiqué — Tony interprète.
- Si le bot est down (SSH timeout), `drift_check` plante (exit code 2). C'est attendu : pas de bot = pas de drift à mesurer, c'est martin-monitor qui prend le relais.

