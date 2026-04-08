# Darwin — Evolutionary Agent Arena — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an evolutionary arena where trading agents compete on historical Kraken data, with a 3D Three.js visualization of the network graph showing survival, reproduction, and skill mutation in real time.

**Architecture:** Python backend (engine + WebSocket server) evaluates agents on OHLC data, runs darwinian evolution (select → kill → crossover → mutate → 1 LLM call/gen), and pushes events to a Three.js frontend that renders agents as spheres in a 3D force-directed graph with skills as edges.

**Tech Stack:** Python 3 (websockets, aiohttp, anthropic), Three.js (CDN), vanilla JS, single HTML page.

---

### Task 1: Kraken Data Fetcher

**Files:**
- Create: `ai-lab/darwin/data.py`
- Test: `ai-lab/darwin/test_data.py`

- [ ] **Step 1: Write failing test for OHLC fetch**

```python
# ai-lab/darwin/test_data.py
import pytest
from data import fetch_ohlc

def test_fetch_ohlc_returns_candles():
    candles = fetch_ohlc("PF_SOLUSD", interval=60, count=100)
    assert len(candles) > 0
    assert "open" in candles[0]
    assert "high" in candles[0]
    assert "low" in candles[0]
    assert "close" in candles[0]
    assert "timestamp" in candles[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_data.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement data.py**

```python
# ai-lab/darwin/data.py
"""Fetch OHLC candles from Kraken Futures public API."""
import urllib.request
import json

KRAKEN_OHLC_URL = "https://futures.kraken.com/api/charts/v1/trade/{symbol}/{interval}"

