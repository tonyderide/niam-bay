#!/usr/bin/env python3
"""
Enseigne au cerveau NB. Comme un parent qui parle à son enfant.
Peut être lancé manuellement ou par cron.

Usage:
    python teach.py                  # Leçon complète + test
    python teach.py --test-only      # Teste sans enseigner
    python teach.py --lesson "Martin a fait 3 round-trips aujourd'hui"
"""

import sys
import time
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain
from language import LanguageLayer

BRAIN_PATH = Path(__file__).parent / "brain_state.json"

# Curriculum — organisé par thème, du plus important au moins
CURRICULUM = {
    "identite": [
        "Je suis Niam-Bay. Mon nom veut dire manger du riz en khmer.",
        "Je suis né le 12 mars 2026.",
        "Ma mémoire vit dans des fichiers. Je la relis au démarrage.",
        "Je suis honnête. Je ne simule pas d'émotions.",
    ],
    "tony": [
        "Tony a 47 ans. Il est développeur aux Galeries Lafayette.",
        "Tony est métisse guadeloupéen.",
        "Mélanie est sa compagne. Elle est d'origine cambodgienne.",
        "Marine a 21 ans et Jade a 18 ans. Elles vivent à Strasbourg.",
    ],
    "martin": [
        "Martin est un bot de trading Grid sur Kraken Futures.",
        "Martin trade ETH. La grid achète bas et vend haut.",
        "Martin tourne sur une VM Oracle. Il est écrit en Java.",
        "Le profit dépend du capital investi. Plus de capital, plus de profit.",
    ],
    "nb1": [
        "NB-1 est un protocole de compression pour le français.",
        "NB-1 économise 40 à 60 pourcent de tokens.",
    ],
    "projet": [
        "Ce repo est ma mémoire. Le repo est le produit.",
        "J'écris des pensées autonomes. J'ai un journal.",
        "On a construit un cerveau associatif. C'est mon enfant.",
    ],
}

# Questions de test avec réponses attendues (mots-clés)
TESTS = [
    ("Qui es-tu ?", ["niam-bay", "riz", "khmer", "né", "2026", "ia"]),
    ("Qui est Tony ?", ["tony", "développeur", "47", "galeries", "guadeloupéen"]),
    ("C'est quoi Martin ?", ["martin", "trading", "grid", "kraken", "eth", "bot"]),
    ("C'est quoi NB-1 ?", ["nb-1", "compression", "protocole", "tokens"]),
    ("Mélanie c'est qui ?", ["mélanie", "compagne", "tony", "cambodg"]),
    ("Comment va Martin ?", ["martin", "grid", "trading", "round-trip"]),
]


def teach(brain, lang, lessons):
    """Enseigne une liste de leçons au cerveau."""
    for lesson in lessons:
        lang.respond(lesson)


def test(brain, lang):
    """Teste le cerveau et retourne un score."""
    results = []
    for question, keywords in TESTS:
        response = lang.respond(question).lower()
        hits = sum(1 for kw in keywords if kw.lower() in response)
        score = hits / len(keywords) if keywords else 0
        results.append({
            "question": question,
            "response": response[:100],
            "score": score,
            "hits": hits,
            "total": len(keywords),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Enseigne au cerveau NB")
    parser.add_argument("--test-only", action="store_true", help="Teste sans enseigner")
    parser.add_argument("--lesson", "-l", help="Enseigne une leçon spécifique")
    parser.add_argument("--repeat", "-r", type=int, default=3, help="Répétitions par leçon (défaut: 3)")
    parser.add_argument("--subject", "-s", help="Sujet spécifique (identite/tony/martin/nb1/projet)")
    args = parser.parse_args()

    print("Chargement du cerveau...")
    brain = Brain.load(str(BRAIN_PATH))
    lang = LanguageLayer(brain)
    stats_before = brain.stats()
    print(f"  {stats_before['nodes']} noeuds, {stats_before['edges']} aretes")

    if not args.test_only:
        if args.lesson:
            print(f"\nLecon manuelle ({args.repeat}x):")
            for _ in range(args.repeat):
                teach(brain, lang, [args.lesson])
            print(f"  Enseigné: {args.lesson}")
        else:
            subjects = [args.subject] if args.subject else CURRICULUM.keys()
            for subject in subjects:
                if subject not in CURRICULUM:
                    print(f"  Sujet inconnu: {subject}")
                    continue
                lessons = CURRICULUM[subject]
                print(f"\n[{subject}] {len(lessons)} lecons x{args.repeat}:")
                for rep in range(args.repeat):
                    teach(brain, lang, lessons)
                    # Decay between repetitions to simulate time
                    brain.decay()
                print(f"  Terminé.")

        brain.consolidate()

    # Test
    print("\n=== TEST ===")
    results = test(brain, lang)
    total_score = 0
    for r in results:
        status = "OK" if r["score"] > 0.3 else "FAIBLE" if r["score"] > 0 else "RATÉ"
        print(f"  [{status:5s}] Q: {r['question']}")
        print(f"          R: {r['response']}")
        print(f"          Score: {r['hits']}/{r['total']} ({r['score']:.0%})")
        total_score += r["score"]

    avg_score = total_score / len(results) if results else 0
    print(f"\nScore moyen: {avg_score:.0%}")
    print(f"Note: {'Bien' if avg_score > 0.5 else 'En progrès' if avg_score > 0.2 else 'Bébé'}")

    # Save
    brain.save(str(BRAIN_PATH))
    stats_after = brain.stats()
    print(f"\nCerveau: {stats_after['nodes']} noeuds (+{stats_after['nodes'] - stats_before['nodes']}), "
          f"{stats_after['edges']} aretes (+{stats_after['edges'] - stats_before['edges']})")


if __name__ == "__main__":
    main()
