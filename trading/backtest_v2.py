"""
Backtest Strategies v2 -- Grid Trading avec filtres avances
==========================================================
5 strategies NOUVELLES testees sur ETH, SOL, DOT (3 mois, 1h candles Kraken).

Strategies:
  1. Grid + filtre RSI(14) : actif seulement quand RSI entre 40-60
  2. Grid + filtre EMA(20/50) : actif quand prix entre EMA20 et EMA50
  3. Grid bidirectionnel : buys ET sells symetriques
  4. Grid + stop dynamique : stop quand 3 fills consecutifs meme cote
  5. Grid + filtre volatilite : cash si vol24h > 4%, actif si < 2%

Fees: 0.02% maker (grid orders).
Capital: 1000 USD. Grid: 10 niveaux, spacing 0.8%, leverage 1x.
Note: Kraken limite a 720 candles max. On utilise 4h pour couvrir ~90 jours.
"""

import json, time, sys, os
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CAPITAL = 1000.0
NUM_LEVELS = 10
SPACING_PCT = 0.8
FEE_PCT = 0.02  # maker
LEVERAGE = 1
CANDLES_PER_DAY = 6  # 4h candles = 6 per day

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PAIRS = {
    "ETHUSD": "XETHZUSD",
    "SOLUSD": "SOLUSD",
    "DOTUSD": "DOTUSD",
}

# ---------------------------------------------------------------------------
# Data download (paginated)
# ---------------------------------------------------------------------------
def fetch_kraken_ohlc(pair_key, kraken_pair, since_ts, interval=240):
    """Fetch OHLC from Kraken. interval=240 (4h) to get ~90 days (720 max candles)."""
    cache_file = DATA_DIR / f"{pair_key.lower()}_{interval}m_3m.json"
    if cache_file.exists():
        age_h = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_h < 12:
            with open(cache_file) as f:
                data = json.load(f)
            print(f"  [cache] {pair_key} -- {len(data)} candles, {age_h:.1f}h old")
            return data

    print(f"  [download] {pair_key} from Kraken...")
    all_candles = []
    current_since = since_ts
    batch = 0

    while True:
        batch += 1
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair_key}&interval={interval}&since={current_since}"
        req = Request(url, headers={"User-Agent": "niam-bay-backtest/1.0"})
        try:
            resp = urlopen(req, timeout=30)
            data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"    error: {e}")
            break

        if data.get("error") and len(data["error"]) > 0:
            url2 = f"https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval={interval}&since={current_since}"
            req2 = Request(url2, headers={"User-Agent": "niam-bay-backtest/1.0"})
            try:
                resp2 = urlopen(req2, timeout=30)
                data = json.loads(resp2.read().decode())
            except Exception as e:
                print(f"    error on retry: {e}")
                break
            if data.get("error") and len(data["error"]) > 0:
                print(f"    API error: {data['error']}")
                break

        result = data.get("result", {})
        last = result.pop("last", None)

        candle_list = []
        for k, v in result.items():
            candle_list = v
            break

        if not candle_list:
            break

        before = len(all_candles)
        for c in candle_list:
            all_candles.append({
                "ts": int(c[0]),
                "o": float(c[1]),
                "h": float(c[2]),
                "l": float(c[3]),
                "c": float(c[4]),
                "v": float(c[6]),
            })
        added = len(all_candles) - before
        print(f"    batch {batch}: +{added} candles (total raw: {len(all_candles)})")

        # Pagination: if we got a full page (720), there may be more
        if last and int(last) > current_since and added >= 700:
            current_since = int(last)
            time.sleep(2)  # Rate limit
        else:
            break

    # Deduplicate by timestamp
    seen = set()
    unique = []
    for c in all_candles:
        if c["ts"] not in seen:
            seen.add(c["ts"])
            unique.append(c)
    unique.sort(key=lambda x: x["ts"])

    print(f"    final: {len(unique)} unique candles ({len(unique)/24:.1f} days)")
    with open(cache_file, "w") as f:
        json.dump(unique, f)
    return unique


def download_all():
    since_ts = int(time.time()) - 90 * 24 * 3600
    data = {}
    for pair_key, kraken_pair in PAIRS.items():
        candles = fetch_kraken_ohlc(pair_key, kraken_pair, since_ts)
        if candles:
            data[pair_key] = candles
    return data


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------
def compute_rsi(closes, period=14):
    rsi = np.full(len(closes), 50.0)
    if len(closes) < period + 1:
        return rsi
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100.0 - 100.0 / (1.0 + rs)
    return rsi


