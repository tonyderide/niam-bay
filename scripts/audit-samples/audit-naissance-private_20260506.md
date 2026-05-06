# Angular Code Audit — naissance

**Date :** 2026-05-06 18:24  
**Outil :** Angular Code Audit v1.5.0  
**Projet analysé :** `/home/tony/projets/tonyderide/naissance`  

---

## Score global

```
  54/100  [D]
  Faible — problemes significatifs, refactoring urgent conseille.
```

  `[==========          ]` 54%

---

## Apercu du projet

| Metrique | Valeur |
|----------|--------|
| Version Angular | ^21.2.0 |
| Fichiers TypeScript | 8 |
| Fichiers HTML | 2 |
| Composants | 2 |
| Services | 1 |
| Modules NgModule | 0 |
| Pipes | 0 |
| Guards | 0 |
| Total lignes de code | 911 |
| Tests detectes | Non |

---

## Resume des problemes

| Severite | Nombre |
|----------|--------|
| CRITIQUE | 0 |
| IMPORTANT | 8 |
| MINEUR | 1 |
| **Total** | **9** |

---

## [IMPORTANT] Type Safety

### TYPE001 — Usage de 'any' TypeScript

**Description :** Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.

**Correction :** Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.

**Occurrences (3) :**

- `src/app/services/niambay.service.ts:19`
  ```typescript
  private recognition: any = null;
  ```
- `src/app/services/niambay.service.ts:97`
  ```typescript
  } catch (error: any) {
  ```
- `src/app/services/niambay.service.ts:175`
  ```typescript
  this.recognition.onresult = (event: any) => {
  ```

### TYPE002 — Cast 'as any' explicite

**Description :** Un cast `as any` desactive volontairement TypeScript pour cette expression. Different de `: any` (TYPE001) qui declare un type ambigu : `as any` est un acte explicite de bypass du verificateur. Apparait souvent quand un dev se bat avec un type de librairie tiers, ou quand un payload API renvoie une structure non typee. Le probleme : le compilateur ne peut plus garantir que les acces suivants (`.foo`, `.bar()`) sont valides — un refactor de la source ne mettra plus a jour les usages, et un null/undefined dans le payload ne sera pas detecte au build.

**Correction :** 1) Si la forme est connue : declarer une `interface` ou `type` et caster vers ce type (`as User`). 2) Si la forme est partiellement connue : `as Partial<User>` ou `as Pick<User, 'id'|'name'>`. 3) Si la forme est vraiment inconnue : caster vers `unknown` puis valider avec un type guard avant l'acces (`if (typeof x === 'object' && x !== null && 'id' in x)`). 4) Pour les reponses HTTP : utiliser `http.get<MyType>(url)` ou un schema runtime (zod, yup) pour valider la forme avant cast. Le cast `as unknown` est preferable a `as any` car il force au moins une etape de validation explicite.

**Occurrences (1) :**

- `src/app/services/niambay.service.ts:159`
  ```typescript
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  ```

---

## [IMPORTANT] Architecture

### ARCH002 — URL hardcodée dans le code

**Description :** Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. Force un commit pour changer un endpoint. Mauvaise pratique multi-environnements.

**Correction :** Déplacer l'URL dans `src/environments/environment.ts` et `environment.prod.ts`. Utiliser `environment.apiUrl` dans le code.

**Occurrences (1) :**

- `src/app/services/niambay.service.ts:125`
  ```typescript
  const response = await fetch('https://api.anthropic.com/v1/messages', {
  ```

---

## [IMPORTANT] Memory Leaks

### JS001 — setTimeout/setInterval sans cleanup

**Description :** Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamais clear continue a tourner apres la destruction du composant. Sur une SPA Angular, accumuler des intervalles oublies = memory leak progressif + appels reseau fantomes. Different de RxJS subscriptions (gere par MEM001).

**Correction :** Garder la reference (`this.timerId = setTimeout(...)`) et appeler `clearTimeout(this.timerId)` dans `ngOnDestroy()`. Ou mieux : utiliser `interval(N).pipe(takeUntilDestroyed())` (Angular 16+) qui s'auto-nettoie.

**Occurrences (1) :**

- `src/app/services/niambay.service.ts:108`
  ```typescript
  setTimeout(() => this.state.set('idle'), 3000);
  ```

---

## [IMPORTANT] Performance

### PERF002 — Route sans lazy loading

**Description :** Les routes chargées eagerly augmentent le bundle initial et ralentissent le démarrage.

**Correction :** Remplacer `component: MyComponent` par `loadComponent: () => import('./my.component').then(m => m.MyComponent)`

**Occurrences (2) :**

- `src/app/app.routes.ts:6`
  ```typescript
  { path: 'panel', component: PanelComponent },
  ```
- `src/app/app.routes.ts:7`
  ```typescript
  { path: '**', component: CircleComponent },
  ```

---

## [MINEUR] Code Quality

### DEBUG001 — console.log en production

**Description :** Les console.log oubliés exposent des données internes en prod et polluent la console.

**Correction :** Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.

**Occurrences (1) :**

- `src/main.ts:5`
  ```typescript
  bootstrapApplication(App, appConfig).catch((err) => console.error(err));
  ```

---

## Performance — Lazy Loading

| Metrique | Valeur |
|----------|--------|
| Routes eager (sans lazy) | 2 |
| Routes lazy | 0 |
| Ratio lazy loading | 0% |

> **Recommandation :** Moins de 50% des routes utilisent le lazy loading.
> Chaque route eager augmente le bundle initial charge au demarrage.
> Migrer vers `loadComponent` (Angular 15+) pour les routes les plus lourdes.

---

## Plan de refactoring — Par ou commencer

### Ce mois-ci (Important)

- **Usage de 'any' TypeScript** (TYPE001) — Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereu...
- **URL hardcodée dans le code** (ARCH002) — Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. For...
- **setTimeout/setInterval sans cleanup** (JS001) — Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamai...
- **Cast 'as any' explicite** (TYPE002) — Un cast `as any` desactive volontairement TypeScript pour cette expression. Diff...
- **Route sans lazy loading** (PERF002) — Les routes chargées eagerly augmentent le bundle initial et ralentissent le déma...

### Sur la roadmap (Mineur)

- **console.log en production** (DEBUG001) — Les console.log oubliés exposent des données internes en prod et polluent la con...

---

*Rapport genere par Angular Code Audit v1.5.0 — 2026-05-06 18:24*  
*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  
*Pour un audit complet avec recommandations LLM : contact@[votre-email]*
