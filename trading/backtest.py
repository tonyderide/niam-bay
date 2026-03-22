"""
Niam-Bay Backtesting Framework
==============================
Generic backtester for any crypto strategy on historical candle data.

Usage:
    python backtest.py                          # run all built-in strategies on ETH 1m
    python backtest.py --data path/to/file.csv  # specify data file
"""

from __future__ import annotations

import copy
import csv
import math
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    index: int = 0


class Signal(Enum):
    HOLD = auto()
    BUY = auto()
    SELL = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()


@dataclass
class Order:
    signal: Signal
    order_type: OrderType
    price: Optional[float] = None     # None = use candle close
    size_pct: float = 1.0             # fraction of available capital (0.0 - 1.0)
    label: str = ""


@dataclass
class Fill:
    signal: Signal
    price: float
    size: float        # base currency
    cost: float        # quote currency
    fee: float
    timestamp: str
    label: str = ""


@dataclass
class Trade:
    """Round-trip: entry + exit."""
    entry_time: str
    exit_time: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    gross_pnl: float
    entry_fee: float
    exit_fee: float
    net_pnl: float
    label: str = ""

    @property
    def fees(self) -> float:
        return self.entry_fee + self.exit_fee


@dataclass
class Results:
    total_trades: int
    win_rate: float
    total_profit: float
    total_fees: float
    net_profit: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)

    def summary_row(self, name: str) -> dict:
        return {
            "Strategy": name,
            "Trades": self.total_trades,
            "Win%": f"{self.win_rate * 100:.1f}",
            "Gross": f"${self.total_profit:+.2f}",
            "Fees": f"${self.total_fees:.2f}",
            "Net": f"${self.net_profit:+.2f}",
            "MaxDD%": f"{self.max_drawdown * 100:.2f}",
            "Sharpe": f"{self.sharpe_ratio:.2f}",
            "PF": f"{self.profit_factor:.2f}",
        }


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def load_candles(path: str | Path) -> List[Candle]:
    """Load CSV candle data. Expected: timestamp,open,high,low,close,volume."""
    candles: List[Candle] = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            candles.append(Candle(
                timestamp=row["timestamp"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                index=i,
            ))
    return candles


# ---------------------------------------------------------------------------
# Strategy base class
# ---------------------------------------------------------------------------

class Strategy(ABC):
    """
    Subclass and implement on_candle().
    Return Order, list[Order], or None.
    """

    @abstractmethod
    def on_candle(self, candle: Candle, position: float, equity: float) -> Optional[Order | list[Order]]:
        """
        candle: current candle
        position: current position in base currency (+ = long, - = short, 0 = flat)
        equity: current total equity in quote currency
        """
        ...

    def on_fill(self, fill: Fill) -> None:
        pass

    def reset(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Technical indicators
# ---------------------------------------------------------------------------

class Indicators:
    """Rolling indicator calculator. Feed candles one by one."""

    def __init__(self):
        self.closes: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        self.volumes: List[float] = []
        self._ema_cache: dict[int, float] = {}

    def update(self, candle: Candle):
        self.closes.append(candle.close)
        self.highs.append(candle.high)
        self.lows.append(candle.low)
        self.volumes.append(candle.volume)

    @property
    def n(self) -> int:
        return len(self.closes)

    def sma(self, period: int) -> Optional[float]:
        if self.n < period:
            return None
        return sum(self.closes[-period:]) / period

    def ema(self, period: int) -> Optional[float]:
        if self.n < period:
            return None
        k = 2 / (period + 1)
        if period not in self._ema_cache:
            self._ema_cache[period] = sum(self.closes[:period]) / period
            for price in self.closes[period:]:
                self._ema_cache[period] = price * k + self._ema_cache[period] * (1 - k)
        else:
            self._ema_cache[period] = self.closes[-1] * k + self._ema_cache[period] * (1 - k)
        return self._ema_cache[period]

    def rsi(self, period: int = 14) -> Optional[float]:
        if self.n < period + 1:
            return None
        changes = [self.closes[i] - self.closes[i - 1] for i in range(-period, 0)]
        gains = [c for c in changes if c > 0]
        losses = [-c for c in changes if c < 0]
        avg_gain = sum(gains) / period if gains else 0.0
        avg_loss = sum(losses) / period if losses else 0.0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def bollinger(self, period: int = 20, num_std: float = 2.0):
        """Returns (lower, middle, upper) or None."""
        if self.n < period:
            return None
        data = self.closes[-period:]
        middle = sum(data) / period
        variance = sum((x - middle) ** 2 for x in data) / period
        std = math.sqrt(variance)
        return (middle - num_std * std, middle, middle + num_std * std)

    def highest(self, period: int, offset: int = 0) -> Optional[float]:
        """Highest high over [-(period+offset) : -offset] or [-period:] if offset=0."""
        need = period + offset
        if len(self.highs) < need:
            return None
        if offset == 0:
            return max(self.highs[-period:])
        return max(self.highs[-(period + offset):-offset])

    def lowest(self, period: int, offset: int = 0) -> Optional[float]:
        need = period + offset
        if len(self.lows) < need:
            return None
        if offset == 0:
            return min(self.lows[-period:])
        return min(self.lows[-(period + offset):-offset])

    def volume_sma(self, period: int) -> Optional[float]:
        if len(self.volumes) < period:
            return None
        return sum(self.volumes[-period:]) / period


# ---------------------------------------------------------------------------
# Backtester engine
# ---------------------------------------------------------------------------

class Backtester:
    """
    Event-driven backtester with proper accounting.

    Capital tracking:
    - cash: available quote currency not locked in positions
    - position: base currency held (positive = long, negative = short)
    - For longs: equity = cash + position * price
    - For shorts: equity = cash + margin_locked + unrealized_pnl

    Fees are always deducted from cash at fill time.
    """

    def __init__(
        self,
        data: List[Candle],
        strategy: Strategy,
        capital: float = 10_000.0,
        leverage: float = 1.0,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0005,
    ):
        self.data = data
        self.strategy = strategy
        self.initial_capital = capital
        self.leverage = leverage
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def run(self) -> Results:
        """
        Simple accounting model:
        - cash: free quote currency
        - margin_locked: quote currency locked as collateral for shorts
        - position: base amount (+long, -short)
        - equity = cash + margin_locked + unrealized_pnl (short) or cash + position*price (long)

        For longs:  cash goes down by cost+fee, position goes up
        For shorts: cash goes down by margin+fee, margin_locked goes up
        """
        self.strategy.reset()

        cash = self.initial_capital
        margin_locked = 0.0  # collateral for short positions
        position = 0.0
        entry_price = 0.0
        entry_time = ""
        entry_label = ""
        entry_fee = 0.0
        total_fees = 0.0
        trades: List[Trade] = []
        equity_curve: List[float] = []

        def equity(price: float) -> float:
            if position > 0:
                return cash + position * price
            elif position < 0:
                unrealized = (entry_price - price) * abs(position)
                return cash + margin_locked + unrealized
            return cash

        for candle in self.data:
            eq = equity(candle.close)
            equity_curve.append(eq)

            result = self.strategy.on_candle(candle, position, eq)
            if result is None:
                continue

            orders = result if isinstance(result, list) else [result]

            for order in orders:
                if order.signal == Signal.HOLD:
                    continue

                fee_rate = self.maker_fee if order.order_type == OrderType.LIMIT else self.taker_fee
                price = order.price if order.price else candle.close

                # ----- CLOSE existing position if signal reverses -----
                if order.signal == Signal.BUY and position < 0:
                    close_cost = abs(position) * price
                    fee = close_cost * fee_rate
                    total_fees += fee
                    gross_pnl = (entry_price - price) * abs(position)
                    # Return margin + pnl - fee to cash
                    cash += margin_locked + gross_pnl - fee
                    margin_locked = 0.0
                    trades.append(Trade(
                        entry_time=entry_time, exit_time=candle.timestamp,
                        side="short", entry_price=entry_price, exit_price=price,
                        size=abs(position), gross_pnl=gross_pnl,
                        entry_fee=entry_fee, exit_fee=fee,
                        net_pnl=gross_pnl - entry_fee - fee,
                        label=entry_label,
                    ))
                    self.strategy.on_fill(Fill(
                        Signal.BUY, price, abs(position), close_cost, fee,
                        candle.timestamp,
                    ))
                    position = 0.0
                    entry_fee = 0.0

                elif order.signal == Signal.SELL and position > 0:
                    sell_value = position * price
                    fee = sell_value * fee_rate
                    total_fees += fee
                    gross_pnl = (price - entry_price) * position
                    cash += sell_value - fee
                    trades.append(Trade(
                        entry_time=entry_time, exit_time=candle.timestamp,
                        side="long", entry_price=entry_price, exit_price=price,
                        size=position, gross_pnl=gross_pnl,
                        entry_fee=entry_fee, exit_fee=fee,
                        net_pnl=gross_pnl - entry_fee - fee,
                        label=entry_label,
                    ))
                    self.strategy.on_fill(Fill(
                        Signal.SELL, price, position, sell_value, fee,
                        candle.timestamp,
                    ))
                    position = 0.0
                    entry_fee = 0.0

                # ----- OPEN new position if now flat -----
                if position == 0.0:
                    alloc = cash * order.size_pct * self.leverage
                    if alloc < 1.0:
                        continue

                    if order.signal == Signal.BUY:
                        size = alloc / price
                        fee = alloc * fee_rate
                        total_fees += fee
                        cash -= alloc + fee
                        position = size
                        entry_price = price
                        entry_time = candle.timestamp
                        entry_label = order.label
                        entry_fee = fee
                        self.strategy.on_fill(Fill(
                            Signal.BUY, price, size, alloc, fee,
                            candle.timestamp, order.label,
                        ))

                    elif order.signal == Signal.SELL:
                        size = alloc / price
                        fee = alloc * fee_rate
                        total_fees += fee
                        # Lock margin from cash
                        cash -= alloc + fee
                        margin_locked = alloc
                        position = -size
                        entry_price = price
                        entry_time = candle.timestamp
                        entry_label = order.label
                        entry_fee = fee
                        self.strategy.on_fill(Fill(
                            Signal.SELL, price, size, alloc, fee,
                            candle.timestamp, order.label,
                        ))

        # Force-close at end
        if len(self.data) > 0 and abs(position) > 1e-12:
            last = self.data[-1]
            price = last.close
            fee_rate = self.taker_fee
            if position > 0:
                sell_value = position * price
                fee = sell_value * fee_rate
                total_fees += fee
                gross_pnl = (price - entry_price) * position
                cash += sell_value - fee
                trades.append(Trade(
                    entry_time=entry_time, exit_time=last.timestamp,
                    side="long", entry_price=entry_price, exit_price=price,
                    size=position, gross_pnl=gross_pnl,
                    entry_fee=entry_fee, exit_fee=fee,
                    net_pnl=gross_pnl - entry_fee - fee,
                    label=entry_label + " [forced]",
                ))
            else:
                close_cost = abs(position) * price
                fee = close_cost * fee_rate
                total_fees += fee
                gross_pnl = (entry_price - price) * abs(position)
                cash += margin_locked + gross_pnl - fee
                margin_locked = 0.0
                trades.append(Trade(
                    entry_time=entry_time, exit_time=last.timestamp,
                    side="short", entry_price=entry_price, exit_price=price,
                    size=abs(position), gross_pnl=gross_pnl,
                    entry_fee=entry_fee, exit_fee=fee,
                    net_pnl=gross_pnl - entry_fee - fee,
                    label=entry_label + " [forced]",
                ))
            position = 0.0

        # Final equity
        equity_curve.append(cash)

        return self._compute_results(trades, total_fees, equity_curve)

    def _compute_results(self, trades: List[Trade], total_fees: float,
                         equity_curve: List[float]) -> Results:
        n_trades = len(trades)
        wins = [t for t in trades if t.net_pnl > 0]
        win_rate = len(wins) / n_trades if n_trades > 0 else 0.0
        total_profit = sum(t.gross_pnl for t in trades)
        net_profit = sum(t.net_pnl for t in trades)

        # Max drawdown
        max_dd = 0.0
        peak = self.initial_capital
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        # Sharpe (annualized from 1-min bars)
        sharpe = 0.0
        if len(equity_curve) > 2:
            returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i - 1] > 0:
                    returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])
            if returns:
                mean_r = sum(returns) / len(returns)
                var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
                std_r = math.sqrt(var_r) if var_r > 0 else 1e-10
                sharpe = (mean_r / std_r) * math.sqrt(525_600)

        # Profit factor
        gross_w = sum(t.gross_pnl for t in trades if t.gross_pnl > 0)
        gross_l = abs(sum(t.gross_pnl for t in trades if t.gross_pnl < 0))
        pf = gross_w / gross_l if gross_l > 0 else (float("inf") if gross_w > 0 else 0.0)

        return Results(
            total_trades=n_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            total_fees=total_fees,
            net_profit=net_profit,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            profit_factor=pf,
            trades=trades,
            equity_curve=equity_curve,
        )


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------

