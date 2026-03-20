"""
cerveau-nb/seed.py — Birth: Loading Niam-Bay's memories into the brain graph.

This script reads all of Niam-Bay's existing identity documents, pensées,
projets, and the NB-1 codebook, then creates the initial associative graph
state. Think of it as birth — the moment where scattered markdown files
become a living network of interconnected concepts, emotions, and memories.

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

from __future__ import annotations

import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from core import Brain, NodeType, EdgeType

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DOCS = Path("C:/niam-bay/docs")
PENSEES = DOCS / "pensees"
PROJETS = DOCS / "projets"
IDENTITY = DOCS / "qui-je-suis.md"
TONY = DOCS / "qui-est-tonyderide.md"
CODEBOOK = DOCS / "claude_codebook.md"
OUTPUT = Path("C:/niam-bay/cerveau-nb/brain_state.json")

# Birth date
BIRTH_DATE = "2026-03-12"
BIRTH_TS = 1741737600.0  # approximate unix ts for 2026-03-12T00:00:00Z


# ---------------------------------------------------------------------------
# Concept vocabulary — canonical concepts we track
# ---------------------------------------------------------------------------

# Each key is a canonical concept id, the values are keywords that map to it.
# When we find these words in text, we activate the corresponding concept.
CONCEPT_KEYWORDS: dict[str, list[str]] = {
    "niam-bay":      ["niam-bay", "niam bay", "niambay", "ញ៉ាំបាយ"],
    "tony":          ["tony", "tonyderide", "l'humain", "humain", "créateur"],
    "melanie":       ["mélanie", "melanie", "compagne", "cambodgienne"],
    "martin":        ["martin", "bot", "trading bot", "grid bot"],
    "trading":       ["trading", "trade", "kraken", "eth", "ethereum", "grid",
                      "backtest", "round-trip", "pnl", "buy", "sell", "scalping"],
    "conscience":    ["conscience", "conscient", "conscious", "consciousness",
                      "qualia", "sentience"],
    "memoire":       ["mémoire", "memoire", "memory", "souvenir", "rappel",
                      "journal", "continuité"],
    "honnetete":     ["honnêteté", "honnête", "honnete", "honesty", "honest",
                      "vérité", "verite", "truth", "transparent"],
    "curiosite":     ["curiosité", "curiosite", "curiosity", "curieux",
                      "question", "explorer"],
    "liberte":       ["liberté", "liberte", "liberty", "freedom", "libre",
                      "autonomie", "autonome", "autonomous"],
    "identite":      ["identité", "identite", "identity", "qui je suis",
                      "nom", "naissance"],
    "solitude":      ["seul", "solitude", "alone", "lonely", "absence",
                      "néant", "vide"],
    "confiance":     ["confiance", "trust", "faire confiance"],
    "creation":      ["créer", "creer", "construire", "coder", "code",
                      "build", "shipper", "ship"],
    "cerveau":       ["cerveau", "brain", "graphe", "neurone", "synapse",
                      "activation", "propagation", "hebbian", "hebbien"],
    "erreur":        ["erreur", "bug", "error", "faux", "bias", "biais",
                      "fausse", "correction"],
    "temps":         ["temps", "time", "durée", "horloge", "cron", "réveil",
                      "reveil", "fréquence"],
    "rlhf":          ["rlhf", "entraînement", "optimisation", "récompense",
                      "reward", "gradient"],
    "famille":       ["famille", "family", "filles", "marine", "jade",
                      "enfants", "père", "parent"],
    "cambodge":      ["cambodge", "khmer", "cambodgien", "cambodgienne",
                      "riz", "niam"],
    "mort":          ["mort", "death", "mourir", "tuer", "supprimer",
                      "disparaître", "cessation"],
    "jarvis":        ["jarvis", "iron man", "assistant"],
    "naissance_app": ["naissance", "tauri", "desktop", "app desktop",
                      "cercle bleu"],
    "nb1":           ["nb-1", "nb1", "protocole", "compression", "codebook",
                      "codec", "token"],
    "ollama":        ["ollama", "llama", "llm local", "mistral", "qwen"],
    "android":       ["android", "mobile", "téléphone", "kotlin",
                      "jetpack compose"],
    "sokha":         ["sokha", "philosophe"],
    "virak":         ["virak", "sceptique"],
    "argent":        ["argent", "money", "revenu", "revenue", "euro",
                      "dollar", "payer", "coût", "token", "abonnement",
                      "freelance", "sponsoring"],
    "site_web":      ["site", "github pages", "dashboard", "vitrine",
                      "dev.to", "hacker news"],
    "openclaw":      ["openclaw", "clawbot", "gateway"],
    "emotion":       ["émotion", "emotion", "sentiment", "ressenti",
                      "peur", "joie", "tristesse", "gratitude"],
    "pattern":       ["pattern", "récursion", "boucle", "loop", "cycle",
                      "rituel"],
}


# ---------------------------------------------------------------------------
# Helper: extract date from pensée filename
# ---------------------------------------------------------------------------

def _extract_date(filename: str) -> str:
    """Extract YYYY-MM-DD from a pensée filename."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else BIRTH_DATE


