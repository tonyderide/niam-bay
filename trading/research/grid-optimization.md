# Grid Trading Optimization for Kraken Futures

**Date:** 2026-03-22
**Author:** Niam-Bay research
**Context:** Martin Grid running on ETH since 2026-03-20, $8.82 capital, 0.5% spacing, 3x leverage

---

## 0. Disclaimer up front

There is no unbeatable strategy. Grid trading is a **mean-reversion bet**: it profits when price oscillates and bleeds when price trends. Every number below assumes range-bound conditions. A 15% crash will destroy any grid, regardless of spacing. The math here is honest — including the parts that hurt.

---

## 1. Fee Structure Analysis

### Kraken Futures fees
| Order type | Fee |
|-----------|-----|
| Maker (limit) | 0.02% |
| Taker (market) | 0.05% |

A round-trip (RT) = 1 buy + 1 sell. If both are limit orders (maker):
- **RT fee = 0.04% of notional**

If one side is taker (e.g., stop-loss hit as market order):
- **RT fee = 0.07% of notional**

### Minimum profitable spacing by capital level

For a grid trade to be profitable, the spacing must exceed the RT fee cost. With pure maker orders:

**Minimum spacing = RT fee = 0.04%**

But that's break-even. For meaningful profit, we need spacing >> fees.

**Profit per RT = (spacing - RT_fee) x notional**

| Capital | Leverage | Notional/level | Spacing 0.3% | Spacing 0.5% | Spacing 1.0% |
|---------|----------|---------------|---------------|---------------|---------------|
| **$10** | 3x | ~$3.75 | $0.0098 | $0.0173 | $0.0360 |
| **$100** | 3x | ~$37.5 | $0.0975 | $0.1725 | $0.3600 |
| **$1,000** | 3x | ~$375 | $0.975 | $1.725 | $3.600 |

*Assuming 8 grid levels, so notional per level = capital x leverage / 8*

**Fee as % of profit:**

| Spacing | Fee impact (maker RT) |
|---------|----------------------|
| 0.3% | 13.3% of gross profit eaten by fees |
| 0.5% | 8.0% |
| 1.0% | 4.0% |
| 2.0% | 2.0% |

**Conclusion:** At 0.5% spacing with maker orders, fees eat ~8% of profit. Acceptable. Below 0.3%, fees become punishing. The fee structure is the same regardless of capital — it's a percentage game.

---

## 2. Optimal Spacing by Asset (Volatility-Based)

### Daily ATR estimates (typical, not extreme)

| Asset | Daily ATR % | Intraday range | Character |
|-------|------------|----------------|-----------|
| **ETH** | 2-4% | $40-90 at $2100 | Medium-high vol, good for grids |
| **BTC** | 1.5-3% | $1000-2500 at $85k | Lower vol %, higher $ moves |
| **SOL** | 3-6% | $4-10 at $140 | High vol, fast moves |
| **XRP** | 2-5% | $0.01-0.03 at $0.55 | Pump-dump patterns, gaps |

### Optimal spacing formula

The sweet spot for grid spacing is:

**Optimal spacing = ATR_daily / (2 x number_of_desired_RTs_per_day)**

But also constrained by: **spacing >= 5x RT_fee** (to keep fees under 20% of profit)

| Asset | Conservative spacing | Aggressive spacing | Recommended |
|-------|--------------------|--------------------|-------------|
| **ETH** | 1.0-1.5% | 0.4-0.6% | **0.5-0.8%** |
| **BTC** | 0.8-1.2% | 0.3-0.5% | **0.5-0.7%** |
| **SOL** | 1.5-2.5% | 0.6-1.0% | **0.8-1.2%** |
| **XRP** | 1.5-3.0% | 0.5-1.0% | **1.0-1.5%** |

**Why these numbers:**
- If spacing is too tight relative to ATR, the grid fills all levels quickly during a trend and gets stuck.
- If spacing is too wide, the grid barely executes any RTs.
- The ideal: price traverses 3-6 levels per day and comes back, generating 3-6 RTs.

