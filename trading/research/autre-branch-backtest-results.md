# Backtest Results — Actual Runs (2026-03-22)

All scripts run from `C:/martin/backtest/` on real ETH candle data.
Every script includes fees (0.055% per side = 0.11% round trip unless noted).
Capital: 100 EUR/USD, Leverage: 10x, Stake: 5 EUR notional 50 EUR.

---

## 1. backtest_v8_final.py

**Data:** ETH 15m candles, 3 weeks (IS: Mar 8-15, OOS1: Mar 1-8, OOS2: Feb 22-Mar 1)
**Method:** Grid search of 864 Strategy O variants (RSI + EMA cross + ADX filter), plus Strategy P (trend breakout) and Strategy Q (momentum score). Validated IS winners on OOS.
**Fees:** Yes (included in PnL)

### Strategy O — Best validated configs (3-week total):

| Config | Trades | Win Rate | Total PnL | Validation |
|--------|--------|----------|-----------|------------|
| RSI14x55 EMA5/21 ADX>15 TP2.0x SL1.5x | 80 | ~49% | **-$0.40** | FAIL (2/3 weeks profitable but IS week offset losses) |
| RSI14x55 EMA9/21 ADX>15 TP4.0x SL1.5x | 75 | ~48% | **+$5.75** | PASS (2/3 weeks profitable) |
| RSI14x55 EMA9/21 ADX>15 TP3.0x SL1.5x | 75 | ~48% | **+$3.05** | PASS |
| RSI14x55 EMA13/21 ADX>15 TP2.0x SL1.5x | 72 | ~50% | **+$1.33** | PASS |

### Strategy P — Pure Trend Following (20-bar breakout + ADX + DI):
- **1 trade in 3 weeks.** PnL: -$0.45. Useless.

### Strategy Q — Momentum Score (RSI + EMA spread + ADX):
- **85 trades, 2/3 weeks profitable**
- **Total PnL: +$7.80** (best overall)
- IS: -$3.23 (45% WR), OOS1: +$3.98 (61% WR), OOS2: +$7.04 (64% WR)
- **Winner declared by the script.**

**Verdict:** Strategy Q won but IS period was negative — possible curve-fit concern. +$7.80 on $10 capital = +78% over 3 weeks, but only on ~85 trades. Tiny sample.

---

## 2. mega_compare.py

**Data:** ETH 5m, 3 months (Dec 16 2025 - Mar 16 2026)
**Method:** All signal types x trailing configs x martingale variants. Starting capital $10.
**Fees:** Yes (implicit in trailing/SL mechanics)

### Top 20 by Profit Factor (min 30 trades):

**Everything lost money or broke even.** The best result:

| # | Signal | Trail | Mart | Trades | WR | Net PnL | MaxDD | PF |
|---|--------|-------|------|--------|----|---------|-------|----|
| 1 | EMA 9/21 Cross | W2.5->T2.0 | No Mart | 115 | 42.6% | **-$0.001** | $10.59 | 1.00 |
| 2 | BB Mean Rev | W3.0->T1.5 | No Mart | 147 | 45.6% | -$9.28 | $72.70 | 0.93 |
| 6 | EMA 9/21 Cross | Flat 2.0% | No Mart | 125 | 40.0% | -$4.36 | $10.95 | 0.86 |

**No strategy was profitable over 3 months on 5m candles.** The best (EMA 9/21 Cross) essentially broke even at -$0.001. Martingale variants made losses worse in every case.

**Verdict:** Complete failure. No edge found on 5m timeframe over 3 months.

---

## 3. full_comparison.py

**Data:** ETH 5m, 30 days (Feb 13 - Mar 13, 2026)
**Method:** 15 strategies compared (RSI, Stoch, MACD combos, divergences, mean reversion). Small positions.
**Fees:** Yes (included)

### Final Ranking (30-day PnL):

| # | Strategy | 30d PnL | Trades | WR | MaxDD |
|---|----------|---------|--------|----|-------|
| 1 | MACD+Stoch Combo | **+$2.40** | 56 | 39.3% | $4.53 |
| 2 | RSI+Stoch+EMA | -$0.05 | 3 | 33.3% | $0.75 |
| 3 | RSI+Stoch Trailing | -$1.40 | 83 | 47.0% | $1.88 |
| 4 | RSI+Stoch Optimized | -$2.01 | 82 | 39.0% | $4.13 |
| 14 | RSI Div Tight | -$8.26 | 180 | 34.4% | $3.15 |
| 15 | RSI Mean Rev Simple | **-$19.31** | 233 | 29.2% | $5.10 |

**Only 1 out of 15 strategies was profitable (MACD+Stoch at +$2.40).** The rest all lost money. Mean reversion was the worst (-$19.31). More trades generally = more losses.

**Verdict:** One marginally profitable strategy, but +$2.40 on 56 trades over 30 days is noise.

---

## 4. final_momentum_swing.py

**Data:** ETH 5m, ~1 year (104,505 candles), aggregated to 5m/15m/30m/60m
**Method:** MomScore and MACD+RSI signals with various lookbacks, trailing stops, martingale variants. Capital $100.
**Fees:** Yes (0.055% per side)

### Results by Timeframe:

| Timeframe | Best Config | Trades | WR | Net PnL | MaxDD | PF |
|-----------|-------------|--------|----|---------|-------|----|
| 5m | All configs | 1200-2500 | 26-28% | **-$65 to -$99** | 70-99% | 0.57-0.86 |
| 15m | All configs | 537-1035 | 27-30% | **-$11 to -$83** | 44-84% | 0.76-0.97 |
| 30m | MomScore LB15 0.3% Mart2x | 308 | 30.5% | **+$287.50** | 46.2% | 1.29 |
| 30m | MACD+RSI LB12 0.1% NoMart | 573 | 31.4% | **+$85.12** | 35.0% | 1.21 |
| 60m | MACD+RSI LB15 0.2% Mart2x | 255 | 28.6% | **+$149.71** | 76.2% | 1.37 |

**Script's declared winner:** MACD+RSI LB15 0.2% Mart2x_H2 on 60m
- 255 trades, 28.6% win rate, **+$149.71 (+150%)**, PF 1.37
- MaxDD: 76.2% (!)
- Monthly breakdown: 8/13 months profitable
- Worst streak: 12 consecutive losses
- Feb 2026: +$94.72, Mar 2026: +$55.69 (recency bias?)

**Real winner (risk-adjusted):** MomScore LB15 0.3% NoMart on 30m
- 308 trades, 28.9% WR, **+$51.65**, MaxDD only 23.1%, PF 1.14

**Verdict:** 5m and 15m are all losers. 30m and 60m show some promise but with very high drawdowns. The +$287.50 on 30m Mart2x had 46% drawdown. The 60m winner had 76% drawdown — nearly wiped out before recovering.

---

## 5. agent10_combiner.py

**Data:** ETH 5m, ~1 year. Split 9 months IS / 3 months OOS.
**Method:** Combined signals (Large Body, Z-score, Inside Bar, RSI, Volume Spike) with various combination logic (Confirm, Regime, Majority, Weighted, Sequential). Capital 100 EUR.
**Fees:** Yes (0.055% per side)

### Top 10 OUT-OF-SAMPLE (min 100 trades):

| # | Strategy | Trades | WR | PnL | MaxDD | PF |
|---|----------|--------|----|-----|-------|----|
| 1 | C4_Weighted(th=2.2) tr=2.0% sl=4.0% | 159 | 37.7% | **+18.62 EUR (+18.6%)** | 9.5% | 1.30 |
| 2 | C2_Regime(40) tr=2.0% sl=3.0% | 147 | 39.5% | **+15.37 EUR (+15.4%)** | 10.4% | 1.28 |
| 3 | C2_Regime(40) tr=2.0% sl=4.0% | 147 | 39.5% | +15.37 EUR | 10.4% | 1.28 |
| 4 | C4_Weighted(th=2.2) tr=2.5% sl=4.0% | 114 | 43.0% | +14.38 EUR | 8.2% | 1.28 |
| 5 | C4_Weighted(th=2.2) tr=2.0% sl=3.0% | 159 | 37.7% | +17.37 EUR | 9.5% | 1.27 |

### In-Sample best:
- C1_Confirm tr=2.5% sl=2.0%: 393 trades, 36.1% WR, **+48.33 EUR**, MaxDD 11.4%, PF 1.24

**Verdict:** This is the most rigorous script (proper IS/OOS split, fees, min trade count). The best OOS result is +18.6% over 3 months with only 9.5% drawdown and PF 1.30. This is the most credible edge found, but it's still modest.

---

## Overall Summary

| Script | Best Result | Timeframe | Fees | Credibility |
|--------|-------------|-----------|------|-------------|
| backtest_v8_final | +$7.80 (Strategy Q) | 15m, 3 weeks | Yes | LOW — tiny sample, IS period was negative |
| mega_compare | -$0.001 (breakeven) | 5m, 3 months | Yes | HIGH — confirms no edge on 5m |
| full_comparison | +$2.40 (MACD+Stoch) | 5m, 30 days | Yes | LOW — marginal, likely noise |
| final_momentum_swing | +$287.50 (30m MomScore Mart2x) | 30m, 1 year | Yes | MEDIUM — good sample but 46% drawdown, martingale inflates returns |
| agent10_combiner | +18.62 EUR OOS (Weighted combo) | 5m, 3mo OOS | Yes | **HIGHEST** — proper IS/OOS, PF 1.30, 9.5% MaxDD |

### Key Takeaways

1. **5-minute timeframe is a graveyard.** Every comprehensive test on 5m over 3+ months shows no edge or losses after fees.
2. **30m and 60m show some promise** but with dangerous drawdowns (46-76%).
3. **Martingale makes everything worse** on 5m, and inflates apparent returns on longer TF while massively increasing drawdown.
4. **The only credible OOS edge** is agent10_combiner's weighted signal combo: +18.6% over 3 months, 9.5% drawdown, PF 1.30. But that's ~6%/month which could still be a statistical fluke on one 3-month window.
5. **Win rates are universally low** (26-43%). Strategies rely on winners being larger than losers, not on being right often.
6. **All fees are included** at 0.055% per side (Kraken taker rate). This is a significant drag — many strategies that look marginal before fees become losers after.
