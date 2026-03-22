# Momentum/Breakout Strategy — Crypto on Kraken

**Date**: 2026-03-22
**Instrument**: PF_ETHUSD (Kraken Futures), potentially BTC, SOL
**Capital**: $15 (same constraint as other strategies)
**Philosophy**: The opposite of mean reversion — ride the trend when price escapes a range.

---

## 1. Core Thesis

Markets alternate between two regimes:
- **Compression** (range/consolidation): low volatility, price coils
- **Expansion** (breakout/trend): high volatility, price moves directionally

The strategy exploits the transition from compression to expansion. We wait for the squeeze, then ride the breakout.

**Why this works in crypto**: Crypto markets are driven by momentum traders, liquidation cascades, and FOMO. When price breaks a level, stop-losses and liquidations fuel the move. Unlike equities, crypto breakouts tend to be more violent and sustained (no market makers dampening moves at the same level).

**Why this fails in crypto**: Wicks. Crypto is notorious for fake breakouts — price spikes past a level, triggers stops, then reverses. This is the primary enemy.

---

## 2. Range Detection (The Squeeze)

Three independent filters. All three must confirm before we consider the market "in compression."

### 2.1 ATR Squeeze

```
ATR(14) = average of True Range over 14 candles
TR = max(high - low, |high - prev_close|, |low - prev_close|)

Squeeze condition: ATR(14) < ATR(50) * 0.7
```

When the short-term ATR drops below 70% of the long-term ATR, volatility is contracting. The spring is coiling.

**Implementation note**: Use percentage ATR (ATR / close * 100) to normalize across price levels.

### 2.2 Bollinger Band Width Squeeze

```
BB(20, 2.0) = standard Bollinger Bands
BB_width = (upper - lower) / middle * 100

Squeeze condition: BB_width < 2.5%  (for 5m candles)
                   BB_width < 3.0%  (for 15m candles)
                   BB_width < 4.0%  (for 1h candles)
```

Bollinger Band width is the single best measure of compression. When it drops to historically low levels, an expansion is coming. The bands don't tell you direction — just that a move is imminent.

### 2.3 Range Box

```
lookback = 20 candles
range_high = max(high[-20:])
range_low = min(low[-20:])
range_pct = (range_high - range_low) / range_low * 100

Squeeze condition: range_pct < threshold
  - 5m:  range_pct < 0.8%
  - 15m: range_pct < 1.2%
  - 1h:  range_pct < 2.0%
```

This is the simplest check: has price been stuck in a tight box?

### Combined Squeeze Score

```python
squeeze = (atr_squeeze and bb_squeeze and range_box)
# All three must be true to enter "watching for breakout" mode
# Once in squeeze mode, we define:
#   breakout_level_long  = range_high
#   breakout_level_short = range_low
```

---

## 3. Breakout Entry

### 3.1 LONG Entry

All conditions must be met on the **same candle**:

```
1. Squeeze was active on the previous candle (or within last 3 candles)
2. close > breakout_level_long  (price closes above the range high)
3. volume > avg_volume(20) * 2.0  (volume spike confirms conviction)
4. candle_body > 60% of candle_range  (strong close, not a wick)
```

Condition 4 is critical for crypto. A candle that closes near its high with a big body means buyers are in control. A candle with a long upper wick means sellers are rejecting the breakout.

### 3.2 SHORT Entry

Mirror of long:

```
1. Squeeze was active on the previous candle (or within last 3 candles)
2. close < breakout_level_short
3. volume > avg_volume(20) * 2.0
4. candle_body > 60% of candle_range  (strong close near low)
```

### 3.3 Volume Confirmation — Why It Matters

Breakouts without volume are fake breakouts. The volume spike confirms that real money is moving, not just a thin order book getting poked. On Kraken Futures, volume data is available in the candle API.

