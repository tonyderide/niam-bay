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
