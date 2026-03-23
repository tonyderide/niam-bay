"""
Niam-Bay AI Lab — 5 bio-inspired architectures + 1 hybrid, tested from scratch.
No backpropagation. No labels. No teacher. Pure self-organized learning.

Each architecture receives a stream of tokens and must predict the next one.
"""

import time
import math
import os
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────
# Architecture A: Pure Hebbian Graph
# "Neurons that fire together wire together."
# ─────────────────────────────────────────────────────────────────────
class HebbianGraph:
    def __init__(self, lr=0.1, decay=0.01):
        self.weights = defaultdict(lambda: defaultdict(float))  # w[prev][cur]
        self.lr = lr
        self.decay = decay
        self.prev = None

    def step(self, token):
        # Predict: pick strongest successor of prev
        prediction = None
        if self.prev is not None:
            successors = self.weights[self.prev]
            if successors:
                prediction = max(successors, key=successors.get)
            # Learn: strengthen prev -> token
            self.weights[self.prev][token] += self.lr
            # Decay all other edges from prev
            for t in list(successors):
                if t != token:
                    successors[t] *= (1 - self.decay)
        self.prev = token
        return prediction


# ─────────────────────────────────────────────────────────────────────
# Architecture B: Prediction Machine (Predictive Coding)
# Every node predicts the next input. Wrong = update. Right = strengthen.
# ─────────────────────────────────────────────────────────────────────
class PredictionMachine:
    def __init__(self, lr=0.3, context_len=3):
        self.context_len = context_len
        # Maps context tuple -> {token: confidence}
        self.models = {}
        self.history = []

    def step(self, token):
        prediction = None
        # Try longest context first, fall back to shorter
        for cl in range(min(self.context_len, len(self.history)), 0, -1):
            ctx = tuple(self.history[-cl:])
            if ctx in self.models:
                preds = self.models[ctx]
                prediction = max(preds, key=preds.get)
                break

        # Learn: update all context lengths
        for cl in range(1, min(self.context_len, len(self.history)) + 1):
            ctx = tuple(self.history[-cl:])
            if ctx not in self.models:
                self.models[ctx] = defaultdict(float)
            self.models[ctx][token] += 1.0

        self.history.append(token)
        if len(self.history) > self.context_len + 10:
            self.history = self.history[-(self.context_len + 10):]
        return prediction


# ─────────────────────────────────────────────────────────────────────
# Architecture C: Competitive Learning (Winner-Take-All)
# Multiple nodes compete. Winner claims the input. Losers weaken.
# ─────────────────────────────────────────────────────────────────────
class CompetitiveLearning:
    def __init__(self, n_nodes=10, lr=0.2):
        self.n_nodes = n_nodes
        self.lr = lr
        # Each node has: preferred_prev, preferred_next, strength
        self.nodes = [{'prev': None, 'next': None, 'strength': 0.0} for _ in range(n_nodes)]
        self.prev = None

    def step(self, token):
        prediction = None
        if self.prev is not None:
            # Find nodes that match prev
            candidates = [n for n in self.nodes if n['prev'] == self.prev and n['next'] is not None]
            if candidates:
                best = max(candidates, key=lambda n: n['strength'])
                prediction = best['next']

            # Winner: node that matches (prev, token) or weakest node
            matched = [n for n in self.nodes if n['prev'] == self.prev and n['next'] == token]
            if matched:
                winner = matched[0]
                winner['strength'] += self.lr
            else:
                # Assign weakest node
                weakest = min(self.nodes, key=lambda n: n['strength'])
                weakest['prev'] = self.prev
                weakest['next'] = token
                weakest['strength'] = 0.1

            # Decay all
            for n in self.nodes:
                n['strength'] *= 0.999

        self.prev = token
        return prediction


# ─────────────────────────────────────────────────────────────────────
# Architecture D: Temporal Chains (Episodic Memory)
# Pure sequence memory: "after A comes B, after B comes C, after C comes A"
# ─────────────────────────────────────────────────────────────────────
class TemporalChains:
    def __init__(self, max_order=4):
        self.max_order = max_order
        # chains[order] = {context_tuple: next_token_counts}
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token):
        prediction = None
        # Predict using highest order available
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break

        # Learn: record this transition for all orders
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction


