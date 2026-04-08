"""WebSocket server — runs evolution and pushes events to frontend."""
import asyncio
import json
import os
import sys
from pathlib import Path

import websockets

from data import fetch_ohlc
from agent import Agent, create_random_agent, SKILL_POOL
from arena import Arena
from evolution import select_survivors, evolve_generation

PORT = int(os.environ.get("DARWIN_PORT", 8765))
clients = set()

async def broadcast(event: dict):
    msg = json.dumps(event)
    for ws in list(clients):
        try:
            await ws.send(msg)
        except websockets.ConnectionClosed:
            clients.discard(ws)

async def run_evolution(config: dict):
    """Main evolution loop."""
    pop_size = config.get("population", 8)
    generations = config.get("generations", 10)
    mutation_rate = config.get("mutation_rate", 0.3)
    kill_ratio = config.get("kill_ratio", 0.3)
    symbol = config.get("symbol", "PF_SOLUSD")

    await broadcast({"type": "status", "message": f"Fetching {symbol} data..."})
    candles = fetch_ohlc(symbol, interval=60, count=2160)
    if not candles:
        await broadcast({"type": "error", "message": "No candle data"})
        return

    await broadcast({"type": "status", "message": f"Got {len(candles)} candles. Creating agents..."})

    agents = [create_random_agent(num_skills=4, generation=0) for _ in range(pop_size)]
    arena = Arena(candles=candles)

    await broadcast({
        "type": "init",
        "agents": [a.to_dict() for a in agents],
        "skill_pool": list(SKILL_POOL.keys()),
        "candle_count": len(candles),
        "symbol": symbol,
    })

    for gen in range(generations):
        arena.evaluate(agents)

        await broadcast({
            "type": "generation",
            "gen": gen,
            "agents": [a.to_dict() for a in agents],
        })

        await asyncio.sleep(0.5)

        survivors = select_survivors(agents, kill_ratio)
        dead = [a for a in agents if not a.alive]

        if dead:
            await broadcast({
                "type": "deaths",
                "gen": gen,
                "dead": [a.to_dict() for a in dead],
            })
            await asyncio.sleep(0.8)

        agents = evolve_generation(agents, target_size=pop_size, kill_ratio=0, mutation_rate=mutation_rate)

        new_agents = [a for a in agents if a.agent_id not in {s.agent_id for s in survivors}]
        if new_agents:
            await broadcast({
                "type": "births",
                "gen": gen,
                "born": [a.to_dict() for a in new_agents],
            })
            await asyncio.sleep(0.5)

    arena.evaluate(agents)
    ranked = sorted(agents, key=lambda a: a.fitness, reverse=True)
    await broadcast({
        "type": "complete",
        "final_ranking": [a.to_dict() for a in ranked],
        "best": ranked[0].to_dict() if ranked else None,
    })

async def handler(ws):
    clients.add(ws)
    try:
        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == "start":
                asyncio.create_task(run_evolution(data.get("config", {})))
            elif data.get("type") == "ping":
                await ws.send(json.dumps({"type": "pong"}))
    except websockets.ConnectionClosed:
        pass
    finally:
        clients.discard(ws)

async def main():
    print(f"Darwin server on ws://localhost:{PORT}")
    async with websockets.serve(handler, "localhost", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
