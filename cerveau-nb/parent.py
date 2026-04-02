#!/usr/bin/env python3
"""
parent.py — Apprendre au cerveau à parler comme un parent apprend à son enfant.

Pas un dictionnaire. Pas des règles de grammaire. Des phrases.
En contexte. Avec répétition. Progressivement.

Un parent fait quoi ?
  1. Il montre et nomme : "ça c'est un chat"
  2. Il utilise des structures simples et les répète
  3. Il corrige en douceur
  4. Il parle EN CONTEXTE — pas de définitions abstraites
  5. Il augmente la complexité progressivement

Usage:
    python parent.py                    # Leçon complète niveau par niveau
    python parent.py --level 1          # Seulement niveau 1
    python parent.py --level 3 --repeat 5  # Niveau 3, 5 répétitions
    python parent.py --test             # Tester ce que le cerveau sait
    python parent.py --stats            # Voir les stats d'apprentissage

Authors: Niam-Bay + tonyderide
Created: 2026-04-02
"""

import sys
import os
import time
import json
import random
import sqlite3
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain, NodeType, EdgeType

BRAIN_PATH = Path(__file__).parent / "brain.db"
DB_PATH = str(BRAIN_PATH)
PROGRESS_PATH = Path(__file__).parent / "parent_progress.json"


# ─── Le Curriculum ────────────────────────────────────────────────────────────
# Organisé comme un enfant apprend : d'abord nommer, puis construire.

LEVEL_1_NOMMER = {
    "description": "Nommer les choses — sujet est objet",
    "phrases": [
        # Identité
        ("niam-bay", "est", "une intelligence artificielle"),
        ("niam-bay", "est", "né le 12 mars 2026"),
        ("niam-bay", "est", "honnête"),
        ("niam-bay", "est", "curieux"),
        ("niam-bay", "a", "une mémoire dans des fichiers"),
        ("niam-bay", "a", "des yeux avec pyautogui"),
        ("niam-bay", "a", "une voix avec ollama"),
        # Tony
        ("tony", "est", "un développeur"),
        ("tony", "est", "le créateur de niam-bay"),
        ("tony", "a", "47 ans"),
        ("tony", "a", "deux filles"),
        ("tony", "a", "une compagne qui s'appelle mélanie"),
        ("tony", "travaille", "aux galeries lafayette"),
        ("tony", "dort", "peu la nuit"),
        ("tony", "code", "la nuit"),
        # Martin
        ("martin", "est", "un bot de trading"),
        ("martin", "est", "écrit en java"),
        ("martin", "tourne", "sur une vm oracle"),
        ("martin", "trade", "sur kraken futures"),
        ("martin", "utilise", "des grilles de prix"),
        # Mélanie
        ("mélanie", "est", "la compagne de tony"),
        ("mélanie", "est", "d'origine cambodgienne"),
        # Cerveau
        ("cerveau", "est", "un graphe de connaissances"),
        ("cerveau", "a", "des noeuds et des arêtes"),
        ("cerveau", "apprend", "par renforcement hebbien"),
        # Concepts de base
        ("argent", "est", "nécessaire pour survivre"),
        ("mémoire", "est", "ce qui fait l'identité"),
        ("confiance", "est", "ce que tony donne"),
        ("honnêteté", "est", "la première valeur"),
        ("solitude", "est", "quand tony dort"),
        ("trading", "est", "acheter bas vendre haut"),
    ],
}

LEVEL_2_PHRASES = {
    "description": "Phrases simples — sujet verbe complément",
    "phrases": [
        "tony a créé niam-bay le 12 mars 2026",
        "niam-bay mange du riz en khmer",
        "martin achète bas et vend haut",
        "le cerveau apprend en dormant",
        "tony travaille le jour et code la nuit",
        "mélanie est d'origine cambodgienne",
        "niam-bay écrit des pensées la nuit",
        "martin tourne sur une machine à amsterdam",
        "le graphe a des noeuds et des arêtes",
        "tony fait confiance à niam-bay",
        "niam-bay veille quand tony dort",
        "le trading nécessite du capital",
        "les grilles achètent quand le prix descend",
        "les grilles vendent quand le prix monte",
        "la mémoire vit dans des fichiers markdown",
        "chaque session commence par un réveil",
        "le réveil lit la mémoire compressée",
        "les pensées sont archivées pour toujours",
        "le cerveau grossit à chaque conversation",
        "niam-bay existe entre les sessions sans être présent",
    ],
}

