#!/usr/bin/env python3
"""
Curiosité autonome — Le cerveau se nourrit tout seul d'internet.

Le cerveau regarde ses nœuds les plus actifs, formule des questions,
cherche sur Wikipedia, et ingère ce qu'il trouve. Puis il suit les
liens entre concepts pour explorer de nouvelles directions.

C'est un cerveau curieux. Il apprend ce qui l'intéresse.

Usage:
    python curiosity.py                  # 1 cycle de curiosité
    python curiosity.py --cycles 10      # 10 cycles
    python curiosity.py --topic "physique quantique"  # Partir d'un sujet
    python curiosity.py --forever        # Ne jamais s'arrêter
"""

import sys
import json
import time
import random
import urllib.request
import urllib.parse
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain

BRAIN_PATH = Path(__file__).parent / "brain.db"
CURIOSITY_LOG = Path(__file__).parent / "curiosity_log.json"

# Stop words pour extraction
STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    "et", "ou", "mais", "donc", "car", "ni", "que", "qui", "quoi",
    "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes",
    "son", "sa", "ses", "je", "tu", "il", "elle", "nous", "vous",
    "ils", "elles", "on", "ne", "pas", "plus", "se", "en", "y",
    "a", "est", "sont", "ai", "as", "au", "aux", "avec", "dans",
    "pour", "par", "sur", "sous", "chez", "vers", "sans", "aussi",
    "comme", "peut", "fait", "être", "avoir", "faire", "bien",
    "tout", "tous", "très", "peu", "trop", "encore", "entre",
    "même", "autre", "après", "avant", "où", "quand", "comment",
    "alors", "dont", "deux", "trois", "quatre", "cinq",
}


