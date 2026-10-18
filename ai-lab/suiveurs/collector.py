#!/usr/bin/env python3
"""Enregistre tous les trades BTC Hyperliquid (WebSocket public) dans ~/nb/suiveurs/trades-AAAAMMJJ.jsonl. Lecture seule. Python 3.8."""
import asyncio, json, os, time
import websockets
OUT = os.path.expanduser("~/nb/suiveurs"); os.makedirs(OUT, exist_ok=True)


async def run():
    async with websockets.connect("wss://api.hyperliquid.xyz/ws", ping_interval=20, max_size=2 ** 22) as ws:
        await ws.send(json.dumps({"method": "subscribe", "subscription": {"type": "trades", "coin": "BTC"}}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("channel") != "trades":
                continue
            f = open(os.path.join(OUT, time.strftime("trades-%Y%m%d.jsonl", time.gmtime())), "a")
            for t in m["data"]:
                f.write(json.dumps({"t": t["time"], "s": t["side"], "px": t["px"], "sz": t["sz"], "u": t["users"]}) + "\n")
            f.close()


while True:
    try:
        asyncio.get_event_loop().run_until_complete(run())
    except Exception as e:
        print(time.strftime("%F %T"), "reconnexion :", type(e).__name__, flush=True); time.sleep(5)