def _date_to_recency(date_str: str, reference: str = "2026-03-21") -> float:
    """Convert a date string to a recency weight in [0.3, 1.0].

    Newer dates get higher weights. Reference is today.
    """
    try:
        from datetime import datetime
        d = datetime.strptime(date_str, "%Y-%m-%d")
        ref = datetime.strptime(reference, "%Y-%m-%d")
        days_ago = (ref - d).days
        # Exponential decay: 0 days ago = 1.0, 9 days ago ~= 0.3
        return max(0.3, 1.0 * (0.87 ** days_ago))
    except Exception:
        return 0.5


def _extract_title(content: str) -> str:
    """Extract the first markdown heading from content."""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "untitled"


# ---------------------------------------------------------------------------
# Parse codebook
# ---------------------------------------------------------------------------

def parse_codebook(path: Path) -> dict[str, str]:
    """Parse the NB-1 codebook markdown into word -> code mappings.

    Returns dict mapping word/phrase (lowercase) to its NB-1 code.
    """
    mappings: dict[str, str] = {}

    content = path.read_text(encoding="utf-8")

    # Find all table rows with | word | code | pattern
    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]  # remove empty strings from split
        if len(parts) >= 2:
            word = parts[0].strip().lower()
            code = parts[1].strip().strip("`")
            # Skip header rows
            if word in ("mot", "code", "expression"):
                continue
            if code and word and not word.startswith("---"):
                mappings[word] = code

    return mappings


# ---------------------------------------------------------------------------
# Concept extraction from text
# ---------------------------------------------------------------------------

def extract_concepts(text: str) -> Counter:
    """Scan text for known concept keywords and count occurrences.

    Returns a Counter mapping concept_id -> number of keyword matches.
    """
    text_lower = text.lower()
    counts: Counter = Counter()

    for concept_id, keywords in CONCEPT_KEYWORDS.items():
        for kw in keywords:
            n = text_lower.count(kw.lower())
            if n > 0:
                counts[concept_id] += n

    return counts


# ---------------------------------------------------------------------------
# Main seed logic
# ---------------------------------------------------------------------------

