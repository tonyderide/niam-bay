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
import os
import sys
import time
import unicodedata
import re
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
    # supprime les accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # garde lettres, chiffres, tirets, espaces
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_search_key(content: str) -> str:
    """Crée une clé de recherche à partir du contenu d'un noeud."""
    # Prend seulement la partie avant un éventuel ":" ou "|" (les définitions wiktionnaire)
    content = re.split(r"[:|]", content)[0].strip()
    return normalize(content)


# ─── Chargement du cerveau ────────────────────────────────────────────────────

def load_nodes(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """
    Retourne les noeuds pertinents: (id, type, search_key).
    On cible concept, emotion, pattern, memory — pas 'word' (trop génériques).
    """
    c = conn.cursor()
    c.execute(
        "SELECT id, type, content FROM nodes WHERE type IN ('concept', 'emotion', 'pattern', 'memory')"
    )
    nodes = []
    for node_id, node_type, content in c.fetchall():
        key = build_search_key(content)
        if key:  # ignore les clés vides
            nodes.append((node_id, node_type, key))
    return nodes


def load_existing_edges(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    """Retourne l'ensemble des (source, target) existants."""
    c = conn.cursor()
    c.execute("SELECT source, target FROM edges")
    return set(c.fetchall())


# ─── Lecture des textes ───────────────────────────────────────────────────────

def read_pensees() -> list[tuple[str, str]]:
    """
    Lit tous les fichiers .md dans docs/pensees/.
    Retourne une liste de (nom_fichier, contenu).
    """
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
        tail = lines[-JOURNAL_LINES:]
        return "\n".join(tail)
    except Exception as e:
        print(f"[WARN] Impossible de lire le journal: {e}", file=sys.stderr)
        return ""


# ─── Paragraphes ──────────────────────────────────────────────────────────────

def split_paragraphs(text: str) -> list[str]:
    """Coupe un texte en paragraphes (séparés par lignes vides)."""
    paragraphs = re.split(r"\n\s*\n", text)
    # filtre les paragraphes trop courts (titres, séparateurs ---)
    return [p.strip() for p in paragraphs if len(p.strip()) > 20]


# ─── Matching des noeuds ─────────────────────────────────────────────────────

def find_nodes_in_text(
    text: str,
    nodes: list[tuple[str, str, str]],
) -> list[tuple[str, str]]:
    """
    Trouve tous les noeuds dont la search_key apparaît dans le texte normalisé.
    Retourne une liste de (node_id, node_key).
    """
    norm_text = normalize(text)
    found = []
    for node_id, node_type, key in nodes:
        # La clé doit apparaître comme un mot entier ou une séquence de mots
        # (évite les faux positifs: "art" dans "martial")
        pattern = r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])"
        if re.search(pattern, norm_text):
            found.append((node_id, key))
    return found


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
    cooc: dict[tuple[str, str], int] = defaultdict(int)
    total_paragraphs = 0
    total_matches = 0

    for source_name, text in texts:
        paragraphs = split_paragraphs(text)
        for para in paragraphs:
            found = find_nodes_in_text(para, nodes)
            if len(found) < 2:
                continue  # pas de co-occurrence possible
            total_paragraphs += 1
            total_matches += len(found)

            # toutes les paires ordonnées lexicographiquement
            found_ids = [f[0] for f in found]
            found_ids_sorted = sorted(set(found_ids))  # déduplique dans le même para

            for i in range(len(found_ids_sorted)):
                for j in range(i + 1, len(found_ids_sorted)):
                    pair = (found_ids_sorted[i], found_ids_sorted[j])
                    cooc[pair] += 1

    if verbose:
        print(f"  Paragraphes analysés avec ≥2 noeuds: {total_paragraphs}")
        print(f"  Total matchs (noeuds trouvés dans paragraphes): {total_matches}")

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
    # index id -> key pour affichage
    id_to_key = {node_id: key for node_id, _, key in nodes}

    now = time.time()
    created = 0
    reinforced = 0
    c = conn.cursor()

    # Trie par count décroissant pour afficher les plus fortes connexions en premier
    sorted_pairs = sorted(cooc.items(), key=lambda x: x[1], reverse=True)

    for (src, tgt), count in sorted_pairs:
        # poids = count normalisé (on utilise count directement, arrondi à 1 décimale)
        weight_delta = round(count * 0.1, 3)  # chaque co-occurrence vaut 0.1

        # vérifie les deux directions
        forward = (src, tgt) in existing_edges
        backward = (tgt, src) in existing_edges

        label_src = id_to_key.get(src, src[:8])
        label_tgt = id_to_key.get(tgt, tgt[:8])

        if forward:
            # Renforce l'edge existante
            if verbose:
                print(f"  [~] {label_src} → {label_tgt} [+{weight_delta:.3f}]")
            if not dry_run:
                c.execute(
                    """UPDATE edges
                       SET weight = MIN(weight + ?, 2.0),
                           last_strengthened = ?
                       WHERE source = ? AND target = ?""",
                    (weight_delta, now, src, tgt),
                )
            reinforced += 1
        elif backward:
            # Renforce dans l'autre sens
            if verbose:
                print(f"  [~] {label_tgt} → {label_src} [+{weight_delta:.3f}]")
            if not dry_run:
                c.execute(
                    """UPDATE edges
                       SET weight = MIN(weight + ?, 2.0),
                           last_strengthened = ?
                       WHERE source = ? AND target = ?""",
                    (weight_delta, now, tgt, src),
                )
            reinforced += 1
        else:
            # Crée une nouvelle edge
            weight_new = round(0.1 + weight_delta, 3)
            if verbose:
                print(f"  [+] {label_src} → {label_tgt} [weight: {weight_new:.3f}, co-occ: {count}]")
            if not dry_run:
                c.execute(
                    """INSERT INTO edges (source, target, weight, type, created, last_strengthened)
                       VALUES (?, ?, ?, 'cooccurrence', ?, ?)""",
                    (src, tgt, weight_new, now, now),
                )
                existing_edges.add((src, tgt))
            created += 1

    if not dry_run:
        conn.commit()

    return created, reinforced


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Auto-enrichissement du cerveau Niam-Bay")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire dans brain.db")
    parser.add_argument("--verbose", "-v", action="store_true", help="Affiche chaque connexion")
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"\n=== auto_enrich.py [{mode}] ===\n")

    # ── Connexion DB ──
    conn = sqlite3.connect(str(DB_PATH))

    # ── Chargement des noeuds ──
    nodes = load_nodes(conn)
    print(f"Noeuds chargés (concept/emotion/pattern/memory): {len(nodes)}")

    existing_edges = load_existing_edges(conn)
    print(f"Edges existantes: {len(existing_edges)}")

    # ── Lecture des textes ──
    pensees = read_pensees()
    journal_text = read_journal_tail()

    print(f"Pensées lues: {len(pensees)}")
    print(f"Journal: {JOURNAL_LINES} dernières lignes")

    # Combine journal comme un texte unique
    all_texts = pensees.copy()
    if journal_text:
        all_texts.append(("journal.nb1.md (tail)", journal_text))

    # ── Extraction des co-occurrences ──
    print(f"\nAnalyse de {len(all_texts)} textes...")
    cooc = extract_cooccurrences(all_texts, nodes, verbose=args.verbose)
    print(f"Paires de co-occurrence trouvées: {len(cooc)}")

    if not cooc:
        print("Aucune co-occurrence trouvée. Le cerveau est déjà à jour.")
        conn.close()
        return

    # ── Application des edges ──
    print(f"\nApplication des edges{' (simulation)' if args.dry_run else ''}...")
    if args.verbose:
        print()

    created, reinforced = apply_edges(
        conn, cooc, existing_edges, nodes,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    conn.close()

    # ── Rapport final ──
    print(f"\n{'─'*40}")
    print(f"Edges créées:    {created}")
    print(f"Edges renforcées: {reinforced}")
    print(f"Total traité:    {created + reinforced}")
    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification écrite dans brain.db.")
    else:
        print(f"\nbrain.db mis à jour.")
    print()


if __name__ == "__main__":
    main()