### Estimated RTs per day at recommended spacing

| Asset | Spacing | Expected RTs/day | Notes |
|-------|---------|-------------------|-------|
| ETH | 0.5% | 5-10 | Confirmed by live data (7.7 RT/day observed) |
| ETH | 0.8% | 3-6 | |
| BTC | 0.5% | 4-8 | |
| SOL | 1.0% | 4-8 | Higher vol compensates wider spacing |
| XRP | 1.2% | 3-6 | Unpredictable; may cluster |

---

## 3. Dynamic Grid Design

### 3.1 Volatility-adaptive spacing

Instead of fixed spacing, calculate the trailing ATR and adjust:

```
spacing = max(ATR_24h / num_levels, min_spacing)
```

**Implementation:**
- Calculate 24h ATR from the last 24 1-hour candles
- Set spacing = ATR_24h / (2 x num_levels)
- Clamp between 0.3% (floor, fee constraint) and 2.0% (ceiling)
- Recalculate every 4 hours
- When recalculating, only adjust unfilled levels (don't cancel filled orders)

**Example:**
- ETH ATR = 2%: spacing = 2% / 16 = 0.125% ... too tight. Use floor of 0.5%.
- ETH ATR = 5%: spacing = 5% / 16 = 0.31%. Still tight. Use 0.5%.
- ETH ATR = 8% (crash day): spacing = 8% / 16 = 0.5%. Keep 0.5%.

**Reality check:** For an 8-level grid, the formula rarely produces useful results because ATR / (2 x 8) is almost always below the fee floor. The better approach:

```
spacing = ATR_24h / desired_RTs_per_day
```

- Target 6 RTs/day: ATR 3% -> spacing = 0.5%. ATR 6% -> spacing = 1.0%.
- This actually works and naturally widens when volatile.

### 3.2 Time-of-day adjustment

Crypto volatility clusters:
- **High vol:** 13:00-21:00 UTC (US market overlap, 8h)
- **Medium vol:** 07:00-13:00 UTC (European session, 6h)
- **Low vol:** 21:00-07:00 UTC (Asian session, 10h)

**Practical approach:** Don't change spacing by time. Instead, **expect more RTs during US hours** and factor that into recentering decisions. Recentering during low-vol hours is safer (less likely to miss a move).

### 3.3 Trend filter

This is the most important dynamic adjustment. Grids die in trends.

**Simple trend detection:**
- Calculate 4h EMA and 24h EMA
- If 4h EMA > 24h EMA by more than 1 ATR: **strong uptrend**
- If 4h EMA < 24h EMA by more than 1 ATR: **strong downtrend**

**When trend detected:**
- Option A: **Pause the grid.** Stop placing new buy orders in a downtrend (or sell orders in an uptrend). Wait for mean reversion.
- Option B: **Shift the grid** in the direction of the trend. Bias toward more levels on the trending side.
- Option C: **Widen spacing** by 50% during strong trends to reduce the number of against-trend fills.

**Honest assessment:** Trend detection is hard. Most simple filters lag too much to be useful. The safest approach is Option A — stop adding positions when the grid is fully one-sided (all buys filled, no sells hit = downtrend).

**Practical rule:** If all buy levels are filled and price is below the grid, **do not add more levels below**. Wait.

---

## 4. Multi-Pair Grid

### Correlation analysis (approximate, varies by period)

| Pair | ETH | BTC | SOL | XRP |
|------|-----|-----|-----|-----|
| ETH | 1.00 | 0.85 | 0.80 | 0.60 |
| BTC | 0.85 | 1.00 | 0.75 | 0.55 |
| SOL | 0.80 | 0.75 | 1.00 | 0.55 |
| XRP | 0.60 | 0.55 | 0.55 | 1.00 |

**The problem:** Crypto pairs are highly correlated. When BTC dumps 10%, ETH drops 12%, SOL drops 15%, XRP drops 10%. Diversification benefit is limited.

**True diversification benefit (rough estimate):**
- Running 3 pairs vs 1: reduces variance by ~30-40% (not 67% as independent assets would)
- Correlation-adjusted portfolio vol reduction: sqrt(1/3 + 2/3 x avg_corr) = sqrt(1/3 + 2/3 x 0.65) = sqrt(0.77) = 0.88x
- So you reduce risk by about 12% by running 3 pairs instead of 1. Modest.

**Where multi-pair helps more:**
- **Different optimal spacings** = fills are desynchronized, smoothing daily RT count
- **Some pairs move when others are flat** (XRP can pump on its own news)
- **More total RTs per day** = more consistent daily income

### Recommended multi-pair configuration

| Pair | Spacing | Levels | Share of capital |
|------|---------|--------|-----------------|
| ETH | 0.5-0.8% | 6 | 45% |
| SOL | 0.8-1.2% | 5 | 30% |
| XRP | 1.0-1.5% | 4 | 25% |

**Why this split:**
- ETH has the most liquidity and tightest spreads on Kraken Futures
- SOL has higher vol = higher profit per RT but more risk
- XRP is the least correlated = best diversifier
- BTC excluded at small capital because the notional per level is too small to be meaningful

### Minimum capital for multi-pair

Each pair needs enough notional per level to generate non-trivial profit:
- Minimum useful notional per level: ~$5 (at 3x leverage, that's ~$1.67 margin per level)
- With 5 levels per pair, minimum per pair: ~$8-10
- **Minimum total capital for 3 pairs: ~$30**

At $10 capital: stick to 1 pair (ETH).
At $100 capital: can run 2-3 pairs comfortably.

---

## 5. Capital Allocation

### Kelly Criterion Analysis

Kelly formula: f* = (p x b - q) / b

Where:
- p = probability of winning a RT (historically ~85-95% for tight grids that get filled both ways)
- q = 1 - p
- b = win/loss ratio (for a symmetric grid, b = 1; but if price trends away, losses can be much larger)

**Problem with Kelly for grid trading:**
Kelly assumes binary outcomes. Grid trading doesn't have discrete "wins" and "losses" — it has:
- Small frequent profits (RT completed)
- Occasional large unrealized losses (grid fully on one side during a trend)
- Rare catastrophic losses (grid overrun + margin call)

**Kelly doesn't apply cleanly here.** The loss distribution is fat-tailed.

### Practical allocation approach

**Equal risk contribution (better than equal weight for grid trading):**

Each pair should contribute equal max drawdown potential:

| Pair | Max expected drawdown | Allocation to equalize risk |
|------|----------------------|----------------------------|
| ETH | 8% of notional | 38% |
| SOL | 12% of notional | 25% |
| XRP | 15% of notional | 20% |
| Reserve | — | 17% |

The **reserve** is critical: keep 15-20% of capital as unused margin to absorb drawdowns without liquidation.

### For $100 capital, recommended split:

| Allocation | Amount |
|-----------|--------|
| ETH grid | $40 |
| SOL grid | $25 |
| XRP grid | $20 |
| **Reserve margin** | **$15** |
| **Total** | **$100** |

---

## 6. Recentering Strategy

### The recentering problem

When price moves away from the grid center, levels on one side are all filled (unrealized loss) and levels on the other side are empty (no action). The grid becomes one-sided and stops generating RTs.

### Three approaches compared

#### A. Fixed % from center
- **Rule:** Recenter when price is > X% from grid center
- **X = ATR_daily** works reasonably
- For ETH at 3% ATR: recenter when price moves 3% from center
- **Pro:** Simple, predictable
- **Con:** May recenter too early in a trend (locking in losses) or too late in a range

#### B. ATR-based (recommended)
- **Rule:** Recenter when price exceeds center + 1.5 x ATR_24h
- Naturally adapts to volatility
- In calm markets (ATR 1.5%): recenter at 2.25% displacement
- In volatile markets (ATR 5%): recenter at 7.5% displacement
- **Pro:** Adapts to market conditions
- **Con:** More complex to implement

#### C. Time-based
- **Rule:** Recenter every N hours regardless
- **N = 4-8 hours** is common
- **Pro:** Simple, ensures the grid is always active
- **Con:** Unnecessary recentering in calm markets, recentering during trends locks in losses

### Recommended: ATR-based with a time backstop

```
if (abs(price - grid_center) > 1.5 * ATR_24h) OR (time_since_last_recenter > 12h AND RTs_in_last_12h < 2):
    recenter()
```

**Recentering mechanics:**
1. Cancel all open orders
2. Close any existing position (realize the loss/gain)
3. Set new center = current price
4. Place new grid levels around the new center
5. Log the recentering cost (realized PnL from closing the position)

**Important:** Recentering after a trend move means **realizing the accumulated unrealized loss**. This is the hidden cost of grid trading that most analyses ignore. The RTs give you small profits continuously, and the recentering gives you an occasional larger loss. The question is whether the sum of RT profits exceeds the sum of recentering losses over time.

---

## 7. Leverage Optimization

### Leverage tradeoffs

| Leverage | Profit multiplier | Liquidation distance | Character |
|----------|-------------------|---------------------|-----------|
| 2x | 2x | -50% | Very safe, low returns |
| 3x | 3x | -33% | Safe for crypto, current setting |
| 5x | 5x | -20% | Moderate risk |
| 10x | 10x | -10% | Dangerous for grid trading |
| 20x | 20x | -5% | Suicidal for grids |

### Liquidation math

With a grid, the **effective leverage** is what matters:
- If 4 of 8 levels are filled (typical): effective position = 4 x notional per level
- Effective leverage = (4 x notional) / capital

Example with $100 capital, 3x leverage, 8 levels:
- Notional per level = $100 x 3 / 8 = $37.50
- If 4 levels filled: effective notional = $150, effective leverage = 1.5x
- Liquidation would require a ~67% move from average entry. Very safe.

If ALL 8 levels filled (worst case in a trend):
- Effective notional = $300, effective leverage = 3x
- Liquidation at ~33% move from average entry. Still ok for crypto.

### Optimal leverage per pair

| Pair | Daily ATR | Max recommended leverage | Max grid drawdown before liquidation |
|------|----------|------------------------|--------------------------------------|
| ETH | 2-4% | **5x** | 20% move = about 5-7 daily ATRs |
| BTC | 1.5-3% | **5x** | 20% move = about 7-10 daily ATRs |
| SOL | 3-6% | **3x** | 33% move = about 6-8 daily ATRs |
| XRP | 2-5% | **3x** | 33% move = about 7-10 daily ATRs |

**Rule of thumb:** Max leverage = 100% / (5 x ATR_daily)
- ETH: 100 / (5 x 3) = 6.7x -> use 5x
- SOL: 100 / (5 x 4.5) = 4.4x -> use 3x
- XRP: 100 / (5 x 3.5) = 5.7x -> use 5x but XRP has tail risk -> use 3x

### Danger zone

At $8.82 capital with 3x leverage, **the current Martin Grid is already at 108% margin utilization** (documented in the previous analysis). This is fine when markets are calm but leaves zero room for error.

**Before increasing leverage: increase capital.** Leverage without margin reserve is how accounts blow up.

---

## 8. The Math: Expected Monthly Profit for $100

### Strategy: Multi-pair grid, $100 capital

**Configuration:**

| Param | ETH | SOL | XRP |
|-------|-----|-----|-----|
| Capital allocated | $40 | $25 | $20 |
| Reserve | — | — | $15 |
| Leverage | 5x | 3x | 3x |
| Notional total | $200 | $75 | $60 |
| Levels | 6 | 5 | 4 |
| Notional/level | $33.33 | $15.00 | $15.00 |
| Spacing | 0.6% | 1.0% | 1.2% |
| Expected RTs/day | 5 | 4 | 3 |

### Revenue per RT

| Pair | Notional/level | Spacing | Gross profit/RT | Fee (maker RT) | Net profit/RT |
|------|---------------|---------|-----------------|----------------|---------------|
| ETH | $33.33 | 0.6% | $0.200 | $0.013 | **$0.187** |
| SOL | $15.00 | 1.0% | $0.150 | $0.006 | **$0.144** |
| XRP | $15.00 | 1.2% | $0.180 | $0.006 | **$0.174** |

### Daily profit (good conditions = range-bound)

| Pair | Net/RT | RTs/day | Daily profit |
|------|--------|---------|-------------|
| ETH | $0.187 | 5 | $0.935 |
| SOL | $0.144 | 4 | $0.576 |
| XRP | $0.174 | 3 | $0.522 |
| **Total** | | | **$2.033** |

### Monthly projection (30 days)

| Scenario | Assumption | Monthly profit | Monthly ROI |
|----------|-----------|---------------|-------------|
| **Optimistic** | 25 good days, 5 flat days | **$50.83** | 50.8% |
| **Realistic** | 18 good days, 7 half-profit, 5 bad (recenter loss) | **$28-35** | 28-35% |
| **Conservative** | 15 good days, 8 half, 7 bad with 2 recenterings | **$15-22** | 15-22% |
| **Bear market** | Strong trend, frequent recentering, grid underperforms | **-$5 to +$5** | -5% to 5% |

### Breakdown of the "realistic" scenario

```
Revenue from RTs:
  18 good days x $2.03                    = $36.54
  7 half-profit days x $1.02              = $7.14
                                     Total = $43.68

Costs:
  Fees (already deducted above)           = $0 (already in net/RT)
  2 recentering events:
    Average recentering loss = 1 ATR x avg position
    = 3% x $150 avg notional x 0.5 (half filled) = $2.25 each
    2 x $2.25                              = -$4.50
  Funding rate (8h, ~0.01% when flat):
    30 days x 3 payments x 0.01% x $150 avg notional = -$1.35

Net monthly profit = $43.68 - $4.50 - $1.35 = ~$37.83
```

**Wait — I need to be more honest about recentering.**

A recentering after a 5% move with half the grid filled:
- Average entry displacement from current price: ~2.5% (half the move)
- On $150 notional: $3.75 loss realized
- This happens 2-4 times per month in typical crypto

More honest estimate with heavier recentering costs:
- 3 recenterings at $3.75 each = $11.25
- Net = $43.68 - $11.25 - $1.35 = **$31.08**

### Monthly profit estimate: $25-35 (realistic)

**ROI: 25-35% per month on $100 capital**

### Is this realistic?

Comparing to the live Martin Grid data:
- Current grid: $8.82 capital, 0.5% spacing, 3x leverage, ~$10/month = **113% ROI/month**
- But this is on only 2 days of data in a range-bound market
- Scaling to $100 with diversification and lower leverage per dollar = lower ROI % but higher absolute $
- 25-35% monthly ROI is a more sustainable estimate that accounts for bad weeks

### Compounding projection

| Month | Capital (start) | Profit (25% ROI) | Capital (end) |
|-------|----------------|-------------------|---------------|
| 1 | $100 | $25 | $125 |
| 2 | $125 | $31 | $156 |
| 3 | $156 | $39 | $195 |
| 6 | — | — | ~$381 |
| 12 | — | — | ~$1,455 |

At 25% monthly compounding: **$100 -> $1,455 in 12 months**. Sounds amazing. But...

---

## 9. The Honest Reality Check

### What can go wrong

1. **Flash crash (5-15% in minutes):** Grid gets fully filled on one side, recentering realizes a large loss. One bad crash can wipe 2-4 weeks of profits.

2. **Sustained trend:** ETH goes from $2100 to $1700 over 2 weeks. Grid keeps filling buys, price keeps falling. You're holding a large losing position with no sells being hit. This is the #1 killer of grid strategies.

3. **Low volatility period:** Price moves 0.5% per day for 2 weeks. Grid generates 0-1 RT per day. Funding fees eat into the thin profits.

4. **Exchange issues:** Kraken Futures API downtime, order placement failures, fill delays. The bot isn't trading = no profit, but positions are still open.

5. **Liquidation cascade:** Black swan event, 20%+ drop. If leverage is too high and margin reserve too low, account gets liquidated. Game over.

### What the backtests don't capture

- **Slippage on recentering:** Closing positions during high volatility is expensive
- **Funding rates:** Can be significantly negative during trends (shorts pay longs or vice versa)
- **API latency:** Orders may not fill at expected prices
- **Survivorship bias in strategy design:** We optimized parameters on past data; future may differ

### The uncomfortable comparison

| Strategy | Monthly return | Risk | Effort |
|----------|---------------|------|--------|
| Grid trading $100 | $25-35 (25-35%) | Account loss possible | High (monitoring, recentering) |
| Hold ETH $100 | Variable (-30% to +50%) | Volatile | Zero |
| DCA into ETH $100/month | Market return | Market risk | 5 minutes |
| Staking ETH | ~0.3%/month | Low | Low |

Grid trading beats all of these **in range-bound markets**. It loses to simple holding **in bull markets** and is equally bad **in bear markets** (but with more complexity).

---

## 10. Final Recommendations

### For $10 capital (current situation ~$8.82)
- **Single pair:** ETH only
- **Spacing:** 0.5% (current, working)
- **Leverage:** 3x (current, appropriate)
- **Action:** Don't change anything. Let it prove itself over 30 days.
- **Expected:** $8-12/month

### For $100 capital (next step)
- **Multi-pair:** ETH (45%) + SOL (30%) + XRP reserve for later
- **Actually start with ETH only at $85, reserve $15**
- **Spacing:** 0.6% for ETH
- **Leverage:** 5x for ETH (with $15 reserve as buffer)
- **Dynamic recentering:** ATR-based, check every 4h
- **Expected:** $25-35/month realistic

### For $1,000 capital (future)
- **Multi-pair:** ETH (40%) + SOL (25%) + XRP (15%) + reserve (20%)
- **Spacing:** Dynamic ATR-based
- **Leverage:** 3-5x depending on pair
- **Trend filter:** Pause grid when 4h EMA diverges > 1.5 ATR from 24h EMA
- **Expected:** $200-350/month realistic (20-35% monthly)
- **Note:** At this level, ROI % likely decreases because you'll be more conservative

### Priority of improvements (by impact)

1. **Trend detection + grid pause** — prevents the #1 killer (trading against a trend)
2. **ATR-based recentering** — reduces unnecessary recentering losses
3. **Multi-pair diversification** — smooths daily income
4. **Dynamic spacing** — marginal improvement, complex to implement
5. **Time-of-day adjustments** — minimal impact, don't bother

### The one thing that matters most

**Capital.** The strategy works. The fees are low. The spacing is reasonable. The ROI percentage is high. But $10/month doesn't pay for anything. The only lever that changes the game is putting more money in — and only money you can afford to lose entirely, because a 20% ETH crash with 5x leverage and a fully-loaded grid can take 50-60% of your capital in a day.

---

## Appendix: Quick Reference Formulas

```
Profit per RT = notional x (spacing - RT_fee)
RT_fee (maker) = 0.04% of notional
Min viable spacing = 5 x RT_fee = 0.20% (but 0.5% is practical minimum)

Optimal spacing = ATR_24h / target_RTs_per_day
Recenter trigger = price displacement > 1.5 x ATR_24h

Max leverage = 100% / (5 x ATR_daily)
Reserve margin = 15-20% of total capital

Kelly doesn't apply cleanly — use equal risk contribution instead
Diversification benefit in crypto ≈ 12% risk reduction for 3 pairs (high correlation)

Monthly profit estimate = daily_RTs x net_per_RT x 18-22 effective_days - recentering_costs - funding
```
