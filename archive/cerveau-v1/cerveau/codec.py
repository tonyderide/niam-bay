"""
NB-1 : Niam-Bay Protocol 1 — Compression codec for LLM communication.

Reduces token count between Tony and Claude by encoding messages
into a compact format using a shared codebook.

Usage:
    from codec import NB1Codec
    codec = NB1Codec()
    encoded = codec.encode("Bonjour Tony, comment ça va ce soir ?")
    decoded = codec.decode(encoded)
    codec.stats()
"""

import json
import re
from pathlib import Path
from typing import Optional


class NB1Codec:
    """NB-1 encoder/decoder engine."""

    VERSION = "NB-1"
    DEFAULT_CODEBOOK = Path(__file__).parent / "codebook.json"

    # --- Built-in dictionary ---

    # Multi-word phrases MUST come before single words (longest match first)
    PHRASES = {
        # Greetings / common phrases
        "comment ça va": "?cv",
        "comment ca va": "?cv",
        "je ne sais pas": "jsp",
        "qu'est-ce que": "qsq",
        "quest-ce que": "qsq",
        "s'il te plaît": "stp",
        "s'il te plait": "stp",
        "s'il vous plaît": "svp",
        "parce que": "pq",
        "est-ce que": "esq",
        "il y a": "iya",
        "c'est-à-dire": "cad",
        "en train de": "etd",
        "je voudrais": "jvd",
        "je veux": "jvx",
        "je pense": "jpn",
        "je suis": "jss",
        "il faut": "ilf",
        "on peut": "onp",
        "on va": "onv",
        "ça va": "cv",
        "ça marche": "cm",
        "pas mal": "pm",
        "bien sûr": "bs",
        "tout de suite": "tds",
        "en fait": "ef",
        "du coup": "dcp",
        "peut-être": "pe",
        "c'est bon": "cb",
        "ce soir": "@sr",
        "ce matin": "@mt",
        "demain matin": "dm@mt",
        "après le boulot": "a@blt",
        "à bientôt": "abt",
    }

    # Single words
    WORDS = {
        # Project-specific
        "grid": "G",
        "martin": "M",
        "naissance": "N",
        "cerveau": "C",
        "trading": "T",
        "ethereum": "E",
        "eth": "E",
        "bitcoin": "B",
        "btc": "B",
        "ollama": "O",
        "token": "tk",
        "tokens": "tks",
        "agent": "ag",
        "codebook": "cb",
        "codec": "cc",
        "proxy": "px",
        "compression": "cmp",
        "protocole": "ptc",

        # People
        "tony": "T1",
        "tonyderide": "T1",
        "mélanie": "M1",
        "melanie": "M1",
        "marine": "M2",
        "jade": "J1",
        "niam-bay": "NB",
        "claude": "CL",

        # Common French words
        "bonjour": "bj",
        "bonsoir": "bsr",
        "salut": "slt",
        "merci": "mrc",
        "oui": "o",
        "non": "n",
        "maintenant": "mtn",
        "aujourd'hui": "ajd",
        "demain": "dm",
        "hier": "hr",
        "toujours": "tjr",
        "jamais": "jms",
        "beaucoup": "bcp",
        "quelque chose": "qqc",
        "quelqu'un": "qqn",
        "pourquoi": "pqo",
        "comment": "cmt",
        "combien": "cbn",
        "quand": "qd",
        "avec": "av",
        "sans": "ss",
        "dans": "ds",
        "pour": "pr",
        "chez": "cz",
        "entre": "etr",
        "depuis": "dps",
        "pendant": "pdt",
        "avant": "avt",
        "après": "apr",
        "entre": "etr",
        "sur": "sr",
        "sous": "so",
        "contre": "ctr",

        # Common verbs
        "faire": "fr",
        "fait": "ft",
        "vouloir": "vl",
        "pouvoir": "pv",
        "savoir": "sv",
        "comprendre": "cp",
        "construire": "cs",
        "construises": "css",
        "regarder": "rg",
        "attendre": "at",
        "attend": "at",
        "travailler": "tv",
        "tourne": "trn",
        "tourner": "trn",
        "installer": "ist",
        "déployer": "dpl",
        "tester": "tst",
        "lancer": "lnc",
        "voir": "vr",
        "aller": "alr",
        "dire": "dr",
        "prendre": "pdr",
        "donner": "dnr",
        "mettre": "mtr",
        "venir": "vnr",
        "partir": "ptr",
        "rester": "rst",
        "envoyer": "env",
        "recevoir": "rcv",
        "créer": "crr",
        "modifier": "mdf",
        "supprimer": "spr",
        "chercher": "crc",
        "trouver": "trv",
        "essayer": "esy",

        # Connectors
        "mais": "ms",
        "donc": "dc",
        "aussi": "as",
        "encore": "ec",
        "alors": "alr",
        "comme": "cm",
        "cependant": "cpd",
        "pourtant": "prt",
        "sinon": "snn",
        "puis": "ps",

        # Tech/domain
        "machine": "mch",
        "service": "svc",
        "stable": "stb",
        "dollars": "$",
        "minutes": "mn",
        "heures": "h",
        "secondes": "s",
        "sell": "SL",
        "buy": "BY",
        "serveur": "svr",
        "démarrer": "dmr",
        "arrêter": "art",
        "mémoire": "mem",
        "fichier": "fch",
        "dossier": "dsr",
        "réseau": "rso",
        "connexion": "cnx",
        "erreur": "err",
        "problème": "pbm",
        "solution": "sln",
        "résultat": "res",
        "paramètre": "prm",
        "configuration": "cfg",
    }

    # Articles to strip (only when standalone)
    ARTICLES = {"le", "la", "les", "un", "une", "des", "du", "de", "l'", "d'"}

    # Filler words to strip
    FILLERS = {"bien", "très", "vraiment", "assez", "plutôt", "tellement", "juste"}

    def __init__(self, codebook_path: Optional[str] = None):
        self.codebook_path = Path(codebook_path) if codebook_path else self.DEFAULT_CODEBOOK
        self.custom_entries: dict[str, str] = {}
        self._encode_count = 0
        self._total_original = 0
        self._total_compressed = 0

        # Load persisted codebook if it exists
        if self.codebook_path.exists():
            self.load_codebook()

        # Build combined dictionary (custom entries override defaults)
        self._rebuild_lookup()

    def _rebuild_lookup(self):
        """Rebuild the lookup tables after any change."""
        # Merge all phrases and words, custom overrides last
        self.all_phrases = dict(self.PHRASES)
        self.all_words = dict(self.WORDS)
        # Custom entries go into words by default
        self.all_words.update(self.custom_entries)

        # Build reverse map for decoding
        self.reverse_phrases = {v: k for k, v in self.all_phrases.items()}
        self.reverse_words = {v: k for k, v in self.all_words.items()}

        # Sort phrases by length (longest first) for greedy matching
        self._sorted_phrases = sorted(self.all_phrases.items(), key=lambda x: len(x[0]), reverse=True)
        self._sorted_words = sorted(self.all_words.items(), key=lambda x: len(x[0]), reverse=True)

        # For decoding: sort codes by length descending
        self._sorted_rev_phrases = sorted(self.reverse_phrases.items(), key=lambda x: len(x[0]), reverse=True)
        self._sorted_rev_words = sorted(self.reverse_words.items(), key=lambda x: len(x[0]), reverse=True)

    # ---- Encoding ----

    def encode(self, text: str) -> str:
        """Encode French text into NB-1 compressed format."""
        original_len = len(text)
        result = text

        # Step 1: Replace multi-word phrases (case-insensitive)
        for phrase, code in self._sorted_phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            result = pattern.sub(code, result)

        # Step 2: Remove articles (standalone, word-boundary)
        for article in self.ARTICLES:
            if article.endswith("'"):
                # l' and d' — remove the article but keep what follows
                pattern = re.compile(r"\b" + re.escape(article), re.IGNORECASE)
                result = pattern.sub("", result)
            else:
                pattern = re.compile(r"\b" + re.escape(article) + r"\b", re.IGNORECASE)
                result = pattern.sub("", result)

        # Step 3: Remove filler words
        for filler in self.FILLERS:
            pattern = re.compile(r"\b" + re.escape(filler) + r"\b", re.IGNORECASE)
            result = pattern.sub("", result)

        # Step 4: Replace single words (case-insensitive, word boundaries)
        for word, code in self._sorted_words:
            pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
            result = pattern.sub(code, result)

        # Step 5: Clean up whitespace
        result = re.sub(r"[ \t]+", " ", result)         # collapse spaces
        result = re.sub(r" ([,;:?.!])", r"\1", result)  # no space before punctuation
        result = re.sub(r"^\s+", "", result, flags=re.MULTILINE)  # leading spaces
        result = result.strip()

        # Stats tracking
        compressed_len = len(result)
        self._encode_count += 1
        self._total_original += original_len
        self._total_compressed += compressed_len

        return result

    # ---- Decoding ----

    def decode(self, compressed: str) -> str:
        """Decode NB-1 compressed text back to (approximate) French."""
        result = compressed

        # Step 1: Expand phrase codes first (they can contain word-code chars)
        for code, phrase in self._sorted_rev_phrases:
            # Use word-boundary-aware replacement
            pattern = re.compile(r"(?<!\w)" + re.escape(code) + r"(?!\w)")
            result = pattern.sub(phrase, result)

        # Step 2: Expand word codes
        for code, word in self._sorted_rev_words:
            if len(code) < 2 and code.isalpha() and code.islower():
                # Very short lowercase codes -- be careful about false matches
                pattern = re.compile(r"(?<!\w)" + re.escape(code) + r"(?!\w)")
            else:
                pattern = re.compile(r"(?<!\w)" + re.escape(code) + r"(?!\w)")
            result = pattern.sub(word, result)

        # Clean up spacing
        result = re.sub(r"[ \t]+", " ", result)
        result = re.sub(r" ([,;:?.!])", r"\1", result)
        result = result.strip()

        return result

    # ---- Codebook persistence ----

    def save_codebook(self):
        """Save the full codebook (built-in + custom) to JSON."""
        data = {
            "version": self.VERSION,
            "phrases": dict(self.PHRASES),
            "words": dict(self.WORDS),
            "custom": self.custom_entries,
        }
        with open(self.codebook_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_codebook(self):
        """Load custom entries from persisted codebook."""
        try:
            with open(self.codebook_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.custom_entries = data.get("custom", {})
            self._rebuild_lookup()
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def add_entry(self, word: str, code: str):
        """Learn a new compression entry."""
        self.custom_entries[word.lower()] = code
        self._rebuild_lookup()

    # ---- Stats ----

    def stats(self) -> dict:
        """Return compression statistics."""
        ratio = (1 - self._total_compressed / self._total_original) * 100 if self._total_original > 0 else 0
        return {
            "version": self.VERSION,
            "phrases": len(self.all_phrases),
            "words": len(self.all_words),
            "custom_entries": len(self.custom_entries),
            "encodes": self._encode_count,
            "original_chars": self._total_original,
            "compressed_chars": self._total_compressed,
            "compression_ratio": f"{ratio:.1f}%",
        }

    def get_full_codebook_md(self) -> str:
        """Export the full codebook as markdown (for claude_codebook.md)."""
        lines = [
            f"# NB-1 Codebook (Niam-Bay Protocol 1)",
            "",
            "## Phrases",
            "| Expression | Code |",
            "|---|---|",
        ]
        for phrase, code in sorted(self.all_phrases.items()):
            lines.append(f"| {phrase} | `{code}` |")

        lines += [
            "",
            "## Mots",
            "| Mot | Code |",
            "|---|---|",
        ]
        for word, code in sorted(self.all_words.items()):
            lines.append(f"| {word} | `{code}` |")

        lines += [
            "",
            "## Articles supprimés",
            ", ".join(sorted(self.ARTICLES)),
            "",
            "## Mots de remplissage supprimés",
            ", ".join(sorted(self.FILLERS)),
            "",
            "## Règles",
            "- Les articles (le, la, les, un, une, des, du, de, l', d') sont supprimés",
            "- Les fillers (bien, très, vraiment...) sont supprimés sauf si porteurs de sens",
            "- Les nombres restent tels quels",
            "- `?` = question, `!` = emphase, `>` = resulte en, `=` = signifie, `+` = et/aussi, `@` = lieu/temps",
        ]
        return "\n".join(lines)


# ---- CLI test mode ----

def run_tests():
    """Run the codec on sample sentences and print results."""
    codec = NB1Codec()

    test_sentences = [
        "Bonjour Tony, comment ça va ce soir ?",
        "La grid ETH a fait un sell à 2153 dollars, on attend le buy",
        "Je voudrais que tu construises le cerveau avec Ollama sur la machine",
        "Martin tourne sur la VM, le service est stable depuis 40 minutes",
        "Mélanie est chez elle, je vais la voir demain après le boulot",
    ]

    print("=" * 70)
    print(f"  NB-1 Codec — Test Suite")
    print("=" * 70)

    for sentence in test_sentences:
        encoded = codec.encode(sentence)
        decoded = codec.decode(encoded)
        orig_len = len(sentence)
        enc_len = len(encoded)
        ratio = (1 - enc_len / orig_len) * 100

        print()
        print(f"  ORIGINAL  ({orig_len:3d} chars): {sentence}")
        print(f"  ENCODED   ({enc_len:3d} chars): {encoded}")
        print(f"  DECODED              : {decoded}")
        print(f"  RATIO                : {ratio:.1f}% reduction")

    print()
    print("-" * 70)
    s = codec.stats()
    print(f"  Aggregate stats: {s['encodes']} encodes, "
          f"{s['original_chars']} -> {s['compressed_chars']} chars, "
          f"{s['compression_ratio']} overall reduction")
    print(f"  Codebook: {s['phrases']} phrases + {s['words']} words")
    print("-" * 70)

    # Save codebook
    codec.save_codebook()
    print(f"\n  Codebook saved to {codec.codebook_path}")

    return codec


if __name__ == "__main__":
    run_tests()
