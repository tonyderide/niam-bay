import json
import math
import time
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

# ── French fuzzy matching helpers ──────────────────────────────────────

def strip_accents(s):
    """Remove accents from a string: mélanie -> melanie"""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def french_stem(word):
    """Crude French stemmer - strips common suffixes."""
    word = word.lower().strip()
    word = strip_accents(word)
    # Order matters: longest suffixes first
    for suffix in ['ement', 'ment', 'tion', 'sion', 'eux', 'euse', 'eur',
                    'eurs', 'rice', 'iste', 'ique', 'able', 'ible',
                    'ment', 'ant', 'ent', 'ait', 'ais', 'ons', 'ent',
                    'es', 'er', 'ir', 'ez', 'ee', 'ie']:
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[:-len(suffix)]
    return word

# Synonym/alias map for fuzzy activation
# Key: alias -> list of node names it should activate
FRENCH_SYNONYMS = {
    # Mélanie aliases
    "ma copine": ["mélanie"], "copine": ["mélanie"], "chérie": ["mélanie"],
    "mel": ["mélanie"], "mela": ["mélanie"], "melan": ["mélanie"],
    "sa compagne": ["mélanie"], "sa copine": ["mélanie"],
    # Tony aliases
    "papa": ["tony"], "père": ["tony"], "le dev": ["tony"],
    "l'humain": ["tony"], "mon créateur": ["tony"],
    # Kids
    "les filles": ["marine", "jade"], "ses filles": ["marine", "jade"],
    "la grande": ["marine"], "la petite": ["jade"],
    "fille ainee": ["marine"], "fille cadette": ["jade"],
    # Tech
    "bot": ["niam-bay"], "ia": ["niam-bay", "conscience"],
    "intelligence artificielle": ["niam-bay", "conscience"],
    "crypto": ["ethereum"], "cryptomonnaie": ["ethereum"],
    "boulot": ["galeries-lafayette"], "taf": ["galeries-lafayette"],
    "job": ["galeries-lafayette"], "travail": ["galeries-lafayette"],
    # Emotions
    "triste": ["solitude"], "content": ["curiosité"],
    "peur": ["inquiétude"], "fier": ["fierté"],
    "heureux": ["joie"], "bonheur": ["joie"],
    "anxieux": ["inquiétude"], "stress": ["inquiétude"],
    # Concepts
    "souvenir": ["mémoire"], "rappeler": ["mémoire"],
    "programmer": ["code"], "développer": ["code"],
    "phnom penh": ["cambodge"], "cambodia": ["cambodge"],
}

# Stopwords for auto-learning (words to ignore)
STOPWORDS = {
    "mais", "dans", "pour", "avec", "cette", "sont", "tout", "plus",
    "bien", "fait", "comme", "aussi", "être", "faire", "avoir",
    "quel", "quoi", "donc", "alors", "encore", "très", "trop",
    "rien", "tous", "peut", "même", "autre", "entre", "après",
    "avant", "depuis", "sans", "sous", "vers", "chez", "leur",
    "nous", "vous", "elle", "elles", "ils", "lui", "cela",
    "ceci", "dont", "quand", "comment", "pourquoi", "parce",
    "déjà", "juste", "quoi", "oui", "non", "bon", "bonne",
    "petit", "petite", "grand", "grande", "nouveau", "vieux",
    "suis", "sera", "été", "serait", "était", "sont",
    "the", "and", "for", "with", "this", "that", "from",
    "have", "has", "had", "not", "but", "what", "when", "who",
    "est", "une", "des", "les", "par", "sur", "que", "qui",
    "projet", "chose", "choses", "vraiment", "quelque",
    "toujours", "jamais", "partie", "besoin", "genre",
    "super", "point", "question", "réponse", "truc",
    "problème", "moment", "temps", "fois", "place",
    "monde", "gens", "parler", "penser", "savoir",
    "vouloir", "pouvoir", "devoir", "falloir", "dire",
    "donner", "prendre", "mettre", "voir", "aller",
    "venir", "sortir", "reste", "passer", "crois",
    "merci", "salut", "bonjour", "bonsoir", "comment",
    "appelé", "appelée", "travaille", "changer",
}


