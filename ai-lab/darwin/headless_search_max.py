#!/usr/bin/env python3
"""Darwin MAX search on cached 1min Binance data.
POP=100, GENS=100, num_skills=6 init, all 3 pairs from current Martin config.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import create_random_agent, SKILL_POOL
from arena import Arena
from evolution import select_survivors, evolve_generation


CACHE_DIR = Path(__file__).parent / "data_cache"
PAIRS = {"LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT"}

POP_SIZE = 100
GENERATIONS = 100
MUTATION_RATE = 0.25
KILL_RATIO = 0.3
NUM_SKILLS_INIT = 6


def load_cache(pair_binance):
    f = CACHE_DIR / f"binance_{pair_binance}_1min_30d.json"
    if not f.exists():
        print(f"  cache miss: {f}")
        return None
    raw = json.loads(f.read_text())
    return [
        {"timestamp": int(k[0]), "open": float(k[1]), "high": float(k[2]),
         "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])}
        for k in raw
    ]


def evolve_one(label, candles):
    if not candles or len(candles) < 800:
        print(f"  SKIP {label}: insufficient ({len(candles) if candles else 0})")
        return None

    q_size = len(candles) // 4
    quarters = [candles[i * q_size : (i + 1) * q_size] for i in range(4)]
    print(f"  {label}: {len(candles)} candles, {q_size}/quarter (~{q_size/1440:.1f} days each)")

    agents = [create_random_agent(num_skills=NUM_SKILLS_INIT, generation=0) for _ in range(POP_SIZE)]
    arena = Arena(candles=quarters[0])

    t0 = time.time()
    for gen in range(GENERATIONS):
        arena.evaluate(agents)
        select_survivors(agents, KILL_RATIO)
        agents = evolve_generation(agents, target_size=POP_SIZE, kill_ratio=0, mutation_rate=MUTATION_RATE)
        if gen % 10 == 0 or gen == GENERATIONS - 1:
            best_train = max(a.fitness for a in agents)
            print(f"    gen {gen:3d}: best train fitness = {best_train:+.3f}")

    for a in agents:
        a.alive = True
    arena.evaluate(agents)
    train_pnl = {a.agent_id: a.fitness for a in agents}

    quarter_pnl = {a.agent_id: {"Q1": train_pnl.get(a.agent_id, 0)} for a in agents}
    for qi in range(1, 4):
        test_arena = Arena(candles=quarters[qi])
        test_arena.evaluate(agents)
        for a in agents:
            quarter_pnl[a.agent_id][f"Q{qi+1}"] = a.fitness

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
            "trade_count_q4": getattr(a, "trade_count", 0),
        })
    results.sort(key=lambda x: (x["positive_quarters"], x["total_pnl"]), reverse=True)
    elapsed = time.time() - t0
    best = results[0]
    print(f"  {label}: done in {elapsed:.1f}s | best={best['positive_quarters']}/4Q tot={best['total_pnl']:+.2f}")
    print(f"    skills: {list(best['skills'].keys()) if isinstance(best['skills'], dict) else best['skills']}")
    print(f"    quarters: {best['quarters']}")
    return {"label": label, "candle_count": len(candles), "agents": results[:10]}


def main():
    print(f"Darwin MAX search on cached 1min Binance data")
    print(f"Config: POP={POP_SIZE} GENS={GENERATIONS} mut={MUTATION_RATE} kill={KILL_RATIO} init_skills={NUM_SKILLS_INIT}\n")

    out = []
    for label, pair_binance in PAIRS.items():
        print(f"[{datetime.utcnow().isoformat()}] {label} ({pair_binance})...")
        candles = load_cache(pair_binance)
        r = evolve_one(label, candles)
        if r:
            out.append(r)

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
            "pop_size": POP_SIZE, "generations": GENERATIONS, "mutation_rate": MUTATION_RATE,
            "kill_ratio": KILL_RATIO, "init_skills": NUM_SKILLS_INIT,
            "data_source": "binance_1min_30d", "pairs": list(PAIRS.keys()),
        },
        "cross_top10": cross[:10],
        "per_symbol_runs": out,
    }
    out_path = Path(__file__).parent / "darwin_max_results_with_fees.json"
    out_path.write_text(json.dumps(output, indent=2))

    print("\n=== TOP STRATEGIES (by robustness) ===")
    for i, c in enumerate(cross[:10], 1):
        sk = list(c['skills'].keys()) if isinstance(c['skills'], dict) else c['skills']
        print(f"{i:2d}. {c['label']:6} {c['positive_quarters']}/4Q tot={c['total_pnl']:+.2f}  skills={sk}")
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()
