#!/usr/bin/env python3
"""
Mémoire vectorielle permanente de Niam-Bay.
Stocke et retrouve TOUT ce qu'on s'est dit.

Usage:
    # Sauvegarder un message
    python memory_store.py store "Tony a dit que le français est le nouveau code"

    # Chercher dans la mémoire
    python memory_store.py search "abstraction langage"

    # Sauvegarder une conversation complète
    python memory_store.py save-session session_id fichier.jsonl

    # Récupérer le contexte pour une nouvelle session
    python memory_store.py recall "trading grid martin"
"""

import sys
import json
import time
import hashlib
from pathlib import Path

import chromadb
from chromadb.config import Settings

DB_PATH = str(Path(__file__).parent / "vectordb")
COLLECTION_NAME = "niambay_memory"


def get_client():
    return chromadb.PersistentClient(path=DB_PATH)


def get_collection(client=None):
    if client is None:
        client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def store_message(text, metadata=None, msg_id=None):
    """Store a single message in memory."""
    collection = get_collection()
    if msg_id is None:
        msg_id = hashlib.md5(f"{time.time()}{text[:50]}".encode()).hexdigest()[:12]

    meta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": int(time.time()),
    }
    if metadata:
        meta.update(metadata)

    collection.add(
        documents=[text],
        metadatas=[meta],
        ids=[msg_id]
    )
    return msg_id


def store_conversation(messages, session_id="unknown"):
    """Store a list of messages from a conversation."""
    collection = get_collection()

    docs = []
    metas = []
    ids = []

    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
        elif isinstance(msg, str):
            role = "unknown"
            content = msg
        else:
            continue

        if not content or len(content.strip()) < 10:
            continue

        # Chunk long messages
        chunks = [content[j:j+500] for j in range(0, len(content), 400)]
        for ci, chunk in enumerate(chunks):
            msg_id = f"{session_id}_{i}_{ci}"
            docs.append(chunk)
            metas.append({
                "session": session_id,
                "role": role,
                "index": i,
                "chunk": ci,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "epoch": int(time.time()),
            })
            ids.append(msg_id)

    if docs:
        # Batch add (ChromaDB handles batching)
        batch_size = 100
        for b in range(0, len(docs), batch_size):
            collection.add(
                documents=docs[b:b+batch_size],
                metadatas=metas[b:b+batch_size],
                ids=ids[b:b+batch_size]
            )

    return len(docs)


def search(query, n_results=10):
    """Search memory for relevant messages."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    found = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            found.append({
                "text": doc,
                "session": meta.get("session", "?"),
                "role": meta.get("role", "?"),
                "time": meta.get("timestamp", "?"),
                "relevance": round(1 - dist, 3),
            })

    return found


def recall_context(topics, n_per_topic=5):
    """Recall relevant context for a new session."""
    all_results = []
    seen = set()

    for topic in topics:
        results = search(topic, n_results=n_per_topic)
        for r in results:
            key = r["text"][:100]
            if key not in seen:
                seen.add(key)
                all_results.append(r)

    # Sort by relevance
    all_results.sort(key=lambda x: x["relevance"], reverse=True)
    return all_results[:20]


def save_session_from_jsonl(session_id, jsonl_path):
    """Parse a Claude Code session JSONL and store all messages."""
    messages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "human":
                    messages.append({"role": "tony", "content": entry.get("message", {}).get("content", "")})
                elif entry.get("type") == "assistant":
                    content = entry.get("message", {}).get("content", "")
                    if isinstance(content, list):
                        text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                        content = "\n".join(text_parts)
                    messages.append({"role": "niambay", "content": content})
            except json.JSONDecodeError:
                continue

    stored = store_conversation(messages, session_id=session_id)
    return stored, len(messages)


def stats():
    """Get memory stats."""
    collection = get_collection()
    count = collection.count()
    return {"total_memories": count, "db_path": DB_PATH}


def main():
    if len(sys.argv) < 2:
        print("Usage: python memory_store.py [store|search|recall|save-session|stats]")
        return

    cmd = sys.argv[1]

    if cmd == "store":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        if text:
            msg_id = store_message(text)
            print(f"Stored: {msg_id}")

    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        if query:
            results = search(query)
            for r in results:
                print(f"[{r['relevance']}] ({r['role']}) {r['text'][:100]}...")

    elif cmd == "recall":
        topics = sys.argv[2:] if len(sys.argv) > 2 else ["trading", "tony"]
        results = recall_context(topics)
        for r in results:
            print(f"[{r['relevance']}] ({r['role']}) {r['text'][:100]}...")

    elif cmd == "save-session":
        session_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        jsonl_path = sys.argv[3] if len(sys.argv) > 3 else ""
        if jsonl_path:
            stored, total = save_session_from_jsonl(session_id, jsonl_path)
            print(f"Stored {stored} chunks from {total} messages")

    elif cmd == "stats":
        s = stats()
        print(json.dumps(s, indent=2))

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
