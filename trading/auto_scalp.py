#!/usr/bin/env python3
"""
Auto Scalp BB — Module de scalping autonome basé sur les Bollinger Bands.
Conçu pour être intégré au sentinel Martin Grid.

Zero dépendance externe : urllib + json + math uniquement.

Stratégie :
  - BB(20, 2σ) sur candles 1min
  - LONG quand prix <= lower BB
  - SHORT quand prix >= upper BB
  - TP +0.5%, SL -0.5%
  - Max 1 position, max 10 trades/jour, pause après 3 pertes consécutives
"""

import json
import logging
import math
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ─── Configuration ────────────────────────────────────────────────────────────

INSTRUMENT = os.environ.get("SCALP_INSTRUMENT", "PF_ETHUSD")
CAPITAL = float(os.environ.get("SCALP_CAPITAL", "16"))
LEVERAGE = int(os.environ.get("SCALP_LEVERAGE", "2"))
TP_PCT = float(os.environ.get("SCALP_TP_PCT", "0.5"))   # +0.5%
SL_PCT = float(os.environ.get("SCALP_SL_PCT", "0.5"))   # -0.5%
POLL_INTERVAL = int(os.environ.get("SCALP_POLL", "30"))  # secondes
DEMO = os.environ.get("SCALP_DEMO", "false").lower() == "true"

BB_PERIOD = 20
BB_STD_MULT = 2.0

TRADING_HOUR_START = 8   # UTC
TRADING_HOUR_END = 22    # UTC

MAX_TRADES_PER_DAY = 10
MAX_DAILY_LOSS = -2.0    # USD
MAX_CONSECUTIVE_LOSSES = 3
LOSS_PAUSE_SECONDS = 1800  # 30 min

MARTIN_API = "http://localhost:8081"
KRAKEN_API = "https://futures.kraken.com/derivatives/api/v3"

LOG_FILE = os.environ.get("SCALP_LOG", "/home/ubuntu/scalp.log")
TELEGRAM_ENV = "/home/ubuntu/.telegram-env"

# ─── Logging ──────────────────────────────────────────────────────────────────

logger = logging.getLogger("auto_scalp")
logger.setLevel(logging.INFO)

_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

_fh = logging.FileHandler(LOG_FILE)
_fh.setFormatter(_fmt)
logger.addHandler(_fh)

_ch = logging.StreamHandler()
_ch.setFormatter(_fmt)
logger.addHandler(_ch)

# ─── Telegram ─────────────────────────────────────────────────────────────────

_TG_TOKEN = None
_TG_CHAT_ID = None


def _load_telegram():
    global _TG_TOKEN, _TG_CHAT_ID
    if _TG_TOKEN:
        return True
    try:
        with open(TELEGRAM_ENV) as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_TOKEN="):
                    _TG_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    _TG_CHAT_ID = line.split("=", 1)[1].strip().strip('"').strip("'")
        return bool(_TG_TOKEN and _TG_CHAT_ID)
    except FileNotFoundError:
        logger.warning("Telegram env not found at %s — notifications disabled", TELEGRAM_ENV)
        return False


def tg_send(msg):
    """Envoie un message Telegram (fire-and-forget)."""
    if not _load_telegram():
        return
    try:
        url = f"https://api.telegram.org/bot{_TG_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": _TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)


# ─── API helpers ──────────────────────────────────────────────────────────────

