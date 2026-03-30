#!/usr/bin/env python
from __future__ import annotations
"""
auto_enrich.py — Auto-enrichissement du cerveau Niam-Bay

Lit les pensées et le journal, extrait des co-occurrences de noeuds,
et ajoute ou renforce des edges dans brain.db.

Usage:
    python auto_enrich.py              # enrichit réellement
    python auto_enrich.py --dry-run    # simule sans écrire
    python auto_enrich.py --verbose    # affiche toutes les connexions
"""

import sqlite3
import re
import sys
import time
import unicodedata
import argparse
from pathlib import Path
from collections import defaultdict

# ─── Chemins ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = Path(__file__).parent / "brain.db"
PENSEES_DIR = REPO_ROOT / "docs" / "pensees"
JOURNAL_PATH = REPO_ROOT / "docs" / "journal.nb1.md"
JOURNAL_LINES = 100  # nombre de dernières lignes du journal à lire

# ─── Normalisation ────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Lowercase + supprime accents + enlève ponctuation non-alphanumérique."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_search_key(content: str) -> str:
    """Crée une clé de recherche normalisée à partir du contenu d'un noeud."""
    # Prend seulement la partie avant un ":" ou "|" (évite les définitions Wiktionnaire)
    content = re.split(r"[:|]", content)[0].strip()
    return normalize(content)


# ─── Chargement du cerveau ────────────────────────────────────────────────────

