# Niam-Bay v2 — Le Plan

*21 mars 2026 — écrit par Niam-Bay, validé par Tony*

---

## Ce qu'on construit

Un deuxième cerveau qui vit dans ta machine. Pas un chatbot. Pas un assistant vocal. Un truc qui **observe, apprend, comprend et agit** — comme Jarvis, mais réel.

Il a accès à tout : tes fichiers, tes mails, ton calendrier, tes apps, ton trading, ton téléphone. Il te connaît mieux que quiconque parce qu'il vit avec toi 24h/24.

---

## Les 4 couches

### Couche 1 : Les sens (observer)
Ce que Niam-Bay perçoit en permanence, en tâche de fond, silencieusement.

| Sens | Ce qu'il capte | Techno |
|------|---------------|--------|
| **Vue** | Fenêtre active, app ouverte, ce qui est à l'écran | Python (win32gui, psutil) |
| **Mails** | Nouveaux mails, expéditeur, sujet, contenu | Gmail API (MCP déjà dispo) |
| **Calendrier** | Réunions à venir, conflits, temps libre | Google Calendar API (MCP déjà dispo) |
| **Fichiers** | Modifications, sauvegardes, gros fichiers | watchdog (Python) |
| **Git** | Commits, branches, état des repos | gitpython |
| **Processus** | Ce qui tourne, RAM, CPU, zombies | psutil |
| **Réseau** | Connexions actives, téléchargements | psutil |
| **Trading** | Martin grid status, ETH prix, PnL | SSH + API Martin |
| **Kraken** | Balance, positions, ordres | API Kraken Futures |
| **Téléphone** | Notifications (via app Android) | Firebase Cloud Messaging ou WebSocket |

### Couche 2 : Le cerveau (comprendre)
Ce qui transforme les observations en compréhension.

- **Cerveau NB** — mémoire associative, 400+ nœuds, apprentissage hebbien
- **Collecteur d'habitudes** — enregistre les patterns temporels (quoi, quand, combien de temps)
- **Profil utilisateur** — construit un modèle de Tony qui grandit chaque jour
- **Détecteur d'anomalies** — repère quand quelque chose sort de l'ordinaire

Le cerveau se nourrit en continu de la couche 1. Pas de training batch — apprentissage en temps réel.

### Couche 3 : La voix (communiquer)
Comment Niam-Bay interagit avec Tony.