**Volume thresholds by timeframe**:
- 5m: volume > 2.0x avg (lots of noise, need strong confirmation)
- 15m: volume > 1.8x avg
- 1h: volume > 1.5x avg (hourly volume is more stable)

---

## 4. Position Sizing

### Risk 2% of Capital Per Trade

```
Capital = $15
Risk per trade = $15 * 0.02 = $0.30

Stop distance = ATR(14) * 1.5  (placed just inside the range)

Example with ETH at $2000, ATR(14) = $8 on 5m candles:
  Stop distance = $8 * 1.5 = $12
  Stop distance % = $12 / $2000 = 0.6%

Position size (notional) = risk / stop_distance_pct
  = $0.30 / 0.006 = $50

With 5x leverage: margin needed = $50 / 5 = $10
With 10x leverage: margin needed = $50 / 10 = $5

This is fine for $15 capital.
```

### Position Size Formula

```python
def position_size(capital, risk_pct, entry_price, stop_price, leverage):
    risk_amount = capital * risk_pct  # $0.30
    stop_distance = abs(entry_price - stop_price) / entry_price
    notional = risk_amount / stop_distance
    margin = notional / leverage

    # Safety: never use more than 40% of capital as margin
    max_margin = capital * 0.40
    if margin > max_margin:
        notional = max_margin * leverage
        # Actual risk will be lower than 2%

    return notional
```

---

## 5. Exit Strategy

### 5.1 Trailing Stop (Primary Exit)

```
trailing_distance = ATR(14) * 2.0

LONG:
  trail_stop = max(trail_stop, current_price - trailing_distance)
  if price <= trail_stop: EXIT

SHORT:
  trail_stop = min(trail_stop, current_price + trailing_distance)
  if price >= trail_stop: EXIT
```

**Why ATR * 2**: Gives the trend room to breathe. ATR * 1 gets stopped out on normal noise. ATR * 3 gives back too much profit. ATR * 2 is the classic compromise.

**Activation**: Trail starts immediately on entry. No "wait for X% profit" — the initial stop IS the trailing stop.

### 5.2 Take Profit (3:1 R/R)

```
risk = |entry - initial_stop|
take_profit = entry + (risk * 3)  (for LONG)
take_profit = entry - (risk * 3)  (for SHORT)
```

Whichever hits first — trailing stop or take profit — we exit.

**Note**: In a strong trend, the trailing stop will let you ride further than 3R. The take profit is a safety measure for when the move is fast and might reverse.

### 5.3 False Breakout Filter (Emergency Exit)

```
if price re-enters the squeeze range within 3 candles after entry:
    EXIT IMMEDIATELY (market order)
    mark this as "false breakout"
    cooldown = 5 candles before next entry in same direction
```

This is the most important risk management rule. A true breakout does not look back. If price re-enters the range, the breakout failed and holding is gambling.

**The math of fast exits**:
- False breakout loss: ~0.3-0.5% (price moved slightly past range, we entered, it came back)
- Holding a failed breakout loss: potentially 1-2% or more
- Cutting false breakouts fast saves the strategy

---

## 6. Timeframe Analysis

### 5-Minute Candles

**Pros**:
- More signals (more squeezes per day)
- Tighter stops = smaller risk per trade
- Catches micro-breakouts from consolidation patterns

**Cons**:
- Extremely high false breakout rate (60-70%)
- Fee impact is brutal (more trades, smaller moves)
- Wicks on 5m candles are proportionally larger
- Need to be very fast (latency matters)

**Verdict**: Marginal. Only works with very tight false breakout filter and low fees.

### 15-Minute Candles

**Pros**:
- Sweet spot for crypto: enough trades, less noise
- False breakout rate drops to ~50-55%
- Fee impact is manageable
- Breakouts tend to be more meaningful

**Cons**:
- Still noisy, still wicky
- 3-6 quality setups per day on ETH

**Verdict**: Best timeframe for this strategy on crypto. Recommended.

### 1-Hour Candles

