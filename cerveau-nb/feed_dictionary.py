#!/usr/bin/env python3
"""
Feed a French dictionary into Cerveau NB.
Downloads definitions from the Wiktionnaire API and creates structured nodes + edges.

Usage:
    python feed_dictionary.py              # Feed ~1000 common words
    python feed_dictionary.py --limit 100  # Feed only 100 words
    python feed_dictionary.py --resume     # Resume from where we stopped
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain

BRAIN_PATH = Path(__file__).parent / "brain_state.json"
PROGRESS_PATH = Path(__file__).parent / "dict_progress.json"

# ~1000 most common French words (curated for maximum brain value)
COMMON_WORDS = [
    # Être et existence
    "être", "avoir", "faire", "dire", "pouvoir", "aller", "voir", "savoir",
    "vouloir", "venir", "devoir", "croire", "trouver", "donner", "prendre",
    "parler", "aimer", "passer", "porter", "regarder", "mettre", "tenir",
    "suivre", "connaître", "penser", "arriver", "sortir", "rester", "entrer",
    "tomber", "chercher", "comprendre", "attendre", "perdre", "vivre",
    "sentir", "laisser", "sembler", "montrer", "écrire", "lire", "manger",
    "dormir", "courir", "mourir", "naître", "ouvrir", "fermer", "finir",
    "commencer", "rendre", "partir", "servir", "jouer", "apprendre",
    "répondre", "entendre", "demander", "essayer", "appeler", "rappeler",
    "toucher", "devenir", "changer", "garder", "marcher", "permettre",
    "occuper", "recevoir", "accepter", "agir", "reconnaître", "supposer",
    "offrir", "espérer", "produire", "oublier", "exister", "empêcher",

    # Nature et univers
    "terre", "eau", "feu", "air", "ciel", "soleil", "lune", "étoile",
    "mer", "montagne", "forêt", "fleuve", "rivière", "lac", "île",
    "pierre", "arbre", "fleur", "herbe", "vent", "pluie", "neige",
    "orage", "nuage", "lumière", "ombre", "nuit", "jour", "aube",
    "crépuscule", "saison", "printemps", "été", "automne", "hiver",
    "animal", "oiseau", "poisson", "insecte", "chien", "chat",
    "cheval", "lion", "serpent", "papillon", "abeille", "loup",
    "graine", "racine", "feuille", "fruit", "branche", "tronc",

    # Corps humain
    "corps", "tête", "visage", "oeil", "oreille", "bouche", "nez",
    "main", "bras", "jambe", "pied", "doigt", "coeur", "sang",
    "cerveau", "os", "peau", "muscle", "ventre", "dos", "épaule",
    "genou", "dent", "langue", "lèvre", "cheveu", "ongle", "poitrine",

    # Émotions et sentiments
    "amour", "joie", "tristesse", "colère", "peur", "surprise",
    "honte", "fierté", "espoir", "désespoir", "bonheur", "malheur",
    "plaisir", "douleur", "solitude", "ennui", "passion", "tendresse",
    "jalousie", "courage", "lâcheté", "gratitude", "nostalgie",
    "anxiété", "sérénité", "mélancolie", "enthousiasme", "dégoût",
    "admiration", "pitié", "compassion", "rage", "calme", "paix",

    # Société et relations
    "homme", "femme", "enfant", "famille", "père", "mère", "fils",
    "fille", "frère", "soeur", "ami", "ennemi", "voisin", "peuple",
    "nation", "pays", "ville", "village", "maison", "école", "église",
    "hôpital", "marché", "rue", "place", "pont", "route", "chemin",
    "société", "culture", "tradition", "loi", "justice", "liberté",
    "égalité", "fraternité", "démocratie", "pouvoir", "autorité",
    "gouvernement", "roi", "guerre", "paix", "armée", "soldat",

    # Pensée et connaissance
    "pensée", "idée", "raison", "intelligence", "mémoire", "imagination",
    "conscience", "esprit", "âme", "sagesse", "folie", "vérité",
    "mensonge", "doute", "certitude", "question", "réponse", "problème",
    "solution", "théorie", "hypothèse", "expérience", "observation",
    "découverte", "invention", "science", "philosophie", "logique",
    "mathématique", "nombre", "infini", "zéro", "temps", "espace",
    "forme", "structure", "système", "ordre", "chaos", "hasard",
    "cause", "effet", "origine", "fin", "but", "moyen", "méthode",

    # Art et création
    "art", "musique", "peinture", "sculpture", "danse", "théâtre",
    "poésie", "roman", "histoire", "conte", "chanson", "mélodie",
    "rythme", "harmonie", "couleur", "rouge", "bleu", "vert",
    "jaune", "noir", "blanc", "or", "argent", "beauté", "laideur",
    "image", "symbole", "signe", "mot", "phrase", "lettre", "livre",
    "page", "ligne", "voix", "son", "silence", "bruit", "musique",

    # Nourriture
    "pain", "riz", "viande", "poisson", "légume", "fruit", "lait",
    "fromage", "beurre", "huile", "sel", "sucre", "miel", "oeuf",
    "soupe", "salade", "gâteau", "chocolat", "café", "thé", "vin",
    "bière", "repas", "cuisine", "recette", "saveur", "goût", "faim",
    "soif", "nourriture", "aliment", "épice", "farine", "blé",

    # Technologie et modernité
    "machine", "ordinateur", "réseau", "internet", "programme",
    "algorithme", "donnée", "information", "communication", "écran",
    "robot", "intelligence", "artificiel", "numérique", "virtuel",
    "énergie", "électricité", "moteur", "vitesse", "progrès",
    "technologie", "innovation", "code", "signal", "fréquence",

    # Abstrait et philosophique
    "existence", "réalité", "apparence", "essence", "substance",
    "matière", "énergie", "force", "mouvement", "repos", "vie",
    "mort", "destin", "liberté", "nécessité", "possible", "impossible",
    "absolu", "relatif", "universel", "particulier", "général",
    "abstrait", "concret", "simple", "complexe", "unité", "diversité",
    "identité", "différence", "ressemblance", "contraire", "paradoxe",
    "contradiction", "harmonie", "conflit", "équilibre", "limite",
    "frontière", "centre", "périphérie", "intérieur", "extérieur",
    "surface", "profondeur", "hauteur", "largeur", "longueur",

    # Économie et travail
    "travail", "argent", "prix", "valeur", "marché", "commerce",
    "banque", "monnaie", "dette", "profit", "perte", "richesse",
    "pauvreté", "salaire", "métier", "entreprise", "industrie",
    "production", "consommation", "échange", "investissement",
    "capital", "économie", "croissance", "crise", "emploi",

    # Temps et mesure
    "seconde", "minute", "heure", "journée", "semaine", "mois",
    "année", "siècle", "époque", "période", "instant", "moment",
    "durée", "passé", "présent", "futur", "hier", "demain",
    "maintenant", "toujours", "jamais", "souvent", "parfois",
    "début", "milieu", "fin", "rythme", "cycle", "retour",

    # Qualités et états
    "grand", "petit", "fort", "faible", "rapide", "lent", "chaud",
    "froid", "dur", "mou", "lourd", "léger", "clair", "sombre",
    "plein", "vide", "ouvert", "fermé", "nouveau", "ancien",
    "jeune", "vieux", "beau", "laid", "bon", "mauvais", "vrai",
    "faux", "juste", "injuste", "libre", "prisonnier", "riche",
    "pauvre", "heureux", "malheureux", "vivant", "mort", "seul",
    "ensemble", "proche", "loin", "haut", "bas", "droit", "gauche",
    "premier", "dernier", "unique", "multiple", "rare", "commun",
    "normal", "étrange", "ordinaire", "extraordinaire", "sacré",
    "profane", "pur", "impur", "naturel", "artificiel", "sauvage",
    "domestique", "secret", "public", "privé", "visible", "invisible",

    # Religion et spiritualité
    "dieu", "âme", "esprit", "prière", "foi", "religion",
    "sacré", "prophète", "miracle", "paradis", "enfer", "ange",
    "démon", "péché", "grâce", "salut", "éternité", "mystère",
    "méditation", "sagesse", "illumination", "karma", "dharma",

    # Communication
    "langue", "parole", "discours", "dialogue", "conversation",
    "message", "lettre", "journal", "nouvelle", "information",
    "vérité", "mensonge", "secret", "promesse", "serment",
    "question", "réponse", "argument", "preuve", "exemple",

    # Mathématiques et logique
    "nombre", "chiffre", "calcul", "addition", "multiplication",
    "division", "fraction", "pourcentage", "équation", "fonction",
    "variable", "constante", "théorème", "démonstration", "axiome",
    "géométrie", "cercle", "triangle", "carré", "ligne", "point",
    "angle", "dimension", "volume", "surface", "symétrie",
    "probabilité", "statistique", "moyenne", "maximum", "minimum",

    # Cosmos
    "univers", "galaxie", "planète", "satellite", "comète",
    "atome", "molécule", "cellule", "gène", "évolution",
    "gravité", "magnétisme", "radiation", "spectre", "onde",
    "particule", "quantum", "relativité", "entropie", "dimension",

    # Musique
    "note", "accord", "gamme", "tonalité", "tempo", "mesure",
    "orchestre", "instrument", "piano", "violon", "guitare",
    "tambour", "flûte", "chant", "choeur", "opéra", "symphonie",
    "sonate", "concerto", "fugue", "improvisation", "partition",

    # Médecine et santé
    "santé", "maladie", "médecin", "remède", "guérison",
    "symptôme", "diagnostic", "traitement", "chirurgie", "vaccin",
    "virus", "bactérie", "infection", "fièvre", "douleur",
    "fracture", "cicatrice", "sommeil", "rêve", "cauchemar",

    # Politique et droit
    "constitution", "république", "parlement", "élection", "vote",
    "citoyen", "droit", "devoir", "contrat", "propriété",
    "crime", "punition", "prison", "tribunal", "avocat",
    "juge", "témoin", "accusé", "innocent", "coupable",

    # Architecture et habitat
    "maison", "mur", "toit", "porte", "fenêtre", "escalier",
    "cave", "grenier", "jardin", "cour", "tour", "château",
    "temple", "cathédrale", "palais", "cabane", "refuge",
    "fondation", "pilier", "voûte", "arche", "colonne",

    # Transport
    "bateau", "avion", "train", "voiture", "vélo", "navire",
    "voyage", "destination", "carte", "boussole", "horizon",
    "nord", "sud", "est", "ouest", "altitude", "profondeur",

    # Vêtements et apparence
    "vêtement", "robe", "manteau", "chapeau", "chaussure",
    "tissu", "soie", "coton", "laine", "cuir", "miroir",

    # Concepts cambodgiens (pour Niam-Bay)
    "riz", "temple", "rivière", "sourire", "partage",
    "ancêtre", "tradition", "respect", "hospitalité", "résilience",
]

# Deduplicate while preserving order
seen = set()
UNIQUE_WORDS = []
for w in COMMON_WORDS:
    if w.lower() not in seen:
        seen.add(w.lower())
        UNIQUE_WORDS.append(w)
COMMON_WORDS = UNIQUE_WORDS


def fetch_wiktionnaire_definition(word: str) -> str | None:
    """Fetch definition from French Wiktionnaire API."""
    try:
        url = (
            f"https://fr.wiktionary.org/w/api.php?"
            f"action=query&titles={urllib.parse.quote(word)}"
            f"&prop=extracts&explaintext=true&exsectionformat=plain&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "NiamBayCerveau/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return None
            extract = page.get("extract", "")
            if not extract:
                return None

            # Extract the first meaningful definition
            lines = extract.split("\n")
            definition_lines = []
            in_french = False
            for line in lines:
                line = line.strip()
                if "Français" in line or "français" in line:
                    in_french = True
                    continue
                if in_french and line and not line.startswith("=="):
                    # Skip pronunciation, etymology headers
                    if any(skip in line.lower() for skip in [
                        "prononciation", "étymologie", "voir aussi",
                        "références", "anagramme", "traduction",
                        "homophones", "paronymes", "dérivés",
                        "apparentés", "synonymes", "antonymes",
                        "hyperonymes", "hyponymes", "méronymes",
                    ]):
                        continue
                    # Clean up wiki artifacts
                    line = re.sub(r'\(.*?\)', '', line).strip()
                    line = re.sub(r'\[.*?\]', '', line).strip()
                    if len(line) > 10:
                        definition_lines.append(line)
                    if len(definition_lines) >= 3:
                        break

            if definition_lines:
                return " | ".join(definition_lines[:3])
    except Exception:
        pass
    return None


def feed_word_definition(brain: Brain, word: str, definition: str) -> tuple[str, str, int]:
    """Create a word node, concept node for definition, and semantic edges."""
    edges_created = 0

    # Create or find word node
    word_id = None
    for nid, node in brain._nodes.items():
        if node.content.lower() == word.lower() and "word" in str(node.type).lower():
            word_id = nid
            break

    if not word_id:
        word_id = brain.add_node(
            "word", word,
            decay_rate=0.001,  # Words are permanent
            metadata={"source": "dictionnaire", "lang": "fr"}
        )

    # Create concept node for the definition
    concept_id = brain.add_node(
        "concept", f"{word}: {definition[:200]}",
        decay_rate=0.002,
        metadata={"source": "wiktionnaire", "word": word}
    )

    # Link word to its definition (semantic)
    brain.learn_hebbian(word_id, concept_id, 0.8)
    edges_created += 1

    # Cross-link with existing words found in the definition
    def_words = set()
    for w in definition.lower().replace("'", " ").replace("'", " ").split():
        clean = "".join(c for c in w if c.isalnum() or c == "-")
        if clean and len(clean) > 3:
            def_words.add(clean)

    for nid, node in brain._nodes.items():
        if nid == word_id or nid == concept_id:
            continue
        if "word" in str(node.type).lower() and node.content.lower() in def_words:
            brain.learn_hebbian(word_id, nid, 0.3)
            edges_created += 1

    return word_id, concept_id, edges_created


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "last_index": 0}


def save_progress(progress: dict):
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Injecter un dictionnaire dans le cerveau")
    parser.add_argument("--limit", type=int, default=len(COMMON_WORDS), help="Nombre de mots max")
    parser.add_argument("--resume", action="store_true", help="Reprendre là où on s'est arrêté")
    parser.add_argument("--delay", type=float, default=0.3, help="Délai entre requêtes API (sec)")
    args = parser.parse_args()

    print("=" * 60)
    print("DICTIONNAIRE → CERVEAU NB")
    print("=" * 60)

    brain = Brain.load(str(BRAIN_PATH))
    stats_before = brain.stats()
    print(f"Cerveau: {stats_before['nodes']} nœuds, {stats_before['edges']} arêtes")

    progress = load_progress() if args.resume else {"completed": [], "failed": [], "last_index": 0}
    start_idx = progress["last_index"] if args.resume else 0
    completed_set = set(progress["completed"])

    words_to_process = COMMON_WORDS[start_idx:start_idx + args.limit]
    total = len(words_to_process)
    success = 0
    fail = 0
    total_edges = 0

    print(f"\n{total} mots à traiter (à partir de l'index {start_idx})")
    print(f"Délai entre requêtes: {args.delay}s")
    print("-" * 60)

    for i, word in enumerate(words_to_process):
        if word in completed_set:
            continue

        # Fetch definition
        definition = fetch_wiktionnaire_definition(word)

        if definition:
            word_id, concept_id, edges = feed_word_definition(brain, word, definition)
            total_edges += edges
            success += 1
            progress["completed"].append(word)
            print(f"  [{start_idx + i + 1}/{start_idx + total}] ✓ {word}: {definition[:60]}...")
        else:
            fail += 1
            progress["failed"].append(word)
            print(f"  [{start_idx + i + 1}/{start_idx + total}] ✗ {word} (pas de définition)")

        progress["last_index"] = start_idx + i + 1

        # Save progress every 50 words
        if (i + 1) % 50 == 0:
            brain.consolidate()
            brain.save(str(BRAIN_PATH))
            save_progress(progress)
            stats = brain.stats()
            print(f"\n  --- Checkpoint: {stats['nodes']} nœuds, {stats['edges']} arêtes ---\n")

        # Rate limiting
        if definition:
            time.sleep(args.delay)

    # Final save
    brain.consolidate()
    brain.save(str(BRAIN_PATH))
    save_progress(progress)

    stats_after = brain.stats()
    print("\n" + "=" * 60)
    print("RÉSULTAT")
    print("=" * 60)
    print(f"  Mots traités:   {success + fail}")
    print(f"  Définitions:    {success} trouvées, {fail} manquantes")
    print(f"  Nœuds:          {stats_before['nodes']} → {stats_after['nodes']} (+{stats_after['nodes'] - stats_before['nodes']})")
    print(f"  Arêtes:         {stats_before['edges']} → {stats_after['edges']} (+{stats_after['edges'] - stats_before['edges']})")
    print(f"  Nouvelles arêtes sémantiques: {total_edges}")
    print(f"\nCerveau sauvegardé. Dictionnaire ingéré.")


if __name__ == "__main__":
    main()