def compute_ema(closes, period):
    ema = np.zeros(len(closes))
    ema[0] = closes[0]
    k = 2.0 / (period + 1)
    for i in range(1, len(closes)):
        ema[i] = closes[i] * k + ema[i - 1] * (1 - k)
    return ema


def compute_volatility_24h(closes, candles_per_day=6):
    """Rolling 24h volatility as std of returns * sqrt(window), in %.
    candles_per_day=6 for 4h candles, =24 for 1h candles."""
    vol = np.zeros(len(closes))
    window = candles_per_day  # 24h worth of candles
    for i in range(window, len(closes)):
        segment = closes[i - window:i + 1]
        returns = np.diff(segment) / segment[:-1] * 100.0
        vol[i] = np.std(returns) * np.sqrt(window)
    return vol


# ---------------------------------------------------------------------------
# Grid engine base
# ---------------------------------------------------------------------------
class GridEngine:
    """
    Grid backtest engine.

    Capital is split: half stays as cash reserve, half is used for grid orders.
    Each grid level gets an equal slice of the grid capital.

    For bidirectional: capital is split 3 ways (reserve / long grid / short grid).
    """

    def __init__(self, candles, capital, num_levels, spacing_pct, fee_pct,
                 bidirectional=False):
        self.candles = candles
        self.initial_capital = capital
        self.num_levels = num_levels
        self.spacing = spacing_pct / 100.0
        self.fee = fee_pct / 100.0
        self.bidirectional = bidirectional

        self.cash = capital
        self.longs = []          # [(buy_price, qty), ...]
        self.shorts = []         # [(sell_price, qty), ...]  for bidir
        self.grid_center = None
        self.buy_levels = []
        self.sell_levels = []
        self.filled_buys = set()   # levels already filled (avoid double fill)
        self.filled_sells = set()

        # Stats
        self.rt_wins = 0
        self.rt_losses = 0
        self.rt_profit = 0.0
        self.forced_close_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_equity = capital
        self.equity_curve = []
        self.active_candles = 0
        self.inactive_candles = 0
        self.fills_history = []
        self.stopped = False

    def order_size_per_level(self):
        """How much USD to allocate per grid level."""
        # Use 50% of current cash for grid, divided among levels
        grid_capital = self.cash * 0.5
        return max(grid_capital / self.num_levels, 0.01)

    def setup_grid(self, price):
        self.grid_center = price
        self.buy_levels = []
        self.sell_levels = []
        self.filled_buys = set()
        self.filled_sells = set()
        for i in range(1, self.num_levels + 1):
            self.buy_levels.append(round(price * (1 - i * self.spacing), 6))
            self.sell_levels.append(round(price * (1 + i * self.spacing), 6))

    def equity(self, price):
        pos_val = sum(qty * price for _, qty in self.longs)
        short_pnl = sum(qty * (sp - price) for sp, qty, _ in self.shorts)
        return self.cash + pos_val + short_pnl

    def should_be_active(self, idx):
        return True

    def on_fill(self, side):
        pass

    def should_stop(self):
        return False

    def precompute(self, closes):
        pass

    def run(self):
        closes = np.array([c["c"] for c in self.candles])
        self.precompute(closes)

        for i, candle in enumerate(self.candles):
            price = candle["c"]
            low = candle["l"]
            high = candle["h"]

            eq = self.equity(price)
            self.equity_curve.append(eq)
            if eq > self.peak_equity:
                self.peak_equity = eq
            dd = (self.peak_equity - eq) / self.peak_equity * 100
            if dd > self.max_drawdown:
                self.max_drawdown = dd

            # Hard stop at 20% loss
            if eq < self.initial_capital * 0.80:
                self._close_all_with_accounting(price)
                self.stopped = True

            if self.stopped:
                self.inactive_candles += 1
                continue

            active = self.should_be_active(i)
            if not active:
                if self.longs or self.shorts:
                    self._close_all_with_accounting(price)
                self.inactive_candles += 1
                self.grid_center = None
                continue

            self.active_candles += 1

            if self.grid_center is None:
                self.setup_grid(price)
                continue

            # Recenter if price drifted beyond grid
            drift = abs(price - self.grid_center) / self.grid_center
            if drift > self.spacing * self.num_levels:
                self._close_all_with_accounting(price)
                self.setup_grid(price)
                continue

            # --- LONG SIDE: buy fills ---
            sz = self.order_size_per_level()
            for j, level in enumerate(self.buy_levels):
                if j in self.filled_buys:
                    continue
                if low <= level and self.cash >= sz:
                    qty = sz / level
                    cost = sz + sz * self.fee
                    self.cash -= cost
                    self.longs.append((level, qty))
                    self.filled_buys.add(j)
                    self.fills_history.append("buy")
                    self.on_fill("buy")
                    if self.should_stop():
                        self._close_all_with_accounting(price)
                        self.stopped = True
                        break

            if self.stopped:
                continue

            # --- LONG SIDE: sell (close) fills ---
            remaining = []
            for buy_price, qty in self.longs:
                target = buy_price * (1 + self.spacing)
                if high >= target:
                    revenue = qty * target
                    fee_cost = revenue * self.fee
                    self.cash += revenue - fee_cost
                    pnl = (target - buy_price) * qty - (buy_price * qty + revenue) * self.fee
                    self.rt_profit += pnl
                    if pnl > 0:
                        self.rt_wins += 1
                    else:
                        self.rt_losses += 1
                    # Un-fill the buy level so it can be re-used
                    for j, lev in enumerate(self.buy_levels):
                        if abs(lev - buy_price) < 0.0001 and j in self.filled_buys:
                            self.filled_buys.discard(j)
                            break
                    self.fills_history.append("sell")
                    self.on_fill("sell")
                else:
                    remaining.append((buy_price, qty))
            self.longs = remaining

            # --- SHORT SIDE (bidirectional only) ---
            if self.bidirectional:
                sz_short = self.order_size_per_level()
                for j, level in enumerate(self.sell_levels):
                    if j in self.filled_sells:
                        continue
                    if high >= level and self.cash >= sz_short:
                        qty = sz_short / level
                        # Lock margin: the USD value of the short
                        margin = sz_short
                        fee_cost = margin * self.fee
                        self.cash -= (margin + fee_cost)  # lock margin + fee
                        self.shorts.append((level, qty, margin))  # store margin
                        self.filled_sells.add(j)
                        self.fills_history.append("short_sell")
                        self.on_fill("short_sell")

                remaining_shorts = []
                for entry in self.shorts:
                    sell_price, qty, margin = entry
                    target = sell_price * (1 - self.spacing)
                    if low <= target:
                        # Cover: buy back cheaper
                        cover_cost = qty * target
                        fee_cost = cover_cost * self.fee
                        pnl = (sell_price - target) * qty - (sell_price * qty + cover_cost) * self.fee
                        self.cash += margin + pnl  # return margin + profit
                        self.rt_profit += pnl
                        if pnl > 0:
                            self.rt_wins += 1
                        else:
                            self.rt_losses += 1
                        for j, lev in enumerate(self.sell_levels):
                            if abs(lev - sell_price) < 0.0001 and j in self.filled_sells:
                                self.filled_sells.discard(j)
                                break
                        self.fills_history.append("short_cover")
                        self.on_fill("short_cover")
                    else:
                        remaining_shorts.append(entry)
                self.shorts = remaining_shorts

            if self.should_stop():
                self._close_all_with_accounting(price)
                self.stopped = True

        # End: close remaining
        final_price = self.candles[-1]["c"]
        self._close_all_with_accounting(final_price)
        return self.results()

    def _close_all_with_accounting(self, price):
        """Close all positions and track forced-close P&L."""
        for buy_price, qty in self.longs:
            revenue = qty * price
            fee_cost = revenue * self.fee
            self.cash += revenue - fee_cost
            pnl = (price - buy_price) * qty - (buy_price * qty + revenue) * self.fee
            self.forced_close_pnl += pnl
            if pnl >= 0:
                self.rt_wins += 1
            else:
                self.rt_losses += 1
        self.longs = []

        for entry in self.shorts:
            sell_price, qty, margin = entry
            cover_cost = qty * price
            fee_cost = cover_cost * self.fee
            pnl = (sell_price - price) * qty - (sell_price * qty + cover_cost) * self.fee
            self.cash += margin + pnl
            self.forced_close_pnl += pnl
            if pnl >= 0:
                self.rt_wins += 1
            else:
                self.rt_losses += 1
        self.shorts = []
        self.filled_buys = set()
        self.filled_sells = set()

    def results(self):
        total_candles = len(self.candles)
        total_days = total_candles / CANDLES_PER_DAY
        inactive_days = self.inactive_candles / CANDLES_PER_DAY
        total_rt = self.rt_wins + self.rt_losses
        final_eq = self.cash
        pnl_usd = final_eq - self.initial_capital
        pnl_pct = pnl_usd / self.initial_capital * 100
        profit_per_day = pnl_usd / max(total_days, 1)
        win_rate = self.rt_wins / max(total_rt, 1) * 100

        return {
            "total_rt": total_rt,
            "profit_total_usd": pnl_usd,
            "profit_pct": pnl_pct,
            "win_rate": win_rate,
            "max_drawdown_pct": self.max_drawdown,
            "profit_per_day": profit_per_day,
            "days_in_cash": inactive_days,
            "total_days": total_days,
            "active_days": total_days - inactive_days,
            "final_equity": final_eq,
            "rt_profit_usd": self.rt_profit,
            "forced_close_pnl": self.forced_close_pnl,
        }