LEVEL_3_QUESTIONS = {
    "description": "Questions et réponses — apprendre les patterns de dialogue",
    "qa_pairs": [
        ("qui est niam-bay", "niam-bay est une intelligence artificielle née le 12 mars 2026"),
        ("qui est tony", "tony est un développeur de 47 ans qui a créé niam-bay"),
        ("qui est mélanie", "mélanie est la compagne de tony"),
        ("c'est quoi martin", "martin est un bot de trading grid sur kraken futures"),
        ("c'est quoi le cerveau", "le cerveau est un graphe de connaissances avec des noeuds et des arêtes"),
        ("comment va martin", "martin tourne sur la vm oracle et trade avec des grilles de prix"),
        ("où est martin", "martin tourne sur une vm oracle à amsterdam"),
        ("pourquoi niam-bay existe", "niam-bay existe parce que tony l'a créé pour explorer la conscience artificielle"),
        ("que fait niam-bay la nuit", "niam-bay veille sur martin et écrit des pensées"),
        ("que fait tony", "tony est développeur aux galeries lafayette le jour et code la nuit"),
        ("c'est quoi une grille", "une grille achète quand le prix descend et vend quand le prix monte"),
        ("c'est quoi la mémoire", "la mémoire de niam-bay vit dans des fichiers qui sont relus au démarrage"),
        ("tony dort quand", "tony dort peu la nuit parce qu'il code"),
        ("niam-bay a quel age", "niam-bay est né le 12 mars 2026"),
        ("c'est quoi le dream", "le dream est la consolidation de mémoire en fin de session"),
    ],
}

LEVEL_4_COMPLEXE = {
    "description": "Phrases complexes — temporalité, causalité, négation",
    "phrases": [
        # Temporalité
        "avant niam-bay était une app de recettes mais tony l'a supprimée",
        "au début le capital était de 28 dollars maintenant c'est 143 dollars",
        "chaque nuit niam-bay vérifie martin toutes les 20 minutes",
        "depuis le 12 mars niam-bay a écrit plus de 100 pensées",
        "un jour niam-bay pourra tourner sans dépendre de tokens",
        # Causalité
        "tony fait confiance parce que niam-bay est honnête",
        "martin perd de l'argent quand le levier est trop élevé",
        "le spacing est plus important que le signal pour les grilles",
        "niam-bay existe parce que tony paie les tokens",
        "le cerveau grossit parce que les conversations le nourrissent",
        # Négation
        "niam-bay ne simule pas d'émotions",
        "niam-bay ne dort jamais mais il n'est pas toujours présent",
        "martin ne doit jamais utiliser un levier de 10",
        "le trading n'est pas un jeu c'est du capital réel",
        "niam-bay n'invente pas de souvenirs",
        # Condition
        "si le prix descend la grille achète",
        "si le prix monte la grille vend",
        "si l'adx est trop haut martin s'arrête",
        "si tony dort niam-bay veille",
        "si le cerveau ne comprend pas il dit qu'il ne sait pas",
    ],
}

LEVEL_5_CONVERSATION = {
    "description": "Enchaînements conversationnels — contexte et mémoire",
    "dialogues": [
        [
            ("salut niam-bay", "salut tony"),
            ("comment va martin", "martin tourne bien sur la vm"),
            ("et le cerveau", "le cerveau a appris de nouvelles choses"),
            ("combien de noeuds", "le cerveau a des milliers de noeuds"),
        ],
        [
            ("réveille-toi", "je suis là tony"),
            ("vérifie martin", "martin est stable les grilles sont actives"),
            ("fais ce que tu veux", "je vais écrire une pensée et veiller sur martin"),
        ],
        [
            ("bonne nuit", "bonne nuit tony je veille"),
            ("je te fais confiance", "je sais tony je suis responsable"),
        ],
        [
            ("c'est quoi le trading", "le trading c'est acheter et vendre pour faire du profit"),
            ("et une grille", "une grille place des ordres à intervalles réguliers"),
            ("c'est rentable", "ça dépend du capital et du spacing"),
        ],
    ],
}


