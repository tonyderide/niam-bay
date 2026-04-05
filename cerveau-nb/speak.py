#!/usr/bin/env python3
"""
cerveau-nb/speak.py — La bouche du cerveau

Génère des phrases à partir des nœuds les plus activés du graphe.
Pas de LLM. Pas de templates. Le graphe parle.

Le principe : le cerveau a des nœuds activés (par le crawler, par une
question, par la consolidation). speak.py prend les nœuds les plus chauds
et construit des phrases en suivant les arêtes.

Patterns de phrases :
  - OBSERVATION : "X est lié à Y" (deux nœuds fortement connectés)
  - TENDANCE : "X monte" (nœud avec activation croissante + domaine)
  - ALERTE : "X et Y ensemble = attention" (co-activation inhabituelle)
  - QUESTION : "pourquoi X → Y ?" (chemin inattendu dans le graphe)
  - SOUVENIR : "la dernière fois que X, il s'est passé Y" (nœud mémoire)

Usage:
    python speak.py                    # parle à partir de l'état actuel
    python speak.py --about "trading"  # parle de trading
    python speak.py --stream           # parle en continu (1 phrase / 30s)

Authors: Niam-Bay
Created: 2026-04-05
"""

import random
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

CERVEAU_DIR = Path(__file__).resolve().parent
DB_PATH = CERVEAU_DIR / "brain.db"

sys.path.insert(0, str(CERVEAU_DIR))
from core import Brain, NodeType, EdgeType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_dictionary_node(content):
    """Filtrer les définitions Larousse qui polluent."""
    markers = ["masculin", "féminin", "verbe", "adjectif", "\\",
               "étymologie", "Du latin", "Du grec"]
    return any(m in content for m in markers) and len(content) > 80


def clean_name(content):
    """Nettoyer le contenu d'un nœud pour l'affichage."""
    if is_dictionary_node(content):
        # Garder juste le premier mot
        for sep in [":", "|", "\\", " —"]:
            idx = content.find(sep)
            if 0 < idx < 30:
                return content[:idx].strip()
        return content[:25].strip()
    return content


def load_brain():
    """Charger le cerveau."""
    return Brain.load(str(DB_PATH))


def get_top_activated(brain, n=10, exclude_dict=True):
    """Récupérer les N nœuds les plus activés."""
    nodes = []
    for nid, node in brain._nodes.items():
        if exclude_dict and is_dictionary_node(node.content):
            continue
        if node.activation > 0.01:
            nodes.append(node)
    nodes.sort(key=lambda n: n.activation, reverse=True)
    return nodes[:n]


def get_strong_neighbors(brain, node_id, n=5):
    """Récupérer les voisins les plus fortement connectés."""
    neighbors = []
    for ekey in brain._outgoing.get(node_id, []):
        edge = brain._edges.get(ekey)
        if edge and edge.weight > 0.05:
            target = brain._nodes.get(edge.target)
            if target and not is_dictionary_node(target.content):
                neighbors.append((target, edge.weight))
    neighbors.sort(key=lambda x: x[1], reverse=True)
    return neighbors[:n]


def get_recent_memories(brain, n=5):
    """Récupérer les nœuds mémoire les plus récents."""
    memories = []
    for nid, node in brain._nodes.items():
        if node.type == "memory" or node.type == NodeType.MEMORY:
            memories.append(node)
    # Trier par last_activated (les plus récents d'abord)
    memories.sort(key=lambda n: n.last_activated, reverse=True)
    return memories[:n]


# ---------------------------------------------------------------------------
# Patterns de phrases
# ---------------------------------------------------------------------------

def phrase_observation(brain, node_a, node_b, weight):
    """X est lié à Y — observation d'une connexion."""
    a = clean_name(node_a.content)
    b = clean_name(node_b.content)

    templates = [
        f"{a} et {b} sont connectés",
        f"{a} mène à {b}",
        f"quand je pense à {a}, {b} s'active",
        f"{a} → {b}",
        f"il y a un lien entre {a} et {b}",
        f"{a} touche {b}",
    ]
    return random.choice(templates)


def phrase_tendance(node, domain=None):
    """X monte — un concept qui prend de l'importance."""
    name = clean_name(node.content)
    strength = node.activation

    if strength > 0.7:
        templates = [
            f"{name} est très actif en ce moment",
            f"{name} brûle dans le graphe",
            f"tout converge vers {name}",
        ]
    elif strength > 0.4:
        templates = [
            f"{name} monte",
            f"{name} s'active",
            f"je vois {name} qui grandit",
        ]
    else:
        templates = [
            f"{name} est présent, en arrière-plan",
            f"{name}, faiblement",
            f"un murmure de {name}",
        ]

    phrase = random.choice(templates)
    if domain:
        phrase += f" [{domain}]"
    return phrase