**Pros**:
- Highest quality breakouts (when they happen, they move)
- Lowest false breakout rate (~40-45%)
- Fee impact is minimal
- Easier to manage psychologically

**Cons**:
- Few signals (maybe 1-2 per day, sometimes 0)
- Wider stops = need more capital per trade
- Miss the start of moves (by the time 1h candle closes, move is underway)

**Verdict**: Best win rate but too few signals for small capital. Good for larger accounts.

### Recommendation

**Primary**: 15m candles
**Confirmation**: Use 1h trend direction as a filter (only take LONG breakouts when 1h trend is up, and vice versa)

---

## 7. Fee Impact Analysis

### Kraken Futures Fee Structure

```
Taker fee: 0.05% per side (market orders)
Maker fee: 0.02% per side (limit orders)
```

Breakout trades are by nature **taker** — you need to get in NOW when the candle closes above/below the level. Limit orders don't work for breakouts (you'd be waiting at a level that may never come back).

### Fee Math Per Trade

```
Entry: market order = 0.05% taker
Exit (trailing stop): market order = 0.05% taker
Exit (take profit): could be limit = 0.02% maker

Round trip (worst case): 0.05% + 0.05% = 0.10%
Round trip (TP is limit): 0.05% + 0.02% = 0.07%
```

### Fee Impact on Profitability

```
Average trade on 15m with ETH:
  Winning trade moves ~1.5% (before trailing stop catches it)
  Losing trade moves ~0.5% (stop hit or false breakout exit)

Fee drag per winning trade: 0.10% / 1.5% = 6.7% of the profit
Fee drag per losing trade: 0.10% / 0.5% = 20% of the loss (makes it worse)

With 100 trades at 35% win rate:
  Gross P/L per trade (winning): +$50 * 1.5% = +$0.75
  Gross P/L per trade (losing):  -$50 * 0.5% = -$0.25
  Fee per trade: $50 * 0.10% = $0.05

  Net winning: $0.75 - $0.05 = $0.70
  Net losing:  -$0.25 - $0.05 = -$0.30

  Expected value per trade = (0.35 * $0.70) + (0.65 * -$0.30)
                            = $0.245 - $0.195
                            = +$0.05 per trade

  Monthly trades (15m, ~4 setups/day * 30 days): ~120 trades
  Monthly expected: 120 * $0.05 = +$6.00
  Monthly return: $6.00 / $15 = +40%
```

**This looks good on paper but is VERY sensitive to win rate.**

```
At 30% win rate:
  EV = (0.30 * $0.70) + (0.70 * -$0.30) = $0.21 - $0.21 = $0.00
  → Breakeven. Fees eat everything.

At 25% win rate:
  EV = (0.25 * $0.70) + (0.75 * -$0.30) = $0.175 - $0.225 = -$0.05
  → Losing money.
```

### Fee Optimization

1. **Use limit orders for TP**: Place TP as a limit order at 3R target. Saves 0.03% per winning trade.
2. **Avoid 5m timeframe**: Too many trades, fees compound.
3. **Don't trade during low volume**: Wider spreads = higher effective fees (slippage).

---

## 8. Best Pairs for Breakout Trading

### What Makes a Good Breakout Pair

1. **High volume**: Tight spreads, real breakouts (not just thin order book moves)
2. **Clear range behavior**: Alternates between compression and expansion
3. **Momentum tendency**: When it breaks, it keeps going (not mean-reverting)
4. **Available on Kraken Futures**: Must be tradeable

### Pair Rankings

| Pair | Volume | Range Clarity | Momentum | Overall |
|------|--------|---------------|----------|---------|
| ETH/USD | Very High | Good | Strong | **A-tier** |
| BTC/USD | Highest | Moderate | Strong | **A-tier** |
| SOL/USD | High | Very Good | Very Strong | **A-tier** |
| AVAX/USD | Medium | Good | Strong | B-tier |
| MATIC/USD | Medium | Moderate | Moderate | C-tier |
| DOGE/USD | High (spiky) | Poor | Pump-dump | C-tier |
| XRP/USD | High | Moderate | Moderate | B-tier |