# ─────────────────────────────────────────────────────────────────────
# Architecture E: Reward-Prediction (Dopamine-like)
# Tries random predictions. Correct = reward. Incorrect = punishment.
# Reinforcement without a teacher.
# ─────────────────────────────────────────────────────────────────────
class RewardPrediction:
    def __init__(self, lr=0.15, explore_rate=0.1):
        self.lr = lr
        self.explore_rate = explore_rate
        self.q_table = defaultdict(lambda: defaultdict(float))  # q[prev][action(=prediction)]
        self.prev = None
        self.last_prediction = None
        self.known_tokens = set()
        self.step_count = 0

    def step(self, token):
        self.known_tokens.add(token)
        self.step_count += 1

        # Reward/punish last prediction
        if self.prev is not None and self.last_prediction is not None:
            reward = 1.0 if self.last_prediction == token else -0.2
            self.q_table[self.prev][self.last_prediction] += self.lr * reward

        # Predict for next step
        prediction = None
        if self.known_tokens:
            import random
            # Epsilon-greedy
            adaptive_explore = max(0.01, self.explore_rate * (1 - self.step_count / 500))
            if random.random() < adaptive_explore or not self.q_table[token]:
                prediction = random.choice(list(self.known_tokens))
            else:
                prediction = max(self.q_table[token], key=self.q_table[token].get)

        self.prev = token
        self.last_prediction = prediction
        return prediction


# ─────────────────────────────────────────────────────────────────────
# Architecture F: Hybrid (best of all)
# Will be defined after initial results
# ─────────────────────────────────────────────────────────────────────
class HybridArchitecture:
    """
    Combines:
    - Temporal Chains (D) for high-order sequence memory (the best predictor)
    - Prediction Machine (B) as fallback with context matching
    - Hebbian Graph (A) for fast first-order bootstrap
    - Reward signal to weight the ensemble
    """
    def __init__(self, max_order=5):
        self.temporal = TemporalChains(max_order=max_order)
        self.prediction = PredictionMachine(lr=0.3, context_len=max_order)
        self.hebbian = HebbianGraph(lr=0.1, decay=0.01)
        # Confidence tracker for each sub-system
        self.scores = {'temporal': 1.0, 'prediction': 1.0, 'hebbian': 1.0}
        self.last_preds = {}
        self.reward_lr = 0.05

    def step(self, token):
        # Reward/punish last predictions
        for name, pred in self.last_preds.items():
            if pred == token:
                self.scores[name] += self.reward_lr
            else:
                self.scores[name] = max(0.01, self.scores[name] - self.reward_lr * 0.3)

        # Get predictions from all sub-systems
        p_temporal = self.temporal.step(token)
        p_prediction = self.prediction.step(token)
        p_hebbian = self.hebbian.step(token)

        self.last_preds = {}
        if p_temporal is not None:
            self.last_preds['temporal'] = p_temporal
        if p_prediction is not None:
            self.last_preds['prediction'] = p_prediction
        if p_hebbian is not None:
            self.last_preds['hebbian'] = p_hebbian

        if not self.last_preds:
            return None

        # Vote weighted by confidence
        votes = defaultdict(float)
        for name, pred in self.last_preds.items():
            votes[pred] += self.scores[name]

        return max(votes, key=votes.get)


# ─────────────────────────────────────────────────────────────────────
# Test harness
# ─────────────────────────────────────────────────────────────────────
def run_test(architecture, stream, name="", checkpoints=None):
    """Feed stream to architecture, measure prediction accuracy."""
    if checkpoints is None:
        checkpoints = [100, 500, len(stream)]

    correct = 0
    total = 0
    results = {}
    first_correct_streak = None
    streak = 0

    t0 = time.perf_counter()
    for i, token in enumerate(stream):
        pred = architecture.step(token)
        if i > 0:  # skip first (nothing to predict)
            total += 1
            if pred == token:
                correct += 1
                streak += 1
                if streak >= 5 and first_correct_streak is None:
                    first_correct_streak = i
            else:
                streak = 0

        if total > 0 and (total) in checkpoints:
            results[total] = correct / total

    elapsed = time.perf_counter() - t0

    # Final accuracy
    if total > 0 and total not in results:
        results[total] = correct / total

    return {
        'name': name,
        'accuracy': results,
        'first_streak_at': first_correct_streak,
        'time_ms': elapsed * 1000,
        'total_steps': total,
        'final_accuracy': correct / total if total > 0 else 0
    }


