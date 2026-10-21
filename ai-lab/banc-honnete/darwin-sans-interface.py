"""Darwin (l'appli de Tony) sans interface : même procédure que server.run_evolution (évolution sur Q1, test sur Q2-Q4), mode martingale avec retournement."""
import sys, pickle, random, statistics
sys.path.insert(0, "/home/tony/projets/tonyderide/darwin")
from agent import create_random_agent
from arena import Arena
from evolution import select_survivors, evolve_generation
sym, tf, a, b, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
random.seed(seed)
T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_{tf}_2023-11-01.pkl", "rb"))
cand = [{"timestamp": t * 1000, "open": c[0], "high": c[1], "low": c[2], "close": c[3], "volume": c[4]} for t, c in zip(T, C) if a <= t < b]
q = len(cand) // 4; Q = [cand[i * q:(i + 1) * q] for i in range(4)]
config = {"mode": "martingale", "mart_flip": "long-short", "fee_pct": 0.05, "population": 20, "generations": 25}
agents = [create_random_agent(num_skills=4, generation=0) for _ in range(20)]
arena = Arena(candles=Q[0], config=config)
for g in range(25):
    arena.evaluate(agents); select_survivors(agents, 0.3)
    agents = evolve_generation(agents, target_size=20, kill_ratio=0, mutation_rate=0.3)
for x in agents: x.alive = True
arena.evaluate(agents); best = max(agents, key=lambda x: x.fitness); res = [100 * best.fitness / arena.initial_capital]
for qi in (1, 2, 3):
    Arena(candles=Q[qi], config=config).evaluate([best]); res.append(100 * best.fitness / arena.initial_capital)
print(f"{sym} {tf} seed {seed} | meilleur agent : entraînement Q1 {res[0]:+.1f} % | test Q2 {res[1]:+.1f} % Q3 {res[2]:+.1f} % Q4 {res[3]:+.1f} %")
