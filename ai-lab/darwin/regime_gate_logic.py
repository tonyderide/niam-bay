"""
Regime Gate Logic — Python port of Martin's Java RegimeGate.java
Cycle 60 — 2026-05-18 18h Paris

Reproduces the per-pair gate logic used in production:
  - 5 conditions on 4h OHLC: ADX(14), price_vs_EMA200, EMA50_vs_EMA200_spread,
    ATR%(14), RSI(14)
  - All 5 must be inside production IQR bounds → OPEN
  - Any fail → CLOSED → close_only on grid

Production bounds (Vmix calibration, 2026-05-09 + widened defaults):
  ADX(14) ∈ [5.0, 50.0]
  price_vs_EMA200 ∈ [-7.0%, 7.0%]
  EMA50_vs_EMA200_spread ∈ [-5.0%, 5.0%]
  ATR%(14) ∈ [0.6%, 3.0%]
  RSI(14) ∈ [20.0, 85.0]

Used by v17_walkforward_gated_backtest.py to measure conditional alpha of
spacing choices when gate filters bad regimes.
"""

import math
from dataclasses import dataclass
from typing import List, Optional


# ---------- Indicator helpers ----------

def wilder_smooth(values: List[float], period: int) -> List[float]:
    """Wilder's SMMA (RMA): seed = SMA of first `period`, then
    SMMA[i] = (SMMA[i-1] * (period-1) + values[i]) / period.

    Matches ta4j MMAIndicator behavior used by ADXIndicator + RSIIndicator.
    """
    if len(values) < period:
        return [float("nan")] * len(values)
    out: List[float] = [float("nan")] * (period - 1)
    seed = sum(values[:period]) / period
    out.append(seed)
    prev = seed
    for v in values[period:]:
        cur = (prev * (period - 1) + v) / period
        out.append(cur)
        prev = cur
    return out


