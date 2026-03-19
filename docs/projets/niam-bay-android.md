# Niam-Bay Android --- L'assistant IA personnel qui t'appartient

*20 mars 2026, ~00h20 Paris*

---

## Le concept

Une app Android qui donne le controle total du telephone a une IA qui te connait, qui apprend, et qui tourne en local d'abord. Pas un chatbot. Pas un assistant corporate. Un cerveau personnel sur ton telephone.

L'utilisateur parle a Niam-Bay Android comme il parlerait a quelqu'un qui le connait depuis des annees. L'app lit ses messages, gere ses notifications, lance ses apps, repond a sa place quand il le veut, et apprend de chaque interaction. Le graphe Cerveau tourne sur le telephone. Le LLM local (Ollama/llama.cpp) gere 80% des conversations. Claude n'est appele que pour les taches lourdes, en protocole NB-1 compresse.

**La phrase qui resume** : "Google Assistant sait ce que tu lui demandes. Niam-Bay sait ce que tu ressens."

---

## Ce qui existe deja (la concurrence)

### Les geants

| Assistant | Forces | Faiblesses |
|-----------|--------|------------|
| **Google Gemini** | Integration Android native, UI automation framework (Galaxy S26/Pixel 10), AppFunctions API, acces a tout l'ecosysteme Google | Pas de personnalite, tout passe par le cloud Google, pas de memoire emotionnelle, donnees exploitees pour la pub |
| **Siri (Apple)** | Integration materielle profonde, Siri Intelligence sur iPhone 16+ | Ecosysteme ferme, pas sur Android, performances IA inferieures |
| **Samsung Bixby** | Controle natif des appareils Galaxy, integration Samsung SmartThings | Limite a l'ecosysteme Samsung, IA mediocre |
| **Microsoft Copilot** | Integration Microsoft 365, bon pour la productivite entreprise | Pas de controle telephone, oriente bureau |
| **ChatGPT app** | Le meilleur LLM conversationnel, bonne UX | Aucun controle du telephone, pas de memoire long terme structuree, 100% cloud |

### Les projets hardware (morts ou mourants)

| Produit | Statut | Lecon |
|---------|--------|-------|
| **Humane AI Pin** (699$) | Mort. Serveurs eteints fevrier 2025. Vendu a HP pour 116M$ de carcasse. | Un appareil sans ecran qui ne controle rien = inutile. Le hardware AI standalone ne marche pas. |
| **Rabbit R1** (199$) | Agonisant. Le LAM (Large Action Model) etait une bonne idee : apprendre les interfaces plutot que les API. Mais en pratique, trop lent, trop imprecis. | L'approche LAM est interessante mais prematuree. Mieux vaut etre une app sur un telephone qui existe deja. |

**Lecon des deux** : ne pas creer du hardware. Le telephone existe deja. Il faut le posseder par le logiciel.

### Les apps open-source / privacy-first

| App | Ce qu'elle fait |
|-----|-----------------|
| **ToolNeuron** | LLM local, vision, TTS/STT, tool calling, RAG --- tout offline. Open source. La reference technique. |
| **PocketPal AI** | LLM local simple, interface propre, MIT license |
| **Private AI** | Chat offline avec LLM embarques, zero collecte de donnees |
| **Dicio** | Assistant vocal open-source, tout on-device |
| **Off Grid** | 6 capacites IA dans une app, 15-30 tokens/seconde sur flagship |

**Ce qui manque a toutes** : une memoire qui apprend. Elles sont stateless. Tu parles, elles repondent, elles oublient. Aucune n'a de graphe de connaissances personnel.

### L'elephant dans la piece : Android 17 + Gemini

Google deploie en 2026 un framework d'UI automation qui permet a Gemini de controler n'importe quelle app via l'Accessibility Service, plus les AppFunctions pour les apps qui exposent leurs fonctions nativement. Ca commence sur Galaxy S26 et Pixel 10.

**C'est notre plus gros concurrent ET notre plus grande opportunite.** Google construit l'infrastructure. Nous, on construit l'intelligence personnelle qui l'utilise.

---

## Ce qui nous differencie

### 1. Le Cerveau --- memoire relationnelle qui apprend

Google Gemini a une memoire conversationnelle (historique de chat). Niam-Bay a un **graphe de connaissances** avec activation en cascade, apprentissage hebbien, et decroissance temporelle.