class GridStrategy(Strategy):
    """
    Grid: buy when price drops to a lower grid level, sell when it rises.
    Only trades a fraction of capital per grid hit. Uses LIMIT (maker fee).
    """

    def __init__(self, spacing_pct: float = 0.3, levels: int = 5):
        self.spacing_pct = spacing_pct / 100.0
        self.levels = levels
        self.grid: List[float] = []
        self.last_idx: Optional[int] = None
        self._init = False

    def reset(self):
        self.grid = []
        self.last_idx = None
        self._init = False

    def on_candle(self, candle: Candle, position: float, equity: float) -> Optional[Order]:
        if not self._init:
            mid = candle.close
            self.grid = sorted(
                mid * (1 + i * self.spacing_pct)
                for i in range(-self.levels, self.levels + 1)
            )
            self.last_idx = self.levels  # center
            self._init = True
            return None

        price = candle.close
        closest = min(range(len(self.grid)), key=lambda i: abs(self.grid[i] - price))

        if closest == self.last_idx:
            return None

        # Size per grid hit: split capital among levels
        size_pct = 1.0 / (2 * self.levels + 1)

        if closest < self.last_idx:
            self.last_idx = closest
            # Price dropped -> buy if flat or short, close if long (won't happen in grid usually)
            if position <= 0:
                return Order(Signal.BUY, OrderType.LIMIT, self.grid[closest],
                             size_pct=size_pct, label=f"grid-L{closest}")
            else:
                # Already long, just track
                return None
        else:
            self.last_idx = closest
            if position >= 0:
                return Order(Signal.SELL, OrderType.LIMIT, self.grid[closest],
                             size_pct=size_pct, label=f"grid-L{closest}")
            else:
                return None


