# Mean Reversion Strategy for Crypto on Kraken

**Date**: 2026-03-22
**Status**: Research / Design phase
**Capital de reference**: 100 EUR

---

## 1. Core Thesis

Crypto prices on short timeframes (15m) oscillate around a moving average. The strategy exploits these oscillations by buying at statistical extremes (oversold) and selling at the mean, or shorting at overbought and covering at the mean.

This works best in **range-bound markets**. In strong trends, mean reversion gets destroyed. The strategy must therefore include a trend filter.

---

## 2. Indicators

### EMA 20 (Exponential Moving Average, 20 periods)
- On 15-minute candles: covers the last 5 hours of price action
- Serves as the "mean" — the middle Bollinger Band
- This is where we expect price to return

### EMA 50 (Exponential Moving Average, 50 periods)
- Covers the last ~12.5 hours
- Acts as **trend filter**: if price is above EMA50, the broader trend is up (favor longs); below, the trend is down (favor shorts)
- This is critical — mean reversion without a trend filter is suicide in crypto

### RSI(14) — Relative Strength Index
- Measures momentum on a 0-100 scale
- < 30 = oversold (potential long entry)
- > 70 = overbought (potential short entry)
- On 15m candles, RSI(14) covers ~3.5 hours of price action

### Bollinger Bands (20, 2)
- Middle band = SMA(20) — note: this is SMA, not EMA. Close to EMA20 but not identical
- Upper band = SMA(20) + 2 * StdDev(20)
- Lower band = SMA(20) - 2 * StdDev(20)
- Statistically, price stays within the bands ~95% of the time
- Touching the band = price is 2 standard deviations from the mean = statistical extreme

**Note on SMA vs EMA discrepancy**: The Bollinger middle band uses SMA(20), while our trend assessment uses EMA(20) and EMA(50). This is intentional — EMA reacts faster for trend following, while SMA is standard for Bollinger calculations. The difference is small on 15m candles.

---

## 3. Entry Signals