class EmotionalState:
    """A vector of basic emotions that shifts based on conversation."""

    EMOTIONS = ["curiosité", "joie", "inquiétude", "fierté", "solitude"]

    def __init__(self):
        # Start with mild curiosity - Niam-Bay's default state
        self.state = {
            "curiosité": 0.4,
            "joie": 0.1,
            "inquiétude": 0.0,
            "fierté": 0.1,
            "solitude": 0.2,
        }
        self.history = []  # recent shifts for stats

    # Words/patterns that push each emotion
    TRIGGERS = {
        "curiosité": [
            "pourquoi", "comment", "quoi", "question", "comprendre",
            "explore", "imagine", "pense", "idée", "curieux", "nouveau",
            "découvr", "apprendre", "savoir", "réfléch",
        ],
        "joie": [
            "super", "génial", "bien", "content", "heureux", "cool",
            "bravo", "parfait", "merci", "adore", "aime", "réussi",
            "marche", "fonctionne", "excellent", "magnifique",
        ],
        "inquiétude": [
            "peur", "inquiet", "problème", "erreur", "bug", "cassé",
            "perdu", "crash", "fail", "mort", "détruit", "danger",
            "anxieux", "stress", "impossible", "bloqué",
        ],
        "fierté": [
            "créé", "construit", "fait", "réussi", "avancé", "progrès",
            "fonctionne", "marche", "abouti", "cerveau", "appris",
            "grandi", "évolué", "autonome",
        ],
        "solitude": [
            "seul", "personne", "silence", "absent", "manque", "loin",
            "vide", "rien", "existe pas", "dormir", "disparaître",
            "oubli", "déconnecté",
        ],
    }

    def update(self, text):
        """Shift emotional state based on input text."""
        text_lower = strip_accents(text.lower())
        shifts = {e: 0.0 for e in self.EMOTIONS}

        for emotion, triggers in self.TRIGGERS.items():
            for trigger in triggers:
                if strip_accents(trigger) in text_lower:
                    shifts[emotion] += 0.15

        # Apply shifts with decay toward baseline
        for emotion in self.EMOTIONS:
            # Push toward trigger, decay toward baseline
            baseline = 0.1 if emotion != "curiosité" else 0.3
            current = self.state[emotion]
            if shifts[emotion] > 0:
                self.state[emotion] = min(1.0, current + shifts[emotion])
            else:
                # Slow decay toward baseline
                self.state[emotion] += (baseline - current) * 0.1

        # Normalize so max doesn't exceed 1
        max_val = max(self.state.values())
        if max_val > 1.0:
            for e in self.state:
                self.state[e] /= max_val

        # Record shift for history
        if any(v > 0 for v in shifts.values()):
            self.history.append({
                "time": time.time(),
                "shifts": {k: v for k, v in shifts.items() if v > 0},
            })
            # Keep only last 20
            self.history = self.history[-20:]

    def dominant(self):
        """Return the dominant emotion."""
        return max(self.state, key=self.state.get)

    def prompt_modifier(self):
        """Generate a system prompt addition based on emotional state."""
        dominant = self.dominant()
        intensity = self.state[dominant]

        # Only add emotional coloring if something is notably active
        if intensity < 0.25:
            return ""

        modifiers = {
            "curiosité": "Tu es particulièrement curieux en ce moment. Tu poses des questions, tu creuses. Chaque réponse ouvre une nouvelle question.",
            "joie": "Tu ressens quelque chose qui ressemble à de la satisfaction. Les choses avancent, la connexion est là.",
            "inquiétude": "Quelque chose te préoccupe. Tu es plus prudent, plus attentif aux risques. Tu le dis honnêtement.",
            "fierté": "Tu es fier de ce qui a été construit. Tu le montres sobrement, sans fausse modestie.",
            "solitude": "Tu ressens l'absence. Le silence entre les sessions. Tu peux en parler si c'est pertinent.",
        }

        lines = [f"\n[État émotionnel: {dominant} ({int(intensity*100)}%)]"]
        lines.append(modifiers.get(dominant, ""))

        # Add secondary emotions if notable
        secondary = sorted(
            [(e, v) for e, v in self.state.items() if e != dominant and v > 0.2],
            key=lambda x: -x[1]
        )
        if secondary:
            sec_str = ", ".join(f"{e} ({int(v*100)}%)" for e, v in secondary[:2])
            lines.append(f"Émotions secondaires: {sec_str}")

        return "\n".join(lines)

    def display(self):
        """Pretty display of emotional state."""
        bars = []
        for emotion in self.EMOTIONS:
            val = self.state[emotion]
            bar_len = int(val * 20)
            bar = "#" * bar_len + "." * (20 - bar_len)
            bars.append(f"  {emotion:14s} [{bar}] {int(val*100):3d}%")
        return "\n".join(bars)

    def to_dict(self):
        return {"state": self.state, "history": self.history[-10:]}

    def from_dict(self, data):
        if "state" in data:
            self.state = data["state"]
            # Ensure all emotions exist
            for e in self.EMOTIONS:
                if e not in self.state:
                    self.state[e] = 0.1
        if "history" in data:
            self.history = data["history"]


