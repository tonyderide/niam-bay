#!/usr/bin/env python3
"""
Martin Trade Alert Bot — Niam-Bay
Surveille les trades fermés par Martin (grid bot Kraken Futures)
et envoie des alertes Telegram quand un round-trip se complète.

Usage:
    python scripts/martin_telegram_bot.py
    python scripts/martin_telegram_bot.py --dry-run   # console only
    python scripts/martin_telegram_bot.py --interval 30  # check every 30s
    python scripts/martin_telegram_bot.py --ssh       # via SSH tunnel (remote VM)
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import requests

# ─── Config ─────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454")
CHAT_ID   = os.getenv("TELEGRAM_CHAT",  "6574420846")

# Martin API — localhost si SSH tunnel actif, sinon direct VM
MARTIN_LOCAL = "http://localhost:8081"
MARTIN_VM    = "http://141.253.108.141:8081"  # rarement accessible direct

STATE_FILE = Path(__file__).parent / ".martin_bot_state.json"

PAIR_LABELS = {
    "PF_XBTUSD": "BTC/USD",
    "PF_SOLUSD": "SOL/USD",
    "PF_DOTUSD": "DOT/USD",
    "PF_ETHUSD": "ETH/USD",
    "PF_ADAUSD": "ADA/USD",
    "PF_XRPUSD": "XRP/USD",
}

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("martin-alert")


# ─── State persistence ────────────────────────────────────────────────────────

def load_state() -> dict:
    """Charge l'état précédent depuis le fichier JSON."""
    if STATE_FILE.exists():
        try:
            with STATE_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Impossible de lire l'état: {e}")
    return {}


def save_state(state: dict):
    """Sauvegarde l'état courant."""
    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Impossible de sauvegarder l'état: {e}")


# ─── Telegram ─────────────────────────────────────────────────────────────────

