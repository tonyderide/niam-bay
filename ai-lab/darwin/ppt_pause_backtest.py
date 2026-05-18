"""
PPT-Pause Backtest — Tier 2 Per-Pair Trend Pause
Cycle 57 — 2026-05-18

Compare 3 strategies on Binance 1min OHLC:
  A) NEUTRAL grid no pause (baseline = Option B)
  B) NEUTRAL grid + PPT-Pause (closeOnly on 3 consecutive 15min ticks of strong downtrend)
  C) DCA passive (buy-and-hold same notional)

Grid params reproduce Option B Martin config:
  - 4 levels, 1.5% spacing
  - leverage 7x, capital $25 per grid
  - maxLoss 10% (=$2.50) = HARD STOP
  - NEUTRAL gridMode: buys below center, sells above

PPT-Pause params from design cycle 56:
  - 15min tick
  - 3 consecutive ticks where:
      price < EMA200(1H) by > 1.5%  AND  RSI(1H,14) < 40
  - On trigger: setCloseOnly = no more buys, existing sells still fire
  - Reprise: 3 consecutive ticks UPTREND (price >= EMA200) + cooldown 1h
"""

import json
import math
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

DATA_DIR = Path(__file__).parent / "data_cache"

# ---------- Indicators ----------

def ema(values: List[float], period: int) -> List[float]:
    """EMA exponential moving average. Returns same length, first period-1 are seed-based."""
    if not values:
        return []
    out = [values[0]]
    k = 2.0 / (period + 1)
    for v in values[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out

def rsi(values: List[float], period: int = 14) -> List[float]:
    """Standard RSI. Returns same length, first `period` entries = 50 (neutral seed)."""
    if len(values) < period + 1:
        return [50.0] * len(values)
    out = [50.0] * period
    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period, len(values)):
        if i > period:
            delta = values[i] - values[i - 1]
            gain = max(delta, 0)
            loss = max(-delta, 0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            out.append(100.0)
        else:
            rs = avg_gain / avg_loss
            out.append(100.0 - (100.0 / (1.0 + rs)))
    # pad first period
    if len(out) < len(values):
        out = [50.0] * (len(values) - len(out)) + out
    return out[: len(values)]

def resample_1min_to_1h(candles_1m: List[List]) -> List[List]:
    """Aggregate 1min candles to 1h. Each output candle: [ts_floor_h, O, H, L, C, V]."""
    if not candles_1m:
        return []
    HOUR_MS = 3600 * 1000
    out = []
    bucket_ts = (candles_1m[0][0] // HOUR_MS) * HOUR_MS
    o = candles_1m[0][1]
    h = candles_1m[0][2]
    l = candles_1m[0][3]
    c = candles_1m[0][4]
    v = candles_1m[0][5]
    for cd in candles_1m[1:]:
        ts = (cd[0] // HOUR_MS) * HOUR_MS
        if ts != bucket_ts:
            out.append([bucket_ts, o, h, l, c, v])
            bucket_ts = ts
            o = cd[1]
            h = cd[2]
            l = cd[3]
            c = cd[4]
            v = cd[5]
        else:
            h = max(h, cd[2])
            l = min(l, cd[3])
            c = cd[4]
            v += cd[5]
    out.append([bucket_ts, o, h, l, c, v])
    return out


# ---------- Grid simulator ----------

class GridState:
    """NEUTRAL grid with 4 levels, 1.5% spacing.

    Convention:
      - center = deploy price
      - levels = [-2, -1, +1, +2] * spacing from center
      - level -1 and -2 = buy levels (when price drops, fill buy)
      - level +1 and +2 = sell levels (when price rises, fill sell)
      - Each level holds `unit_size` units of base currency

    State tracking:
      - filled[level] = True if filled at price levels[level]
      - position_units = net long position from filled buys minus sells
      - cash = USD cash (margin) — starts at capital
    """

    def __init__(self, center_price: float, capital_usd: float, leverage: int,
                 levels_count: int = 4, spacing_pct: float = 0.015,
                 fees_pct: float = 0.0005, max_loss_pct: float = 0.10):
        self.center = center_price
        self.capital = capital_usd
        self.leverage = leverage
        self.notional = capital_usd * leverage
        self.fees_pct = fees_pct
        self.max_loss_pct = max_loss_pct

        # generate levels: equal buy/sell around center
        buys = levels_count // 2
        sells = levels_count - buys
        self.levels = []
        for i in range(buys, 0, -1):
            self.levels.append({
                "side": "buy",
                "price": center_price * (1 - spacing_pct * i),
                "filled": False,
                "level_idx": -i,
            })
        for i in range(1, sells + 1):
            self.levels.append({
                "side": "sell",
                "price": center_price * (1 + spacing_pct * i),
                "filled": False,
                "level_idx": i,
            })

        # unit size: notional / center / levels_count for symmetric exposure
        self.unit_size = self.notional / center_price / levels_count

        self.position_units = 0.0
        self.avg_entry = 0.0
        self.realized_pnl = 0.0
        self.fills = 0
        self.close_only = False
        self.stopped = False
        self.stop_reason = None

    def _record_fill(self, level: Dict, price: float):
        # signed fill quantity: buy = +unit_size, sell = -unit_size
        fill_side = 1 if level["side"] == "buy" else -1
        fill_qty = self.unit_size * fill_side

        if self.position_units == 0:
            # opening from flat
            self.avg_entry = price
            self.position_units = fill_qty
        elif (self.position_units > 0) == (fill_side > 0):
            # same direction → weighted average entry
            new_total = self.position_units + fill_qty
            self.avg_entry = (
                self.avg_entry * abs(self.position_units) + price * self.unit_size
            ) / abs(new_total)
            self.position_units = new_total
        else:
            # opposite direction → realize PnL on closed portion
            # for closing long (pos>0, sell): pnl = (price - avg) * qty
            # for closing short (pos<0, buy): pnl = (avg - price) * qty
            close_qty = min(self.unit_size, abs(self.position_units))
            if self.position_units > 0:
                pnl = (price - self.avg_entry) * close_qty
            else:
                pnl = (self.avg_entry - price) * close_qty
            self.realized_pnl += pnl
            # reduce position toward zero by close_qty in current direction
            sign = 1 if self.position_units > 0 else -1
            self.position_units -= sign * close_qty
            # leftover from fill flips direction (only if unit_size > current position)
            leftover = self.unit_size - close_qty
            if leftover > 1e-12:
                self.avg_entry = price
                self.position_units = fill_side * leftover

        self.realized_pnl -= price * self.unit_size * self.fees_pct
        self.fills += 1
        level["filled"] = True

    def tick(self, low: float, high: float, close: float) -> Optional[str]:
        """Process price range over a minute. Returns 'STOP' if hard stop fired."""
        if self.stopped:
            return None
        for lvl in self.levels:
            if lvl["filled"]:
                continue
            if lvl["side"] == "buy":
                if self.close_only:
                    continue
                if low <= lvl["price"]:
                    self._record_fill(lvl, lvl["price"])
            else:  # sell
                if high >= lvl["price"]:
                    self._record_fill(lvl, lvl["price"])
        # hard stop check: unrealized + realized vs maxLoss
        # works for longs (units>0) and shorts (units<0) — formula identical
        upnl = (close - self.avg_entry) * self.position_units if self.position_units != 0 else 0.0
        total = self.realized_pnl + upnl
        if total <= -self.capital * self.max_loss_pct:
            # market close at `close` price — close both long and short legs
            if self.position_units != 0:
                close_pnl = (close - self.avg_entry) * self.position_units
                close_pnl -= close * abs(self.position_units) * self.fees_pct
                self.realized_pnl += close_pnl
                self.position_units = 0
            self.stopped = True
            self.stop_reason = "HARD_STOP_MAX_LOSS"
            return "STOP"
        return None

    def set_close_only(self, value: bool):
        self.close_only = value

    def unrealized(self, mark_price: float) -> float:
        if self.position_units == 0:
            return 0.0
        return (mark_price - self.avg_entry) * self.position_units

    def total_pnl(self, mark_price: float) -> float:
        return self.realized_pnl + self.unrealized(mark_price)


# ---------- PPT-Pause logic ----------

class PPTPauseLogic:
    """Replays cycle 56 design.

    Tick every 15min. Counts 3 consecutive ticks where:
      - emaStatus DOWNTREND (price < EMA200)
      - price < EMA200 by > 1.5%
      - RSI < 40
    On trigger: pauseAt = ts, set grid.close_only=True
    Reprise: 3 consecutive UPTREND ticks (price >= EMA200) + cooldown 1h
    """

    def __init__(self, pause_threshold: int = 3, resume_threshold: int = 3,
                 down_ema_pct: float = -0.015, up_ema_pct: float = 0.0,
                 rsi_down: float = 40, rsi_up: float = 45,
                 cooldown_ms: int = 3600_000):
        self.pause_threshold = pause_threshold
        self.resume_threshold = resume_threshold
        self.down_ema_pct = down_ema_pct
        self.up_ema_pct = up_ema_pct
        self.rsi_down = rsi_down
        self.rsi_up = rsi_up
        self.cooldown_ms = cooldown_ms

        self.down_count = 0
        self.up_count = 0
        self.paused_at_ts = None
        self.pause_events = []
        self.resume_events = []

    def tick(self, ts_ms: int, price: float, ema200: float, rsi_val: float,
             grid: GridState):
        if math.isnan(ema200) or math.isnan(rsi_val) or ema200 == 0:
            return

        pct_diff = (price - ema200) / ema200
        downtrend = (pct_diff < self.down_ema_pct) and (rsi_val < self.rsi_down)
        uptrend = (pct_diff >= self.up_ema_pct) and (rsi_val > self.rsi_up)

        if downtrend:
            self.down_count += 1
            self.up_count = 0
        elif uptrend:
            self.up_count += 1
            self.down_count = 0
        else:
            self.down_count = 0
            self.up_count = 0

        # pause trigger
        if (not grid.close_only and not grid.stopped
                and self.down_count >= self.pause_threshold):
            grid.set_close_only(True)
            self.paused_at_ts = ts_ms
            self.pause_events.append({
                "ts": ts_ms, "price": price, "ema200": ema200,
                "rsi": rsi_val, "down_pct": pct_diff,
            })

        # resume trigger
        if (grid.close_only and self.paused_at_ts is not None
                and self.up_count >= self.resume_threshold
                and (ts_ms - self.paused_at_ts) >= self.cooldown_ms):
            grid.set_close_only(False)
            self.resume_events.append({
                "ts": ts_ms, "price": price, "ema200": ema200,
                "rsi": rsi_val, "paused_for_ms": ts_ms - self.paused_at_ts,
            })
            self.paused_at_ts = None


# ---------- Backtest driver ----------

def load_candles(path: Path) -> List[List]:
    with open(path) as f:
        return json.load(f)


def run_scenario(candles_1m: List[List], with_pause: bool,
                 capital: float = 25.0, leverage: int = 7,
                 dca_passive: bool = False) -> Dict:
    if not candles_1m:
        return {"error": "no data"}

    center = candles_1m[0][4]  # close of first minute
    grid = GridState(center_price=center, capital_usd=capital, leverage=leverage)

    # Pre-compute hourly indicators (used by pause + by reporting)
    h_candles = resample_1min_to_1h(candles_1m)
    h_closes = [c[4] for c in h_candles]
    h_ema200 = ema(h_closes, 200) if len(h_closes) >= 200 else ema(h_closes, len(h_closes))
    h_rsi = rsi(h_closes, 14)
    h_ts = [c[0] for c in h_candles]

    pause = PPTPauseLogic() if with_pause else None

    HOUR_MS = 3600 * 1000
    TICK_MS = 15 * 60 * 1000
    last_pause_tick_ms = candles_1m[0][0]
    h_idx = 0

    if dca_passive:
        # invest full notional at center, hold to end
        units = grid.notional / center
        # close at last minute close
        final_price = candles_1m[-1][4]
        pnl = (final_price - center) * units
        pnl -= (center + final_price) * units * grid.fees_pct  # entry + exit fees
        return {
            "strategy": "DCA_PASSIVE",
            "realized_pnl": pnl,
            "total_pnl": pnl,
            "fills": 1,
            "stopped": False,
            "stop_reason": None,
            "final_price": final_price,
            "center": center,
            "pause_events": 0,
            "resume_events": 0,
        }

    for cd in candles_1m:
        ts, o, h, l, c, v = cd
        # grid tick on minute range
        grid.tick(low=l, high=h, close=c)

        # advance hourly indicator pointer
        while h_idx + 1 < len(h_ts) and ts >= h_ts[h_idx + 1]:
            h_idx += 1

        # PPT-Pause tick every 15min on current price + hourly indicators
        if pause and (ts - last_pause_tick_ms) >= TICK_MS:
            last_pause_tick_ms = ts
            current_ema200 = h_ema200[h_idx] if h_idx < len(h_ema200) else float("nan")
            current_rsi = h_rsi[h_idx] if h_idx < len(h_rsi) else float("nan")
            pause.tick(ts, c, current_ema200, current_rsi, grid)

        if grid.stopped:
            break

    final_price = candles_1m[-1][4]
    return {
        "strategy": "GRID_WITH_PAUSE" if with_pause else "GRID_NO_PAUSE",
        "realized_pnl": grid.realized_pnl,
        "unrealized_pnl": grid.unrealized(final_price),
        "total_pnl": grid.total_pnl(final_price),
        "fills": grid.fills,
        "stopped": grid.stopped,
        "stop_reason": grid.stop_reason,
        "final_price": final_price,
        "center": center,
        "position_units": grid.position_units,
        "close_only_end": grid.close_only,
        "pause_events": len(pause.pause_events) if pause else 0,
        "resume_events": len(pause.resume_events) if pause else 0,
    }


def main():
    datasets = [
        ("DOT Option B (2026-05-11 → 12, ~33h)", "binance_DOTUSDT_1min_optionb.json"),
        ("DOT 30d (2026-04-12 → 05-12)", "binance_DOTUSDT_1min_30d.json"),
        ("LINK 30d (2026-04-12 → 05-12)", "binance_LINKUSDT_1min_30d.json"),
        ("ADA 30d (2026-04-12 → 05-12)", "binance_ADAUSDT_1min_30d.json"),
    ]

    print("=" * 90)
    print("PPT-Pause Backtest — Cycle 57 — 2026-05-18")
    print("Grid: 4 levels, 1.5% spacing, leverage 7x, capital $25, maxLoss 10%, fees 0.05%")
    print("Pause: 3 consec 15min ticks, price < EMA200(1H) -1.5%, RSI(1H) < 40")
    print("Resume: 3 consec 15min ticks UPTREND, cooldown 1h")
    print("=" * 90)

    for label, fname in datasets:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"\n# {label}\n  MISSING: {fname}")
            continue
        candles = load_candles(path)
        print(f"\n# {label}")
        print(f"  candles: {len(candles)} | price_start: ${candles[0][4]:.4f} → price_end: ${candles[-1][4]:.4f} "
              f"({(candles[-1][4]/candles[0][4]-1)*100:+.2f}%)")

        a = run_scenario(candles, with_pause=False)
        b = run_scenario(candles, with_pause=True)
        c = run_scenario(candles, with_pause=False, dca_passive=True)

        for r in (a, b, c):
            tag = r["strategy"]
            tpnl = r["total_pnl"]
            rpnl = r.get("realized_pnl", 0.0)
            upnl = r.get("unrealized_pnl", 0.0)
            fills = r["fills"]
            stopped = r.get("stopped", False)
            sr = r.get("stop_reason") or ""
            pe = r.get("pause_events", 0)
            re_ = r.get("resume_events", 0)
            print(f"  {tag:18s} | total ${tpnl:+7.3f} ({tpnl/25*100:+5.1f}%) | "
                  f"realized ${rpnl:+6.3f} | uPnL ${upnl:+6.3f} | "
                  f"fills {fills:3d} | stopped={str(stopped):5s} {sr:18s} "
                  f"| pause {pe} resume {re_}")

        # delta with vs without pause
        delta = b["total_pnl"] - a["total_pnl"]
        delta_pct = delta / 25 * 100
        verdict = "PAUSE HELPS" if delta > 0 else ("PAUSE NEUTRAL" if abs(delta) < 0.01 else "PAUSE HURTS")
        print(f"  ΔPause vs NoPause: ${delta:+7.3f} ({delta_pct:+.2f}% of capital) → {verdict}")


if __name__ == "__main__":
    main()
