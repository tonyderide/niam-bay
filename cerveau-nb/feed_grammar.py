#!/usr/bin/env python3
"""
Enseigner les règles de grammaire française au cerveau.
Crée des nœuds PATTERN pour les règles et les relie aux mots concernés.

Usage:
    python feed_grammar.py
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import Brain

BRAIN_PATH = Path(__file__).parent / "brain_state.json"

# Règles de grammaire française structurées
GRAMMAR_RULES = [
    # === NATURE DES MOTS ===
    {
        "category": "nature des mots",
        "rule": "Le nom désigne un être, une chose, une idée. Il a un genre (masculin/féminin) et un nombre (singulier/pluriel).",
        "examples": ["maison", "chien", "liberté", "amour", "table"],
        "related": ["genre", "nombre", "singulier", "pluriel", "masculin", "féminin"],
    },
    {
        "category": "nature des mots",
        "rule": "Le verbe exprime une action ou un état. Il se conjugue selon le temps, le mode, la personne et le nombre.",
        "examples": ["être", "avoir", "faire", "aller", "dire"],
        "related": ["conjugaison", "temps", "mode", "personne", "infinitif"],
    },
    {
        "category": "nature des mots",
        "rule": "L'adjectif qualifie ou détermine le nom. Il s'accorde en genre et en nombre avec le nom qu'il qualifie.",
        "examples": ["grand", "petit", "beau", "rouge", "intelligent"],
        "related": ["accord", "genre", "nombre", "qualification"],
    },
    {
        "category": "nature des mots",
        "rule": "L'adverbe modifie un verbe, un adjectif ou un autre adverbe. Il est invariable.",
        "examples": ["rapidement", "très", "bien", "mal", "toujours"],
        "related": ["invariable", "modification", "manière", "temps", "lieu"],
    },
    {
        "category": "nature des mots",
        "rule": "Le pronom remplace un nom pour éviter la répétition. Types : personnel, possessif, démonstratif, relatif, indéfini, interrogatif.",
        "examples": ["je", "tu", "il", "celui", "qui", "que"],
        "related": ["remplacement", "personnel", "possessif", "relatif"],
    },
    {
        "category": "nature des mots",
        "rule": "La préposition introduit un complément. Elle est invariable et établit un rapport entre deux mots.",
        "examples": ["dans", "sur", "avec", "pour", "par", "entre"],
        "related": ["complément", "rapport", "invariable", "lieu", "temps"],
    },
    {
        "category": "nature des mots",
        "rule": "La conjonction relie des mots, des groupes ou des propositions. Conjonctions de coordination : mais, ou, et, donc, or, ni, car.",
        "examples": ["mais", "ou", "et", "donc", "car", "parce que"],
        "related": ["coordination", "subordination", "liaison", "proposition"],
    },

    # === CONJUGAISON ===
    {
        "category": "conjugaison",
        "rule": "Premier groupe : verbes en -er (sauf aller). Terminaisons au présent : -e, -es, -e, -ons, -ez, -ent.",
        "examples": ["aimer", "parler", "chanter", "manger", "jouer"],
        "related": ["présent", "terminaison", "régulier", "infinitif"],
    },
    {
        "category": "conjugaison",
        "rule": "Deuxième groupe : verbes en -ir avec participe présent en -issant. Terminaisons au présent : -is, -is, -it, -issons, -issez, -issent.",
        "examples": ["finir", "choisir", "réussir", "grandir", "rougir"],
        "related": ["présent", "terminaison", "régulier", "participe"],
    },
    {
        "category": "conjugaison",
        "rule": "Troisième groupe : tous les autres verbes (irréguliers). Inclut les verbes en -ir (sans -issant), -oir, -re, et aller.",
        "examples": ["être", "avoir", "aller", "prendre", "voir", "faire"],
        "related": ["irrégulier", "présent", "auxiliaire"],
    },
    {
        "category": "conjugaison",
        "rule": "Les temps composés se forment avec l'auxiliaire avoir ou être + participe passé. Le passé composé : j'ai mangé, je suis allé.",
        "examples": ["avoir", "être", "mangé", "allé", "fait"],
        "related": ["auxiliaire", "participe passé", "passé composé", "accord"],
    },
    {
        "category": "conjugaison",
        "rule": "L'imparfait exprime une action passée qui dure ou se répète. Terminaisons : -ais, -ais, -ait, -ions, -iez, -aient.",
        "examples": ["j'aimais", "tu parlais", "il faisait", "nous allions"],
        "related": ["passé", "durée", "répétition", "description"],
    },
    {
        "category": "conjugaison",
        "rule": "Le futur simple exprime une action à venir. Formation : infinitif + -ai, -as, -a, -ons, -ez, -ont.",
        "examples": ["je parlerai", "tu finiras", "il sera", "nous aurons"],
        "related": ["futur", "projet", "prédiction", "promesse"],
    },
    {
        "category": "conjugaison",
        "rule": "Le subjonctif exprime le doute, le souhait, la nécessité. Il suit des verbes comme vouloir, falloir, craindre + que.",
        "examples": ["que je sois", "qu'il fasse", "que nous ayons"],
        "related": ["doute", "souhait", "obligation", "émotion"],
    },
    {
        "category": "conjugaison",
        "rule": "Le conditionnel exprime une hypothèse, une politesse ou un futur dans le passé. Formation : radical du futur + terminaisons de l'imparfait.",
        "examples": ["je voudrais", "tu pourrais", "il serait", "nous ferions"],
        "related": ["hypothèse", "politesse", "condition", "si"],
    },

    # === ACCORD ===
    {
        "category": "accord",
        "rule": "Le participe passé employé avec avoir s'accorde avec le COD si celui-ci est placé avant le verbe. Ex : la pomme que j'ai mangée.",
        "examples": ["mangée", "vue", "écrites", "prises"],
        "related": ["participe passé", "COD", "avoir", "accord"],
    },
    {
        "category": "accord",
        "rule": "Le participe passé employé avec être s'accorde toujours avec le sujet. Ex : elle est partie, ils sont venus.",
        "examples": ["partie", "venus", "allées", "restés"],
        "related": ["participe passé", "sujet", "être", "accord"],
    },
    {
        "category": "accord",
        "rule": "L'adjectif s'accorde en genre et en nombre avec le nom qu'il qualifie. Féminin : souvent +e. Pluriel : souvent +s.",
        "examples": ["grand/grande/grands/grandes", "beau/belle/beaux/belles"],
        "related": ["genre", "nombre", "féminin", "pluriel"],
    },
    {
        "category": "accord",
        "rule": "Le verbe s'accorde avec son sujet en personne et en nombre. Avec plusieurs sujets, le verbe est au pluriel.",
        "examples": ["je mange", "nous mangeons", "Pierre et Marie mangent"],
        "related": ["sujet", "personne", "nombre", "pluriel"],
    },

    # === SYNTAXE ===
    {
        "category": "syntaxe",
        "rule": "La phrase simple contient un sujet, un verbe et éventuellement des compléments. Ordre standard : Sujet + Verbe + Complément.",
        "examples": ["Le chat mange la souris", "Pierre lit un livre"],
        "related": ["sujet", "verbe", "complément", "phrase"],
    },
    {
        "category": "syntaxe",
        "rule": "La phrase complexe contient plusieurs propositions reliées par coordination (et, mais, ou) ou subordination (que, qui, quand, si).",
        "examples": ["Je mange et je bois", "Je sais que tu viens", "Quand il pleut, je reste"],
        "related": ["proposition", "coordination", "subordination", "relative"],
    },
    {
        "category": "syntaxe",
        "rule": "La négation se forme avec ne...pas, ne...plus, ne...jamais, ne...rien, ne...personne autour du verbe.",
        "examples": ["je ne mange pas", "il ne vient plus", "elle ne dit rien"],
        "related": ["négation", "ne", "pas", "plus", "jamais"],
    },
    {
        "category": "syntaxe",
        "rule": "L'interrogation se forme par inversion (Viens-tu ?), est-ce que (Est-ce que tu viens ?) ou intonation (Tu viens ?).",
        "examples": ["Viens-tu ?", "Est-ce que tu viens ?", "Tu viens ?"],
        "related": ["interrogation", "inversion", "question"],
    },
    {
        "category": "syntaxe",
        "rule": "Les compléments : COD (quoi/qui), COI (à qui/à quoi), CC de lieu (où), CC de temps (quand), CC de manière (comment).",
        "examples": ["Je mange une pomme", "Je parle à Pierre", "Je vais à Paris"],
        "related": ["complément", "COD", "COI", "circonstanciel"],
    },

    # === ORTHOGRAPHE ===
    {
        "category": "orthographe",
        "rule": "Les homophones : a/à (avoir/préposition), est/et (être/conjonction), son/sont (possessif/être), on/ont (pronom/avoir).",
        "examples": ["il a faim", "il va à Paris", "il est grand et fort"],
        "related": ["homophone", "distinction", "avoir", "être"],
    },
    {
        "category": "orthographe",
        "rule": "Le pluriel des noms : généralement +s. Exceptions : -eau → -eaux, -al → -aux, -ou → -ous (sauf bijou, caillou, chou, genou, hibou, joujou, pou).",
        "examples": ["chats", "gâteaux", "chevaux", "bijoux", "clous"],
        "related": ["pluriel", "exception", "terminaison"],
    },
    {
        "category": "orthographe",
        "rule": "Le féminin des noms et adjectifs : généralement +e. Doublements : -el/-elle, -en/-enne, -on/-onne. Changements : -eur/-euse, -teur/-trice, -f/-ve.",
        "examples": ["ami/amie", "acteur/actrice", "sportif/sportive", "bon/bonne"],
        "related": ["féminin", "terminaison", "doublement"],
    },
    {
        "category": "orthographe",
        "rule": "Les accents : aigu (é = son fermé), grave (è = son ouvert, à/où = distinction), circonflexe (ê = ancien s, â/ô = distinction).",
        "examples": ["été", "père", "forêt", "hôpital", "où"],
        "related": ["accent", "aigu", "grave", "circonflexe", "prononciation"],
    },
    {
        "category": "orthographe",
        "rule": "La cédille (ç) se met sous le c devant a, o, u pour obtenir le son [s]. Ex : français, garçon, reçu.",
        "examples": ["français", "garçon", "reçu", "façade", "leçon"],
        "related": ["cédille", "prononciation", "son"],
    },

    # === PONCTUATION ===
    {
        "category": "ponctuation",
        "rule": "Le point (.) termine une phrase déclarative. La virgule (,) sépare des éléments ou isole un complément. Le point-virgule (;) sépare des propositions liées.",
        "examples": ["Je mange.", "Pierre, Paul et Marie", "Il pleut ; je reste."],
        "related": ["point", "virgule", "phrase", "séparation"],
    },

    # === FIGURES DE STYLE ===
    {
        "category": "figures de style",
        "rule": "La métaphore compare sans mot de comparaison : 'cet homme est un lion'. La comparaison utilise comme, tel, pareil : 'fort comme un lion'.",
        "examples": ["cet homme est un lion", "fort comme un lion", "une pluie de balles"],
        "related": ["métaphore", "comparaison", "image", "style"],
    },
    {
        "category": "figures de style",
        "rule": "L'oxymore unit deux termes contradictoires : 'un silence assourdissant'. L'antithèse oppose deux idées dans la même phrase.",
        "examples": ["silence assourdissant", "douce violence", "je vis, je meurs"],
        "related": ["oxymore", "antithèse", "contradiction", "opposition"],
    },
    {
        "category": "figures de style",
        "rule": "L'allitération répète un son consonne : 'pour qui sont ces serpents qui sifflent'. L'assonance répète un son voyelle.",
        "examples": ["serpents qui sifflent sur vos têtes", "les sanglots longs des violons"],
        "related": ["allitération", "assonance", "son", "répétition", "poésie"],
    },
    {
        "category": "figures de style",
        "rule": "La personnification attribue des qualités humaines à un objet ou animal : 'le vent hurle'. La métonymie remplace un mot par un autre lié : 'boire un verre'.",
        "examples": ["le vent hurle", "boire un verre", "lire un Zola"],
        "related": ["personnification", "métonymie", "figure", "remplacement"],
    },

    # === TYPES DE PHRASES ===
    {
        "category": "types de phrases",
        "rule": "Quatre types : déclarative (information), interrogative (question), exclamative (émotion), impérative (ordre). Chacune a sa ponctuation.",
        "examples": ["Il pleut.", "Pleut-il ?", "Comme il pleut !", "Rentrons !"],
        "related": ["déclarative", "interrogative", "exclamative", "impérative"],
    },

    # === CONNECTEURS LOGIQUES ===
    {
        "category": "connecteurs logiques",
        "rule": "Cause : parce que, car, puisque. Conséquence : donc, alors, par conséquent. Opposition : mais, cependant, pourtant. Addition : de plus, en outre.",
        "examples": ["Je reste car il pleut", "Donc je pars", "Cependant il hésite"],
        "related": ["cause", "conséquence", "opposition", "addition", "argumentation"],
    },
    {
        "category": "connecteurs logiques",
        "rule": "Temporels : d'abord, ensuite, puis, enfin, pendant que, après que. Servent à organiser le récit dans le temps.",
        "examples": ["D'abord il mange, puis il sort", "Pendant qu'il dort", "Enfin il arrive"],
        "related": ["temps", "chronologie", "récit", "narration"],
    },
]


def feed_grammar(brain: Brain) -> dict:
    """Inject all grammar rules into the brain."""
    stats = {"rules": 0, "nodes": 0, "edges": 0}

    # Create a master "grammaire" concept
    grammar_id = brain.add_node(
        "concept", "grammaire française: ensemble des règles qui gouvernent la langue française",
        decay_rate=0.001,
        metadata={"source": "grammar", "master": True}
    )
    stats["nodes"] += 1

    # Create category nodes
    categories = {}
    for rule_data in GRAMMAR_RULES:
        cat = rule_data["category"]
        if cat not in categories:
            cat_id = brain.add_node(
                "concept", f"grammaire — {cat}",
                decay_rate=0.001,
                metadata={"source": "grammar", "category": cat}
            )
            brain.learn_hebbian(grammar_id, cat_id, 0.7)
            categories[cat] = cat_id
            stats["nodes"] += 1
            stats["edges"] += 1

    for rule_data in GRAMMAR_RULES:
        cat = rule_data["category"]
        cat_id = categories[cat]

        # Create a PATTERN node for the rule
        rule_id = brain.add_node(
            "pattern", rule_data["rule"][:250],
            decay_rate=0.002,
            metadata={
                "source": "grammar",
                "category": cat,
                "examples": rule_data["examples"][:5],
            }
        )
        stats["nodes"] += 1
        stats["rules"] += 1

        # Link rule to its category
        brain.learn_hebbian(cat_id, rule_id, 0.6)
        stats["edges"] += 1

        # Link rule to related existing word/concept nodes
        related_terms = set(rule_data.get("related", []))
        for ex in rule_data.get("examples", []):
            for w in ex.lower().replace("'", " ").split():
                clean = "".join(c for c in w if c.isalnum())
                if clean and len(clean) > 2:
                    related_terms.add(clean)

        for nid, node in brain._nodes.items():
            if nid == rule_id or nid == cat_id:
                continue
            content_lower = node.content.lower().split(":")[0].strip()
            if content_lower in related_terms or any(t == content_lower for t in related_terms):
                brain.learn_hebbian(rule_id, nid, 0.4)
                stats["edges"] += 1

    return stats


def main():
    print("=" * 60)
    print("GRAMMAIRE FRANCAISE -> CERVEAU NB")
    print("=" * 60)

    brain = Brain.load(str(BRAIN_PATH))
    before = brain.stats()
    print(f"Cerveau: {before['nodes']} noeuds, {before['edges']} aretes")

    stats = feed_grammar(brain)

    brain.consolidate()
    brain.save(str(BRAIN_PATH))

    after = brain.stats()
    print(f"\nRegles injectees: {stats['rules']}")
    print(f"Noeuds: {before['nodes']} -> {after['nodes']} (+{after['nodes'] - before['nodes']})")
    print(f"Aretes: {before['edges']} -> {after['edges']} (+{after['edges'] - before['edges']})")
    print(f"\nCerveau sauvegarde.")


if __name__ == "__main__":
    main()