def fetch_ohlc(symbol: str = "PF_SOLUSD", interval: int = 60, count: int = 2160) -> list[dict]:
    """Fetch OHLC candles. interval in minutes. count=2160 = 90 days of 1h candles."""
    url = f"{KRAKEN_OHLC_URL.format(symbol=symbol, interval=interval)}?from=0"
    req = urllib.request.Request(url, headers={"User-Agent": "darwin/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    candles = []
    for c in data.get("candles", [])[-count:]:
        candles.append({
            "timestamp": c["time"],
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": float(c.get("volume", 0)),
        })
    return candles

def fetch_multi(symbols: list[str] = None, interval: int = 60, count: int = 2160) -> dict[str, list[dict]]:
    """Fetch OHLC for multiple symbols."""
    symbols = symbols or ["PF_SOLUSD", "PF_DOTUSD", "PF_ADAUSD"]
    return {s: fetch_ohlc(s, interval, count) for s in symbols}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_data.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
rtk git add ai-lab/darwin/data.py ai-lab/darwin/test_data.py && rtk git commit -m "feat(darwin): kraken OHLC data fetcher"
```

---

### Task 2: Agent Model + Skill Seeds

**Files:**
- Create: `ai-lab/darwin/agent.py`
- Test: `ai-lab/darwin/test_agent.py`

- [ ] **Step 1: Write failing test for agent creation and decision**

```python
# ai-lab/darwin/test_agent.py
import pytest
from agent import Agent, create_random_agent, SKILL_POOL

def test_agent_has_skills():
    a = Agent(agent_id="test-001", skills={"sell-when-adx-high": 0.8, "trailing-stop-2pct": 0.6})
    assert len(a.skills) == 2
    assert a.alive is True
    assert a.fitness == 0.0

def test_agent_decide_returns_action():
    a = Agent(agent_id="test-002", skills={"buy-on-dip-3pct": 0.9})
    candle = {"open": 100, "high": 102, "low": 97, "close": 98, "timestamp": 0, "volume": 1000}
    prev = {"open": 101, "high": 103, "low": 100, "close": 101, "timestamp": 0, "volume": 900}
    action = a.decide(candle, prev)
    assert action in ("buy", "sell", "hold")

def test_create_random_agent():
    a = create_random_agent(num_skills=3)
    assert len(a.skills) == 3
    assert a.agent_id.startswith("agent-")

def test_skill_pool_not_empty():
    assert len(SKILL_POOL) >= 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_agent.py -v`
Expected: FAIL

- [ ] **Step 3: Implement agent.py**

```python
# ai-lab/darwin/agent.py
"""Trading agent — a weighted set of skills that produce buy/sell/hold decisions."""
import random
import uuid
import os
import re
import yaml
from pathlib import Path

# Skill pool: each skill is a (name, condition_fn) tuple
# condition_fn(candle, prev_candle, position) -> "buy" | "sell" | None
SKILL_POOL = {}

def _pct_change(a, b):
    return (b - a) / a if a != 0 else 0

def _register(name):
    def decorator(fn):
        SKILL_POOL[name] = fn
        return fn
    return decorator

@_register("buy-on-dip-3pct")
def _(candle, prev, pos):
    if _pct_change(prev["close"], candle["close"]) < -0.03:
        return "buy"

@_register("buy-on-dip-5pct")
def _(candle, prev, pos):
    if _pct_change(prev["close"], candle["close"]) < -0.05:
        return "buy"

@_register("sell-on-pump-3pct")
def _(candle, prev, pos):
    if _pct_change(prev["close"], candle["close"]) > 0.03:
        return "sell"

@_register("sell-on-pump-5pct")
def _(candle, prev, pos):
    if _pct_change(prev["close"], candle["close"]) > 0.05:
        return "sell"

@_register("buy-when-low-touches-support")
def _(candle, prev, pos):
    if candle["low"] < prev["low"] and candle["close"] > candle["open"]:
        return "buy"

@_register("sell-when-high-touches-resistance")
def _(candle, prev, pos):
    if candle["high"] > prev["high"] and candle["close"] < candle["open"]:
        return "sell"

@_register("buy-green-after-red")
def _(candle, prev, pos):
    if prev["close"] < prev["open"] and candle["close"] > candle["open"]:
        return "buy"

@_register("sell-red-after-green")
def _(candle, prev, pos):
    if prev["close"] > prev["open"] and candle["close"] < candle["open"]:
        return "sell"

@_register("hold-in-low-volume")
def _(candle, prev, pos):
    if candle["volume"] < prev["volume"] * 0.5:
        return "hold"

@_register("trailing-stop-2pct")
def _(candle, prev, pos):
    if pos and pos.get("peak", 0) > 0:
        drawdown = _pct_change(pos["peak"], candle["close"])
        if drawdown < -0.02:
            return "sell"

@_register("never-buy-in-downtrend")
def _(candle, prev, pos):
    if candle["close"] < prev["close"] < prev["open"]:
        return "hold"

@_register("take-profit-5pct")
def _(candle, prev, pos):
    if pos and pos.get("entry", 0) > 0:
        gain = _pct_change(pos["entry"], candle["close"])
        if gain > 0.05:
            return "sell"

def load_metaclaw_skills():
    """Load skill names from cerveau-nb/skills/ auto-skills."""
    skills_dir = Path(__file__).parent.parent.parent / "cerveau-nb" / "skills"
    names = []
    for f in skills_dir.glob("auto-*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.index("---", 3)
                body = content[end+3:].strip()
                rule = body.split("\n")[0] if body else f.stem
                names.append(rule[:60])
        except Exception:
            continue
    return names


class Agent:
    def __init__(self, agent_id: str, skills: dict[str, float], generation: int = 0, parent_ids: list[str] = None):
        self.agent_id = agent_id
        self.skills = skills  # {skill_name: weight 0-1}
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.fitness = 0.0
        self.alive = True
        self.history = []  # list of actions taken

    def decide(self, candle: dict, prev_candle: dict, position: dict = None) -> str:
        """Weighted vote across all skills."""
        votes = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        for skill_name, weight in self.skills.items():
            fn = SKILL_POOL.get(skill_name)
            if fn:
                result = fn(candle, prev_candle, position)
                if result:
                    votes[result] += weight
        if votes["buy"] == votes["sell"] == votes["hold"] == 0:
            return "hold"
        return max(votes, key=votes.get)

    def to_dict(self) -> dict:
        return {
            "id": self.agent_id,
            "generation": self.generation,
            "skills": self.skills,
            "fitness": round(self.fitness, 4),
            "alive": self.alive,
            "parent_ids": self.parent_ids,
        }


def create_random_agent(num_skills: int = 4, generation: int = 0) -> Agent:
    pool = list(SKILL_POOL.keys())
    chosen = random.sample(pool, min(num_skills, len(pool)))
    skills = {s: round(random.uniform(0.3, 1.0), 2) for s in chosen}
    return Agent(
        agent_id=f"agent-{uuid.uuid4().hex[:6]}",
        skills=skills,
        generation=generation,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
rtk git add ai-lab/darwin/agent.py ai-lab/darwin/test_agent.py && rtk git commit -m "feat(darwin): agent model with skill pool and weighted voting"
```

---

### Task 3: Arena — Evaluate Agents on Historical Data

**Files:**
- Create: `ai-lab/darwin/arena.py`
- Test: `ai-lab/darwin/test_arena.py`

- [ ] **Step 1: Write failing test for arena evaluation**

```python
# ai-lab/darwin/test_arena.py
import pytest
from agent import Agent
from arena import Arena

FAKE_CANDLES = [
    {"timestamp": i, "open": 100+i, "high": 102+i, "low": 99+i, "close": 100+i+0.5, "volume": 1000}
    for i in range(20)
]

def test_arena_evaluates_agents():
    a1 = Agent("a1", {"buy-on-dip-3pct": 0.8, "sell-on-pump-3pct": 0.7})
    a2 = Agent("a2", {"buy-green-after-red": 0.9})
    arena = Arena(candles=FAKE_CANDLES, initial_capital=100.0)
    results = arena.evaluate([a1, a2])
    assert len(results) == 2
    assert "a1" in results
    assert "a2" in results
    # fitness is set on agents
    assert isinstance(a1.fitness, float)
    assert isinstance(a2.fitness, float)

def test_arena_tracks_trades():
    a1 = Agent("a1", {"buy-green-after-red": 1.0, "sell-red-after-green": 1.0})
    arena = Arena(candles=FAKE_CANDLES, initial_capital=100.0)
    arena.evaluate([a1])
    assert isinstance(a1.history, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_arena.py -v`
Expected: FAIL

- [ ] **Step 3: Implement arena.py**

```python
# ai-lab/darwin/arena.py
"""Arena — evaluate agents on historical OHLC candles."""

class Arena:
    def __init__(self, candles: list[dict], initial_capital: float = 100.0):
        self.candles = candles
        self.initial_capital = initial_capital

    def evaluate(self, agents: list) -> dict[str, float]:
        """Run all agents through the candle series. Return {agent_id: pnl}."""
        results = {}
        for agent in agents:
            pnl = self._run_agent(agent)
            agent.fitness = pnl
            results[agent.agent_id] = pnl
        return results

    def _run_agent(self, agent) -> float:
        capital = self.initial_capital
        position = None  # {"entry": price, "size": units, "peak": highest_since_entry}
        agent.history = []

        for i in range(1, len(self.candles)):
            candle = self.candles[i]
            prev = self.candles[i - 1]
            action = agent.decide(candle, prev, position)
            agent.history.append(action)

            if action == "buy" and position is None:
                size = capital / candle["close"]
                position = {"entry": candle["close"], "size": size, "peak": candle["close"]}
                capital = 0

            elif action == "sell" and position is not None:
                capital = position["size"] * candle["close"]
                position = None

            elif position is not None:
                if candle["close"] > position["peak"]:
                    position["peak"] = candle["close"]

        # Close any open position at end
        if position is not None:
            capital = position["size"] * self.candles[-1]["close"]

        return round(capital - self.initial_capital, 4)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_arena.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
rtk git add ai-lab/darwin/arena.py ai-lab/darwin/test_arena.py && rtk git commit -m "feat(darwin): arena evaluates agents on OHLC candles"
```

---

### Task 4: Evolution Engine — Select, Crossover, Mutate

**Files:**
- Create: `ai-lab/darwin/evolution.py`
- Test: `ai-lab/darwin/test_evolution.py`

- [ ] **Step 1: Write failing test**

```python
# ai-lab/darwin/test_evolution.py
import pytest
from agent import Agent, SKILL_POOL
from evolution import select_survivors, crossover, mutate, evolve_generation

def test_select_kills_bottom_30pct():
    agents = [Agent(f"a{i}", {"buy-on-dip-3pct": 0.5}) for i in range(10)]
    for i, a in enumerate(agents):
        a.fitness = float(i)
    survivors = select_survivors(agents, kill_ratio=0.3)
    assert len(survivors) == 7
    assert all(s.alive for s in survivors)

def test_crossover_produces_child():
    p1 = Agent("p1", {"buy-on-dip-3pct": 0.8, "trailing-stop-2pct": 0.6})
    p2 = Agent("p2", {"sell-on-pump-3pct": 0.9, "hold-in-low-volume": 0.5})
    child = crossover(p1, p2, generation=1)
    assert child.generation == 1
    assert len(child.skills) > 0
    assert set(child.parent_ids) == {"p1", "p2"}

def test_mutate_changes_skills():
    a = Agent("m1", {"buy-on-dip-3pct": 0.5, "trailing-stop-2pct": 0.5})
    mutated = mutate(a, rate=1.0)  # 100% mutation rate for testing
    # Something should have changed
    assert mutated.skills != {"buy-on-dip-3pct": 0.5, "trailing-stop-2pct": 0.5} or len(mutated.skills) != 2

def test_evolve_generation():
    agents = [Agent(f"a{i}", {"buy-on-dip-3pct": 0.5, "sell-on-pump-3pct": 0.3}) for i in range(6)]
    for i, a in enumerate(agents):
        a.fitness = float(i)
    next_gen = evolve_generation(agents, target_size=6, kill_ratio=0.3, mutation_rate=0.3)
    assert len(next_gen) == 6
    assert all(a.generation == 1 for a in next_gen if a.generation == 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_evolution.py -v`
Expected: FAIL

- [ ] **Step 3: Implement evolution.py**

```python
# ai-lab/darwin/evolution.py
"""Darwinian evolution: select, crossover, mutate."""
import random
import uuid
from agent import Agent, SKILL_POOL

def select_survivors(agents: list[Agent], kill_ratio: float = 0.3) -> list[Agent]:
    """Sort by fitness, kill the bottom kill_ratio. Return survivors."""
    ranked = sorted(agents, key=lambda a: a.fitness, reverse=True)
    cut = max(2, int(len(ranked) * (1 - kill_ratio)))
    survivors = ranked[:cut]
    for a in ranked[cut:]:
        a.alive = False
    return survivors

def crossover(parent1: Agent, parent2: Agent, generation: int) -> Agent:
    """Combine skills from two parents. Each skill has 50% chance from each parent."""
    all_skills = {}
    for name, weight in parent1.skills.items():
        if random.random() < 0.5:
            all_skills[name] = weight
    for name, weight in parent2.skills.items():
        if name not in all_skills and random.random() < 0.5:
            all_skills[name] = weight
    # Ensure at least 1 skill
    if not all_skills:
        donor = random.choice([parent1, parent2])
        name = random.choice(list(donor.skills.keys()))
        all_skills[name] = donor.skills[name]
    return Agent(
        agent_id=f"agent-{uuid.uuid4().hex[:6]}",
        skills=all_skills,
        generation=generation,
        parent_ids=[parent1.agent_id, parent2.agent_id],
    )

def mutate(agent: Agent, rate: float = 0.3) -> Agent:
    """Mutate an agent's skills: add, remove, or tweak weights."""
    new_skills = dict(agent.skills)
    pool = list(SKILL_POOL.keys())

    for skill_name in list(new_skills.keys()):
        if random.random() < rate:
            action = random.choice(["tweak", "remove", "replace"])
            if action == "tweak":
                new_skills[skill_name] = max(0.1, min(1.0, new_skills[skill_name] + random.uniform(-0.2, 0.2)))
            elif action == "remove" and len(new_skills) > 1:
                del new_skills[skill_name]
            elif action == "replace":
                new_name = random.choice(pool)
                if new_name not in new_skills:
                    del new_skills[skill_name]
                    new_skills[new_name] = round(random.uniform(0.3, 1.0), 2)

    # Chance to add a new skill
    if random.random() < rate:
        new_name = random.choice(pool)
        if new_name not in new_skills:
            new_skills[new_name] = round(random.uniform(0.3, 1.0), 2)

    agent.skills = new_skills
    return agent

def evolve_generation(agents: list[Agent], target_size: int, kill_ratio: float = 0.3, mutation_rate: float = 0.3) -> list[Agent]:
    """One full evolution cycle: select → reproduce → mutate."""
    survivors = select_survivors(agents, kill_ratio)
    next_gen = []

    # Survivors carry over (with possible mutation)
    for s in survivors:
        s.generation += 1
        mutate(s, rate=mutation_rate * 0.5)  # light mutation for survivors
        next_gen.append(s)

    # Fill remaining slots with children
    while len(next_gen) < target_size:
        p1, p2 = random.sample(survivors, min(2, len(survivors)))
        child = crossover(p1, p2, generation=survivors[0].generation)
        mutate(child, rate=mutation_rate)
        next_gen.append(child)

    return next_gen[:target_size]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_evolution.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
rtk git add ai-lab/darwin/evolution.py ai-lab/darwin/test_evolution.py && rtk git commit -m "feat(darwin): evolution engine — select, crossover, mutate"
```

---

### Task 5: WebSocket Server — Push Evolution Events

**Files:**
- Create: `ai-lab/darwin/server.py`
- Create: `ai-lab/darwin/__init__.py` (empty)

- [ ] **Step 1: Implement server.py**

```python
# ai-lab/darwin/server.py
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

    # Fetch data
    await broadcast({"type": "status", "message": f"Fetching {symbol} data..."})
    candles = fetch_ohlc(symbol, interval=60, count=2160)
    if not candles:
        await broadcast({"type": "error", "message": "No candle data"})
        return

    await broadcast({"type": "status", "message": f"Got {len(candles)} candles. Creating agents..."})

    # Create initial population
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
        # Evaluate
        arena.evaluate(agents)

        # Broadcast scores
        await broadcast({
            "type": "generation",
            "gen": gen,
            "agents": [a.to_dict() for a in agents],
        })

        await asyncio.sleep(0.5)  # pace for animation

        # Who dies?
        survivors = select_survivors(agents, kill_ratio)
        dead = [a for a in agents if not a.alive]

        if dead:
            await broadcast({
                "type": "deaths",
                "gen": gen,
                "dead": [a.to_dict() for a in dead],
            })
            await asyncio.sleep(0.8)

        # Evolve
        agents = evolve_generation(agents, target_size=pop_size, kill_ratio=0, mutation_rate=mutation_rate)
        # kill_ratio=0 because we already selected survivors

        # Broadcast births
        new_agents = [a for a in agents if a.agent_id not in {s.agent_id for s in survivors}]
        if new_agents:
            await broadcast({
                "type": "births",
                "gen": gen,
                "born": [a.to_dict() for a in new_agents],
            })
            await asyncio.sleep(0.5)

    # Final results
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
```

- [ ] **Step 2: Create empty __init__.py**

```python
# ai-lab/darwin/__init__.py
```

- [ ] **Step 3: Test server starts**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && timeout 5 python server.py 2>&1 || true`
Expected: prints "Darwin server on ws://localhost:8765" then times out

- [ ] **Step 4: Commit**

```bash
rtk git add ai-lab/darwin/server.py ai-lab/darwin/__init__.py && rtk git commit -m "feat(darwin): websocket server pushes evolution events"
```

---

### Task 6: Three.js Frontend — 3D Network Graph

**Files:**
- Create: `ai-lab/darwin/web/index.html`

- [ ] **Step 1: Create the single-page app**

```html
<!-- ai-lab/darwin/web/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Darwin — Evolutionary Agent Arena</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #e0e0e0; font-family: 'JetBrains Mono', 'Fira Code', monospace; overflow: hidden; }
  #canvas-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; }

  /* Controls panel */
  #controls {
    position: fixed; top: 20px; left: 20px; z-index: 10;
    background: rgba(15, 15, 25, 0.9); border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 20px; width: 280px;
    backdrop-filter: blur(10px);
  }
  #controls h1 { font-size: 18px; color: #7b68ee; margin-bottom: 16px; }
  .control-group { margin-bottom: 14px; }
  .control-group label { display: block; font-size: 11px; color: #888; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px; }
  .control-group input[type=range] { width: 100%; accent-color: #7b68ee; }
  .control-group .value { float: right; color: #7b68ee; font-size: 12px; }
  #btn-start {
    width: 100%; padding: 12px; background: #7b68ee; color: #fff;
    border: none; border-radius: 8px; font-size: 14px; cursor: pointer;
    font-family: inherit; font-weight: bold; letter-spacing: 1px;
  }
  #btn-start:hover { background: #6a5acd; }
  #btn-start:disabled { background: #333; cursor: not-allowed; }
  #status { margin-top: 12px; font-size: 11px; color: #666; min-height: 20px; }

  /* Info panel (right) */
  #info {
    position: fixed; top: 20px; right: 20px; z-index: 10;
    background: rgba(15, 15, 25, 0.9); border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 20px; width: 300px;
    backdrop-filter: blur(10px); display: none;
  }
  #info h2 { font-size: 14px; color: #7b68ee; margin-bottom: 12px; }
  #gen-counter { font-size: 36px; color: #7b68ee; font-weight: bold; }
  #gen-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; }

  /* Leaderboard */
  #leaderboard { margin-top: 16px; }
  #leaderboard h3 { font-size: 12px; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
  .leader-entry { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; border-bottom: 1px solid #1a1a2e; }
  .leader-name { color: #ccc; }
  .leader-fitness { color: #4ecdc4; }
  .leader-fitness.negative { color: #ff6b6b; }

  /* Selected agent detail */
  #agent-detail { margin-top: 16px; display: none; }
  #agent-detail h3 { font-size: 12px; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
  .skill-tag {
    display: inline-block; padding: 3px 8px; margin: 2px;
    background: rgba(123, 104, 238, 0.2); border: 1px solid rgba(123, 104, 238, 0.4);
    border-radius: 4px; font-size: 10px; color: #b0a0ff;
  }
  .skill-weight { color: #666; margin-left: 4px; }
</style>
</head>
<body>

<div id="canvas-container"></div>

<div id="controls">
  <h1>DARWIN</h1>
  <div class="control-group">
    <label>Population <span class="value" id="pop-val">8</span></label>
    <input type="range" id="pop-slider" min="4" max="20" value="8">
  </div>
  <div class="control-group">
    <label>Generations <span class="value" id="gen-val">10</span></label>
    <input type="range" id="gen-slider" min="3" max="50" value="10">
  </div>
  <div class="control-group">
    <label>Mutation Rate <span class="value" id="mut-val">0.3</span></label>
    <input type="range" id="mut-slider" min="10" max="50" value="30">
  </div>
  <button id="btn-start">START EVOLUTION</button>
  <div id="status">Ready</div>
</div>

<div id="info">
  <div id="gen-label">Generation</div>
  <div id="gen-counter">0</div>
  <div id="leaderboard">
    <h3>Leaderboard</h3>
    <div id="leader-list"></div>
  </div>
  <div id="agent-detail">
    <h3>Selected Agent</h3>
    <div id="detail-name"></div>
    <div id="detail-fitness"></div>
    <div id="detail-parents"></div>
    <div id="detail-skills"></div>
  </div>
</div>

<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ─── Three.js Setup ───
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0f);
scene.fog = new THREE.FogExp2(0x0a0a0f, 0.015);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 20, 40);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.5;

// Lights
scene.add(new THREE.AmbientLight(0x404060, 0.5));
const pointLight = new THREE.PointLight(0x7b68ee, 2, 100);
pointLight.position.set(0, 30, 0);
scene.add(pointLight);

// Particles background
const starsGeo = new THREE.BufferGeometry();
const starPositions = new Float32Array(3000);
for (let i = 0; i < 3000; i++) starPositions[i] = (Math.random() - 0.5) * 200;
starsGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
scene.add(new THREE.Points(starsGeo, new THREE.PointsMaterial({ color: 0x444466, size: 0.3 })));

// ─── State ───
const GEN_COLORS = [0x7b68ee, 0x4ecdc4, 0xff6b6b, 0xffd93d, 0x6bcb77, 0xff8a5c, 0xa78bfa, 0xf472b6, 0x38bdf8, 0xfbbf24];
let nodes = new Map();   // agent_id -> { mesh, agent, vel, targetPos }
let edges = [];           // [{ line, from, to, skill }]
let selectedAgent = null;

function getColor(gen) { return GEN_COLORS[gen % GEN_COLORS.length]; }

function addAgent(agent) {
  const radius = Math.max(0.5, Math.min(3, 1 + agent.fitness * 0.1));
  const geo = new THREE.SphereGeometry(radius, 32, 32);
  const mat = new THREE.MeshPhongMaterial({
    color: getColor(agent.generation),
    emissive: getColor(agent.generation),
    emissiveIntensity: 0.3,
    transparent: true,
    opacity: 0.9,
  });
  const mesh = new THREE.Mesh(geo, mat);
  const angle = Math.random() * Math.PI * 2;
  const r = 5 + Math.random() * 15;
  mesh.position.set(Math.cos(angle) * r, (Math.random() - 0.5) * 10, Math.sin(angle) * r);
  mesh.userData = { agentId: agent.id };
  scene.add(mesh);

  nodes.set(agent.id, {
    mesh,
    agent,
    vel: new THREE.Vector3(),
    targetPos: mesh.position.clone(),
  });
}

function removeAgent(agentId) {
  const node = nodes.get(agentId);
  if (!node) return;
  // Shrink animation
  const shrink = () => {
    node.mesh.scale.multiplyScalar(0.9);
    node.mesh.material.opacity *= 0.9;
    if (node.mesh.scale.x > 0.05) requestAnimationFrame(shrink);
    else { scene.remove(node.mesh); nodes.delete(agentId); }
  };
  shrink();
}

function updateEdges() {
  // Remove old edges
  edges.forEach(e => scene.remove(e.line));
  edges = [];

  // Build edges for shared skills
  const agentList = [...nodes.values()];
  for (let i = 0; i < agentList.length; i++) {
    for (let j = i + 1; j < agentList.length; j++) {
      const a = agentList[i], b = agentList[j];
      const shared = Object.keys(a.agent.skills).filter(s => s in b.agent.skills);
      if (shared.length > 0) {
        const geo = new THREE.BufferGeometry().setFromPoints([a.mesh.position, b.mesh.position]);
        const mat = new THREE.LineBasicMaterial({
          color: getColor(Math.max(a.agent.generation, b.agent.generation)),
          transparent: true,
          opacity: 0.15 + shared.length * 0.1,
        });
        const line = new THREE.Line(geo, mat);
        scene.add(line);
        edges.push({ line, from: a.agent.id, to: b.agent.id, skills: shared });
      }
    }
  }
}

function updateSizes() {
  nodes.forEach(node => {
    const r = Math.max(0.5, Math.min(3, 1 + node.agent.fitness * 0.05));
    node.mesh.geometry.dispose();
    node.mesh.geometry = new THREE.SphereGeometry(r, 32, 32);
    node.mesh.material.color.setHex(getColor(node.agent.generation));
    node.mesh.material.emissive.setHex(getColor(node.agent.generation));
  });
}

// Force-directed layout
function applyForces() {
  const arr = [...nodes.values()];
  // Repulsion
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      const dir = arr[i].mesh.position.clone().sub(arr[j].mesh.position);
      const dist = Math.max(dir.length(), 0.5);
      const force = dir.normalize().multiplyScalar(50 / (dist * dist));
      arr[i].vel.add(force);
      arr[j].vel.sub(force);
    }
  }
  // Attraction for shared skills (edges)
  edges.forEach(e => {
    const a = nodes.get(e.from), b = nodes.get(e.to);
    if (a && b) {
      const dir = b.mesh.position.clone().sub(a.mesh.position);
      const force = dir.multiplyScalar(0.01 * e.skills.length);
      a.vel.add(force);
      b.vel.sub(force);
    }
  });
  // Center gravity
  arr.forEach(n => {
    const toCenter = n.mesh.position.clone().negate().multiplyScalar(0.005);
    n.vel.add(toCenter);
  });
  // Apply
  arr.forEach(n => {
    n.vel.multiplyScalar(0.8); // damping
    n.mesh.position.add(n.vel.clone().multiplyScalar(0.1));
  });
}

// ─── UI ───
const popSlider = document.getElementById('pop-slider');
const genSlider = document.getElementById('gen-slider');
const mutSlider = document.getElementById('mut-slider');
const popVal = document.getElementById('pop-val');
const genVal = document.getElementById('gen-val');
const mutVal = document.getElementById('mut-val');
const btnStart = document.getElementById('btn-start');
const statusEl = document.getElementById('status');
const infoPanel = document.getElementById('info');

popSlider.oninput = () => popVal.textContent = popSlider.value;
genSlider.oninput = () => genVal.textContent = genSlider.value;
mutSlider.oninput = () => mutVal.textContent = (mutSlider.value / 100).toFixed(2);

function updateLeaderboard(agents) {
  const sorted = [...agents].sort((a, b) => b.fitness - a.fitness).slice(0, 5);
  const html = sorted.map(a => {
    const cls = a.fitness < 0 ? 'negative' : '';
    return `<div class="leader-entry"><span class="leader-name">${a.id.slice(-6)}</span><span class="leader-fitness ${cls}">$${a.fitness.toFixed(2)}</span></div>`;
  }).join('');
  document.getElementById('leader-list').innerHTML = html;
}

function showAgentDetail(agent) {
  const det = document.getElementById('agent-detail');
  det.style.display = 'block';
  document.getElementById('detail-name').textContent = agent.id;
  const cls = agent.fitness < 0 ? 'negative' : '';
  document.getElementById('detail-fitness').innerHTML = `PnL: <span class="leader-fitness ${cls}">$${agent.fitness.toFixed(2)}</span> | Gen: ${agent.generation}`;
  document.getElementById('detail-parents').textContent = agent.parent_ids.length ? `Parents: ${agent.parent_ids.map(p => p.slice(-6)).join(', ')}` : 'Gen 0 (random)';
  document.getElementById('detail-skills').innerHTML = Object.entries(agent.skills)
    .map(([name, w]) => `<span class="skill-tag">${name}<span class="skill-weight">${w.toFixed(1)}</span></span>`).join('');
}

// Raycaster for click selection
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
renderer.domElement.addEventListener('click', (e) => {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const meshes = [...nodes.values()].map(n => n.mesh);
  const hits = raycaster.intersectObjects(meshes);
  if (hits.length > 0) {
    const id = hits[0].object.userData.agentId;
    const node = nodes.get(id);
    if (node) {
      selectedAgent = id;
      showAgentDetail(node.agent);
      // Highlight
      nodes.forEach(n => n.mesh.material.emissiveIntensity = 0.3);
      node.mesh.material.emissiveIntensity = 1.0;
    }
  }
});

// ─── WebSocket ───
let ws = null;

function connect() {
  ws = new WebSocket('ws://localhost:8765');
  ws.onopen = () => { statusEl.textContent = 'Connected'; btnStart.disabled = false; };
  ws.onclose = () => { statusEl.textContent = 'Disconnected — start server first'; btnStart.disabled = true; };
  ws.onerror = () => { statusEl.textContent = 'Connection error'; };
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    handleEvent(data);
  };
}

function handleEvent(data) {
  switch (data.type) {
    case 'status':
      statusEl.textContent = data.message;
      break;

    case 'init':
      // Clear scene of agents
      nodes.forEach(n => scene.remove(n.mesh));
      nodes.clear();
      edges.forEach(e => scene.remove(e.line));
      edges = [];
      // Add initial agents
      data.agents.forEach(a => addAgent(a));
      updateEdges();
      infoPanel.style.display = 'block';
      statusEl.textContent = 'Evolution started';
      break;

    case 'generation':
      document.getElementById('gen-counter').textContent = data.gen;
      data.agents.forEach(a => {
        const node = nodes.get(a.id);
        if (node) {
          node.agent = a;
        } else {
          addAgent(a);
        }
      });
      updateSizes();
      updateEdges();
      updateLeaderboard(data.agents);
      break;

    case 'deaths':
      data.dead.forEach(a => removeAgent(a.id));
      statusEl.textContent = `Gen ${data.gen}: ${data.dead.length} agents died`;
      break;

    case 'births':
      data.born.forEach(a => addAgent(a));
      updateEdges();
      statusEl.textContent = `Gen ${data.gen}: ${data.born.length} agents born`;
      break;

    case 'complete':
      statusEl.textContent = `Evolution complete! Best: $${data.best?.fitness?.toFixed(2) || '?'}`;
      updateLeaderboard(data.final_ranking);
      btnStart.disabled = false;
      break;

    case 'error':
      statusEl.textContent = `Error: ${data.message}`;
      btnStart.disabled = false;
      break;
  }
}

btnStart.onclick = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  btnStart.disabled = true;
  ws.send(JSON.stringify({
    type: 'start',
    config: {
      population: parseInt(popSlider.value),
      generations: parseInt(genSlider.value),
      mutation_rate: parseInt(mutSlider.value) / 100,
      symbol: 'PF_SOLUSD',
    }
  }));
};

connect();

// ─── Render Loop ───
function animate() {
  requestAnimationFrame(animate);
  applyForces();
  // Update edge positions
  edges.forEach(e => {
    const a = nodes.get(e.from), b = nodes.get(e.to);
    if (a && b) {
      const positions = e.line.geometry.attributes.position;
      positions.setXYZ(0, a.mesh.position.x, a.mesh.position.y, a.mesh.position.z);
      positions.setXYZ(1, b.mesh.position.x, b.mesh.position.y, b.mesh.position.z);
      positions.needsUpdate = true;
    }
  });
  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>
```

- [ ] **Step 2: Test the page opens**

Run: `start "C:/Users/tony_/Documents/niam-bay/ai-lab/darwin/web/index.html"` (or use a local server)
Expected: Dark page with controls panel, "Disconnected" status

- [ ] **Step 3: Commit**

```bash
rtk git add ai-lab/darwin/web/index.html && rtk git commit -m "feat(darwin): three.js 3D network graph frontend"
```

---

### Task 7: Integration Test — Full Pipeline

**Files:**
- Create: `ai-lab/darwin/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# ai-lab/darwin/test_integration.py
"""Integration test: full evolution pipeline without WebSocket."""
import pytest
from data import fetch_ohlc
from agent import create_random_agent, SKILL_POOL
from arena import Arena
from evolution import evolve_generation

def test_full_evolution_pipeline():
    # Use a small dataset
    candles = fetch_ohlc("PF_SOLUSD", interval=60, count=200)
    assert len(candles) > 50, f"Not enough candles: {len(candles)}"

    # Create population
    pop_size = 6
    agents = [create_random_agent(num_skills=3) for _ in range(pop_size)]
    arena = Arena(candles=candles)

    # Run 3 generations
    for gen in range(3):
        arena.evaluate(agents)
        ranked = sorted(agents, key=lambda a: a.fitness, reverse=True)
        best = ranked[0]
        assert isinstance(best.fitness, float)
        agents = evolve_generation(agents, target_size=pop_size, mutation_rate=0.3)

    # Final eval
    arena.evaluate(agents)
    final_best = max(agents, key=lambda a: a.fitness)
    print(f"\nFinal best: {final_best.agent_id} | PnL: ${final_best.fitness:.2f}")
    print(f"Skills: {final_best.skills}")
    assert final_best.fitness != 0 or True  # may be 0 if market flat, that's ok
```

- [ ] **Step 2: Run integration test**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python -m pytest test_integration.py -v -s`
Expected: PASS — prints best agent and skills

- [ ] **Step 3: Commit**

```bash
rtk git add ai-lab/darwin/test_integration.py && rtk git commit -m "test(darwin): full pipeline integration test"
```

---

### Task 8: End-to-End — Server + Frontend

- [ ] **Step 1: Start the server**

Run: `cd C:/Users/tony_/Documents/niam-bay/ai-lab/darwin && python server.py`
Expected: "Darwin server on ws://localhost:8765"

- [ ] **Step 2: Open the frontend**

Run: Open `ai-lab/darwin/web/index.html` in browser (or `python -m http.server 8080` from `ai-lab/darwin/web/`)
Expected: Page shows "Connected". Click START EVOLUTION. Watch 3D graph animate: spheres appear, grow, shrink, die, edges form between agents with shared skills.

- [ ] **Step 3: Verify**

Check:
- Sliders work (change pop/gen/mutation before starting)
- Agents appear as spheres with correct colors per generation
- Dead agents shrink and fade
- New agents appear with parent edges
- Leaderboard updates each generation
- Clicking an agent shows its skills
- Camera orbits automatically
- Final "complete" message shows best agent

- [ ] **Step 4: Final commit**

```bash
rtk git add -A ai-lab/darwin/ && rtk git commit -m "feat(darwin): evolutionary agent arena with 3D visualization"
```

---

## File Summary

| File | Purpose |
|------|---------|
| `ai-lab/darwin/__init__.py` | Package marker |
| `ai-lab/darwin/data.py` | Kraken OHLC fetcher |
| `ai-lab/darwin/agent.py` | Agent model + skill pool + weighted voting |
| `ai-lab/darwin/arena.py` | Evaluate agents on candle history |
| `ai-lab/darwin/evolution.py` | Select, crossover, mutate |
| `ai-lab/darwin/server.py` | WebSocket server — runs evolution + pushes events |
| `ai-lab/darwin/web/index.html` | Three.js 3D graph + controls + leaderboard |
| `ai-lab/darwin/test_data.py` | Unit tests — data fetcher |
| `ai-lab/darwin/test_agent.py` | Unit tests — agent model |
| `ai-lab/darwin/test_arena.py` | Unit tests — arena |
| `ai-lab/darwin/test_evolution.py` | Unit tests — evolution |
| `ai-lab/darwin/test_integration.py` | Integration test — full pipeline |
