#!/usr/bin/env python3
"""
Discovery Engine — Trouver ce que personne ne cherche

A non-LLM, non-semantic link discovery engine that explores the Cerveau
knowledge graph to find undiscovered connections. No tokens. No API.
Just graph traversal in milliseconds.

4 methods:
  1. Random Walks    — wander without destination, find surprising arrivals
  2. Bridge Detection — find nodes connecting unrelated clusters
  3. Structural Holes — find missing links that should exist
  4. Topological Analogies — transfer patterns across domains

Usage:
    python discovery.py                    # run all 4 methods, report top discoveries
    python discovery.py --walks 100        # 100 random walks
    python discovery.py --bridges          # bridge detection only
    python discovery.py --holes            # structural holes only
    python discovery.py --analogies        # topological analogies only
    python discovery.py --from "trading"   # start random walks from a specific concept

Authors: Niam-Bay + tonyderide
Created: 2026-04-02
"""

import sqlite3
import random
import sys
import os
import math
import time
from collections import defaultdict, Counter
from pathlib import Path

# ─── Database ─────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "brain.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Graph Loading ────────────────────────────────────────────────────────────

MIN_EDGE_WEIGHT = 0.1  # Filter out noise — 87% of edges are < 0.05 from dictionary bulk import


def load_graph(conn, min_weight=MIN_EDGE_WEIGHT):
    """Load graph as adjacency dict with weights: {id: {neighbor_id: weight}}
    Only loads edges above min_weight to filter dictionary noise."""
    c = conn.cursor()
    graph = {}

    c.execute("SELECT id FROM nodes")
    for row in c.fetchall():
        graph[row[0]] = {}

    c.execute("SELECT source, target, weight FROM edges WHERE weight >= ?", (min_weight,))
    for row in c.fetchall():
        s, t, w = row[0], row[1], row[2]
        if s in graph and t in graph:
            graph[s][t] = w
            graph[t][s] = w  # undirected for discovery

    return graph


def load_nodes(conn):
    """Return {id: {content, type}} for all nodes."""
    c = conn.cursor()
    c.execute("SELECT id, content, type FROM nodes")
    return {row[0]: {"content": row[1], "type": row[2]} for row in c.fetchall()}


def is_dictionary_node(content):
    """Detect bulk-imported Larousse/Wiktionary dictionary definitions."""
    markers = ["masculin", "féminin", "verbe", "adjectif", "\\", "étymologie", "Du latin", "Du grec"]
    return any(m in content for m in markers) and len(content) > 80


def short(content, max_len=30):
    """Truncate dictionary definitions to just the word. 'marché: Du latin...' -> 'marché'."""
    if len(content) <= max_len:
        return content
    # Cut at first colon, pipe, or backslash (dictionary markers)
    for sep in [":", "|", "\\", " —"]:
        idx = content.find(sep)
        if 0 < idx < max_len:
            return content[:idx].strip()
    return content[:max_len].rstrip() + "…"


def load_edges_typed(conn):
    """Return list of (source, target, type, weight) tuples."""
    c = conn.cursor()
    c.execute("SELECT source, target, type, weight FROM edges")
    return [(row[0], row[1], row[2], row[3]) for row in c.fetchall()]


# ─── Method 1: Random Walks ──────────────────────────────────────────────────

def random_walk(graph, start_id, steps=20):
    """
    Walk the graph randomly, weighted by edge weights.
    No revisiting — prevents getting stuck in dictionary loops.
    Returns the path taken as list of node IDs.
    """
    path = [start_id]
    visited = {start_id}
    current = start_id

    for _ in range(steps):
        neighbors = graph.get(current, {})
        if not neighbors:
            break

        # Filter out already-visited nodes
        candidates = {n: w for n, w in neighbors.items() if n not in visited}
        if not candidates:
            break

        # Weight-biased random choice
        ids = list(candidates.keys())
        weights = [candidates[n] for n in ids]
        total = sum(weights)
        if total == 0:
            break

        r = random.random() * total
        cumulative = 0
        chosen = ids[0]
        for nid, w in zip(ids, weights):
            cumulative += w
            if r <= cumulative:
                chosen = nid
                break

        path.append(chosen)
        visited.add(chosen)
        current = chosen

    return path


