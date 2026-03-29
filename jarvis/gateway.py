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
# No external API key needed — Gateway handles everything locally
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


async def build_smart_response(text: str, is_trading: bool) -> str:
    """Build response from live data — no API key needed."""
    txt = text.lower().strip()

    try:
        if is_trading:
            # Fetch real data
            async with httpx.AsyncClient() as c:
                grids_r = await c.get(f"{MARTIN_API}/api/grid/active", timeout=5)
                grids = grids_r.json()

                bal_r = await c.get(f"{MARTIN_API}/api/bot/balance", timeout=5)
                bal = bal_r.json()
                acc = bal.get("accounts", {}).get("flex", {})
                pv = round(acc.get("portfolioValue", 0), 2)
                am = round(acc.get("availableMargin", 0), 2)

            # Status / balance
            if any(w in txt for w in ["status", "état", "etat", "balance", "portfolio"]):
                if not grids:
                    return f"Aucune grid active. Portfolio: ${pv} | Dispo: ${am}"
                lines = []
                async with httpx.AsyncClient() as c:
                    for pair in grids:
                        p = pair if isinstance(pair, str) else pair.get("instrument", "?")
                        st_r = await c.get(f"{MARTIN_API}/api/grid/status/{p}", timeout=5)
                        st = st_r.json()
                        mode = st.get("gridMode", "?")
                        rt = st.get("completedRoundTrips", 0)
                        profit = st.get("totalProfit", 0)
                        lev = st.get("leverage", "?")
                        cap = st.get("capital", 0)
                        center = st.get("centerPrice", 0)
                        lines.append(f"{p} ({mode}) x{lev} — {cap}$ | RT: {rt} | Profit: {profit:.4f}$ | Centre: {center}")
                return f"Portfolio: ${pv} | Dispo: ${am}\n" + "\n".join(lines)

            # Price
            if any(w in txt for w in ["prix", "price"]):
                async with httpx.AsyncClient() as c:
                    r = await c.get("https://api.kraken.com/0/public/Ticker", params={"pair": "SOLUSD,DOTUSD,ETHUSD,XBTUSD"}, timeout=5)
                    data = r.json().get("result", {})
                labels = {"XXBTZUSD": "BTC", "XETHZUSD": "ETH", "XXLMZUSD": "XLM", "SOLUSD": "SOL", "DOTUSD": "DOT", "ETHUSD": "ETH", "XBTUSD": "BTC"}
                lines = []
                for k, v in data.items():
                    name = labels.get(k, k)
                    price = float(v["c"][0])
                    lines.append(f"{name}: ${price:,.2f}")
                return "\n".join(lines) if lines else "Erreur prix"

            # Stop grid
            if "stop" in txt:
                pair_map = {"btc": "PF_XBTUSD", "sol": "PF_SOLUSD", "dot": "PF_DOTUSD", "eth": "PF_ETHUSD"}
                target = None
                for k, v in pair_map.items():
                    if k in txt:
                        target = v
                        break
                if target:
                    async with httpx.AsyncClient() as c:
                        r = await c.post(f"{MARTIN_API}/api/grid/stop/{target}", timeout=10)
                    return f"Grid {target} arrêtée."
                return "Quelle grid arrêter? (btc/sol/dot/eth)"

            # Start grid
            if "start" in txt or "lance" in txt:
                pair_map = {"btc": "PF_XBTUSD", "sol": "PF_SOLUSD", "dot": "PF_DOTUSD", "eth": "PF_ETHUSD"}
                mode = "SHORT" if "short" in txt else "NEUTRAL"
                target = None
                for k, v in pair_map.items():
                    if k in txt:
                        target = v
                        break
                if target:
                    async with httpx.AsyncClient() as c:
                        r = await c.post(f"{MARTIN_API}/api/grid/start", params={
                            "instrument": target, "capital": 10, "leverage": 5,
                            "gridSpacingPct": 0.5, "totalLevels": 10, "maxLossPercent": 15,
                            "gridMode": mode
                        }, timeout=10)
                    return f"Grid {mode} lancée sur {target}."
                return "Quelle paire? (btc/sol/dot/eth)"

            # Default trading
            return f"Portfolio: ${pv} | Dispo: ${am} | Grids actives: {len(grids)}"

        # Non-trading messages
        if any(w in txt for w in ["bonjour", "salut", "hello", "hey", "yo"]):
            return "Salut Tony."
        if any(w in txt for w in ["comment", "ça va", "ca va"]):
            return "Opérationnel. Qu'est-ce que tu veux faire?"
        if any(w in txt for w in ["aide", "help"]):
            return "Commandes: status, balance, prix, start [pair], stop [pair], short [pair]"

        return f"Message reçu: {text}. Tape 'aide' pour les commandes."

    except Exception as e:
        return f"Erreur: {e}"


# ─── Serve static frontend ───
# In production, serve the built Jarvis frontend
# app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)
