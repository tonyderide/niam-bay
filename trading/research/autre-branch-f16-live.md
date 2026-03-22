# F16 Live Strategy Analysis — ScalpingBotService.java

> **Source**: `C:/martin/backend/src/main/java/com/martin/scalping/ScalpingBotService.java`
> **Status**: LIVE on Kraken Futures with REAL money
> **Analyzed**: 2026-03-22
> **Lines of code**: ~1353

---

## 1. What is F16?

F16 is a **scalping strategy** running on Kraken Futures. Despite the file header still referencing "F13", the actual running code is **F16**, as confirmed by the bot startup log:

```
F16 (MACD+RSI+ADX+BB + Swing SL 3x1h + Compound Capital)
```

### Evolution trail visible in the code:
- **F13**: MACD+RSI + 2-Level Trailing + Martingale (original header comments)
- **F15**: Removed martingale, introduced compound capital (comment at line 984)
- **F16**: Added ADX trend filter + BB squeeze breakout filter + Swing stop on 1h candles

### Indicators used:
| Indicator | Parameters | Role |
|-----------|-----------|------|
| **MACD** | Fast=5, Slow=13, Signal=4 | Primary entry signal (histogram zero cross) |
| **RSI** | Period=14 | Entry filter (anti-overbought/oversold) |
| **ADX** | Period=14 | Trend filter (skip ranging markets) |
| **Bollinger Bands** | Period=20, StdDev=2.0 | Squeeze/breakout filter |
| **Swing Stop (1h)** | Lookback=3 candles | Stop-loss placement |
| EMA 9/21 | - | Display only (not used for signals) |
| ATR 14 | - | Display only (momentum score) |
| Stochastic 14,3,3 | - | Display only (not used for signals) |

### Timeframes:
- **Signal candles**: 5-minute OHLC (fetches 12 hours = 144 candles)
- **Stop-loss candles**: 1-hour OHLC (fetches last 3 candles for swing stop)
- **Tick interval**: Every 10 seconds (`@Scheduled(fixedDelay = 10000)`)

---

## 2. Entry Signals

### LONG entry (all conditions must be true):
1. **MACD histogram crosses above zero**: `prevMacdHist <= 0 && macdHist > 0`
2. **RSI < 55**: Not overbought (room to go up)
3. **ADX >= 20**: Market is trending (not ranging)
4. **BB not in squeeze**: `bbWidth >= 0.3%` (or just broke out of squeeze)
5. **Spread < 0.08%**: Liquidity check
6. **Trading hours**: 08:00-22:00 UTC (if enabled)
7. **Daily loss limit not hit**: Less than 10% of capital lost today
8. **Not in cooldown**: Post-trade cooldown expired

### SHORT entry (all conditions must be true):
1. **MACD histogram crosses below zero**: `prevMacdHist >= 0 && macdHist < 0`
2. **RSI > 45**: Not oversold (room to go down)
3. **ADX >= 20**: Market is trending
4. **BB not in squeeze**: Same as long
5. Same spread, hours, loss limit, cooldown checks

### Order type: **Market order** (taker)

### Key observation:
The RSI filter is very loose: 45-55 is a narrow exclusion band. This means:
- LONG is blocked only when RSI > 55 (quite generous)
- SHORT is blocked only when RSI < 45 (also generous)
- This allows entries in almost all conditions except strong overextension

---

## 3. Exit Signals

### There is NO fixed take-profit. The strategy relies entirely on trailing stops and swing stops.

### A. Swing Stop (primary stop-loss)
- On entry, fetches the **last 3 hourly candles**
- **LONG**: stop = lowest low of those 3 candles
- **SHORT**: stop = highest high of those 3 candles
- This is both the **software trailing stop starting point** AND a **Kraken server-side stop order**
- Checked every 10s tick: if price crosses the swing level, immediate market close

### B. 2-Level Trailing Stop
Two phases:

**Phase 1 — Wide (before activation)**:
- Trailing distance = 1.5% from entry (but actually starts at swing stop level, not 1.5%)
- Initial trailing stop = swing stop price (or 1.5% fallback if swing stop unavailable)
- Trail does NOT move until price reaches +0.3% profit

**Phase 2 — Tight (after activation)**:
- Once price is >= 0.3% above entry (LONG) or >= 0.3% below entry (SHORT)
- Trailing distance tightens to **1.0%** from current price
- Trail only moves in favorable direction (ratchets up for LONG, down for SHORT)
- `newStop = price * (1 - 0.01)` for LONG; `price * (1 + 0.01)` for SHORT

**Trail hit labeling**:
- If trailing was activated (price went +0.3%), exit = `TRAIL_TP` (profit)
- If trailing was never activated (price never reached +0.3%), exit = `TRAIL_SL` (loss)

### C. Safety Stop-Loss on Kraken Server
- A **server-side stop order** is placed on Kraken at entry
- Price = swing stop level (or 5% fallback if swing stop unavailable)
- Trigger signal = **mark price** (not last price — protects against wicks)
- This is a safety net: if the bot crashes/disconnects, Kraken will close the position
- Every tick, the bot checks if the position still exists on Kraken; if not, it records a `SAFETY_SL` trade

### D. No time-based exits
There is no maximum hold duration. Positions can be held indefinitely.

---

## 4. Position Sizing

### Compound capital model (F15/F16):
```
effectiveCapital = min(configuredCapital, availableMargin on Kraken)
notional = effectiveCapital * leverage * 0.90  // 90% to leave room for margin + fees
size = notional / currentPrice
```

### Key behaviors:
- **Capital updates dynamically**: Reads `availableMargin` from Kraken API each trade
- **Compound growth**: `effectiveCapital = capital + realizedPnl` (profits grow position size)
- **Floor**: If `effectiveCapital <= 0`, uses 10% of initial capital (survival mode)
- **90% utilization**: Only 90% of margin is used, leaving buffer for fees and margin requirements
- **Size multiplier is ALWAYS 1.0** (line 992): `state.setSizeMultiplier(1.0)`

### Rounding:
- ETH: 3 decimal places (e.g., 0.123 ETH)
- XBT: 4 decimal places
- Other: 4 decimal places

---

## 5. Martingale Behavior

### MARTINGALE IS DEAD. The code has legacy constants but they are NOT used.

**Legacy constants still in the file (UNUSED):**
```java
HEDGE_AFTER_LOSSES = 2    // never read
MARTINGALE_MULT = 2.0     // never applied
MAX_DOUBLINGS = 2          // never checked
```

**In `recordTrade()` (line 984-992):**
```java
// === F15: NO MARTINGALE -- Capital dynamique (compound growth) ===
state.setSizeMultiplier(1.0); // always 1x -- size grows naturally with capital + RPnL
```

The code explicitly sets `sizeMultiplier = 1.0` after every trade, regardless of win or loss. The martingale logic was removed in F15 and never brought back.

**Growth model instead**: Sizes grow organically because `effectiveCapital = capital + realizedPnl`. Winning makes positions bigger; losing makes them smaller. This is compound growth, not martingale.

---

## 6. Fee Handling

### Constants:
- `TAKER_FEE = 0.0005` (0.05% per side — Kraken Futures taker fee)
- Total round-trip fee = 0.10% (`TAKER_FEE + TAKER_FEE`)

### Fee calculation:
```java
fees = entryPrice * positionSize * totalFeeRate
netPnl = rawPnl - fees
```

### Important: fees are calculated on entry notional value only, not on both legs separately. This slightly underestimates fees when exit price differs significantly from entry. For scalping (small moves), this is negligible.

### All entries and exits are **market orders** (taker), no limit orders are used. This means every trade pays the full taker fee on both sides.

---

## 7. Risk Management

