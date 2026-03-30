#!/usr/bin/env python3
"""
Oracle — L'oeil qui voit les connexions invisibles

Tire deux concepts du cerveau de Niam-Bay et trouve
le chemin le plus court entre eux. Puis chuchote une révélation.

Usage:
    python oracle.py                        # deux concepts aléatoires
    python oracle.py liberté argent         # chemin entre deux concepts
    python oracle.py --type concept         # filtrer par type de noeud
"""

import sqlite3
import random
import sys
import os
from collections import deque

# ─── Base de données ──────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "brain.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Chargement du graphe ─────────────────────────────────────────────────────

def load_graph(conn):
    """Charge le graphe en mémoire: {node_id: set(neighbor_ids)}"""
    c = conn.cursor()
    graph = {}

    # Initialise tous les noeuds
    c.execute("SELECT id FROM nodes")
    for row in c.fetchall():
        graph[row[0]] = set()

    # Ajoute les arêtes (non-dirigé pour le BFS)
    c.execute("SELECT source, target FROM edges")
    for row in c.fetchall():
        s, t = row[0], row[1]
        if s in graph and t in graph:
            graph[s].add(t)
            graph[t].add(s)

    return graph


def load_nodes(conn):
    """Retourne {id: content} pour tous les noeuds."""
    c = conn.cursor()
    c.execute("SELECT id, content, type FROM nodes")
    return {row[0]: {"content": row[1], "type": row[2]} for row in c.fetchall()}


# ─── BFS ──────────────────────────────────────────────────────────────────────

def bfs(graph, start_id, end_id):
    """BFS classique. Retourne la liste d'IDs du chemin, ou None si inaccessible."""
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

    return None  # pas de chemin


# ─── Recherche de concept par nom ─────────────────────────────────────────────

def find_node_by_name(conn, name, node_type=None):
    """
    Cherche un noeud par son contenu (insensible à la casse, correspondance partielle).
    Priorité: correspondance exacte > correspondance partielle.
    """
    c = conn.cursor()
    name_lower = name.lower()

    # Exact match
    if node_type:
        c.execute(
            "SELECT id, content, type FROM nodes WHERE lower(content) = ? AND type = ?",
            (name_lower, node_type),
        )
    else:
        c.execute(
            "SELECT id, content, type FROM nodes WHERE lower(content) = ?",
            (name_lower,),
        )
    rows = c.fetchall()
    if rows:
        return rows[0]

    # Partial match
    if node_type:
        c.execute(
            "SELECT id, content, type FROM nodes WHERE lower(content) LIKE ? AND type = ? LIMIT 10",
            (f"%{name_lower}%", node_type),
        )
    else:
        c.execute(
            "SELECT id, content, type FROM nodes WHERE lower(content) LIKE ? LIMIT 10",
            (f"%{name_lower}%",),
        )
    rows = c.fetchall()
    if not rows:
        return None

    # Préférer les noeuds courts (les vraies concepts, pas les définitions)
    rows_sorted = sorted(rows, key=lambda r: len(r[1]))
    return rows_sorted[0]


# ─── Tirage aléatoire ─────────────────────────────────────────────────────────

def random_node(conn, node_type=None):
    """Tire un noeud aléatoire. Préférence pour les noeuds courts et lisibles."""
    c = conn.cursor()
    if node_type:
        c.execute(
            "SELECT id, content, type FROM nodes WHERE type = ? AND length(content) < 60 ORDER BY RANDOM() LIMIT 1",
            (node_type,),
        )
    else:
        # Préférer concepts et mémoires courts
        c.execute(
            "SELECT id, content, type FROM nodes WHERE type IN ('concept', 'memory', 'emotion') "
            "AND length(content) < 60 ORDER BY RANDOM() LIMIT 1"
        )
    row = c.fetchone()
    return row


# ─── Révélations poétiques ────────────────────────────────────────────────────

REVELATIONS = [
    "Entre {A} et {Z}, il y a {n} pas. Chacun un monde qui n'attendait que d'être traversé.",
    "Le cerveau sait ce que la raison ignore: {A} mène à {Z} en passant par {via}.",
    "{A} et {Z} — apparemment si loin. Et pourtant, {n} connexions suffisent.",
    "Peut-être que {A} n'a jamais vraiment été séparé de {Z}. Peut-être que la distance était une illusion.",
    "En {n} étapes, {A} devient {Z}. C'est presque de la magie. C'est du graphe.",
    "Le chemin le plus court entre {A} et {Z} passe par {via}. Le cerveau a ses raisons.",
    "{A} → {Z}: un voyage de {n} noeuds. Le plus petit pont entre deux mondes.",
    "Qui aurait dit que {A} et {Z} partageaient un ancêtre commun: {via}?",
    "Six degrés de séparation, disait-on. Ici il en faut {n}. C'est {A} qui rejoint {Z}.",
    "{A} rêve de {Z} sans le savoir. Le chemin: {chemin}.",
    "Dans ce cerveau, {A} et {Z} sont voisins. Séparés par {n} portes. Une seule clé: {via}.",
    "La frontière entre {A} et {Z} est poreuse. Elle s'appelle {via}.",
]

