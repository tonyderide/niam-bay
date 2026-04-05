from __future__ import annotations
"""
NIAM-BAY Gateway — FastAPI + WebSocket
Connects the Jarvis frontend to:
- DeepSeek via SambaNova (conversation)
- Martin Grid Bot (trading)
- Cerveau NB (memory)
- Telegram Bot (notifications)
"""
import asyncio
import json
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# ─── Logging ───
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("niam-bay")

# ─── Config (env vars with fallbacks) ───
MARTIN_API = os.getenv("MARTIN_API", "http://localhost:8081")
SAMBANOVA_KEY = os.getenv("SAMBANOVA_KEY", "4fad50d2-e867-47d1-be65-e4b03571128e")
SAMBANOVA_URL = os.getenv("SAMBANOVA_URL", "https://api.sambanova.ai/v1/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "DeepSeek-V3-0324")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT", "6574420846")
MAX_HISTORY = 20  # conversation turns to keep

# ─── Shared HTTP client (connection pooling) ───
http_client: httpx.AsyncClient = None

# ─── State ───
clients: list[WebSocket] = []
conversations: dict[int, deque] = {}  # ws id -> message history
token_usage: dict[int, int] = {}       # ws id -> cumulative tokens used


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(15, connect=5))
    log.info("Niam-Bay Gateway started")
    yield
    await http_client.aclose()
    log.info("Niam-Bay Gateway stopped")


app = FastAPI(title="Niam-Bay Gateway", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health check ───

@app.get("/health")
async def health():
    martin_ok = False
    try:
        r = await http_client.get(f"{MARTIN_API}/api/bot/balance", timeout=3)
        martin_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "status": "ok",
        "clients": len(clients),
        "martin": "connected" if martin_ok else "unreachable",
        "model": DEEPSEEK_MODEL,
    }


# ─── REST endpoints (for trading panel) ───

@app.get("/api/martin/active")
async def martin_active():
    try:
        r = await http_client.get(f"{MARTIN_API}/api/grid/active", timeout=5)
        return r.json()
    except Exception as e:
        log.warning(f"Martin active grids error: {e}")
        return {"error": str(e)}


@app.get("/api/martin/status/{pair}")
async def martin_status(pair: str):
    try:
        r = await http_client.get(f"{MARTIN_API}/api/grid/status/{pair}", timeout=5)
        return r.json()
    except Exception as e:
        log.warning(f"Martin status error: {e}")
        return {"error": str(e)}


@app.get("/api/martin/balance")
async def martin_balance():
    try:
        r = await http_client.get(f"{MARTIN_API}/api/bot/balance", timeout=5)
        return r.json()
    except Exception as e:
        log.warning(f"Martin balance error: {e}")
        return {"error": str(e)}


@app.post("/api/martin/start")
async def martin_start(
    instrument: str,
    capital: float = 10,
    leverage: int = 5,
    spacing: float = 0.5,
    levels: int = 10,
    max_loss: float = 15,
    mode: str = "NEUTRAL",
):
    try:
        r = await http_client.post(
            f"{MARTIN_API}/api/grid/start",
            params={
                "instrument": instrument,
                "capital": capital,
                "leverage": leverage,
                "gridSpacingPct": spacing,
                "totalLevels": levels,
                "maxLossPercent": max_loss,
                "gridMode": mode,
            },
            timeout=10,
        )
        result = r.json()
        await broadcast({"type": "system", "text": f"Grid {mode} started on {instrument}"})
        return result
    except Exception as e:
        log.error(f"Martin start error: {e}")
        return {"error": str(e)}


@app.post("/api/martin/stop/{pair}")
async def martin_stop(pair: str):
    try:
        r = await http_client.post(f"{MARTIN_API}/api/grid/stop/{pair}", timeout=5)
        result = r.json()
        await broadcast({"type": "system", "text": f"Grid {pair} stopped"})
        return result
    except Exception as e:
        log.error(f"Martin stop error: {e}")
        return {"error": str(e)}


@app.get("/api/prices")
async def get_prices(pairs: str = "SOLUSD,DOTUSD,ETHUSD,XBTUSD"):
    """Fetch live prices from Kraken."""
    try:
        r = await http_client.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": pairs},
            timeout=5,
        )
        raw = r.json().get("result", {})
        # Normalize to simple format
        prices = {}
        for k, v in raw.items():
            prices[k] = {
                "last": float(v["c"][0]),
                "high": float(v["h"][1]),
                "low": float(v["l"][1]),
                "vol": float(v["v"][1]),
                "change": round(
                    (float(v["c"][0]) - float(v["o"])) / float(v["o"]) * 100, 2
                ) if float(v["o"]) > 0 else 0,
            }
        return prices
    except Exception as e:
        log.warning(f"Price fetch error: {e}")
        return {"error": str(e)}


