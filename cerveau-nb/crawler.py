#!/usr/bin/env python3
"""
cerveau-nb/crawler.py — Les yeux du cerveau

Crawl des flux RSS intelligents (trading, tech, IA, crypto) et nourrit
le cerveau-nb avec les concepts extraits. Pas de LLM. Pas de tokens.
Juste du RSS + extraction de mots-clés + le graphe.

Usage:
    python crawler.py              # un cycle de crawl
    python crawler.py --loop 900   # crawl toutes les 15 min
    python crawler.py --list       # affiche les feeds configurés

Authors: Niam-Bay
Created: 2026-04-05
"""

import feedparser
import hashlib
import json
import re
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CERVEAU_DIR = Path(__file__).resolve().parent
DB_PATH = CERVEAU_DIR / "brain.db"
CRAWL_STATE_PATH = CERVEAU_DIR / "crawl_state.json"
CRAWL_LOG_PATH = CERVEAU_DIR / "crawl_log.jsonl"

sys.path.insert(0, str(CERVEAU_DIR))
from core import Brain, NodeType, EdgeType


# ---------------------------------------------------------------------------
# Feeds — les sources du cerveau
# ---------------------------------------------------------------------------

FEEDS = {
    # Crypto / Trading
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "domain": "crypto",
        "lang": "en",
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/rss",
        "domain": "crypto",
        "lang": "en",
    },
    "decrypt": {
        "url": "https://decrypt.co/feed",
        "domain": "crypto",
        "lang": "en",
    },
    # Tech / IA
    "hackernews": {
        "url": "https://hnrss.org/frontpage",
        "domain": "tech",
        "lang": "en",
    },
    "arxiv_ai": {
        "url": "http://export.arxiv.org/rss/cs.AI",
        "domain": "ia",
        "lang": "en",
    },
    "anthropic": {
        "url": "https://www.anthropic.com/rss.xml",
        "domain": "ia",
        "lang": "en",
    },
    # Dev
    "devto": {
        "url": "https://dev.to/feed",
        "domain": "dev",
        "lang": "en",
    },
}


# ---------------------------------------------------------------------------
# NLP léger — extraction de concepts sans spaCy
# ---------------------------------------------------------------------------

STOP_EN = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "how", "when", "where", "why", "if", "then", "than", "but", "and",
    "or", "not", "no", "so", "as", "at", "by", "for", "from", "in",
    "into", "of", "on", "to", "up", "with", "about", "after", "before",
    "between", "under", "over", "through", "during", "each", "every",
    "all", "both", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "also", "just", "very", "too", "even",
    "new", "first", "last", "long", "great", "little", "just",
    "like", "back", "still", "well", "way", "get", "got", "make",
    "made", "say", "said", "go", "going", "come", "take", "know",
    "see", "think", "look", "want", "give", "use", "find", "tell",
    "ask", "work", "seem", "feel", "try", "leave", "call",
}

STOP_FR = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    "et", "ou", "mais", "donc", "car", "ni", "que", "qui", "quoi",
    "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes",
    "son", "sa", "ses", "je", "tu", "il", "elle", "nous", "vous",
    "ils", "elles", "on", "ne", "pas", "plus", "se", "en", "y",
    "est", "sont", "ai", "as", "au", "aux", "avec", "dans",
    "pour", "par", "sur", "sous", "chez", "vers", "sans",
}

# Concepts qu'on veut tracker spécifiquement
CRYPTO_ENTITIES = {
    "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "cardano", "ada",
    "polkadot", "dot", "chainlink", "link", "kraken", "binance", "coinbase",
    "defi", "nft", "stablecoin", "usdt", "usdc", "airdrop", "halving",
    "whale", "liquidation", "leverage", "futures", "spot", "grid",
}

TECH_ENTITIES = {
    "claude", "anthropic", "openai", "gpt", "llm", "transformer", "diffusion",
    "rust", "python", "typescript", "angular", "react", "wasm",
    "mcp", "agent", "rag", "embedding", "fine-tuning", "rlhf",
}


def normalize(text):
    """Lowercase, strip accents, clean."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def extract_concepts(title, summary="", lang="en"):
    """Extraire les concepts d'un titre + résumé d'article."""
    text = f"{title} {summary}"
    text = re.sub(r"<[^>]+>", " ", text)  # strip HTML
    text = re.sub(r"http\S+", "", text)    # strip URLs
    words = re.findall(r"[\w]+", text.lower())

    stopwords = STOP_EN if lang == "en" else STOP_FR
    concepts = []

    for w in words:
        if len(w) < 3 or w in stopwords or w.isdigit():
            continue
        # Priorité aux entités connues
        if w in CRYPTO_ENTITIES or w in TECH_ENTITIES:
            concepts.append(w)
        elif len(w) > 4:  # mots significatifs
            concepts.append(w)

    # Dédupliquer en gardant l'ordre
    seen = set()
    unique = []
    for c in concepts:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique[:20]  # max 20 concepts par article


def extract_sentiment(title):
    """Sentiment basique : positif/négatif/neutre basé sur des mots-clés."""
    title_lower = title.lower()
    pos = ["surge", "rally", "bullish", "soar", "gain", "breakout", "launch",
           "boom", "record", "milestone", "hausse", "monte", "profit"]
    neg = ["crash", "drop", "bearish", "plunge", "loss", "hack", "exploit",
           "scam", "ban", "fear", "baisse", "chute", "perte", "liquidation"]

    pos_count = sum(1 for w in pos if w in title_lower)
    neg_count = sum(1 for w in neg if w in title_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Cerveau integration
# ---------------------------------------------------------------------------

def load_brain():
    """Charger le cerveau depuis SQLite."""
    return Brain.load(str(DB_PATH))


def article_id(url, title):
    """Hash unique pour un article."""
    return hashlib.md5(f"{url}:{title}".encode()).hexdigest()[:12]


def load_crawl_state():
    """Charger l'état du crawl (articles déjà vus)."""
    if CRAWL_STATE_PATH.exists():
        return json.loads(CRAWL_STATE_PATH.read_text(encoding="utf-8"))
    return {"seen": {}, "last_crawl": None, "total_articles": 0, "total_concepts": 0}