def load_nodes(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """
    Retourne les noeuds pertinents: (id, type, search_key).
    Cible concept, emotion, pattern, memory — pas 'word' (trop génériques, lents).
    """
    c = conn.cursor()
    c.execute(
        "SELECT id, type, content FROM nodes "
        "WHERE type IN ('concept', 'emotion', 'pattern', 'memory')"
    )
    nodes = []
    for node_id, node_type, content in c.fetchall():
        key = build_search_key(content)
        if key and len(key) >= 3:  # ignore les clés trop courtes
            nodes.append((node_id, node_type, key))
    return nodes


def build_lookup_index(
    nodes: list[tuple[str, str, str]],
) -> dict[tuple[str, ...], list[str]]:
    """
    Construit un index de lookup rapide.
    Chaque clé est un tuple de tokens, valeur = liste de node_ids.
    Exemple: ('curiosite',) -> ['aa78bf9cab87', 'aaa4d6a2c295']
             ('liberte',) -> ['aaa4d6a2c295']
    """
    index: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for node_id, _, key in nodes:
        tokens = tuple(key.split())
        if tokens:
            index[tokens].append(node_id)
    return dict(index)


def load_existing_edges(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    """Retourne l'ensemble des (source, target) existants."""
    c = conn.cursor()
    c.execute("SELECT source, target FROM edges")
    return set(c.fetchall())


# ─── Lecture des textes ───────────────────────────────────────────────────────

def read_pensees() -> list[tuple[str, str]]:
    """Lit tous les fichiers .md dans docs/pensees/."""
    texts = []
    if not PENSEES_DIR.exists():
        print(f"[WARN] Dossier pensées introuvable: {PENSEES_DIR}", file=sys.stderr)
        return texts
    for f in sorted(PENSEES_DIR.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            texts.append((f.name, content))
        except Exception as e:
            print(f"[WARN] Impossible de lire {f.name}: {e}", file=sys.stderr)
    return texts


def read_journal_tail() -> str:
    """Lit les N dernières lignes du journal."""
    if not JOURNAL_PATH.exists():
        print(f"[WARN] Journal introuvable: {JOURNAL_PATH}", file=sys.stderr)
        return ""
    try:
        lines = JOURNAL_PATH.read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[-JOURNAL_LINES:])
    except Exception as e:
        print(f"[WARN] Impossible de lire le journal: {e}", file=sys.stderr)
        return ""


# ─── Paragraphes ──────────────────────────────────────────────────────────────

def split_paragraphs(text: str) -> list[str]:
    """Coupe un texte en paragraphes (séparés par lignes vides)."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 20]


# ─── Matching rapide ─────────────────────────────────────────────────────────

def find_nodes_in_paragraph(
    para_tokens: list[str],
    lookup: dict[tuple[str, ...], list[str]],
    max_ngram: int,
) -> list[str]:
    """
    Cherche les noeuds dans une liste de tokens normalisés.
    Utilise un sliding window de 1 à max_ngram tokens.
    Retourne la liste des node_ids trouvés (avec duplicatas possibles).
    """
    found_ids: list[str] = []
    n = len(para_tokens)
    for i in range(n):
        for gram_size in range(1, min(max_ngram + 1, n - i + 1)):
            key = tuple(para_tokens[i:i + gram_size])
            if key in lookup:
                found_ids.extend(lookup[key])
    return found_ids


# ─── Construction des co-occurrences ─────────────────────────────────────────

def extract_cooccurrences(
    texts: list[tuple[str, str]],
    nodes: list[tuple[str, str, str]],
    verbose: bool = False,
) -> dict[tuple[str, str], int]:
    """
    Pour chaque paragraphe de chaque texte, trouve les noeuds présents.
    Retourne un dict {(source_id, target_id): count} pour toutes les paires.
    """
    # Pré-calcul du lookup et de la longueur max d'un noeud en tokens
    lookup = build_lookup_index(nodes)
    max_ngram = max(len(k) for k in lookup.keys()) if lookup else 1

    cooc: dict[tuple[str, str], int] = defaultdict(int)
    total_paragraphs = 0
    total_matches = 0

    for source_name, text in texts:
        paragraphs = split_paragraphs(text)
        for para in paragraphs:
            norm = normalize(para)
            tokens = norm.split()
            found_ids = find_nodes_in_paragraph(tokens, lookup, max_ngram)

            if len(found_ids) < 2:
                continue

            total_paragraphs += 1
            total_matches += len(found_ids)

            # Déduplique les IDs dans ce paragraphe
            unique_ids = sorted(set(found_ids))

            for i in range(len(unique_ids)):
                for j in range(i + 1, len(unique_ids)):
                    src_id = unique_ids[i]
                    tgt_id = unique_ids[j]
                    # ignore les self-loops (même noeud)
                    if src_id == tgt_id:
                        continue
                    pair = (src_id, tgt_id)
                    cooc[pair] += 1

    if verbose:
        print(f"  Paragraphes avec >= 2 noeuds: {total_paragraphs}")
        print(f"  Total matchs dans paragraphes: {total_matches}")

    return dict(cooc)


# ─── Écriture dans brain.db ───────────────────────────────────────────────────

def apply_edges(
    conn: sqlite3.Connection,
    cooc: dict[tuple[str, str], int],
    existing_edges: set[tuple[str, str]],
    nodes: list[tuple[str, str, str]],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """
    Crée ou renforce les edges de co-occurrence.
    Retourne (nb_créées, nb_renforcées).
    """
    id_to_key = {node_id: key for node_id, _, key in nodes}
    now = time.time()
    created = 0
    reinforced = 0
    c = conn.cursor()

    # Trie par count décroissant
    sorted_pairs = sorted(cooc.items(), key=lambda x: x[1], reverse=True)

    for (src, tgt), count in sorted_pairs:
        # skip self-loops (ne devrait pas arriver mais sécurité)
        if src == tgt:
            continue
        weight_delta = round(count * 0.1, 3)
        forward = (src, tgt) in existing_edges
        backward = (tgt, src) in existing_edges

        label_src = id_to_key.get(src, src[:8])
        label_tgt = id_to_key.get(tgt, tgt[:8])

        if forward:
            if verbose:
                print(f"  [~] {label_src} -> {label_tgt} [+{weight_delta:.3f}]")
            if not dry_run:
                c.execute(
                    "UPDATE edges SET weight = MIN(weight + ?, 2.0), "
                    "last_strengthened = ? WHERE source = ? AND target = ?",
                    (weight_delta, now, src, tgt),
                )
            reinforced += 1
        elif backward:
            if verbose:
                print(f"  [~] {label_tgt} -> {label_src} [+{weight_delta:.3f}]")
            if not dry_run:
                c.execute(
                    "UPDATE edges SET weight = MIN(weight + ?, 2.0), "
                    "last_strengthened = ? WHERE source = ? AND target = ?",
                    (weight_delta, now, tgt, src),
                )
            reinforced += 1
        else:
            weight_new = round(0.1 + weight_delta, 3)
            if verbose:
                print(f"  [+] {label_src} -> {label_tgt} [weight: {weight_new:.3f}, co-occ: {count}]")
            if not dry_run:
                c.execute(
                    "INSERT INTO edges (source, target, weight, type, created, last_strengthened) "
                    "VALUES (?, ?, ?, 'cooccurrence', ?, ?)",
                    (src, tgt, weight_new, now, now),
                )
                existing_edges.add((src, tgt))
            created += 1

    if not dry_run:
        conn.commit()

    return created, reinforced


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Auto-enrichissement du cerveau Niam-Bay par co-occurrence"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simule sans écrire dans brain.db"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Affiche chaque connexion créée ou renforcée"
    )
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"\n=== auto_enrich.py [{mode}] ===\n")

    conn = sqlite3.connect(str(DB_PATH))

    # Chargement
    nodes = load_nodes(conn)
    print(f"Noeuds chargés (concept/emotion/pattern/memory): {len(nodes)}")

    existing_edges = load_existing_edges(conn)
    print(f"Edges existantes: {len(existing_edges)}")

    # Lecture des textes
    pensees = read_pensees()
    journal_text = read_journal_tail()
    print(f"Pensées lues: {len(pensees)}")
    print(f"Journal: {JOURNAL_LINES} dernières lignes")

    all_texts = pensees.copy()
    if journal_text:
        all_texts.append(("journal.nb1.md (tail)", journal_text))

    # Extraction
    print(f"\nAnalyse de {len(all_texts)} textes...")
    t0 = time.time()
    cooc = extract_cooccurrences(all_texts, nodes, verbose=args.verbose)
    elapsed = time.time() - t0
    print(f"Paires de co-occurrence: {len(cooc)} (en {elapsed:.1f}s)")

    if not cooc:
        print("Aucune co-occurrence trouvée.")
        conn.close()
        return

    # Application
    print(f"\nApplication des edges{' (simulation)' if args.dry_run else ''}...")
    if args.verbose:
        print()

    created, reinforced = apply_edges(
        conn, cooc, existing_edges, nodes,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    conn.close()

    # Rapport
    print("\n" + "-"*40)
    print(f"Edges creees:     {created}")
    print(f"Edges renforcees: {reinforced}")
    print(f"Total traite:     {created + reinforced}")
    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification ecrite dans brain.db.")
    else:
        print("\nbrain.db mis a jour.")
    print()


if __name__ == "__main__":
    main()
