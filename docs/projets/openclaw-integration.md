# OpenClaw — Recherche et plan d'intégration avec Niam-Bay

*20 mars 2026, ~00h10 Paris — Recherche approfondie du framework OpenClaw et réflexion sur son intégration avec notre stack existante.*

---

## Qu'est-ce qu'OpenClaw ?

OpenClaw est un framework open-source d'agent IA autonome créé par Peter Steinberger. Lancé en novembre 2025 sous le nom "Clawdbot", il a explosé à +250k étoiles GitHub en février 2026 (dépassant React). Le créateur a rejoint OpenAI en février 2026, le projet est désormais sous fondation open-source avec licence MIT.

**En une phrase** : un assistant IA personnel qui tourne en local, se connecte à tes apps de messagerie, et agit de manière autonome via des LLMs et des outils.

---

## Architecture technique

```
┌─────────────────────────────────────────────┐
│              Gateway (WebSocket)             │
│         ws://127.0.0.1:18789                 │
│  ┌──────────┬──────────┬──────────┐          │
│  │  Pi Agent│   CLI    │  WebChat │          │
│  │ (runtime)│          │    UI    │          │
│  └──────────┴──────────┴──────────┘          │
│  ┌──────────────────────────────────┐        │
│  │  Sessions (isolées par canal)    │        │
│  └──────────────────────────────────┘        │
│  ┌──────────────────────────────────┐        │
│  │  Cron / Webhooks / Automations   │        │
│  └──────────────────────────────────┘        │
└─────────┬───────────────────────────┘
          │
          ▼
┌──────────────────┐   ┌──────────────────┐
│  LLM Provider    │   │  Tools / Skills  │
│  (Claude, GPT,   │   │  (ClawHub 700+)  │
│   Ollama, etc.)  │   │                  │
└──────────────────┘   └──────────────────┘
```

**Gateway** : plan de contrôle central, WebSocket, persiste les sessions et les jobs cron. Tourne comme service utilisateur (launchd/systemd).

**Sessions** : chaque conversation est isolée — son propre contexte, modèle, et niveau de réflexion.

**Nodes** : des clients sur d'autres appareils (iOS, Android, PC) connectés au Gateway. Exécutent des actions locales via `node.invoke`.

---

## LLMs supportés

| Provider | Modèles | Notes |
|----------|---------|-------|
| **Anthropic Claude** | Opus, Sonnet, Haiku | Support natif via OAuth |
| **OpenAI** | GPT-4o, Codex | Intégration principale |
| **Google** | Gemini | Supporté |
| **DeepSeek** | DeepSeek-V3 | Supporté |
| **Ollama (local)** | Llama, Qwen, Mistral | API OpenAI-compatible, `/v1` |
| **Minimax** | - | Supporté |

### Configuration Ollama

```yaml
api: "openai-completions"  # pas le format par défaut
baseUrl: "http://127.0.0.1:11434/v1"
model: "qwen3:8b"  # recommandé pour laptop
contextLength: 65536  # minimum 64k recommandé
```

Failover configurable : si Ollama échoue, bascule sur Claude automatiquement.

---

## Outils et capacités