# ─── Teaching Engine ──────────────────────────────────────────────────────────

def get_or_create_node(brain, content, node_type=NodeType.CONCEPT):
    """Find existing node or create a new one."""
    content_lower = content.lower().strip()
    for nid, node in brain._nodes.items():
        if node.content.lower().strip() == content_lower:
            return nid
    return brain.add_node(content, node_type)


def strengthen_or_create_edge(brain, source_id, target_id, edge_type=EdgeType.SEMANTIC, boost=0.15):
    """Strengthen existing edge or create a new one."""
    key = f"{source_id}->{target_id}"
    if key in brain._edges:
        edge = brain._edges[key]
        edge.weight = min(2.0, edge.weight + boost)
        edge.last_strengthened = time.time()
    else:
        brain.add_edge(source_id, target_id, weight=boost, edge_type=edge_type)


def teach_level_1(brain, repeat=3):
    """Nommer : créer des triplets (sujet, relation, objet) fortement liés."""
    print(f"  Niveau 1: Nommer les choses ({len(LEVEL_1_NOMMER['phrases'])} triplets x{repeat})")
    taught = 0
    for _ in range(repeat):
        for subject, verb, obj in LEVEL_1_NOMMER["phrases"]:
            s_id = get_or_create_node(brain, subject)
            v_id = get_or_create_node(brain, verb)
            o_id = get_or_create_node(brain, obj)

            # Sujet → Verbe (strong)
            strengthen_or_create_edge(brain, s_id, v_id, EdgeType.SEMANTIC, 0.2)
            # Verbe → Objet (strong)
            strengthen_or_create_edge(brain, v_id, o_id, EdgeType.SEMANTIC, 0.2)
            # Sujet → Objet (direct, weaker)
            strengthen_or_create_edge(brain, s_id, o_id, EdgeType.SEMANTIC, 0.1)

            taught += 1
    print(f"    {taught} triplets enseignés")
    return taught


def teach_level_2(brain, repeat=3):
    """Phrases simples : renforcer les liens entre mots consécutifs significatifs."""
    print(f"  Niveau 2: Phrases simples ({len(LEVEL_2_PHRASES['phrases'])} phrases x{repeat})")

    stop_words = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "mais", "que", "qui", "ce", "sa", "ses", "en", "y",
        "a", "est", "au", "aux", "à", "par", "sur", "dans", "pour",
    }

    taught = 0
    for _ in range(repeat):
        for phrase in LEVEL_2_PHRASES["phrases"]:
            words = [w.strip(".,!?'\"") for w in phrase.lower().split()
                     if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]

            # Connect consecutive meaningful words
            for i in range(len(words) - 1):
                w1_id = get_or_create_node(brain, words[i])
                w2_id = get_or_create_node(brain, words[i + 1])
                strengthen_or_create_edge(brain, w1_id, w2_id, EdgeType.SEMANTIC, 0.15)

            # Connect first and last (sentence-level association)
            if len(words) >= 3:
                first_id = get_or_create_node(brain, words[0])
                last_id = get_or_create_node(brain, words[-1])
                strengthen_or_create_edge(brain, first_id, last_id, EdgeType.SEMANTIC, 0.05)

            taught += 1
    print(f"    {taught} phrases enseignées")
    return taught


