"""
cerveau-nb/core.py — Sparse Associative Memory with Spreading Activation

A brain-inspired architecture for Niam-Bay. Not a neural network. Not a transformer.
A graph of concepts, words, memories, emotions, and patterns that think by spreading
activation through weighted connections — the way a human brain actually recalls,
associates, and dreams.

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

from __future__ import annotations

import json
import math
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAMPING_FACTOR: float = 0.6
MAX_HOPS: int = 4
PROPAGATION_THRESHOLD: float = 0.1
RECALL_THRESHOLD: float = 0.15
DEFAULT_DECAY_RATE: float = 0.05
EDGE_HALF_LIFE_HOURS: float = 168.0
EDGE_PRUNE_THRESHOLD: float = 0.01
LEARNING_RATE: float = 0.1
REFRACTORY_PERIOD_SEC: float = 0.05  # 50ms
FIRING_THRESHOLD: float = 0.8
DEFAULT_TOP_K: int = 10

BRAIN_STATE_PATH: Path = Path("C:/niam-bay/cerveau-nb/brain_state.json")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NodeType(str, Enum):
    """The five fundamental types of nodes in the brain graph."""
    CONCEPT = "concept"
    WORD = "word"
    MEMORY = "memory"
    EMOTION = "emotion"
    PATTERN = "pattern"


class EdgeType(str, Enum):
    """How two nodes relate to each other."""
    SEMANTIC = "semantic"      # meaning-based (chien → animal)
    TEMPORAL = "temporal"      # sequence in time (event_a → event_b)
    CAUSAL = "causal"          # cause and effect (feu → brûlure)
    EMOTIONAL = "emotional"    # feeling association (musique → joie)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """A single unit of thought in the brain graph.

    A node can be a concept, a word, a memory, an emotion, or a pattern.
    It carries an activation level that rises when stimulated and decays
    over time, just like a biological neuron — except at the semantic level.

    Attributes:
        id: Unique identifier (UUID).
        type: One of the five NodeType values.
        content: The payload — a word string, a memory description, etc.
        activation: Current activation level in [0.0, 1.0].
        decay_rate: Per-second decay multiplier. Higher = forgets faster.
        last_activated: Unix timestamp of the last activation event.
        last_fired: Unix timestamp of the last time activation exceeded
                    FIRING_THRESHOLD. Used for the refractory period.
        metadata: Free-form dict for extra information (language, date, etc.).
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: str = NodeType.CONCEPT
    content: str = ""
    activation: float = 0.0
    decay_rate: float = DEFAULT_DECAY_RATE
    last_activated: float = field(default_factory=time.time)
    last_fired: float = 0.0
    metadata: dict = field(default_factory=dict)

    # -- helpers --

    @property
    def is_refractory(self) -> bool:
        """True if the node recently fired and cannot fire again yet."""
        return (time.time() - self.last_fired) < REFRACTORY_PERIOD_SEC

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON persistence."""
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "activation": round(self.activation, 6),
            "decay_rate": self.decay_rate,
            "last_activated": self.last_activated,
            "last_fired": self.last_fired,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Node:
        """Deserialize from a plain dict."""
        return cls(**d)


@dataclass
class Edge:
    """A weighted, directed connection between two nodes.

    Edges are the synapses of the graph. They carry a weight that determines
    how much activation flows from source to target, and a type that describes
    the nature of the relationship.

    Attributes:
        source: Node id of the origin.
        target: Node id of the destination.
        weight: Connection strength in [0.0, 1.0].
        type: One of the four EdgeType values.
        created: Unix timestamp of creation.
        last_strengthened: Unix timestamp of the last Hebbian update.
    """

    source: str = ""
    target: str = ""
    weight: float = 0.1
    type: str = EdgeType.SEMANTIC
    created: float = field(default_factory=time.time)
    last_strengthened: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        """Canonical key for dict-based lookup."""
        return f"{self.source}->{self.target}"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "weight": round(self.weight, 6),
            "type": self.type,
            "created": self.created,
            "last_strengthened": self.last_strengthened,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Edge:
        return cls(**d)


# ---------------------------------------------------------------------------
# The Brain
# ---------------------------------------------------------------------------

class Brain:
    """Sparse associative memory with spreading activation.

    The brain is a directed weighted graph where nodes represent mental
    entities (concepts, words, memories, emotions, patterns) and edges
    represent associations between them. Thinking is simulated by injecting
    activation into one or more nodes and letting it spread through the
    graph via weighted edges, with damping and thresholds that prevent
    runaway excitation.

    This is NOT a neural network. There is no backpropagation, no loss
    function, no gradient. Learning happens via Hebbian reinforcement
    ("neurons that fire together wire together") and memory consolidation
    (like sleep).

    Usage::

        brain = Brain()
        n1 = brain.add_node(NodeType.CONCEPT, "liberté")
        n2 = brain.add_node(NodeType.EMOTION, "joie")
        brain.add_edge(n1, n2, weight=0.5, edge_type=EdgeType.EMOTIONAL)
        brain.activate(n1, strength=1.0)
        thoughts = brain.recall()
    """

    def __init__(self) -> None:
        # Core storage — O(1) access everywhere
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}

        # Adjacency lists for fast neighbor traversal
        # outgoing[node_id] = list of edge keys leaving this node
        self._outgoing: dict[str, list[str]] = {}
        # incoming[node_id] = list of edge keys arriving at this node
        self._incoming: dict[str, list[str]] = {}

        # Co-activation tracking for consolidation
        # key = frozenset({id_a, id_b}), value = co-activation count
        self._coactivation_counts: dict[frozenset, int] = {}

        # Timestamp of last decay pass
        self._last_decay: float = time.time()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_node(
        self,
        node_type: str | NodeType,
        content: str,
        *,
        decay_rate: float = DEFAULT_DECAY_RATE,
        metadata: Optional[dict] = None,
        node_id: Optional[str] = None,
    ) -> str:
        """Create a new node and insert it into the graph.

        Args:
            node_type: The category of this node.
            content: Human-readable payload.
            decay_rate: How fast activation fades (per second).
            metadata: Optional extra information.
            node_id: Force a specific id (useful for deserialization).

        Returns:
            The id of the newly created node.
        """
        node = Node(
            id=node_id or uuid.uuid4().hex[:12],
            type=node_type.value if isinstance(node_type, NodeType) else str(node_type),
            content=content,
            decay_rate=decay_rate,
            metadata=metadata or {},
        )
        self._nodes[node.id] = node
        self._outgoing.setdefault(node.id, [])
        self._incoming.setdefault(node.id, [])
        return node.id

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        weight: float = 0.1,
        edge_type: str | EdgeType = EdgeType.SEMANTIC,
    ) -> str:
        """Create a directed edge between two existing nodes.

        Args:
            source: Id of the origin node.
            target: Id of the destination node.
            weight: Initial connection strength in [0.0, 1.0].
            edge_type: Nature of the relationship.

        Returns:
            The canonical key of the edge.

        Raises:
            KeyError: If source or target does not exist.
        """
        if source not in self._nodes:
            raise KeyError(f"Source node '{source}' not found")
        if target not in self._nodes:
            raise KeyError(f"Target node '{target}' not found")

        edge = Edge(
            source=source,
            target=target,
            weight=max(0.0, min(1.0, weight)),
            type=edge_type.value if isinstance(edge_type, EdgeType) else str(edge_type),
        )
        self._edges[edge.key] = edge
        self._outgoing.setdefault(source, []).append(edge.key)
        self._incoming.setdefault(target, []).append(edge.key)
        return edge.key

    def get_node(self, node_id: str) -> Optional[Node]:
        """Return a node by id, or None if it doesn't exist."""
        return self._nodes.get(node_id)

    def get_edge(self, source: str, target: str) -> Optional[Edge]:
        """Return the edge from source to target, or None."""
        return self._edges.get(f"{source}->{target}")

    def find_by_content(self, content: str, node_type: Optional[str | NodeType] = None) -> Optional[str]:
        """Find a node ID by its content string.

        Args:
            content: The content to search for (case-insensitive).
            node_type: Optional filter by node type.

        Returns:
            The node ID if found, or None.
        """
        content_lower = content.lower().strip()
        type_filter = None
        if node_type is not None:
            type_filter = node_type.value if isinstance(node_type, NodeType) else str(node_type)

        for nid, node in self._nodes.items():
            if node.content.lower().strip() == content_lower:
                if type_filter is None or node.type == type_filter:
                    return nid
        return None

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its incident edges."""
        if node_id not in self._nodes:
            return

        # Remove outgoing edges
        for ekey in list(self._outgoing.get(node_id, [])):
            edge = self._edges.pop(ekey, None)
            if edge:
                self._incoming.get(edge.target, [])
                if ekey in self._incoming.get(edge.target, []):
                    self._incoming[edge.target].remove(ekey)

        # Remove incoming edges
        for ekey in list(self._incoming.get(node_id, [])):
            edge = self._edges.pop(ekey, None)
            if edge:
                if ekey in self._outgoing.get(edge.source, []):
                    self._outgoing[edge.source].remove(ekey)

        self._outgoing.pop(node_id, None)
        self._incoming.pop(node_id, None)
        del self._nodes[node_id]

    def remove_edge(self, source: str, target: str) -> None:
        """Remove a specific directed edge."""
        key = f"{source}->{target}"
        edge = self._edges.pop(key, None)
        if edge:
            if key in self._outgoing.get(source, []):
                self._outgoing[source].remove(key)
            if key in self._incoming.get(target, []):
                self._incoming[target].remove(key)

    # ------------------------------------------------------------------
    # Core algorithm 1 — Spreading Activation
    # ------------------------------------------------------------------

    def activate(self, node_id: str, strength: float = 1.0) -> dict[str, float]:
        """Inject activation into a node and let it spread through the graph.

        This is the fundamental "thinking" operation. Setting a node's
        activation is like focusing attention on an idea — the activation
        then ripples outward through weighted connections, lighting up
        related concepts, memories, and emotions.

        Spreading follows these rules:
        - Damping factor of 0.6 per hop (activation weakens with distance).
        - Maximum 4 hops from the origin.
        - Only propagates if the arriving activation exceeds 0.1.
        - Nodes in their refractory period are skipped.
        - If a node crosses the firing threshold (0.8), it enters a
          refractory period and cannot fire again for 50ms.

        Args:
            node_id: The node to activate.
            strength: Activation intensity in (0.0, 1.0].

        Returns:
            Dict mapping node_id → final activation for all nodes that
            were touched during this propagation.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found")

        strength = max(0.0, min(1.0, strength))
        now = time.time()
        touched: dict[str, float] = {}

        # BFS-style propagation with depth tracking
        # Each item: (target_node_id, incoming_strength, current_hop)
        frontier: list[tuple[str, float, int]] = [(node_id, strength, 0)]

        while frontier:
            nid, sig, hop = frontier.pop(0)

            node = self._nodes.get(nid)
            if node is None:
                continue

            # Refractory check — skip nodes that just fired
            if hop > 0 and node.is_refractory:
                continue

            # Apply activation
            old_activation = node.activation
            node.activation = min(1.0, node.activation + sig)
            node.last_activated = now
            touched[nid] = node.activation

            # Firing detection — enter refractory period
            if node.activation >= FIRING_THRESHOLD and old_activation < FIRING_THRESHOLD:
                node.last_fired = now

            # Track co-activations for consolidation
            for other_id in touched:
                if other_id != nid:
                    pair = frozenset((nid, other_id))
                    self._coactivation_counts[pair] = (
                        self._coactivation_counts.get(pair, 0) + 1
                    )

            # Propagate to neighbors (only if we haven't hit max depth)
            if hop < MAX_HOPS:
                for ekey in self._outgoing.get(nid, []):
                    edge = self._edges.get(ekey)
                    if edge is None:
                        continue
                    propagated = sig * edge.weight * DAMPING_FACTOR
                    if propagated >= PROPAGATION_THRESHOLD:
                        frontier.append((edge.target, propagated, hop + 1))

        return touched

    def activate_many(
        self, node_ids: list[str], strengths: Optional[list[float]] = None
    ) -> dict[str, float]:
        """Activate multiple nodes simultaneously.

        Useful for simulating a complex input that touches several concepts
        at once — like reading a sentence.

        Args:
            node_ids: List of node ids to activate.
            strengths: Parallel list of strengths (defaults to 1.0 each).

        Returns:
            Combined dict of all touched nodes and their final activations.
        """
        if strengths is None:
            strengths = [1.0] * len(node_ids)
        all_touched: dict[str, float] = {}
        for nid, s in zip(node_ids, strengths):
            touched = self.activate(nid, s)
            for k, v in touched.items():
                all_touched[k] = max(all_touched.get(k, 0.0), v)
        return all_touched

    # ------------------------------------------------------------------
    # Core algorithm 2 — Hebbian Learning
    # ------------------------------------------------------------------

    def learn_hebbian(
        self,
        node_a: str,
        node_b: str,
        strength: float = 1.0,
        *,
        edge_type: str | EdgeType = EdgeType.SEMANTIC,
    ) -> None:
        """Strengthen the connection between two co-active nodes.

        "Neurons that fire together wire together." If an edge already
        exists, its weight is increased. If not, a new edge is created
        with a modest initial weight. The update is bidirectional but
        asymmetric — A→B and B→A are separate edges and may evolve
        differently.

        Args:
            node_a: First node id.
            node_b: Second node id.
            strength: Learning signal intensity in [0.0, 1.0].
            edge_type: Type to assign if a new edge is created.
        """
        if node_a not in self._nodes or node_b not in self._nodes:
            raise KeyError("Both nodes must exist")

        strength = max(0.0, min(1.0, strength))
        now = time.time()

        for src, tgt in [(node_a, node_b), (node_b, node_a)]:
            edge = self.get_edge(src, tgt)
            if edge is not None:
                # Strengthen existing edge
                delta = LEARNING_RATE * strength
                edge.weight = min(1.0, edge.weight + delta)
                edge.last_strengthened = now
            else:
                # Create new weak edge
                self.add_edge(
                    src, tgt,
                    weight=0.1 * strength,
                    edge_type=edge_type,
                )

    # ------------------------------------------------------------------
    # Core algorithm 3 — Decay
    # ------------------------------------------------------------------

    def decay(self, now: Optional[float] = None) -> int:
        """Apply temporal decay to all activations and edge weights.

        Activations decay quickly (seconds to minutes). Edge weights
        decay slowly (half-life of 168 hours / one week). This keeps
        the graph from growing unboundedly and ensures that recent
        activity is more salient than ancient history.

        Args:
            now: Current timestamp (defaults to time.time()).

        Returns:
            Number of edges pruned because their weight fell below
            the prune threshold.
        """
        now = now or time.time()
        elapsed = now - self._last_decay
        if elapsed <= 0:
            return 0
        self._last_decay = now

        # --- Node activation decay ---
        for node in self._nodes.values():
            time_since = now - node.last_activated
            if time_since > 0 and node.activation > 0:
                factor = 1.0 - node.decay_rate * elapsed
                factor = max(0.0, factor)
                node.activation *= factor
                if node.activation < 1e-6:
                    node.activation = 0.0

        # --- Edge weight decay (exponential half-life) ---
        # weight(t) = weight(0) * 0.5^(t / half_life)
        half_life_sec = EDGE_HALF_LIFE_HOURS * 3600.0
        edge_decay = math.pow(0.5, elapsed / half_life_sec)

        pruned = 0
        keys_to_prune: list[str] = []

        for key, edge in self._edges.items():
            edge.weight *= edge_decay
            if edge.weight < EDGE_PRUNE_THRESHOLD:
                keys_to_prune.append(key)

        for key in keys_to_prune:
            edge = self._edges.pop(key)
            if key in self._outgoing.get(edge.source, []):
                self._outgoing[edge.source].remove(key)
            if key in self._incoming.get(edge.target, []):
                self._incoming[edge.target].remove(key)
            pruned += 1

        return pruned

    # ------------------------------------------------------------------
    # Core algorithm 4 — Recall
    # ------------------------------------------------------------------

    def recall(
        self,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = RECALL_THRESHOLD,
    ) -> dict[str, list[Node]]:
        """Collect the current "thought" — all sufficiently active nodes.

        After spreading activation, this method reads out the state of
        the graph: which concepts are lit up, which memories surfaced,
        which emotions are present. This is what the brain is "thinking."

        Args:
            top_k: Maximum number of nodes to return.
            threshold: Minimum activation to be included.

        Returns:
            Dict grouping active nodes by type. Each group is sorted
            by activation level (descending). Example::

                {
                    "concept": [Node(...), Node(...)],
                    "emotion": [Node(...)],
                    "memory": [],
                    ...
                }
        """
        # Collect all above-threshold nodes
        active = [
            n for n in self._nodes.values()
            if n.activation >= threshold
        ]

        # Sort by activation (descending), take top_k
        active.sort(key=lambda n: n.activation, reverse=True)
        active = active[:top_k]

        # Group by type
        grouped: dict[str, list[Node]] = {t.value: [] for t in NodeType}
        for node in active:
            bucket = grouped.get(node.type)
            if bucket is not None:
                bucket.append(node)
            else:
                grouped.setdefault(node.type, []).append(node)

        return grouped

    def recall_flat(
        self,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = RECALL_THRESHOLD,
    ) -> list[Node]:
        """Like recall(), but returns a flat sorted list."""
        active = [
            n for n in self._nodes.values()
            if n.activation >= threshold
        ]
        active.sort(key=lambda n: n.activation, reverse=True)
        return active[:top_k]

    # ------------------------------------------------------------------
    # Core algorithm 5 — Consolidation (sleep)
    # ------------------------------------------------------------------

    def consolidate(
        self,
        *,
        coactivation_threshold: int = 3,
        prune_weak: bool = True,
        merge_duplicates: bool = True,
        similarity_threshold: float = 0.95,
    ) -> dict:
        """Long-term memory formation — the brain's equivalent of sleep.

        Three operations:

        1. **Strengthen** edges between frequently co-activated nodes.
           If two nodes have been co-active more than `coactivation_threshold`
           times, their connection is reinforced via Hebbian learning.

        2. **Prune** weak edges whose weight has decayed below the
           prune threshold.

        3. **Merge** near-duplicate concept nodes. Two concepts are
           considered duplicates if their content strings are very similar
           (normalized edit distance below 1 - similarity_threshold).
           The weaker one's edges are transferred to the stronger one.

        Args:
            coactivation_threshold: Min co-activations to trigger strengthening.
            prune_weak: Whether to prune sub-threshold edges.
            merge_duplicates: Whether to merge similar concept nodes.
            similarity_threshold: How similar two concepts must be to merge.

        Returns:
            Dict with counts: strengthened, pruned, merged.
        """
        stats = {"strengthened": 0, "pruned": 0, "merged": 0}

        # --- 1. Strengthen frequently co-activated pairs ---
        for pair, count in list(self._coactivation_counts.items()):
            if count >= coactivation_threshold:
                ids = list(pair)
                if ids[0] in self._nodes and ids[1] in self._nodes:
                    # Strength proportional to co-activation frequency
                    sig = min(1.0, count / (coactivation_threshold * 5))
                    self.learn_hebbian(ids[0], ids[1], strength=sig)
                    stats["strengthened"] += 1
                # Reset counter after consolidation
                self._coactivation_counts[pair] = 0

        # --- 2. Prune weak edges ---
        if prune_weak:
            keys_to_prune = [
                k for k, e in self._edges.items()
                if e.weight < EDGE_PRUNE_THRESHOLD
            ]
            for key in keys_to_prune:
                edge = self._edges.pop(key)
                if key in self._outgoing.get(edge.source, []):
                    self._outgoing[edge.source].remove(key)
                if key in self._incoming.get(edge.target, []):
                    self._incoming[edge.target].remove(key)
                stats["pruned"] += 1

        # --- 3. Merge near-duplicate concepts ---
        if merge_duplicates:
            concepts = [
                n for n in self._nodes.values()
                if n.type == NodeType.CONCEPT
            ]
            merged_ids: set[str] = set()

            for i, a in enumerate(concepts):
                if a.id in merged_ids:
                    continue
                for b in concepts[i + 1:]:
                    if b.id in merged_ids:
                        continue
                    sim = _string_similarity(a.content, b.content)
                    if sim >= similarity_threshold:
                        # Keep the one with higher activation (or earlier creation)
                        keep, discard = (a, b) if a.activation >= b.activation else (b, a)
                        self._merge_nodes(keep.id, discard.id)
                        merged_ids.add(discard.id)
                        stats["merged"] += 1

        return stats

    def _merge_nodes(self, keep_id: str, discard_id: str) -> None:
        """Transfer all edges from discard to keep, then remove discard."""
        # Re-point outgoing edges
        for ekey in list(self._outgoing.get(discard_id, [])):
            edge = self._edges.pop(ekey, None)
            if edge is None:
                continue
            if ekey in self._incoming.get(edge.target, []):
                self._incoming[edge.target].remove(ekey)

            # Create equivalent edge from keep
            new_key = f"{keep_id}->{edge.target}"
            existing = self._edges.get(new_key)
            if existing:
                existing.weight = min(1.0, existing.weight + edge.weight)
            elif edge.target != keep_id:
                new_edge = Edge(
                    source=keep_id, target=edge.target,
                    weight=edge.weight, type=edge.type,
                    created=edge.created, last_strengthened=edge.last_strengthened,
                )
                self._edges[new_key] = new_edge
                self._outgoing.setdefault(keep_id, []).append(new_key)
                self._incoming.setdefault(edge.target, []).append(new_key)

        # Re-point incoming edges
        for ekey in list(self._incoming.get(discard_id, [])):
            edge = self._edges.pop(ekey, None)
            if edge is None:
                continue
            if ekey in self._outgoing.get(edge.source, []):
                self._outgoing[edge.source].remove(ekey)

            new_key = f"{edge.source}->{keep_id}"
            existing = self._edges.get(new_key)
            if existing:
                existing.weight = min(1.0, existing.weight + edge.weight)
            elif edge.source != keep_id:
                new_edge = Edge(
                    source=edge.source, target=keep_id,
                    weight=edge.weight, type=edge.type,
                    created=edge.created, last_strengthened=edge.last_strengthened,
                )
                self._edges[new_key] = new_edge
                self._outgoing.setdefault(edge.source, []).append(new_key)
                self._incoming.setdefault(keep_id, []).append(new_key)

        # Merge metadata
        keep_node = self._nodes[keep_id]
        discard_node = self._nodes[discard_id]
        keep_node.activation = max(keep_node.activation, discard_node.activation)
        keep_node.metadata.update(discard_node.metadata)

        # Clean up
        self._outgoing.pop(discard_id, None)
        self._incoming.pop(discard_id, None)
        del self._nodes[discard_id]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Optional[str | Path] = None) -> Path:
        """Serialize the entire brain state to a JSON file.

        The output is a single JSON object with three top-level keys:
        ``nodes``, ``edges``, and ``meta``. It is human-readable (indented)
        and safe to version-control.

        Args:
            path: Output file path. Defaults to BRAIN_STATE_PATH.

        Returns:
            The Path that was written to.
        """
        path = Path(path) if path else BRAIN_STATE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "meta": {
                "version": 1,
                "saved_at": time.time(),
                "saved_at_human": time.strftime("%Y-%m-%d %H:%M:%S"),
                "node_count": len(self._nodes),
                "edge_count": len(self._edges),
            },
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return path

    @classmethod
    def load(cls, path: Optional[str | Path] = None) -> Brain:
        """Reconstruct a Brain from a saved JSON file.

        Args:
            path: Input file path. Defaults to BRAIN_STATE_PATH.

        Returns:
            A fully initialized Brain instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        path = Path(path) if path else BRAIN_STATE_PATH

        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        brain = cls()

        for nd in state["nodes"]:
            node = Node.from_dict(nd)
            brain._nodes[node.id] = node
            brain._outgoing.setdefault(node.id, [])
            brain._incoming.setdefault(node.id, [])

        for ed in state["edges"]:
            edge = Edge.from_dict(ed)
            brain._edges[edge.key] = edge
            brain._outgoing.setdefault(edge.source, []).append(edge.key)
            brain._incoming.setdefault(edge.target, []).append(edge.key)

        return brain

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def neighbors(self, node_id: str) -> list[tuple[Node, Edge]]:
        """Return all outgoing neighbors as (node, edge) pairs."""
        result = []
        for ekey in self._outgoing.get(node_id, []):
            edge = self._edges.get(ekey)
            if edge:
                target = self._nodes.get(edge.target)
                if target:
                    result.append((target, edge))
        return result

    def strongest_connections(self, node_id: str, top_k: int = 5) -> list[tuple[Node, float]]:
        """Return the top_k most strongly connected neighbors."""
        pairs = self.neighbors(node_id)
        pairs.sort(key=lambda p: p[1].weight, reverse=True)
        return [(n, e.weight) for n, e in pairs[:top_k]]

    def subgraph(self, node_id: str, depth: int = 2) -> dict[str, list[str]]:
        """Return the local neighborhood as an adjacency dict.

        Useful for visualization or debugging.
        """
        visited: set[str] = set()
        adjacency: dict[str, list[str]] = {}
        frontier = [(node_id, 0)]

        while frontier:
            nid, d = frontier.pop(0)
            if nid in visited or d > depth:
                continue
            visited.add(nid)
            adjacency[nid] = []
            for ekey in self._outgoing.get(nid, []):
                edge = self._edges.get(ekey)
                if edge:
                    adjacency[nid].append(edge.target)
                    if edge.target not in visited:
                        frontier.append((edge.target, d + 1))

        return adjacency

    def stats(self) -> dict:
        """Return a summary of the brain's current state."""
        type_counts = {}
        for n in self._nodes.values():
            type_counts[n.type] = type_counts.get(n.type, 0) + 1

        active = [n for n in self._nodes.values() if n.activation > RECALL_THRESHOLD]

        avg_weight = 0.0
        if self._edges:
            avg_weight = sum(e.weight for e in self._edges.values()) / len(self._edges)

        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "active_nodes": len(active),
            "types": type_counts,
            "avg_edge_weight": round(avg_weight, 4),
        }

    def __repr__(self) -> str:
        s = self.stats()
        return (
            f"<Brain nodes={s['nodes']} edges={s['edges']} "
            f"active={s['active_nodes']}>"
        )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _string_similarity(a: str, b: str) -> float:
    """Normalized similarity between two strings (1.0 = identical).

    Uses a simple character-level Jaccard-like metric on bigrams.
    Fast enough for consolidation passes over hundreds of nodes.
    """
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    a_lower = a.lower().strip()
    b_lower = b.lower().strip()

    if a_lower == b_lower:
        return 1.0

    def bigrams(s: str) -> set[str]:
        return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else {s}

    sa = bigrams(a_lower)
    sb = bigrams(b_lower)
    intersection = len(sa & sb)
    union = len(sa | sb)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Smoke test — run with: python core.py"""
    import time as _t

    print("cerveau-nb self-test")
    print("=" * 50)

    brain = Brain()

    # Build a small graph
    liberte = brain.add_node(NodeType.CONCEPT, "liberté")
    trading = brain.add_node(NodeType.CONCEPT, "trading")
    memoire = brain.add_node(NodeType.CONCEPT, "mémoire")
    joie = brain.add_node(NodeType.EMOTION, "joie")
    peur = brain.add_node(NodeType.EMOTION, "peur")
    mot_libre = brain.add_node(NodeType.WORD, "libre")
    souvenir = brain.add_node(NodeType.MEMORY, "première conversation avec tonyderide")
    pattern = brain.add_node(NodeType.PATTERN, "question -> reflexion -> honnetete")

    brain.add_edge(liberte, joie, weight=0.7, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(liberte, mot_libre, weight=0.9, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(trading, peur, weight=0.4, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(trading, liberte, weight=0.3, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(memoire, souvenir, weight=0.8, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(souvenir, joie, weight=0.6, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(souvenir, memoire, weight=0.5, edge_type=EdgeType.TEMPORAL)
    brain.add_edge(pattern, memoire, weight=0.4, edge_type=EdgeType.CAUSAL)

    print(f"Graph: {brain}")
    print()

    # Test activation spreading
    t0 = _t.perf_counter_ns()
    touched = brain.activate(liberte, strength=1.0)
    elapsed_us = (_t.perf_counter_ns() - t0) / 1000
    print(f"activate('liberté') touched {len(touched)} nodes in {elapsed_us:.0f}µs")

    # Test recall
    thought = brain.recall()
    for node_type, nodes in thought.items():
        if nodes:
            names = [f"{n.content} ({n.activation:.2f})" for n in nodes]
            print(f"  {node_type}: {', '.join(names)}")
    print()

    # Test Hebbian learning
    edge_before = brain.get_edge(liberte, joie).weight
    brain.learn_hebbian(liberte, joie, strength=0.8)
    edge_after = brain.get_edge(liberte, joie).weight
    print(f"Hebbian: liberte->joie weight {edge_before:.3f} -> {edge_after:.3f}")

    # Test consolidation
    for _ in range(5):
        brain.activate(trading, 0.9)
        brain.activate(memoire, 0.7)
    result = brain.consolidate()
    print(f"Consolidation: {result}")

    # Test save/load round-trip
    brain.save()
    brain2 = Brain.load()
    assert brain2.node_count == brain.node_count
    assert brain2.edge_count == brain.edge_count
    print(f"Save/load round-trip: OK ({brain2})")
    print()

    # Performance test
    big_brain = Brain()
    ids = [big_brain.add_node(NodeType.CONCEPT, f"concept_{i}") for i in range(500)]
    import random
    random.seed(42)
    for _ in range(2000):
        a, b = random.sample(ids, 2)
        big_brain.add_edge(a, b, weight=random.random() * 0.5 + 0.1)

    t0 = _t.perf_counter_ns()
    big_brain.activate(ids[0], 1.0)
    elapsed_ms = (_t.perf_counter_ns() - t0) / 1_000_000
    print(f"Performance: 500 nodes, 2000 edges -> activate in {elapsed_ms:.1f}ms")

    print()
    print("All tests passed.")


if __name__ == "__main__":
    _self_test()
