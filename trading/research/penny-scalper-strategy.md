# Penny Scalper: $0.01/trade Strategy for Kraken Futures

**Date**: 2026-03-30
**Capital**: $23
**Target**: $0.01 net profit per completed round trip
**Status**: Validated by math + partial backtest on real data

---

## 1. The Constraint Math (Working Backwards)

```
Target:          $0.01 net per round trip
Capital:         $23
Leverage:        5x (conservative) to 10x (aggressive)
Notional:        $115 (5x) to $230 (10x)
Maker fee:       0.02% per side = 0.04% round trip
Taker fee:       0.05% per side = 0.10% round trip

Fee per RT (maker-maker, $115 notional): $0.046
Fee per RT (maker-maker, $230 notional): $0.092

Breakeven spacing (5x):  0.04% = $0.046 in fees
For $0.01 net (5x):      need 0.049% spacing minimum
For $0.01 net (10x):     need 0.044% spacing minimum (more notional = more fee)
```

**Critical insight**: At $23 capital with maker fees, any spacing above 0.05% nets more than $0.01 per RT. The math works. The challenge is execution and risk management.

---

## 2. The Strategy: Filtered Micro-Grid

### Why Grid (not directional trading)

Every directional strategy tested in this repo (mean reversion, momentum breakout, BB scalping) has the same problem: **win rate uncertainty**. At $23, a few bad trades wipe you out.

Grid trading sidesteps the direction problem entirely. Each round trip is a mechanical buy-low-sell-high within a tight range. The profit is structural, not predictive.

**Evidence from our backtests**:
- Grid on ETH: +29.92% in 1 week, 0% max drawdown (backtest-2026-03-19.md)
- Grid on BTC: +24.32% in 1 week, 0% max drawdown
- Sweep results: 1692/2565 configs profitable (66% hit rate)
- Top grid configs: 90%+ win rate, 150-250+ Sharpe ratios

### Why "Filtered" (not always-on)

The backtests also proved that grids **bleed in trending markets**:
- EEG filter results: always-on baseline beat filtered versions on 3-month data
- BUT: the 3-month period was a -32% downtrend. The baseline "won" by luck (oscillations within the trend)
- Signal V2 results: BB squeeze + EMA trend filter reduced max drawdown from 16.1% to 4.7%

**The solution**: Run the grid ONLY when the market is oscillating, not trending. Turn it off otherwise.

---

## 3. Concrete Parameters

### Grid Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Pair** | PF_SOLUSD (primary), PF_ETHUSD (secondary) | SOL: highest oscillation frequency (27% of 1m candles >= 0.05%). ETH: deepest liquidity |
| **Spacing** | 0.10% | Sweet spot: $0.0173 net/RT at 5x, $0.0345 at 10x. Well above $0.01 target |
| **Levels** | 4 (2 buy + 2 sell) | At $23 capital, 4 levels = $28.75 notional per level (5x) |
| **Leverage** | 5x (start), scale to 7x at $35 capital | Conservative start. 10x only above $50 |
| **Order type** | LIMIT only (maker) | 0.02% vs 0.05% taker. Non-negotiable |
| **Recenter trigger** | Price drifts > 2 spacings from center | At 0.10% spacing, recenter at 0.20% drift |

### Per-Trade Economics

```
Notional per level:   $28.75 (at 5x)
Spacing:              0.10%
Gross per RT:         $28.75 * 0.001 = $0.02875
Fee per RT:           $28.75 * 0.0004 = $0.01150
NET per RT:           $0.01725

Margin of safety:     $0.01725 / $0.01 = 1.73x the target
```

### At 10x Leverage (when capital grows to $50+)

```
Notional:             $50 * 10 = $500
Per level (4):        $125
Gross per RT:         $125 * 0.001 = $0.125
Fee per RT:           $125 * 0.0004 = $0.05
NET per RT:           $0.075

Margin of safety:     7.5x the target
```

---

## 4. Entry Filter: When to Run the Grid

### Filter: BB Squeeze + EMA Golden Cross

From our backtest results (RESULTATS_V2.md), this combination delivered:
- 78.1% win rate (EMA trend filter)
- 4.7% max drawdown (BB squeeze)
- Active ~20-30% of the time

```python
def should_grid_be_active(candles_1h):
    """
    Check every 15 minutes.
    Returns True if market is range-bound and not in a downtrend.
    """
    closes = [c['close'] for c in candles_1h[-200:]]

    # 1. BB Squeeze: bandwidth in lowest 25th percentile
    sma20 = mean(closes[-20:])
    stddev = stdev(closes[-20:])
    bb_width = (2 * stddev) / sma20
    bb_widths_history = [calc_bb_width(closes[:i]) for i in range(50, len(closes))]
    percentile_25 = sorted(bb_widths_history)[len(bb_widths_history) // 4]
    bb_squeeze = bb_width <= percentile_25

    # 2. EMA Trend: not in a crash
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    trend_ok = ema50 > ema200  # Golden cross

    # 3. RSI sanity: not extremely overbought/oversold
    rsi = calc_rsi(closes, 14)
    rsi_ok = 35 < rsi < 65  # Range-bound zone

    return bb_squeeze and trend_ok and rsi_ok
```