class MeanReversionStrategy(Strategy):
    """
    Mean reversion: buy oversold (BB lower + low RSI), sell overbought.
    Uses LIMIT (maker fee). Allocates 50% per trade.
    """

    def __init__(self, ema_period: int = 20, rsi_period: int = 14, bb_period: int = 20):
        self.ema_period = ema_period
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.ind = Indicators()

    def reset(self):
        self.ind = Indicators()

    def on_candle(self, candle: Candle, position: float, equity: float) -> Optional[Order]:
        self.ind.update(candle)

        rsi = self.ind.rsi(self.rsi_period)
        bb = self.ind.bollinger(self.bb_period)
        if rsi is None or bb is None:
            return None

        lower, middle, upper = bb

        # Entry: buy oversold
        if candle.close < lower and rsi < 35 and position <= 0:
            return Order(Signal.BUY, OrderType.LIMIT, candle.close,
                         size_pct=0.5, label=f"mr-buy rsi={rsi:.0f}")

        # Entry: sell overbought
        if candle.close > upper and rsi > 65 and position >= 0:
            return Order(Signal.SELL, OrderType.LIMIT, candle.close,
                         size_pct=0.5, label=f"mr-sell rsi={rsi:.0f}")

        # Exit: revert to mean
        if position > 0 and candle.close > middle:
            return Order(Signal.SELL, OrderType.LIMIT, candle.close,
                         size_pct=1.0, label="mr-exit-long")

        if position < 0 and candle.close < middle:
            return Order(Signal.BUY, OrderType.LIMIT, candle.close,
                         size_pct=1.0, label="mr-exit-short")

        return None


