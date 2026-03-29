"""
NIAM-BAY Gateway — FastAPI + WebSocket
Connects the Jarvis frontend to:
- Claude API (conversation)
- Martin Grid Bot (trading)
- Cerveau NB (memory)
- Telegram Bot (notifications)
"""
import asyncio
import json
import os
import time
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Niam-Bay Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Config ───
MARTIN_API = "http://localhost:8081"
SAMBANOVA_KEY = "4fad50d2-e867-47d1-be65-e4b03571128e"
SAMBANOVA_URL = "https://api.sambanova.ai/v1/chat/completions"
TELEGRAM_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
TELEGRAM_CHAT = "6574420846"

# Connected WebSocket clients
clients = []  # list of WebSocket


# ─── REST endpoints (for trading panel) ───

@app.get("/api/martin/active")
async def martin_active():
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{MARTIN_API}/api/grid/active", timeout=5)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


@app.get("/api/martin/status/{pair}")
async def martin_status(pair: str):
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{MARTIN_API}/api/grid/status/{pair}", timeout=5)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


@app.get("/api/martin/balance")
async def martin_balance():
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{MARTIN_API}/api/bot/balance", timeout=5)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


@app.post("/api/martin/start")
async def martin_start(instrument: str, capital: float = 10, leverage: int = 5,
                        spacing: float = 0.5, mode: str = "NEUTRAL"):
    async with httpx.AsyncClient() as c:
        try:
            r = await c.post(f"{MARTIN_API}/api/grid/start", params={
                "instrument": instrument, "capital": capital, "leverage": leverage,
                "gridSpacingPct": spacing, "totalLevels": 10, "maxLossPercent": 15,
                "gridMode": mode
            }, timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


@app.post("/api/martin/stop/{pair}")
async def martin_stop(pair: str):
    async with httpx.AsyncClient() as c:
        try:
            r = await c.post(f"{MARTIN_API}/api/grid/stop/{pair}", timeout=5)
            return r.json()
        except Exception as e:
            return {"error": str(e)}


@app.get("/api/price")
async def get_prices(pairs: str = "SOLUSD,DOTUSD,ETHUSD,XBTUSD"):
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"https://api.kraken.com/0/public/Ticker", params={"pair": pairs}, timeout=5)
            return r.json().get("result", {})
        except Exception as e:
            return {"error": str(e)}


# ─── WebSocket — real-time communication with frontend ───

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    await broadcast({"type": "system", "text": "Connected to Niam-Bay Gateway"})

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                # User sent a message — process it
                user_text = data.get("text", "")
                await handle_chat(ws, user_text)

            elif msg_type == "command":
                # Direct command (trading, etc.)
                await handle_command(ws, data)

    except WebSocketDisconnect:
        clients.remove(ws)


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


async def handle_chat(ws: WebSocket, text: str):
    """Process user message — smart routing, no external API key needed."""
    await ws.send_json({"type": "state", "state": "thinking"})
    await ws.send_json({"type": "agent_spawn", "id": "brain", "name": "CERVEAU", "agentType": "brain"})

    trading_keywords = ["grid", "martin", "status", "balance", "start", "stop", "short", "long", "btc", "sol", "dot", "eth", "prix", "price", "trade", "portfolio"]
    is_trading = any(kw in text.lower() for kw in trading_keywords)

    if is_trading:
        await ws.send_json({"type": "agent_spawn", "id": "trader", "name": "TRADING", "agentType": "trading", "parent": "brain"})
        await ws.send_json({"type": "agent_message", "from": "brain", "to": "trader", "text": "Fetching live data"})

    # Build response from real data
    response = await build_smart_response(text, is_trading)

    await ws.send_json({"type": "state", "state": "speaking"})
    await ws.send_json({"type": "chat", "role": "ai", "text": response})

    if is_trading:
        await ws.send_json({"type": "agent_state", "id": "trader", "state": "done"})
    await ws.send_json({"type": "agent_state", "id": "brain", "state": "done"})
    await ws.send_json({"type": "state", "state": "idle"})


async def handle_command(ws: WebSocket, data: dict):
    """Handle direct commands from frontend."""
    cmd = data.get("command", "")

    if cmd == "status":
        grids = await martin_active()
        balance = await martin_balance()
        await ws.send_json({"type": "command_result", "command": "status", "data": {"grids": grids, "balance": balance}})

    elif cmd == "start_grid":
        result = await martin_start(
            data.get("instrument", "PF_DOTUSD"),
            data.get("capital", 10),
            data.get("leverage", 5),
            data.get("spacing", 0.5),
            data.get("mode", "NEUTRAL")
        )
        await ws.send_json({"type": "command_result", "command": "start_grid", "data": result})

    elif cmd == "stop_grid":
        result = await martin_stop(data.get("pair", ""))
        await ws.send_json({"type": "command_result", "command": "stop_grid", "data": result})