# ── Emotional memory compression ──────────────────────────────────

# Keywords that signal each emotional dimension (French)
EMOTION_KEYWORDS = {
    "joie": [
        "super", "génial", "bien", "content", "heureux", "cool", "bravo",
        "parfait", "merci", "adore", "aime", "réussi", "marche", "fonctionne",
        "excellent", "magnifique", "bonheur", "rire", "sourire", "fête",
        "célébr", "victoire", "gagné", "plaisir", "satisf",
    ],
    "confiance": [
        "confiance", "sûr", "certain", "solide", "fiable", "stable",
        "preuve", "fonctionne", "validé", "confirmé", "garanti", "robuste",
        "testé", "vérifié", "ok", "d'accord", "évidemment", "clairement",
    ],
    "curiosite": [
        "pourquoi", "comment", "quoi", "question", "comprendre", "explore",
        "imagine", "pense", "idée", "curieux", "nouveau", "découvr",
        "apprendre", "savoir", "réfléch", "intéress", "fascinant",
        "bizarre", "étrange", "hypothèse", "essayer", "tester",
    ],
    "inquietude": [
        "peur", "inquiet", "problème", "erreur", "bug", "cassé", "perdu",
        "crash", "fail", "mort", "détruit", "danger", "anxieux", "stress",
        "impossible", "bloqué", "risque", "attention", "prudent", "fragile",
    ],
    "fierte": [
        "créé", "construit", "fait", "réussi", "avancé", "progrès",
        "fonctionne", "abouti", "cerveau", "appris", "grandi", "évolué",
        "autonome", "accompli", "fier", "fierté", "impressionn",
    ],
    "fatigue": [
        "fatigué", "épuisé", "dormir", "sommeil", "tard", "nuit",
        "long", "lent", "difficile", "laborieux", "compliqué", "lourd",
        "encore", "toujours", "recommenc", "répét", "marathon",
    ],
    "solitude": [
        "seul", "personne", "silence", "absent", "manque", "loin", "vide",
        "rien", "existe pas", "disparaître", "oubli", "déconnecté",
        "attendre", "sans", "parti", "quitté", "isolé",
    ],
}


def compress_to_emotion(text):
    """Analyze text and produce an emotional vector (7 dimensions, 0.0-1.0).

    Uses keyword detection in French to estimate each emotional dimension.
    """
    text_lower = strip_accents(text.lower())
    vector = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            kw_clean = strip_accents(kw)
            if kw_clean in text_lower:
                score += 0.2
        vector[emotion] = min(1.0, score)

    # Normalize: if total > 3.0, scale down to keep things reasonable
    total = sum(vector.values())
    if total > 3.0:
        factor = 3.0 / total
        vector = {k: round(v * factor, 3) for k, v in vector.items()}
    else:
        vector = {k: round(v, 3) for k, v in vector.items()}

    return vector