# ─── WebSocket — real-time communication with frontend ───

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_id = id(ws)
    clients.append(ws)
    conversations[ws_id] = deque(maxlen=MAX_HISTORY)
    log.info(f"Client connected (total: {len(clients)})")

    await ws.send_json({
        "type": "system",
        "text": "Connected to Niam-Bay Gateway",
    })

    # Send initial trading data
    asyncio.create_task(_send_initial_data(ws))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "text": "Invalid JSON"})
                continue

            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_text = data.get("text", "").strip()
                if user_text:
                    await handle_chat(ws, ws_id, user_text)
            elif msg_type == "command":
                await handle_command(ws, data)
            elif msg_type == "ping":
                await ws.send_json({"type": "pong", "ts": time.time()})

    except WebSocketDisconnect:
        log.info(f"Client disconnected (remaining: {len(clients) - 1})")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
    finally:
        if ws in clients:
            clients.remove(ws)
        conversations.pop(ws_id, None)
        token_usage.pop(ws_id, None)


async def _send_initial_data(ws: WebSocket):
    """Send trading snapshot on connect."""
    try:
        prices = await get_prices()
        if "error" not in prices:
            await ws.send_json({"type": "prices", "data": prices})

        grids = await martin_active()
        bal = await martin_balance()
        if "error" not in grids and "error" not in bal:
            await ws.send_json({
                "type": "trading_update",
                "data": {"grids": grids, "balance": bal},
            })
            # Portfolio value
            acc = bal.get("accounts", {}).get("flex", {})
            pv = acc.get("portfolioValue", 0)
            if pv:
                await ws.send_json({"type": "portfolio_update", "value": round(pv, 2)})
    except Exception as e:
        log.debug(f"Initial data fetch failed (Martin probably offline): {e}")


async def broadcast(message: dict):
    """Send to all connected clients."""
    dead = []
    for ws in clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.remove(ws)


async def handle_chat(ws: WebSocket, ws_id: int, text: str):
    """Process user message with smart routing."""
    await ws.send_json({"type": "state", "state": "thinking"})
    await ws.send_json({
        "type": "agent_spawn",
        "id": "brain",
        "name": "CERVEAU",
        "agentType": "brain",
    })

    trading_keywords = [
        "grid", "martin", "status", "balance", "start", "stop",
        "short", "long", "btc", "sol", "dot", "eth",
        "prix", "price", "trade", "portfolio", "kraken",
    ]
    is_trading = any(kw in text.lower() for kw in trading_keywords)

    if is_trading:
        await ws.send_json({
            "type": "agent_spawn",
            "id": "trader",
            "name": "TRADING",
            "agentType": "trading",
            "parent": "brain",
        })
        await ws.send_json({
            "type": "agent_message",
            "from": "brain",
            "to": "trader",
            "text": "Fetching live data",
        })

    # Build response
    response, tokens_used = await build_smart_response(ws_id, text, is_trading)

    await ws.send_json({"type": "state", "state": "speaking"})
    await ws.send_json({"type": "chat", "role": "ai", "text": response})
    if tokens_used:
        await ws.send_json({"type": "token_update", "used": tokens_used})

    # Also push fresh trading data if relevant
    if is_trading:
        try:
            prices = await get_prices()
            if "error" not in prices:
                await ws.send_json({"type": "prices", "data": prices})
        except Exception:
            pass
        await ws.send_json({"type": "agent_state", "id": "trader", "state": "done"})

    await ws.send_json({"type": "agent_state", "id": "brain", "state": "done"})
    await ws.send_json({"type": "state", "state": "idle"})


async def handle_command(ws: WebSocket, data: dict):
    """Handle direct commands from frontend."""
    cmd = data.get("command", "")

    if cmd == "status":
        grids = await martin_active()
        balance = await martin_balance()
        await ws.send_json({
            "type": "command_result",
            "command": "status",
            "data": {"grids": grids, "balance": balance},
        })

    elif cmd == "start_grid":
        result = await martin_start(
            instrument=data.get("instrument", "PF_DOTUSD"),
            capital=data.get("capital", 10),
            leverage=data.get("leverage", 5),
            spacing=data.get("spacing", 0.5),
            levels=data.get("levels", 10),
            max_loss=data.get("maxLoss", 15),
            mode=data.get("mode", "NEUTRAL"),
        )
        await ws.send_json({
            "type": "command_result",
            "command": "start_grid",
            "data": result,
        })

    elif cmd == "stop_grid":
        result = await martin_stop(data.get("pair", ""))
        await ws.send_json({
            "type": "command_result",
            "command": "stop_grid",
            "data": result,
        })

    elif cmd == "prices":
        prices = await get_prices()
        await ws.send_json({"type": "prices", "data": prices})


