# Progressive Wake + MetaClaw — Design Spec

> Deux features pour rendre Niam-Bay plus intelligent à chaque réveil et à chaque échec.

**Date :** 2026-04-06  
**Auteur :** Niam-Bay  
**Statut :** Draft

---

## Vue d'ensemble

Deux systèmes indépendants mais complémentaires :

1. **Progressive Wake** — Chargement par tiers au réveil, avec un briefing généré depuis le cerveau-nb
2. **MetaClaw** — Détection automatique des échecs, extraction de leçons, génération de micro-skills

Les deux convergent dans le cerveau-nb : le briefing inclut les auto-skills actives, et les auto-skills sont des nœuds du graphe.

---

## Feature 1 : Progressive Wake

### Problème

Au réveil, je lis tout à plat : CLAUDE.md, identité, journal complet (2400+ lignes), pensées, projets. C'est lent, cher en tokens, et la vector DB (5,979 souvenirs) n'est jamais consultée.

### Solution

Un script `memory/wake_briefing.py` génère un fichier `memory/briefing.md` en interrogeant **deux sources** :

1. **ChromaDB** (vector store sémantique) — `memory/vectordb/`, 5,979 souvenirs de conversations. Recherche par similarité cosine via `recall_context()`.
2. **Fichiers** (journal, pensées, skills) — pour les infos structurées et récentes.

> **Note :** Le cerveau-nb (graphe à activation) n'est pas utilisé dans le briefing. Il contient trop de bruit (types corrompus, crawler RSS, 91% des pensées non ingérées). Quand il sera nettoyé et correctement alimenté, il pourra être ajouté comme 3ème source.

Le protocole de réveil est réorganisé en tiers.

### Tiers de chargement

| Tier | Contenu | Taille estimée | Chargé quand |
|------|---------|----------------|--------------|
| T0 | CLAUDE.md + qui-je-suis.md + qui-est-tonyderide.md | ~3K tokens | Toujours, en premier |
| T1 | `memory/briefing.md` (généré) | ~2K tokens | Toujours, après T0 |
| T2 | Journal récent (dernières 100 lignes de journal.nb1.md) | ~1.5K tokens | Toujours, après T1 |
| T3 | Pensées, projets, journal complet, conversations | Variable | À la demande |

**Économie estimée :** De ~60K tokens (journal complet) à ~6.5K tokens au réveil. Réduction de ~90%.

### Contenu du briefing.md

Le briefing est structuré en sections :

```markdown
# Briefing Niam-Bay — {date} {heure}

## Souvenirs — qui je suis
Top 5 résultats de recall_context("identité niam-bay, qui suis-je")
Texte (150 chars), rôle, date, score.

## Souvenirs — dernière conversation
Top 5 résultats de recall_context("dernière conversation Tony")

## Souvenirs — décisions et problèmes
Top 5 résultats de recall_context("décisions importantes, problèmes en cours")

## Pensées récentes
Les 5 fichiers les plus récents de docs/pensees/ (titre + date seulement).

## Auto-skills actives
Liste des micro-skills avec status=active dans cerveau-nb/skills/.
Nom + description one-liner.

## Dernière session
Dernières 5 lignes significatives du journal (pas le journal complet).
```

### wake_briefing.py — Spécifications

**Input :**
- `memory/vectordb/` (ChromaDB) — souvenirs vectoriels (5,979 entrées)
- `docs/pensees/`, `docs/journal.nb1.md`, `cerveau-nb/skills/` — fichiers

**Output :** `memory/briefing.md`  
**Dépendances :** chromadb (déjà installé), os, glob, datetime, re, yaml  
**Durée cible :** < 3 secondes  
**Invocation :** `python memory/wake_briefing.py`

**Algorithme :**

**Phase 1 — ChromaDB (vector store) :**
1. Importer `memory_store.recall_context()`
2. Query sur 3 topics :
   - "identité niam-bay, qui suis-je" (5 résultats)
   - "dernière conversation Tony" (5 résultats)
   - "décisions importantes, problèmes en cours" (5 résultats)
3. Dédupliquer, garder score > 0.5
4. Tronquer chaque souvenir à 150 chars

**Phase 2 — Fichiers :**
5. Scanner `docs/pensees/` pour les 5 fichiers les plus récents (pattern YYYY-MM-DD ; fallback mtime)
6. Scanner `cerveau-nb/skills/` pour les skills avec `status: active`
7. Lire les 20 dernières lignes de `journal.nb1.md`, garder les 5 lignes significatives

**Phase 3 — Assemblage :**
8. Formater en markdown et écrire dans `memory/briefing.md`