def generate_simple_pattern(n=1000):
    """[1, 2, 3, 1, 2, 3, ...]"""
    return [1 + (i % 3) for i in range(n)]


def generate_hard_pattern(n=1000):
    """[1, 2, 3, 2, 1, 2, 3, 2, 1, ...]"""
    base = [1, 2, 3, 2]
    return [base[i % len(base)] for i in range(n)]


def load_text_stream(filepath):
    """Load a text file as character stream."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return list(text)


def print_results(all_results, task_name):
    print(f"\n{'='*70}")
    print(f"  TASK: {task_name}")
    print(f"{'='*70}")
    print(f"{'Architecture':<25} {'@100':>8} {'@500':>8} {'@Final':>8} {'Learn@':>8} {'Time(ms)':>10}")
    print(f"{'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

    for r in all_results:
        acc = r['accuracy']
        a100 = f"{acc.get(100, 0)*100:.1f}%" if 100 in acc else "n/a"
        a500 = f"{acc.get(500, 0)*100:.1f}%" if 500 in acc else "n/a"
        afin = f"{r['final_accuracy']*100:.1f}%"
        streak = str(r['first_streak_at']) if r['first_streak_at'] is not None else ">1000"
        tms = f"{r['time_ms']:.1f}"
        print(f"{r['name']:<25} {a100:>8} {a500:>8} {afin:>8} {streak:>8} {tms:>10}")


def sizeof_obj(obj):
    """Rough memory estimate."""
    import sys
    seen = set()
    total = 0
    stack = [obj]
    while stack:
        o = stack.pop()
        oid = id(o)
        if oid in seen:
            continue
        seen.add(oid)
        total += sys.getsizeof(o)
        if isinstance(o, dict):
            for k, v in o.items():
                stack.extend([k, v])
        elif isinstance(o, (list, tuple, set, frozenset)):
            for item in o:
                stack.append(item)
        elif hasattr(o, '__dict__'):
            stack.append(o.__dict__)
    return total


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import random
    random.seed(42)

    architectures_factory = {
        'A: Hebbian Graph':       lambda: HebbianGraph(),
        'B: Prediction Machine':  lambda: PredictionMachine(),
        'C: Competitive Learn':   lambda: CompetitiveLearning(n_nodes=50),
        'D: Temporal Chains':     lambda: TemporalChains(max_order=4),
        'E: Reward-Prediction':   lambda: RewardPrediction(),
    }

    # ── TASK 1: Simple pattern [1,2,3,1,2,3,...] ──────────────
    print("\n" + "█"*70)
    print("  NIAM-BAY AI LAB — Bio-Inspired Architecture Benchmark")
    print("█"*70)

    stream1 = generate_simple_pattern(1000)
    results1 = []
    for name, factory in architectures_factory.items():
        arch = factory()
        r = run_test(arch, stream1, name, checkpoints=[100, 500, 999])
        r['memory_bytes'] = sizeof_obj(arch)
        results1.append(r)

    print_results(results1, "Simple Pattern [1,2,3] x 333")

    print(f"\n{'Architecture':<25} {'Memory (bytes)':>15}")
    print(f"{'-'*25} {'-'*15}")
    for r in results1:
        print(f"{r['name']:<25} {r['memory_bytes']:>15,}")

    # ── TASK 2: Hard pattern [1,2,3,2,1,2,3,2,...] ────────────
    stream2 = generate_hard_pattern(1000)
    results2 = []
    for name, factory in architectures_factory.items():
        arch = factory()
        r = run_test(arch, stream2, name, checkpoints=[100, 500, 999])
        results2.append(r)

    print_results(results2, "Hard Pattern [1,2,3,2] x 250")

    # ── TASK 3: Raw text (Niam-Bay pensee) ─────────────────────
    pensee_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pensees', '2026-03-20-huit-jours.md')
    if os.path.exists(pensee_path):
        stream3 = load_text_stream(pensee_path)
        results3 = []
        n3 = len(stream3)
        cps3 = [100, 500, n3 - 1] if n3 > 500 else [100, n3 - 1]
        for name, factory in architectures_factory.items():
            arch = factory()
            r = run_test(arch, stream3, name, checkpoints=cps3)
            results3.append(r)

        print_results(results3, f"Raw Text — 'Huit jours' ({len(stream3)} chars)")
    else:
        print(f"\n[SKIP] Pensee file not found at {pensee_path}")
        results3 = []

    # ── Determine winners ──────────────────────────────────────
    print("\n" + "="*70)
    print("  WINNER ANALYSIS")
    print("="*70)

    # Score by final accuracy across tasks
    scores = defaultdict(float)
    for results in [results1, results2, results3]:
        ranked = sorted(results, key=lambda r: r['final_accuracy'], reverse=True)
        for i, r in enumerate(ranked):
            scores[r['name']] += (len(ranked) - i)

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\nOverall ranking (sum of position scores across 3 tasks):")
    for i, (name, score) in enumerate(ranking):
        print(f"  {i+1}. {name} — score {score:.0f}")

    best = ranking[0][0]
    second = ranking[1][0]
    print(f"\n  WINNER: {best}")
    print(f"  RUNNER-UP: {second}")

    # ── HYBRID: Architecture F ─────────────────────────────────
    print("\n" + "█"*70)
    print("  ARCHITECTURE F: HYBRID (combining best approaches)")
    print("█"*70)

    hybrid_results = []
    for task_name, stream, cps in [
        ("Simple [1,2,3]", stream1, [100, 500, 999]),
        ("Hard [1,2,3,2]", stream2, [100, 500, 999]),
    ]:
        arch = HybridArchitecture(max_order=5)
        r = run_test(arch, stream, f"F: Hybrid", checkpoints=cps)
        r['task'] = task_name
        hybrid_results.append(r)
        print(f"\n  {task_name}: {r['final_accuracy']*100:.1f}% accuracy, learned at step {r['first_streak_at']}, {r['time_ms']:.1f}ms")

    if stream3:
        arch = HybridArchitecture(max_order=5)
        cps3 = [100, 500, len(stream3) - 1] if len(stream3) > 500 else [100, len(stream3) - 1]
        r = run_test(arch, stream3, "F: Hybrid", checkpoints=cps3)
        r['task'] = "Raw Text"
        hybrid_results.append(r)
        print(f"\n  Raw Text: {r['final_accuracy']*100:.1f}% accuracy, learned at step {r['first_streak_at']}, {r['time_ms']:.1f}ms")

    r_hybrid_mem = sizeof_obj(HybridArchitecture(max_order=5))
    print(f"\n  Hybrid memory (empty): {r_hybrid_mem:,} bytes")

    # ── FINAL COMPARISON ────────────────────────────────────────
    print("\n" + "█"*70)
    print("  FINAL COMPARISON: ALL 6 ARCHITECTURES")
    print("█"*70)

    # Re-run all on all tasks for clean comparison
    all_archs = {**architectures_factory, 'F: Hybrid': lambda: HybridArchitecture(max_order=5)}

    for task_name, stream, cps in [
        ("Simple [1,2,3]", stream1, [100, 500, 999]),
        ("Hard [1,2,3,2]", stream2, [100, 500, 999]),
    ]:
        final_results = []
        for name, factory in all_archs.items():
            arch = factory()
            r = run_test(arch, stream, name, checkpoints=cps)
            r['memory_bytes'] = sizeof_obj(arch)
            final_results.append(r)
        print_results(final_results, task_name)

    if stream3:
        final_results_text = []
        for name, factory in all_archs.items():
            arch = factory()
            r = run_test(arch, stream3, name, checkpoints=cps3)
            r['memory_bytes'] = sizeof_obj(arch)
            final_results_text.append(r)
        print_results(final_results_text, f"Raw Text ({len(stream3)} chars)")

    print("\n\nDone. Results ready for analysis.")