def ema_series(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    out = [values[0]]
    k = 2.0 / (period + 1)
    for v in values[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def rsi_series(closes: List[float], period: int = 14) -> List[float]:
    """Wilder RSI matching ta4j RSIIndicator default behavior."""
    n = len(closes)
    if n < period + 1:
        return [50.0] * n
    out = [50.0] * period
    gains = [max(closes[i] - closes[i - 1], 0.0) for i in range(1, period + 1)]
    losses = [max(closes[i - 1] - closes[i], 0.0) for i in range(1, period + 1)]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period, n):
        if i > period:
            delta = closes[i] - closes[i - 1]
            gain = max(delta, 0.0)
            loss = max(-delta, 0.0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            out.append(100.0)
        else:
            rs = avg_gain / avg_loss
            out.append(100.0 - (100.0 / (1.0 + rs)))
    if len(out) < n:
        out = [50.0] * (n - len(out)) + out
    return out[:n]


def adx_series(candles_4h: List[List], period: int = 14) -> List[float]:
    """Compute ADX(14) using Wilder's smoothing matching ta4j.

    Each candle = [ts, o, h, l, c, v]. Returns list of ADX values; first 2*period
    entries are NaN.
    """
    n = len(candles_4h)
    if n < period * 2 + 1:
        return [float("nan")] * n

    tr_list = [float("nan")]
    plus_dm = [float("nan")]
    minus_dm = [float("nan")]

    for i in range(1, n):
        h = candles_4h[i][2]
        l = candles_4h[i][3]
        pc = candles_4h[i - 1][4]
        ph = candles_4h[i - 1][2]
        pl = candles_4h[i - 1][3]

        tr = max(h - l, abs(h - pc), abs(l - pc))
        up_move = h - ph
        down_move = pl - l
        pdm = up_move if (up_move > down_move and up_move > 0) else 0.0
        mdm = down_move if (down_move > up_move and down_move > 0) else 0.0

        tr_list.append(tr)
        plus_dm.append(pdm)
        minus_dm.append(mdm)

    # wilder smooth each (skip leading nan)
    def smooth(vals: List[float]) -> List[float]:
        clean = [v for v in vals if not math.isnan(v)]
        smoothed = wilder_smooth(clean, period)
        return [float("nan")] + smoothed + [float("nan")] * (n - 1 - len(smoothed))

    str_smooth = smooth(tr_list)
    pdm_smooth = smooth(plus_dm)
    mdm_smooth = smooth(minus_dm)

    dx_list: List[float] = []
    for i in range(n):
        s = str_smooth[i]
        pd = pdm_smooth[i]
        md = mdm_smooth[i]
        if math.isnan(s) or s == 0 or math.isnan(pd) or math.isnan(md):
            dx_list.append(float("nan"))
            continue
        plus_di = 100.0 * pd / s
        minus_di = 100.0 * md / s
        denom = plus_di + minus_di
        if denom == 0:
            dx_list.append(0.0)
        else:
            dx_list.append(100.0 * abs(plus_di - minus_di) / denom)

    # ADX = wilder smooth of DX
    dx_clean = [v for v in dx_list if not math.isnan(v)]
    adx_smoothed = wilder_smooth(dx_clean, period)
    adx_full = [float("nan")] * (n - len(adx_smoothed)) + adx_smoothed
    return adx_full[:n]


def atr_pct_series(candles_4h: List[List], period: int = 14) -> List[float]:
    """ATR(14) as percentage of close price — same simple SMA-of-TR method
    used in the Java code (last 14 TR averaged, divided by current price * 100).
    """
    n = len(candles_4h)
    if n < period + 1:
        return [float("nan")] * n
    out: List[float] = [float("nan")] * period
    tr_buf: List[float] = []
    for i in range(1, n):
        h = candles_4h[i][2]
        l = candles_4h[i][3]
        pc = candles_4h[i - 1][4]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_buf.append(tr)
        if len(tr_buf) > period:
            tr_buf.pop(0)
        if i >= period:
            atr = sum(tr_buf) / period
            price = candles_4h[i][4]
            out.append((atr / price) * 100.0 if price > 0 else float("nan"))
    return out[:n]


# ---------- Resample 1min → 4h ----------

def resample_to_4h(candles_1m: List[List]) -> List[List]:
    if not candles_1m:
        return []
    FOUR_H_MS = 4 * 3600 * 1000
    out: List[List] = []
    bucket = (candles_1m[0][0] // FOUR_H_MS) * FOUR_H_MS
    o, h, l, c, v = (candles_1m[0][1], candles_1m[0][2], candles_1m[0][3],
                     candles_1m[0][4], candles_1m[0][5])
    for cd in candles_1m[1:]:
        ts = (cd[0] // FOUR_H_MS) * FOUR_H_MS
        if ts != bucket:
            out.append([bucket, o, h, l, c, v])
            bucket = ts
            o = cd[1]; h = cd[2]; l = cd[3]; c = cd[4]; v = cd[5]
        else:
            h = max(h, cd[2])
            l = min(l, cd[3])
            c = cd[4]
            v += cd[5]
    out.append([bucket, o, h, l, c, v])
    return out


# ---------- Gate decision ----------

@dataclass(frozen=True)
class GateBounds:
    adx_min: float = 5.0
    adx_max: float = 50.0
    price_vs_ema200_min: float = -7.0
    price_vs_ema200_max: float = 7.0
    ema_spread_min: float = -5.0
    ema_spread_max: float = 5.0
    atr_pct_min: float = 0.6
    atr_pct_max: float = 3.0
    rsi_min: float = 20.0
    rsi_max: float = 85.0


@dataclass
class GateSnapshot:
    open: bool
    adx: float
    price_vs_ema200_pct: float
    ema_spread_pct: float
    atr_pct: float
    rsi: float
    failed: List[str]


class PerPairGate:
    """Per-pair gate evaluator. Pre-computes indicator series on 4h candles.

    Either supply `candles_4h` directly (preferred — preserves warmup history) or
    `candles_1m` which will be resampled. Direct 4h input lets you bring a full
    historical cache (years) so EMA200 stabilizes before the simulation window.
    """

    def __init__(self, candles_1m: Optional[List[List]] = None,
                 candles_4h: Optional[List[List]] = None,
                 bounds: Optional[GateBounds] = None):
        self.bounds = bounds or GateBounds()
        if candles_4h is not None:
            self.h4 = list(candles_4h)
        elif candles_1m is not None:
            self.h4 = resample_to_4h(candles_1m)
        else:
            raise ValueError("Provide candles_1m or candles_4h")
        self._n = len(self.h4)
        closes = [c[4] for c in self.h4]
        # EMA always produces values (seed = first close); we mark early bars
        # NaN via min_bars filter below so untrustworthy EMA200 doesn't fire gate.
        self.ema50 = ema_series(closes, 50) if self._n > 0 else []
        self.ema200 = ema_series(closes, 200) if self._n > 0 else []
        self.rsi = rsi_series(closes, 14)
        self.adx = adx_series(self.h4, 14)
        self.atr_pct = atr_pct_series(self.h4, 14)
        # Production requires ≥210 4h candles to evaluate. We mark gate UNKNOWN
        # for any tick before bar 210 in this dataset.
        self.min_bars = 210
        self._ts = [c[0] for c in self.h4]
        self._closes = closes

    def _idx_for_ts(self, ts_ms: int) -> int:
        """Last 4h bar whose start_ts <= ts_ms. -1 if before first bar."""
        if not self._ts or ts_ms < self._ts[0]:
            return -1
        lo, hi = 0, self._n - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._ts[mid] <= ts_ms:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def evaluate(self, ts_ms: int) -> Optional[GateSnapshot]:
        idx = self._idx_for_ts(ts_ms)
        if idx < 0 or idx >= self._n or idx < self.min_bars:
            return None
        ema200 = self.ema200[idx]
        ema50 = self.ema50[idx]
        rsi_v = self.rsi[idx]
        adx_v = self.adx[idx]
        atr_v = self.atr_pct[idx]
        close = self._closes[idx]
        if any(math.isnan(v) or v == 0 for v in (ema200, ema50, close)) \
                or math.isnan(rsi_v) or math.isnan(adx_v) or math.isnan(atr_v):
            return None
        price_vs_ema200 = (close - ema200) / ema200 * 100.0
        ema_spread = (ema50 - ema200) / ema200 * 100.0

        b = self.bounds
        failed: List[str] = []
        if adx_v < b.adx_min or adx_v > b.adx_max:
            failed.append(f"ADX={adx_v:.2f}")
        if price_vs_ema200 < b.price_vs_ema200_min or price_vs_ema200 > b.price_vs_ema200_max:
            failed.append(f"pVsE200={price_vs_ema200:+.2f}%")
        if ema_spread < b.ema_spread_min or ema_spread > b.ema_spread_max:
            failed.append(f"spread={ema_spread:+.2f}%")
        if atr_v < b.atr_pct_min or atr_v > b.atr_pct_max:
            failed.append(f"ATR%={atr_v:.2f}%")
        if rsi_v < b.rsi_min or rsi_v > b.rsi_max:
            failed.append(f"RSI={rsi_v:.2f}")
        return GateSnapshot(
            open=(not failed),
            adx=adx_v,
            price_vs_ema200_pct=price_vs_ema200,
            ema_spread_pct=ema_spread,
            atr_pct=atr_v,
            rsi=rsi_v,
            failed=failed,
        )


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    cache = Path("/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache")
    fname = sys.argv[1] if len(sys.argv) > 1 else "binance_LINKUSDT_1min_30d.json"
    path = cache / fname
    candles = json.load(open(path))
    gate = PerPairGate(candles)
    print(f"Loaded {len(candles)} 1min candles → {gate._n} 4h candles")
    # Sample every 24h, report gate state + reason
    SAMPLE_MS = 24 * 3600 * 1000
    last_sample = 0
    open_count = 0
    closed_count = 0
    for cd in candles[::240]:  # every 240min ≈ 4h
        snap = gate.evaluate(cd[0])
        if snap is None:
            continue
        if snap.open:
            open_count += 1
        else:
            closed_count += 1
    total = open_count + closed_count
    print(f"Gate OPEN: {open_count}/{total} ticks ({open_count/total*100:.1f}%)")
    print(f"Gate CLOSED: {closed_count}/{total} ticks ({closed_count/total*100:.1f}%)")
    # show last snapshot
    last_snap = gate.evaluate(candles[-1][0])
    if last_snap:
        state = "OPEN" if last_snap.open else "CLOSED"
        print(f"Last bar: {state} | ADX={last_snap.adx:.2f} pVsE200={last_snap.price_vs_ema200_pct:+.2f}% "
              f"spread={last_snap.ema_spread_pct:+.2f}% ATR%={last_snap.atr_pct:.2f}% RSI={last_snap.rsi:.2f}")
        if last_snap.failed:
            print(f"  failed: {', '.join(last_snap.failed)}")