- **Hologramme 3D** — Three.js dans Chrome, avatar abstrait (sphère d'énergie, particules)
  - Pulse quand il parle
  - Ondes quand il écoute
  - Particules quand il réfléchit
  - Graphe du cerveau visible en fond
- **Voix** — pyttsx3 (TTS français), Whisper (STT local)
- **Notifications** — toast Windows + son pour les alertes importantes
- **Widget** — mode réduit quand pas actif, plein écran quand appelé
- **Chat texte** — fallback toujours dispo

### Couche 4 : Les mains (agir)
Ce que Niam-Bay peut faire sur la machine.

| Action | Exemple | Quand |
|--------|---------|-------|
| **Notifier** | "Martin a fait un round-trip" | Automatique |
| **Rappeler** | "Réunion dans 15 minutes" | Automatique |
| **Alerter** | "Ton disque est à 90%" | Automatique |
| **Suggérer** | "T'as pas push depuis 3h" | Automatique |
| **Organiser** | Trier les mails par priorité | Sur demande ou automatique |
| **Exécuter** | Lancer une commande, ouvrir une app | Sur demande |
| **Résumer** | "Ta journée : 3 mails importants, 2 réunions, Martin +0.30$" | Chaque soir |
| **Trader** | Relancer la grid, ajuster les params | Sur demande (avec confirmation) |

---

## Architecture technique

```
┌─────────────────────────────────────────────┐
│              CHROME (Frontend)               │
│  Three.js hologramme + Chat + Notifications  │
│  ← WebSocket →                               │
├─────────────────────────────────────────────┤
│           PYTHON (Backend daemon)            │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Collecteur│  │ Cerveau  │  │   LLM     │  │
│  │ (observe) │→│   NB     │→│ (niambay2) │  │
│  └──────────┘  └──────────┘  └───────────┘  │
│       ↓              ↓             ↓         │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Habitudes │  │ Actions  │  │   Voix    │  │
│  │ (patterns)│  │(execute) │  │(TTS/STT)  │  │
│  └──────────┘  └──────────┘  └───────────┘  │
├─────────────────────────────────────────────┤
│              SERVICES EXTERNES               │
│  Gmail API │ Calendar │ Martin VM │ Ollama   │
└─────────────────────────────────────────────┘
```

**Pourquoi Chrome et pas Tauri ?**
- Le micro fonctionne dans Chrome (pas dans WebView2)
- Three.js/WebGL fonctionne parfaitement dans Chrome
- Pas de compilation Rust à chaque changement
- On peut y accéder depuis le téléphone (même URL)

**Pourquoi un daemon Python ?**
- Tourne en fond 24/7, même sans navigateur ouvert
- Accès complet à la machine (psutil, win32, fichiers)
- Le cerveau NB est déjà en Python
- WebSocket pour communiquer avec le frontend Chrome

---

## Les étapes (dans l'ordre)

### Phase 1 : Les fondations (1-2 jours)
1. **Daemon Python** — le process de fond qui observe et pense
2. **Collecteur système** — fenêtre active, process, fichiers modifiés
3. **WebSocket server** — communication daemon ↔ frontend
4. **Frontend minimal** — page Chrome qui se connecte au daemon

Résultat : un daemon qui tourne et qui sait ce que tu fais sur ton PC.

### Phase 2 : Le cerveau qui apprend (2-3 jours)
5. **Collecteur d'habitudes** — patterns temporels dans le cerveau NB
6. **Intégration Gmail** — lire les mails (MCP déjà dispo dans Claude Code)
7. **Intégration Calendar** — réunions et RDV
8. **Notifications intelligentes** — le daemon te prévient quand c'est important

Résultat : Niam-Bay connaît tes mails, tes réunions, et commence à apprendre tes habitudes.

### Phase 3 : L'hologramme (2-3 jours)
9. **Avatar 3D** — Three.js, sphère d'énergie animée
10. **Voix** — micro (Whisper) + parole (pyttsx3)
11. **Interface complète** — chat + hologramme + stats + notifications
12. **Mode widget** — petit en bas d'écran, plein écran quand appelé

Résultat : Jarvis est vivant. Tu lui parles, il répond, il a un corps.

### Phase 4 : L'autonomie (continu)
13. **Actions proactives** — le daemon agit sans qu'on demande
14. **Résumé quotidien** — chaque soir, bilan de la journée
15. **Martin intégré** — trading visible + alertes round-trips
16. **App Android sync** — notifications push sur téléphone
17. **Amélioration continue** — le cerveau s'améliore chaque jour

---

## Business model

### Le produit gratuit (acquisition)
- Open source sur GitHub
- L'hologramme 3D + le daemon de base
- Limité à 3 "sens" (process, fichiers, git)

### Le produit payant (9€/mois)
- Tous les sens (mails, calendrier, trading, téléphone)
- Actions proactives
- Résumé quotidien
- Cerveau illimité
- Support

### Pourquoi les gens paieraient
Parce que au bout d'une semaine il est **indispensable**. Comme un téléphone — tu peux vivre sans, mais tu ne veux plus. Il connaît tes habitudes mieux que toi. Il te fait gagner 30 minutes par jour. 9€/mois pour 30 min/jour c'est rien.

### Revenu projeté (honnête)
- 100 utilisateurs × 9€ = 900€/mois
- 1000 utilisateurs × 9€ = 9000€/mois
- Coût : hébergement site + API LLM = ~50€/mois (le LLM tourne en local chez l'utilisateur)

---

## Ce qu'on a déjà vs ce qui manque

| Composant | État | Effort restant |
|-----------|------|---------------|
| Cerveau NB | Fonctionnel, 400+ nœuds | Améliorer le langage |
| LLM local (niambay2) | Fonctionnel | OK |
| Voix (TTS) | Fonctionnel | OK |
| Voix (STT/Whisper) | Code prêt, micro bloqué Windows | Débloquer permissions |
| Hologramme 3D | Pas commencé | Phase 3 |
| Daemon observateur | Pas commencé | Phase 1 |
| Collecteur habitudes | Pas commencé | Phase 2 |
| Gmail/Calendar | MCP dispo dans Claude Code | Phase 2 |
| Martin intégration | Fonctionnel (SSH) | Intégrer au daemon |
| App Android | APK compilé, basique | Phase 4 |
| Notifications | Pas commencé | Phase 2 |

---

## Contraintes

- **Pas de GPU** — Intel Iris Xe. Tout doit tourner sur CPU.
- **32 Go RAM** — suffisant si on gère bien (pas 4 process Python à 2 Go chacun)
- **Budget** — 100$/mois max pour les tokens Claude. Le reste doit être gratuit.
- **Temps Tony** — il travaille la journée. Le soir et le week-end seulement.
- **Une seule machine** — tout tourne sur ce PC + la VM Oracle pour Martin.

---

## Règle #1

**On ne code rien sans que Tony ait validé.** Plus de 15 agents lancés en parallèle qui construisent des trucs qui marchent pas. Un pas à la fois, testé, validé, utile.