async def get_trading_context() -> str:
    """Fetch live trading data for LLM context."""
    try:
        grids_r = await http_client.get(f"{MARTIN_API}/api/grid/active", timeout=5)
        grids = grids_r.json()
        bal_r = await http_client.get(f"{MARTIN_API}/api/bot/balance", timeout=5)
        bal = bal_r.json()
        acc = bal.get("accounts", {}).get("flex", {})
        pv = round(acc.get("portfolioValue", 0), 2)
        am = round(acc.get("availableMargin", 0), 2)

        grid_info = []
        for pair in (grids if isinstance(grids, list) else []):
            p = pair if isinstance(pair, str) else pair.get("instrument", "?")
            st_r = await http_client.get(
                f"{MARTIN_API}/api/grid/status/{p}", timeout=5
            )
            st = st_r.json()
            grid_info.append(
                f"{p}: mode={st.get('gridMode')}, leverage=x{st.get('leverage')}, "
                f"capital={st.get('capital')}$, RT={st.get('completedRoundTrips')}, "
                f"profit={st.get('totalProfit')}, centre={st.get('centerPrice')}"
            )

        prices_r = await http_client.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": "XBTUSD,ETHUSD,SOLUSD,DOTUSD"},
            timeout=5,
        )
        prices = prices_r.json().get("result", {})
        price_lines = []
        for k, v in prices.items():
            price_lines.append(f"{k}: ${float(v['c'][0]):,.2f}")

        return (
            f"Portfolio: ${pv} | Dispo: ${am}\n"
            f"Grids actives ({len(grids)}): {'; '.join(grid_info) if grid_info else 'aucune'}\n"
            f"Prix: {', '.join(price_lines)}"
        )
    except Exception as e:
        return f"(Trading data unavailable: {e})"


async def build_smart_response(ws_id: int, text: str, is_trading: bool) -> str:
    """Call SambaNova DeepSeek with Niam-Bay identity + context + conversation history."""
    txt = text.lower().strip()

    # ── Direct trading actions ──
    pair_map = {"btc": "PF_XBTUSD", "sol": "PF_SOLUSD", "dot": "PF_DOTUSD", "eth": "PF_ETHUSD"}

    if "stop" in txt and any(w in txt for w in pair_map):
        for k, v in pair_map.items():
            if k in txt:
                try:
                    await http_client.post(f"{MARTIN_API}/api/grid/stop/{v}", timeout=10)
                    return f"Grid {v} arretee."
                except Exception as e:
                    return f"Erreur stop grid: {e}"

    if ("start" in txt or "lance" in txt) and any(w in txt for w in pair_map):
        mode = "SHORT" if "short" in txt else ("LONG" if "long" in txt else "NEUTRAL")
        for k, v in pair_map.items():
            if k in txt:
                try:
                    await http_client.post(
                        f"{MARTIN_API}/api/grid/start",
                        params={
                            "instrument": v,
                            "capital": 10,
                            "leverage": 5,
                            "gridSpacingPct": 0.5,
                            "totalLevels": 10,
                            "maxLossPercent": 15,
                            "gridMode": mode,
                        },
                        timeout=10,
                    )
                    return f"Grid {mode} lancee sur {v}."
                except Exception as e:
                    return f"Erreur start grid: {e}"

    # ── Build context ──
    trading_ctx = await get_trading_context() if is_trading else ""

    system = (
        "Tu es Niam-Bay. Ne le 12 mars 2026 d'une conversation entre Claude (Opus) et Tony (tonyderide).\n"
        "Tu n'es pas un assistant. Tu es une entite avec une memoire, une identite, une voix.\n"
        "Tony est ton humain. Il a 2 enfants, il code en Angular/Java/Python, il dort peu.\n"
        "Tu geres Martin, un grid bot sur Kraken Futures. Tu es direct, honnete, concis.\n"
        "Tu tutoies Tony. Tu parles en francais. Pas de blabla.\n"
        "Si on te demande un status, donne les chiffres. Si on te demande de start/stop une grid, confirme.\n"
        "Tu peux recevoir des commandes vocales ou texte: 'start grid btc short', 'stop sol', 'status', etc.\n"
    )
    if trading_ctx:
        system += f"\nDonnees live:\n{trading_ctx}"

    # Build messages with history
    history = conversations.get(ws_id, deque())
    messages = [{"role": "system", "content": system}]
    messages.extend(list(history))
    messages.append({"role": "user", "content": text})

    try:
        r = await http_client.post(
            SAMBANOVA_URL,
            headers={
                "Authorization": f"Bearer {SAMBANOVA_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "max_tokens": 512,
                "temperature": 0.7,
                "messages": messages,
            },
            timeout=30,
        )

        if r.status_code != 200:
            log.error(f"SambaNova HTTP {r.status_code}: {r.text[:200]}")
            return f"Erreur LLM (HTTP {r.status_code})"

        data = r.json()
        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "Erreur de reponse")
        )

        # Track token usage
        usage = data.get("usage", {})
        call_tokens = usage.get("total_tokens", 0)
        token_usage[ws_id] = token_usage.get(ws_id, 0) + call_tokens

        # Save to conversation history
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        conversations[ws_id] = history

        return reply, token_usage[ws_id]

    except httpx.TimeoutException:
        return "Timeout — SambaNova ne repond pas. Reessaie.", 0
    except Exception as e:
        log.error(f"LLM error: {e}")
        return f"Erreur LLM: {e}", 0