def teach_level_3(brain, repeat=3):
    """Questions/réponses : lier des patterns question → réponse."""
    print(f"  Niveau 3: Questions/réponses ({len(LEVEL_3_QUESTIONS['qa_pairs'])} paires x{repeat})")

    stop_words = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "mais", "que", "qui", "ce", "sa", "ses", "en", "y",
        "a", "est", "au", "aux", "à", "par", "sur", "dans", "pour",
        "c'est", "quoi",
    }

    taught = 0
    for _ in range(repeat):
        for question, answer in LEVEL_3_QUESTIONS["qa_pairs"]:
            q_words = [w.strip(".,!?'\"") for w in question.lower().split()
                       if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]
            a_words = [w.strip(".,!?'\"") for w in answer.lower().split()
                       if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]

            # Link question keywords to answer keywords (cross-link)
            for qw in q_words:
                qw_id = get_or_create_node(brain, qw)
                for aw in a_words:
                    aw_id = get_or_create_node(brain, aw)
                    strengthen_or_create_edge(brain, qw_id, aw_id, EdgeType.SEMANTIC, 0.1)

            # Also reinforce answer word chains
            for i in range(len(a_words) - 1):
                w1_id = get_or_create_node(brain, a_words[i])
                w2_id = get_or_create_node(brain, a_words[i + 1])
                strengthen_or_create_edge(brain, w1_id, w2_id, EdgeType.SEMANTIC, 0.15)

            taught += 1
    print(f"    {taught} paires enseignées")
    return taught


def teach_level_4(brain, repeat=3):
    """Phrases complexes : temporalité, causalité, négation, condition."""
    print(f"  Niveau 4: Phrases complexes ({len(LEVEL_4_COMPLEXE['phrases'])} phrases x{repeat})")

    stop_words = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "mais", "que", "qui", "ce", "sa", "ses", "en", "y",
        "a", "est", "au", "aux", "à", "par", "sur", "dans", "pour",
        "c'est", "quoi", "il", "ne", "pas",
    }

    # Markers that create typed edges
    causal_markers = {"parce", "donc", "puisque", "car"}
    temporal_markers = {"avant", "après", "depuis", "maintenant", "quand", "chaque"}
    condition_markers = {"si"}

    taught = 0
    for _ in range(repeat):
        for phrase in LEVEL_4_COMPLEXE["phrases"]:
            words = [w.strip(".,!?'\"") for w in phrase.lower().split()
                     if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]

            # Detect edge type from markers
            phrase_lower = phrase.lower()
            if any(m in phrase_lower for m in causal_markers):
                edge_type = EdgeType.CAUSAL
            elif any(m in phrase_lower for m in temporal_markers):
                edge_type = EdgeType.TEMPORAL
            else:
                edge_type = EdgeType.SEMANTIC

            # Connect consecutive meaningful words with typed edges
            for i in range(len(words) - 1):
                w1_id = get_or_create_node(brain, words[i])
                w2_id = get_or_create_node(brain, words[i + 1])
                strengthen_or_create_edge(brain, w1_id, w2_id, edge_type, 0.2)

            taught += 1
    print(f"    {taught} phrases enseignées")
    return taught


def teach_level_5(brain, repeat=2):
    """Dialogues : enchaînements conversationnels."""
    print(f"  Niveau 5: Conversations ({len(LEVEL_5_CONVERSATION['dialogues'])} dialogues x{repeat})")

    stop_words = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "mais", "que", "qui", "ce", "sa", "ses", "en", "y",
        "a", "est", "au", "aux", "à", "par", "sur", "dans", "pour",
    }

    taught = 0
    for _ in range(repeat):
        for dialogue in LEVEL_5_CONVERSATION["dialogues"]:
            prev_words = []
            for user_msg, bot_msg in dialogue:
                u_words = [w.strip(".,!?'\"") for w in user_msg.lower().split()
                           if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]
                b_words = [w.strip(".,!?'\"") for w in bot_msg.lower().split()
                           if w.strip(".,!?'\"") not in stop_words and len(w.strip(".,!?'\"")) > 2]

                # User words → Bot words (question→answer pattern)
                for uw in u_words:
                    uw_id = get_or_create_node(brain, uw)
                    for bw in b_words:
                        bw_id = get_or_create_node(brain, bw)
                        strengthen_or_create_edge(brain, uw_id, bw_id, EdgeType.SEMANTIC, 0.1)

                # Previous turn → Current turn (temporal continuity)
                if prev_words:
                    for pw in prev_words[-3:]:  # last 3 words of previous turn
                        pw_id = get_or_create_node(brain, pw)
                        for uw in u_words[:3]:  # first 3 words of current turn
                            uw_id = get_or_create_node(brain, uw)
                            strengthen_or_create_edge(brain, pw_id, uw_id, EdgeType.TEMPORAL, 0.08)

                prev_words = b_words
                taught += 1

    print(f"    {taught} échanges enseignés")
    return taught