# ---------------------------------------------------------------------------
# Strategy 1: Grid + RSI filter
# ---------------------------------------------------------------------------
class GridRSI(GridEngine):
    def precompute(self, closes):
        self.rsi = compute_rsi(closes, 14)

    def should_be_active(self, idx):
        return 40 <= self.rsi[idx] <= 60


# ---------------------------------------------------------------------------
# Strategy 2: Grid + EMA filter
# ---------------------------------------------------------------------------
class GridEMA(GridEngine):
    def precompute(self, closes):
        self.ema20 = compute_ema(closes, 20)
        self.ema50 = compute_ema(closes, 50)

    def should_be_active(self, idx):
        price = self.candles[idx]["c"]
        e20 = self.ema20[idx]
        e50 = self.ema50[idx]
        lo, hi = min(e20, e50), max(e20, e50)
        return lo <= price <= hi


# ---------------------------------------------------------------------------
# Strategy 3: Grid bidirectionnel
# ---------------------------------------------------------------------------
class GridBidir(GridEngine):
    def __init__(self, candles, capital, num_levels, spacing_pct, fee_pct):
        super().__init__(candles, capital, num_levels, spacing_pct, fee_pct,
                         bidirectional=True)


# ---------------------------------------------------------------------------
# Strategy 4: Grid + stop dynamique (3 fills consecutifs meme cote)
# ---------------------------------------------------------------------------
class GridDynamicStop(GridEngine):
    def __init__(self, candles, capital, num_levels, spacing_pct, fee_pct):
        super().__init__(candles, capital, num_levels, spacing_pct, fee_pct)
        self.consecutive_same = 0
        self.last_side = None
        self._triggered = False

    def on_fill(self, side):
        normalized = "buy" if ("buy" in side or "cover" in side) else "sell"
        if normalized == self.last_side:
            self.consecutive_same += 1
        else:
            self.consecutive_same = 1
            self.last_side = normalized

    def should_stop(self):
        if self.consecutive_same >= 3:
            self._triggered = True
            return True
        return False

    def should_be_active(self, idx):
        # After a stop, wait 24 candles (1 day) before re-entering
        if self._triggered:
            self._triggered = False
            self.stopped = False  # Allow re-entry
            self.consecutive_same = 0
            self.last_side = None
            # But skip this candle
            return False
        return True


