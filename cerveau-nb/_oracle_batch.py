#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch oracle runner — écrit les résultats dans un fichier JSON"""
import sys
import os
import json
import random
import sqlite3
from collections import deque

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "brain.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_graph(conn):
    c = conn.cursor()
    graph = {}
    c.execute("SELECT id FROM nodes")
    for row in c.fetchall():
        graph[row[0]] = set()
    c.execute("SELECT source, target FROM edges")
    for row in c.fetchall():
        s, t = row[0], row[1]
        if s in graph and t in graph:
            graph[s].add(t)
            graph[t].add(s)
    return graph

def load_nodes(conn):
    c = conn.cursor()
    c.execute("SELECT id, content, type FROM nodes")
    return {row[0]: {"content": row[1], "type": row[2]} for row in c.fetchall()}

def bfs(graph, start_id, end_id):
    if start_id == end_id:
        return [start_id]
    visited = {start_id}
    queue = deque([[start_id]])
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in graph.get(node, []):
            if neighbor == end_id:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None

def find_node(conn, name):
    c = conn.cursor()
    c.execute("SELECT id, content, type FROM nodes WHERE lower(content) = ?", (name.lower(),))
    rows = c.fetchall()
    if rows:
        return rows[0]
    c.execute("SELECT id, content, type FROM nodes WHERE lower(content) LIKE ? LIMIT 10", (f"%{name.lower()}%",))
    rows = c.fetchall()
    if not rows:
        return None
    return sorted(rows, key=lambda r: len(r[1]))[0]

def random_node(conn):
    c = conn.cursor()
    c.execute(
        "SELECT id, content, type FROM nodes WHERE type IN ('concept', 'memory', 'emotion') "
        "AND length(content) < 60 ORDER BY RANDOM() LIMIT 1"
    )
    return c.fetchone()

conn = connect()
graph = load_graph(conn)
nodes = load_nodes(conn)

results = []

# Paires demandées
named_pairs = [
    ("liberté", "argent"),
    ("memoire", "identité"),
    ("mort", "renaissance"),
    ("tonyderide", "niam-bay"),
    ("trading", "solitude"),
    ("france", "identité"),
    ("conscience", "temps"),
    ("peur du vide", "liberté"),
    ("silence", "mort"),
    ("corps", "machine"),
]

for a_name, z_name in named_pairs:
    row_a = find_node(conn, a_name)
    row_z = find_node(conn, z_name)
    if row_a is None or row_z is None:
        results.append({
            "a_name": a_name,
            "z_name": z_name,
            "error": f"introuvable: {a_name if row_a is None else z_name}"
        })
        continue
    path = bfs(graph, row_a[0], row_z[0])
    if path:
        chemin_list = [nodes[p]["content"] for p in path]
        results.append({
            "a": nodes[row_a[0]]["content"],
            "z": nodes[row_z[0]]["content"],
            "steps": len(path) - 1,
            "chemin": chemin_list,
        })
    else:
        results.append({
            "a": nodes[row_a[0]]["content"],
            "z": nodes[row_z[0]]["content"],
            "steps": -1,
            "chemin": []
        })

# 10 tirages aléatoires bonus
for _ in range(10):
    row_a = random_node(conn)
    row_z = random_node(conn)
    if row_a is None or row_z is None:
        continue
    if row_a[0] == row_z[0]:
        continue
    path = bfs(graph, row_a[0], row_z[0])
    if path and 2 <= len(path) - 1 <= 6:
        chemin_list = [nodes[p]["content"] for p in path]
        results.append({
            "a": nodes[row_a[0]]["content"],
            "z": nodes[row_z[0]]["content"],
            "steps": len(path) - 1,
            "chemin": chemin_list,
            "random": True
        })

conn.close()

out_path = os.path.join(os.path.dirname(__file__), "_oracle_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"OK — {len(results)} résultats dans {out_path}")