def tg_send(text: str, dry_run: bool = False):
    """Envoie un message Telegram. En dry-run, affiche dans la console."""
    if dry_run:
        print(f"\n{'='*50}")
        print("TELEGRAM (dry-run):")
        print(text)
        print('='*50)
        return True

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if r.status_code == 200:
            return True
        else:
            log.error(f"Telegram error {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


# ─── Martin API ───────────────────────────────────────────────────────────────

def martin_get(path: str, martin_url: str, timeout: int = 8) -> dict | list | None:
    """Appel HTTP vers l'API Martin. Retourne None si erreur."""
    try:
        r = requests.get(f"{martin_url}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        log.warning(f"Timeout: {path}")
        return None
    except Exception as e:
        log.warning(f"Martin API error {path}: {e}")
        return None


def detect_martin_url() -> str | None:
    """Détecte automatiquement si Martin est accessible (local ou VM)."""
    for url in [MARTIN_LOCAL, MARTIN_VM]:
        result = martin_get("/api/bot/balance", url, timeout=3)
        if result is not None:
            log.info(f"Martin accessible sur {url}")
            return url
    return None


# ─── Core logic ───────────────────────────────────────────────────────────────

def get_fills_snapshot(martin_url: str) -> dict:
    """
    Récupère l'état complet des fills pour toutes les grids actives.
    Retourne: { "PF_DOTUSD": [fill1, fill2, ...], ... }
    """
    snapshot = {}

    grids = martin_get("/api/grid/active", martin_url)
    if grids is None:
        return snapshot

    if not isinstance(grids, list):
        log.warning(f"Format inattendu pour /api/grid/active: {type(grids)}")
        return snapshot

    for item in grids:
        pair = item if isinstance(item, str) else item.get("instrument", "")
        if not pair:
            continue

        status = martin_get(f"/api/grid/status/{pair}", martin_url)
        if not status:
            continue

        fills = status.get("fills", [])
        snapshot[pair] = {
            "fills": fills,
            "completedRoundTrips": status.get("completedRoundTrips", 0),
            "totalProfit": status.get("totalProfit", 0),
            "gridMode": status.get("gridMode", "NEUTRAL"),
            "leverage": status.get("leverage", 1),
            "capital": status.get("capital", 0),
        }

    return snapshot


def get_balance(martin_url: str) -> dict:
    """Récupère la balance du compte."""
    bal = martin_get("/api/bot/balance", martin_url)
    if not bal:
        return {}
    acc = bal.get("accounts", {}).get("flex", {})
    return {
        "portfolioValue": round(acc.get("portfolioValue", 0), 2),
        "availableMargin": round(acc.get("availableMargin", 0), 2),
        "unrealizedPnl": round(acc.get("unrealizedFunding", 0), 4),
    }


def find_new_fills(prev_snapshot: dict, curr_snapshot: dict) -> list[dict]:
    """
    Compare les snapshots et retourne les nouveaux fills (trades fermés).
    Un fill = un ordre exécuté. Un round-trip = 2 fills (buy + sell).
    On détecte les fills avec pnl != 0 (trades fermés rentables ou non).
    """
    new_trades = []

    for pair, curr_data in curr_snapshot.items():
        curr_fills = curr_data.get("fills", [])
        prev_data = prev_snapshot.get(pair, {})
        prev_fills = prev_data.get("fills", []) if prev_data else []

        # Identifie les fills via leur timestamp ou orderId
        prev_ids = set()
        for f in prev_fills:
            fid = f.get("orderId") or f.get("timestamp") or f.get("uid")
            if fid:
                prev_ids.add(str(fid))

        # Cherche les nouveaux fills avec un P&L (round-trips complets)
        for f in curr_fills:
            fid = f.get("orderId") or f.get("timestamp") or f.get("uid")
            fid_str = str(fid) if fid else None

            # Skip si déjà connu
            if fid_str and fid_str in prev_ids:
                continue

            pnl = f.get("pnl")
            if pnl is None:
                continue

            try:
                pnl_val = float(pnl)
            except (ValueError, TypeError):
                continue

            # Un fill avec pnl = trade fermé (round-trip)
            new_trades.append({
                "pair": pair,
                "label": PAIR_LABELS.get(pair, pair.replace("PF_", "").replace("USD", "/USD")),
                "pnl": pnl_val,
                "side": f.get("side", "?"),
                "price": f.get("price") or f.get("fillPrice"),
                "size": f.get("size") or f.get("quantity"),
                "timestamp": f.get("timestamp") or f.get("time"),
                "gridMode": curr_data.get("gridMode", "NEUTRAL"),
                "rt_total": curr_data.get("completedRoundTrips", 0),
                "total_profit": curr_data.get("totalProfit", 0),
            })

    return new_trades


def detect_rt_increase(prev_snapshot: dict, curr_snapshot: dict) -> list[dict]:
    """
    Fallback: détecte via l'augmentation de completedRoundTrips
    si les fills ne sont pas suffisamment discriminants.
    """
    events = []
    for pair, curr_data in curr_snapshot.items():
        prev_data = prev_snapshot.get(pair, {})
        if not prev_data:
            continue

        prev_rt = prev_data.get("completedRoundTrips", 0)
        curr_rt = curr_data.get("completedRoundTrips", 0)

        if curr_rt > prev_rt:
            delta = curr_rt - prev_rt
            # Estime le profit par RT
            prev_profit = float(prev_data.get("totalProfit", 0))
            curr_profit = float(curr_data.get("totalProfit", 0))
            rt_profit = round(curr_profit - prev_profit, 4)

            events.append({
                "pair": pair,
                "label": PAIR_LABELS.get(pair, pair),
                "rt_new": delta,
                "rt_total": curr_rt,
                "pnl": round(rt_profit / delta, 4) if delta > 0 else rt_profit,
                "total_profit": curr_profit,
                "gridMode": curr_data.get("gridMode", "NEUTRAL"),
            })
    return events


def format_trade_message(trade: dict, balance: dict) -> str:
    """Formate le message Telegram pour un trade fermé."""
    pnl = trade.get("pnl", 0)
    emoji = "🟢" if pnl >= 0 else "🔴"
    sign = "+" if pnl >= 0 else ""
    label = trade.get("label", "?")
    mode = trade.get("gridMode", "NEUTRAL")
    rt = trade.get("rt_total", "?")
    total_profit = trade.get("total_profit", 0)

    # Timestamp lisible
    ts = trade.get("timestamp")
    ts_str = ""
    if ts:
        try:
            if isinstance(ts, (int, float)):
                ts_ms = ts / 1000 if ts > 1e10 else ts
                dt = datetime.fromtimestamp(ts_ms)
            else:
                dt = datetime.fromisoformat(str(ts)[:19])
            ts_str = f"\n🕐 {dt.strftime('%H:%M:%S')}"
        except Exception:
            pass

    # Prix d'exécution
    price = trade.get("price")
    price_str = f" @ ${float(price):,.2f}" if price else ""

    pv = balance.get("portfolioValue", 0)
    am = balance.get("availableMargin", 0)

    lines = [
        f"{emoji} *Martin — Trade fermé*",
        f"`{sign}{pnl:.4f}$` | *{label}* | {mode}",
        f"RT #{rt}{price_str}{ts_str}",
        f"Profit total grid: `{total_profit:+.4f}$`",
    ]
    if pv:
        lines.append(f"Portfolio: `{pv:.2f}$` | Dispo: `{am:.2f}$`")

    return "\n".join(lines)


def format_rt_message(event: dict, balance: dict) -> str:
    """Formate le message pour un round-trip détecté via compteur."""
    pnl = event.get("pnl", 0)
    emoji = "🟢" if pnl >= 0 else "🔴"
    sign = "+" if pnl >= 0 else ""
    label = event.get("label", "?")
    mode = event.get("gridMode", "NEUTRAL")
    rt = event.get("rt_total", "?")
    n = event.get("rt_new", 1)
    total_profit = event.get("total_profit", 0)

    pv = balance.get("portfolioValue", 0)
    am = balance.get("availableMargin", 0)

    plural = "s" if n > 1 else ""
    lines = [
        f"{emoji} *Martin — {n} round-trip{plural} fermé{plural}*",
        f"`{sign}{pnl:.4f}$` / RT | *{label}* | {mode}",
        f"Total: RT #{rt} | Profit cumulé: `{total_profit:+.4f}$`",
    ]
    if pv:
        lines.append(f"Portfolio: `{pv:.2f}$` | Dispo: `{am:.2f}$`")

    return "\n".join(lines)


# ─── Main loop ────────────────────────────────────────────────────────────────

def run(interval: int = 60, dry_run: bool = False, martin_url: str = None):
    """Boucle principale de surveillance."""
    log.info(f"Martin Alert Bot démarré — interval={interval}s dry_run={dry_run}")

    if not martin_url:
        log.info("Détection automatique de Martin...")
        martin_url = detect_martin_url()
        if not martin_url:
            log.error("Martin inaccessible. Lance le SSH tunnel d'abord:")
            log.error("  ssh -i ~/.ssh/martin_vm.key -L 8081:localhost:8081 ubuntu@141.253.108.141 -N &")
            if not dry_run:
                sys.exit(1)
            martin_url = MARTIN_LOCAL  # dry-run: essaie quand même

    # Chargement de l'état précédent
    saved = load_state()
    prev_snapshot = saved.get("snapshot", {})
    prev_balance = saved.get("balance", {})

    log.info(f"État précédent chargé — {len(prev_snapshot)} grids connues")

    if not dry_run:
        tg_send(
            f"👁 *Niam-Bay* — Surveillance Martin démarrée\n"
            f"Intervalle: {interval}s | {datetime.now().strftime('%d/%m %H:%M')}",
            dry_run=False,
        )

    consecutive_errors = 0

    while True:
        try:
            curr_snapshot = get_fills_snapshot(martin_url)

            if not curr_snapshot:
                consecutive_errors += 1
                if consecutive_errors == 3:
                    msg = (
                        f"⚠️ *Martin offline* depuis {consecutive_errors * interval}s\n"
                        f"{datetime.now().strftime('%H:%M:%S')}"
                    )
                    log.warning("Martin semble offline")
                    tg_send(msg, dry_run=dry_run)
                elif consecutive_errors > 3:
                    log.warning(f"Toujours offline ({consecutive_errors} cycles)")
                time.sleep(interval)
                continue

            if consecutive_errors >= 3:
                log.info("Martin revenu en ligne")
                tg_send("✅ *Martin de retour en ligne*", dry_run=dry_run)

            consecutive_errors = 0

            # Balance
            balance = get_balance(martin_url)

            # Détection des nouveaux trades
            if prev_snapshot:
                # Méthode 1: via les fills individuels
                new_fills = find_new_fills(prev_snapshot, curr_snapshot)

                # Méthode 2: fallback via compteur RT (si fills sans ID unique)
                rt_events = detect_rt_increase(prev_snapshot, curr_snapshot)

                if new_fills:
                    log.info(f"{len(new_fills)} nouveaux fills détectés")
                    for trade in new_fills:
                        msg = format_trade_message(trade, balance)
                        log.info(f"Trade: {trade['label']} {trade['pnl']:+.4f}$")
                        tg_send(msg, dry_run=dry_run)
                elif rt_events:
                    # Fallback si les fills ne permettent pas la détection fine
                    log.info(f"{len(rt_events)} RT détectés via compteur")
                    for event in rt_events:
                        msg = format_rt_message(event, balance)
                        log.info(f"RT: {event['label']} {event['rt_new']} trips")
                        tg_send(msg, dry_run=dry_run)
                else:
                    # Résumé debug toutes les 10 cycles
                    total_rt = sum(
                        d.get("completedRoundTrips", 0)
                        for d in curr_snapshot.values()
                    )
                    total_fills = sum(
                        len(d.get("fills", []))
                        for d in curr_snapshot.values()
                    )
                    log.info(
                        f"Pas de nouveau trade | "
                        f"{len(curr_snapshot)} grids | "
                        f"RT total: {total_rt} | "
                        f"Fills: {total_fills}"
                    )
            else:
                log.info(f"Premier cycle — {len(curr_snapshot)} grids indexées")
                for pair, data in curr_snapshot.items():
                    label = PAIR_LABELS.get(pair, pair)
                    rt = data.get("completedRoundTrips", 0)
                    fills = len(data.get("fills", []))
                    profit = data.get("totalProfit", 0)
                    log.info(f"  {label}: RT={rt} fills={fills} profit={profit:+.4f}$")

            # Sauvegarde de l'état
            save_state({
                "snapshot": curr_snapshot,
                "balance": balance,
                "last_check": datetime.now().isoformat(),
                "martin_url": martin_url,
            })
            prev_snapshot = curr_snapshot
            prev_balance = balance

        except KeyboardInterrupt:
            log.info("Arrêt demandé.")
            tg_send("⏹ Martin Alert Bot arrêté.", dry_run=dry_run)
            break
        except Exception as e:
            log.error(f"Erreur inattendue dans la boucle: {e}", exc_info=True)
            consecutive_errors += 1

        time.sleep(interval)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Martin Alert Bot — Surveille les trades et envoie des alertes Telegram"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=60,
        help="Intervalle de vérification en secondes (défaut: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche dans la console, n'envoie pas de Telegram",
    )
    parser.add_argument(
        "--martin-url",
        type=str,
        default=None,
        help=f"URL de l'API Martin (défaut: auto-détection entre {MARTIN_LOCAL} et {MARTIN_VM})",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Envoie un message de test Telegram et quitte",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Supprime l'état sauvegardé (repart de zéro)",
    )
    args = parser.parse_args()

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            log.info(f"État supprimé: {STATE_FILE}")
        else:
            log.info("Pas d'état sauvegardé.")
        return

    if args.test:
        msg = (
            "🧪 *Martin Alert Bot — Test*\n"
            f"Token: `{BOT_TOKEN[:20]}...`\n"
            f"Chat: `{CHAT_ID}`\n"
            f"Heure: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`"
        )
        ok = tg_send(msg, dry_run=False)
        print(f"Message envoyé: {'OK' if ok else 'ERREUR'}")
        return

    run(
        interval=args.interval,
        dry_run=args.dry_run,
        martin_url=args.martin_url,
    )


if __name__ == "__main__":
    main()