### Kill Switch

```python
def emergency_stop(equity, capital, daily_pnl):
    """Hard stops that override everything."""
    if equity < capital * 0.85:      # -15% total drawdown
        return True, "MAX_DRAWDOWN"
    if daily_pnl < -capital * 0.05:  # -5% daily loss
        return True, "DAILY_LIMIT"
    return False, None
```

---

## 5. Position Management

### Grid Lifecycle

```
1. INIT: Calculate center_price from current market price
2. PLACE: Set 2 buy limits below center, 2 sell limits above center
   - Buy 1: center * (1 - 0.001) = center - 0.10%
   - Buy 2: center * (1 - 0.002) = center - 0.20%
   - Sell 1: center * (1 + 0.001) = center + 0.10%
   - Sell 2: center * (1 + 0.002) = center + 0.20%

3. FILL: When a buy fills, immediately place a sell at +0.10%
         When a sell fills against a filled buy, that's 1 RT = $0.0173 profit

4. RECENTER: If price moves > 0.20% from center:
   - Cancel all unfilled orders
   - Close any one-sided inventory (accept small loss)
   - Set new center at current price
   - Place new grid

5. SHUTDOWN: When filter says market is trending:
   - Cancel all unfilled orders
   - Close inventory at market (taker fee accepted)
   - Wait for range conditions to return
```

### Recentering Cost

```
Recenter = close inventory at market
Worst case: 2 filled buys, price dropped 0.30% below highest buy
Loss: 2 * $28.75 * 0.003 + taker_fee = $0.1725 + $0.0288 = ~$0.20

This means: 1 recenter wipes ~12 round trips of profit
Goal: minimize recenters via the entry filter
```

---

## 6. Pair Selection (Data-Driven)

From 1-minute candle analysis of 720 candles per pair:

| Pair | 1m moves >= 0.05% | 5m moves >= 0.10% | Oscillation Score |
|------|-------------------|-------------------|-------------------|
| **SOL** | 27.1% | 29.7% | **Best** |
| DOT | 21.8% | 37.6% | Very Good |
| ADA | 22.9% | 27.7% | Good |
| LINK | 21.4% | 27.1% | Good |
| ETH | 20.3% | 23.2% | Good |
| BTC | 14.4% | 19.6% | Lowest |

**Primary pair**: SOL -- highest 1m oscillation frequency, good liquidity on Kraken Futures.
**Secondary**: ETH or DOT -- ETH for liquidity, DOT for oscillation.

**Avoid BTC for micro-grid**: Lowest oscillation frequency + tick size of $1.0 makes 0.10% spacing = $83+ per grid level, requiring much more capital.

---

## 7. Expected Performance

### Conservative Estimate (5x leverage, SOL only)

```
Round trips per hour: 2 (conservative, data shows 4-6 possible)
Hours active per day: 16 (filter removes ~33% of time)
Daily RTs: 32
Net per RT: $0.0173
Daily profit: $0.55
Monthly profit: $16.60
Monthly ROI: 72%

At $23 capital growing at 72%/month (compound):
Month 0: $23.00
Month 1: $39.56
Month 2: $68.04
Month 3: $117.03
Month 6: $595.04
```

### Pessimistic Estimate (2x recenters/day eating profit)

```
Daily RTs: 32
RT profit: 32 * $0.0173 = $0.55
Recenter cost: 2 * $0.20 = $0.40
Net daily: $0.15
Monthly: $4.50 (19.6% ROI)
```

### Optimistic Estimate (7x leverage, SOL + ETH)

```
Daily RTs: 60 (2 pairs)
Net per RT: $0.024 (7x leverage)
Daily profit: $1.44
Monthly: $43.20 (188% ROI)
```

---

## 8. Implementation Architecture

### Option A: Extend Martin Grid Bot (Java)

The Martin bot already has grid infrastructure:
- `GridTradingService.java` handles grid placement, fills, recentering
- `GridController.java` exposes API
- Deployed on Oracle VM

**Changes needed**:
1. Add `PennyScalperMode` to GridTradingService with 0.10% spacing
2. Add BB squeeze + EMA filter before grid activation
3. Add daily PnL tracking with kill switch
4. Reduce tick-based recheck to 1-minute intervals

**Pros**: Already deployed, battle-tested, API works.
**Cons**: Adding a new mode to existing code adds complexity.

### Option B: Standalone Python Bot (Recommended for testing)