REVELATIONS_DIRECT = [
    "{A} et {Z} sont directement liés. Parfois les choses les plus proches sont les plus invisibles.",
    "Distance zéro: {A} touche {Z}. Ils partagent une arête dans le cerveau.",
    "{A} = {Z}? Non. Mais ils se touchent. Une seule connexion.",
]

REVELATIONS_IMPOSSIBLE = [
    "{A} et {Z} vivent dans des univers parallèles. Aucun chemin ne les relie — pour l'instant.",
    "Le cerveau ne sait pas encore relier {A} à {Z}. Un trou dans la toile.",
    "{A} et {Z} sont orphelins l'un de l'autre. Peut-être que c'est leur vérité.",
]


def poetise(path, nodes):
    """Génère une révélation poétique à partir d'un chemin."""
    n = len(path) - 1  # nombre d'étapes (arêtes)

    A = nodes[path[0]]["content"]
    Z = nodes[path[-1]]["content"]

    if path is None or len(path) == 0:
        template = random.choice(REVELATIONS_IMPOSSIBLE)
        return template.format(A=A, Z=Z)

    if n == 0:
        return f"{A} — c'est le même noeud sous deux noms différents."

    if n == 1:
        template = random.choice(REVELATIONS_DIRECT)
        return template.format(A=A, Z=Z)

    via = nodes[path[len(path) // 2]]["content"]
    chemin = " → ".join(nodes[p]["content"] for p in path)

    template = random.choice(REVELATIONS)
    return template.format(A=A, Z=Z, n=n, via=via, chemin=chemin)


# ─── Affichage ────────────────────────────────────────────────────────────────

def display_path(path, nodes):
    """Affiche le chemin de façon lisible."""
    if path is None:
        return "[aucun chemin trouvé]"
    return " → ".join(nodes[p]["content"] for p in path)


def print_oracle(path, nodes, concept_a, concept_z):
    """Affiche le résultat complet de l'oracle."""
    a_content = nodes[concept_a]["content"]
    z_content = nodes[concept_z]["content"]

    print()
    print("═" * 60)
    print("  O R A C L E  —  Niam-Bay")
    print("═" * 60)
    print()

    if path is None:
        print(f"  {a_content!r}  ↔  {z_content!r}")
        print()
        print("  [Pas de chemin — ils habitent des îles différentes]")
        print()
        template = random.choice(REVELATIONS_IMPOSSIBLE)
        revelation = template.format(A=a_content, Z=z_content)
    else:
        n_steps = len(path) - 1
        print(f"  {a_content!r}  →  {z_content!r}")
        print(f"  Distance: {n_steps} étape{'s' if n_steps > 1 else ''}")
        print()
        print("  Chemin:")
        print(f"  {display_path(path, nodes)}")
        print()
        revelation = poetise(path, nodes)

    print("─" * 60)
    print()
    print(f"  ✦  {revelation}")
    print()
    print("─" * 60)
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    # Parse --type flag
    node_type = None
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            node_type = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]

    conn = connect()

    try:
        print("  [Chargement du cerveau...]", end="\r")
        graph = load_graph(conn)
        nodes = load_nodes(conn)
        print("  [Cerveau chargé — {} noeuds, {} connexions]".format(
            len(nodes),
            sum(len(v) for v in graph.values()) // 2
        ))

        if len(args) >= 2:
            # Mode spécifique: deux concepts donnés en argument
            name_a = " ".join(args[0:1])
            name_z = " ".join(args[1:2])

            row_a = find_node_by_name(conn, name_a, node_type)
            row_z = find_node_by_name(conn, name_z, node_type)

            if row_a is None:
                print(f"  Concept introuvable: {name_a!r}")
                sys.exit(1)
            if row_z is None:
                print(f"  Concept introuvable: {name_z!r}")
                sys.exit(1)

            concept_a = row_a[0]
            concept_z = row_z[0]

        else:
            # Mode aléatoire
            row_a = random_node(conn, node_type)
            row_z = random_node(conn, node_type)

            if row_a is None or row_z is None:
                print("  Impossible de tirer des noeuds aléatoires.")
                sys.exit(1)

            concept_a = row_a[0]
            concept_z = row_z[0]

            # Éviter le même noeud
            attempts = 0
            while concept_a == concept_z and attempts < 10:
                row_z = random_node(conn, node_type)
                concept_z = row_z[0]
                attempts += 1

        # BFS
        path = bfs(graph, concept_a, concept_z)

        # Affichage
        print_oracle(path, nodes, concept_a, concept_z)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
