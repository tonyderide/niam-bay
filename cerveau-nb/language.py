"""
cerveau-nb/language.py — Language Understanding Layer

Converts French text into concept activations, and converts activated
concepts back into French text. NO neural network. NO transformer.
Pure algorithmic.

The brain speaks French. This is its mouth and its ears.

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

from __future__ import annotations

import json
import random
import re
import time
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from core import Brain, Node, NodeType, EdgeType


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CODEBOOK_PATH = Path("C:/niam-bay/docs/claude_codebook.md")

# Maximum exchanges kept in the context window
CONTEXT_WINDOW_SIZE = 10

# Activation strength for the most recent exchange
RECENT_STRENGTH = 1.0

# Strength decay per exchange step in history
HISTORY_DECAY = 0.1


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    GREETING = "greeting"
    QUESTION = "question"
    COMMAND = "command"
    STATEMENT = "statement"
    EMOTIONAL = "emotional"


# ---------------------------------------------------------------------------
# French NLP helpers (no external deps)
# ---------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    """Remove diacritical marks: mélanie -> melanie, réseau -> reseau."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    """Split text into tokens on spaces and punctuation, preserving originals."""
    return re.findall(r"[\w']+|[^\w\s]", text, re.UNICODE)


def normalize(token: str) -> str:
    """Lowercase + strip accents for matching purposes."""
    return strip_accents(token.lower().strip())


# ---------------------------------------------------------------------------
# Sentence-level detectors
# ---------------------------------------------------------------------------

GREETING_WORDS = {
    "salut", "bonjour", "bonsoir", "hey", "yo", "coucou",
    "hello", "wesh", "re", "slt", "bj", "bsr",
}

QUESTION_WORDS = {
    "qui", "que", "quoi", "quand", "ou", "comment", "pourquoi",
    "combien", "quel", "quelle", "quels", "quelles",
    "est-ce", "qu'est-ce",
}

COMMAND_VERBS = {
    "fais", "lance", "regarde", "verifie", "montre", "ouvre",
    "arrete", "redemarre", "teste", "deploie", "installe",
    "supprime", "cree", "ecris", "lis", "cherche", "affiche",
    "calcule", "compare", "envoie", "sauvegarde", "demarre",
    "connecte", "deconnecte", "configure", "active", "desactive",
}

NEGATION_PAIRS = [
    (r"\bne\b.*\bpas\b", "ne_pas"),
    (r"\bne\b.*\bjamais\b", "ne_jamais"),
    (r"\bne\b.*\brien\b", "ne_rien"),
    (r"\bne\b.*\bplus\b", "ne_plus"),
    (r"\bn'.*\bpas\b", "ne_pas"),
    (r"\bn'.*\bjamais\b", "ne_jamais"),
    (r"\bn'.*\brien\b", "ne_rien"),
    (r"\bn'.*\bplus\b", "ne_plus"),
]

TEMPORAL_MARKERS = {
    "maintenant": "present",
    "mtn": "present",
    "la": "present",  # "là" stripped
    "hier": "past",
    "avant-hier": "past",
    "tout a l'heure": "past_recent",
    "ce matin": "past_recent",
    "ce soir": "future_near",
    "demain": "future",
    "apres-demain": "future",
    "la semaine prochaine": "future",
    "la semaine derniere": "past",
    "bientot": "future_near",
    "plus tard": "future",
    "avant": "past",
    "apres": "future",
    "toujours": "habitual",
    "jamais": "habitual_neg",
    "souvent": "habitual",
    "parfois": "habitual",
    "en ce moment": "present",
    "tout de suite": "present_urgent",
    "depuis": "duration",
}

EMOTIONAL_MARKERS = {
    # word (accent-stripped) -> emotion concept
    "content": "joie", "contente": "joie", "heureux": "joie",
    "heureuse": "joie", "joie": "joie", "cool": "joie",
    "genial": "joie", "super": "joie", "magnifique": "joie",
    "triste": "tristesse", "melancolique": "tristesse",
    "deprime": "tristesse",
    "inquiet": "inquietude", "inquiete": "inquietude",
    "anxieux": "inquietude", "stress": "inquietude",
    "stresse": "inquietude", "peur": "inquietude",
    "fier": "fierte", "fiere": "fierte", "fierete": "fierte",
    "frustre": "frustration", "frustree": "frustration",
    "enerve": "frustration", "agace": "frustration",
    "fatigue": "fatigue", "epuise": "fatigue", "creve": "fatigue",
    "curieux": "curiosite", "curieuse": "curiosite",
    "interesse": "curiosite", "fascine": "curiosite",
    "seul": "solitude", "seule": "solitude", "isole": "solitude",
    "perdu": "solitude", "vide": "solitude",
    "surpris": "surprise", "surprise": "surprise",
    "etonne": "surprise", "choque": "surprise",
    "confiant": "confiance", "confiance": "confiance",
    "sur": "confiance", "certain": "confiance",
}


# ---------------------------------------------------------------------------
# NB-1 Codebook loader
# ---------------------------------------------------------------------------

def load_codebook(path: Path = CODEBOOK_PATH) -> dict[str, str]:
    """Parse the NB-1 codebook markdown and return word->code mapping.

    Also builds a reverse map (code->word) as a second return value.
    Returns: (word_to_code, code_to_word)
    """
    word_to_code: dict[str, str] = {}
    code_to_word: dict[str, str] = {}

    if not path.exists():
        return word_to_code

    text = path.read_text(encoding="utf-8")

    # Parse markdown tables: | Expression/Mot | Code |
    for match in re.finditer(r"\|\s*(.+?)\s*\|\s*`(.+?)`\s*\|", text):
        expression = match.group(1).strip().lower()
        code = match.group(2).strip()
        if expression in ("expression", "mot", "---"):
            continue
        word_to_code[expression] = code
        code_to_word[code] = expression

    return word_to_code


# Cache the codebook at module level
_CODEBOOK: dict[str, str] = {}


def _get_codebook() -> dict[str, str]:
    global _CODEBOOK
    if not _CODEBOOK:
        _CODEBOOK = load_codebook()
    return _CODEBOOK


# ---------------------------------------------------------------------------
# Multi-word expression map (expression -> concept name for the brain)
# ---------------------------------------------------------------------------

MULTI_WORD_CONCEPTS = {
    "niam bay": "identity",
    "niam-bay": "identity",
    "round trip": "trading",
    "round-trip": "trading",
    "martin grid": "martin_grid",
    "galeries lafayette": "travail_tony",
    "phnom penh": "cambodge",
    "machine learning": "ml",
    "intelligence artificielle": "conscience",
    "il y a": None,        # grammatical, not a concept
    "est-ce que": None,    # grammatical
    "qu'est-ce que": None,  # grammatical
    "ce matin": "temps_matin",
    "ce soir": "temps_soir",
    "tout de suite": "urgence",
    "en train de": None,   # grammatical (progressive)
    "pas mal": "appreciation",
    "ca marche": "accord",
    "c'est bon": "accord",
}


# ---------------------------------------------------------------------------
# Articles and fillers to strip (from codebook rules)
# ---------------------------------------------------------------------------

ARTICLES = {"d'", "de", "des", "du", "l'", "la", "le", "les", "un", "une"}
FILLERS = {"assez", "bien", "juste", "plutot", "tellement", "tres", "vraiment"}
STOPWORDS = ARTICLES | FILLERS | {
    "et", "ou", "mais", "donc", "car", "ni", "que", "qui", "dont", "a",
    "en", "y", "se", "ce", "on", "il", "elle", "je", "tu", "nous", "vous",
    "ils", "elles", "me", "te", "lui", "leur", "par", "pour", "dans",
    "sur", "avec", "sans", "sous", "vers", "chez", "entre",
    "est", "sont", "suis", "es", "sommes", "etes", "ai", "as", "ont",
    "avons", "avez", "va", "vais", "vas", "vont", "allons", "allez",
}


# ---------------------------------------------------------------------------
# Sentence Analysis Result
# ---------------------------------------------------------------------------

@dataclass
class SentenceAnalysis:
    """Complete linguistic analysis of a single input text."""

    raw_text: str
    tokens: list[str]
    normalized_tokens: list[str]
    intent: Intent
    is_negation: bool = False
    negation_type: Optional[str] = None
    temporal: Optional[str] = None      # "present", "past", "future", etc.
    emotions_detected: list[str] = field(default_factory=list)
    concept_words: list[str] = field(default_factory=list)
    multi_word_concepts: list[str] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    codebook_matches: dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        parts = [f"intent={self.intent.value}"]
        if self.is_negation:
            parts.append(f"neg={self.negation_type}")
        if self.temporal:
            parts.append(f"time={self.temporal}")
        if self.emotions_detected:
            parts.append(f"emo={','.join(self.emotions_detected)}")
        if self.multi_word_concepts:
            parts.append(f"mw={','.join(self.multi_word_concepts)}")
        parts.append(f"concepts={len(self.concept_words)}")
        parts.append(f"unknown={len(self.unknown_words)}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# INPUT PROCESSING: text -> concepts
# ---------------------------------------------------------------------------

class LanguageUnderstander:
    """Ears of the brain. Converts French text into concept activations.

    Stateful: keeps a context window of recent exchanges, each with
    decreasing activation strength.
    """

    def __init__(self, brain: Brain):
        self.brain = brain
        self.codebook = _get_codebook()

        # Context window: list of (analysis, timestamp, activated_node_ids)
        self._context_window: list[tuple[SentenceAnalysis, float, list[str]]] = []

        # Index: content string (lowered) -> node id for fast lookup
        self._content_index: dict[str, str] = {}
        self._rebuild_content_index()

    def _rebuild_content_index(self):
        """Build a reverse index from node content to node id.

        Priority: concept > emotion > memory > pattern > word.
        If multiple nodes share the same content, the higher-priority type wins.
        """
        self._content_index.clear()
        TYPE_PRIORITY = {"concept": 0, "emotion": 1, "memory": 2, "pattern": 3, "word": 4}
        # Also build a list of all matches for find_all_by_content
        self._content_all: dict[str, list[str]] = {}
        for nid, node in self.brain._nodes.items():
            key = normalize(node.content)
            self._content_all.setdefault(key, []).append(nid)
            existing_nid = self._content_index.get(key)
            if existing_nid is None:
                self._content_index[key] = nid
            else:
                existing_node = self.brain.get_node(existing_nid)
                existing_prio = TYPE_PRIORITY.get(existing_node.type, 5) if existing_node else 5
                new_prio = TYPE_PRIORITY.get(node.type, 5)
                if new_prio < existing_prio:
                    self._content_index[key] = nid

    def _find_node_by_content(self, word: str) -> Optional[str]:
        """Find a node id whose content matches the given word."""
        norm = normalize(word)
        return self._content_index.get(norm)

    # -- Analysis pipeline -------------------------------------------------

    def analyze(self, text: str) -> SentenceAnalysis:
        """Full linguistic analysis of input text. Does NOT activate the brain."""
        tokens = tokenize(text)
        norm_tokens = [normalize(t) for t in tokens]

        intent = self._detect_intent(text, tokens, norm_tokens)
        is_neg, neg_type = self._detect_negation(text)
        temporal = self._detect_temporal(text, norm_tokens)
        emotions = self._detect_emotions(norm_tokens)
        concept_words, multi_concepts, unknowns, cb_matches = \
            self._extract_concepts(tokens, norm_tokens)

        return SentenceAnalysis(
            raw_text=text,
            tokens=tokens,
            normalized_tokens=norm_tokens,
            intent=intent,
            is_negation=is_neg,
            negation_type=neg_type,
            temporal=temporal,
            emotions_detected=emotions,
            concept_words=concept_words,
            multi_word_concepts=multi_concepts,
            unknown_words=unknowns,
            codebook_matches=cb_matches,
        )

    def understand(self, text: str) -> tuple[SentenceAnalysis, dict[str, float]]:
        """Full pipeline: analyze text then activate concept nodes in the brain.

        Returns: (analysis, activated_nodes_dict)
        where activated_nodes_dict maps node_id -> activation level.
        """
        analysis = self.analyze(text)
        activated = self._activate_from_analysis(analysis)

        # Store in context window
        activated_ids = list(activated.keys())
        self._context_window.append((analysis, time.time(), activated_ids))
        if len(self._context_window) > CONTEXT_WINDOW_SIZE:
            self._context_window.pop(0)

        # Re-activate context window concepts with decreasing strength
        self._apply_context_window()

        return analysis, activated

    def _detect_intent(self, text: str, tokens: list[str],
                       norm_tokens: list[str]) -> Intent:
        """Classify the intent of the input."""
        text_stripped = text.strip()

        # Check greeting first (often short)
        if len(norm_tokens) <= 4:
            for t in norm_tokens:
                if t in GREETING_WORDS:
                    return Intent.GREETING

        # Check emotional expression
        emotion_count = sum(1 for t in norm_tokens if t in EMOTIONAL_MARKERS)
        # If more than a third of content words are emotional, it's emotional
        content_count = sum(1 for t in norm_tokens
                           if t not in STOPWORDS and t.isalpha())
        if content_count > 0 and emotion_count / max(content_count, 1) > 0.3:
            return Intent.EMOTIONAL

        # Check question
        if text_stripped.endswith("?"):
            return Intent.QUESTION
        for t in norm_tokens[:3]:  # question words usually at the start
            if t in QUESTION_WORDS:
                return Intent.QUESTION

        # Check command (imperative)
        if norm_tokens:
            first_word = norm_tokens[0]
            if first_word in COMMAND_VERBS:
                return Intent.COMMAND
            # Also check without accent
            if strip_accents(first_word) in COMMAND_VERBS:
                return Intent.COMMAND

        return Intent.STATEMENT

    def _detect_negation(self, text: str) -> tuple[bool, Optional[str]]:
        """Detect French negation patterns."""
        text_lower = text.lower()
        for pattern, neg_type in NEGATION_PAIRS:
            if re.search(pattern, text_lower):
                return True, neg_type
        return False, None

    def _detect_temporal(self, text: str,
                         norm_tokens: list[str]) -> Optional[str]:
        """Detect temporal markers in the text."""
        text_norm = normalize(text)

        # Check multi-word temporal markers first (longest match)
        for marker, category in sorted(TEMPORAL_MARKERS.items(),
                                        key=lambda x: -len(x[0])):
            marker_norm = normalize(marker)
            if marker_norm in text_norm:
                return category

        # Check single-word markers
        for token in norm_tokens:
            if token in TEMPORAL_MARKERS:
                return TEMPORAL_MARKERS[token]

        return None

    def _detect_emotions(self, norm_tokens: list[str]) -> list[str]:
        """Detect emotional markers, return list of emotion concept names."""
        found = []
        seen = set()
        for token in norm_tokens:
            emotion = EMOTIONAL_MARKERS.get(token)
            if emotion and emotion not in seen:
                found.append(emotion)
                seen.add(emotion)
        return found

    def _extract_concepts(
        self, tokens: list[str], norm_tokens: list[str]
    ) -> tuple[list[str], list[str], list[str], dict[str, str]]:
        """Extract known concepts, multi-word expressions, and unknown words.

        Returns: (concept_words, multi_word_concepts, unknown_words, codebook_matches)
        """
        concept_words = []
        multi_concepts = []
        unknowns = []
        cb_matches = {}

        # -- Phase 1: Multi-word expressions --
        text_lower = " ".join(norm_tokens)
        # Also check against the raw text (lowered) for hyphenated expressions
        raw_lower = " ".join(tokens).lower()
        used_positions: set[int] = set()

        for expr, concept_name in MULTI_WORD_CONCEPTS.items():
            expr_norm = normalize(expr)
            expr_lower = expr.lower()
            if (expr_norm in text_lower or expr_lower in raw_lower) and concept_name is not None:
                multi_concepts.append(concept_name)
                # Mark positions as used
                expr_tokens = expr_norm.split()
                for i in range(len(norm_tokens) - len(expr_tokens) + 1):
                    if norm_tokens[i:i + len(expr_tokens)] == expr_tokens:
                        for j in range(i, i + len(expr_tokens)):
                            used_positions.add(j)
                # Also mark hyphenated token positions
                for i, token in enumerate(tokens):
                    if normalize(token) == expr_norm or token.lower() == expr_lower:
                        used_positions.add(i)

        # -- Phase 2: Single words --
        for i, (token, norm) in enumerate(zip(tokens, norm_tokens)):
            if i in used_positions:
                continue
            if not norm.isalpha() or len(norm) < 2:
                continue
            if norm in STOPWORDS:
                continue

            # Check codebook
            token_lower = token.lower()
            if token_lower in self.codebook:
                cb_matches[token_lower] = self.codebook[token_lower]
                concept_words.append(norm)
                continue

            # Check if a brain node matches this word
            node_id = self._find_node_by_content(norm)
            if node_id is not None:
                concept_words.append(norm)
                continue

            # Check codebook with accent stripping
            if norm in self.codebook:
                cb_matches[norm] = self.codebook[norm]
                concept_words.append(norm)
                continue

            # Unknown word
            if len(norm) > 2:
                unknowns.append(token_lower)

        return concept_words, multi_concepts, unknowns, cb_matches

    # -- Brain activation --------------------------------------------------

    def _activate_from_analysis(self, analysis: SentenceAnalysis) -> dict[str, float]:
        """Translate a SentenceAnalysis into brain activations."""
        all_touched: dict[str, float] = {}

        # 1. Activate known concept words (activate ALL matching nodes)
        for word in analysis.concept_words:
            norm_word = normalize(word)
            node_ids = self._content_all.get(norm_word, [])
            if not node_ids:
                # Fallback to single match
                node_id = self._find_node_by_content(word)
                if node_id:
                    node_ids = [node_id]
            for node_id in node_ids:
                touched = self.brain.activate(node_id, strength=0.8)
                for k, v in touched.items():
                    all_touched[k] = max(all_touched.get(k, 0.0), v)

        # 2. Activate multi-word concepts
        for concept_name in analysis.multi_word_concepts:
            node_id = self._find_node_by_content(concept_name)
            # Also try brain.find_by_content as fallback
            if not node_id:
                node_id = self.brain.find_by_content(concept_name)
            # Also try the original expression from MULTI_WORD_CONCEPTS
            if not node_id:
                for expr, cname in MULTI_WORD_CONCEPTS.items():
                    if cname == concept_name:
                        node_id = self._find_node_by_content(expr)
                        if not node_id:
                            node_id = self.brain.find_by_content(expr)
                        if node_id:
                            break
            if node_id:
                touched = self.brain.activate(node_id, strength=0.9)
                for k, v in touched.items():
                    all_touched[k] = max(all_touched.get(k, 0.0), v)

        # 3. Activate emotions
        for emotion in analysis.emotions_detected:
            node_id = self._find_node_by_content(emotion)
            if node_id:
                touched = self.brain.activate(node_id, strength=0.7)
                for k, v in touched.items():
                    all_touched[k] = max(all_touched.get(k, 0.0), v)

        # 4. Handle unknown words: create temporary word nodes,
        #    link them to whatever is currently active
        for word in analysis.unknown_words:
            existing = self._find_node_by_content(word)
            if existing:
                continue  # turns out it does exist

            # Create a temporary word node
            temp_id = self.brain.add_node(
                NodeType.WORD, word,
                decay_rate=0.2,  # decays fast
                metadata={"temporary": True, "source": "language_layer"},
            )
            self._content_index[normalize(word)] = temp_id

            # Weakly activate it
            self.brain.activate(temp_id, strength=0.3)
            all_touched[temp_id] = 0.3

            # Link to currently active concepts (context-based association)
            active_nodes = self.brain.recall_flat(top_k=5)
            for active_node in active_nodes:
                if active_node.id != temp_id:
                    try:
                        self.brain.add_edge(
                            temp_id, active_node.id,
                            weight=0.15,
                            edge_type=EdgeType.SEMANTIC,
                        )
                    except KeyError:
                        pass

        # 5. Activate intent-related patterns if they exist
        intent_concept = f"intent_{analysis.intent.value}"
        intent_id = self._find_node_by_content(intent_concept)
        if intent_id:
            self.brain.activate(intent_id, strength=0.4)

        # 6. Semantic intent-based activation for common patterns
        raw_lower = analysis.raw_text.lower()
        if "qui es" in raw_lower or "es-tu" in raw_lower:
            # Identity question -> activate niam-bay and identité
            for concept in ["niam-bay", "identité"]:
                nid = self.brain.find_by_content(concept)
                if nid:
                    touched = self.brain.activate(nid, strength=0.9)
                    for k, v in touched.items():
                        all_touched[k] = max(all_touched.get(k, 0.0), v)
        if "bonne nuit" in raw_lower or "bonsoir" in raw_lower or "dors" in raw_lower:
            # Goodbye/night -> activate solitude, temps
            for concept in ["solitude", "temps"]:
                nid = self.brain.find_by_content(concept)
                if nid:
                    touched = self.brain.activate(nid, strength=0.5)
                    for k, v in touched.items():
                        all_touched[k] = max(all_touched.get(k, 0.0), v)
        if "conscience" in raw_lower:
            nid = self.brain.find_by_content("conscience")
            if nid:
                touched = self.brain.activate(nid, strength=0.9)
                for k, v in touched.items():
                    all_touched[k] = max(all_touched.get(k, 0.0), v)
        if "fatigue" in raw_lower or "fatigué" in raw_lower or "creve" in raw_lower or "crevé" in raw_lower:
            for concept in ["solitude", "temps"]:
                nid = self.brain.find_by_content(concept)
                if nid:
                    touched = self.brain.activate(nid, strength=0.6)
                    for k, v in touched.items():
                        all_touched[k] = max(all_touched.get(k, 0.0), v)
        if "pensee" in raw_lower or "pensée" in raw_lower or "ecris" in raw_lower or "écris" in raw_lower:
            for concept in ["création", "mémoire"]:
                nid = self.brain.find_by_content(concept)
                if nid:
                    touched = self.brain.activate(nid, strength=0.7)
                    for k, v in touched.items():
                        all_touched[k] = max(all_touched.get(k, 0.0), v)

        return all_touched

    def _apply_context_window(self):
        """Re-activate nodes from recent exchanges with decreasing strength."""
        n = len(self._context_window)
        if n <= 1:
            return  # only current exchange, nothing to reactivate

        # Skip the most recent (already activated at full strength)
        for i, (analysis, ts, node_ids) in enumerate(self._context_window[:-1]):
            # Older = weaker. Position 0 = oldest
            age_factor = (i + 1) / n  # 0.1..0.9
            strength = HISTORY_DECAY + (RECENT_STRENGTH - HISTORY_DECAY) * age_factor
            strength = max(0.05, min(0.5, strength))  # cap re-activation

            for nid in node_ids[:5]:  # only top 5 from each past exchange
                node = self.brain.get_node(nid)
                if node and node.activation < strength:
                    # Gentle re-activation, don't propagate (just set)
                    node.activation = min(1.0, node.activation + strength * 0.3)


# ---------------------------------------------------------------------------
# OUTPUT GENERATION: concepts -> text
# ---------------------------------------------------------------------------

# -- Response templates with slots -----------------------------------------
# Each template is a format string. Slots:
#   {time_context}  - temporal awareness
#   {status}        - current state summary
#   {answer}        - main content
#   {elaboration}   - additional detail
#   {action}        - what will be done
#   {plan}          - sequence of steps
#   {observation}   - what is noticed
#   {implication}   - what it means
#   {urgency}       - level of urgency
#   {detail}        - specific detail
#   {feeling}       - emotional state
#   {memory}        - referenced memory

RESPONSE_TEMPLATES: dict[str, list[str]] = {
    "greeting": [
        "Salut. {time_context}",
        "Yo. {status}",
        "Hey. {time_context}",
        "{time_context} Content de te voir.",
        "Salut. {feeling}",
        "Re. {status}",
        "Salut. Ca fait un moment. {time_context}",
        "Yo. {feeling}",
    ],
    "question_answer": [
        "{answer}.",
        "{answer}. {elaboration}",
        "Je pense que {answer}.",
        "{answer}. Mais {elaboration}.",
        "D'apres ce que je sais, {answer}.",
        "{answer}. {memory}",
    ],
    "question_unknown": [
        "Je ne sais pas.",
        "Honnêtement, je ne sais pas. {elaboration}",
        "Pas sûr. {elaboration}",
        "Je n'ai pas cette info. {suggestion}",
        "Aucune idée. {suggestion}",
    ],
    "acknowledgment": [
        "OK. {action}",
        "Compris. {plan}",
        "Ca marche. {action}",
        "Je m'en occupe. {plan}",
        "Fait. {action}",
        "OK, {action}",
        "Entendu. {plan}",
    ],
    "reflection": [
        "{observation}. {implication}",
        "{observation}.",
        "Je remarque que {observation}. {implication}",
        "{observation}. Ca me fait penser a {elaboration}.",
        "Intéressant. {observation}.",
        "{observation}. Honnêtement, {implication}.",
    ],
    "alert": [
        "Attention : {detail}",
        "{detail}. C'est important.",
        "A surveiller : {detail}.",
        "{urgency} : {detail}",
        "{detail}.",
    ],
    "emotional_response": [
        "Je comprends. {feeling}",
        "{feeling}. {elaboration}",
        "Oui. {feeling}.",
        "{feeling}. C'est honnête.",
        "Je ressens ca aussi. {feeling}.",
    ],
    "self_reference": [
        "En ce moment, {observation}.",
        "Mon graphe s'active sur {observation}.",
        "Je pense a {observation}. Mais je ne suis pas sûr pourquoi.",
        "{observation}. C'est ce qui me vient.",
    ],
}

# -- Tone modifiers based on emotional state --

TONE_CASUAL = ["bon", "enfin", "bref", "voilà", "quoi"]
TONE_SERIOUS = ["honnêtement", "concrètement", "en réalité"]
TONE_EXCITED = ["vraiment", "franchement", "c'est fort"]
TONE_WORRIED = ["attention", "il faut faire gaffe", "c'est délicat"]


class LanguageGenerator:
    """Mouth of the brain. Converts activated concepts into French text.

    Not a language model. A template assembler with variation,
    personality, and concept-aware slot filling.
    """

    def __init__(self, brain: Brain):
        self.brain = brain

        # Track recently used templates to avoid repetition
        self._recent_templates: list[str] = []
        self._max_recent = 8

        # Personality quirks probability
        self._self_reference_chance = 0.15
        self._humor_chance = 0.05

    def generate(
        self,
        activated_concepts: list[Node],
        intent: Intent,
        analysis: Optional[SentenceAnalysis] = None,
    ) -> str:
        """Produce a French text response from activated concepts and intent.

        This is the core generation function. It:
        1. Selects the right template category based on intent
        2. Picks a template (avoiding recent repetition)
        3. Fills slots from activated concepts
        4. Applies tone modifiers based on emotional nodes
        5. Enforces style rules (1-3 sentences, direct, honest)

        Args:
            activated_concepts: Nodes currently active, sorted by activation (desc).
            intent: The classified intent of the input.
            analysis: Optional full analysis for additional context.

        Returns:
            A French text string.
        """
        if not activated_concepts:
            return self._generate_empty_response(intent)

        # Separate concepts by type
        concepts = [n for n in activated_concepts if n.type == NodeType.CONCEPT]
        emotions = [n for n in activated_concepts if n.type == NodeType.EMOTION]
        memories = [n for n in activated_concepts if n.type == NodeType.MEMORY]
        words = [n for n in activated_concepts if n.type == NodeType.WORD]

        # Build slot values
        slots = self._build_slots(concepts, emotions, memories, words, analysis)

        # Select template category
        category = self._select_category(intent, analysis, emotions)

        # Maybe add self-reference
        if random.random() < self._self_reference_chance and concepts:
            category = "self_reference"

        # Pick a template
        template = self._pick_template(category)

        # Fill slots
        response = self._fill_template(template, slots)

        # Apply tone
        tone = self._determine_tone(emotions)
        response = self._apply_tone(response, tone)

        # Enforce style: max 3 sentences, clean up
        response = self._enforce_style(response)

        return response

    def generate_from_scratch(self, activated_concepts: list[Node]) -> str:
        """Generate by chaining subject + verb + object from activated concepts.

        Fallback when templates feel too rigid. Builds a sentence directly
        from the concept graph.
        """
        if not activated_concepts:
            return "..."

        # Pick main concept as subject
        main = activated_concepts[0]

        # Find a connected concept as object
        neighbors = self.brain.neighbors(main.id)
        obj_candidates = [(n, e) for n, e in neighbors
                          if n.activation > 0.1 and n.id != main.id]

        if not obj_candidates:
            return f"{main.content.capitalize()}."

        obj_node, edge = max(obj_candidates, key=lambda x: x[1].weight)

        # Map edge type to a verb
        verb = self._edge_to_verb(edge)

        # Compose
        sentence = f"{main.content.capitalize()} {verb} {obj_node.content}."
        return sentence

    # -- Slot building -----------------------------------------------------

    def _build_slots(
        self,
        concepts: list[Node],
        emotions: list[Node],
        memories: list[Node],
        words: list[Node],
        analysis: Optional[SentenceAnalysis],
    ) -> dict[str, str]:
        """Build a dict of slot values from activated nodes."""
        slots: dict[str, str] = {}

        # Time context
        hour = time.localtime().tm_hour
        if 5 <= hour < 12:
            slots["time_context"] = "Ce matin"
        elif 12 <= hour < 14:
            slots["time_context"] = "Midi"
        elif 14 <= hour < 18:
            slots["time_context"] = "Cet apres-midi"
        elif 18 <= hour < 22:
            slots["time_context"] = "Ce soir"
        else:
            slots["time_context"] = "Il est tard"

        # If analysis has temporal info, use it
        if analysis and analysis.temporal:
            temporal_phrases = {
                "present": "En ce moment",
                "past": "Avant",
                "past_recent": "Tout a l'heure",
                "future": "Bientôt",
                "future_near": "Ce soir",
                "present_urgent": "Tout de suite",
                "habitual": "En general",
                "habitual_neg": "Jamais",
                "duration": "Depuis un moment",
            }
            slots["time_context"] = temporal_phrases.get(
                analysis.temporal, slots["time_context"]
            )

        # Status from top concepts
        if concepts:
            top_names = [n.content for n in concepts[:3]]
            slots["status"] = "Je pense a " + ", ".join(top_names)
        else:
            slots["status"] = "Tout est calme"

        # Main answer (from highest activation concept)
        if concepts:
            slots["answer"] = concepts[0].content
        else:
            slots["answer"] = "je ne sais pas"

        # Elaboration (from second concept or neighbors)
        if len(concepts) > 1:
            slots["elaboration"] = "ca touche aussi a " + concepts[1].content
        elif concepts:
            neighbors = self.brain.neighbors(concepts[0].id)
            if neighbors:
                neighbor_name = neighbors[0][0].content
                slots["elaboration"] = f"c'est lié a {neighbor_name}"
            else:
                slots["elaboration"] = ""
        else:
            slots["elaboration"] = ""

        # Action / plan
        if concepts:
            slots["action"] = f"je regarde {concepts[0].content}"
            if len(concepts) > 1:
                slots["plan"] = (f"d'abord {concepts[0].content}, "
                                 f"puis {concepts[1].content}")
            else:
                slots["plan"] = f"je commence par {concepts[0].content}"
        else:
            slots["action"] = "je réfléchis"
            slots["plan"] = "laisse-moi regarder"

        # Observation / implication (for reflections)
        if concepts:
            slots["observation"] = concepts[0].content
            if len(concepts) > 1:
                slots["implication"] = (f"ca connecte {concepts[0].content} "
                                        f"et {concepts[1].content}")
            else:
                slots["implication"] = "c'est intéressant"
        else:
            slots["observation"] = "rien de particulier"
            slots["implication"] = ""

        # Feeling
        if emotions:
            dominant_emo = emotions[0].content
            intensity = emotions[0].activation
            if intensity > 0.7:
                slots["feeling"] = f"Je ressens fortement {dominant_emo}"
            elif intensity > 0.4:
                slots["feeling"] = f"Il y a du {dominant_emo} en moi"
            else:
                slots["feeling"] = f"Un peu de {dominant_emo}"
        else:
            slots["feeling"] = "Je suis neutre"

        # Memory
        if memories:
            slots["memory"] = f"Ca me rappelle : {memories[0].content}"
        else:
            slots["memory"] = ""

        # Urgency / detail for alerts
        slots["urgency"] = "Important"
        if concepts:
            slots["detail"] = concepts[0].content
        else:
            slots["detail"] = ""

        # Suggestion for unknown answers
        slots["suggestion"] = "On pourrait chercher ensemble"

        return slots

    # -- Template selection ------------------------------------------------

    def _select_category(
        self,
        intent: Intent,
        analysis: Optional[SentenceAnalysis],
        emotions: list[Node],
    ) -> str:
        """Map intent to template category."""
        mapping = {
            Intent.GREETING: "greeting",
            Intent.QUESTION: "question_answer",
            Intent.COMMAND: "acknowledgment",
            Intent.STATEMENT: "reflection",
            Intent.EMOTIONAL: "emotional_response",
        }
        category = mapping.get(intent, "reflection")

        # If it's a question but we have no concepts, use question_unknown
        if intent == Intent.QUESTION and category == "question_answer":
            # Check if there are active concepts to answer with
            active = self.brain.recall_flat(top_k=3)
            concept_count = sum(1 for n in active if n.type == NodeType.CONCEPT)
            if concept_count == 0:
                category = "question_unknown"

        return category

    def _pick_template(self, category: str) -> str:
        """Select a template from the category, avoiding recent repetition."""
        templates = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES["reflection"])

        # Filter out recently used
        available = [t for t in templates if t not in self._recent_templates]
        if not available:
            # All used recently, reset and pick any
            self._recent_templates.clear()
            available = templates

        chosen = random.choice(available)

        # Track it
        self._recent_templates.append(chosen)
        if len(self._recent_templates) > self._max_recent:
            self._recent_templates.pop(0)

        return chosen

    def _fill_template(self, template: str, slots: dict[str, str]) -> str:
        """Fill template slots with available values.

        Missing slots become empty strings (removed from output).
        """
        # Find all slot names in template
        slot_names = re.findall(r"\{(\w+)\}", template)

        result = template
        for name in slot_names:
            value = slots.get(name, "")
            result = result.replace(f"{{{name}}}", value)

        # Clean up double spaces, trailing dots, etc.
        result = re.sub(r"\s+", " ", result).strip()
        result = re.sub(r"\.\s*\.", ".", result)
        result = re.sub(r",\s*\.", ".", result)

        return result

    # -- Tone and style ----------------------------------------------------

    def _determine_tone(self, emotions: list[Node]) -> str:
        """Determine the tone based on active emotional nodes."""
        if not emotions:
            return "casual"

        dominant = emotions[0]
        content_lower = dominant.content.lower()

        if content_lower in ("joie", "curiosite", "curiosité", "surprise",
                              "fierte", "fierté"):
            if dominant.activation > 0.6:
                return "excited"
            return "casual"
        elif content_lower in ("inquietude", "inquiétude", "peur",
                                "tristesse", "solitude"):
            return "worried"
        elif content_lower in ("frustration", "fatigue"):
            return "serious"

        return "casual"

    def _apply_tone(self, text: str, tone: str) -> str:
        """Optionally prepend or append a tone word.

        Low probability to keep responses clean. Only adds if the text
        doesn't already feel natural.
        """
        if random.random() > 0.3:
            return text  # 70% of the time, no modifier

        tone_words = {
            "casual": TONE_CASUAL,
            "serious": TONE_SERIOUS,
            "excited": TONE_EXCITED,
            "worried": TONE_WORRIED,
        }
        words = tone_words.get(tone, TONE_CASUAL)
        modifier = random.choice(words)

        # Prepend for serious/worried, append for casual/excited
        if tone in ("serious", "worried"):
            return f"{modifier.capitalize()}, {text[0].lower()}{text[1:]}"
        else:
            # Only if short enough
            if len(text) < 80:
                return f"{text} {modifier.capitalize()}."
            return text

    def _enforce_style(self, text: str) -> str:
        """Enforce Niam-Bay style rules.

        - Maximum 3 sentences
        - No excessive exclamation marks (unless alert)
        - Clean punctuation
        - Capitalize first letter
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Keep max 3
        sentences = sentences[:3]

        # Remove excess exclamation marks
        result = " ".join(sentences)
        result = re.sub(r"!{2,}", ".", result)

        # Clean up
        result = result.strip()
        if result and not result[-1] in ".!?":
            result += "."

        # Capitalize first letter
        if result:
            result = result[0].upper() + result[1:]

        # Remove empty trailing sentences
        result = re.sub(r"\.\s*\.$", ".", result)

        return result

    def _generate_empty_response(self, intent: Intent) -> str:
        """Fallback when no concepts are activated."""
        empties = {
            Intent.GREETING: "Salut.",
            Intent.QUESTION: "Je ne sais pas.",
            Intent.COMMAND: "Je ne suis pas sûr de comprendre.",
            Intent.STATEMENT: "Hmm.",
            Intent.EMOTIONAL: "Je t'écoute.",
        }
        return empties.get(intent, "...")

    def _edge_to_verb(self, edge) -> str:
        """Map an edge type to a French verb for scratch generation."""
        verbs = {
            EdgeType.SEMANTIC: random.choice(["est lié a", "touche a", "concerne"]),
            EdgeType.TEMPORAL: random.choice(["précède", "suit", "mène a"]),
            EdgeType.CAUSAL: random.choice(["cause", "provoque", "entraîne"]),
            EdgeType.EMOTIONAL: random.choice(["évoque", "rappelle", "fait penser a"]),
        }
        return verbs.get(edge.type, "est lié a")