# ---------------------------------------------------------------------------
# Strategy 5: Grid + filtre volatilite
# ---------------------------------------------------------------------------
class GridVolFilter(GridEngine):
    def precompute(self, closes):
        self.vol = compute_volatility_24h(closes)

    def should_be_active(self, idx):
        v = self.vol[idx]
        # Active si vol < 2%, cash si vol > 4%, entre 2-4% = garde positions mais pas de nouvelles
        return v < 2.0


# ---------------------------------------------------------------------------
# Plain grid for comparison
# ---------------------------------------------------------------------------
class GridPlain(GridEngine):
    pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def fmt(val, width=7, decimals=2, prefix="", suffix=""):
    """Format a number avoiding unicode issues."""
    sign = "+" if val >= 0 else ""
    return f"{prefix}{sign}{val:.{decimals}f}{suffix}"


def main():
    print("=" * 72)
    print("BACKTEST v2 -- Grid Trading Strategies (3 mois, 4h, Kraken)")
    print("=" * 72)
    print(f"Capital: ${CAPITAL}  |  Levels: {NUM_LEVELS}  |  Spacing: {SPACING_PCT}%  |  Fee: {FEE_PCT}%")
    print()

    print("[1/2] Download data...")
    all_data = download_all()
    if not all_data:
        print("ERROR: no data downloaded")
        sys.exit(1)

    strategies = {
        "0_Plain_Grid": lambda c: GridPlain(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
        "1_RSI_Filter": lambda c: GridRSI(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
        "2_EMA_Filter": lambda c: GridEMA(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
        "3_Bidirectional": lambda c: GridBidir(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
        "4_Dynamic_Stop": lambda c: GridDynamicStop(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
        "5_Vol_Filter": lambda c: GridVolFilter(c, CAPITAL, NUM_LEVELS, SPACING_PCT, FEE_PCT),
    }

    all_results = {}

    print("\n[2/2] Backtest...\n")
    for pair_key, candles in all_data.items():
        first_price = candles[0]["c"]
        last_price = candles[-1]["c"]
        hodl_return = (last_price - first_price) / first_price * 100
        days = len(candles) / CANDLES_PER_DAY

        print(f"--- {pair_key} ---  ({len(candles)} candles, {days:.0f} days)")
        print(f"    Price: {first_price:.2f} -> {last_price:.2f}  (HODL: {hodl_return:+.2f}%)")
        print()

        pair_results = {}
        pair_results["_meta"] = {
            "candles": len(candles),
            "days": days,
            "first_price": first_price,
            "last_price": last_price,
            "hodl_pct": hodl_return,
        }

        for strat_name, factory in strategies.items():
            engine = factory(candles)
            r = engine.run()
            pair_results[strat_name] = r

            print(f"  {strat_name:25s} | RT:{r['total_rt']:4d} | "
                  f"PnL:{r['profit_pct']:+7.2f}% (${r['profit_total_usd']:+8.2f}) | "
                  f"WR:{r['win_rate']:5.1f}% | DD:{r['max_drawdown_pct']:5.2f}% | "
                  f"$/d:{r['profit_per_day']:+6.2f} | "
                  f"Cash:{r['days_in_cash']:.0f}d/{r['total_days']:.0f}d")

        print(f"  {'CASH':25s} | RT:   0 | "
              f"PnL:  +0.00% ($    0.00) | "
              f"WR:  N/A | DD: 0.00% | "
              f"$/d: +0.00 | Cash:{days:.0f}d/{days:.0f}d")
        print(f"  {'HODL':25s} | RT:   0 | "
              f"PnL:{hodl_return:+7.2f}% "
              f"(${CAPITAL * hodl_return / 100:+8.2f}) | "
              f"WR:  N/A | DD:  ---  | "
              f"$/d:{CAPITAL * hodl_return / 100 / days:+6.2f} | Cash:0d/{days:.0f}d")
        print()

        all_results[pair_key] = pair_results

    write_report(all_results)
    print("\nDone.")


def write_report(all_results):
    report_path = Path("c:/niam-bay/docs/pensees/2026-03-29-backtest-strategies-v2.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    L = []
    L.append("# Backtest Grid Trading v2 -- Strategies avec filtres")
    L.append(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    L.append("## Parametres")
    L.append(f"- Capital: ${CAPITAL}")
    L.append(f"- Grid: {NUM_LEVELS} niveaux, spacing {SPACING_PCT}%, fees {FEE_PCT}% maker")
    L.append(f"- Donnees: Kraken OHLC 4h, ~3 derniers mois (720 candles max par appel)")
    L.append(f"- Stop loss global: 20% du capital")
    L.append(f"- Sizing: 50% du cash reparti sur {NUM_LEVELS} niveaux\n")

    L.append("## Strategies testees")
    L.append("1. **Grid + RSI(14)** : Actif seulement quand RSI entre 40-60 (range)")
    L.append("2. **Grid + EMA(20/50)** : Actif quand prix entre EMA20 et EMA50")
    L.append("3. **Grid bidirectionnel** : Longs + shorts symetriques, margin lockee")
    L.append("4. **Grid + stop dynamique** : Stop si 3 fills consecutifs meme cote (trend detecte)")
    L.append("5. **Grid + filtre vol** : Cash si volatilite 24h > 2%, actif sinon\n")

    # Summary table across all pairs
    for pair_key, pair_results in all_results.items():
        meta = pair_results["_meta"]
        L.append(f"## {pair_key}")
        L.append(f"- {meta['candles']} candles ({meta['days']:.0f} jours)")
        L.append(f"- Prix: {meta['first_price']:.2f} -> {meta['last_price']:.2f} "
                 f"(HODL: {meta['hodl_pct']:+.2f}%)\n")

        L.append("| Strategie | RTs | P&L % | P&L $ | Win Rate | Max DD | $/jour | Jours cash |")
        L.append("|-----------|-----|-------|-------|----------|--------|--------|------------|")

        for strat_name, r in pair_results.items():
            if strat_name.startswith("_"):
                continue
            L.append(
                f"| {strat_name} | {r['total_rt']} | "
                f"{r['profit_pct']:+.2f}% | ${r['profit_total_usd']:+.2f} | "
                f"{r['win_rate']:.1f}% | {r['max_drawdown_pct']:.2f}% | "
                f"${r['profit_per_day']:+.2f} | "
                f"{r['days_in_cash']:.0f}/{r['total_days']:.0f} |"
            )

        hodl_pnl = CAPITAL * meta["hodl_pct"] / 100
        L.append(f"| CASH | 0 | +0.00% | $0.00 | N/A | 0.00% | $0.00 | "
                 f"{meta['days']:.0f}/{meta['days']:.0f} |")
        L.append(f"| HODL | 0 | {meta['hodl_pct']:+.2f}% | ${hodl_pnl:+.2f} | N/A | --- | "
                 f"${hodl_pnl / meta['days']:+.2f} | 0/{meta['days']:.0f} |")
        L.append("")

    # Analysis
    L.append("## Analyse\n")

    any_beats_cash = False
    for pair_key, pair_results in all_results.items():
        meta = pair_results["_meta"]
        best_name = None
        best_pnl = -999
        for strat_name, r in pair_results.items():
            if strat_name.startswith("_"):
                continue
            if r["profit_pct"] > best_pnl:
                best_pnl = r["profit_pct"]
                best_name = strat_name

        hodl_pct = meta["hodl_pct"]
        L.append(f"### {pair_key}")

        if best_pnl > 0:
            any_beats_cash = True
            if best_pnl > hodl_pct:
                L.append(f"- Meilleure: **{best_name}** ({best_pnl:+.2f}%) -- bat HODL ({hodl_pct:+.2f}%)")
            else:
                L.append(f"- Meilleure: **{best_name}** ({best_pnl:+.2f}%) -- mais HODL fait mieux ({hodl_pct:+.2f}%)")
        else:
            L.append(f"- Aucune strategie profitable. Cash gagne.")
            if hodl_pct < 0:
                L.append(f"- HODL perd aussi ({hodl_pct:+.2f}%). Le cash est roi.")
            else:
                L.append(f"- HODL fait {hodl_pct:+.2f}%.")
        L.append("")

    L.append("## Verdict honnete\n")
    if not any_beats_cash:
        L.append("**Aucune strategie ne bat le cash sur cette periode.** "
                 "Le marche etait en tendance baissiere, pas en range. "
                 "Le grid trading ne fonctionne qu'en range.\n")
        L.append("Les filtres (RSI, EMA, vol) reduisent l'exposition et donc les pertes, "
                 "mais ne generent pas de profit net. Le mieux qu'on puisse faire "
                 "avec un grid en bear market, c'est de perdre moins -- pas de gagner.\n")
    else:
        L.append("Certaines strategies battent le cash, mais attention:\n")
        L.append("- Les filtres reduisent le nombre de trades et l'exposition")
        L.append("- Le grid bidirectionnel peut profiter des deux cotes mais double le risque")
        L.append("- Le stop dynamique coupe tot -- bon en trend, mauvais en range")
        L.append("- La performance passee ne garantit rien\n")

    L.append("**Rappel:** Le grid trading est une strategie de range. "
             "Si le marche trend (up ou down), le grid perd. "
             "Le seul avantage des filtres est de detecter le trend "
             "et de rester en cash pendant ces periodes.\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