### Layer 1: Daily Loss Limit
- **Max daily loss = 10% of initial capital**
- Tracked per UTC day (resets at midnight UTC)
- When hit: **all trading stops for the rest of the day**
- Can be manually reset via `resetDailyLossLimit()`

### Layer 2: Cooldowns
- **After a win**: 20-second cooldown (`COOLDOWN_AFTER_TRADE_MS`)
- **After a loss**: 60-second cooldown (`COOLDOWN_AFTER_LOSS_MS`)
- **Entry timeout**: If entry order not filled in 60 seconds, cancel and 60s cooldown

### Layer 3: Trading Hours
- Active only **08:00-22:00 UTC** (configurable, can be disabled)
- Outside hours: no new entries (existing positions continue to be managed)

### Layer 4: Spread Filter
- Max spread = 0.08% (`MAX_SPREAD_PCT = 0.0008`)
- Skips entry if spread is too wide (low liquidity)

### Layer 5: ADX Trend Filter
- Requires ADX >= 20 to enter (ranging markets filtered out)

### Layer 6: BB Squeeze Filter
- Does not enter during BB squeeze (BB width < 0.3%)
- Can enter on squeeze breakout (was squeezed, now not)

### Layer 7: Safety Stop on Kraken Server
- Server-side stop order as crash protection
- Placed at swing stop level (or 5% from entry as fallback)
- Uses **mark price** trigger (not last price)

### Layer 8: Orphaned Position Detection
- On bot startup, checks if a position already exists on Kraken
- If found, resumes management (sets up trailing stop and safety SL)
- Cancels orphaned orders that don't belong to active positions

### What's MISSING:
- **No max position count** (can only have 1 position per instrument, but no global limit)
- **No max drawdown from peak** (only daily loss limit, no overall drawdown limit)
- **No correlation risk** (if running on multiple instruments, no combined risk check)
- **No volatility scaling** (ATR is computed but not used for sizing or stop placement)

---

## 8. ADX Trend Filter

### How it works:
```java
ADX_MIN_TREND = 20.0
if (currentAdx < ADX_MIN_TREND) {
    // Skip — "NO TREND, market is ranging"
    return;
}
```

### ADX calculation (Wilder's method):
1. Compute True Range, +DM, -DM for each bar
2. Smooth with Wilder's smoothing (period=14)
3. Compute +DI and -DI from smoothed values
4. DX = |+DI - -DI| / (+DI + -DI) * 100
5. ADX = smoothed average of DX values

### What ADX >= 20 means:
- ADX < 20: market is ranging/choppy — **skip trade**
- ADX 20-25: trend is emerging — trade allowed
- ADX > 25: strong trend — trade allowed
- ADX > 40: very strong trend — trade allowed

### Purpose: Prevents MACD whipsaws in sideways markets. MACD generates many false signals when price is range-bound; ADX filters those out.

### Limitation: ADX does NOT tell you the direction of the trend (that's what DI+/DI- do, but they are NOT used for entry decisions). The bot relies on MACD for direction.

---

## 9. BB Squeeze Breakout

### How it works:
```java
BB_SQUEEZE_THRESHOLD = 0.003  // 0.3%
bbWidth = (bbUpper - bbLower) / bbMiddle

isSqueezed = bbWidth < 0.003
squeezBreakout = wasSqueezed && !isSqueezed
```

### Three scenarios:
1. **In squeeze** (`bbWidth < 0.3%`): **Do not trade.** Wait.
2. **Normal** (`bbWidth >= 0.3%`, was not squeezed): **Trade normally** on MACD signal.
3. **Squeeze breakout** (was squeezed, now `bbWidth >= 0.3%`): **Trade** — noted in the reason string but no special handling (same entry logic).

### Purpose: BB squeeze = low volatility compression. The strategy avoids entering during low-volatility periods (when MACD signals are weak) and prefers entering when volatility is expanding (breakout).

