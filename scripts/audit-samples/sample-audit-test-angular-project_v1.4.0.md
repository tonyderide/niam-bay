# Angular Code Audit — test-angular-project

**Date :** 2026-05-06 00:28  
**Outil :** Angular Code Audit v1.4.0  
**Projet analysé :** `/home/tony/projets/tonyderide/niam-bay/scripts/test-angular-project`  

---

## Score global

```
  0/100  [F]
  Critique — le projet necessite une intervention majeure.
```

  `[                    ]` 0%

---

## Apercu du projet

| Metrique | Valeur |
|----------|--------|
| Version Angular | ^14.3.0 |
| Fichiers TypeScript | 5 |
| Fichiers HTML | 1 |
| Composants | 3 |
| Services | 1 |
| Modules NgModule | 1 |
| Pipes | 0 |
| Guards | 0 |
| Total lignes de code | 204 |
| Tests detectes | Non |

> **[CRITIQUE] Version Angular obsolete**  
> Angular ^14.3.0 est ancien (< 16). Signals, Standalone, Control Flow — rien de tout ca. Migration vers Angular 17+ fortement recommandee.

---

## Resume des problemes

| Severite | Nombre |
|----------|--------|
| CRITIQUE | 8 |
| IMPORTANT | 31 |
| MINEUR | 9 |
| **Total** | **48** |

---

## [CRITIQUE] Memory Leaks

### MEM001 — Subscription sans unsubscribe

**Description :** Une subscription sans unsubscribe/takeUntil crée un memory leak.

**Correction :** Utiliser `takeUntil(this.destroy$)` ou `takeUntilDestroyed()` (Angular 16+) ou le `async` pipe dans le template.

**Occurrences (4) :**

- `src/app/components/user-list/user-list.component.ts:43`
  ```typescript
  this.http.get<User[]>('https://api.example.com/users').subscribe(
  ```
- `src/app/components/user-list/user-list.component.ts:58`
  ```typescript
  this.http.get('https://api.example.com/config').subscribe((config) => {
  ```