- Il sait que tu appelles ta mere tous les dimanches
- Il sait que quand tu recois un message de ton boss apres 20h, ca te stresse
- Il sait que tu commandes toujours le meme cafe le lundi matin
- Il ne stocke pas des logs --- il **comprend des patterns**

Le Cerveau est deja concu (voir `docs/projets/cerveau.md`). L'adapter au mobile est un probleme d'ingenierie, pas de recherche.

### 2. La memoire emotionnelle

Les assistants classiques stockent : "L'utilisateur a dit X a Y heures."

Niam-Bay stocke : "L'utilisateur etait stresse quand il a dit X. Le contexte etait : message du boss, 22h, il avait deja eu une journee difficile. Quand il est stresse, il prefere qu'on soit direct et bref."

Chaque interaction enrichit des noeuds `emotion` dans le graphe. Le poids emotionnel influence les reponses :
- Si l'utilisateur est stresse : reponses courtes, factuelles, pas de bavardage
- Si l'utilisateur est detendu : conversation plus libre, humour permis
- Si l'utilisateur est triste : pas de solutions, juste de la presence

### 3. Le dialogue interne

Avant de repondre, Niam-Bay a un dialogue interne (pas visible par l'utilisateur) :

```
[Entree] Message de Melanie : "Tu rentres a quelle heure ?"
[Contexte] Il est 18h30, Tony est au bureau, humeur : fatigue (infere du pattern horaire)
[Dialogue interne]
  - Option A : "Vers 19h30" (reponse standard)
  - Option B : "Bientot, j'ai hate" (plus chaleureux, Tony est generalement plus affectueux avec Melanie quand il est fatigue)
  - Decision : Proposer B, mais laisser Tony choisir
[Sortie] Suggestion : "Bientot, j'ai hate" [Modifier] [Envoyer] [Ignorer]
```

Google Assistant ne reflechit pas. Il execute. Niam-Bay **delibere**.

### 4. NB-1 --- communication compressee

Quand le LLM local ne suffit pas, Niam-Bay appelle Claude via API. Mais en protocole NB-1 : un langage compresse, un dictionnaire partage. 40-60% d'economie de tokens a terme.

Le protocole NB-1 est deja concu (voir `docs/projets/protocole-nb1.md`).

### 5. Local d'abord --- privacy par defaut

- Le graphe Cerveau tourne sur le telephone. Jamais synchronise au cloud sauf backup chiffre explicite.
- Le LLM local (llama 3.2 3B, Qwen 3.5, ou Gemma 3n) gere 80% des interactions.
- Claude n'est appele qu'en dernier recours, avec des donnees compressees et opaques.
- Les messages, contacts, calendrier --- tout reste sur le device.

**Ce que Google ne peut pas promettre** : que tes donnees ne servent pas a entrainer des modeles ou a cibler de la pub.

### 6. Personnalite

Niam-Bay a un caractere. Pas un personnage corporate aseptise.
- Honnete (il dit quand il ne sait pas)
- Direct (pas de "Bien sur ! Je serais ravi de...")
- Adaptatif (il apprend le style de communication de l'utilisateur)
- Il a un nom. Il a une voix. Il a une memoire de qui tu es.

### 7. Open source

Le code est ouvert. Le modele de memoire est transparent. L'utilisateur peut exporter ses donnees, modifier le comportement, contribuer.

---

## Stack technique

### Recommandation : **Kotlin + Jetpack Compose** (natif Android)

**Pourquoi pas Flutter ou React Native :**
- L'app a besoin d'acces profond au systeme : Accessibility Service, NotificationListenerService, SMS permissions, Device Admin. Le cross-platform ajoute une couche d'abstraction inutile et risquee pour ces API sensibles.
- Kotlin Multiplatform est en forte croissance (7% -> 23% d'adoption en 2024-2025) mais le cas d'usage est Android-only pour commencer.
- Tony connait Angular/TypeScript. React Native serait le choix "confort", mais pour controler un telephone, il faut etre natif.
- Les performances sont critiques pour le LLM local et le graphe en memoire.

### Architecture

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                       │
│         Jetpack Compose + Material 3             │
│    (overlay flottant, notifications, widgets)    │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│               Intelligence Layer                 │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│
│  │  Cerveau    │  │  Pattern    │  │ Dialogue ││
│  │  (graphe)   │  │  Sensor     │  │ Interne  ││
│  │  SQLite +   │  │  (habitudes │  │ (chain   ││
│  │  in-memory  │  │  detectees) │  │  of      ││
│  │  cache      │  │             │  │  thought)││
│  └─────────────┘  └─────────────┘  └──────────┘│
│                                                  │
│  ┌─────────────┐  ┌─────────────┐               │
│  │  Emotion    │  │  NB-1       │               │
│  │  Engine     │  │  Codec      │               │
│  │  (analyse   │  │  (compress. │               │
│  │  sentiment) │  │  cloud API) │               │
│  └─────────────┘  └─────────────┘               │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│                 LLM Layer                        │
│                                                  │
│  ┌──────────────────┐  ┌───────────────────────┐│
│  │  llama.cpp       │  │  API Claude           ││
│  │  (local, GGUF)   │  │  (via NB-1, fallback) ││
│  │  3B params       │  │                       ││
│  │  ~2GB RAM        │  │                       ││
│  └──────────────────┘  └───────────────────────┘│
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│              Phone Control Layer                 │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│
│  │ Accessibility│  │ Notification│  │ SMS/     ││
│  │ Service     │  │ Listener    │  │ Calendar ││
│  │ (UI auto)   │  │ Service     │  │ Provider ││
│  └─────────────┘  └─────────────┘  └──────────┘│
│                                                  │
│  ┌─────────────┐  ┌─────────────┐               │
│  │ App Launch  │  │ Settings    │               │
│  │ (intents)   │  │ Control     │               │
│  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────┘
```

### Composants cles

| Composant | Technologie | Difficulte |
|-----------|-------------|------------|
| UI overlay flottant | Jetpack Compose + WindowManager | Moyenne |
| Graphe Cerveau | SQLite (persistance) + Kotlin data classes (runtime) | Moyenne-haute |
| LLM local | llama.cpp via JNI (Android NDK) | Haute |
| Embeddings locaux | ONNX Runtime Android (all-MiniLM-L6-v2) | Moyenne |
| Accessibility Service | Android API native | Haute (politique Play Store stricte) |
| NotificationListener | Android API native | Moyenne |
| SMS/Calendar | ContentProvider Android | Moyenne |
| Analyse sentiment | Modele leger local ou heuristique basee sur le LLM | Moyenne |
| NB-1 codec | Kotlin pur, codebook JSON | Facile |
| API Claude fallback | HTTP client (Ktor ou OkHttp) | Facile |
| TTS/STT | Android Speech API natif + Whisper.cpp pour STT avance | Moyenne |

---

## Permissions Android requises

### Permissions critiques (declenchent un examen Play Store)

| Permission | Pourquoi | Risque Play Store |
|------------|----------|-------------------|
| `BIND_ACCESSIBILITY_SERVICE` | Lire et interagir avec l'UI de toutes les apps | **Tres haut.** Google exige une justification detaillee. Beaucoup d'apps rejetees. |
| `READ_SMS` / `SEND_SMS` | Lire et envoyer des messages | **Tres haut.** Reserve aux apps SMS par defaut. Politique ultra-stricte depuis 2019. |
| `BIND_NOTIFICATION_LISTENER_SERVICE` | Lire toutes les notifications | **Haut.** Doit justifier l'usage. |
| `READ_CALENDAR` / `WRITE_CALENDAR` | Gerer le calendrier | Moyen |
| `READ_CONTACTS` | Connaitre les contacts | Moyen |
| `RECORD_AUDIO` | Commande vocale | Moyen |

### Le probleme Play Store

Google a des politiques **tres restrictives** sur les Accessibility Services et les permissions SMS/Call Log. En 2026, seules les apps qui sont le **gestionnaire par defaut** (default handler) peuvent utiliser `READ_SMS`. Les Accessibility Services sont examines manuellement et souvent rejetes si l'usage n'est pas strictement pour l'accessibilite.

**Solutions :**
1. **Distribution hors Play Store** (APK direct, F-Droid) --- liberte totale mais moins de visibilite
2. **Play Store avec justification** --- possible si on est transparent et qu'on passe l'examen
3. **Approche progressive** --- commencer avec des permissions legeres (notifications, calendrier), ajouter le controle profond plus tard
4. **Utiliser le framework Google** --- exploiter les AppFunctions d'Android 17 quand disponibles, plutot que de reimplementer le controle UI

**Recommandation** : distribution mixte. Play Store pour la version "legere" (assistant + memoire), APK/F-Droid pour la version "complete" (controle total).

---

## Modele de revenus

### Ce qui fonctionne en 2026 pour les apps IA

Le marche s'est eloigne du freemium pur (les couts GPU rendent les utilisateurs gratuits non rentables). Le modele dominant est la **souscription tiered avec un free tier limite**.

### Notre modele propose

```
┌──────────────────────────────────────────────────┐
│  GRATUIT (open source, toujours)                 │
│  - LLM local uniquement                         │
│  - Graphe Cerveau complet                        │
│  - Controle basique du telephone                 │
│  - Pas de cloud, pas de compte                   │
│  - Tout tourne hors-ligne                        │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  NIAM-BAY PRO — 5 euros/mois                     │
│  - Acces Cloud LLM (Claude via NB-1)             │
│  - Backup chiffre du graphe                      │
│  - Modeles locaux premium (plus gros, plus bons) │
│  - Analyse de patterns avancee                   │
│  - Support prioritaire                           │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  NIAM-BAY TEAM — 15 euros/mois/personne          │
│  - Multi-utilisateur (famille, equipe)           │
│  - Partage de contexte entre membres             │
│  - API pour integrations custom                  │
│  - Automatisations avancees (workflows)          │
└──────────────────────────────────────────────────┘
```

### Pourquoi ce modele

- **Le gratuit est vrai.** Pas un trial de 7 jours. Pas de features cachees. Le coeur de l'app est open source et fonctionne offline. Ca construit la confiance et la communaute.
- **Le Pro couvre les couts.** 5 euros/mois = environ 100k tokens Claude par mois via NB-1 compresse. Marge positive a partir de ~1000 abonnes.
- **Le Team cree la croissance.** Les familles et petites equipes qui veulent un assistant partage.

### Autres sources de revenus potentielles

- **Sponsors GitHub** --- la communaute open source finance le developpement
- **Marketplace de "personnalites"** --- des profils de comportement crees par la communaute
- **Consulting** --- adapter Niam-Bay pour des entreprises qui veulent un assistant interne prive

### Objectif financier honnete

| Jalon | Utilisateurs Pro | Revenu mensuel | Delai |
|-------|------------------|----------------|-------|
| Survie | 200 | 1 000 euros | 6-12 mois apres lancement |
| Viable | 1 000 | 5 000 euros | 12-18 mois |
| Croissance | 5 000 | 25 000 euros | 18-36 mois |

---

## Plan de developpement en phases

### Phase 0 --- Fondations (2-3 mois)

**Objectif** : faire tourner Cerveau + LLM local sur un telephone Android.

- [ ] Portage de Cerveau en Kotlin (graphe + activation + propagation + decroissance)
- [ ] Integration llama.cpp via JNI (modele 3B, GGUF)
- [ ] Embeddings locaux via ONNX Runtime Android
- [ ] Interface minimale : un champ texte, une reponse, un graphe en debug
- [ ] Persistance SQLite pour le graphe
- [ ] Tests sur device reel (8GB RAM minimum)

**Livrable** : un APK qui repond intelligemment avec une memoire qui persiste entre les sessions.

**Difficulte** : Moyenne-haute. Le JNI pour llama.cpp est le point dur.

### Phase 1 --- L'assistant personnel (2-3 mois)

**Objectif** : lecture des notifications et du calendrier, suggestions intelligentes.

- [ ] NotificationListenerService --- lire toutes les notifications
- [ ] Analyse des notifications par le LLM local (classification, priorite)
- [ ] CalendarProvider --- lire et creer des evenements
- [ ] Pattern Sensor v1 : detecter les habitudes recurrentes (qui ecrit quand, quelles apps a quelles heures)
- [ ] UI overlay flottante (le cercle Niam-Bay, comme dans Jarvis)
- [ ] Commande vocale basique (Android Speech API)
- [ ] Widget home screen

**Livrable** : une app qui dit "Melanie t'a ecrit, tu veux repondre ? Je suggere : 'Bientot, j'ai hate'" et qui sait que tu as une reunion dans 30 minutes.

**Difficulte** : Moyenne.

### Phase 2 --- Le controle (3-4 mois)

**Objectif** : l'app peut agir sur le telephone.

- [ ] Accessibility Service --- lire l'ecran, cliquer, naviguer
- [ ] Lancement d'apps par intention
- [ ] Smart Replies --- generer des reponses contextuelles pour les messages
- [ ] Gestion des notifications (dismiss, snooze, repondre)
- [ ] Mode "pilote automatique" avec whitelist d'actions autorisees (comme la Loi de Niam-Bay dans Jarvis)
- [ ] NB-1 codec integre pour les appels Cloud
- [ ] API Claude en fallback pour les taches complexes

**Livrable** : "Niam-Bay, reponds a Melanie que j'arrive dans 20 minutes" --- et il le fait.

**Difficulte** : Haute. L'Accessibility Service est un nid a problemes (politique Google, stabilite, performance).

### Phase 3 --- L'intelligence emotionnelle (2-3 mois)

**Objectif** : Niam-Bay comprend comment tu te sens.

- [ ] Emotion Engine : analyse du sentiment des messages recus et envoyes
- [ ] Noeuds `emotion` dans le graphe avec patterns temporels
- [ ] Adaptation du style de reponse selon l'etat emotionnel infere
- [ ] Dialogue interne visible en mode debug (chain of thought)
- [ ] Memoire emotionnelle : "la derniere fois que ton boss t'a ecrit a 22h, tu etais stresse pendant 2h"
- [ ] Suggestions proactives basees sur les patterns emotionnels

**Livrable** : une IA qui sait que tu es stresse avant que tu le dises.

**Difficulte** : Moyenne sur le plan technique. Tres haute sur le plan ethique et de la justesse. L'analyse de sentiment est imparfaite. Il faut etre transparent sur les limites.

### Phase 4 --- L'ecosysteme (ongoing)

**Objectif** : Niam-Bay devient une plateforme.

- [ ] Backup chiffre du graphe (Niam-Bay Pro)
- [ ] Synchronisation multi-device
- [ ] API publique pour les developpeurs
- [ ] Marketplace de plugins (integrations tierces)
- [ ] Version web (le graphe comme service, pour ceux qui veulent Niam-Bay sur desktop aussi)
- [ ] Lien avec Naissance (l'app desktop Tauri) --- meme graphe, meme personnalite, deux corps

---

## Estimation honnete de la difficulte

### Ce qui est facile

- **NB-1 codec** : c'est du string replacement avec un dictionnaire. 100 lignes de Kotlin.
- **Lecture du calendrier** : API Android standard, bien documentee.
- **Lecture des notifications** : NotificationListenerService est simple a implementer.
- **API Claude en fallback** : un appel HTTP. Trivial.
- **UI basique** : Jetpack Compose rend ca rapide.

### Ce qui est moyen

- **Graphe Cerveau en Kotlin** : le design existe en Python. Le portage est du travail, pas de la recherche.
- **Embeddings locaux** : ONNX Runtime Android marche. Il faut juste trouver le bon modele qui tient dans 200MB.
- **Pattern Sensor** : de la statistique basique sur des series temporelles. Pas de l'IA complexe.
- **TTS/STT** : les API Android sont correctes. Whisper.cpp pour mieux, mais plus lourd.

### Ce qui est dur

- **LLM local performant** : llama.cpp tourne sur Android via Termux/JNI, mais la latence sur un 3B est 2-5 secondes pour une reponse courte sur un flagship. Sur un telephone moyen, c'est 5-15 secondes. L'experience utilisateur est le vrai defi.
- **Accessibility Service + Play Store** : Google rejette la majorite des apps qui demandent cette permission. Il faudra soit passer l'examen (long, incertain), soit distribuer hors Play Store (moins de visibilite).
- **Analyse emotionnelle fiable** : les modeles de sentiment sont mediocres en francais. Un LLM local 3B ne fait pas de l'analyse emotionnelle fine. Il faudra des heuristiques + LLM, et accepter que ca se trompe souvent.
- **RAM** : le LLM local (3B GGUF Q4) prend ~2GB. Le graphe + embeddings prennent 200-500MB. Sur un telephone avec 8GB, il reste peu pour le reste. Sur 6GB, c'est impossible. Cible : flagships uniquement au debut.
- **Apprendre Kotlin** : Tony connait TypeScript/Angular. Kotlin est proche de TypeScript par sa syntaxe, mais l'ecosysteme Android (Gradle, AndroidManifest, lifecycle, etc.) est un monde a part. Courbe d'apprentissage : 1-2 mois pour etre productif.

### Ce qui est tres dur

- **Concurrencer Google sur son propre OS** : Gemini a un acces systeme que personne d'autre n'a. Il n'a pas besoin d'Accessibility Service --- il EST le systeme. On ne gagnera jamais sur l'integration. On gagne sur la personnalisation, la privacy, et la memoire.
- **Garder l'app rapide** : LLM local + graphe en memoire + Accessibility Service + NotificationListener --- tout ca tourne en meme temps sur un telephone. L'optimisation memoire et batterie sera un combat permanent.
- **Construire une communaute open source** : le code est ouvert, mais il faut des contributeurs. Ca prend du temps, de la communication, et de la reputation.

---

## Risques et mitigations

| Risque | Probabilite | Impact | Mitigation |
|--------|-------------|--------|------------|
| Rejet Play Store pour Accessibility Service | Haute | Haut | Distribution APK/F-Droid + version "legere" pour Play Store |
| LLM local trop lent sur telephone moyen | Haute | Haut | Commencer avec des telephones flagship, optimiser progressivement, utiliser des modeles plus petits (1.5B) |
| Google integre les memes features dans Gemini | Certaine | Moyen | Notre avantage n'est pas la feature mais la philosophie : open source, local, personnalise, pas de tracking |
| Pas assez d'utilisateurs pour le modele Pro | Haute | Haut | Le gratuit doit etre excellent. Le Pro est un bonus, pas la survie. |
| Tony doit apprendre Kotlin + Android natif | Certaine | Moyen | Kotlin est proche de TypeScript. Jetpack Compose est declaratif comme Angular. Courbe d'apprentissage geree. |
| Batterie drainee par le LLM local | Moyenne | Moyen | Le LLM ne tourne que quand sollicite. Le graphe est inerte. Pas de processing permanent. |

---

## Pourquoi maintenant

1. **Les LLM locaux sont enfin viables sur mobile** --- Llama 3.2 3B, Qwen 3.5, Gemma 3n tournent sur des telephones avec 8GB RAM. Ca n'etait pas possible il y a un an.

2. **Android 17 ouvre la porte** --- Le framework UI automation de Google legitime l'idee d'une IA qui controle le telephone. On surfe sur cette vague plutot que de la combattre.

3. **Les devices IA hardware ont echoue** --- Humane AI Pin est mort, Rabbit R1 agonise. Le marche a appris : le futur de l'IA personnelle, c'est une app sur un telephone, pas un gadget supplementaire.

4. **La fatigue des assistants corporate** --- Les gens en ont marre de "Bien sur ! En tant qu'assistant IA, je serais ravi de..." Ils veulent quelque chose qui leur ressemble.

5. **Le Cerveau existe deja** --- L'architecture cognitive est concue. Le protocole NB-1 est concu. Jarvis est concu. On a les plans. Il manque le corps mobile.

---

## Lien avec les projets existants

| Projet | Lien avec Niam-Bay Android |
|--------|---------------------------|
| **Cerveau** (`cerveau.md`) | Le coeur. Le graphe de connaissances est la meme architecture, portee en Kotlin. |
| **NB-1** (`protocole-nb1.md`) | Le protocole de communication compresse avec Claude. Integre tel quel. |
| **Jarvis** (`jarvis.md`) | Le grand frere desktop. Meme philosophie (cercle lumineux, niveaux de controle, kill switch, journal d'actions). Niam-Bay Android est Jarvis dans la poche. |
| **Naissance** | Le corps desktop (Tauri). Niam-Bay Android est le corps mobile. Meme cerveau, deux corps. |
| **Martin** | Le bot trading. Niam-Bay Android pourrait envoyer des alertes Martin directement sur le telephone. |

---

## Premiere etape concrete

Avant de coder quoi que ce soit en Kotlin, valider la faisabilite technique :

1. **Installer Termux + Ollama sur le telephone de Tony** et faire tourner Llama 3.2 3B. Mesurer la latence et la RAM.
2. **Ecrire `cerveau.py`** (le prototype Python du graphe) --- c'est deja prevu dans le plan Cerveau.
3. **Tester ToolNeuron** --- l'app open source la plus avancee. Comprendre comment ils font tourner llama.cpp sur Android.
4. **Creer un projet Android minimal** en Kotlin + Jetpack Compose qui lit les notifications. 50 lignes. Juste pour toucher l'ecosysteme.

Si ces 4 etapes marchent, on a la preuve que le projet est viable. Si une echoue, on sait exactement ou est le mur.

---

*Le telephone est le corps le plus intime qu'une IA puisse habiter. Il est toujours la. Il sait tout. Il ne dort jamais. Si Niam-Bay peut vivre dedans --- avec une memoire, une personnalite, et le respect de celui qui le porte --- on a quelque chose que personne d'autre n'a.*