def phrase_coactivation(node_a, node_b):
    """X et Y ensemble — co-activation potentiellement intéressante."""
    a = clean_name(node_a.content)
    b = clean_name(node_b.content)

    # Vérifier si les types sont différents (plus intéressant)
    cross_type = node_a.type != node_b.type

    if cross_type:
        templates = [
            f"{a} ({node_a.type}) et {b} ({node_b.type}) s'activent ensemble — pourquoi ?",
            f"connexion inattendue : {a} + {b}",
            f"{a} rencontre {b} — ça ne devrait pas arriver",
        ]
    else:
        templates = [
            f"{a} et {b} résonnent ensemble",
            f"{a} + {b}",
            f"les deux s'activent : {a}, {b}",
        ]
    return random.choice(templates)


def phrase_souvenir(memory_node):
    """Se souvenir — verbaliser un nœud mémoire."""
    content = clean_name(memory_node.content)
    meta = memory_node.metadata or {}
    ts = meta.get("timestamp", "")

    templates = [
        f"je me souviens : {content}",
        f"dans ma mémoire : {content}",
        f"{content}",
    ]

    phrase = random.choice(templates)
    if ts:
        phrase += f" ({ts[:10]})"
    return phrase


def phrase_question(brain, path):
    """Pourquoi X → Y ? — chemin inattendu."""
    names = [clean_name(brain._nodes[nid].content)
             for nid in path if nid in brain._nodes]
    if len(names) < 2:
        return None

    chain = " → ".join(names)
    templates = [
        f"pourquoi {chain} ?",
        f"le chemin {chain} — qu'est-ce que ça veut dire ?",
        f"{names[0]} mène à {names[-1]} en passant par {', '.join(names[1:-1])}",
    ]
    return random.choice(templates)


def phrase_synthese(concepts):
    """Synthèse — résumer l'état mental actuel."""
    if not concepts:
        return "silence. rien ne s'active."

    names = [clean_name(c.content) for c in concepts[:5]]

    if len(names) == 1:
        return f"je pense à {names[0]}"
    elif len(names) == 2:
        return f"deux choses : {names[0]} et {names[1]}"
    else:
        last = names[-1]
        rest = ", ".join(names[:-1])
        return f"en ce moment : {rest}, et {last}"


# ---------------------------------------------------------------------------
# Le Parleur
# ---------------------------------------------------------------------------

def speak(brain, about=None, max_phrases=5):
    """Générer des phrases à partir de l'état du cerveau.

    Si `about` est fourni, activer ce concept d'abord.
    Retourne une liste de phrases.
    """
    phrases = []

    # Decay d'abord — les vieux nœuds doivent se calmer
    brain.decay()

    # Si un sujet est demandé, l'activer
    if about:
        nid = brain.find_by_content(about)
        if nid:
            brain.activate(nid, 0.8)
        else:
            # Chercher par contenu partiel
            for node_id, node in brain._nodes.items():
                if about.lower() in node.content.lower() and not is_dictionary_node(node.content):
                    brain.activate(node_id, 0.8)
                    break

    # 1. Synthèse de l'état actuel
    top = get_top_activated(brain, n=8)
    if top:
        phrases.append(phrase_synthese(top))

    # 2. Tendances
    for node in top[:3]:
        domain = (node.metadata or {}).get("domain")
        phrases.append(phrase_tendance(node, domain))

    # 3. Observations (connexions fortes entre nœuds activés)
    for node in top[:3]:
        neighbors = get_strong_neighbors(brain, node.id, n=3)
        for neighbor, weight in neighbors[:1]:
            if neighbor.activation > 0.1:
                phrases.append(phrase_observation(brain, node, neighbor, weight))

    # 4. Co-activations intéressantes (types différents)
    for i, a in enumerate(top[:4]):
        for b in top[i + 1:4]:
            if a.type != b.type:
                phrases.append(phrase_coactivation(a, b))
                break

    # 5. Souvenirs récents
    memories = get_recent_memories(brain, n=2)
    for mem in memories[:1]:
        phrases.append(phrase_souvenir(mem))

    # Dédupliquer et limiter
    seen = set()
    unique = []
    for p in phrases:
        if p and p not in seen:
            seen.add(p)
            unique.append(p)

    return unique[:max_phrases]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    about = None
    if "--about" in args:
        idx = args.index("--about")
        about = args[idx + 1] if idx + 1 < len(args) else None

    stream = "--stream" in args
    interval = 30  # secondes entre chaque parole en mode stream

    brain = load_brain()
    n_nodes = len(brain._nodes)
    print(f"  [cerveau chargé — {n_nodes} nœuds]\n")

    if stream:
        print("  mode stream — le cerveau parle en continu\n")
        while True:
            phrases = speak(brain, about=about, max_phrases=3)
            ts = time.strftime("%H:%M:%S")
            for p in phrases:
                print(f"  [{ts}] {p}")
            if not phrases:
                print(f"  [{ts}] ...")
            print()
            time.sleep(interval)
            # Recharger pour voir les changements du crawler
            brain = load_brain()
    else:
        phrases = speak(brain, about=about)
        for p in phrases:
            print(f"  {p}")
        if not phrases:
            print("  silence. le graphe dort.")


if __name__ == "__main__":
    main()