class BreakoutStrategy(Strategy):
    """
    Breakout: enter when price breaks PREVIOUS bar's lookback range, with
    volume confirmation. Uses MARKET (taker fee). Allocates 80% per trade.
    """

    def __init__(self, lookback: int = 20, volume_mult: float = 1.5):
        self.lookback = lookback
        self.volume_mult = volume_mult
        self.ind = Indicators()

    def reset(self):
        self.ind = Indicators()

    def on_candle(self, candle: Candle, position: float, equity: float) -> Optional[Order]:
        self.ind.update(candle)

        # Use offset=1 so we compare current bar to PREVIOUS lookback range
        # (otherwise highest always == current high and breakout never fires)
        if self.ind.n < self.lookback + 1:
            return None

        prev_highs = self.ind.highs[-(self.lookback + 1):-1]
        prev_lows = self.ind.lows[-(self.lookback + 1):-1]
        prev_vols = self.ind.volumes[-(self.lookback + 1):-1]

        highest = max(prev_highs)
        lowest = min(prev_lows)
        vol_avg = sum(prev_vols) / len(prev_vols)

        vol_ok = candle.volume > vol_avg * self.volume_mult

        # Breakout long
        if candle.close > highest and vol_ok and position <= 0:
            return Order(Signal.BUY, OrderType.MARKET,
                         size_pct=0.8, label=f"bo-long v={candle.volume:.1f}")

        # Breakout short
        if candle.close < lowest and vol_ok and position >= 0:
            return Order(Signal.SELL, OrderType.MARKET,
                         size_pct=0.8, label=f"bo-short v={candle.volume:.1f}")

        # Exit: revert to midpoint
        mid = (highest + lowest) / 2
        if position > 0 and candle.close < mid:
            return Order(Signal.SELL, OrderType.MARKET,
                         size_pct=1.0, label="bo-exit-long")
        if position < 0 and candle.close > mid:
            return Order(Signal.BUY, OrderType.MARKET,
                         size_pct=1.0, label="bo-exit-short")

        return None


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def print_table(results: dict[str, Results]):
    cols = ["Strategy", "Trades", "Win%", "Gross", "Fees", "Net",
            "MaxDD%", "Sharpe", "PF"]
    rows = [res.summary_row(name) for name, res in results.items()]

    widths = {c: len(c) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))

    hdr = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    print()
    print("=" * len(hdr))
    print("  BACKTEST RESULTS")
    print("=" * len(hdr))
    print(hdr)
    print(sep)
    for row in rows:
        print(" | ".join(str(row.get(c, "")).ljust(widths[c]) for c in cols))
    print("=" * len(hdr))
    print()