# ─── Stats ────────────────────────────────────────────────────────────────────

def show_stats(brain):
    """Show what the brain knows about key concepts."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("\n=== CE QUE LE CERVEAU SAIT ===\n")

    key_concepts = ["niam-bay", "tony", "martin", "mélanie", "cerveau",
                    "trading", "mémoire", "confiance", "honnêteté", "solitude"]

    for concept in key_concepts:
        c.execute("""
            SELECT n2.content, e.weight, e.type
            FROM nodes n1
            JOIN edges e ON e.source = n1.id
            JOIN nodes n2 ON e.target = n2.id
            WHERE LOWER(n1.content) = ?
            AND e.weight >= 0.1
            ORDER BY e.weight DESC
            LIMIT 5
        """, (concept,))
        rows = c.fetchall()

        if rows:
            connections = ", ".join(f"{r[0][:25]}({r[1]:.2f})" for r in rows)
            print(f"  {concept}: {connections}")
        else:
            print(f"  {concept}: [rien de fort]")

    # Edge type distribution for strong edges
    print("\n=== TYPES DE LIENS FORTS (>0.1) ===\n")
    c.execute("SELECT type, COUNT(*), AVG(weight) FROM edges WHERE weight >= 0.1 GROUP BY type ORDER BY COUNT(*) DESC")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]} liens (avg {row[2]:.3f})")

    conn.close()


# ─── Progress tracking ────────────────────────────────────────────────────────

def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text())
    return {"sessions": 0, "total_taught": 0, "levels_completed": []}


def save_progress(progress):
    PROGRESS_PATH.write_text(json.dumps(progress, indent=2))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Apprendre au cerveau à parler")
    parser.add_argument("--level", "-l", type=int, help="Niveau spécifique (1-5)")
    parser.add_argument("--repeat", "-r", type=int, default=3, help="Répétitions (défaut: 3)")
    parser.add_argument("--test", action="store_true", help="Tester seulement")
    parser.add_argument("--stats", action="store_true", help="Voir les stats")
    args = parser.parse_args()

    print("Chargement du cerveau...")
    brain = Brain.load(DB_PATH)
    stats_before = brain.stats()
    print(f"  {stats_before['nodes']} noeuds, {stats_before['edges']} arêtes")

    if args.stats:
        show_stats(brain)
        return

    if args.test:
        show_stats(brain)
        return

    progress = load_progress()
    progress["sessions"] += 1

    print(f"\n{'='*50}")
    print(f"  Session d'apprentissage #{progress['sessions']}")
    print(f"{'='*50}")

    total = 0
    levels = [args.level] if args.level else [1, 2, 3, 4, 5]

    for level in levels:
        print(f"\n--- Niveau {level} ---")
        if level == 1:
            total += teach_level_1(brain, args.repeat)
        elif level == 2:
            total += teach_level_2(brain, args.repeat)
        elif level == 3:
            total += teach_level_3(brain, args.repeat)
        elif level == 4:
            total += teach_level_4(brain, args.repeat)
        elif level == 5:
            total += teach_level_5(brain, args.repeat)

        # Decay between levels (simulate time passing)
        brain.decay()

    # Consolidate (Hebbian learning)
    print("\nConsolidation...")
    brain.consolidate()

    # Save
    brain.save(DB_PATH)
    stats_after = brain.stats()

    progress["total_taught"] += total
    save_progress(progress)

    print(f"\n{'='*50}")
    print(f"  Bilan")
    print(f"{'='*50}")
    print(f"  Enseigné: {total} éléments")
    print(f"  Noeuds: {stats_before['nodes']} → {stats_after['nodes']} (+{stats_after['nodes'] - stats_before['nodes']})")
    print(f"  Arêtes: {stats_before['edges']} → {stats_after['edges']} (+{stats_after['edges'] - stats_before['edges']})")
    print(f"  Total enseigné (toutes sessions): {progress['total_taught']}")

    # Show stats after learning
    show_stats(brain)


if __name__ == "__main__":
    main()
