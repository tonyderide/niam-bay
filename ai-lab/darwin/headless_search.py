#!/usr/bin/env python3
"""Headless Darwin evolution — sweep symbols/intervals, find most robust strategy.

Usage:  python3 headless_search.py
Output: ./darwin_results.json with ranked strategies + per-quarter PnL.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data import fetch_ohlc
from agent import create_random_agent, SKILL_POOL
from arena import Arena
from evolution import select_survivors, evolve_generation


SYMBOLS = ["PF_LINKUSD", "PF_DOTUSD", "PF_SOLUSD", "PF_XBTUSD", "PF_ETHUSD", "PF_ADAUSD"]
INTERVALS = [60, 240]  # 1h and 4h candles
POP_SIZE = 30
GENERATIONS = 25
MUTATION_RATE = 0.3
KILL_RATIO = 0.3
NUM_SKILLS_INIT = 4


def evolve_one(symbol: str, interval: int):
    """Evolve population on Q1, test on Q2/Q3/Q4. Return ranked agents + per-quarter PnL."""
    label = f"{symbol}@{interval}min"
    print(f"[{datetime.utcnow().isoformat()}] {label}: fetching...")

    candles = fetch_ohlc(symbol, interval=interval, count=8760)
    if not candles or len(candles) < 400:
        print(f"  SKIP {label}: insufficient data ({len(candles) if candles else 0})")
        return None

    q_size = len(candles) // 4
    quarters = [candles[i * q_size : (i + 1) * q_size] for i in range(4)]
    print(f"  {label}: {len(candles)} candles, {q_size}/quarter, training on Q1")

    agents = [create_random_agent(num_skills=NUM_SKILLS_INIT, generation=0) for _ in range(POP_SIZE)]
    arena = Arena(candles=quarters[0])

    t0 = time.time()
    for gen in range(GENERATIONS):
        arena.evaluate(agents)
        select_survivors(agents, KILL_RATIO)
        agents = evolve_generation(agents, target_size=POP_SIZE, kill_ratio=0, mutation_rate=MUTATION_RATE)

    # Final eval on training Q1
    for a in agents:
        a.alive = True
    arena.evaluate(agents)
    train_pnl = {a.agent_id: a.fitness for a in agents}

    # Test on Q2, Q3, Q4
    quarter_pnl = {a.agent_id: {"Q1": train_pnl.get(a.agent_id, 0)} for a in agents}
    for qi in range(1, 4):
        test_arena = Arena(candles=quarters[qi])
        test_arena.evaluate(agents)
        for a in agents:
            quarter_pnl[a.agent_id][f"Q{qi+1}"] = a.fitness

    # Score by robustness: positive quarters count (max 4) then total PnL
    results = []
    for a in agents:
        qpnl = quarter_pnl[a.agent_id]
        positive = sum(1 for v in qpnl.values() if v > 0)
        total = round(sum(qpnl.values()), 4)
        results.append({
            "agent_id": a.agent_id,
            "skills": a.skills if isinstance(a.skills, dict) else [s.name for s in a.skills],
            "quarters": {k: round(v, 4) for k, v in qpnl.items()},
            "positive_quarters": positive,
            "total_pnl": total,
        })

    results.sort(key=lambda x: (x["positive_quarters"], x["total_pnl"]), reverse=True)
    elapsed = time.time() - t0
    best = results[0]
    print(f"  {label}: done in {elapsed:.1f}s | best={best['positive_quarters']}/4Q tot={best['total_pnl']:+.2f}")
    print(f"    skills: {list(best['skills'].keys()) if isinstance(best['skills'], dict) else best['skills']}")
    print(f"    quarters: {best['quarters']}")
    return {"label": label, "symbol": symbol, "interval": interval, "candle_count": len(candles), "agents": results[:5]}


def main():
    out = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            r = evolve_one(symbol, interval)
            if r:
                out.append(r)

    # Cross-symbol top: aggregate all top-1 per (symbol,interval)
    cross = []
    for r in out:
        if r["agents"]:
            top = r["agents"][0]
            cross.append({
                "label": r["label"],
                "positive_quarters": top["positive_quarters"],
                "total_pnl": top["total_pnl"],
                "skills": top["skills"],
                "quarters": top["quarters"],
            })
    cross.sort(key=lambda x: (x["positive_quarters"], x["total_pnl"]), reverse=True)

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "config": {
            "pop_size": POP_SIZE,
            "generations": GENERATIONS,
            "mutation_rate": MUTATION_RATE,
            "kill_ratio": KILL_RATIO,
            "init_skills": NUM_SKILLS_INIT,
        },
        "cross_symbol_top10": cross[:10],
        "per_symbol_runs": out,
    }

    out_path = Path(__file__).parent / "darwin_results.json"
    out_path.write_text(json.dumps(output, indent=2))

    print("\n=== TOP STRATEGIES (cross-symbol, by robustness) ===")
    for i, c in enumerate(cross[:10], 1):
        sk = list(c['skills'].keys()) if isinstance(c['skills'], dict) else c['skills']
        print(f"{i:2d}. {c['label']:24s} {c['positive_quarters']}/4Q tot={c['total_pnl']:+.2f}  skills={sk}")
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()