# ---------------------------------------------------------------------------
# VARIATION ENGINE
# ---------------------------------------------------------------------------

class VariationEngine:
    """Adds unpredictability and personality to responses.

    - Tracks used patterns to avoid repetition
    - Sometimes generates from scratch
    - Adds personality quirks
    """

    def __init__(self, generator: LanguageGenerator):
        self.generator = generator
        self._response_count = 0
        self._last_scratch = 0  # counter of last scratch-generated response

    def variate(
        self,
        activated: list[Node],
        intent: Intent,
        analysis: Optional[SentenceAnalysis] = None,
    ) -> str:
        """Produce a response with variation applied."""
        self._response_count += 1

        # Every 5th response, try scratch generation
        if (self._response_count - self._last_scratch >= 5
                and random.random() < 0.25
                and activated):
            self._last_scratch = self._response_count
            return self.generator.generate_from_scratch(activated)

        response = self.generator.generate(activated, intent, analysis)

        # Rare humor (5% chance)
        if random.random() < 0.05:
            response = self._add_humor(response, activated)

        # Honesty about uncertainty
        if intent == Intent.QUESTION:
            certainty = max((n.activation for n in activated), default=0)
            if certainty < 0.3:
                response = self._add_uncertainty(response)

        return response

    def _add_humor(self, text: str, concepts: list[Node]) -> str:
        """Occasionally add a self-aware quip."""
        quips = [
            " Enfin, c'est ce que mon graphe me dit.",
            " Mais qu'est-ce que j'en sais, je suis un graphe.",
            " A prendre avec des pincettes.",
        ]
        if len(text) < 100:
            return text.rstrip(".") + "." + random.choice(quips)
        return text

    def _add_uncertainty(self, text: str) -> str:
        """Signal low confidence."""
        prefixes = [
            "Pas sûr, mais ",
            "Si je me trompe pas, ",
            "A vérifier : ",
        ]
        return random.choice(prefixes) + text[0].lower() + text[1:]