### LONG Entry (buy)
All three conditions must be true simultaneously:
1. **Price touches or crosses below the lower Bollinger Band** — price is at a statistical extreme
2. **RSI(14) < 30** — momentum confirms oversold
3. **Price > EMA50** — the broader trend is still up (we're buying a dip in an uptrend)

### SHORT Entry (sell/short)
All three conditions must be true simultaneously:
1. **Price touches or crosses above the upper Bollinger Band** — price is at a statistical extreme
2. **RSI(14) > 70** — momentum confirms overbought
3. **Price < EMA50** — the broader trend is still down (we're shorting a bounce in a downtrend)

### Signal Frequency (realistic estimate)
On 15m candles, requiring all three conditions simultaneously is **restrictive**. Expected signals per pair:
- In ranging markets: ~2-4 signals per week
- In trending markets: ~0-1 signals per week
- Average across all conditions: **~1-3 signals per week per pair**

This is good. More signals would mean lower quality.

---

## 4. Exit Signals

### Take Profit (TP)
- Price returns to the **middle Bollinger Band** (SMA20)
- This is the "mean" in mean reversion

### Stop Loss (SL)
- **1.5x the entry distance** beyond the band
- Example for LONG: if entry is at lower band and the band is 2% below SMA20, then SL is at 2% + (1.5 * 2%) = 5% below SMA20, or 3% below the lower band

**Concrete example**:
```
ETH price: 1800 EUR
SMA(20): 1850 EUR
Lower BB: 1800 EUR (distance = 50 EUR = 2.7%)
Entry: 1800 EUR
TP: 1850 EUR (profit = +50 EUR = +2.7%)
SL: 1800 - (1.5 * 50) = 1725 EUR (loss = -75 EUR = -4.2%)
```

Risk/Reward ratio: 50 / 75 = **0.67** (we risk more than we gain per trade)

This means we need a **win rate above 60%** to be profitable. More on this in section 9.

### Time Stop
- Close the position after **4 hours** (16 candles of 15 minutes) if neither TP nor SL is hit
- Rationale: if price hasn't reverted in 4 hours, the mean reversion thesis for this trade is broken
- Expected outcome of time-stopped trades: small loss or small gain (near breakeven)

---

## 5. Backtesting Pseudocode

```python
# Mean Reversion Backtest — Pseudocode

def backtest(candles_15m, pair):
    """
    candles_15m: list of {timestamp, open, high, low, close, volume}
    Returns: list of trades with P&L
    """

    # --- Compute indicators ---
    ema20  = EMA(close_prices, period=20)
    ema50  = EMA(close_prices, period=50)
    rsi14  = RSI(close_prices, period=14)
    sma20  = SMA(close_prices, period=20)
    stddev = STDDEV(close_prices, period=20)
    upper_bb = sma20 + 2 * stddev
    lower_bb = sma20 - 2 * stddev

    trades = []
    position = None  # None, 'long', or 'short'

    for i in range(50, len(candles)):  # start at 50 to have enough data
        c = candles[i]

        if position is None:
            # --- Check LONG entry ---
            if (c.close <= lower_bb[i] and
                rsi14[i] < 30 and
                c.close > ema50[i]):

                position = 'long'
                entry_price = c.close
                entry_time = c.timestamp
                entry_distance = sma20[i] - lower_bb[i]
                tp_price = sma20[i]
                sl_price = entry_price - (1.5 * entry_distance)

            # --- Check SHORT entry ---
            elif (c.close >= upper_bb[i] and
                  rsi14[i] > 70 and
                  c.close < ema50[i]):

                position = 'short'
                entry_price = c.close
                entry_time = c.timestamp
                entry_distance = upper_bb[i] - sma20[i]
                tp_price = sma20[i]
                sl_price = entry_price + (1.5 * entry_distance)

        else:
            # --- Check exits ---
            time_elapsed = c.timestamp - entry_time

            if position == 'long':
                if c.high >= tp_price:
                    exit_price = tp_price
                    result = 'TP'
                elif c.low <= sl_price:
                    exit_price = sl_price
                    result = 'SL'
                elif time_elapsed >= 4 * 3600:  # 4 hours in seconds
                    exit_price = c.close
                    result = 'TIME'
                else:
                    continue

            elif position == 'short':
                if c.low <= tp_price:
                    exit_price = tp_price
                    result = 'TP'
                elif c.high >= sl_price:
                    exit_price = sl_price
                    result = 'SL'
                elif time_elapsed >= 4 * 3600:
                    exit_price = c.close
                    result = 'TIME'
                else:
                    continue

            # --- Record trade ---
            if position == 'long':
                pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - exit_price) / entry_price * 100

            # Subtract fees (entry + exit)
            pnl_pct -= 2 * FEE_PCT  # see section 7

            trades.append({
                'pair': pair,
                'side': position,
                'entry': entry_price,
                'exit': exit_price,
                'pnl_pct': pnl_pct,
                'result': result,
                'duration_min': time_elapsed / 60
            })

            position = None

    return trades


def analyze(trades):
    wins = [t for t in trades if t['pnl_pct'] > 0]
    losses = [t for t in trades if t['pnl_pct'] <= 0]

    win_rate = len(wins) / len(trades) * 100
    avg_win = mean([t['pnl_pct'] for t in wins])
    avg_loss = mean([t['pnl_pct'] for t in losses])
    expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)

    print(f"Trades: {len(trades)}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Avg win: +{avg_win:.2f}%")
    print(f"Avg loss: {avg_loss:.2f}%")
    print(f"Expectancy per trade: {expectancy:.3f}%")
    print(f"TP/SL/TIME split: {count by result}")
```

### Implementation Notes
- Use Kraken OHLCV API: `GET https://api.kraken.com/0/public/OHLC?pair=XETHZEUR&interval=15`
- Kraken gives max 720 candles per call (~7.5 days on 15m). For longer backtests, paginate with `since` parameter
- For serious backtesting: download data to local CSV first, then run offline
- Consider using `ccxt` library for standardized exchange access

---

## 6. Fee Impact Analysis

### Kraken Fee Structure
- **Maker fee**: 0.02% (limit orders that add liquidity)
- **Taker fee**: 0.04% (market orders that remove liquidity)

For this strategy, we should use **limit orders** for entries (we know our entry price in advance from the Bollinger Band) and **limit orders** for TP. Only the SL would be a market/stop order (taker).

### Fee Math Per Trade

**Winning trade (TP hit — both sides maker):**
```
Fees = 2 * 0.02% = 0.04% round trip
Average TP profit (before fees) = ~2.0-3.0% (distance from BB to SMA20)
Net profit = 2.5% - 0.04% = 2.46%
Fee impact: 1.6% of gross profit eaten by fees
```

**Losing trade (SL hit — entry maker, exit taker):**
```
Fees = 0.02% + 0.04% = 0.06% round trip
Average SL loss (before fees) = ~3.75-4.5%
Net loss = 4.0% + 0.06% = 4.06%
Fee impact: 1.5% added to gross loss
```

### Verdict on Fees
Kraken's fees are **negligible** for this strategy. At 0.04% round trip, fees eat less than 2% of profit. This is a non-issue.

Compare with:
- Binance maker: 0.10% (5x more expensive)
- Coinbase Pro: 0.04-0.06%
- Kraken: 0.02% maker — one of the cheapest

**Kraken is actually a good choice for this strategy.** Fees are not the problem. The problem is win rate. See section 9.

---

## 7. Pair Ranking: Mean Reversion Suitability

Mean reversion works best on assets that:
- **Oscillate frequently** around the mean (high mean-reversion tendency)
- **Don't trend strongly** for extended periods
- **Have high liquidity** (tight spreads, fast execution)
- **Have moderate volatility** (enough to generate signals, not so much to blow through stops)

### Ranking (best to worst for mean reversion on 15m):

| Rank | Pair   | Oscillation | Trend Risk | Liquidity | Spread  | Verdict |
|------|--------|-------------|------------|-----------|---------|---------|
| 1    | **ETH** | High        | Medium     | Excellent | Tight   | Best candidate. Oscillates well, liquid enough. Not as momentum-driven as SOL. |
| 2    | **BTC** | Medium-High | Medium     | Excellent | Tightest| Very liquid but can have strong multi-day trends. Usable. |
| 3    | **XRP** | High        | High       | Good      | Medium  | Oscillates a lot but prone to sudden spikes (news-driven). Dangerous for SL. |
| 4    | **SOL** | Medium      | High       | Good      | Medium  | Too momentum-driven. When SOL trends, it trends HARD. Mean reversion gets crushed. |
| 5    | **ADA** | Medium      | Medium     | Lower     | Wider   | Lower liquidity on Kraken = wider spreads. Spread can eat into the small mean-reversion profits. Also tends to follow BTC closely with lag. |

### Recommendation
Start with **ETH/EUR** only. It has the best combination of oscillation + liquidity + reasonable spread on Kraken. Add BTC/EUR once validated.

Do NOT trade ADA or SOL with this strategy until backtested specifically. SOL's momentum character will likely produce a negative expectancy.

---

## 8. The Math — Honest Expected Results

### Assumptions (conservative, based on typical 15m crypto behavior)

```
Win rate (TP hit):           55%     (optimistic is 60%, pessimistic is 50%)
Loss rate (SL hit):          25%
Time stop rate:              20%     (breakeven-ish, slight loss on average)

Average TP profit:           +2.5%   (distance from BB to SMA20)
Average SL loss:             -4.0%   (1.5x entry distance)
Average time stop P&L:      -0.5%   (slightly negative, price drifted)
```

### Expectancy Per Trade

```
E = (0.55 * 2.5%) + (0.25 * -4.0%) + (0.20 * -0.5%)
E = 1.375% + (-1.0%) + (-0.1%)
E = +0.275% per trade (before fees)
E = +0.275% - 0.04% fees = +0.235% per trade (after fees)
```

### Monthly Projection on 100 EUR — ETH only

```
Signals per week (ETH):          ~2
Trades per month:                ~8
Capital per trade:               100 EUR (full capital, no leverage)

Expected monthly gain:
  = 8 trades * 0.235% * 100 EUR
  = 8 * 0.235 EUR
  = 1.88 EUR/month
  = +1.88% monthly return
```

### With 5 Pairs (ETH, BTC, XRP, SOL, ADA)

```
Signals per month (all pairs):   ~30-40
Let's say 30 usable trades

Expected monthly gain:
  = 30 * 0.235% * 100 EUR
  = 7.05 EUR/month
  = +7.05% monthly return
```

### Reality Check: What Can Go Wrong

The +0.235% expectancy assumes:
- **No execution slippage**: In practice, you won't always get filled at the exact BB price
- **No API latency**: 15m candles = you have time, but still
- **No regime change**: The 55% win rate assumes ranging markets. In a strong trend month, win rate can drop to 35-40%, making expectancy **negative**
- **No black swans**: A flash crash can blow through your SL before execution

**Adjusted realistic expectancy**: +0.10% to +0.20% per trade, accounting for slippage and imperfect execution.

```
Realistic monthly return (1 pair, 100 EUR):   +0.80 to +1.60 EUR
Realistic monthly return (5 pairs, 100 EUR):  +3.00 to +6.00 EUR
```

### Compounding Over 12 Months (single pair, conservative +1% monthly)

```
Month  0: 100.00 EUR
Month  3: 103.03 EUR
Month  6: 106.15 EUR
Month 12: 112.68 EUR
```

Annual return: **~12.7%** on 100 EUR = **12.68 EUR profit** over a year.

Not exciting. But with 1000 EUR:
```
Annual profit at 12.7%: ~127 EUR
Monthly: ~10.58 EUR
```

With 5000 EUR:
```
Annual profit at 12.7%: ~635 EUR
Monthly: ~52.92 EUR
```

---

## 9. The Honest Assessment

### What This Strategy IS
- A statistically-grounded approach to short-term crypto trading
- Low risk per trade (2.5-4% of capital at risk)
- Systematic and automatable
- Good for learning how to think about edge, expectancy, and risk

### What This Strategy IS NOT
- A money printer. +0.2% per trade is a thin edge.
- Safe. A bad month can wipe 3-4 good months.
- Passive income. Needs monitoring, parameter tuning, regime detection.

### The Hard Truth About Mean Reversion in Crypto

1. **Crypto trends more than it ranges.** Mean reversion strategies have their best months when the market is boring and sideways. In 2024-2025 bull runs, this strategy would have been net negative on many pairs.

2. **The 55% win rate is optimistic.** Academic studies on Bollinger Band strategies in equities show 50-55% win rates. Crypto is wilder. A realistic floor is 48-52%.

3. **At 50% win rate, the strategy is net negative:**
   ```
   E = (0.50 * 2.5%) + (0.30 * -4.0%) + (0.20 * -0.5%)
   E = 1.25% - 1.2% - 0.1% = -0.05% per trade
   ```
   **That's a losing strategy.** The margin between profitable and unprofitable is razor-thin.

4. **You need a regime filter.** The strategy should only activate during low-volatility, range-bound periods. Adding an ADX(14) < 25 filter (ADX measures trend strength) could improve win rate by filtering out trending periods. This is probably the single most impactful improvement.

### Suggested Improvements

| Improvement | Impact | Complexity |
|---|---|---|
| Add ADX(14) < 25 filter (no-trend filter) | High | Low |
| Use ATR-based position sizing instead of fixed % | Medium | Low |
| Add volume confirmation (volume spike at reversal) | Medium | Medium |
| Use multiple timeframe confirmation (1h + 15m) | High | Medium |
| Machine learning regime detection | High | High |
| Dynamic Bollinger width (widen bands in high-vol) | Medium | Medium |

---

## 10. Implementation Roadmap

### Phase 1: Backtest (Week 1-2)
- [ ] Download 3 months of 15m candle data for ETH/EUR from Kraken
- [ ] Implement the backtest in Python (use `pandas` + `ta-lib` or `pandas_ta`)
- [ ] Run backtest, measure win rate, expectancy, max drawdown
- [ ] If expectancy < +0.1%: stop. Adjust parameters or abandon.

### Phase 2: Paper Trading (Week 3-6)
- [ ] Implement live signal generation (connect to Kraken WebSocket)
- [ ] Paper trade for 1 month (log signals, simulate fills, track P&L)
- [ ] Compare paper results with backtest expectations
- [ ] If paper results are >30% worse than backtest: investigate overfitting

### Phase 3: Live Trading — Small (Week 7+)
- [ ] Start with 50 EUR (not 100) — half capital to limit initial risk
- [ ] Use Kraken API with limit orders only
- [ ] Set hard daily loss limit: -5% of capital = stop trading for 24h
- [ ] Run for 1 month, compare with paper trading results

### Phase 4: Scale or Kill
- [ ] If live results match paper trading (+/- 20%): consider scaling to full capital
- [ ] If live results are significantly worse: investigate execution issues or kill strategy
- [ ] Add second pair (BTC) only after 2 months of positive live results

---

## 11. Kraken API Notes

### Relevant Endpoints
```
# Get OHLC data (for backtesting and live signals)
GET https://api.kraken.com/0/public/OHLC?pair=XETHZEUR&interval=15

# Place limit order (for entries and TP)
POST https://api.kraken.com/0/private/AddOrder
  pair=XETHZEUR
  type=buy
  ordertype=limit
  price=1800
  volume=0.05

# Place stop-loss order
POST https://api.kraken.com/0/private/AddOrder
  pair=XETHZEUR
  type=sell
  ordertype=stop-loss
  price=1725
  volume=0.05
```

### WebSocket for Live Data
```
wss://ws.kraken.com/v2
Subscribe to: ohlc-15 channel for real-time candle updates
```

---

## 12. Bottom Line

**Is this strategy worth pursuing?**

Maybe. The theoretical edge exists but is thin (+0.2% per trade). With 100 EUR, the absolute returns are too small to matter (~1-2 EUR/month). The real value is:

1. **Learning**: Building and backtesting this teaches you how trading strategies work, how to measure edge, and how to think about risk.
2. **Infrastructure**: The bot you build for this can be adapted for other strategies.
3. **Validation**: If the backtest shows > +0.15% expectancy over 3 months of data, it's worth paper trading. If paper trading confirms, it's worth risking real money.

**What I would do**: Backtest first. If the numbers hold, paper trade. If paper trading confirms, start with 50 EUR. Never risk money on a strategy that only exists in theory.

The math doesn't lie, but the math is only as good as the assumptions. Validate every assumption with data.