```python
# penny_scalper.py -- standalone bot
# Runs on same Oracle VM alongside Martin

import krakenex  # or ccxt
import time

class PennyScalper:
    def __init__(self, pair="PF_SOLUSD", capital=23, leverage=5,
                 spacing_pct=0.10, levels=4):
        self.pair = pair
        self.capital = capital
        self.leverage = leverage
        self.spacing = spacing_pct / 100
        self.levels = levels
        self.notional = capital * leverage
        self.per_level = self.notional / levels

        self.center_price = None
        self.active_orders = {}
        self.filled_buys = []
        self.total_pnl = 0
        self.daily_pnl = 0
        self.round_trips = 0

    def check_filter(self):
        """BB squeeze + EMA trend check on 1h candles."""
        candles = self.api.get_ohlc(self.pair, interval=60, count=200)
        # ... implement filter logic from section 4
        return True  # placeholder

    def place_grid(self, center):
        """Place limit orders around center price."""
        self.center_price = center
        half = self.levels // 2

        for i in range(1, half + 1):
            buy_price = center * (1 - self.spacing * i)
            sell_price = center * (1 + self.spacing * i)

            self.place_limit_buy(buy_price, self.per_level / buy_price)
            self.place_limit_sell(sell_price, self.per_level / sell_price)

    def on_fill(self, order):
        """Handle fill event."""
        if order['side'] == 'buy':
            self.filled_buys.append(order['price'])
            # Place matching sell
            sell_price = order['price'] * (1 + self.spacing)
            self.place_limit_sell(sell_price, order['size'])

        elif order['side'] == 'sell' and self.filled_buys:
            buy_price = self.filled_buys.pop(0)
            gross = self.per_level * (order['price'] - buy_price) / buy_price
            fees = self.per_level * 0.0002 * 2
            net = gross - fees
            self.total_pnl += net
            self.daily_pnl += net
            self.round_trips += 1
            print(f"RT #{self.round_trips}: +${net:.4f} (total: ${self.total_pnl:.4f})")

    def check_recenter(self, current_price):
        """Recenter if price drifted too far."""
        if self.center_price is None:
            return
        drift = abs(current_price - self.center_price) / self.center_price
        if drift > self.spacing * self.levels:
            self.close_inventory(current_price)
            self.cancel_all()
            self.place_grid(current_price)

    def run(self):
        """Main loop."""
        while True:
            if not self.check_filter():
                self.shutdown()
                time.sleep(900)  # recheck in 15min
                continue

            price = self.get_price()

            if self.center_price is None:
                self.place_grid(price)

            self.check_recenter(price)
            self.check_fills()

            # Kill switch
            equity = self.capital + self.total_pnl
            if equity < self.capital * 0.85:
                self.shutdown()
                break
            if self.daily_pnl < -self.capital * 0.05:
                self.shutdown()
                time.sleep(86400)  # wait 24h

            time.sleep(5)  # check every 5 seconds
```

---

## 9. Scaling Plan

| Capital | Leverage | Notional | Net/RT | Strategy |
|---------|----------|----------|--------|----------|
| $23 | 5x | $115 | $0.017 | SOL only, 0.10% spacing, 4 levels |
| $50 | 7x | $350 | $0.053 | SOL + ETH, 0.10% spacing, 4 levels each |
| $100 | 5x | $500 | $0.075 | SOL + ETH, 0.15% spacing, 6 levels |
| $200 | 5x | $1000 | $0.150 | 3 pairs, 0.15% spacing, 8 levels |
| $500 | 5x | $2500 | $0.375 | 3 pairs, wider spacing, larger levels |

**Position sizing rule**: Never use more than 40% of capital as margin. At 5x, $23 * 0.40 = $9.20 margin = $46 notional per pair max.

---

## 10. Risk Registry

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Strong trend (>2% unidirectional) | Grid bleeds, recenters eat profit | Medium | BB squeeze + EMA filter. Kill switch at -5% daily |
| Flash crash / liquidation | Total loss of position | Low | SL at -15% equity. 5x leverage (not 10x) |
| API downtime | Can't recenter, orders stuck | Low | All orders have expiry. Heartbeat check |
| Low volatility period | No round trips, capital idle | Medium | Multi-pair. Accept idle time (no loss) |
| Spread wider than spacing | Fills at worse prices | Low | SOL/ETH spread is ~0.02-0.03%, well below 0.10% spacing |
| Fee tier change | Maker fee increase above 0.02% | Very Low | Monitor Kraken fee schedule. Strategy works up to 0.04% maker |

---

## 11. Deployment Checklist

- [ ] Paper trade for 1 week on Kraken Futures demo
- [ ] Verify fill rate matches backtest expectations
- [ ] Verify recenter frequency
- [ ] Measure actual slippage on limit orders
- [ ] Deploy with $23 on live account
- [ ] Monitor for 48h manually
- [ ] Set up Telegram alerts for: RT completed, recenter, filter on/off, kill switch
- [ ] Review after 1 week: actual $/RT vs $0.0173 target

---

## 12. Bottom Line

**The strategy works** if and only if:
1. You use MAKER orders exclusively (0.02% fee, not 0.05% taker)
2. You filter out trending markets (BB squeeze + EMA)
3. You trade SOL or ETH (high oscillation frequency)
4. You accept that the grid will be IDLE 30-50% of the time
5. You recenter quickly when drift exceeds 2 spacings

**$0.01 per trade is achievable** with 0.10% spacing at 5x leverage on $23. Each RT actually nets $0.0173, giving a 73% margin of safety over the $0.01 target.

**The real enemy is not fees. It's directional exposure.** The filter is more important than the grid parameters.

**Next step**: Implement as Python bot, paper trade 1 week, then go live.