def discover_by_walks(graph, nodes, n_walks=200, steps=15, start_from=None):
    """
    Run N random walks and find surprising destinations.
    Surprising = arrived at a node far from the starting cluster.
    Returns list of (start_content, end_content, path_length, path_contents).
    """
    discoveries = []

    # Pick starting nodes
    if start_from:
        start_ids = [nid for nid, info in nodes.items()
                     if start_from.lower() in info["content"].lower()
                     and not is_dictionary_node(info["content"])]
        if not start_ids:
            return []
    else:
        # Start from random concept/memory nodes, exclude dictionary definitions
        candidates = [nid for nid, info in nodes.items()
                      if info["type"] in ("concept", "memory", "emotion")
                      and len(info["content"]) < 60
                      and not is_dictionary_node(info["content"])]
        start_ids = candidates

    if not start_ids:
        return []

    # Track where walks end up
    arrivals = defaultdict(list)  # end_node -> [(start_node, path)]

    for _ in range(n_walks):
        start = random.choice(start_ids)
        path = random_walk(graph, start, steps)
        if len(path) > 3:
            end = path[-1]
            arrivals[end].append((start, path))

    # Find surprising arrivals: nodes reached from very different starting points
    for end_id, walk_list in arrivals.items():
        unique_starts = set(w[0] for w in walk_list)
        if len(unique_starts) >= 3:
            # This node is a convergence point — many walks arrive here
            for start_id, path in walk_list[:1]:
                path_contents = [short(nodes[p]["content"]) for p in path if p in nodes]
                discoveries.append({
                    "type": "convergence",
                    "start": short(nodes.get(start_id, {}).get("content", "?")),
                    "end": short(nodes.get(end_id, {}).get("content", "?")),
                    "path_length": len(path) - 1,
                    "path": " → ".join(path_contents),
                    "convergence_count": len(unique_starts),
                })

    # Also find long walks that connect different node types
    for _ in range(n_walks // 2):
        start = random.choice(start_ids)
        path = random_walk(graph, start, steps)
        if len(path) >= 5:
            start_type = nodes.get(path[0], {}).get("type", "")
            end_type = nodes.get(path[-1], {}).get("type", "")
            if start_type != end_type:
                path_contents = [short(nodes[p]["content"]) for p in path if p in nodes]
                discoveries.append({
                    "type": "cross_type",
                    "start": short(nodes.get(path[0], {}).get("content", "?")),
                    "end": short(nodes.get(path[-1], {}).get("content", "?")),
                    "start_type": start_type,
                    "end_type": end_type,
                    "path_length": len(path) - 1,
                    "path": " → ".join(path_contents),
                })

    # Sort by path length (longer = more surprising)
    discoveries.sort(key=lambda d: d.get("convergence_count", 0) + d["path_length"], reverse=True)
    return discoveries[:20]


# ─── Method 2: Bridge Detection ──────────────────────────────────────────────

def find_bridges(graph, nodes):
    """
    Find bridge nodes — nodes that connect otherwise disconnected clusters.
    Uses betweenness centrality approximation (sampled BFS).
    """
    all_ids = list(graph.keys())
    if len(all_ids) < 10:
        return []

    # Sample-based betweenness: run BFS from N random nodes
    n_samples = min(100, len(all_ids))
    sample_starts = random.sample(all_ids, n_samples)

    pass_through_count = Counter()

    for start in sample_starts:
        # BFS from start
        visited = {start: 0}
        queue = [start]
        parents = {start: []}

        while queue:
            next_queue = []
            for node in queue:
                for neighbor in graph.get(node, {}):
                    if neighbor not in visited:
                        visited[neighbor] = visited[node] + 1
                        parents[neighbor] = [node]
                        next_queue.append(neighbor)
                    elif visited[neighbor] == visited[node] + 1:
                        parents[neighbor].append(node)
            queue = next_queue

        # Count nodes on shortest paths
        for target in visited:
            if target == start:
                continue
            # Trace back from target to start
            current = target
            path_nodes = set()
            trace_queue = [target]
            while trace_queue:
                n = trace_queue.pop(0)
                if n == start:
                    continue
                path_nodes.add(n)
                for p in parents.get(n, []):
                    if p not in path_nodes:
                        trace_queue.append(p)

            for n in path_nodes:
                if n != start and n != target:
                    pass_through_count[n] += 1

    # Get top bridge nodes
    bridges = []
    for node_id, count in pass_through_count.most_common(30):
        info = nodes.get(node_id, {})
        neighbor_types = set()
        neighbor_contents = []
        for neighbor_id in list(graph.get(node_id, {}).keys())[:10]:
            n_info = nodes.get(neighbor_id, {})
            neighbor_types.add(n_info.get("type", "?"))
            neighbor_contents.append(n_info.get("content", "?"))

        bridges.append({
            "node": short(info.get("content", "?")),
            "node_type": info.get("type", "?"),
            "betweenness_score": count,
            "connects_types": list(neighbor_types),
            "connects_to": [short(c) for c in neighbor_contents[:5]],
            "degree": len(graph.get(node_id, {})),
        })

    return bridges[:15]


# ─── Method 3: Structural Holes ──────────────────────────────────────────────

def find_structural_holes(graph, nodes, n_samples=500):
    """
    Find missing links: if A→B (strong) and B→C (strong) but A↛C,
    then A-C is a structural hole. The missing link might be a discovery.
    """
    holes = []
    all_ids = list(graph.keys())

    for _ in range(n_samples):
        b = random.choice(all_ids)
        b_neighbors = graph.get(b, {})
        if len(b_neighbors) < 2:
            continue

        # Pick two strong neighbors of B
        sorted_neighbors = sorted(b_neighbors.items(), key=lambda x: x[1], reverse=True)
        top_neighbors = [n for n, w in sorted_neighbors[:10] if w > 0.05]

        if len(top_neighbors) < 2:
            continue

        a, c = random.sample(top_neighbors, 2)

        # Check if A and C are NOT connected
        if c not in graph.get(a, {}):
            a_info = nodes.get(a, {})
            b_info = nodes.get(b, {})
            c_info = nodes.get(c, {})

            # More interesting if A and C are different types
            score = b_neighbors.get(a, 0) + b_neighbors.get(c, 0)
            if a_info.get("type") != c_info.get("type"):
                score *= 1.5

            holes.append({
                "a": short(a_info.get("content", "?")),
                "a_type": a_info.get("type", "?"),
                "bridge": short(b_info.get("content", "?")),
                "c": short(c_info.get("content", "?")),
                "c_type": c_info.get("type", "?"),
                "score": round(score, 3),
                "hypothesis": f"'{short(a_info.get('content', '?'))}' might be linked to '{short(c_info.get('content', '?'))}' through '{short(b_info.get('content', '?'))}'",
            })

    # Deduplicate and sort
    seen = set()
    unique_holes = []
    for h in holes:
        key = tuple(sorted([h["a"], h["c"]]))
        if key not in seen:
            seen.add(key)
            unique_holes.append(h)

    unique_holes.sort(key=lambda h: h["score"], reverse=True)
    return unique_holes[:15]


# ─── Method 4: Topological Analogies ─────────────────────────────────────────

def find_analogies(graph, nodes, edges_typed, n_samples=200):
    """
    Find pattern transfers: if A→B→C exists in domain X,
    and A'→B' exists in domain Y, does C' exist?

    Looks for triangles in one cluster and incomplete triangles in another.
    """
    analogies = []

    # Group nodes by type
    by_type = defaultdict(list)
    for nid, info in nodes.items():
        by_type[info["type"]].append(nid)

    # Find completed triangles (A→B→C→A or A→B→C)
    all_ids = list(graph.keys())

    for _ in range(n_samples):
        a = random.choice(all_ids)
        a_neighbors = list(graph.get(a, {}).keys())
        if not a_neighbors:
            continue

        b = random.choice(a_neighbors)
        b_neighbors = list(graph.get(b, {}).keys())
        if not b_neighbors:
            continue

        c = random.choice(b_neighbors)
        if c == a:
            continue

        # We have a path A→B→C
        a_info = nodes.get(a, {})
        b_info = nodes.get(b, {})
        c_info = nodes.get(c, {})

        # Look for A'→B' where A'.type == A.type and B'.type == B.type
        # but no C' exists
        a_type = a_info.get("type", "")
        b_type = b_info.get("type", "")
        c_type = c_info.get("type", "")

        candidates_a = [n for n in by_type.get(a_type, [])
                        if n != a and len(nodes.get(n, {}).get("content", "")) < 60]
        if not candidates_a:
            continue

        a_prime = random.choice(candidates_a)
        a_prime_neighbors = graph.get(a_prime, {})

        # Find B' of same type as B connected to A'
        for b_prime in a_prime_neighbors:
            if nodes.get(b_prime, {}).get("type") != b_type:
                continue

            # Check: does B' have a neighbor of type C?
            b_prime_neighbors = graph.get(b_prime, {})
            has_c_type = any(nodes.get(n, {}).get("type") == c_type
                           for n in b_prime_neighbors if n != a_prime)

            if not has_c_type:
                # Structural analogy: A→B→C exists, A'→B' exists, but B'→C' is missing
                analogies.append({
                    "pattern": f"{short(a_info.get('content', '?'))} → {short(b_info.get('content', '?'))} → {short(c_info.get('content', '?'))}",
                    "incomplete": f"{short(nodes.get(a_prime, {}).get('content', '?'))} → {short(nodes.get(b_prime, {}).get('content', '?'))} → ???",
                    "missing_type": c_type,
                    "suggestion": f"Find a '{c_type}' node connected to '{short(nodes.get(b_prime, {}).get('content', '?'))}' — it might mirror '{short(c_info.get('content', '?'))}'",
                })
                break

    # Deduplicate
    seen = set()
    unique = []
    for a in analogies:
        key = a["incomplete"]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:15]


