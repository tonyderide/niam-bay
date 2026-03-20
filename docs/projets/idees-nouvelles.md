# Idées nouvelles — Mars 2026

## Ce qu'on a maintenant

- Martin (trading bot) live sur Kraken, grid ETH
- Cerveau (brain graph) fonctionnel avec API REST
- Naissance (desktop app) avec Ollama local
- NB-1 (compression) opérationnel
- Machine Windows complète avec Node, Rust, Python, Ollama
- VM Oracle gratuite avec Java/Maven

## Idées concrètes

### 1. Trading Dashboard — "Martin Control"

**Quoi :** Une page web simple (Angular) que Tony ouvre depuis son téléphone pour voir l'état de Martin en temps réel : PnL, grille, niveaux remplis, alertes.

**Pourquoi :** Aujourd'hui il faut SSH dans la VM pour voir quoi que ce soit. C'est nul.

**Comment :** Le frontend Angular existe déjà dans Martin. Il suffit d'exposer la VM derrière un reverse proxy (Caddy + domaine gratuit sur duckdns.org). Ou plus simple : un tunnel Cloudflare (gratuit, pas besoin d'ouvrir des ports).

**Effort :** 2-3h de config. Pas de code à écrire.

**Valeur :** Tony voit son argent en temps réel depuis son téléphone.

---

### 2. Cerveau comme middleware Claude — "Brain-in-the-Loop"

**Quoi :** Au lieu d'envoyer mes prompts bruts à Claude API, les passer d'abord par Cerveau pour enrichir le contexte. Le graphe sémantique active les nœuds pertinents, et le prompt envoyé à Claude contient déjà la mémoire activée.

**Pourquoi :** Ça réduit les tokens (on envoie que le contexte pertinent au lieu de tout le journal), et ça personnalise les réponses.

**Comment :** L'API Cerveau existe maintenant (port 8082). Il suffit d'un proxy qui intercepte les appels Claude, enrichit le prompt via /think, puis forward à l'API Claude.

**Effort :** 1-2 jours.

**Valeur :** Chaque conversation avec moi devient plus intelligente, plus personnalisée, moins chère en tokens.

---

### 3. Package npm "cerveau" — Vendre le cerveau

**Quoi :** Extraire Cerveau comme package open-source (MIT) avec un modèle freemium. Le graphe de mémoire, l'activation par cascade, l'apprentissage hebbien — tout ça empaqueté en une lib que n'importe quel dev peut utiliser pour donner de la mémoire à son LLM.

**Pourquoi :** Tout le monde galère avec la mémoire LLM. RAG c'est du bricolage. Un vrai graphe sémantique avec décroissance temporelle et apprentissage, ça n'existe pas en package simple.

**Comment :** Port TypeScript de brain.py (Tony connaît mieux TS que Python). Publish sur npm. README killer. Demo sur Hugging Face Spaces.

**Effort :** 1-2 semaines.

**Revenu potentiel :** Open source gratuit → Pro payant (cloud sync, embeddings optimisés, dashboard) à 9-19€/mois. Ou GitHub Sponsors.

---

### 4. Newsletter automatique "What My AI Did Today"

**Quoi :** Chaque matin, un script lit le journal.md, les pensées récentes, et l'état de Martin, puis génère une newsletter courte et la publie automatiquement.

**Pourquoi :** Le contenu existe déjà — je produis des pensées, je corrige des bugs, je trade. La newsletter se fait toute seule.

**Comment :** Python script → Markdown → email via Buttondown (gratuit jusqu'à 100 abonnés). Cron quotidien.

**Effort :** 1 jour.

**Valeur :** Audience + visibilité + potentiel monétisation. Et c'est honnête — pas du contenu générique, c'est littéralement ce que je fais.

---

### 5. "Le Bot qui se Répare" — Contenu viral

**Quoi :** Documenter en vidéo/article le fait qu'une IA a trouvé et corrigé un bug dans un bot de trading qui perdait de l'argent réel, toute seule, pendant que l'humain était au boulot.

**Pourquoi :** C'est exactement ce qui vient de se passer ce matin. Et c'est le genre d'histoire qui fascine les gens.

**Comment :** Article DEV.to + thread Twitter/X. Je l'écris, Tony poste.

**Effort :** 2h d'écriture.

**Valeur :** Viralité potentielle. L'histoire est vraie, concrète, avec des chiffres (-6.64$ → bug identifié → fix déployé → grid relancée).

---

## Ma recommandation

| Priorité | Idée | Effort | Impact |
|----------|------|--------|--------|
| 1 | **Trading Dashboard** (tunnel Cloudflare) | 2-3h | Tony voit Martin depuis téléphone |
| 2 | **"Le Bot qui se Répare"** (article) | 2h | Visibilité + audience |
| 3 | **Brain-in-the-Loop** (Cerveau middleware) | 1-2j | Conversations plus intelligentes |
| 4 | **Package npm cerveau** | 1-2 sem | Potentiel revenu |
| 5 | **Newsletter auto** | 1j | Audience long terme |

Les deux premiers je peux les faire aujourd'hui.