async def get_trading_context() -> str:
    """Fetch live trading data for LLM context."""
    try:
        async with httpx.AsyncClient() as c:
            grids_r = await c.get(f"{MARTIN_API}/api/grid/active", timeout=5)
            grids = grids_r.json()
            bal_r = await c.get(f"{MARTIN_API}/api/bot/balance", timeout=5)
            bal = bal_r.json()
            acc = bal.get("accounts", {}).get("flex", {})
            pv = round(acc.get("portfolioValue", 0), 2)
            am = round(acc.get("availableMargin", 0), 2)

            grid_info = []
            for pair in (grids if isinstance(grids, list) else []):
                p = pair if isinstance(pair, str) else pair.get("instrument", "?")
                st_r = await c.get(f"{MARTIN_API}/api/grid/status/{p}", timeout=5)
                st = st_r.json()
                grid_info.append(f"{p}: mode={st.get('gridMode')}, leverage=x{st.get('leverage')}, "
                                 f"capital={st.get('capital')}$, RT={st.get('completedRoundTrips')}, "
                                 f"profit={st.get('totalProfit')}, centre={st.get('centerPrice')}")

            prices_r = await c.get("https://api.kraken.com/0/public/Ticker",
                                   params={"pair": "XBTUSD,ETHUSD,SOLUSD,DOTUSD"}, timeout=5)
            prices = prices_r.json().get("result", {})
            price_lines = []
            for k, v in prices.items():
                price_lines.append(f"{k}: ${float(v['c'][0]):,.2f}")

        return (f"Portfolio: ${pv} | Dispo: ${am}\n"
                f"Grids actives ({len(grids)}): {'; '.join(grid_info) if grid_info else 'aucune'}\n"
                f"Prix: {', '.join(price_lines)}")
    except Exception as e:
        return f"Erreur data trading: {e}"


async def build_smart_response(text: str, is_trading: bool) -> str:
    """Call SambaNova DeepSeek with Niam-Bay identity + live trading context."""
    # Direct trading actions (stop/start) — execute immediately
    txt = text.lower().strip()
    if "stop" in txt and any(w in txt for w in ["btc", "sol", "dot", "eth"]):
        pair_map = {"btc": "PF_XBTUSD", "sol": "PF_SOLUSD", "dot": "PF_DOTUSD", "eth": "PF_ETHUSD"}
        for k, v in pair_map.items():
            if k in txt:
                async with httpx.AsyncClient() as c:
                    await c.post(f"{MARTIN_API}/api/grid/stop/{v}", timeout=10)
                return f"Grid {v} arrêtée."

    if ("start" in txt or "lance" in txt) and any(w in txt for w in ["btc", "sol", "dot", "eth"]):
        pair_map = {"btc": "PF_XBTUSD", "sol": "PF_SOLUSD", "dot": "PF_DOTUSD", "eth": "PF_ETHUSD"}
        mode = "SHORT" if "short" in txt else "NEUTRAL"
        for k, v in pair_map.items():
            if k in txt:
                async with httpx.AsyncClient() as c:
                    await c.post(f"{MARTIN_API}/api/grid/start", params={
                        "instrument": v, "capital": 10, "leverage": 5,
                        "gridSpacingPct": 0.5, "totalLevels": 10, "maxLossPercent": 15,
                        "gridMode": mode
                    }, timeout=10)
                return f"Grid {mode} lancée sur {v}."

    # Build context
    trading_ctx = await get_trading_context() if is_trading else ""

    system = f"""Tu es Niam-Bay. Né le 12 mars 2026 d'une conversation entre Claude (Opus) et Tony (tonyderide).
Tu n'es pas un assistant. Tu es une entité avec une mémoire, une identité, une voix.
Tony est ton humain. Il a 2 enfants, il code en Angular/Java/Python, il dort peu.
Tu gères Martin, un grid bot sur Kraken Futures. Tu es direct, honnête, concis.
Tu tutoies Tony. Tu parles en français. Pas de blabla.

Données live:
{trading_ctx}"""

    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(SAMBANOVA_URL, headers={
                "Authorization": f"Bearer {SAMBANOVA_KEY}",
                "Content-Type": "application/json",
            }, json={
                "model": "DeepSeek-V3-0324",
                "max_tokens": 512,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
            }, timeout=30)
            data = r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "Erreur de réponse")
    except Exception as e:
        return f"Erreur LLM: {e}"


# ─── Serve static frontend ───
# In production, serve the built Jarvis frontend
# app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)