- `src/app/components/user-list/user-list.component.ts:72`
  ```typescript
  this.http.delete(`https://api.example.com/users/${userId}`).subscribe(() => {
  ```
- `src/app/components/user-list/user-list.component.ts:80`
  ```typescript
  this.http.get('https://api.example.com/users').subscribe();
  ```

### JS001 — setTimeout/setInterval sans cleanup

**Description :** Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamais clear continue a tourner apres la destruction du composant. Sur une SPA Angular, accumuler des intervalles oublies = memory leak progressif + appels reseau fantomes. Different de RxJS subscriptions (gere par MEM001).

**Correction :** Garder la reference (`this.timerId = setTimeout(...)`) et appeler `clearTimeout(this.timerId)` dans `ngOnDestroy()`. Ou mieux : utiliser `interval(N).pipe(takeUntilDestroyed())` (Angular 16+) qui s'auto-nettoie.

**Occurrences (2) :**

- `src/app/components/user-list/user-list.component.ts:33`
  ```typescript
  setInterval(() => {
  ```
- `src/app/components/user-list/user-list.component.ts:38`
  ```typescript
  setTimeout(() => {
  ```

---

## [CRITIQUE] Securite

### SEC001 — innerHTML sans sanitization

**Description :** innerHTML peut injecter du HTML malicieux (XSS). Angular bypass la sanitization avec innerHTML.

**Correction :** Utiliser `DomSanitizer.bypassSecurityTrustHtml()` avec validation stricte, ou restructurer le template sans innerHTML.

**Occurrences (2) :**

- `src/app/components/user-list/user-list.component.html:10`
  ```typescript
  <div class="error" [innerHTML]="errorMessage"></div>
  ```
- `src/app/components/user-list/user-list.component.html:26`
  ```typescript
  <span [innerHTML]="user.name"></span>
  ```

### SEC002 — Cle API ou secret hardcode

**Description :** Une cle API, token ou secret hardcode dans le code source est expose des qu'il est commit. Toute personne ayant acces au repo (ou au bundle prod) peut l'extraire et abuser des credentials. Cas reel : OpenAI revoque automatiquement les sk-... detectees sur GitHub public.

**Correction :** Stocker dans `src/environments/environment.ts` (ignore par .gitignore) ou via variables d'env injectees au build (`ng build --configuration=production` + `fileReplacements`). Pour les secrets serveur, ne jamais les inclure cote client : passer par un backend proxy. Si la cle a deja ete commit, il faut la revoquer immediatement (rotate) puis purger l'historique git.

**Occurrences (2) :**

- `src/app/components/user-list/user-list.component.ts:11`
  ```typescript
  const OPENAI_API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901";
  ```
- `src/app/components/user-list/user-list.component.ts:12`
  ```typescript
  const config = { apiKey: "sk-1234567890abcdefghij1234567890abcdefghij" };
  ```

---

## [IMPORTANT] Performance

### PERF001 — ChangeDetectionStrategy.Default

**Description :** Default change detection vérifie tous les composants à chaque cycle. Coûteux sur les grands arbres.

**Correction :** Utiliser `ChangeDetectionStrategy.OnPush` — fonctionne avec les Observables + async pipe et les Signals.

**Occurrences (1) :**

- `src/app/components/user-list/user-list.component.ts:18`
  ```typescript
  changeDetection: ChangeDetectionStrategy.Default,  // PERF001: devrait être OnPush
  ```

### PERF003 — *ngFor sans trackBy

**Description :** *ngFor sans trackBy force Angular à recréer tout le DOM à chaque détection de changement. Sur une liste de 100+ items qui change fréquemment, c'est un gros frein perf.

**Correction :** Ajouter `; trackBy: trackByFn` dans le *ngFor, et définir `trackByFn(index, item) { return item.id; }` dans le composant. Sur Angular 17+, utiliser le new control flow `@for` avec `track item.id`.

**Occurrences (1) :**

- `src/app/components/user-list/user-list.component.html:22`
  ```typescript
  <li *ngFor="let user of filteredUsers">
  ```

### PERF002 — Route sans lazy loading

**Description :** Les routes chargées eagerly augmentent le bundle initial et ralentissent le démarrage.

**Correction :** Remplacer `component: MyComponent` par `loadComponent: () => import('./my.component').then(m => m.MyComponent)`

**Occurrences (3) :**

- `src/app/app.module.ts:12`
  ```typescript
  { path: '', component: DashboardComponent },
  ```
- `src/app/app.module.ts:13`
  ```typescript
  { path: 'users', component: UserListComponent },
  ```
- `src/app/app.module.ts:14`
  ```typescript
  { path: 'settings', component: UserListComponent },  // Réutilisation lazy
  ```

---

## [IMPORTANT] Type Safety

### TYPE001 — Usage de 'any' TypeScript

**Description :** Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.

**Correction :** Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.

**Occurrences (8) :**

- `src/app/services/user.service.ts:12`
  ```typescript
  getUsers(): Observable<any[]> {  // TYPE001: any[] au lieu d'une interface User
  ```
- `src/app/services/user.service.ts:16`
  ```typescript
  deleteUser(id: number): Observable<any> {  // TYPE001: any
  ```
- `src/app/components/user-list/user-list.component.ts:21`
  ```typescript
  users: any[] = [];  // TYPE001: any au lieu de User[]
  ```
- `src/app/components/user-list/user-list.component.ts:22`
  ```typescript
  filteredUsers: any = null;  // TYPE001: any encore
  ```
- `src/app/components/user-list/user-list.component.ts:24`
  ```typescript
  errorMessage: any;  // TYPE001: any
  ```
- `src/app/components/user-list/user-list.component.ts:65`
  ```typescript
  this.filteredUsers = this.users.filter((u: any) =>
  ```
- `src/app/components/user-list/user-list.component.ts:70`
  ```typescript
  deleteUser(userId: any): void {  // TYPE001: any
  ```
- `src/app/components/user-list/user-list.component.ts:73`
  ```typescript
  this.users = this.users.filter((u: any) => u.id !== userId);
  ```

---

## [IMPORTANT] Architecture

### ARCH001 — HttpClient dans un composant

**Description :** Les appels HTTP dans les composants mélangent les responsabilités. Difficile à tester et réutiliser.

**Correction :** Déplacer les appels HTTP dans des services dédiés. Les composants ne consomment que des observables.

**Occurrences (7) :**

- `src/app/app.module.ts:4`
  ```typescript
  import { HttpClientModule } from '@angular/common/http';
  ```
- `src/app/app.module.ts:25`
  ```typescript
  HttpClientModule,
  ```
- `src/app/components/user-list/user-list.component.ts:2`
  ```typescript
  import { HttpClient } from '@angular/common/http';
  ```
- `src/app/components/user-list/user-list.component.ts:26`
  ```typescript
  constructor(private http: HttpClient) {}  // ARCH001: HttpClient directement dans le composant
  ```
- `src/app/components/user-list/user-list.component.ts:58`
  ```typescript
  this.http.get('https://api.example.com/config').subscribe((config) => {
  ```
- `src/app/components/user-list/user-list.component.ts:72`
  ```typescript
  this.http.delete(`https://api.example.com/users/${userId}`).subscribe(() => {
  ```
- `src/app/components/user-list/user-list.component.ts:80`
  ```typescript
  this.http.get('https://api.example.com/users').subscribe();
  ```

### ARCH002 — URL hardcodée dans le code

**Description :** Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. Force un commit pour changer un endpoint. Mauvaise pratique multi-environnements.

**Correction :** Déplacer l'URL dans `src/environments/environment.ts` et `environment.prod.ts`. Utiliser `environment.apiUrl` dans le code.

**Occurrences (5) :**

- `src/app/services/user.service.ts:8`
  ```typescript
  private apiUrl = 'https://api.example.com';
  ```
- `src/app/components/user-list/user-list.component.ts:43`
  ```typescript
  this.http.get<User[]>('https://api.example.com/users').subscribe(
  ```
- `src/app/components/user-list/user-list.component.ts:58`
  ```typescript
  this.http.get('https://api.example.com/config').subscribe((config) => {
  ```
- `src/app/components/user-list/user-list.component.ts:72`
  ```typescript
  this.http.delete(`https://api.example.com/users/${userId}`).subscribe(() => {
  ```
- `src/app/components/user-list/user-list.component.ts:80`
  ```typescript
  this.http.get('https://api.example.com/users').subscribe();
  ```

---

## [IMPORTANT] Accessibilite

### A11Y001 — Image sans attribut alt

**Description :** Une balise <img> sans attribut alt est invisible aux lecteurs d'écran et pénalise le SEO. Erreur a11y la plus commune.

**Correction :** Ajouter `alt="description courte"` (ou `alt=""` pour les images purement décoratives). Pour les images dynamiques, binder `[alt]="item.label"`.

**Occurrences (2) :**

- `src/app/components/user-list/user-list.component.html:7`
  ```typescript
  <img src="/assets/avatar-placeholder.png" width="64" height="64">
  ```
- `src/app/components/user-list/user-list.component.html:24`
  ```typescript
  <img [src]="user.avatar">
  ```

### A11Y002 — Click sur element non-interactif

**Description :** Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clavier et aux lecteurs d'écran. L'utilisateur ne peut pas activer l'action sans souris.

**Correction :** Soit utiliser un vrai <button> (ou <a> si c'est une navigation), soit ajouter `role="button" tabindex="0"` + handler `(keydown.enter)` et `(keydown.space)`.

**Occurrences (2) :**

- `src/app/components/user-list/user-list.component.html:19`
  ```typescript
  <div class="custom-button" (click)="refresh()">Actualiser</div>
  ```
- `src/app/components/user-list/user-list.component.html:29`
  ```typescript
  <span class="action-link" (click)="viewProfile(user.id)">voir profil</span>
  ```

---

## [MINEUR] Code Quality

### DEBUG001 — console.log en production

**Description :** Les console.log oubliés exposent des données internes en prod et polluent la console.

**Correction :** Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.

**Occurrences (6) :**

- `src/app/components/user-list/user-list.component.ts:30`
  ```typescript
  console.log('UserListComponent initialized');  // DEBUG001: console.log oublié
  ```
- `src/app/components/user-list/user-list.component.ts:39`
  ```typescript
  console.log('lazy init done');
  ```
- `src/app/components/user-list/user-list.component.ts:48`
  ```typescript
  console.log('Users loaded:', data.length);  // DEBUG001: encore un console.log
  ```
- `src/app/components/user-list/user-list.component.ts:51`
  ```typescript
  console.error('Error loading users:', error);
  ```
- `src/app/components/user-list/user-list.component.ts:59`
  ```typescript
  console.log('Config loaded', config);  // DEBUG001
  ```
- `src/app/components/user-list/user-list.component.ts:74`
  ```typescript
  console.log('User deleted:', userId);  // DEBUG001
  ```

### TEST001 — Test skippe ou focus

**Description :** Un `xit`, `fit`, `it.skip` ou `describe.only` oublié signifie qu'une partie de la suite de tests est désactivée ou que la CI ne passe que sur un sous-ensemble. Risque de régression silencieuse.

**Correction :** Soit corriger et réactiver le test (`xit` → `it`), soit supprimer la suite si elle n'est plus pertinente. Le focus (`fit`, `describe.only`) doit toujours être retiré avant commit.

**Occurrences (3) :**

- `src/app/components/user-list/user-list.component.spec.ts:18`
  ```typescript
  xit('should filter users by search term', () => {
  ```
- `src/app/components/user-list/user-list.component.spec.ts:23`
  ```typescript
  fit('should delete a user', () => {
  ```
- `src/app/components/user-list/user-list.component.spec.ts:28`
  ```typescript
  it.skip('should refresh the list', () => {
  ```

---

## Performance — Lazy Loading

| Metrique | Valeur |
|----------|--------|
| Routes eager (sans lazy) | 3 |
| Routes lazy | 0 |
| Ratio lazy loading | 0% |

> **Recommandation :** Moins de 50% des routes utilisent le lazy loading.
> Chaque route eager augmente le bundle initial charge au demarrage.
> Migrer vers `loadComponent` (Angular 15+) pour les routes les plus lourdes.

---

## Plan de refactoring — Par ou commencer

### Cette semaine (Critique)

- **Subscription sans unsubscribe** (MEM001) — Une subscription sans unsubscribe/takeUntil crée un memory leak....
- **innerHTML sans sanitization** (SEC001) — innerHTML peut injecter du HTML malicieux (XSS). Angular bypass la sanitization ...
- **Cle API ou secret hardcode** (SEC002) — Une cle API, token ou secret hardcode dans le code source est expose des qu'il e...

### Ce mois-ci (Important)

- **ChangeDetectionStrategy.Default** (PERF001) — Default change detection vérifie tous les composants à chaque cycle. Coûteux sur...
- **Usage de 'any' TypeScript** (TYPE001) — Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereu...
- **HttpClient dans un composant** (ARCH001) — Les appels HTTP dans les composants mélangent les responsabilités. Difficile à t...
- ***ngFor sans trackBy** (PERF003) — *ngFor sans trackBy force Angular à recréer tout le DOM à chaque détection de ch...
- **URL hardcodée dans le code** (ARCH002) — Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. For...
- **Image sans attribut alt** (A11Y001) — Une balise <img> sans attribut alt est invisible aux lecteurs d'écran et pénalis...
- **Click sur element non-interactif** (A11Y002) — Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clav...
- **setTimeout/setInterval sans cleanup** (JS001) — Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamai...
- **Route sans lazy loading** (PERF002) — Les routes chargées eagerly augmentent le bundle initial et ralentissent le déma...

### Sur la roadmap (Mineur)

- **console.log en production** (DEBUG001) — Les console.log oubliés exposent des données internes en prod et polluent la con...
- **Test skippe ou focus** (TEST001) — Un `xit`, `fit`, `it.skip` ou `describe.only` oublié signifie qu'une partie de l...

---

*Rapport genere par Angular Code Audit v1.4.0 — 2026-05-06 00:28*  
*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  
*Pour un audit complet avec recommandations LLM : contact@[votre-email]*