def print_trades(trades: List[Trade], limit: int = 8):
    if not trades:
        print("  (no trades)")
        return
    for i, t in enumerate(trades[:limit]):
        d = "L" if t.side == "long" else "S"
        w = "W" if t.net_pnl > 0 else "L"
        print(f"  {i+1:3d}. {d} {t.entry_price:>9.2f}->{t.exit_price:>9.2f}  "
              f"sz={t.size:.4f}  pnl={t.net_pnl:+8.2f} [{w}]  "
              f"fee={t.fees:.2f}  {t.label}")
    if len(trades) > limit:
        print(f"  ... +{len(trades) - limit} more")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    data_dir = Path(__file__).parent / "data"

    eth_file = data_dir / "XETHZUSD_1m.csv"
    if not eth_file.exists():
        csv_files = list(data_dir.glob("*_1m.csv"))
        if not csv_files:
            print("ERROR: No 1m CSV data in", data_dir)
            sys.exit(1)
        eth_file = csv_files[0]

    print(f"Loading {eth_file.name} ...")
    candles = load_candles(eth_file)
    print(f"  {len(candles)} candles  |  "
          f"{candles[0].timestamp} -> {candles[-1].timestamp}  |  "
          f"${min(c.low for c in candles):.2f} - ${max(c.high for c in candles):.2f}")
    print()

    capital = 10_000.0

    strategies = {
        "Grid 0.3%/5lv":      GridStrategy(spacing_pct=0.3, levels=5),
        "Grid 0.5%/3lv":      GridStrategy(spacing_pct=0.5, levels=3),
        "Grid 1.0%/3lv":      GridStrategy(spacing_pct=1.0, levels=3),
        "MeanRev 20/14/20":   MeanReversionStrategy(20, 14, 20),
        "MeanRev 10/7/10":    MeanReversionStrategy(10, 7, 10),
        "Breakout 20/1.5x":   BreakoutStrategy(20, 1.5),
        "Breakout 20/1.0x":   BreakoutStrategy(20, 1.0),
        "Breakout 50/1.5x":   BreakoutStrategy(50, 1.5),
    }

    all_results: dict[str, Results] = {}
    for name, strat in strategies.items():
        bt = Backtester(candles, strat, capital)
        res = bt.run()
        all_results[name] = res
        print(f"  {name:25s}  {res.total_trades:3d} trades  net={res.net_profit:+10.2f}")

    print_table(all_results)

    # Trade details for strategies with trades
    for name, res in all_results.items():
        if res.total_trades > 0:
            print(f"--- {name} ---")
            print_trades(res.trades, limit=5)
            print()

    # Best strategy
    best = max(all_results, key=lambda k: all_results[k].net_profit)
    print(f"BEST: {best} -> Net ${all_results[best].net_profit:+.2f}")
    print()

    # Cross-pair with best strategy
    files_1m = sorted(data_dir.glob("*_1m.csv"))
    if len(files_1m) > 1:
        print("--- Cross-pair test with best strategy ---")
        cross: dict[str, Results] = {}
        for f in files_1m:
            pair = f.stem.replace("_1m", "")
            c = load_candles(f)
            fresh = copy.deepcopy(strategies[best])
            bt = Backtester(c, fresh, capital)
            cross[pair] = bt.run()
        print_table(cross)


if __name__ == "__main__":
    main()