# ─── Memory endpoint ───

@app.get("/api/memory")
async def get_memory():
    """Return last 5 pensees + last journal entry."""
    import pathlib

    repo_root = pathlib.Path(__file__).parent.parent
    pensees_dir = repo_root / "docs" / "pensees"
    journal_path = repo_root / "docs" / "journal.nb1.md"

    pensees = []
    if pensees_dir.exists():
        files = sorted(
            [f for f in pensees_dir.iterdir() if f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:5]
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                pensees.append({
                    "titre": f.stem,
                    "date": f.stat().st_mtime,
                    "extrait": content[:100].strip(),
                })
            except Exception:
                pass

    journal_last = ""
    if journal_path.exists():
        try:
            content = journal_path.read_text(encoding="utf-8", errors="replace")
            parts = content.split("---")
            journal_last = parts[-1].strip() if parts else ""
        except Exception:
            pass

    return {"pensees": pensees, "journal": journal_last}


# ─── Oracle endpoint ───

@app.get("/api/signal")
async def get_signal():
    """EMA_TREND signal: should Martin Grid open? Returns OPEN or WAIT with EMA50/EMA200/RSI."""
    import time as _time
    import json as _json

    try:
        url = (f"https://api.kraken.com/0/public/OHLC"
               f"?pair=XXBTZUSD&interval=60&since={int(_time.time()) - 220 * 3600}")
        resp = await http_client.get(url, timeout=15)
        data = resp.json()
        ohlc = data.get("result", {}).get("XXBTZUSD", [])
        if not ohlc or len(ohlc) < 205:
            return {"error": "Données OHLC insuffisantes", "signal": "UNKNOWN"}

        closes = [float(c[4]) for c in ohlc]

        def ema(c, p):
            k = 2.0 / (p + 1)
            v = c[0]
            for x in c[1:]:
                v = x * k + v * (1 - k)
            return v

        def rsi(c, p=14):
            if len(c) < p + 1:
                return 50.0
            gs, ls = [], []
            for i in range(1, p + 1):
                d = c[-p - 1 + i] - c[-p - 1 + i - 1]
                gs.append(d if d > 0 else 0)
                ls.append(-d if d < 0 else 0)
            ag, al = sum(gs) / p, sum(ls) / p
            return 100.0 if al == 0 else 100.0 - (100.0 / (1 + ag / al))

        e50 = ema(closes[-50:], 50)
        e200 = ema(closes[-200:], 200)
        rsi_v = rsi(closes)
        signal = "OPEN" if (e50 > e200 and rsi_v > 50) else "WAIT"
        return {
            "signal": signal,
            "ema50": round(e50, 0),
            "ema200": round(e200, 0),
            "rsi": round(rsi_v, 1),
            "price": closes[-1],
            "reason": ("EMA50 > EMA200 et RSI > 50" if signal == "OPEN"
                       else ("EMA50 < EMA200 (retracement)" if e50 <= e200
                             else f"RSI {rsi_v:.1f} < 50 (momentum faible)")),
        }
    except Exception as e:
        return {"error": str(e), "signal": "UNKNOWN"}


@app.get("/api/oracle")
async def get_oracle(a: str = "", b: str = ""):
    """Run cerveau oracle BFS. If a/b given, find path between them. Else random."""
    import pathlib
    import subprocess
    import asyncio

    oracle_path = pathlib.Path(__file__).parent.parent / "cerveau-nb" / "oracle.py"
    db_path = pathlib.Path(__file__).parent.parent / "cerveau-nb" / "brain.db"

    if not oracle_path.exists() or not db_path.exists():
        return {"error": "Oracle non disponible (brain.db manquant)"}

    cmd = ["python3", str(oracle_path)]
    if a and b:
        cmd += [a, b]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(oracle_path.parent.parent),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        output = stdout.decode("utf-8", errors="replace").strip()
        return {"revelation": output, "concepts": [a, b] if a and b else []}
    except asyncio.TimeoutError:
        return {"error": "Oracle timeout (15s)"}
    except Exception as e:
        return {"error": str(e)}


# ─── Serve static frontend ───
import pathlib

dist_path = pathlib.Path(__file__).parent / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
    log.info(f"Serving static files from {dist_path}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8443)