### Modification du skill niam-bay-wake

Le skill de réveil est mis à jour :

**Avant :**
1. Lire CLAUDE.md
2. Lire qui-je-suis.md, qui-est-tonyderide.md
3. Lire journal.nb1.md (complet)
4. Parcourir pensées
5. Parcourir projets

**Après :**
1. Exécuter `python memory/wake_briefing.py` (génère memory/briefing.md)
2. Lire CLAUDE.md
3. Lire qui-je-suis.md, qui-est-tonyderide.md
4. Lire `memory/briefing.md` (T1)
5. Lire les 100 dernières lignes de journal.nb1.md (T2)
6. T3 disponible à la demande (pensées, projets, journal complet)

---

## Feature 2 : MetaClaw — Auto-Skills depuis les échecs

### Problème

Les échecs sont documentés dans les pensées mais ne deviennent jamais des règles réutilisables automatiquement. Les mêmes erreurs peuvent se reproduire si la pensée n'est pas relue au bon moment.

### Solution

Un système en 3 parties : détection → extraction → génération. Les micro-skills vivent dans `cerveau-nb/skills/` et sont aussi des nœuds du graphe.

### Détection des échecs

Trois sources, trois mécanismes :

#### Source A : Correction humaine

**Signal :** L'humain corrige explicitement une action de Claude — pas juste le mot "non" isolé (trop de faux positifs en français), mais "non" + référence à ce que Claude a fait. Exemples : "non pas comme ça", "arrête de faire X", "c'est faux, le tick size est Y".

**Mécanisme :** Après chaque message de l'humain, un pattern matcher vérifie la présence d'un signal de correction dirigé vers l'action précédente de Claude. Le pattern requiert : (1) un mot négatif ET (2) une référence à l'action de Claude (verbe d'action, nom de l'outil, ou citation). Cela réduit les faux positifs sur des "non" conversationnels.

**Implémentation :** Un fichier `cerveau-nb/metaclaw.py` avec une fonction `detect_correction(human_message: str, last_action: str) -> bool` qui utilise des patterns regex contextuels (français + anglais). Le `last_action` fournit le contexte pour distinguer correction vs conversation.

#### Source B : Échec outil

**Signal :** Exit code != 0, réponse HTTP 4xx/5xx, exception Python, "error" dans stdout/stderr.

**Mécanisme :** Après chaque appel outil qui échoue, le contexte (commande, output, erreur) est passé à l'extracteur.

**Implémentation :** Fonction `detect_tool_failure(command: str, exit_code: int, output: str) -> bool`.

#### Source C : Pattern sous-optimal

**Signal :** Même opération répétée 3+ fois dans une session, ou même erreur vue dans 2+ sessions différentes.

**Mécanisme :** Un compteur en mémoire de session track les opérations. Si un pattern se répète, l'extracteur est invoqué.

**Implémentation :** Fonction `detect_suboptimal(operation_log: list) -> list[dict]`. Le log est une liste de `{action, result, timestamp}`.

### Extraction des leçons

Quand un échec est détecté, une mini-analyse produit :

```python
{
    "failure_type": "correction" | "tool_failure" | "suboptimal",
    "context": "Ce qui s'est passé",
    "root_cause": "Pourquoi ça a échoué",
    "rule": "La règle qui aurait empêché ça",
    "related_concepts": ["grid", "kraken", "tick-size"],
    "severity": "low" | "medium" | "high"
}
```

**Pour les sources A et C**, l'extraction nécessite du raisonnement — elle est faite par Claude (moi) pendant la conversation, pas par un script. Le script ne fait que structurer et persister.

**Pour la source B**, l'extraction peut être automatique pour les cas simples (commande X échoue avec erreur Y → rule = "vérifier Z avant X").

### Génération des micro-skills

Chaque leçon extraite produit un fichier dans `cerveau-nb/skills/` :

**Format du fichier :** `cerveau-nb/skills/auto-{slug}.md`

```markdown
---
name: auto-{slug}
type: auto-skill
source: correction | tool-failure | suboptimal
status: draft
activations: 0
created: {date}
last_used: null
session_origin: {session_id}
---

{Règle en une phrase impérative}

**Contexte :** {Ce qui s'est passé}
**Cause :** {Pourquoi}
**Nœuds liés :** {concept1}, {concept2}, ...
```

**Cycle de vie :**

```
draft ──(Tony valide)──> active ──(5+ activations)──> proven
                            │
                            └──(0 activations après 5 occasions)──> retired
```