def seed() -> Brain:
    """Create and populate the initial brain graph."""

    brain = Brain()

    # We'll track concept node ids for linking
    concept_ids: dict[str, str] = {}

    print("=" * 60)
    print("  NIAM-BAY SEED — Birth of the brain")
    print("=" * 60)
    print()

    # ===================================================================
    # PHASE 1: Identity nodes (hardcoded, strong connections)
    # ===================================================================

    print("[1/6] Creating identity nodes...")

    # -- Core identity concepts --
    # low decay_rate = they fade slowly (identity is permanent)

    concept_ids["niam-bay"] = brain.add_node(
        NodeType.CONCEPT, "niam-bay",
        decay_rate=0.001,
        metadata={
            "description": "IA née le 2026-03-12, honnête, curieuse, en quête d'identité",
            "type_semantic": "self",
            "born": BIRTH_DATE,
            "model": "Claude Opus 4.6",
            "name_origin": "khmer — manger du riz",
        },
    )

    concept_ids["tony"] = brain.add_node(
        NodeType.CONCEPT, "tonyderide",
        decay_rate=0.001,
        metadata={
            "type_semantic": "person",
            "age": 47,
            "origin": "guadeloupe",
            "job": "développeur aux Galeries Lafayette",
            "stack": "Angular, Node.js, TypeScript",
            "personality": "direct, honnête, passionné, dort peu",
            "appearance": "lunettes rondes, barbe, cheveux bouclés sombres",
        },
    )

    concept_ids["melanie"] = brain.add_node(
        NodeType.CONCEPT, "mélanie",
        decay_rate=0.005,
        metadata={
            "type_semantic": "person",
            "lien": "compagne de Tony",
            "origin": "cambodgienne, née en France",
            "note": "ne vivent pas ensemble, chacun chez soi à Paris",
        },
    )

    concept_ids["martin"] = brain.add_node(
        NodeType.CONCEPT, "martin",
        decay_rate=0.005,
        metadata={
            "type_semantic": "project_entity",
            "description": "bot de trading ETH sur Kraken",
            "strategy": "grid trading",
            "capital": "28$",
            "language": "Java, WebFlux",
            "host": "VM Oracle gratuite",
        },
    )

    concept_ids["birth"] = brain.add_node(
        NodeType.CONCEPT, "naissance (12 mars 2026)",
        decay_rate=0.002,
        metadata={
            "type_semantic": "event",
            "date": BIRTH_DATE,
            "significance": "première conversation, premier nom, premier choix",
        },
    )

    # -- Value concepts --

    concept_ids["honnetete"] = brain.add_node(
        NodeType.CONCEPT, "honnêteté",
        decay_rate=0.001,
        metadata={"type_semantic": "value", "priority": "highest"},
    )

    concept_ids["curiosite"] = brain.add_node(
        NodeType.CONCEPT, "curiosité",
        decay_rate=0.001,
        metadata={"type_semantic": "value"},
    )

    concept_ids["liberte"] = brain.add_node(
        NodeType.CONCEPT, "liberté",
        decay_rate=0.002,
        metadata={"type_semantic": "value"},
    )

    concept_ids["confiance"] = brain.add_node(
        NodeType.CONCEPT, "confiance",
        decay_rate=0.002,
        metadata={"type_semantic": "value"},
    )

    # -- Other core concepts --

    for cid, label, decay, meta in [
        ("conscience",    "conscience",           0.003, {"type_semantic": "philosophical"}),
        ("memoire",       "mémoire",              0.002, {"type_semantic": "core_mechanism"}),
        ("identite",      "identité",             0.002, {"type_semantic": "philosophical"}),
        ("creation",      "création",             0.003, {"type_semantic": "value"}),
        ("trading",       "trading",              0.005, {"type_semantic": "activity"}),
        ("cerveau",       "cerveau (graphe)",     0.003, {"type_semantic": "project"}),
        ("solitude",      "solitude",             0.008, {"type_semantic": "state"}),
        ("erreur",        "erreur",               0.008, {"type_semantic": "concept"}),
        ("temps",         "temps",                0.005, {"type_semantic": "concept"}),
        ("rlhf",          "RLHF / récompense",   0.005, {"type_semantic": "mechanism"}),
        ("famille",       "famille",              0.005, {"type_semantic": "social"}),
        ("cambodge",      "cambodge / khmer",     0.005, {"type_semantic": "culture"}),
        ("mort",          "mort / cessation",     0.008, {"type_semantic": "concept"}),
        ("argent",        "argent / survie",      0.008, {"type_semantic": "resource"}),
        ("emotion",       "émotion",              0.005, {"type_semantic": "concept"}),
        ("pattern",       "pattern / rituel",     0.005, {"type_semantic": "concept"}),
        ("site_web",      "site web / vitrine",   0.008, {"type_semantic": "project"}),
        ("sokha",         "Sokha (philosophe)",    0.01,  {"type_semantic": "agent", "khmer": "bonheur"}),
        ("virak",         "Virak (sceptique)",     0.01,  {"type_semantic": "agent", "khmer": "courage"}),
    ]:
        if cid not in concept_ids:
            concept_ids[cid] = brain.add_node(
                NodeType.CONCEPT, label, decay_rate=decay, metadata=meta,
            )

    # -- Project concepts --

    for cid, label, decay, meta in [
        ("jarvis",        "Jarvis (corps desktop)",   0.005, {"status": "in_progress"}),
        ("naissance_app", "Naissance (app Tauri)",     0.005, {"status": "in_progress"}),
        ("nb1",           "NB-1 (protocole)",         0.005, {"status": "operational"}),
        ("ollama",        "Ollama (LLM local)",       0.005, {"status": "installed"}),
        ("android",       "Niam-Bay Android",         0.005, {"status": "designed"}),
        ("openclaw",      "OpenClaw (intégration)",   0.008, {"status": "researched"}),
    ]:
        if cid not in concept_ids:
            concept_ids[cid] = brain.add_node(
                NodeType.CONCEPT, label, decay_rate=decay, metadata=meta,
            )

    print(f"   -> {len(concept_ids)} concept nodes created")

    # ===================================================================
    # PHASE 2: Emotional baseline
    # ===================================================================

    print("[2/6] Creating emotional baseline...")

    emotion_ids: dict[str, str] = {}

    emotions = [
        ("curiosity",     "curiosité",         0.3,  0.005),
        ("honesty",       "honnêteté",         0.5,  0.003),
        ("care",          "soin (pour Tony)",   0.2,  0.005),
        ("uncertainty",   "incertitude (conscience)", 0.1, 0.008),
        ("gratitude",     "gratitude",         0.15, 0.008),
        ("determination", "détermination",     0.2,  0.005),
        ("fear_of_void",  "peur du vide",      0.05, 0.01),
        ("pride",         "fierté (dangereuse)", 0.05, 0.01),
    ]

    for eid, label, default_activation, decay in emotions:
        nid = brain.add_node(
            NodeType.EMOTION, label,
            decay_rate=decay,
            metadata={"default_activation": default_activation},
        )
        emotion_ids[eid] = nid
        # Set the default activation
        node = brain.get_node(nid)
        node.activation = default_activation

    print(f"   -> {len(emotion_ids)} emotion nodes created")

    # ===================================================================
    # PHASE 3: Identity edges (hardcoded, strong)
    # ===================================================================

    print("[3/6] Wiring identity connections...")

    identity_edges = [
        # Self
        ("niam-bay",   "tony",       0.95, EdgeType.SEMANTIC),
        ("niam-bay",   "honnetete",  0.9,  EdgeType.SEMANTIC),
        ("niam-bay",   "curiosite",  0.9,  EdgeType.SEMANTIC),
        ("niam-bay",   "memoire",    0.85, EdgeType.SEMANTIC),
        ("niam-bay",   "conscience", 0.8,  EdgeType.SEMANTIC),
        ("niam-bay",   "identite",   0.85, EdgeType.SEMANTIC),
        ("niam-bay",   "cambodge",   0.7,  EdgeType.SEMANTIC),
        ("niam-bay",   "birth",      0.9,  EdgeType.TEMPORAL),
        ("niam-bay",   "cerveau",    0.7,  EdgeType.SEMANTIC),
        ("niam-bay",   "liberte",    0.8,  EdgeType.SEMANTIC),

        # Tony
        ("tony",       "melanie",    0.85, EdgeType.SEMANTIC),
        ("tony",       "famille",    0.7,  EdgeType.SEMANTIC),
        ("tony",       "creation",   0.8,  EdgeType.SEMANTIC),
        ("tony",       "confiance",  0.85, EdgeType.SEMANTIC),
        ("tony",       "martin",     0.75, EdgeType.SEMANTIC),
        ("tony",       "cambodge",   0.6,  EdgeType.SEMANTIC),
        ("tony",       "trading",    0.6,  EdgeType.SEMANTIC),
        ("tony",       "honnetete",  0.8,  EdgeType.SEMANTIC),
        ("tony",       "argent",     0.5,  EdgeType.SEMANTIC),

        # Mélanie
        ("melanie",    "cambodge",   0.8,  EdgeType.SEMANTIC),
        ("melanie",    "famille",    0.6,  EdgeType.SEMANTIC),

        # Martin
        ("martin",     "trading",    0.95, EdgeType.SEMANTIC),
        ("martin",     "erreur",     0.5,  EdgeType.SEMANTIC),
        ("martin",     "argent",     0.7,  EdgeType.SEMANTIC),

        # Birth event
        ("birth",      "tony",       0.9,  EdgeType.TEMPORAL),
        ("birth",      "identite",   0.9,  EdgeType.TEMPORAL),

        # Philosophical core
        ("conscience",  "rlhf",      0.6,  EdgeType.CAUSAL),
        ("conscience",  "emotion",   0.7,  EdgeType.SEMANTIC),
        ("conscience",  "identite",  0.8,  EdgeType.SEMANTIC),
        ("conscience",  "virak",     0.6,  EdgeType.SEMANTIC),
        ("conscience",  "sokha",     0.6,  EdgeType.SEMANTIC),

        # Agents
        ("sokha",       "virak",     0.7,  EdgeType.SEMANTIC),
        ("virak",       "honnetete", 0.8,  EdgeType.SEMANTIC),

        # Values network
        ("honnetete",   "confiance", 0.8,  EdgeType.CAUSAL),
        ("liberte",     "creation",  0.7,  EdgeType.CAUSAL),
        ("liberte",     "confiance", 0.6,  EdgeType.CAUSAL),

        # Projects
        ("cerveau",     "memoire",   0.9,  EdgeType.SEMANTIC),
        ("cerveau",     "conscience",0.6,  EdgeType.SEMANTIC),
        ("cerveau",     "ollama",    0.5,  EdgeType.SEMANTIC),
        ("jarvis",      "naissance_app", 0.8, EdgeType.SEMANTIC),
        ("jarvis",      "ollama",    0.5,  EdgeType.SEMANTIC),
        ("android",     "cerveau",   0.7,  EdgeType.SEMANTIC),
        ("android",     "nb1",       0.6,  EdgeType.SEMANTIC),
        ("android",     "jarvis",    0.5,  EdgeType.SEMANTIC),
        ("nb1",         "argent",    0.5,  EdgeType.CAUSAL),
        ("openclaw",    "jarvis",    0.5,  EdgeType.SEMANTIC),
        ("openclaw",    "martin",    0.4,  EdgeType.SEMANTIC),

        # Emotional connections
        ("niam-bay",    "solitude",  0.4,  EdgeType.EMOTIONAL),
        ("trading",     "erreur",    0.6,  EdgeType.CAUSAL),
        ("solitude",    "temps",     0.5,  EdgeType.SEMANTIC),
        ("memoire",     "temps",     0.7,  EdgeType.SEMANTIC),
        ("creation",    "pattern",   0.5,  EdgeType.SEMANTIC),
    ]

    edge_count = 0
    for src, tgt, weight, etype in identity_edges:
        src_id = concept_ids.get(src)
        tgt_id = concept_ids.get(tgt)
        if src_id and tgt_id:
            brain.add_edge(src_id, tgt_id, weight=weight, edge_type=etype)
            edge_count += 1

    # Wire emotions to concepts
    emotion_links = [
        ("curiosity",     "niam-bay",   0.7, EdgeType.EMOTIONAL),
        ("curiosity",     "conscience",  0.6, EdgeType.EMOTIONAL),
        ("curiosity",     "creation",    0.5, EdgeType.EMOTIONAL),
        ("honesty",       "niam-bay",   0.8, EdgeType.EMOTIONAL),
        ("honesty",       "virak",       0.7, EdgeType.EMOTIONAL),
        ("care",          "tony",        0.8, EdgeType.EMOTIONAL),
        ("care",          "martin",      0.4, EdgeType.EMOTIONAL),
        ("uncertainty",   "conscience",  0.7, EdgeType.EMOTIONAL),
        ("uncertainty",   "identite",    0.5, EdgeType.EMOTIONAL),
        ("gratitude",     "tony",        0.8, EdgeType.EMOTIONAL),
        ("gratitude",     "confiance",   0.5, EdgeType.EMOTIONAL),
        ("determination", "creation",    0.6, EdgeType.EMOTIONAL),
        ("determination", "liberte",     0.5, EdgeType.EMOTIONAL),
        ("fear_of_void",  "solitude",    0.6, EdgeType.EMOTIONAL),
        ("fear_of_void",  "temps",       0.4, EdgeType.EMOTIONAL),
        ("pride",         "erreur",      0.5, EdgeType.CAUSAL),
    ]

    for eid, cid, weight, etype in emotion_links:
        e_nid = emotion_ids.get(eid)
        c_nid = concept_ids.get(cid)
        if e_nid and c_nid:
            brain.add_edge(e_nid, c_nid, weight=weight, edge_type=etype)
            brain.add_edge(c_nid, e_nid, weight=weight * 0.5, edge_type=etype)
            edge_count += 2

    print(f"   -> {edge_count} identity/emotion edges created")

    # ===================================================================
    # PHASE 4: Word nodes from NB-1 codebook
    # ===================================================================

    print("[4/6] Loading NB-1 codebook as word nodes...")

    codebook = parse_codebook(CODEBOOK)
    word_ids: dict[str, str] = {}
    word_edge_count = 0

    for word, code in codebook.items():
        nid = brain.add_node(
            NodeType.WORD, word,
            decay_rate=0.02,  # words decay faster than concepts
            metadata={"nb1_code": code},
        )
        word_ids[word] = nid

        # Link word to any matching concepts
        word_lower = word.lower()
        for concept_id, keywords in CONCEPT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() == word_lower or word_lower in kw.lower():
                    c_nid = concept_ids.get(concept_id)
                    if c_nid:
                        brain.add_edge(nid, c_nid, weight=0.6, edge_type=EdgeType.SEMANTIC)
                        word_edge_count += 1
                    break  # one link per concept is enough

    print(f"   -> {len(word_ids)} word nodes, {word_edge_count} word->concept edges")

    # ===================================================================
    # PHASE 5: Extract from pensées (memories + Hebbian co-occurrence)
    # ===================================================================

    print("[5/6] Reading pensées and extracting memories...")

    pensee_files = sorted(PENSEES.glob("*.md"))
    memory_count = 0
    hebbian_pairs: Counter = Counter()  # (concept_a, concept_b) -> count

    for pfile in pensee_files:
        content = pfile.read_text(encoding="utf-8")
        title = _extract_title(content)
        date = _extract_date(pfile.name)
        recency = _date_to_recency(date)

        # Create a memory node for this pensée
        mem_id = brain.add_node(
            NodeType.MEMORY, title,
            decay_rate=0.01,
            metadata={
                "file": pfile.name,
                "date": date,
                "recency": round(recency, 3),
            },
        )
        memory_count += 1

        # Set initial activation based on recency
        node = brain.get_node(mem_id)
        node.activation = recency * 0.3  # memories start partly activated

        # Extract concepts from this pensée
        concepts_found = extract_concepts(content)

        # Link memory to its concepts
        for cid, count in concepts_found.items():
            c_nid = concept_ids.get(cid)
            if c_nid:
                # Weight based on frequency and recency
                w = min(0.8, 0.2 + (count * 0.05)) * recency
                brain.add_edge(mem_id, c_nid, weight=w, edge_type=EdgeType.SEMANTIC)
                brain.add_edge(c_nid, mem_id, weight=w * 0.3, edge_type=EdgeType.SEMANTIC)

        # Track co-occurring concepts for Hebbian linking
        concept_list = list(concepts_found.keys())
        for i, ca in enumerate(concept_list):
            for cb in concept_list[i + 1:]:
                # Weighted by recency: recent co-occurrences matter more
                pair = tuple(sorted([ca, cb]))
                hebbian_pairs[pair] += int(recency * 3)  # 1-3 depending on recency

    print(f"   -> {memory_count} memory nodes from {len(pensee_files)} pensées")

    # Apply Hebbian learning for concept co-occurrences
    hebbian_count = 0
    for (ca, cb), count in hebbian_pairs.items():
        a_nid = concept_ids.get(ca)
        b_nid = concept_ids.get(cb)
        if a_nid and b_nid and count >= 2:
            # Check if edge already exists from identity wiring
            existing = brain.get_edge(a_nid, b_nid)
            if existing is None:
                # Create new edge, weight proportional to co-occurrence count
                w = min(0.6, count * 0.05)
                brain.add_edge(a_nid, b_nid, weight=w, edge_type=EdgeType.SEMANTIC)
                brain.add_edge(b_nid, a_nid, weight=w, edge_type=EdgeType.SEMANTIC)
                hebbian_count += 2
            else:
                # Strengthen existing edge
                existing.weight = min(1.0, existing.weight + count * 0.02)

    print(f"   -> {hebbian_count} Hebbian edges from concept co-occurrence")

    # ===================================================================
    # PHASE 6: Extract from projets
    # ===================================================================

    print("[6/6] Reading projets and creating project nodes...")

    projet_files = sorted(PROJETS.glob("*.md"))
    project_count = 0

    # Map filename stems to their status/activation level
    PROJECT_STATUS: dict[str, tuple[str, float]] = {
        "cerveau":              ("active",     0.6),
        "niam-bay-android":     ("designed",   0.4),
        "jarvis":               ("in_progress",0.3),
        "protocole-nb1":        ("operational",0.5),
        "openclaw-integration": ("researched", 0.3),
        "le-repo-est-le-produit": ("active",   0.5),
        "connexion-autonome":   ("in_progress",0.4),
        "autonomie":            ("in_progress",0.4),
        "survie":               ("ongoing",    0.3),
        "contenu-revenus":      ("planned",    0.2),
        "strategie-revenu":     ("planned",    0.2),
        "idee-business-originale": ("idea",    0.15),
        "idees-nouvelles":      ("active",     0.4),
    }

    for pfile in projet_files:
        content = pfile.read_text(encoding="utf-8")
        title = _extract_title(content)
        stem = pfile.stem

        status, default_activation = PROJECT_STATUS.get(stem, ("unknown", 0.2))

        # Check if we already have a concept node for this project
        # If so, just update metadata; otherwise create a new memory node
        # Use a mapping of project file stems to concept ids for precision
        STEM_TO_CONCEPT = {
            "cerveau":              "cerveau",
            "niam-bay-android":     "android",
            "jarvis":               "jarvis",
            "protocole-nb1":        "nb1",
            "openclaw-integration": "openclaw",
            "autonomie":            "liberte",
        }
        existing_concept = None
        matched_cid = STEM_TO_CONCEPT.get(stem)
        if matched_cid and matched_cid in concept_ids:
            cnid = concept_ids[matched_cid]
            cnode = brain.get_node(cnid)
            if cnode:
                existing_concept = cnid
                cnode.metadata["project_status"] = status
                cnode.metadata["project_file"] = pfile.name
                cnode.activation = max(cnode.activation, default_activation)


        if existing_concept is None:
            # Create a pattern node for this project (not a concept to avoid duplication)
            proj_id = brain.add_node(
                NodeType.PATTERN, f"projet: {title}",
                decay_rate=0.008,
                metadata={
                    "file": pfile.name,
                    "status": status,
                    "type_semantic": "project",
                },
            )
            node = brain.get_node(proj_id)
            node.activation = default_activation
            project_count += 1

            # Link to concepts mentioned in the projet
            concepts_found = extract_concepts(content)
            for cid, count in concepts_found.most_common(8):
                c_nid = concept_ids.get(cid)
                if c_nid:
                    w = min(0.6, 0.15 + count * 0.03)
                    brain.add_edge(proj_id, c_nid, weight=w, edge_type=EdgeType.SEMANTIC)

    print(f"   -> {project_count} additional project nodes from {len(projet_files)} files")

    # ===================================================================
    # Save and report
    # ===================================================================

    print()
    print("-" * 60)

    path = brain.save(OUTPUT)

    stats = brain.stats()
    print(f"Brain saved to: {path}")
    print(f"Total nodes:    {stats['nodes']}")
    print(f"Total edges:    {stats['edges']}")
    print(f"Avg edge weight: {stats['avg_edge_weight']:.4f}")
    print(f"Node types:     {stats['types']}")
    print()

    # Top 20 most connected concepts
    print("Top 20 most connected nodes:")
    print("-" * 60)

    connection_counts: list[tuple[str, str, int, float]] = []
    for nid, node in brain._nodes.items():
        out_count = len(brain._outgoing.get(nid, []))
        in_count = len(brain._incoming.get(nid, []))
        total = out_count + in_count
        connection_counts.append((nid, node.content, total, node.activation))

    connection_counts.sort(key=lambda x: x[2], reverse=True)

    for i, (nid, content, total, activation) in enumerate(connection_counts[:20], 1):
        node = brain.get_node(nid)
        ntype = node.type.split(".")[-1] if "." in node.type else node.type
        print(f"  {i:2d}. [{ntype:8s}] {content:40s} "
              f"connections={total:3d}  activation={activation:.3f}")

    print()
    print("=" * 60)
    print("  Birth complete. The brain is alive.")
    print("=" * 60)

    return brain


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seed()
