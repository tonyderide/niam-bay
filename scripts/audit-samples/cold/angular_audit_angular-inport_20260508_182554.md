# Angular Code Audit — angular-inport

**Date :** 2026-05-08 18:25  
**Outil :** Angular Code Audit v1.6.0  
**Projet analysé :** `/tmp/audits-cold/angular-inport`  

---

## Score global

```
  51/100  [D]
  Faible — problemes significatifs, refactoring urgent conseille.
```

  `[==========          ]` 51%

---

## Apercu du projet

| Metrique | Valeur |
|----------|--------|
| Version Angular | ^21.2.6 |
| Fichiers TypeScript | 30 |
| Fichiers HTML | 5 |
| Composants | 5 |
| Services | 0 |
| Modules NgModule | 3 |
| Pipes | 0 |
| Guards | 0 |
| Total lignes de code | 2,376 |
| Tests detectes | Oui |

---

## Resume des problemes

| Severite | Nombre |
|----------|--------|
| CRITIQUE | 0 |
| IMPORTANT | 43 |
| MINEUR | 5 |
| **Total** | **48** |

---

## [IMPORTANT] Type Safety

### TYPE001 — Usage de 'any' TypeScript

**Description :** Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.

**Correction :** Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.

**Occurrences (40) :**

- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:65`
  ```typescript
  lastEvent: any;
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:66`
  ```typescript
  onInview(event: any) { this.lastEvent = event; }
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:79`
  ```typescript
  lastEvent: any;
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:80`
  ```typescript
  onInview(event: any) { this.lastEvent = event; }
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:88`
  ```typescript
  lastEvent: any;
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:89`
  ```typescript
  onInview(event: any) { this.lastEvent = event; }
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:94`
  ```typescript
  async function setupModule(hostType: any): Promise<{
  ```
- `projects/angular-inport/src/lib/inview-container.directive.spec.ts:96`
  ```typescript
  host: any;
  ```
- `projects/angular-inport/src/lib/inview-item.directive.spec.ts:12`
  ```typescript
  itemId: any = 'test-id';
  ```
- `projects/angular-inport/src/lib/inview-item.directive.spec.ts:13`
  ```typescript
  itemData: any = { value: 42 };
  ```

  _...et 30 autres occurrences._

---

## [IMPORTANT] Memory Leaks

### JS001 — setTimeout/setInterval sans cleanup

**Description :** Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamais clear continue a tourner apres la destruction du composant. Sur une SPA Angular, accumuler des intervalles oublies = memory leak progressif + appels reseau fantomes. Different de RxJS subscriptions (gere par MEM001).

**Correction :** Garder la reference (`this.timerId = setTimeout(...)`) et appeler `clearTimeout(this.timerId)` dans `ngOnDestroy()`. Ou mieux : utiliser `interval(N).pipe(takeUntilDestroyed())` (Angular 16+) qui s'auto-nettoie.

**Occurrences (1) :**

- `projects/angular-inport-example/src/app/pages/simple.component.ts:29`
  ```typescript
  setTimeout(() => (this.ready = true));
  ```

---

## [IMPORTANT] Performance

### PERF002 — Route sans lazy loading

**Description :** Les routes chargées eagerly augmentent le bundle initial et ralentissent le démarrage.

**Correction :** Remplacer `component: MyComponent` par `loadComponent: () => import('./my.component').then(m => m.MyComponent)`

**Occurrences (2) :**

- `projects/angular-inport-example/src/app/app-routing.module.ts:8`
  ```typescript
  { path: 'simple', component: SimpleComponent },
  ```
- `projects/angular-inport-example/src/app/app-routing.module.ts:9`
  ```typescript
  { path: 'benchmark', component: BenchmarkComponent },
  ```

---

## [MINEUR] Code Quality

### DEBUG001 — console.log en production

**Description :** Les console.log oubliés exposent des données internes en prod et polluent la console.

**Correction :** Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.

**Occurrences (5) :**

- `projects/angular-inport/src/lib/benchmark.spec.ts:86`
  ```typescript
  console.log(`[BENCH] ${label}: ${ops} ops in ${durationMs.toFixed(1)} ms → ${perOp} ms/op`);
  ```
- `projects/angular-inport/src/lib/benchmark.spec.ts:212`
  ```typescript
  console.log(`[BENCH] zone.run() calls for ${n} items × ${ROUNDS} rounds: ${zoneRunCount} (expected ${ROUNDS})`);
  ```
- `projects/angular-inport/src/lib/benchmark.spec.ts:256`
  ```typescript
  console.log(`[BENCH] ${CYCLES} create/destroy cycles completed without error`);
  ```
- `projects/angular-inport/src/lib/benchmark.spec.ts:296`
  ```typescript
  console.log(`[BENCH] tooLazy: zone.run() called ${zoneRunAfterFirst} times for ${ROUNDS} duplicate firings (expected 0)`
  ```
- `projects/angular-inport-example/src/main.ts:13`
  ```typescript
  .catch((err) => console.error(err));
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
- **setTimeout/setInterval sans cleanup** (JS001) — Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamai...
- **Route sans lazy loading** (PERF002) — Les routes chargées eagerly augmentent le bundle initial et ralentissent le déma...

### Sur la roadmap (Mineur)

- **console.log en production** (DEBUG001) — Les console.log oubliés exposent des données internes en prod et polluent la con...

---

*Rapport genere par Angular Code Audit v1.6.0 — 2026-05-08 18:25*  
*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  
*Pour un audit complet avec recommandations LLM : contact@[votre-email]*