def api_get(url, timeout=10):
    """GET JSON depuis une URL."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def api_post(url, data, timeout=10):
    """POST JSON vers une URL."""
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ─── Market data ──────────────────────────────────────────────────────────────

def fetch_candles_1m(instrument=INSTRUMENT, count=30):
    """Récupère les candles 1min depuis Kraken Futures API publique.
    Retourne une liste de dicts avec au minimum 'close' (float).
    """
    # Kraken Futures OHLC endpoint
    url = f"{KRAKEN_API}/tickers/{instrument}"
    data = api_get(url)
    # Fallback : utiliser le ticker pour le prix courant si candles pas dispo
    # On va utiliser l'API charts pour les candles
    url_candles = (
        f"https://futures.kraken.com/api/charts/v1/trade/{instrument}/1m"
        f"?from={int(time.time()) - 60 * count}&to={int(time.time())}"
    )
    try:
        candles_data = api_get(url_candles)
        # Format: {"candles": [{"time": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}]}
        if "candles" in candles_data and len(candles_data["candles"]) >= BB_PERIOD:
            return candles_data["candles"]
    except Exception as e:
        logger.warning("Charts API failed (%s), trying alternate", e)

    # Alternate : Kraken Spot REST pour OHLC (fonctionne toujours)
    # PF_ETHUSD -> ETHUSD pair
    pair = instrument.replace("PF_", "")
    url_spot = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1"
    try:
        spot_data = api_get(url_spot)
        if "result" in spot_data:
            for key in spot_data["result"]:
                if key != "last":
                    raw = spot_data["result"][key]
                    # Format: [time, open, high, low, close, vwap, volume, count]
                    candles = []
                    for c in raw[-count:]:
                        candles.append({
                            "time": c[0],
                            "open": float(c[1]),
                            "high": float(c[2]),
                            "low": float(c[3]),
                            "close": float(c[4]),
                            "volume": float(c[6]),
                        })
                    return candles
    except Exception as e:
        logger.warning("Spot OHLC API failed: %s", e)

    return []


def fetch_price(instrument=INSTRUMENT):
    """Récupère le prix courant via Kraken Futures ticker."""
    url = f"{KRAKEN_API}/tickers/{instrument}"
    data = api_get(url)
    # Le ticker renvoie {"tickers": [{"tag": ..., "last": ..., ...}]}
    if "tickers" in data:
        for t in data["tickers"]:
            if t.get("symbol", "").upper() == instrument.upper() or t.get("tag", "").upper() == instrument.upper():
                return float(t["last"])
        # Si un seul ticker, le prendre
        if len(data["tickers"]) == 1:
            return float(data["tickers"][0]["last"])
    raise ValueError(f"Could not parse price from ticker: {data}")


def fetch_balance():
    """Récupère le balance depuis Martin API."""
    try:
        data = api_get(f"{MARTIN_API}/api/system/status")
        # Essayer différents champs possibles
        for key in ("balance", "availableBalance", "equity"):
            if key in data:
                return float(data[key])
        # Chercher dans les sous-objets
        if "account" in data:
            for key in ("balance", "availableBalance", "equity"):
                if key in data["account"]:
                    return float(data["account"][key])
    except Exception as e:
        logger.warning("Could not fetch balance: %s", e)
    return None


# ─── Bollinger Bands ──────────────────────────────────────────────────────────

def compute_bb(candles, period=BB_PERIOD, mult=BB_STD_MULT):
    """Calcule les Bollinger Bands.
    Retourne (sma, upper, lower) ou None si pas assez de données.
    """
    if len(candles) < period:
        return None

    closes = [c["close"] for c in candles[-period:]]
    sma = sum(closes) / period
    variance = sum((c - sma) ** 2 for c in closes) / period
    std = math.sqrt(variance)

    upper = sma + mult * std
    lower = sma - mult * std

    return sma, upper, lower


# ─── Trading logic ────────────────────────────────────────────────────────────

class ScalpBot:
    def __init__(self):
        # Position state
        self.in_position = False
        self.position_side = None    # "buy" or "sell"
        self.entry_price = 0.0
        self.position_size = 0.0
        self.entry_time = None

        # Daily counters (reset at midnight UTC)
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.current_day = None

        # Consecutive loss tracking
        self.consecutive_losses = 0
        self.paused_until = 0  # timestamp

        # Stats
        self.total_trades = 0
        self.total_pnl = 0.0

    def _reset_daily(self):
        """Reset daily counters if new day."""
        today = datetime.now(timezone.utc).date()
        if self.current_day != today:
            if self.current_day is not None:
                logger.info("=== Nouveau jour — reset compteurs (PnL hier: $%.2f) ===", self.daily_pnl)
            self.current_day = today
            self.trades_today = 0
            self.daily_pnl = 0.0

    def _is_trading_hours(self):
        """Vérifie si on est dans les heures de trading."""
        hour = datetime.now(timezone.utc).hour
        return TRADING_HOUR_START <= hour < TRADING_HOUR_END

    def _is_paused(self):
        """Vérifie si on est en pause après pertes consécutives."""
        if time.time() < self.paused_until:
            return True
        return False

    def _can_trade(self):
        """Vérifie toutes les conditions pour ouvrir un trade."""
        if self.in_position:
            return False, "position ouverte"
        if not self._is_trading_hours():
            return False, "hors heures (08-22 UTC)"
        if self._is_paused():
            remaining = int(self.paused_until - time.time())
            return False, f"pause pertes ({remaining}s restantes)"
        if self.trades_today >= MAX_TRADES_PER_DAY:
            return False, f"max trades/jour atteint ({MAX_TRADES_PER_DAY})"
        if self.daily_pnl <= MAX_DAILY_LOSS:
            return False, f"max perte journalière (${self.daily_pnl:.2f})"
        return True, "OK"

    def _calc_size(self, price):
        """Calcule la taille de position."""
        size = (CAPITAL * LEVERAGE) / price
        # Arrondir à 5 décimales (Kraken Futures)
        return round(size, 5)

    def _tp_price(self, entry, side):
        """Calcule le prix de Take Profit."""
        if side == "buy":
            return entry * (1 + TP_PCT / 100)
        else:
            return entry * (1 - TP_PCT / 100)

    def _sl_price(self, entry, side):
        """Calcule le prix de Stop Loss."""
        if side == "buy":
            return entry * (1 - SL_PCT / 100)
        else:
            return entry * (1 + SL_PCT / 100)

    def open_position(self, side, price):
        """Ouvre une position via Martin API."""
        # Vérifier le balance
        balance = fetch_balance()
        if balance is not None and balance < CAPITAL * 0.5:
            logger.warning("Balance trop bas ($%.2f) — skip trade", balance)
            return False

        size = self._calc_size(price)
        tp = self._tp_price(price, side)
        sl = self._sl_price(price, side)

        order_data = {
            "instrument": INSTRUMENT,
            "side": side,
            "size": size,
            "demo": DEMO,
        }

        try:
            result = api_post(f"{MARTIN_API}/api/scalp/order", order_data)
            logger.info("ORDER %s %.5f %s @ $%.2f — TP: $%.2f / SL: $%.2f", side.upper(), size, INSTRUMENT, price, tp, sl)

            self.in_position = True
            self.position_side = side
            self.entry_price = price
            self.position_size = size
            self.entry_time = time.time()
            self.trades_today += 1
            self.total_trades += 1

            tg_send(
                f"🔵 *SCALP {side.upper()}*\n"
                f"Instrument: `{INSTRUMENT}`\n"
                f"Prix: `${price:.2f}`\n"
                f"Size: `{size:.5f}`\n"
                f"TP: `${tp:.2f}` (+{TP_PCT}%)\n"
                f"SL: `${sl:.2f}` (-{SL_PCT}%)\n"
                f"Trade #{self.trades_today}/{MAX_TRADES_PER_DAY}"
            )
            return True

        except Exception as e:
            logger.error("Order failed: %s", e)
            return False

    def close_position(self, reason, current_price):
        """Ferme la position avec un ordre inverse reduceOnly."""
        close_side = "sell" if self.position_side == "buy" else "buy"

        order_data = {
            "instrument": INSTRUMENT,
            "side": close_side,
            "size": self.position_size,
            "reduceOnly": True,
            "demo": DEMO,
        }

        # Calcul PnL
        if self.position_side == "buy":
            pnl = (current_price - self.entry_price) / self.entry_price * CAPITAL * LEVERAGE
        else:
            pnl = (self.entry_price - current_price) / self.entry_price * CAPITAL * LEVERAGE

        try:
            result = api_post(f"{MARTIN_API}/api/scalp/order", order_data)
        except Exception as e:
            logger.error("Close order failed: %s — will retry", e)
            return False

        duration = int(time.time() - self.entry_time) if self.entry_time else 0
        self.daily_pnl += pnl
        self.total_pnl += pnl

        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                self.paused_until = time.time() + LOSS_PAUSE_SECONDS
                logger.warning("⚠️ %d pertes consécutives — pause %d min", self.consecutive_losses, LOSS_PAUSE_SECONDS // 60)
        else:
            self.consecutive_losses = 0

        emoji = "🟢" if pnl >= 0 else "🔴"
        logger.info(
            "CLOSE %s @ $%.2f — %s PnL: $%.3f (%s) — durée: %ds — jour: $%.2f",
            self.position_side.upper(), current_price, reason, pnl,
            "profit" if pnl >= 0 else "perte", duration, self.daily_pnl
        )

        tg_send(
            f"{emoji} *SCALP CLOSE* ({reason})\n"
            f"Side: `{self.position_side.upper()}`\n"
            f"Entry: `${self.entry_price:.2f}` → Exit: `${current_price:.2f}`\n"
            f"PnL: `${pnl:+.3f}`\n"
            f"Durée: `{duration}s`\n"
            f"Jour: `${self.daily_pnl:+.2f}` | Total: `${self.total_pnl:+.2f}`"
        )

        # Reset position
        self.in_position = False
        self.position_side = None
        self.entry_price = 0.0
        self.position_size = 0.0
        self.entry_time = None

        return True

    def check_exit(self, current_price):
        """Vérifie si TP ou SL atteint."""
        if not self.in_position:
            return

        tp = self._tp_price(self.entry_price, self.position_side)
        sl = self._sl_price(self.entry_price, self.position_side)

        if self.position_side == "buy":
            if current_price >= tp:
                self.close_position("TP", current_price)
            elif current_price <= sl:
                self.close_position("SL", current_price)
        else:  # sell
            if current_price <= tp:
                self.close_position("TP", current_price)
            elif current_price >= sl:
                self.close_position("SL", current_price)

    def check_entry(self, candles, current_price):
        """Vérifie les signaux BB pour ouvrir une position."""
        can, reason = self._can_trade()
        if not can:
            return

        bb = compute_bb(candles)
        if bb is None:
            logger.debug("Pas assez de candles pour BB (%d/%d)", len(candles), BB_PERIOD)
            return

        sma, upper, lower = bb

        # Signal LONG : prix touche ou passe sous la lower BB
        if current_price <= lower:
            logger.info("SIGNAL LONG — prix $%.2f <= lower BB $%.2f (SMA: $%.2f)", current_price, lower, sma)
            self.open_position("buy", current_price)

        # Signal SHORT : prix touche ou passe au-dessus de la upper BB
        elif current_price >= upper:
            logger.info("SIGNAL SHORT — prix $%.2f >= upper BB $%.2f (SMA: $%.2f)", current_price, upper, sma)
            self.open_position("sell", current_price)

    def run(self):
        """Boucle principale."""
        logger.info("=" * 60)
        logger.info("Auto Scalp BB démarré")
        logger.info("Instrument: %s | Capital: $%.2f | Leverage: x%d", INSTRUMENT, CAPITAL, LEVERAGE)
        logger.info("TP: +%.1f%% | SL: -%.1f%% | Heures: %02d-%02d UTC", TP_PCT, SL_PCT, TRADING_HOUR_START, TRADING_HOUR_END)
        logger.info("Demo: %s | Poll: %ds", DEMO, POLL_INTERVAL)
        logger.info("=" * 60)

        tg_send(
            f"🚀 *Auto Scalp BB démarré*\n"
            f"Instrument: `{INSTRUMENT}`\n"
            f"Capital: `${CAPITAL:.0f}` x{LEVERAGE}\n"
            f"TP/SL: `+{TP_PCT}%/-{SL_PCT}%`\n"
            f"Demo: `{DEMO}`"
        )

        while True:
            try:
                self._reset_daily()

                # Récupérer prix
                try:
                    price = fetch_price()
                except Exception as e:
                    logger.error("Fetch price failed: %s", e)
                    time.sleep(POLL_INTERVAL)
                    continue

                # Si en position, vérifier exit (TP/SL)
                if self.in_position:
                    self.check_exit(price)
                else:
                    # Récupérer candles et vérifier entry
                    try:
                        candles = fetch_candles_1m()
                        if candles:
                            self.check_entry(candles, price)
                    except Exception as e:
                        logger.error("Fetch candles failed: %s", e)

            except KeyboardInterrupt:
                logger.info("Arrêt demandé (Ctrl+C)")
                if self.in_position:
                    logger.warning("⚠️ POSITION OUVERTE ! Side: %s, Entry: $%.2f", self.position_side, self.entry_price)
                    tg_send(f"⚠️ *Scalp arrêté avec position ouverte !*\nSide: `{self.position_side}` @ `${self.entry_price:.2f}`")
                break
            except Exception as e:
                logger.error("Erreur inattendue: %s", e, exc_info=True)

            time.sleep(POLL_INTERVAL)

        logger.info("Auto Scalp BB arrêté — Total: %d trades, PnL: $%.2f", self.total_trades, self.total_pnl)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot = ScalpBot()
    bot.run()