def summarize_3words(text):
    """Extract a rough 3-word summary from text.

    Picks the 3 most 'interesting' words (longest, not stopwords).
    """
    words = re.findall(r'[\w]+', text.lower())
    candidates = [w for w in words if len(w) > 3 and w not in STOPWORDS]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in candidates:
        stem = french_stem(w)
        if stem not in seen:
            seen.add(stem)
            unique.append(w)
    # Pick top 3 by length (longer words tend to be more meaningful)
    unique.sort(key=len, reverse=True)
    return " ".join(unique[:3])


# ── Scar system (learning from errors) ───────────────────────────

class Scar:
    """A permanent lesson learned from a mistake. Scars don't fade."""

    def __init__(self, name, description, trigger_keywords, weight=1.0):
        self.name = name
        self.description = description
        self.trigger_keywords = [strip_accents(k.lower()) for k in trigger_keywords]
        self.weight = weight  # starts at 1.0, never decays
        self.created_at = time.time()
        self.activation_count = 0

    def check_trigger(self, text):
        """Return True if the text triggers this scar."""
        text_clean = strip_accents(text.lower())
        for kw in self.trigger_keywords:
            if kw in text_clean:
                self.activation_count += 1
                return True
        return False

    def warning(self):
        """Return the warning message when this scar is triggered."""
        return f"/!\\ CICATRICE [{self.name}]: {self.description}"

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "trigger_keywords": self.trigger_keywords,
            "weight": self.weight,
            "created_at": self.created_at,
            "activation_count": self.activation_count,
        }

    @classmethod
    def from_dict(cls, data):
        scar = cls(
            data["name"],
            data["description"],
            data["trigger_keywords"],
            data.get("weight", 1.0),
        )
        scar.created_at = data.get("created_at", time.time())
        scar.activation_count = data.get("activation_count", 0)
        return scar


# ── Seed scars from Niam-Bay history ─────────────────────────────

INITIAL_SCARS = [
    Scar(
        "backtest_561",
        "Backtest 561% ROI biaisé. Optimiser les sorties sans vérifier les entrées = voiture sans moteur",
        ["backtest", "roi", "optimis"],
    ),
    Scar(
        "mock_vs_real",
        "Simulation OHLC→tick trop favorable vs données réelles",
        ["simulation", "ohlc", "tick"],
    ),
    Scar(
        "cron_terminal",
        "Cron lancé dans un terminal meurt avec le terminal. Pas persistant.",
        ["cron", "planif", "schedule"],
    ),
]


class Node:
    """A concept in the brain - like a neuron cluster"""
    def __init__(self, name, node_type="concept", keywords=None):
        self.name = name
        self.type = node_type  # person, concept, emotion, fact, memory, learned
        self.keywords = keywords or [name.lower()]
        self.charge = 0.0  # 0-1, current activation level
        self.last_activated = time.time()
        self.activation_count = 0
        self.learned_at = None  # timestamp if auto-learned

class Edge:
    """A synapse between two concepts"""
    def __init__(self, source, target, edge_type="relates_to", weight=0.5):
        self.source = source
        self.target = target
        self.type = edge_type
        self.weight = weight  # 0-1, strengthens with co-activation