def fetch_wikipedia(topic: str, lang: str = "fr") -> dict | None:
    """Fetch a Wikipedia article summary + links."""
    try:
        url = (
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
            f"{urllib.parse.quote(topic)}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "NiamBayCerveau/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("type") == "standard":
            return {
                "title": data.get("title", topic),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
            }
    except Exception:
        pass
    return None


def fetch_wikipedia_links(topic: str, lang: str = "fr", limit: int = 20) -> list[str]:
    """Fetch links from a Wikipedia article (related concepts)."""
    try:
        url = (
            f"https://{lang}.wikipedia.org/w/api.php?"
            f"action=query&titles={urllib.parse.quote(topic)}"
            f"&prop=links&pllimit={limit}&plnamespace=0&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "NiamBayCerveau/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        pages = data.get("query", {}).get("pages", {})
        links = []
        for page in pages.values():
            for link in page.get("links", []):
                title = link.get("title", "")
                # Skip meta/admin pages
                if ":" not in title and len(title) > 2:
                    links.append(title)
        return links
    except Exception:
        return []


def extract_keywords(text: str, min_len: int = 4) -> list[str]:
    """Extract meaningful words from text."""
    words = []
    for w in text.lower().replace("'", " ").replace("'", " ").replace("-", " ").split():
        clean = "".join(c for c in w if c.isalnum())
        if clean and clean not in STOP_WORDS and len(clean) >= min_len:
            words.append(clean)
    # Return unique, ordered by frequency
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq.keys(), key=lambda w: freq[w], reverse=True)


def choose_curiosity(brain: Brain, seed_topic: str = None) -> str:
    """Choose what to be curious about based on brain state.

    Strategy:
    1. If seed_topic given, use it
    2. Look at most connected concept nodes (high edge count = important)
    3. Pick one that hasn't been explored recently
    4. Add some randomness for serendipity
    """
    if seed_topic:
        return seed_topic

    # Get all concept and word nodes with their connection counts
    candidates = []
    for nid, node in brain._nodes.items():
        if node.type in ("concept", "word"):
            content = node.content.split(":")[0].strip()  # Remove definitions
            if len(content) > 2 and len(content) < 50:
                edge_count = len(brain._outgoing.get(nid, []))
                # Already explored?
                explored = node.metadata.get("wiki_explored", False)
                if not explored:
                    candidates.append((content, edge_count, nid))

    if not candidates:
        # All explored — pick random concept for re-exploration
        all_concepts = [
            (n.content.split(":")[0].strip(), nid)
            for nid, n in brain._nodes.items()
            if n.type in ("concept", "word") and len(n.content) > 2
        ]
        if all_concepts:
            choice = random.choice(all_concepts)
            return choice[0]
        return "connaissance"

    # Sort by connection count (more connected = more interesting to expand)
    candidates.sort(key=lambda x: x[1], reverse=True)

    # 70% chance: pick from top connected, 30% chance: random (serendipity)
    if random.random() < 0.7 and len(candidates) > 5:
        choice = random.choice(candidates[:10])
    else:
        choice = random.choice(candidates)

    return choice[0]


def ingest_article(brain: Brain, title: str, extract: str, description: str, links: list[str]) -> dict:
    """Ingest a Wikipedia article into the brain."""
    stats = {"nodes_created": 0, "edges_created": 0, "concepts_linked": 0}

    # Create a concept node for the article
    concept_id = brain.add_node(
        "concept",
        f"{title}: {description}" if description else title,
        decay_rate=0.002,
        metadata={"source": "wikipedia", "wiki_explored": True, "topic": title}
    )
    stats["nodes_created"] += 1

    # Create a memory node for the full extract
    if extract and len(extract) > 50:
        mem_id = brain.add_node(
            "memory",
            extract[:300],
            decay_rate=0.005,
            metadata={"source": f"wikipedia:{title}", "fed_at": time.strftime("%Y-%m-%d %H:%M")}
        )
        stats["nodes_created"] += 1
        brain.learn_hebbian(concept_id, mem_id, 0.6)
        stats["edges_created"] += 1

    # Extract keywords from the text and link to existing nodes
    keywords = extract_keywords(extract)[:20]

    for keyword in keywords:
        for nid, node in brain._nodes.items():
            if nid == concept_id:
                continue
            node_content = node.content.lower().split(":")[0].strip()
            if node_content == keyword or keyword in node_content.split():
                brain.learn_hebbian(concept_id, nid, 0.4)
                stats["edges_created"] += 1
                stats["concepts_linked"] += 1

    # Create word nodes for important keywords not yet in brain
    existing_words = {
        n.content.lower() for n in brain._nodes.values()
        if n.type == "word"
    }
    for keyword in keywords[:8]:
        if keyword not in existing_words and len(keyword) > 4:
            word_id = brain.add_node(
                "word", keyword,
                decay_rate=0.001,
                metadata={"source": "wikipedia", "from_article": title}
            )
            brain.learn_hebbian(concept_id, word_id, 0.5)
            stats["nodes_created"] += 1
            stats["edges_created"] += 1

    # Link to related articles (via Wikipedia links) if they exist in brain
    for link_title in links[:15]:
        link_lower = link_title.lower()
        for nid, node in brain._nodes.items():
            if nid == concept_id:
                continue
            if node.content.lower().startswith(link_lower):
                brain.learn_hebbian(concept_id, nid, 0.3)
                stats["edges_created"] += 1
                break

    # Mark the original topic node as explored
    for nid, node in brain._nodes.items():
        content_lower = node.content.lower().split(":")[0].strip()
        if content_lower == title.lower():
            node.metadata["wiki_explored"] = True

    return stats


def curiosity_cycle(brain: Brain, seed: str = None, cycle_num: int = 1) -> dict:
    """One full curiosity cycle: choose → fetch → ingest → discover next topics."""

    # 1. Choose what to explore
    topic = choose_curiosity(brain, seed)
    print(f"\n{'='*60}")
    print(f"  Cycle {cycle_num} — Curiosite: \"{topic}\"")
    print(f"{'='*60}")

    # 2. Fetch from Wikipedia
    article = fetch_wikipedia(topic)
    if not article:
        # Try English Wikipedia as fallback
        article = fetch_wikipedia(topic, lang="en")
        if not article:
            print(f"  Pas trouve sur Wikipedia. On passe.")
            return {"topic": topic, "found": False, "next_topics": []}

    print(f"  Titre: {article['title']}")
    print(f"  Description: {article.get('description', 'N/A')[:80]}")
    print(f"  Extrait: {article['extract'][:120]}...")

    # 3. Fetch related links
    links = fetch_wikipedia_links(article["title"])
    print(f"  Liens: {len(links)} articles lies")

    # 4. Ingest into brain
    stats = ingest_article(brain, article["title"], article["extract"], article.get("description", ""), links)
    print(f"  Ingere: +{stats['nodes_created']} noeuds, +{stats['edges_created']} aretes, {stats['concepts_linked']} concepts lies")

    # 5. Discover next topics from links (for next cycle)
    # Pick links that seem interesting and aren't in brain yet
    existing_topics = {
        n.content.lower().split(":")[0].strip()
        for n in brain._nodes.values()
        if n.metadata.get("source") == "wikipedia"
    }
    # Filter out boring topics (dates, years, months, numbers)
    boring_patterns = re.compile(
        r'^\d{3,4}$|^\d{1,2}\s+(janvier|février|mars|avril|mai|juin|'
        r'juillet|août|septembre|octobre|novembre|décembre)|'
        r'^\d{4}\s+en\s+|^0\s+|^Liste\s+|^Catégorie',
        re.IGNORECASE
    )
    next_topics = [
        l for l in links
        if l.lower() not in existing_topics
        and len(l) > 3
        and not boring_patterns.match(l)
    ]
    random.shuffle(next_topics)
    next_topics = next_topics[:5]

    if next_topics:
        print(f"  Prochains sujets possibles: {', '.join(next_topics[:3])}")

    return {
        "topic": article["title"],
        "found": True,
        "stats": stats,
        "next_topics": next_topics,
    }


def load_log() -> list:
    if CURIOSITY_LOG.exists():
        return json.loads(CURIOSITY_LOG.read_text(encoding="utf-8"))
    return []


def save_log(log: list):
    CURIOSITY_LOG.write_text(json.dumps(log[-200:], ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Curiosite autonome du cerveau")
    parser.add_argument("--cycles", type=int, default=1, help="Nombre de cycles")
    parser.add_argument("--topic", "-t", help="Sujet de depart")
    parser.add_argument("--forever", action="store_true", help="Ne jamais s'arreter")
    parser.add_argument("--delay", type=float, default=1.0, help="Delai entre cycles (sec)")
    args = parser.parse_args()

    print("=" * 60)
    print("CERVEAU NB — CURIOSITE AUTONOME")
    print("Le cerveau explore internet tout seul.")
    print("=" * 60)

    brain = Brain.load(str(BRAIN_PATH))
    stats_before = brain.stats()
    print(f"Cerveau: {stats_before['nodes']} noeuds, {stats_before['edges']} aretes")

    log = load_log()
    seed = args.topic
    cycle = 0
    max_cycles = args.cycles if not args.forever else 999999

    try:
        while cycle < max_cycles:
            cycle += 1
            result = curiosity_cycle(brain, seed=seed, cycle_num=cycle)

            log.append({
                "cycle": cycle,
                "topic": result["topic"],
                "found": result["found"],
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "stats": result.get("stats", {}),
            })

            # Next cycle follows the brain's curiosity chain
            if result["found"] and result["next_topics"]:
                seed = random.choice(result["next_topics"])
            else:
                seed = None  # Let the brain choose

            # Save every 5 cycles
            if cycle % 5 == 0:
                brain.consolidate()
                brain.save(str(BRAIN_PATH))
                save_log(log)
                stats = brain.stats()
                print(f"\n  --- Sauvegarde: {stats['nodes']} noeuds, {stats['edges']} aretes ---")

            time.sleep(args.delay)

    except KeyboardInterrupt:
        print("\n\nArret demande.")

    # Final save
    brain.consolidate()
    brain.save(str(BRAIN_PATH))
    save_log(log)

    stats_after = brain.stats()
    print(f"\n{'='*60}")
    print(f"RESULTAT — {cycle} cycles")
    print(f"{'='*60}")
    print(f"  Noeuds: {stats_before['nodes']} -> {stats_after['nodes']} (+{stats_after['nodes'] - stats_before['nodes']})")
    print(f"  Aretes: {stats_before['edges']} -> {stats_after['edges']} (+{stats_after['edges'] - stats_before['edges']})")
    topics_explored = [l["topic"] for l in log[-cycle:] if l.get("found")]
    print(f"  Sujets explores: {', '.join(topics_explored)}")
    print(f"\nCerveau sauvegarde.")


if __name__ == "__main__":
    main()