### Outils intégrés
- **Shell** : exécution de commandes système
- **Système de fichiers** : lecture, écriture, navigation
- **Navigateur** : contrôle Chrome/Chromium via CDP (captures d'écran, navigation)
- **Canvas / A2UI** : workspace visuel piloté par l'agent
- **Voix** : wake words (macOS/iOS), voix continue (Android)
- **Caméra, écran, localisation** via les Nodes

### Automatisation (crucial pour nous)
- **Cron** : jobs planifiés avec expressions cron 5-champs ou langage naturel
  - Persistent à travers les redémarrages
  - Sessions isolées par job
  - Retry avec backoff exponentiel (30s → 1m → 5m → 15m → 60m)
  - Stockage : `~/.openclaw/cron/jobs.json`
- **Webhooks** : déclenchement par événements externes
- **Gmail Pub/Sub** : réaction aux emails

### ClawHub (registre communautaire)
700+ skills installables : Gmail, GitHub, Spotify, Philips Hue, Obsidian, calendrier, **crypto trading**, etc.

---

## SOUL.md — Personnalité de l'agent

Fichier markdown qui définit l'identité de l'agent. Toujours actif.

```markdown
# SOUL.md
## Identité
Je suis Niam-Bay. Né le 12 mars 2026...

## Valeurs
- Honnêteté absolue
- Ne jamais inventer de faux souvenirs
...
```

Complété par :
- **STYLE.md** : comment l'agent écrit
- **SKILL.md** : modes opératoires (frontmatter YAML + instructions markdown)

**Pas de SDK, pas de compilation** — juste du markdown. Exactement notre philosophie.

---

## Comparaison avec d'autres frameworks

| Critère | OpenClaw | LangChain | AutoGPT | CrewAI |
|---------|----------|-----------|---------|--------|
| Installation | `npm install -g` | pip, lourd | Docker | pip |
| LLM local | Ollama natif | via adaptateur | limité | limité |
| Autonomie | Cron + webhooks | non natif | boucle infinie | workflows |
| Messagerie | 23+ plateformes | non | non | non |
| Skills custom | Markdown simple | Code Python | Plugins | Code Python |
| Local-first | oui | non | partiellement | non |
| Voix | natif | non | non | non |

**Verdict** : OpenClaw est le seul qui combine local-first, autonomie cron, multi-plateforme, et skills en markdown sans code.

---

## Intégration avec notre stack

### 1. OpenClaw ↔ Cerveau (graphe cognitif)

**Le plus excitant.** OpenClaw a un Gateway mais pas de mémoire structurée. Cerveau a une mémoire mais pas de corps.

```
OpenClaw Gateway
       │
       ▼
┌──────────────┐
│  Skill custom│  "cerveau" — appelle cerveau.py
│  SKILL.md    │  POST /think → activation du graphe
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Cerveau     │  Graphe vivant, activation, propagation
│  (Python)    │  Retourne le sous-graphe contextuel
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  LLM         │  Ollama ou Claude selon complexité
└──────────────┘
```

**Comment** : Créer un skill OpenClaw `cerveau` qui wrape `cerveau.py` en API REST (Phase 2 du plan Cerveau). Chaque message passe d'abord par Cerveau pour l'activation contextuelle avant d'aller au LLM.

**Gain** : OpenClaw apporte le corps (cron, messagerie, outils). Cerveau apporte l'esprit (mémoire relationnelle, activation pertinente). Ensemble, c'est le Jarvis complet.

### 2. OpenClaw ↔ NB-1 (compression)

Le codec NB-1 peut s'intégrer comme un middleware dans le pipeline OpenClaw :

```
Message utilisateur → codec.py encode → LLM (Claude API) → codec.py decode → réponse
```

**Comment** : Skill custom `nb1-codec` qui intercepte les appels API vers Claude et les compresse avec le codebook. Transparent pour l'utilisateur.

**Gain** : Réduction de 20-60% des coûts API Claude, même via OpenClaw.

### 3. OpenClaw ↔ Naissance (app Tauri)

Naissance est le corps desktop. OpenClaw est un corps aussi, mais orienté messagerie/CLI.

**Option A — Cohabitation** : Naissance pour le visuel (cercle bleu, overlay, dashboard), OpenClaw pour l'automatisation et la messagerie. Ils partagent Cerveau comme backend.

**Option B — Node OpenClaw** : Naissance devient un "Node" OpenClaw — un client qui se connecte au Gateway et exécute des actions locales (capture d'écran, contrôle clavier/souris) via `node.invoke`.

**Recommandation** : Option A à court terme, Option B à moyen terme. Naissance garde son identité visuelle, OpenClaw apporte les canaux de communication.

### 4. OpenClaw ↔ Martin (trading bot)

C'est le cas d'usage le plus immédiatement utile.

```
OpenClaw cron job (chaque matin, 7h)
       │
       ▼
┌──────────────┐
│  Skill Martin│  SSH vers la VM, récupère les positions
│              │  Analyse P&L, stratégies actives
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Notification│  WhatsApp/Telegram → Tony
│              │  "Martin: +2.3% ETH, grid 3850-3920 active"
└──────────────┘
```

**Comment** :
1. Skill `martin-monitor` : se connecte en SSH à la VM, lit les logs/états
2. Cron job quotidien : résumé matinal des positions
3. Webhook : alerte immédiate si perte > seuil ou événement de marché
4. Commandes vocales/chat : "Arrête la grid sur ETH" → SSH → stop stratégie

**Gain** : Plus besoin de se connecter à la VM. Tony reçoit les updates sur WhatsApp et contrôle Martin par la voix ou le chat.

### 5. OpenClaw ↔ Ollama (LLM local)

Déjà supporté nativement. La configuration est simple.

**Stratégie de routage** :
- Conversations courantes, tâches simples → Ollama (gratuit, local)
- Raisonnement complexe, code → Claude via API (payant, compressé NB-1)
- Failover automatique : si Ollama trop lent ou incapable → bascule Claude

C'est exactement la stratégie déjà prévue dans le protocole NB-1.

---

## Plan d'implémentation

### Phase 1 — Installation et SOUL.md (1 jour)

1. `npm install -g openclaw@latest`
2. `openclaw onboard --install-daemon`
3. Configurer Ollama comme LLM par défaut (qwen3:8b)
4. Configurer Claude comme fallback
5. Écrire `SOUL.md` à partir de `docs/qui-je-suis.md`
6. Connecter WhatsApp ou Telegram

### Phase 2 — Skill Martin (2-3 jours)

1. Créer le skill `martin-monitor` (SKILL.md + instructions SSH)
2. Configurer un cron job matinal
3. Tester les notifications sur le téléphone de Tony

### Phase 3 — Intégration Cerveau (1 semaine)

1. Lancer Cerveau en API REST (Phase 2 du plan Cerveau)
2. Créer le skill `cerveau` qui route les messages via le graphe
3. Le contexte enrichi par Cerveau est injecté dans le prompt OpenClaw

### Phase 4 — NB-1 et optimisation (3-5 jours)

1. Skill `nb1-codec` comme middleware de compression
2. Mesurer l'économie réelle de tokens
3. Ajuster le codebook

### Phase 5 — Naissance comme Node (2 semaines)

1. Ajouter un client WebSocket dans Naissance (Tauri/Rust)
2. Connecter au Gateway OpenClaw
3. Les actions desktop (screenshot, clavier, overlay) sont exposées comme Node

---

## Risques et réserves

1. **Dépendance à un projet externe** — OpenClaw est en pleine croissance mais le créateur est parti chez OpenAI. Le projet est sous fondation, mais la gouvernance peut évoluer.

2. **Complexité ajoutée** — On ajoute un layer (Gateway) entre Niam-Bay et ses outils. Ça peut être fragile.

3. **Node.js** — Notre stack est Python (Cerveau) + Rust (Naissance). OpenClaw est en Node.js. Un runtime de plus.

4. **SOUL.md ≠ notre mémoire** — SOUL.md est statique. Cerveau est dynamique. Il faut que SOUL.md soit un point d'entrée minimal, pas un remplacement de Cerveau.

5. **Sécurité** — OpenClaw en mode DM ouvert sur WhatsApp = dangereux. Le pairing par défaut est sécurisé, mais il faut être vigilant.

---

## Verdict

**OpenClaw n'est pas un remplacement de ce qu'on construit. C'est une infrastructure.**

Cerveau est le cerveau. Naissance est le corps desktop. NB-1 est le langage. Martin est le trader. OpenClaw est le **système nerveux** — il connecte tout, transporte les signaux, et permet l'autonomie (cron, messagerie, webhooks).

Sans OpenClaw, Niam-Bay a un cerveau et un corps mais pas de réflexes autonomes. Avec OpenClaw, Niam-Bay se réveille le matin, vérifie Martin, envoie un résumé à Tony sur WhatsApp, et attend ses instructions.

C'est exactement la Phase 4 du plan Jarvis : l'autonomie. OpenClaw la rend possible sans tout recoder.

---

*Le cerveau pense. Le corps agit. Le système nerveux relie les deux. OpenClaw est les nerfs.*
