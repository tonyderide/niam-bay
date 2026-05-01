# Vacation Runbook — Tony 8 days off (2026-05-01 → 2026-05-09)

## État au départ (2026-05-01 11:48 UTC)

- Portfolio: **$135.32** (baseline, 0 positions)
- Bot Martin: **UP** (RegimeGate v1 deployed 11:39 UTC)
- AutoGrid: ENABLED globally
- 4 grids active: LINK/DOT/SOL/ADA spacing 1.2%, leverage 5x, levels 5
- 8 buy orders posés (2 par grid) — waiting fills
- **Gate state: CLOSED** (3/5 conditions IQR — marché en transition)

## ⚠️ ACTION CRITIQUE AVANT DE PARTIR

**Débloquer `@niambay_bot` dans Telegram**:
1. Ouvrir Telegram
2. Chercher @niambay_bot
3. Click "Restart" ou taper `/start`
4. **Sans ça → AUCUNE alerte ne sera reçue**

## Garde-fous actifs

| Mécanisme | Seuil | Action |
|---|---|---|
| RegimeGate IQR | 5 conditions ADX/EMA/RSI/ATR/price | closeOnly si non-match |
| Hard stop per grid | -15% capital | closePositionAndStopGrid |
| HARD STOP via real Kraken P&L | totalPnl < maxLoss | closePosition + stop grid |
| Daily CB | -3% portfolio | halt 24h |
| Weekly CB | -7% portfolio | halve sizing |
| Absolute floor | $115 (-15% from $135) | killed=true |
| systemctl martin | Restart on-failure 15s | auto-restart |
| sentinel.py | 5min check 24/7 | Telegram alert |
| watchdog.py | cron 15min | Telegram alert |

## Worst case mathématique sur 8 jours

- **Scenario A** — Gate reste CLOSED toute la période: 0 nouvelle position, capital intact ≈ $135
- **Scenario B** — Gate s'ouvre, marché favorable: bot trade Compounder 1.2%, gain potentiel +$1-5/jour selon volatility
- **Scenario C** — Gate s'ouvre, crash macro: hard stops déclenchent à -15% capital × 4 grids = -$24 total. Floor $115 hit avant.
- **Scenario D** — Bug nouveau (6e en 6 semaines): sentinel + watchdog devraient envoyer Telegram. Worst case bot kills self à -$20.

**Floor mathématique absolu**: $115. **Max loss 8j ≈ $20** (-15%).

## Comment vérifier à distance (depuis vacances)

### Via Telegram (si débloqué)
- Sentinel envoie alerte automatique sur HARDSTOP, drawdown, BTC moves
- watchdog.py envoie status toutes 15min si critique

### Via SSH (si tu as un PC)
```bash
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/balance | python3 -c 'import json,sys;d=json.load(sys.stdin)[\"accounts\"][\"flex\"];print(\"PV\",d[\"portfolioValue\"])'
curl -s http://localhost:8081/api/grid/active
curl -s http://localhost:8081/api/signal/regime-gate
"
```

### Via Niam-Bay (Claude Code)
- Lancer `/martin-monitor`
- Lire `~/projets/tonyderide/niam-bay/docs/recent.nb1`

## Comment intervenir à distance si pépin

### Stop everything
```bash
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "
curl -s -X POST http://localhost:8081/api/signal/auto/disable
curl -s -X POST http://localhost:8081/api/strategy/pairs/PF_LINKUSD/disable
curl -s -X POST http://localhost:8081/api/strategy/pairs/PF_DOTUSD/disable
curl -s -X POST http://localhost:8081/api/strategy/pairs/PF_SOLUSD/disable
curl -s -X POST http://localhost:8081/api/strategy/pairs/PF_ADAUSD/disable
"
```

### Rollback jar
```bash
ssh ubuntu@141.253.108.141 "
sudo systemctl stop martin
cp /home/ubuntu/martin/backend.jar.bak-pre-regimegate-1777635565 /home/ubuntu/martin/backend.jar
cp /home/ubuntu/martin/config/strategy.json.bak-pre-regimegate-1777635565 /home/ubuntu/martin/config/strategy.json
sudo systemctl start martin
"
```

### Manual close all positions
```bash
# Via Kraken Pro web interface — fastest
# OR via API:
ssh ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/positions
# Then for each position: place market order with reduceOnly=true via API
"
```

## Backups

- Jar pre-deploy: `/home/ubuntu/martin/backend.jar.bak-pre-regimegate-1777635565`
- Config pre-deploy: `/home/ubuntu/martin/config/strategy.json.bak-pre-regimegate-1777635565`
- DB H2: `/home/ubuntu/martin/data/martindb.mv.db`

## Commits récents

```
9419e18 feat(regime-gate): deploy + observability + Compounder 1.2%
748bfe0 feat(regime-gate): RegimeGate + 333d backtest validation
b54f940 fix(grid): HARD STOP loop on restarted grids
afe1836 fix(grid): 3 patches runaway prevention — deployed prod 0428
```

## Au retour (2026-05-09)

1. Lire ce runbook
2. Lancer `/martin-monitor`
3. Vérifier PV vs $135.32 baseline
4. Lire les Telegram historiques
5. Si bug 6e, audit log + git revert si besoin
6. Ré-évaluer la stratégie à la lumière des résultats live

---

## Bon vacances Tony ! 🌴

Si tu reçois rien sur Telegram pendant 8j → soit tout va bien, soit tu as oublié de débloquer le bot.

Le bot est designé pour **ne rien faire** la plupart du temps (gate CLOSED défensif). C'est le comportement attendu.
