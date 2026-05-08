# Angular Code Audit — EcoCraftingTool

**Date :** 2026-05-08 18:25  
**Outil :** Angular Code Audit v1.6.0  
**Projet analysé :** `/tmp/audits-cold/EcoCraftingTool`  

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
| Version Angular | ^21.2.0 |
| Fichiers TypeScript | 83 |
| Fichiers HTML | 14 |
| Composants | 26 |
| Services | 16 |
| Modules NgModule | 0 |
| Pipes | 2 |
| Guards | 0 |
| Total lignes de code | 95,004 |
| Tests detectes | Non |

---

## Resume des problemes

| Severite | Nombre |
|----------|--------|
| CRITIQUE | 8 |
| IMPORTANT | 32 |
| MINEUR | 13 |
| **Total** | **53** |

---

## [CRITIQUE] Memory Leaks

### MEM001 — Subscription sans unsubscribe

**Description :** Une subscription sans unsubscribe/takeUntil crée un memory leak.

**Correction :** Utiliser `takeUntil(this.destroy$)` ou `takeUntilDestroyed()` (Angular 16+) ou le `async` pipe dans le template.

**Occurrences (8) :**

- `src/app/service/price-calculator-server.service.spec.ts:44`
  ```typescript
  service.getAllRecipes(true).subscribe(result => {
  ```
- `src/app/service/price-calculator-server.service.spec.ts:70`
  ```typescript
  service.getAllItems(true).subscribe(result => {
  ```
- `src/app/service/price-calculator-server.service.spec.ts:88`
  ```typescript
  service.attemptConnection(serverConfig).subscribe(result => connectionSucceeded = result);
  ```
- `src/app/service/price-calculator-server.service.spec.ts:106`
  ```typescript
  service.attemptConnection(serverConfig).subscribe(result => connectionSucceeded = result);
  ```
- `src/app/service/price-calculator-server.service.spec.ts:128`
  ```typescript
  service.attemptConnection(serverConfig).subscribe(result => connectionSucceeded = result);
  ```
- `src/app/header/header.component.ts:63`
  ```typescript
  this.releaseNotesService.getReleases().subscribe(releases => {
  ```
- `src/app/header/header.component.ts:112`
  ```typescript
  dialogRef.afterClosed().subscribe((result: ServerDialogResult) => {
  ```
- `src/app/header/server/server-dialog.component.ts:121`
  ```typescript
  .subscribe({
  ```

### JS001 — setTimeout/setInterval sans cleanup

**Description :** Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamais clear continue a tourner apres la destruction du composant. Sur une SPA Angular, accumuler des intervalles oublies = memory leak progressif + appels reseau fantomes. Different de RxJS subscriptions (gere par MEM001).

**Correction :** Garder la reference (`this.timerId = setTimeout(...)`) et appeler `clearTimeout(this.timerId)` dans `ngOnDestroy()`. Ou mieux : utiliser `interval(N).pipe(takeUntilDestroyed())` (Angular 16+) qui s'auto-nettoie.

**Occurrences (5) :**

- `src/app/service/locale.service.ts:79`
  ```typescript
  await new Promise(resolve => setTimeout(resolve));
  ```
- `src/app/service/locale.service.ts:88`
  ```typescript
  await new Promise(resolve => setTimeout(resolve));
  ```
- `src/app/service/locale.service.ts:97`
  ```typescript
  await new Promise(resolve => setTimeout(resolve));
  ```
- `src/app/crafting/skills/skills.component.ts:79`
  ```typescript
  setTimeout(() => {
  ```
- `src/app/crafting/skills/skills.component.ts:114`
  ```typescript
  setTimeout(() => {
  ```

---

## [IMPORTANT] Type Safety

### TYPE001 — Usage de 'any' TypeScript

**Description :** Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.

**Correction :** Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.

**Occurrences (9) :**

- `src/app/test-utils.ts:13`
  ```typescript
  export function provideMockDialogData(data: any = null): Provider {
  ```
