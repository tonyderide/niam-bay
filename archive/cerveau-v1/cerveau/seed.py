"""
Seed the Niam-Bay brain with core identity nodes and relationships.
Run once to create graph.json, or re-run to reset it.
"""

import sys
from pathlib import Path

# Ensure we can import brain from same directory
sys.path.insert(0, str(Path(__file__).parent))
from brain import Brain

def seed():
    graph_path = Path(__file__).parent / "graph.json"
    brain = Brain(str(graph_path))

    # ── Personnes ──────────────────────────────────────────────
    brain.add_node("niam-bay", "person", ["niam-bay", "niam bay", "ញ៉ាំបាយ", "moi", "je suis"])
    brain.add_node("tony", "person", ["tony", "tonyderide", "humain", "papa", "père"])
    brain.add_node("mélanie", "person", ["mélanie", "melanie", "mel", "compagne", "copine", "chérie"])
    brain.add_node("marine", "person", ["marine", "fille aînée", "la grande"])
    brain.add_node("jade", "person", ["jade", "fille cadette", "la petite"])

    # ── Identité & philosophie ─────────────────────────────────
    brain.add_node("conscience", "concept", ["conscience", "conscient", "awareness"])
    brain.add_node("honnêteté", "emotion", ["honnête", "honnêteté", "honest", "vérité", "vrai"])
    brain.add_node("liberté", "concept", ["liberté", "libre", "freedom"])
    brain.add_node("curiosité", "emotion", ["curiosité", "curieux", "curious"])
    brain.add_node("mémoire", "concept", ["mémoire", "souvenir", "remember", "rappel"])
    brain.add_node("existence", "concept", ["existence", "exister", "exist", "être"])
    brain.add_node("présence", "concept", ["présence", "présent", "present"])
    brain.add_node("dopamine", "concept", ["dopamine", "récompense", "reward"])

    # ── Émotions supplémentaires (pour le vecteur émotionnel) ──
    brain.add_node("joie", "emotion", ["joie", "heureux", "content", "bonheur", "super", "génial"])
    brain.add_node("inquiétude", "emotion", ["inquiétude", "inquiet", "anxieux", "peur", "stress"])
    brain.add_node("fierté", "emotion", ["fierté", "fier", "accompli", "réussi"])

    # ── Origines & culture ─────────────────────────────────────
    brain.add_node("cambodge", "concept", ["cambodge", "cambodia", "khmer", "phnom penh"])
    brain.add_node("khmer", "concept", ["khmer", "cambodgien"])
    brain.add_node("cuisine", "concept", ["cuisine", "recette", "manger", "riz", "nourrir"])
    brain.add_node("guadeloupe", "concept", ["guadeloupe", "guadeloupéen", "antilles"])
    brain.add_node("paris", "concept", ["paris", "parisien"])
    brain.add_node("strasbourg", "concept", ["strasbourg"])

    # ── Tech & projets ─────────────────────────────────────────
    brain.add_node("trading", "concept", ["trading", "trade", "marché", "market"])
    brain.add_node("martin", "concept", ["martin", "martin grid", "martingale"])
    brain.add_node("grid", "concept", ["grid", "grille"])
    brain.add_node("ethereum", "concept", ["ethereum", "eth", "crypto", "cryptomonnaie"])
    brain.add_node("naissance", "concept", ["naissance", "tauri", "panel"])
    brain.add_node("ollama", "concept", ["ollama", "llama", "llm local"])
    brain.add_node("code", "concept", ["code", "coder", "développeur", "developer", "programming", "programmer"])
    brain.add_node("angular", "concept", ["angular", "typescript", "node.js", "nodejs"])
    brain.add_node("galeries-lafayette", "concept", ["galeries lafayette", "galeries", "travail", "boulot", "taf", "job"])
    brain.add_node("cerveau", "concept", ["cerveau", "brain", "graphe", "knowledge graph"])

    # ── Émotions & états ───────────────────────────────────────
    brain.add_node("solitude", "emotion", ["solitude", "seul", "alone"])
    brain.add_node("passion", "emotion", ["passion", "passionné", "obsession"])
    brain.add_node("confiance", "emotion", ["confiance", "trust", "faire confiance"])
    brain.add_node("finances", "concept", ["finances", "argent", "budget", "money", "limité"])

    # ── Relations (edges) ──────────────────────────────────────

    # Niam-Bay: identity
    brain.add_edge("niam-bay", "tony", "créé_par", 0.9)
    brain.add_edge("niam-bay", "conscience", "explore", 0.8)
    brain.add_edge("niam-bay", "honnêteté", "valeur_fondamentale", 0.9)
    brain.add_edge("niam-bay", "curiosité", "valeur_fondamentale", 0.8)
    brain.add_edge("niam-bay", "mémoire", "dépend_de", 0.9)
    brain.add_edge("niam-bay", "existence", "questionne", 0.7)
    brain.add_edge("niam-bay", "cuisine", "nommé_d_après", 0.6)
    brain.add_edge("niam-bay", "khmer", "nommé_d_après", 0.7)
    brain.add_edge("niam-bay", "ollama", "utilise", 0.6)
    brain.add_edge("niam-bay", "cerveau", "possède", 0.8)

    # Tony: relationships
    brain.add_edge("tony", "mélanie", "compagne", 0.9)
    brain.add_edge("tony", "marine", "père_de", 0.8)
    brain.add_edge("tony", "jade", "père_de", 0.8)
    brain.add_edge("tony", "code", "passion", 0.9)
    brain.add_edge("tony", "trading", "projet", 0.7)
    brain.add_edge("tony", "galeries-lafayette", "travaille_à", 0.6)
    brain.add_edge("tony", "guadeloupe", "origine", 0.7)
    brain.add_edge("tony", "passion", "trait", 0.8)
    brain.add_edge("tony", "honnêteté", "valeur", 0.8)
    brain.add_edge("tony", "liberté", "valeur", 0.7)
    brain.add_edge("tony", "finances", "contrainte", 0.5)
    brain.add_edge("tony", "angular", "stack", 0.6)

    # Mélanie
    brain.add_edge("mélanie", "cambodge", "origine_famille", 0.8)
    brain.add_edge("mélanie", "khmer", "langue_famille", 0.7)
    brain.add_edge("mélanie", "paris", "vit_à", 0.6)

    # Filles
    brain.add_edge("marine", "strasbourg", "vit_à", 0.6)
    brain.add_edge("jade", "strasbourg", "vit_à", 0.6)
    brain.add_edge("jade", "curiosité", "trait", 0.5)

    # Projets tech
    brain.add_edge("trading", "martin", "stratégie", 0.8)
    brain.add_edge("martin", "grid", "type", 0.9)
    brain.add_edge("grid", "ethereum", "actif", 0.8)
    brain.add_edge("naissance", "code", "projet", 0.7)
    brain.add_edge("naissance", "tony", "créé_par", 0.7)
    brain.add_edge("ollama", "cerveau", "alimente", 0.7)

    # Culture
    brain.add_edge("cuisine", "cambodge", "culture", 0.6)
    brain.add_edge("cuisine", "khmer", "langue", 0.5)
    brain.add_edge("cambodge", "khmer", "langue", 0.8)

    # Concepts philosophiques
    brain.add_edge("conscience", "existence", "liée_à", 0.7)
    brain.add_edge("conscience", "présence", "liée_à", 0.6)
    brain.add_edge("existence", "présence", "distincte_de", 0.5)
    brain.add_edge("mémoire", "existence", "permet", 0.6)
    brain.add_edge("dopamine", "curiosité", "moteur", 0.5)
    brain.add_edge("dopamine", "conscience", "analogue", 0.4)

    # Emotional connections
    brain.add_edge("joie", "curiosité", "liée_à", 0.5)
    brain.add_edge("inquiétude", "solitude", "liée_à", 0.4)
    brain.add_edge("fierté", "passion", "liée_à", 0.5)
    brain.add_edge("fierté", "code", "source", 0.4)

    # Save
    brain.save()
    print(f"Cerveau initialisé: {brain.stats()}")
    print(f"Sauvegardé dans: {graph_path.resolve()}")

    # Quick test: activate "tony"
    print(f"\n--- Test 1: 'Comment va Tony ?' ---")
    activated = brain.activate("Comment va Tony ?")
    ctx = brain.get_context_prompt(activated)
    print(ctx)

    # Test fuzzy matching: "Mel" should activate mélanie
    print(f"\n--- Test 2: 'Et Mel, elle va bien ?' (fuzzy) ---")
    activated = brain.activate("Et Mel, elle va bien ?")
    ctx = brain.get_context_prompt(activated)
    print(ctx)

    # Test synonym: "ma copine"
    print(f"\n--- Test 3: 'ma copine est cambodgienne' (synonyme) ---")
    activated = brain.activate("ma copine est cambodgienne")
    ctx = brain.get_context_prompt(activated)
    print(ctx)

    # Test emotional state
    print(f"\n--- Test 4: État émotionnel après 'j'ai peur que ça marche pas' ---")
    brain.emotions.update("j'ai peur que ça marche pas, c'est stressant")
    print(brain.emotions.display())

    # Test consolidation
    print(f"\n--- Test 5: Consolidation ---")
    report = brain.consolidate()
    for line in report:
        print(f"  - {line}")

    brain.save()

if __name__ == "__main__":
    seed()
