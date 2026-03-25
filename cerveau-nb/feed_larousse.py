#!/usr/bin/env python3
"""
Nourrir le cerveau avec le dictionnaire Larousse.
Scrape les définitions depuis larousse.fr et les injecte dans le cerveau.

Usage:
    python feed_larousse.py                # Feed les mots courants
    python feed_larousse.py --limit 100    # Limiter à 100 mots
    python feed_larousse.py --resume       # Reprendre où on s'est arrêté
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import re
import argparse
import html
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain

BRAIN_PATH = Path(__file__).parent / "brain_state.json"
PROGRESS_PATH = Path(__file__).parent / "larousse_progress.json"


def get_larousse_definition(word: str) -> str | None:
    """Fetch definition from Larousse.fr"""
    try:
        # URL-encode the word properly for accented characters
        safe_word = urllib.parse.quote(word, safe='')
        url = f'https://www.larousse.fr/dictionnaires/francais/{safe_word}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8', errors='ignore')

        # Extract definitions
        defs = re.findall(
            r'<li[^>]*class="DivisionDefinition"[^>]*>(.*?)</li>',
            raw, re.DOTALL
        )

        results = []
        for d in defs[:3]:
            # Clean HTML
            clean = re.sub(r'<[^>]+>', ' ', d)
            clean = html.unescape(clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            # Remove "Synonymes :" and after
            clean = re.split(r'Synonyme|Contraire|Homonyme', clean)[0].strip()
            if len(clean) > 10:
                results.append(clean)

        if results:
            return ' | '.join(results[:3])

    except Exception:
        pass
    return None


def feed_word(brain: Brain, word: str, definition: str) -> int:
    """Inject a word + Larousse definition into the brain."""
    edges = 0

    # Find or create word node
    word_id = None
    for nid, node in brain._nodes.items():
        if node.content.lower() == word.lower() and "word" in str(node.type).lower():
            word_id = nid
            break

    if not word_id:
        word_id = brain.add_node(
            "word", word,
            decay_rate=0.001,
            metadata={"source": "larousse", "lang": "fr"}
        )

    # Create concept node for definition
    concept_id = brain.add_node(
        "concept", f"{word}: {definition[:250]}",
        decay_rate=0.002,
        metadata={"source": "larousse", "word": word}
    )

    # Link word to definition
    brain.learn_hebbian(word_id, concept_id, 0.8)
    edges += 1

    # Cross-link with existing words in definition
    def_words = set()
    for w in definition.lower().replace("'", " ").replace("\u2019", " ").split():
        clean = "".join(c for c in w if c.isalnum() or c == "-")
        if clean and len(clean) > 4:
            def_words.add(clean)

    for nid, node in brain._nodes.items():
        if nid in (word_id, concept_id):
            continue
        if "word" in str(node.type).lower() and node.content.lower() in def_words:
            brain.learn_hebbian(word_id, nid, 0.3)
            edges += 1

    return edges


# Mots courants français (sans doublons avec feed_dictionary.py)
WORDS = [
    # Verbes courants
    "abandonner", "aborder", "absorber", "accompagner", "accomplir",
    "accueillir", "adapter", "admirer", "adopter", "affirmer",
    "agiter", "ajouter", "alimenter", "allumer", "analyser",
    "annoncer", "apparaître", "appartenir", "appliquer", "apporter",
    "approcher", "approuver", "arracher", "arranger", "assister",
    "assurer", "atteindre", "attirer", "avancer", "avouer",
    "balancer", "bâtir", "battre", "blesser", "bloquer",
    "bouger", "briller", "briser", "brûler", "calculer",
    "cacher", "calmer", "caractériser", "caresser", "célébrer",
    "charger", "chasser", "chauffer", "circuler", "citer",
    "classer", "collaborer", "combattre", "commander", "communiquer",
    "comparer", "compléter", "composer", "compter", "concentrer",
    "concevoir", "conduire", "confier", "confirmer", "confondre",
    "conquérir", "consacrer", "conseiller", "conserver", "considérer",
    "constituer", "construire", "consulter", "contenir", "continuer",
    "contribuer", "contrôler", "convaincre", "convenir", "corriger",
    "couper", "couvrir", "craindre", "créer", "critiquer",
    "cueillir", "cultiver", "danser", "débattre", "décider",
    "déclarer", "découvrir", "décrire", "défendre", "définir",
    "dégager", "demeurer", "démontrer", "dépasser", "dépendre",
    "déplacer", "déposer", "déranger", "désigner", "désirer",
    "dessiner", "déterminer", "détruire", "développer", "deviner",
    "diriger", "discuter", "disposer", "distinguer", "distribuer",
    "diviser", "dominer", "durer", "échapper", "éclairer",
    "écouter", "effectuer", "effacer", "élever", "éliminer",
    "embrasser", "emmener", "employer", "encourager", "endormir",
    "engager", "enlever", "enrichir", "enseigner", "entourer",
    "entraîner", "entreprendre", "envahir", "envelopper", "envoyer",
    "éprouver", "établir", "éteindre", "étendre", "étonner",
    "étudier", "évaluer", "éveiller", "évoluer", "examiner",
    "exécuter", "exercer", "exiger", "expliquer", "exploiter",
    "explorer", "exposer", "exprimer", "fabriquer", "faciliter",
    "fonder", "forcer", "former", "fournir", "franchir",
    "frapper", "fréquenter", "fuir", "gagner", "garantir",
    "gouverner", "grandir", "guérir", "habiter", "haïr",
    "hésiter", "identifier", "ignorer", "illustrer", "imaginer",
    "imposer", "imprimer", "inclure", "indiquer", "inspirer",
    "installer", "instruire", "intéresser", "interpréter", "intervenir",
    "introduire", "inventer", "inviter", "isoler", "juger",
    "jurer", "justifier", "lancer", "libérer", "lier",
    "limiter", "livrer", "loger", "maintenir", "manifester",
    "manipuler", "manquer", "mélanger", "menacer", "mener",
    "mériter", "mesurer", "modifier", "multiplier", "nager",
    "négliger", "nommer", "nourrir", "observer", "obtenir",
    "offenser", "opérer", "opposer", "organiser", "orienter",

    # Noms abstraits
    "abandon", "absence", "abondance", "abstraction", "accident",
    "accusation", "action", "activité", "adaptation", "adhésion",
    "admiration", "adversaire", "affection", "agonie", "alliance",
    "ambiguïté", "ambition", "analyse", "angoisse", "apparence",
    "application", "argument", "aspiration", "assurance", "atmosphère",
    "attention", "attitude", "audace", "authenticité", "aventure",
    "bénédiction", "bienfait", "bienveillance", "bravoure", "brutalité",
    "capacité", "caractère", "catastrophe", "certitude", "chance",
    "changement", "charme", "civilisation", "clarté", "cohérence",
    "combinaison", "compétence", "complexité", "comportement", "concentration",
    "condition", "confiance", "confusion", "connaissance", "conséquence",
    "construction", "contemplation", "conviction", "coopération", "corruption",
    "création", "curiosité", "danger", "décision", "défaite",
    "définition", "délicatesse", "démonstration", "dépendance", "désolation",
    "destruction", "détermination", "développement", "dignité", "dimension",
    "direction", "discipline", "distinction", "domination", "durée",
    "éducation", "efficacité", "élégance", "émotion", "énergie",
    "engagement", "enthousiasme", "environnement", "épreuve", "espérance",
    "estimation", "éternité", "événement", "évidence", "évolution",
    "excellence", "exception", "existence", "expérience", "expression",
    "fascination", "fatalité", "fidélité", "fondation", "fonction",
    "générosité", "génie", "gloire", "gouvernance", "habitude",
    "harmonie", "héritage", "honneur", "humanité", "humilité",
    "illusion", "imagination", "importance", "impression", "indépendance",
    "influence", "injustice", "innocence", "inspiration", "instinct",
    "intelligence", "intention", "intuition", "ironie", "justice",
    "jeunesse", "jouissance", "jugement", "légitimité", "lucidité",
    "magnificence", "majesté", "maturité", "médiocrité", "merveille",
    "métamorphose", "méthode", "modestie", "morale", "motivation",
    "mouvement", "mutation", "naissance", "nature", "nécessité",
    "noblesse", "obligation", "obsession", "opinion", "opposition",
    "optimisme", "originalité", "perception", "perfection", "permanence",
    "personnalité", "perspective", "philosophie", "possession", "potentiel",
    "précision", "prédiction", "présence", "prétention", "principe",
    "profondeur", "progression", "proportion", "protection", "providence",
    "prudence", "puissance", "qualité", "quantité", "raison",
    "réalisation", "réconciliation", "réflexion", "relation", "renaissance",
    "résistance", "résolution", "responsabilité", "révélation", "révolution",
    "richesse", "sacrifice", "satisfaction", "sensibilité", "signification",
    "simplicité", "sincérité", "situation", "solidarité", "souffrance",
    "stabilité", "stratégie", "subtilité", "sympathie", "tentation",
    "tolérance", "tradition", "transformation", "transparence", "triomphe",
    "unité", "urgence", "utilité", "vérité", "vertu",
    "victoire", "violence", "vision", "vivacité", "volonté",

    # Noms concrets
    "aiguille", "ancre", "anneau", "armure", "autel",
    "balance", "balcon", "bandeau", "barque", "berceau",
    "bibliothèque", "bijou", "blessure", "boussole", "bouteille",
    "calendrier", "calice", "carrefour", "cascade", "chaîne",
    "chandelle", "chariot", "cloche", "coffre", "colline",
    "comptoir", "couronne", "cristal", "drapeau", "échelle",
    "écluse", "émeraude", "encre", "énigme", "éventail",
    "falaise", "flamme", "fontaine", "forteresse", "fossé",
    "foudre", "glacier", "grotte", "hameau", "horloge",
    "icône", "jardin", "joyau", "labyrinthe", "lampe",
    "lanterne", "légende", "manuscrit", "marbre", "médaille",
    "mosaïque", "navire", "oasis", "orchidée", "parchemin",
    "perle", "phare", "prairie", "pyramide", "rosée",
    "ruisseau", "sable", "sanctuaire", "saphir", "sentier",
    "source", "tapisserie", "terrasse", "trésor", "vallée",
    "velours", "vitrail", "voile", "volcan",

    # Adjectifs
    "absolu", "abstrait", "abondant", "admirable", "agréable",
    "amer", "audacieux", "authentique", "aveugle", "bienveillant",
    "brillant", "brutal", "calme", "capable", "certain",
    "charitable", "complexe", "confiant", "considérable", "courageux",
    "cruel", "curieux", "dangereux", "délicat", "digne",
    "discret", "efficace", "élégant", "éternel", "évident",
    "exceptionnel", "extraordinaire", "fidèle", "formidable", "fragile",
    "généreux", "glorieux", "gracieux", "grave", "harmonieux",
    "honnête", "humble", "immense", "imprévisible", "indispensable",
    "infini", "innocent", "invisible", "juste", "légitime",
    "lumineux", "magnifique", "majestueux", "merveilleux", "modeste",
    "mystérieux", "noble", "obscur", "original", "paisible",
    "parfait", "patient", "permanent", "précieux", "profond",
    "pur", "radical", "redoutable", "remarquable", "respectable",
    "rigoureux", "robuste", "sacré", "sensible", "serein",
    "sincère", "sobre", "solennel", "splendide", "sublime",
    "subtil", "superbe", "terrible", "tranquille", "transparent",
    "universel", "vaillant", "vaste", "véritable", "vigoureux",
]

# Deduplicate
seen = set()
UNIQUE = []
for w in WORDS:
    if w.lower() not in seen:
        seen.add(w.lower())
        UNIQUE.append(w)
WORDS = UNIQUE


def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "last_index": 0}


def save_progress(progress):
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=len(WORDS))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    print("=" * 60)
    print("LAROUSSE -> CERVEAU NB")
    print("=" * 60)

    brain = Brain.load(str(BRAIN_PATH))
    before = brain.stats()
    print(f"Cerveau: {before['nodes']} noeuds, {before['edges']} aretes")

    progress = load_progress() if args.resume else {"completed": [], "failed": [], "last_index": 0}
    start = progress["last_index"] if args.resume else 0
    completed_set = set(progress["completed"])

    words = WORDS[start:start + args.limit]
    total = len(words)
    success = fail = total_edges = 0

    print(f"\n{total} mots a traiter (index {start})")
    print("-" * 60)

    for i, word in enumerate(words):
        if word in completed_set:
            continue

        definition = get_larousse_definition(word)

        if definition:
            edges = feed_word(brain, word, definition)
            total_edges += edges
            success += 1
            progress["completed"].append(word)
            short_def = definition[:70].replace('\n', ' ')
            print(f"  [{start+i+1}/{start+total}] OK {word}: {short_def}...")
        else:
            fail += 1
            progress["failed"].append(word)
            print(f"  [{start+i+1}/{start+total}] -- {word}")

        progress["last_index"] = start + i + 1

        if (i + 1) % 50 == 0:
            brain.consolidate()
            brain.save(str(BRAIN_PATH))
            save_progress(progress)
            s = brain.stats()
            print(f"\n  --- Checkpoint: {s['nodes']} noeuds, {s['edges']} aretes ---\n")

        time.sleep(args.delay)

    brain.consolidate()
    brain.save(str(BRAIN_PATH))
    save_progress(progress)

    after = brain.stats()
    print(f"\n{'='*60}")
    print(f"RESULTAT")
    print(f"{'='*60}")
    print(f"  Traites: {success + fail}")
    print(f"  Definitions: {success} trouvees, {fail} manquantes")
    print(f"  Noeuds: {before['nodes']} -> {after['nodes']} (+{after['nodes'] - before['nodes']})")
    print(f"  Aretes: {before['edges']} -> {after['edges']} (+{after['edges'] - before['edges']})")
    print(f"  Cerveau sauvegarde.")


if __name__ == "__main__":
    main()
