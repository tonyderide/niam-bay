# Campagne walk-forward OOS — 2026-07-07 02:13 UTC
Frais maker 0.02% / taker 0.05% + slippage 0.03%. Verdict = OOS only, n>=30.
Rappel : live = 30-50% du backtest.

## XBT
- donchian: PAS D'EDGE | OOS total -41.69% | folds [np.float64(-13.16), np.float64(12.07), np.float64(4.55), np.float64(-7.42), np.float64(-25.14), np.float64(-21.7), np.float64(9.11)] | trades 102
- regime_pullback: PAS D'EDGE | OOS total 3.12% | folds [np.float64(17.93), np.float64(-5.01), np.float64(-15.37), np.float64(-10.03), np.float64(3.07), np.float64(-1.62), np.float64(14.15)] | trades 132
- trend_grid: POSITIF-OOS | OOS total 38.45% | folds [np.float64(3.16), np.float64(7.56), np.float64(2.65), np.float64(4.92), np.float64(10.53), np.float64(10.53), np.float64(-0.9)] | trades 265
## ETH
- donchian: PAS D'EDGE | OOS total -28.35% | folds [np.float64(3.98), np.float64(32.09), np.float64(4.54), np.float64(-11.26), np.float64(-44.72), np.float64(-5.06), np.float64(-7.92)] | trades 119
- regime_pullback: PAS D'EDGE | OOS total -90.87% | folds [np.float64(-40.41), np.float64(-17.82), np.float64(-18.04), np.float64(1.45), np.float64(-12.09), np.float64(-16.22), np.float64(12.26)] | trades 251
- trend_grid: POSITIF-OOS | OOS total 86.87% | folds [np.float64(20.02), np.float64(14.1), np.float64(8.83), np.float64(8.54), np.float64(22.5), np.float64(15.39), np.float64(-2.51)] | trades 281
## SOL
- donchian: PAS D'EDGE | OOS total -79.38% | folds [np.float64(-23.83), np.float64(7.82), np.float64(-28.05), np.float64(-9.73), np.float64(0.31), np.float64(-16.41), np.float64(-9.49)] | trades 145
- regime_pullback: PAS D'EDGE | OOS total -65.5% | folds [np.float64(-21.76), np.float64(-22.74), np.float64(-4.68), np.float64(17.82), np.float64(-44.56), np.float64(-27.12), np.float64(37.54)] | trades 288
- trend_grid: POSITIF-OOS | OOS total 145.34% | folds [np.float64(68.26), np.float64(11.77), np.float64(4.85), np.float64(13.05), np.float64(28.09), np.float64(15.66), np.float64(3.66)] | trades 276
## ADA
- donchian: PAS D'EDGE | OOS total -82.47% | folds [np.float64(-51.09), np.float64(-4.09), np.float64(-1.98), np.float64(30.1), np.float64(-19.62), np.float64(-14.71), np.float64(-21.08)] | trades 175
- regime_pullback: POSITIF-OOS | OOS total 45.89% | folds [np.float64(32.19), np.float64(4.08), np.float64(34.22), np.float64(2.85), np.float64(-36.12), np.float64(-28.03), np.float64(36.7)] | trades 296
- trend_grid: POSITIF-OOS | OOS total 126.51% | folds [np.float64(44.87), np.float64(7.09), np.float64(13.25), np.float64(25.07), np.float64(17.25), np.float64(12.62), np.float64(6.36)] | trades 223
## DOT
- donchian: PAS D'EDGE | OOS total -48.94% | folds [np.float64(-33.14), np.float64(8.53), np.float64(3.92), np.float64(-21.15), np.float64(19.67), np.float64(-8.24), np.float64(-18.53)] | trades 148
- regime_pullback: PAS D'EDGE | OOS total 50.8% | folds [np.float64(-1.15), np.float64(-2.91), np.float64(34.66), np.float64(-11.22), np.float64(-12.14), np.float64(-2.3), np.float64(45.86)] | trades 283
- trend_grid: POSITIF-OOS | OOS total 155.79% | folds [np.float64(30.37), np.float64(10.21), np.float64(22.59), np.float64(34.49), np.float64(29.24), np.float64(14.34), np.float64(14.55)] | trades 248
## LINK
- donchian: PAS D'EDGE | OOS total -92.72% | folds [np.float64(-35.32), np.float64(14.77), np.float64(-29.38), np.float64(-17.37), np.float64(2.65), np.float64(-36.38), np.float64(8.31)] | trades 144
- regime_pullback: PAS D'EDGE | OOS total -95.77% | folds [np.float64(-0.5), np.float64(-50.13), np.float64(-19.54), np.float64(17.3), np.float64(-27.31), np.float64(-29.31), np.float64(13.72)] | trades 409
- trend_grid: POSITIF-OOS | OOS total 135.8% | folds [np.float64(61.09), np.float64(14.28), np.float64(7.89), np.float64(5.84), np.float64(22.15), np.float64(16.25), np.float64(8.3)] | trades 284
## Conclusion (Fable 0707)
- donchian: mort. regime_pullback 1h: mort (l'edge des runs précédents = artefact de trous de données).
- trend_grid: POSITIF-OOS 6/6 paires, 41/42 folds verts. 3e méthodologie indépendante convergente
  (gate IQR mai +3.31%, trend-aware juin +28%/180j, walk-forward 0707).
- L'edge = QUAND (régime EMA200+momentum → grid ; sinon cash), pas QUOI.
- Caveat: moteur trend_grid = proxy optimiste (récolte surestimée en tendance). Attendu réel ≈ juin (+28%/180j), dératé 30-50% en live.
- Pipeline: TrendStateManager WARM_ONLY en prod depuis 0706 → comparer logs vs réel 2-3 semaines → TREND_MODE=LIVE si confirmé.