### Notable: The squeeze breakout flag is recorded in the signal reason for logging but does NOT change position size or stop-loss placement. It's purely a gate filter, not a signal booster.

---

## 10. Swing Stop

### How it works:
```java
SWING_LOOKBACK_1H = 3  // last 3 hourly candles

// LONG: stop = lowest low of last 3h
// SHORT: stop = highest high of last 3h
```

### Fetching:
- Calls Kraken API for 1h OHLC candles (fetches ~4 hours of data, uses last 3)
- Parsed at entry time (when order is filled)
- Also fetched on bot restart (orphaned position resume)

### Usage:
1. **Initial trailing stop** = swing stop price (instead of arbitrary % from entry)
2. **Server-side safety SL** = placed at swing stop price on Kraken
3. **Software check every 10s**: if price crosses swing level, immediate market close

### Why this matters:
Traditional scalping bots use fixed % stops (e.g., 2% from entry). The swing stop adapts to market structure:
- In volatile markets, the 3h range is wide, giving more room
- In calm markets, the 3h range is tight, cutting losses faster
- It uses actual support/resistance levels (recent lows/highs) rather than arbitrary numbers

### Interaction with trailing:
- Trail starts at swing stop level
- Once price moves +0.3% in favor, trail tightens to 1.0% from current price
- Trail can only move in favorable direction
- The effective stop = **max(trailStop, swingStop)** for LONG / **min(trailStop, swingStop)** for SHORT
- So the swing stop acts as a floor — the trail can tighten above it but never widen below it

### Fallback:
If 1h candle data is unavailable, falls back to 1.5% wide trailing stop from entry + 5% hard safety SL on Kraken.

---

## 11. State Machine

```
FLAT ──[signal]──> ENTRY_PENDING ──[filled]──> IN_POSITION ──[exit]──> COOLDOWN ──[timer]──> FLAT
                         |                                                  ^
                         └──[timeout/cancel]──> COOLDOWN ──────────────────┘
```

Each state is handled every 10 seconds:
- **FLAT**: Check filters, compute indicators, look for MACD cross
- **ENTRY_PENDING**: Wait up to 60s for market order fill (should be instant for market orders)
- **IN_POSITION**: Monitor PnL, update trailing stop, check swing stop, check if Kraken closed it
- **COOLDOWN**: Wait 20s (win) or 60s (loss), then back to FLAT

---

## 12. Instrument Specificity — Can This Work on ADA/SOL/LINK?

### What's hardcoded for ETH:
The code itself is **instrument-agnostic** with minor rounding differences:
```java
// Rounding
if (instrument.contains("XBT")) return round(size, 4);    // BTC
if (instrument.contains("ETH")) return round(size, 3);    // ETH
return round(size, 4);                                      // everything else -> 4 decimals

// Tick rounding
if (instrument.contains("XBT")) return Math.round(price * 10.0) / 10.0;  // $0.10 tick
if (instrument.contains("ETH")) return round(price, 1);                    // $0.10 tick
return round(price, 2);                                                     // $0.01 tick
```

### Can it trade ADA/SOL/LINK?

**Technically yes.** The bot takes `instrument` as a parameter (e.g., `"PF_ADAUSD"`, `"PF_SOLUSD"`). You can call `startBot("PF_SOLUSD", capital, leverage, false)` and it will work.

**But there are practical concerns:**

| Factor | ETH | ADA/SOL/LINK |
|--------|-----|--------------|
| **Liquidity** | Excellent — tight spreads | Moderate — may fail spread filter more often |
| **MACD(5,13,4) tuning** | Optimized for ETH 5m volatility | Untested — ADA moves differently than ETH |
| **ADX threshold (20)** | Calibrated for ETH trend cycles | May be too low for ADA (ranging more), too high for SOL (trendy) |
| **BB squeeze (0.3%)** | Fits ETH volatility profile | ADA/SOL have different volatility — threshold needs retuning |
| **Swing stop (3x1h)** | 3h of ETH range is meaningful | ADA's 3h range might be too tight; SOL's might be too wide |
| **Spread filter (0.08%)** | ETH futures rarely exceed this | ADA/LINK futures may often exceed this, reducing trade frequency |
| **Taker fee (0.05%)** | Same across instruments | Same, but lower-volatility coins have smaller moves — fees eat more |
| **Rounding** | 3 decimals for size, $0.10 tick | Falls to default (4 decimals, $0.01 tick) — may need adjustment |