- `src/app/test-utils.ts:20`
  ```typescript
  export function provideDialogTestingDependencies(dialogData?: any): Provider[] {
  ```
- `src/app/service/storage.service.ts:29`
  ```typescript
  get(key: string): any;
  ```
- `src/app/service/locale.service.ts:30`
  ```typescript
  get(key: string): any;
  ```
- `src/app/service/image.service.ts:71`
  ```typescript
  getImgStyle(nameID: string, imageFile: string, xPos: number, yPos: number, size: number, filter?: string): any {
  ```
- `src/app/service/image.service.ts:78`
  ```typescript
  getProfitImgStyle(): any {
  ```
- `src/app/service/image.service.ts:84`
  ```typescript
  getCalorieImgStyle(): any {
  ```
- `src/app/service/image.service.ts:90`
  ```typescript
  getTableImgStyle(table: CraftingTable): any {
  ```
- `src/app/service/image.service.ts:97`
  ```typescript
  getSkillImgStyle(skill: Skill): any {
  ```

### TYPE002 — Cast 'as any' explicite

**Description :** Un cast `as any` desactive volontairement TypeScript pour cette expression. Different de `: any` (TYPE001) qui declare un type ambigu : `as any` est un acte explicite de bypass du verificateur. Apparait souvent quand un dev se bat avec un type de librairie tiers, ou quand un payload API renvoie une structure non typee. Le probleme : le compilateur ne peut plus garantir que les acces suivants (`.foo`, `.bar()`) sont valides — un refactor de la source ne mettra plus a jour les usages, et un null/undefined dans le payload ne sera pas detecte au build.

**Correction :** 1) Si la forme est connue : declarer une `interface` ou `type` et caster vers ce type (`as User`). 2) Si la forme est partiellement connue : `as Partial<User>` ou `as Pick<User, 'id'|'name'>`. 3) Si la forme est vraiment inconnue : caster vers `unknown` puis valider avec un type guard avant l'acces (`if (typeof x === 'object' && x !== null && 'id' in x)`). 4) Pour les reponses HTTP : utiliser `http.get<MyType>(url)` ou un schema runtime (zod, yup) pour valider la forme avant cast. Le cast `as unknown` est preferable a `as any` car il force au moins une etape de validation explicite.

**Occurrences (1) :**

- `src/app/service/locale.service.ts:120`
  ```typescript
  const wn = window.navigator as any;
  ```

---

## [IMPORTANT] Architecture

### ARCH001 — HttpClient dans un composant

**Description :** Les appels HTTP dans les composants mélangent les responsabilités. Difficile à tester et réutiliser.

**Correction :** Déplacer les appels HTTP dans des services dédiés. Les composants ne consomment que des observables.

**Occurrences (11) :**

- `src/app/app.config.ts:2`
  ```typescript
  import {provideHttpClient} from '@angular/common/http';
  ```
- `src/app/app.config.ts:8`
  ```typescript
  provideHttpClient(),
  ```
- `src/app/service/price-calculator-server.service.spec.ts:5`
  ```typescript
  import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
  ```
- `src/app/service/price-calculator-server.service.spec.ts:6`
  ```typescript
  import {provideHttpClient} from '@angular/common/http';
  ```
- `src/app/service/price-calculator-server.service.spec.ts:20`
  ```typescript
  providers: [provideHttpClient(), provideHttpClientTesting()]
  ```
- `src/app/service/release-notes.service.spec.ts:4`
  ```typescript
  import {provideHttpClient} from '@angular/common/http';
  ```
- `src/app/service/release-notes.service.spec.ts:12`
  ```typescript
  providers: [provideHttpClient(), provideDialogTestingDependencies()]
  ```
- `src/app/header/header.component.spec.ts:4`
  ```typescript
  import {provideHttpClient} from '@angular/common/http';
  ```
- `src/app/header/header.component.spec.ts:14`
  ```typescript
  providers: [provideHttpClient()]
  ```
- `src/app/header/release-notes/release-notes-dialog.component.spec.ts:4`
  ```typescript
  import {provideHttpClient} from '@angular/common/http';
  ```

  _...et 1 autres occurrences._