### Recommended Focus

1. **SOL/USD**: Best breakout characteristics in current market. Clear consolidation patterns, strong follow-through when it breaks. Higher beta than ETH.
2. **ETH/USD**: Reliable, deep liquidity, we already have data and infrastructure for it.
3. **BTC/USD**: Widest stop distances (more capital needed per trade), but cleanest breakouts.

**Avoid**: Meme coins (DOGE, SHIB) — breakouts are random pumps, not technical. Low-cap alts — thin books, fake breakouts everywhere.

---

## 9. Expected Results — The Honest Math

### Realistic Assumptions (15m candles, ETH)

```
Win rate: 35% (realistic for breakout strategies with filters)
Average winner: 1.5% move * $50 notional = $0.75 gross
Average loser: 0.5% move * $50 notional = $0.25 gross
Fee per trade: $0.05 (round trip on $50 notional)
Slippage per trade: ~$0.01 (0.01% on $50)

Net winner: $0.75 - $0.05 - $0.01 = $0.69
Net loser: -$0.25 - $0.05 - $0.01 = -$0.31

Trades per day: 3-5 quality setups (not all taken — only those passing all filters)
Let's say 3 trades/day executed.
Trades per month: ~90

Monthly EV = 90 * [(0.35 * 0.69) + (0.65 * -0.31)]
           = 90 * [0.2415 - 0.2015]
           = 90 * 0.04
           = +$3.60

Monthly return: $3.60 / $15 = +24%
```

### Sensitivity Table

| Win Rate | Avg Win | Avg Loss | EV/Trade | Monthly (90 trades) | Monthly % |
|----------|---------|----------|----------|---------------------|-----------|
| 25% | $0.69 | -$0.31 | -$0.06 | -$5.40 | **-36%** |
| 30% | $0.69 | -$0.31 | -$0.01 | -$0.90 | **-6%** |
| 35% | $0.69 | -$0.31 | +$0.04 | +$3.60 | **+24%** |
| 40% | $0.69 | -$0.31 | +$0.09 | +$8.10 | **+54%** |
| 45% | $0.69 | -$0.31 | +$0.14 | +$12.60 | **+84%** |

### The Critical Insight

**The strategy lives or dies on the false breakout filter.**

- Without filter: win rate ~25-28%. Strategy loses money.
- With volume filter only: win rate ~30-33%. Marginal.
- With volume + body strength + 3-candle re-entry: win rate ~35-40%. Profitable.
- Adding 1h trend alignment: pushes to ~38-42%. Best case.

### Comparison to Existing Martingale Strategy

| Metric | Martingale/Trailing | Momentum/Breakout |
|--------|--------------------|--------------------|
| Win rate | ~50-55% | ~35% |
| Avg win | Small (0.5-1%) | Larger (1.5%) |
| Avg loss | Variable (martingale risk) | Fixed (0.5%) |
| Ruin risk | HIGH (martingale doubles) | LOW (fixed 2% risk) |
| Monthly return | Higher in good months | More consistent |
| Drawdown | Can wipe account | Max ~10-15% drawdown |
| Psychological | Stressful (watching losses double) | Many small losses, few big wins |

**Key advantage of breakout over martingale**: No ruin risk. The martingale can theoretically lose everything in a bad streak. The breakout strategy's worst month is -36% (all false breakouts), but it never goes to zero.

---

## 10. Implementation Plan

### Phase 1: Backtest (Python)

Build on existing `backtest_trailing.py` infrastructure:

```python
# Pseudocode structure
def detect_squeeze(candles, i):
    """Return True if market is in squeeze at candle i."""
    atr_14 = calc_atr(candles, i, 14)
    atr_50 = calc_atr(candles, i, 50)
    bb_width = calc_bb_width(candles, i, 20, 2.0)
    range_pct = calc_range(candles, i, 20)

    return (atr_14 < atr_50 * 0.7 and
            bb_width < 2.5 and
            range_pct < 0.8)

def check_breakout(candles, i, squeeze_range):
    """Return 'long', 'short', or None."""
    c = candles[i]
    vol_avg = avg_volume(candles, i, 20)
    body_ratio = abs(c.close - c.open) / (c.high - c.low + 1e-9)

    if (c.close > squeeze_range.high and
        c.volume > vol_avg * 2.0 and
        body_ratio > 0.6):
        return 'long'

    if (c.close < squeeze_range.low and
        c.volume > vol_avg * 2.0 and
        body_ratio > 0.6):
        return 'short'

    return None

def manage_position(position, candle, atr):
    """Trailing stop + TP + false breakout check."""
    # ... trailing stop logic
    # ... take profit at 3R
    # ... false breakout: price re-enters range within 3 candles
```

### Phase 2: Optimize

Test these parameter ranges:
- ATR squeeze threshold: 0.6 to 0.8 (step 0.05)
- BB width threshold: 1.5% to 3.5% (step 0.5)
- Volume multiplier: 1.5x to 3.0x (step 0.5)
- Trailing stop: ATR * 1.5 to ATR * 3.0 (step 0.5)
- TP ratio: 2R to 4R (step 0.5)
- Body ratio: 0.5 to 0.7 (step 0.1)

**Beware overfitting**: With this many parameters, you WILL find a combination that looks amazing on historical data. Use walk-forward validation: optimize on 60% of data, validate on 40%.

### Phase 3: Paper Trade

Run on Kraken Futures demo for 2 weeks minimum. Track:
- Actual win rate vs backtest
- Slippage on market orders
- Signal quality (are squeezes detected correctly?)
- Execution speed (does the 15m candle close give enough time to enter?)

### Phase 4: Live ($15)

Same $15 capital. Fixed 2% risk. No martingale. No doubling.

---

## 11. Risk Warnings

1. **30-40% win rate is psychologically brutal.** You will have 5-8 losing trades in a row regularly. This is normal. It does not mean the strategy is broken.

2. **Breakout strategies underperform in ranging markets.** If crypto enters a multi-week range (sideways chop), every breakout will be false. The strategy will bleed slowly. Consider a "regime switch" that turns off the bot during extended low-volatility periods.

3. **Correlation risk**: If running this alongside the martingale strategy, they may both be in a trade on the same asset. This doubles your exposure. Consider running them on different pairs.

4. **Slippage in fast markets**: The best breakouts happen in the fastest markets. That's also when slippage is highest. Budget 0.01-0.03% slippage per fill during volatile moves.

5. **Weekend/holiday gaps**: Crypto trades 24/7 but volume drops on weekends. Breakout quality decreases. Consider reducing position size or skipping weekends.

---

## 12. Summary

| Parameter | Value |
|-----------|-------|
| Strategy | Momentum breakout after squeeze |
| Timeframe | 15m (primary), 1h (trend filter) |
| Pair | ETH/USD (primary), SOL/USD (secondary) |
| Capital | $15 |
| Risk per trade | 2% ($0.30) |
| Leverage | 5x-10x (as needed for position sizing) |
| Entry | Close above/below range + volume spike + strong body |
| Stop | ATR(14) * 1.5 from entry (initial), then trail at ATR(14) * 2 |
| Take profit | 3R from entry |
| False breakout exit | Price re-enters range within 3 candles |
| Expected win rate | 35% (with all filters) |
| Expected monthly return | +24% ($3.60) |
| Maximum expected drawdown | -36% (worst month, recoverable) |
| Ruin risk | Essentially zero (fixed risk per trade) |

**Next step**: Build the backtest in `trading/backtest_breakout.py` using existing Kraken data infrastructure.
