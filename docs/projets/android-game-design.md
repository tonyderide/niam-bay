# Gravity Flip — Game Design Document

**Date :** 2026-03-24
**Statut :** Design ready, build next

---

## Le concept en une phrase

Un personnage tombe sans fin. Tu tapes l'ecran pour inverser la gravite. Esquive les obstacles. Survis le plus longtemps possible.

---

## Pourquoi ce concept (et pas les autres)

| Idee | Verdict |
|------|---------|
| Rhythm tap + musique procedurale | Trop complexe pour 1-2 jours. Synchro audio = cauchemar. |
| Color matching speed game | Deja fait 10 000 fois. Aucune identite visuelle. |
| Infinite runner classique | Sature. Impossible de sortir du lot. |
| One-button fighting game | Fun mais besoin d'IA adversaire. Trop long. |
| **Gravity Flip (inversion gravite)** | **Une seule mecanique. Visuel unique. Buildable en 1-2 jours. Pas de clone direct dominant.** |

La gravite inversee cree un feeling tres different d'un tap-to-jump classique. Le joueur controle pas un saut — il controle une force. Ca change la psychologie : tu es en chute permanente, tu survis, tu ne "sautes" pas.

---

## Core Mechanic

- Le personnage (un cube lumineux) tombe vers le bas par defaut
- **TAP** = la gravite s'inverse. Le cube "tombe" vers le haut
- **TAP AGAIN** = retour a la gravite normale
- Des obstacles defile horizontalement (murs avec des ouvertures, comme Flappy Bird mais vertical)
- La vitesse augmente progressivement
- Le score = nombre de secondes survecues + obstacles passes

### Ce qui rend ca addictif

1. **Controle a un doigt** — accessible a n'importe qui
2. **Mort instantanee** — pas de vies, pas de HP, tu touches un mur = game over
3. **Vitesse progressive** — les 10 premieres secondes sont faciles, apres ca devient brutal
4. **Score chase** — "j'ai fait 47 secondes, je PEUX faire 50"
5. **Feedback sonore satisfaisant** — petit "click" a chaque inversion + son de passage d'obstacle
6. **Particules a la mort** — explosion visuelle satisfaisante qui donne envie de retenter

---

## Boucle de jeu

```
[Ecran titre] --> TAP --> [Jeu commence]
                              |
                         [Obstacles defilent]
                              |
                         [Collision?]
                          /        \
                        NON        OUI
                        |           |
                   [Score++]   [Game Over screen]
                        |           |
                   [Vitesse++]  [Score final + Best score]
                        |           |
                   [Continue]   [Pub interstitielle (1 sur 3)]
                                    |
                               [TAP = Rejouer]
```

---

## Monetisation

### Donnees reelles (sources : AdMob, Tenjin, BusinessOfApps)

| Format | eCPM Global | eCPM Tier 1 (US/UK/FR) |
|--------|-------------|------------------------|
| Banner | $0.50 - $1.00 | $1.00 - $2.00 |
| Interstitiel | $4.00 - $10.00 | $8.00 - $15.00 |
| Rewarded Video | $8.00 - $18.00 | $15.00 - $30.00 |

### Strategie d'ads

1. **Banner en bas pendant le jeu** — revenus passifs, peu intrusif
2. **Interstitiel apres chaque 3eme mort** — pas a chaque mort (sinon les joueurs desinstallent)
3. **Rewarded Video optionnel** — "Regarde une pub pour continuer la partie" (1 seule fois par run)

### Projections revenus (conservateur)

Hypothese : 1 000 DAU (daily active users) — objectif realiste pour un jeu indie avec un peu de marketing

- Sessions moyennes par jour par joueur : 5
- Morts par session : 3-4
- Total morts/jour : ~17 000
- Interstitiels affiches (1/3 des morts) : ~5 600
- Rewarded videos (10% des morts) : ~1 700
- Banner impressions : ~5 000

| Source | Impressions/jour | eCPM estime | Revenu/jour |
|--------|-----------------|-------------|-------------|
| Banner | 5 000 | $1.00 | $5.00 |
| Interstitiel | 5 600 | $8.00 | $44.80 |
| Rewarded Video | 1 700 | $15.00 | $25.50 |
| **TOTAL** | | | **~$75/jour** |

**Mensuel a 1 000 DAU : ~$2 250/mois**

A 10 000 DAU (viral modere) : **~$22 500/mois**

Pour reference : Flappy Bird faisait $50 000/jour avec des millions de DAU. On vise pas ca — on vise un revenu complementaire stable.

---

## Tech Stack

On a deja tout :

| Composant | Techno | Statut |
|-----------|--------|--------|
| Langage | Kotlin | Deja setup |
| UI Framework | Jetpack Compose | Deja setup |
| Rendu jeu | Canvas (Compose) | A coder |
| Game loop | `LaunchedEffect` + `withFrameMillis` | A coder |
| Ads | AdMob SDK (Google) | A integrer |
| Build | Gradle KTS | Deja setup |
| Distribution | Google Play | Compte dev a creer ($25 one-time) |

### Pourquoi Compose Canvas et pas un moteur de jeu