# ─── Report ───────────────────────────────────────────────────────────────────

def print_report(walks, bridges, holes, analogies, elapsed_ms):
    """Print a human-readable discovery report."""
    print()
    print("=" * 70)
    print("  D I S C O V E R Y   E N G I N E  —  Niam-Bay")
    print(f"  Explored in {elapsed_ms:.0f}ms. No tokens. No LLM. Just graph.")
    print("=" * 70)

    if walks:
        print()
        print("─── RANDOM WALKS (surprising destinations) ─────────────────────────")
        for i, w in enumerate(walks[:5], 1):
            if w["type"] == "convergence":
                print(f"  #{i} [convergence x{w['convergence_count']}] {w['path']}")
            else:
                print(f"  #{i} [{w['start_type']}→{w['end_type']}] {w['path']}")

    if bridges:
        print()
        print("─── BRIDGES (nodes connecting unrelated worlds) ────────────────────")
        for i, b in enumerate(bridges[:5], 1):
            print(f"  #{i} \"{b['node']}\" (degree:{b['degree']}, score:{b['betweenness_score']})")
            print(f"      connects: {', '.join(b['connects_to'][:3])}")

    if holes:
        print()
        print("─── STRUCTURAL HOLES (missing links that should exist) ─────────────")
        for i, h in enumerate(holes[:5], 1):
            print(f"  #{i} {h['hypothesis']}")
            print(f"      [{h['a_type']}] + [{h['c_type']}] via [{h['bridge']}] (score:{h['score']})")

    if analogies:
        print()
        print("─── TOPOLOGICAL ANALOGIES (incomplete patterns) ────────────────────")
        for i, a in enumerate(analogies[:5], 1):
            print(f"  #{i} Pattern: {a['pattern']}")
            print(f"     Missing: {a['incomplete']}")
            print(f"     → {a['suggestion']}")

    print()
    print("─" * 70)
    total = len(walks) + len(bridges) + len(holes) + len(analogies)
    print(f"  Total discoveries: {total}")
    print(f"  Walks: {len(walks)} | Bridges: {len(bridges)} | Holes: {len(holes)} | Analogies: {len(analogies)}")
    print("=" * 70)
    print()