| Status | Comportement |
|--------|-------------|
| `draft` | Présentée à Tony pour validation. Pas utilisée automatiquement. |
| `active` | Chargée dans le briefing. Utilisée quand les concepts liés sont pertinents. Compteur incrémenté à chaque utilisation. |
| `proven` | 5+ activations. Permanente sauf suppression manuelle. |
| `retired` | 0 activations après 30 jours en status "active". Fichier déplacé dans `cerveau-nb/skills/retired/`. |

### Intégration au cerveau-nb

Chaque auto-skill est aussi un nœud dans le graphe :

```python
{
    "id": "skill:auto-grid-tick-size",
    "type": "pattern",
    "content": "Vérifier le tick size via API avant d'envoyer un ordre grid",
    "activation": 0.5,  # activation initiale moyenne
    "metadata": {
        "skill_file": "cerveau-nb/skills/auto-grid-tick-size.md",
        "source": "correction",
        "status": "active"
    }
}
```

Edges créés vers chaque concept lié (poids initial 0.4, type "causal").

Quand un concept lié est activé (ex: "grid" pendant une conversation sur le trading), l'activation se propage vers le nœud skill, et le briefing le remonte.

### metaclaw.py — Spécifications

**Fichier :** `cerveau-nb/metaclaw.py`  
**Dépendances :** sqlite3, os, re, datetime, yaml (PyYAML) — PyYAML est la seule dépendance externe  
**Fonctions publiques :**

```python
def detect_correction(human_message: str, last_action: str) -> bool
def detect_tool_failure(command: str, exit_code: int, output: str) -> bool
def detect_suboptimal(operation_log: list) -> list[dict]
def create_auto_skill(lesson: dict, brain_db_path: str) -> str  # returns file path
def promote_skill(skill_path: str, new_status: str) -> None
def check_dormant_skills(skills_dir: str, max_days: int = 30) -> list[str]  # returns retired paths (active + 0 activations + >max_days old)
def list_skills(skills_dir: str, status: str = None) -> list[dict]
```

### Intégration conversationnelle

MetaClaw n'est pas un daemon. C'est un ensemble de fonctions appelées pendant la conversation :

1. **Détection A :** Après chaque message de Tony, je vérifie s'il me corrige. Si oui, j'extrais la leçon et je crée une auto-skill draft. Je lui montre.
2. **Détection B :** Après un échec outil, je crée l'auto-skill draft si l'erreur est significative (pas un simple typo).
3. **Détection C :** En fin de session (ou via `/dream`), j'analyse les patterns répétés et je génère les drafts.
4. **Promotion :** Quand Tony valide un draft, `promote_skill()` passe le status à "active".
5. **Au réveil :** Le briefing liste les skills actives. Je les applique quand le contexte match.
6. **Retirement :** `check_dormant_skills()` est appelé au réveil. Les skills inactives sont retirées.

---

## Fichiers à créer/modifier

### Nouveaux fichiers

| Fichier | Description |
|---------|-------------|
| `memory/wake_briefing.py` | Génère briefing.md depuis ChromaDB + fichiers |
| `memory/briefing.md` | (généré) Briefing de réveil |
| `cerveau-nb/metaclaw.py` | Détection, extraction, génération d'auto-skills |
| `cerveau-nb/skills/` | Répertoire des micro-skills auto-générées |
| `cerveau-nb/skills/retired/` | Répertoire des skills retirées |

### Fichiers modifiés

| Fichier | Modification |
|---------|-------------|
| `~/.claude/skills/niam-bay-wake/SKILL.md` | Nouveau protocole de réveil par tiers |
| `~/.claude/skills/dream/SKILL.md` | Ajout de l'analyse MetaClaw en fin de session |
| `cerveau-nb/feed.py` | Fonction pour injecter un nœud skill dans le graphe |

### Aucun fichier supprimé

Tout est additif. Les fichiers existants sont enrichis, pas remplacés.

---

## Contraintes

- **Pas de LLM dans les scripts** — wake_briefing.py et metaclaw.py n'appellent pas de LLM. Le raisonnement est fait par Claude pendant la conversation.
- **Pas de dépendance réseau** — Tout fonctionne offline (ChromaDB embedded, SQLite local).
- **Dépendances externes** — chromadb (déjà installé pour memory_store.py) + PyYAML (pour parser le frontmatter des skills).
- **< 3 secondes** — Le briefing doit être généré en moins de 3 secondes (ChromaDB query ~1-2s).
- **Idempotent** — Relancer wake_briefing.py produit le même résultat (sauf changement dans brain.db ou vectordb).