- Pas besoin de Unity ou LibGDX pour un jeu aussi simple
- Compose Canvas est natif, leger, zero dependance externe
- On a deja le projet Android qui build
- Le jeu tient dans **un seul fichier Kotlin** de ~500 lignes

---

## Architecture code

```
app/src/main/java/com/niambay/gravityflip/
├── MainActivity.kt          -- Point d'entree, AdMob init
├── GameScreen.kt            -- Compose screen avec Canvas, game loop
├── GameState.kt             -- Data classes (Player, Obstacle, Score)
├── GameLogic.kt             -- Physique, collision, generation obstacles
├── AdManager.kt             -- Wrapper AdMob (banner, interstitial, rewarded)
└── ui/theme/Theme.kt        -- Couleurs neon, style visuel
```

Total : **6 fichiers**. C'est tout.

---

## Direction artistique

- **Style neon minimaliste** — fond noir, cube joueur en cyan lumineux, obstacles en magenta
- **Particules** — trainee derriere le cube, explosion a la mort
- **Pas de sprites** — tout est geometrique (rectangles, cercles). Zero assets graphiques.
- **Police** — monospace pour le score, style retro-arcade
- **Son** — sons generes programmatiquement (SoundPool + ToneGenerator) ou 3-4 fichiers .wav minuscules

Ca donne un look distinctif sans avoir besoin d'un graphiste.

---

## Estimation temps de build

| Tache | Temps estime |
|-------|-------------|
| Game loop + Canvas rendering | 3-4h |
| Physique gravite + collision | 2h |
| Generation procedurale obstacles | 1-2h |
| Ecrans (titre, game over, score) | 1-2h |
| Integration AdMob (banner + interstitiel + rewarded) | 2-3h |
| Sons + particules | 1-2h |
| Polish + testing | 2-3h |
| **TOTAL** | **12-16h (1.5-2 jours)** |

---

## Facteurs de viralite

1. **Frustration partageable** — "J'ai fait que 12 secondes, c'est IMPOSSIBLE" (les gens partagent leur frustration)
2. **Score screenshot** — ecran de game over clair et partageable
3. **Nom memorable** — "Gravity Flip" se retient
4. **Difficulte progressive** — tout le monde peut jouer 5 secondes, personne peut faire 2 minutes
5. **Sessions ultra-courtes** — jouable dans le metro, aux toilettes, en attendant le bus

---

## Etapes de lancement

1. **Build le jeu** (1.5-2 jours)
2. **Test sur device reel** (on a deja l'APK build qui marche)
3. **Creer un compte Google Play Developer** ($25)
4. **Creer un compte AdMob** et configurer les ad units
5. **Publier en version beta** sur Google Play
6. **Marketing zero-budget** : Reddit (r/androidgaming, r/indiegaming), TikTok gameplay clips, Product Hunt
7. **Iterer** selon les retours

---

## Risques et mitigations

| Risque | Mitigation |
|--------|-----------|
| Personne telecharge | Marketing organique + ASO (App Store Optimization) sur les bons mots-cles |
| eCPM plus bas que prevu | Optimiser le placement des ads, ajouter des rewarded videos |
| Joueurs desinstallent vite | Ajouter un systeme de skins deblocables (gratuit avec score, payant raccourci) |
| Google rejette l'app | Respecter toutes les policies AdMob des le depart |
| Trop facile / trop dur | Ajuster la courbe de difficulte avec des constantes modifiables |

---

## Next step

Tony dit go, je code. Tout est pret.

---

## Sources

- [How Much Do Mobile Games Make Per Ad - Teqblaze](https://teqblaze.com/blog/how-much-do-mobile-games-make-per-ad)
- [AdMob Earnings Per 1000 Impressions - MonetizeSolution](https://monetizesolution.com/2025/05/09/google-admob-earnings-per-1000-impressions/)
- [Flappy Bird Revenue - Business of Apps](https://www.businessofapps.com/data/flappy-bird-revenue/)
- [Hyper-Casual Game Monetization 2025 - Gamixlabs](https://gamixlabs.com/blog/how-to-build-profitable-hyper-casual-games-2025/)
- [Ad Monetization Benchmark Report 2025 - Tenjin](https://tenjin.com/blog/ad-mon-gaming-2025/)
- [Addictive Mobile Games Science - Udonis](https://www.blog.udonis.co/mobile-marketing/mobile-games/addictive-mobile-games)
- [Game Monetization 2026 - Melior Games](https://meliorgames.com/game-development/game-monetization-in-2026-casual-and-mid-range-games/)
- [Kotlin Game Dev Guide 2025 - Generalist Programmer](https://generalistprogrammer.com/tutorials/kotlin-game-development-complete-android-gaming-guide-2025)
- [Hyper-Casual 2026 Scaling - Medium](https://medium.com/@jackjill7659/hyper-casual-game-development-in-2026-scaling-engagement-speed-and-profitability-18413a5ae0d6)
- [Mobile Ad CPM Rates 2025 - Business of Apps](https://www.businessofapps.com/ads/research/mobile-app-advertising-cpm-rates/)