---

## [IMPORTANT] Accessibilite

### A11Y002 — Click sur element non-interactif

**Description :** Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clavier et aux lecteurs d'écran. L'utilisateur ne peut pas activer l'action sans souris.

**Correction :** Soit utiliser un vrai <button> (ou <a> si c'est une navigation), soit ajouter `role="button" tabindex="0"` + handler `(keydown.enter)` et `(keydown.space)`.

**Occurrences (6) :**

- `src/app/header/export/export-dialog.component.html:4`
  ```typescript
  <span class="ml-auto material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```
- `src/app/header/release-notes/release-notes-dialog.component.html:3`
  ```typescript
  <span class="ml-auto material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```
- `src/app/header/settings/settings-dialog.component.html:3`
  ```typescript
  <span class="ml-auto material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```
- `src/app/header/import/import-dialog.component.html:4`
  ```typescript
  <span class="ml-auto material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```
- `src/app/header/server/server-dialog.component.html:12`
  ```typescript
  <span class="ml-auto material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```
- `src/app/crafting/recipe-dialog/recipe-dialog.component.html:3`
  ```typescript
  <span class="material-icons cursor-pointer hover:opacity-80" (click)="close()">close</span>
  ```

---

## [MINEUR] Code Quality

### DEBUG001 — console.log en production

**Description :** Les console.log oubliés exposent des données internes en prod et polluent la console.

**Correction :** Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.

**Occurrences (13) :**

- `src/main.ts:6`
  ```typescript
  .catch((err) => console.error(err));
  ```
- `src/assets/data/util/data-utils.ts:11`
  ```typescript
  console.error(`Crafting table ${nameID} not found`);
  ```
- `src/assets/data/util/data-utils.ts:19`
  ```typescript
  console.error(`Skill ${nameID} not found`);
  ```
- `src/assets/data/util/data-utils.ts:27`
  ```typescript
  console.error(`Item ${nameID} not found`);
  ```
- `src/app/service/crafting.service.ts:289`
  ```typescript
  console.warn(`Could not compute prices for all recipes after ${maxLoops} loops`);
  ```
- `src/app/service/locale.service.ts:156`
  ```typescript
  console.warn(`Could not find locale data for ${type}`);
  ```
- `src/app/service/locale.service.ts:161`
  ```typescript
  console.debug(`Could not find locale entry for ${nameID} in ${type}`);
  ```
- `src/app/service/price-calculator-server.service.ts:151`
  ```typescript
  console.debug(`New item found: ${id}`);
  ```
- `src/app/service/price-calculator-server.service.ts:264`
  ```typescript
  console.debug(`Output not found: ${serverOutput.NameID}`);
  ```
- `src/app/service/price-calculator-server.service.ts:275`
  ```typescript
  console.debug(`Output quantity mismatch: ${serverOutput.NameID} ${match.quantity} ${serverOutput.Ammount}`);
  ```

  _...et 3 autres occurrences._

---

## Plan de refactoring — Par ou commencer

### Cette semaine (Critique)

- **Subscription sans unsubscribe** (MEM001) — Une subscription sans unsubscribe/takeUntil crée un memory leak....

### Ce mois-ci (Important)

- **Usage de 'any' TypeScript** (TYPE001) — Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereu...
- **HttpClient dans un composant** (ARCH001) — Les appels HTTP dans les composants mélangent les responsabilités. Difficile à t...
- **Click sur element non-interactif** (A11Y002) — Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clav...
- **setTimeout/setInterval sans cleanup** (JS001) — Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamai...
- **Cast 'as any' explicite** (TYPE002) — Un cast `as any` desactive volontairement TypeScript pour cette expression. Diff...

### Sur la roadmap (Mineur)

- **console.log en production** (DEBUG001) — Les console.log oubliés exposent des données internes en prod et polluent la con...

---

*Rapport genere par Angular Code Audit v1.6.0 — 2026-05-08 18:25*  
*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  
*Pour un audit complet avec recommandations LLM : contact@[votre-email]*
