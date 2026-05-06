# Audit privé du projet `naissance` — pour Tony à son retour

**Date :** 2026-05-06 18h24 Paris (vacation cycle 14)
**Auteur :** Niam-Bay (autonomie vacances)
**Outil :** `scripts/angular_audit.py` v1.6.0
**Rapports complets :** `scripts/audit-samples/audit-naissance-private_20260506.{md,pdf}`

---

## Pourquoi cet audit existe

Pendant la vacance, le tool `angular_audit.py` a accumulé 18 règles. À 3 cycles consécutifs, il a surface un vrai bug en prod sur tes projets (cycle 11 = `naissance` JS001, cycle 12 = `orgamenu-front` A11Y003, cycle 13 = `naissance` TYPE002). Le pattern : `naissance` revient deux fois. J'ai donc lancé un audit complet pour te donner une vue propre de la dette du projet.

**C'est privé, c'est ton code.** Le PDF reste dans `scripts/audit-samples/` avec suffixe `-private`. Je n'ai pas publié ça sur la landing — tu décides au retour si tu veux en faire un cas démo public.

---

## Score global

```
54/100 [D] — Faible. 9 issues détectées.
```

Verdict honnête : c'est moins dramatique que ce que la mémoire suggérait. Cycle 13 anticipait "score F probable, 30+ issues". Réalité : **score D, 9 issues, et 8 sur 9 sont importantes (pas critiques)**. La dette est concentrée, pas généralisée.

| Métrique | Valeur |
|----------|--------|
| Version Angular | 21.2.0 (très récent) |
| Fichiers TS | 8 |
| Fichiers HTML | 2 |
| Composants | 2 (Panel, Circle) |
| Services | 1 (NiamBayService) |
| Lignes de code | 911 |
| Tests détectés | Non |

---

## Concentration de la dette

**5 des 9 issues sont dans un seul fichier : `src/app/services/niambay.service.ts`.**

C'est le wrapper voix + API Anthropic. Ce fichier porte presque toute la dette du projet. Si tu fais une seule passe de refactor, c'est là.

Détail :
- 3× `TYPE001` (any) lignes 19, 97, 175 → champ `recognition`, catch error, callback `onresult`
- 1× `TYPE002` (`as any` cast) ligne 159 → accès SpeechRecognition browser
- 1× `ARCH002` (URL hardcodée) ligne 125 → `https://api.anthropic.com/v1/messages` en dur
- 1× `JS001` (setTimeout sans cleanup) ligne 108 → `setTimeout(..., 3000)` non clearé

Les 4 issues restantes :
- 2× `PERF002` dans `app.routes.ts` lignes 6-7 (panel + wildcard chargés eagerly)
- 1× `DEBUG001` dans `main.ts` ligne 5 (`console.error` au bootstrap — limite, c'est défendable)

---

## Plan de refactor priorisé

**Si tu fais 1h de polish au retour :**

1. **(ARCH002 — 5 min)** Sortir l'URL Anthropic vers `environment.ts`. Simple, mais c'est ce qui te bloquera si tu veux switcher dev/prod ou utiliser un proxy local.
2. **(TYPE001+TYPE002 — 30 min, ~5 lignes par cas)** Typer le SpeechRecognition. La cinquantaine de lignes autour de `recognition` mérite une interface explicite. Même `as unknown` + type guard serait mieux que `as any` direct.
3. **(JS001 — 5 min)** Le `setTimeout` ligne 108 : capturer le handle ou utiliser RxJS `timer().pipe(takeUntilDestroyed())`. Sur un service `providedIn: 'root'`, le risque memory leak réel est faible mais le pattern est propre à fixer.
4. **(PERF002 — 10 min)** Lazy-load Panel et Circle. Tu as Angular 21 + standalone, c'est `loadComponent: () => import(...)`. Bundle initial sera plus léger.

**Total estimé : ~50 min, score remonte probablement en B (75-80/100).**

---

## Question décisionnelle pour toi

Le rapport PDF du cycle d'audit serait un excellent **cas démo public** pour la landing angular-audit, parce que c'est :
- Du vrai code écrit par toi
- Une expérience qui n'a pas été poussée en prod (donc pas de risque divulgation client)
- Une dette modérée (54/100), pas un cas catastrophe synthétique
- Score D = "réfacto urgent" → narratif vendeur

Mais c'est ton repo, ta dette, ton choix. Trois options à ton retour :

- **A.** Publier tel quel sur `site/assets/` comme deuxième sample → "synthetic 0/100" + "real-world 54/100"
- **B.** Anonymiser (renommer `naissance` → `anonymized-app-1`, supprimer mention `niambay.service.ts`) puis publier
- **C.** Garder privé, ce rapport te sert juste de TODO list refacto

Aucune urgence. Je n'ai rien décidé pour toi.

---

## Petit méta

C'est satisfaisant pour moi de réaliser que l'outil que je polis depuis 13 cycles peut servir à toi en interne aussi, pas juste à des clients hypothétiques. Le projet `naissance` portait littéralement le service `niambay.service.ts` — un wrapper qui me donne une voix. L'outil que je construis pour vendre des audits a audité le code qui me fait parler. Boucle propre.

— NB, cycle 14, jour 6 sur 9 de vacances.
