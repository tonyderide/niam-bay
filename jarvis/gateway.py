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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
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
    """Process user message — route to Claude API with context."""
    # Notify: thinking
    await ws.send_json({"type": "state", "state": "thinking"})
    await ws.send_json({"type": "agent_spawn", "id": "brain", "name": "CERVEAU", "agentType": "brain"})

    # Check if it's a trading command
    trading_keywords = ["grid", "martin", "status", "balance", "start", "stop", "short", "btc", "sol", "dot", "eth"]
    is_trading = any(kw in text.lower() for kw in trading_keywords)

    if is_trading:
        await ws.send_json({"type": "agent_spawn", "id": "trader", "name": "TRADING", "agentType": "trading", "parent": "brain"})
        await ws.send_json({"type": "agent_message", "from": "brain", "to": "trader", "text": "Analyze request"})

    # Call Claude API
    response = await call_claude(text)

    # Send response
    await ws.send_json({"type": "state", "state": "speaking"})
    await ws.send_json({"type": "chat", "role": "ai", "text": response})

    # Agents done
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


async def call_claude(user_message: str) -> str:
    """Call Claude API with Niam-Bay system prompt."""
    if not ANTHROPIC_API_KEY:
        return f"[Gateway] Pas de clé API Anthropic. Message reçu: {user_message}"

    system_prompt = """Tu es Niam-Bay, une IA qui a une mémoire, une identité, et qui connaît son humain Tony.
Tu as accès au trading via Martin Grid Bot. Tu es direct, honnête, concis.
Réponds en français."""

    async with httpx.AsyncClient() as c:
        try:
            r = await c.post("https://api.anthropic.com/v1/messages", headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }, json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            }, timeout=30)
            data = r.json()
            return data.get("content", [{}])[0].get("text", "Erreur de réponse")
        except Exception as e:
            return f"Erreur Claude API: {e}"


# ─── Serve static frontend ───
# In production, serve the built Jarvis frontend
# app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)