### Verdict:
The strategy architecture is portable but the **parameters are ETH-tuned**. Running it on ADA/SOL/LINK without parameter adjustment would likely:
- Trade less frequently (spread filter blocks more entries)
- Have worse win rate (MACD params not optimized for those volatility profiles)
- Have suboptimal stop placement (swing stop lookback and BB thresholds need calibration)

**Recommended approach**: Backtest F16 parameters on ADA/SOL/LINK 5m data before going live. Key parameters to re-optimize:
- MACD periods (5, 13, 4)
- RSI thresholds (55, 45)
- ADX minimum (20)
- BB squeeze threshold (0.003)
- Swing lookback (3 candles)
- Trail percentages (1.5%, 1.0%, 0.3%)
- Spread filter (0.08%)

---

## 13. Summary of Strengths and Weaknesses

### Strengths:
1. **No martingale** — compound growth instead of doubling down
2. **Multi-layer risk management** — daily limit, cooldowns, spread filter, ADX filter, BB filter
3. **Server-side safety stop** — survives bot crashes
4. **Swing-based stop loss** — adapts to market structure, not arbitrary %
5. **Orphaned position recovery** — handles restarts gracefully
6. **Mark price trigger** — safety SL not triggered by flash wicks on last price

### Weaknesses:
1. **Market orders only** — always pays taker fee both sides (0.10% round trip)
2. **No take profit** — relies entirely on trailing, which can give back profits in spiky reversals
3. **MACD is lagging** — even with fast params (5,13,4), histogram cross comes after the move starts
4. **No volatility-adjusted sizing** — ATR is computed but unused for position sizing
5. **No max drawdown kill switch** — only daily limit, no overall equity curve protection
6. **Entry is binary** — no scaling in/out, no partial positions
7. **10-second tick is slow for scalping** — a lot can happen in 10 seconds on ETH futures
8. **Trailing stop never tightens the Kraken server-side order** — only the initial swing stop is placed on Kraken; the software trailing is only checked every 10s. If the bot freezes for >10s, the server-side stop (at swing level) is the only protection, potentially giving back more profit than the software trail would have
9. **Available margin sync can shrink capital** — `calculatePositionSize` resets `state.capital` to current available margin, which can create unexpected behavior if margin is temporarily reduced by other positions

---

## 14. Flow Diagram

```
Every 10 seconds:
  |
  v
[Update prices from Kraken]
  |
  v
[Which phase?]
  |
  |-- FLAT:
  |     Check daily loss limit -> Check trading hours -> Check spread
  |     Fetch 5m candles -> Compute MACD, RSI, ADX, BB
  |     ADX < 20? -> Skip (ranging)
  |     BB squeeze? -> Skip (waiting for breakout)
  |     MACD histogram cross zero? + RSI filter? -> ENTRY (market order)
  |
  |-- ENTRY_PENDING:
  |     Wait for fill (max 60s) -> On fill: fetch 1h candles for swing stop
  |     Set trailing stop = swing stop level
  |     Place safety SL on Kraken at swing stop
  |     -> IN_POSITION
  |
  |-- IN_POSITION:
  |     Check if Kraken closed position (safety SL hit?)
  |     Check swing stop level
  |     Update trailing stop (1.5% -> 1.0% after +0.3% profit)
  |     If trail hit -> close market order -> record trade -> COOLDOWN
  |
  |-- COOLDOWN:
  |     Wait 20s (win) or 60s (loss) -> FLAT
```