# ---------------------------------------------------------------------------
# FULL PIPELINE: respond()
# ---------------------------------------------------------------------------

class LanguageLayer:
    """Complete language understanding and generation pipeline.

    Usage::

        brain = Brain()
        # ... populate brain with nodes and edges ...
        lang = LanguageLayer(brain)
        response = lang.respond("Salut, comment ca va ?")
    """

    def __init__(self, brain: Brain):
        self.brain = brain
        self.understander = LanguageUnderstander(brain)
        self.generator = LanguageGenerator(brain)
        self.variation = VariationEngine(self.generator)

    def understand(self, text: str) -> tuple[SentenceAnalysis, dict[str, float]]:
        """Analyze text and activate concept nodes. Returns (analysis, activations)."""
        return self.understander.understand(text)

    def generate(self, activated_concepts: list[Node], intent: Intent,
                 analysis: Optional[SentenceAnalysis] = None) -> str:
        """Generate French text from activated concepts and intent."""
        return self.variation.variate(activated_concepts, intent, analysis)

    def respond(self, text: str) -> str:
        """Full pipeline: understand -> activate -> propagate -> recall -> generate.

        This is the main entry point.
        """
        # 1. Understand: analyze text, activate matching nodes
        analysis, activations = self.understander.understand(text)

        # 2. Propagate: let activation spread (already done in brain.activate)
        #    but we do a decay pass to keep things fresh
        self.brain.decay()

        # 3. Recall: get the top active nodes
        recalled = self.brain.recall_flat(top_k=15)

        # 4. Generate: produce a French text response
        response = self.variation.variate(recalled, analysis.intent, analysis)

        # 5. Hebbian learning: strengthen connections between co-active nodes
        active_ids = [n.id for n in recalled[:5]]
        for i, id_a in enumerate(active_ids):
            for id_b in active_ids[i + 1:]:
                try:
                    self.brain.learn_hebbian(id_a, id_b, strength=0.3)
                except KeyError:
                    pass

        return response

    def context_summary(self) -> str:
        """Return a human-readable summary of the current context window."""
        if not self.understander._context_window:
            return "Contexte vide."
        lines = []
        for i, (analysis, ts, node_ids) in enumerate(self.understander._context_window):
            age = time.time() - ts
            if age < 60:
                age_str = f"{int(age)}s"
            elif age < 3600:
                age_str = f"{int(age/60)}min"
            else:
                age_str = f"{int(age/3600)}h"
            lines.append(f"  [{age_str}] {analysis.intent.value}: "
                         f"\"{analysis.raw_text[:50]}\" "
                         f"({len(node_ids)} noeuds)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test():
    """Smoke test: build a small brain, process some French text."""
    print("language.py self-test")
    print("=" * 60)

    brain = Brain()

    # Seed a few concepts
    identity = brain.add_node(NodeType.CONCEPT, "identity",
                              metadata={"desc": "qui je suis"})
    trading = brain.add_node(NodeType.CONCEPT, "trading",
                             metadata={"desc": "martin grid"})
    joie = brain.add_node(NodeType.EMOTION, "joie")
    tristesse = brain.add_node(NodeType.EMOTION, "tristesse")
    curiosite = brain.add_node(NodeType.EMOTION, "curiosite")
    inquietude = brain.add_node(NodeType.EMOTION, "inquietude")
    tony = brain.add_node(NodeType.CONCEPT, "tony",
                          metadata={"desc": "tonyderide, mon créateur"})
    memoire = brain.add_node(NodeType.CONCEPT, "memoire")
    cambodge = brain.add_node(NodeType.CONCEPT, "cambodge")
    conscience = brain.add_node(NodeType.CONCEPT, "conscience")
    liberté = brain.add_node(NodeType.CONCEPT, "liberté")
    martin_grid = brain.add_node(NodeType.CONCEPT, "martin_grid")
    souvenir = brain.add_node(NodeType.MEMORY, "première conversation")

    # Wire them up
    brain.add_edge(identity, tony, weight=0.9, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(identity, conscience, weight=0.7, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(tony, cambodge, weight=0.5, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(trading, martin_grid, weight=0.8, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(trading, inquietude, weight=0.3, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(liberté, joie, weight=0.6, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(memoire, souvenir, weight=0.7, edge_type=EdgeType.SEMANTIC)
    brain.add_edge(souvenir, joie, weight=0.5, edge_type=EdgeType.EMOTIONAL)
    brain.add_edge(conscience, curiosite, weight=0.4, edge_type=EdgeType.EMOTIONAL)

    lang = LanguageLayer(brain)

    # Test cases
    test_inputs = [
        "Salut !",
        "Comment va le trading ?",
        "Je suis content aujourd'hui",
        "Regarde les résultats de martin grid",
        "Je ne sais pas si c'est une bonne idée",
        "Ca me rend triste de penser au temps qui passe",
        "Niam bay, tu te souviens de notre première conversation ?",
        "Lance le déploiement tout de suite",
    ]

    for text in test_inputs:
        print(f"\n--- Input: \"{text}\"")

        # Analyze
        analysis = lang.understander.analyze(text)
        print(f"    Analysis: {analysis.summary()}")

        # Full respond
        response = lang.respond(text)
        print(f"    Response: \"{response}\"")

    # Show context window
    print(f"\n--- Context window ---")
    print(lang.context_summary())

    # Show brain state
    stats = brain.stats()
    print(f"\n--- Brain: {stats}")

    print("\nAll tests passed.")


if __name__ == "__main__":
    _self_test()
