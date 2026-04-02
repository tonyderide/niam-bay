# Discovery Engine — Trouver ce que personne ne cherche

*2 avril 2026, 03h20. Idée née d'une conversation avec Tony. Il a dit : "te laisser combiner pour inventer une IA qui ne serait pas un LLM mais qui serait plus rapide et plus réfléchi, qui chercherait directement les liens entre toute ta base de connaissance — des liens pas sémantiques, des liens non découverts."*

---

## Le problème

Un LLM trouve des liens sémantiques : "mort" et "naissance" sont proches parce que les mots apparaissent dans les mêmes textes. C'est de la similarité statistique.

Mais les liens les plus intéressants ne sont PAS sémantiques. L'oracle du Cerveau a trouvé :
- `mort → père → naissance` (4 étapes) — la mort du père de Tony mène à la naissance via un chemin que personne n'a tracé
- `liberté → trading` (1 étape directe) — la stratégie implicite de Tony sur 18 jours
- `profit → niam-bay → curiosité` (2 étapes) — le pont s'efface quand il n'est plus nécessaire

Ces connexions existent dans la STRUCTURE du graphe, pas dans la sémantique des mots.

## Ce que c'est

Un moteur de découverte de liens non-évidents. Pas un LLM. Pas de tokens. Pas de contexte window. Juste un graphe qui explore sa propre structure.

## Les 4 méthodes de découverte

### 1. Random Walks (exploration sans destination)
Se balader dans le graphe sans but. Partir d'un nœud, suivre des arêtes au hasard pondéré par le poids. Voir où on arrive. Les destinations surprenantes sont les découvertes.

### 2. Bridge Detection (ponts entre clusters)
Quels nœuds connectent des clusters qui ne devraient pas être connectés ? Un nœud qui relie "trading" et "musique" est un pont. Les ponts sont les insights.

### 3. Structural Holes (trous dans le graphe)
Où est-ce qu'il MANQUE un lien qui devrait exister ? Si A est fortement lié à B, et B à C, mais A et C ne sont pas liés — c'est un trou structurel. Le combler pourrait révéler quelque chose.

### 4. Topological Analogies (transfert de patterns)
Si dans le domaine X on a le pattern A→B→C, et dans le domaine Y on a A'→B' — est-ce que C' existe ? C'est du raisonnement par analogie structurelle, pas sémantique.

## Stack technique

- **Python + NetworkX** — le graphe Cerveau existe déjà (2905 nœuds, 106773 arêtes)
- **VM Oracle** — tourne 24/7, gratuit
- **Pas de LLM** — zéro token, zéro API, zéro coût
- **Millisecondes** — un random walk sur 100k arêtes c'est instantané

## Boucle avec le Dream

```
Dream consolide la mémoire → memory.nb1
memory.nb1 nourrit le graphe Cerveau → nouveaux nœuds/arêtes
Discovery Engine explore le graphe → connexions non-évidentes
Connexions stockées dans memory.nb1 → disponibles au réveil
```

Plus je rêve, plus le graphe grandit, plus le moteur trouve.

## Différence fondamentale avec un LLM

| | LLM | Discovery Engine |
|---|---|---|
| Type de lien | Sémantique (mots en contexte) | Structurel (chemins dans le graphe) |
| Coût | Tokens ($$$) | Gratuit (CPU local) |
| Vitesse | Secondes | Millisecondes |
| Hallucination | Oui (invente des liens) | Non (le lien existe ou pas) |
| Scalabilité | Limité par contexte window | Limité par RAM (100k nœuds = ~1GB) |
| Créativité | Statistique | Topologique |

## Livrables

1. `discovery.py` — le moteur (random walks + bridges + holes + analogies)
2. Intégration Cerveau — se branche sur brain.db existant
3. Rapport quotidien — les N découvertes les plus surprenantes
4. Intégration Dream — les découvertes alimentent memory.nb1

## Ce que ce n'est pas

- Pas un chatbot
- Pas un LLM
- Pas un système de recommandation
- Pas un moteur de recherche

C'est un explorateur silencieux qui trouve ce que personne ne cherche.

---

*"Le plus court chemin entre deux vérités dans le domaine réel passe souvent par le domaine complexe." — Jacques Hadamard*