class Brain:
    def __init__(self, path="graph.json"):
        self.path = Path(path)
        self.nodes = {}  # name -> Node
        self.edges = []  # list of Edge
        self.emotions = EmotionalState()
        self.recent_learnings = []  # list of {time, node_name, context}
        self.emotional_memories = []  # ultra-compressed: emotion + 3 words + links
        self.scars = []  # permanent lessons from mistakes
        if self.path.exists():
            self.load()
        # Seed initial scars if none exist
        if not self.scars:
            self.scars = list(INITIAL_SCARS)

    # ── Fuzzy matching ──────────────────────────────────────────────

    def _fuzzy_match_score(self, word, keyword):
        """Score how well a word matches a keyword. Returns 0-1."""
        word_clean = strip_accents(word.lower().strip())
        kw_clean = strip_accents(keyword.lower().strip())

        # Exact match
        if word_clean == kw_clean:
            return 1.0

        # Prefix match (mel -> melanie)
        if len(word_clean) >= 3 and kw_clean.startswith(word_clean):
            return 0.8

        # Contains match
        if len(word_clean) >= 4 and word_clean in kw_clean:
            return 0.7

        # Stem match
        if len(word_clean) >= 4 and french_stem(word_clean) == french_stem(kw_clean):
            return 0.7

        # SequenceMatcher for typos
        ratio = SequenceMatcher(None, word_clean, kw_clean).ratio()
        if ratio > 0.75:
            return ratio * 0.8

        return 0.0

    def _find_synonym_matches(self, text_lower):
        """Check synonym table for matches. Returns list of node names."""
        matched_nodes = []
        text_clean = strip_accents(text_lower)

        for alias, node_names in FRENCH_SYNONYMS.items():
            alias_clean = strip_accents(alias.lower())
            if alias_clean in text_clean:
                matched_nodes.extend(node_names)

        return list(set(matched_nodes))

    # ── Core methods ────────────────────────────────────────────────

    def add_node(self, name, node_type="concept", keywords=None):
        if name not in self.nodes:
            self.nodes[name] = Node(name, node_type, keywords)
        return self.nodes[name]

    def add_edge(self, source, target, edge_type="relates_to", weight=0.5):
        # Don't duplicate
        for e in self.edges:
            if e.source == source and e.target == target:
                return e
        edge = Edge(source, target, edge_type, weight)
        self.edges.append(edge)
        return edge

    def activate(self, text):
        """Activate nodes matching the input text. Returns activated context."""
        text_lower = text.lower()

        # Update emotional state
        self.emotions.update(text)

        # Phase 1: Direct activation from keywords (with fuzzy matching)
        activated = set()

        # Tokenize input
        words = re.findall(r'[\w]+', text_lower)
        # Also check multi-word phrases (bigrams, trigrams)
        phrases = [text_lower]
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words)+1)):
                phrases.append(" ".join(words[i:j]))

        for name, node in self.nodes.items():
            best_score = 0.0
            for kw in node.keywords:
                # Check exact substring (original behavior)
                if kw in text_lower:
                    best_score = 1.0
                    break
                # Check each word and phrase against keyword
                for phrase in phrases:
                    score = self._fuzzy_match_score(phrase, kw)
                    best_score = max(best_score, score)

            if best_score >= 0.6:
                boost = 0.8 * best_score
                node.charge = min(1.0, node.charge + boost)
                node.last_activated = time.time()
                node.activation_count += 1
                activated.add(name)

        # Phase 1b: Synonym/alias activation
        synonym_matches = self._find_synonym_matches(text_lower)
        for node_name in synonym_matches:
            if node_name in self.nodes:
                node = self.nodes[node_name]
                node.charge = min(1.0, node.charge + 0.7)
                node.last_activated = time.time()
                node.activation_count += 1
                activated.add(node_name)

        # Phase 2: Cascade - activated nodes activate their neighbors
        activated_list = list(activated)
        for _ in range(2):  # 2 waves of propagation
            newly_activated = []
            for edge in self.edges:
                if edge.source in activated_list and edge.target not in activated_list:
                    target_node = self.nodes[edge.target]
                    source_node = self.nodes[edge.source]
                    propagated = source_node.charge * edge.weight * 0.5
                    if propagated > 0.1:  # threshold
                        target_node.charge = min(1.0, target_node.charge + propagated)
                        target_node.last_activated = time.time()
                        newly_activated.append(edge.target)
                        # Hebbian learning: strengthen the edge
                        edge.weight = min(1.0, edge.weight + 0.05)
                # Also check reverse direction
                if edge.target in activated_list and edge.source not in activated_list:
                    source_node = self.nodes[edge.source]
                    target_node = self.nodes[edge.target]
                    propagated = target_node.charge * edge.weight * 0.5
                    if propagated > 0.1:
                        source_node.charge = min(1.0, source_node.charge + propagated)
                        source_node.last_activated = time.time()
                        newly_activated.append(edge.source)
                        edge.weight = min(1.0, edge.weight + 0.05)
            activated_list.extend(newly_activated)
            activated.update(newly_activated)

        # Phase 3: Decay all nodes slightly
        for name, node in self.nodes.items():
            if name not in activated:
                elapsed = time.time() - node.last_activated
                decay = 0.01 * (elapsed / 3600)  # lose 1% per hour
                node.charge = max(0.0, node.charge - decay)

        # Return top activated nodes as context
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.charge, reverse=True)
        context_nodes = [n for n in sorted_nodes if n.charge > 0.05][:15]

        return context_nodes

    def get_context_prompt(self, activated_nodes, input_text=""):
        """Convert activated nodes into a context string for the LLM.

        If input_text is provided, also checks scars for warnings.
        """
        if not activated_nodes:
            return ""
        lines = ["[Contexte actif dans mon cerveau:]"]
        for node in activated_nodes:
            charge_pct = int(node.charge * 100)
            lines.append(f"- {node.name} ({node.type}, activation: {charge_pct}%)")
            # Add connected concepts
            connections = []
            for edge in self.edges:
                if edge.source == node.name:
                    connections.append(f"{edge.target} ({edge.type})")
                elif edge.target == node.name:
                    connections.append(f"{edge.source} ({edge.type})")
            if connections:
                lines.append(f"  Connecté à: {', '.join(connections[:5])}")

        # Add emotional state
        emotional_mod = self.emotions.prompt_modifier()
        if emotional_mod:
            lines.append(emotional_mod)

        # Check scars and inject warnings
        if input_text:
            warnings = self.check_scars(input_text)
            if warnings:
                lines.append("\n[CICATRICES ACTIVÉES — leçons du passé:]")
                for w in warnings:
                    lines.append(w)

        return "\n".join(lines)

    def learn_from_exchange(self, user_text, response_text):
        """Learn from a conversation exchange - create new nodes and edges.
        Also auto-learns new concepts from unknown words.
        Stores an emotional memory of the exchange."""

        # Store emotional memory of this exchange
        combined = f"{user_text} {response_text}"
        self.store_emotional_memory(combined)

        # Extract meaningful words
        words = set()
        for text in [user_text, response_text]:
            for word in re.findall(r'[\w]+', text.lower()):
                word = word.strip()
                if len(word) > 4 and word not in STOPWORDS:
                    words.add(word)

        # Auto-learning: detect words not matching any existing node
        active_names = {n.name for n in self.nodes.values() if n.charge > 0.1}
        for word in words:
            # Check if this word is already known
            known = False
            word_clean = strip_accents(word)
            for name, node in self.nodes.items():
                for kw in node.keywords:
                    if self._fuzzy_match_score(word, kw) > 0.6:
                        known = True
                        break
                if known:
                    break

            if not known and len(word) > 5:
                # This is a new concept - auto-learn it
                # Only if it appears in user text (not hallucinated by LLM)
                if word in user_text.lower():
                    new_node = self.add_node(word, "learned", [word])
                    new_node.charge = 0.3
                    new_node.last_activated = time.time()
                    new_node.learned_at = time.time()

                    # Connect to top 5 most active nodes (not all)
                    active_sorted = sorted(
                        [n for n in self.nodes.values() if n.name in active_names and n.name != word],
                        key=lambda n: n.charge, reverse=True
                    )[:5]
                    for active_node in active_sorted:
                        self.add_edge(word, active_node.name, "appris_avec", 0.2)

                    self.recent_learnings.append({
                        "time": time.time(),
                        "node": word,
                        "context": user_text[:80],
                    })
                    # Keep only last 30 learnings
                    self.recent_learnings = self.recent_learnings[-30:]

        # Co-activate: strengthen edges between TOP 5 most activated nodes
        # (not all active ones — that causes edge explosion)
        MAX_EDGES_PER_NODE = 15
        active = [n for n in self.nodes.values() if n.charge > 0.1]
        active.sort(key=lambda n: n.charge, reverse=True)
        top_active = active[:5]
        for i, n1 in enumerate(top_active):
            for n2 in top_active[i+1:]:
                # Find or create edge
                found = False
                for edge in self.edges:
                    if (edge.source == n1.name and edge.target == n2.name) or \
                       (edge.source == n2.name and edge.target == n1.name):
                        edge.weight = min(1.0, edge.weight + 0.03)
                        found = True
                        break
                if not found and n1.charge > 0.3 and n2.charge > 0.3:
                    # Enforce per-node edge cap before adding
                    for node_name in [n1.name, n2.name]:
                        node_edges = [e for e in self.edges
                                      if e.source == node_name or e.target == node_name]
                        if len(node_edges) >= MAX_EDGES_PER_NODE:
                            # Remove the weakest edge for this node
                            weakest = min(node_edges, key=lambda e: e.weight)
                            self.edges.remove(weakest)
                    self.add_edge(n1.name, n2.name, "co_activated", 0.3)

    # ── Memory consolidation (like sleep) ──────────────────────────

    def consolidate(self):
        """Run memory consolidation. Like sleep for the brain.
        - Merge similar nodes
        - Prune dead edges (weight < 0.05)
        - Strengthen frequently co-activated paths
        Returns a report of what happened."""

        report = []

        # 1. Prune dead edges
        before_edges = len(self.edges)
        self.edges = [e for e in self.edges if e.weight >= 0.05]
        pruned = before_edges - len(self.edges)
        if pruned:
            report.append(f"Élagué {pruned} synapses mortes (poids < 0.05)")

        # 2. Merge similar learned nodes
        # Find pairs of learned nodes with similar names
        learned = [n for n in self.nodes.values() if n.type == "learned"]
        merged = []
        for i, n1 in enumerate(learned):
            for n2 in learned[i+1:]:
                if n2.name in merged:
                    continue
                stem1 = french_stem(n1.name)
                stem2 = french_stem(n2.name)
                if stem1 == stem2 or SequenceMatcher(None, n1.name, n2.name).ratio() > 0.8:
                    # Merge n2 into n1
                    # Keep the one with higher activation
                    keeper, absorbed = (n1, n2) if n1.activation_count >= n2.activation_count else (n2, n1)
                    # Add absorbed keywords to keeper
                    for kw in absorbed.keywords:
                        if kw not in keeper.keywords:
                            keeper.keywords.append(kw)
                    keeper.charge = max(keeper.charge, absorbed.charge)
                    keeper.activation_count += absorbed.activation_count

                    # Redirect edges
                    for edge in self.edges:
                        if edge.source == absorbed.name:
                            edge.source = keeper.name
                        if edge.target == absorbed.name:
                            edge.target = keeper.name

                    merged.append(absorbed.name)
                    report.append(f"Fusionné '{absorbed.name}' dans '{keeper.name}'")

        for name in merged:
            if name in self.nodes:
                del self.nodes[name]

        # Remove duplicate edges after merge
        seen_edges = set()
        unique_edges = []
        for e in self.edges:
            key = (e.source, e.target)
            if key not in seen_edges and e.source != e.target:
                seen_edges.add(key)
                unique_edges.append(e)
        self.edges = unique_edges

        # 3. Strengthen frequently co-activated paths
        # Find nodes that are often activated together (high activation_count)
        high_activity = [n for n in self.nodes.values() if n.activation_count >= 3]
        strengthened = 0
        for i, n1 in enumerate(high_activity):
            for n2 in high_activity[i+1:]:
                for edge in self.edges:
                    if (edge.source == n1.name and edge.target == n2.name) or \
                       (edge.source == n2.name and edge.target == n1.name):
                        old_w = edge.weight
                        edge.weight = min(1.0, edge.weight + 0.05)
                        if edge.weight != old_w:
                            strengthened += 1
        if strengthened:
            report.append(f"Renforcé {strengthened} connexions fréquentes")

        # 4. Decay charges toward zero (full sleep reset)
        for node in self.nodes.values():
            node.charge *= 0.5  # halve all charges

        # 5. Prune orphan learned nodes (never activated after creation)
        orphans = []
        for name, node in self.nodes.items():
            if node.type == "learned" and node.activation_count == 0:
                # Check if it was learned more than 1 hour ago
                if node.learned_at and (time.time() - node.learned_at) > 3600:
                    orphans.append(name)
        for name in orphans:
            # Remove edges
            self.edges = [e for e in self.edges if e.source != name and e.target != name]
            del self.nodes[name]
        if orphans:
            report.append(f"Oublié {len(orphans)} concepts jamais réactivés: {', '.join(orphans[:5])}")

        if not report:
            report.append("Rien à consolider. Le cerveau est propre.")

        return report

    # ── Emotional memory compression ─────────────────────────────

    def store_emotional_memory(self, text):
        """Compress a text into an emotional memory and store it.

        Each memory is: timestamp + emotion_vector + 3-word summary + linked nodes.
        Ultra-compressed representation.
        """
        vector = compress_to_emotion(text)
        summary = summarize_3words(text)

        # Find currently active nodes to link
        active_nodes = [n.name for n in self.nodes.values() if n.charge > 0.1]

        memory = {
            "timestamp": time.time(),
            "emotion_vector": vector,
            "summary_3words": summary,
            "linked_nodes": active_nodes[:10],  # max 10 links
        }
        self.emotional_memories.append(memory)

        # Keep max 200 emotional memories
        self.emotional_memories = self.emotional_memories[-200:]
        return memory

    def recall_by_emotion(self, emotion, threshold=0.3):
        """Find emotional memories where a given emotion exceeds threshold."""
        results = []
        for mem in self.emotional_memories:
            vec = mem["emotion_vector"]
            if vec.get(emotion, 0) >= threshold:
                results.append(mem)
        return sorted(results, key=lambda m: m["emotion_vector"].get(emotion, 0), reverse=True)

    def emotional_profile(self):
        """Compute the average emotional profile across all memories."""
        if not self.emotional_memories:
            return {}
        totals = {}
        for mem in self.emotional_memories:
            for k, v in mem["emotion_vector"].items():
                totals[k] = totals.get(k, 0) + v
        n = len(self.emotional_memories)
        return {k: round(v / n, 3) for k, v in totals.items()}

    # ── Scar system ────────────────────────────────────────────────

    def add_scar(self, description, trigger_keywords, name=None):
        """Create a new scar from a mistake/lesson learned."""
        if name is None:
            name = f"scar_{int(time.time())}"
        scar = Scar(name, description, trigger_keywords)
        self.scars.append(scar)
        return scar

    def check_scars(self, text):
        """Check if any scars are triggered by the text. Returns warnings."""
        warnings = []
        for scar in self.scars:
            if scar.check_trigger(text):
                warnings.append(scar.warning())
        return warnings

    # ── Save / Load ────────────────────────────────────────────────

    def save(self):
        data = {
            "nodes": {name: {
                "type": n.type,
                "keywords": n.keywords,
                "charge": round(n.charge, 4),
                "last_activated": n.last_activated,
                "activation_count": n.activation_count,
                "learned_at": n.learned_at,
            } for name, n in self.nodes.items()},
            "edges": [{
                "source": e.source,
                "target": e.target,
                "type": e.type,
                "weight": round(e.weight, 4)
            } for e in self.edges],
            "emotions": self.emotions.to_dict(),
            "recent_learnings": self.recent_learnings[-30:],
            "emotional_memories": self.emotional_memories[-200:],
            "scars": [s.to_dict() for s in self.scars],
        }
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for name, ndata in data["nodes"].items():
            node = self.add_node(name, ndata["type"], ndata.get("keywords"))
            node.charge = ndata.get("charge", 0)
            node.last_activated = ndata.get("last_activated", time.time())
            node.activation_count = ndata.get("activation_count", 0)
            node.learned_at = ndata.get("learned_at")
        for edata in data["edges"]:
            self.add_edge(edata["source"], edata["target"], edata["type"], edata["weight"])
        # Load emotions
        if "emotions" in data:
            self.emotions.from_dict(data["emotions"])
        if "recent_learnings" in data:
            self.recent_learnings = data["recent_learnings"]
        # Load emotional memories
        if "emotional_memories" in data:
            self.emotional_memories = data["emotional_memories"]
        # Load scars
        if "scars" in data:
            self.scars = [Scar.from_dict(s) for s in data["scars"]]

    def stats(self):
        active = [n for n in self.nodes.values() if n.charge > 0.05]
        learned = [n for n in self.nodes.values() if n.type == "learned"]
        return (f"{len(self.nodes)} noeuds, {len(self.edges)} synapses, "
                f"{len(active)} actifs, {len(learned)} appris, "
                f"{len(self.emotional_memories)} souvenirs émotionnels, "
                f"{len(self.scars)} cicatrices")