def save_crawl_state(state):
    """Sauvegarder l'état du crawl."""
    CRAWL_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def log_crawl(entry):
    """Append une entrée au log de crawl."""
    with open(CRAWL_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def feed_article_to_brain(brain, concepts, title, domain, sentiment):
    """Nourrir le cerveau avec les concepts d'un article.

    1. Pour chaque concept, trouver ou créer le nœud
    2. Activer les nœuds
    3. Renforcer les liens entre concepts co-occurrents (Hebb)
    4. Créer un nœud mémoire pour l'article
    """
    node_ids = []

    for concept in concepts:
        # Chercher un nœud existant
        nid = brain.find_by_content(concept)
        if nid is None:
            # Créer un nouveau nœud concept
            nid = brain.add_node(
                NodeType.CONCEPT,
                concept,
                metadata={"source": "crawler", "domain": domain}
            )
        node_ids.append(nid)
        # Activer le nœud
        brain.activate(nid, 0.3)

    # Apprentissage hebbien entre tous les concepts co-occurrents
    for i, nid_a in enumerate(node_ids):
        for nid_b in node_ids[i + 1:]:
            brain.learn_hebbian(nid_a, nid_b, strength=0.3)

    # Créer un nœud mémoire pour l'article
    mem_content = f"[{domain}] {title[:100]}"
    mem_id = brain.add_node(
        NodeType.MEMORY,
        mem_content,
        metadata={
            "source": "crawler",
            "domain": domain,
            "sentiment": sentiment,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    )

    # Lier la mémoire aux concepts
    for nid in node_ids[:5]:  # max 5 liens par mémoire
        brain.learn_hebbian(mem_id, nid, strength=0.2)

    # Lier au domaine si le nœud existe
    domain_node = brain.find_by_content(domain)
    if domain_node:
        brain.learn_hebbian(mem_id, domain_node, strength=0.1)

    return mem_id, len(node_ids)


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

def crawl_one_cycle(brain, state, verbose=True):
    """Un cycle de crawl : tous les feeds, extraction, apprentissage."""
    new_articles = 0
    new_concepts = 0
    entries_by_domain = {}

    for feed_name, feed_info in FEEDS.items():
        url = feed_info["url"]
        domain = feed_info["domain"]
        lang = feed_info["lang"]

        if verbose:
            print(f"  [{feed_name}] fetching...", end="", flush=True)

        try:
            parsed = feedparser.parse(url)
            entries = parsed.entries[:10]  # max 10 articles par feed
        except Exception as e:
            if verbose:
                print(f" ERROR: {e}")
            continue

        feed_new = 0
        for entry in entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            aid = article_id(link, title)
            if aid in state["seen"]:
                continue

            # Extraire les concepts
            concepts = extract_concepts(title, summary, lang)
            if not concepts:
                state["seen"][aid] = time.time()
                continue

            sentiment = extract_sentiment(title)

            # Nourrir le cerveau
            mem_id, n_concepts = feed_article_to_brain(
                brain, concepts, title, domain, sentiment
            )

            # Logger
            log_crawl({
                "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "feed": feed_name,
                "title": title[:120],
                "concepts": concepts[:10],
                "sentiment": sentiment,
                "n_concepts": n_concepts,
            })

            state["seen"][aid] = time.time()
            state["total_articles"] = state.get("total_articles", 0) + 1
            state["total_concepts"] = state.get("total_concepts", 0) + n_concepts
            new_articles += 1
            new_concepts += n_concepts
            feed_new += 1

        if verbose:
            print(f" {feed_new} new")

        entries_by_domain[domain] = entries_by_domain.get(domain, 0) + feed_new

    state["last_crawl"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_crawl_state(state)

    return new_articles, new_concepts, entries_by_domain


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if "--list" in args:
        print("\n  Feeds configurés :")
        for name, info in FEEDS.items():
            print(f"    [{info['domain']}] {name}: {info['url']}")
        print(f"\n  Total: {len(FEEDS)} feeds")
        return

    loop_interval = None
    if "--loop" in args:
        idx = args.index("--loop")
        loop_interval = int(args[idx + 1]) if idx + 1 < len(args) else 900

    # Charger le cerveau
    print("  [Loading brain...]", end="\r")
    brain = load_brain()
    n_before = len(brain._nodes)
    print(f"  [Brain loaded — {n_before} nodes]")

    state = load_crawl_state()

    while True:
        print(f"\n  === Crawl {time.strftime('%H:%M:%S')} ===")
        t0 = time.time()

        new_art, new_conc, by_domain = crawl_one_cycle(brain, state)

        # Sauvegarder le cerveau
        brain.save(str(DB_PATH))
        n_after = len(brain._nodes)
        elapsed = time.time() - t0

        print(f"\n  +{new_art} articles, +{new_conc} concepts ({elapsed:.1f}s)")
        print(f"  Brain: {n_before} → {n_after} nodes")
        for domain, count in by_domain.items():
            print(f"    [{domain}] +{count}")

        if loop_interval is None:
            break

        print(f"\n  Next crawl in {loop_interval}s...")
        time.sleep(loop_interval)
        n_before = n_after


if __name__ == "__main__":
    main()