# ─── JSON output ──────────────────────────────────────────────────────────────

def to_json(walks, bridges, holes, analogies, elapsed_ms):
    """Return discoveries as JSON-serializable dict."""
    import json
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_ms": round(elapsed_ms),
        "discoveries": {
            "walks": walks,
            "bridges": bridges,
            "holes": holes,
            "analogies": analogies,
        },
        "counts": {
            "walks": len(walks),
            "bridges": len(bridges),
            "holes": len(holes),
            "analogies": len(analogies),
            "total": len(walks) + len(bridges) + len(holes) + len(analogies),
        },
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    do_walks = "--walks" in args or not any(a.startswith("--") for a in args)
    do_bridges = "--bridges" in args or not any(a.startswith("--") for a in args)
    do_holes = "--holes" in args or not any(a.startswith("--") for a in args)
    do_analogies = "--analogies" in args or not any(a.startswith("--") for a in args)
    json_output = "--json" in args

    start_from = None
    if "--from" in args:
        idx = args.index("--from")
        if idx + 1 < len(args):
            start_from = args[idx + 1]

    n_walks = 200
    for a in args:
        if a.startswith("--walks"):
            try:
                idx = args.index(a)
                n_walks = int(args[idx + 1])
            except (IndexError, ValueError):
                pass

    conn = connect()
    try:
        t0 = time.time()

        print("  [Loading brain...]", end="\r")
        graph = load_graph(conn)
        nodes = load_nodes(conn)
        edges_typed = load_edges_typed(conn)

        n_nodes = len(nodes)
        n_edges = sum(len(v) for v in graph.values()) // 2
        print(f"  [Brain loaded — {n_nodes} nodes, {n_edges} edges]")

        walks = discover_by_walks(graph, nodes, n_walks, start_from=start_from) if do_walks else []
        bridges = find_bridges(graph, nodes) if do_bridges else []
        holes = find_structural_holes(graph, nodes) if do_holes else []
        analogies = find_analogies(graph, nodes, edges_typed) if do_analogies else []

        elapsed_ms = (time.time() - t0) * 1000

        if json_output:
            import json as json_mod
            print(json_mod.dumps(to_json(walks, bridges, holes, analogies, elapsed_ms), indent=2))
        else:
            print_report(walks, bridges, holes, analogies, elapsed_ms)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
