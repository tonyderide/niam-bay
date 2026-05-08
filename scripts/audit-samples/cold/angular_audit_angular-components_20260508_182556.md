# Angular Code Audit — angular-components

**Date :** 2026-05-08 18:25  
**Outil :** Angular Code Audit v1.6.0  
**Projet analysé :** `/tmp/audits-cold/angular-components`  

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
| Version Angular | ^6.1.0 |
| Fichiers TypeScript | 21 |
| Fichiers HTML | 5 |
| Composants | 3 |
| Services | 0 |
| Modules NgModule | 2 |
| Pipes | 0 |
| Guards | 0 |
| Total lignes de code | 2,221 |
| Tests detectes | Oui |

> **[CRITIQUE] Version Angular obsolete**  
> Angular ^6.1.0 est ancien (< 16). Signals, Standalone, Control Flow — rien de tout ca. Migration vers Angular 17+ fortement recommandee.

---

## Resume des problemes

| Severite | Nombre |
|----------|--------|
| CRITIQUE | 2 |
| IMPORTANT | 26 |
| MINEUR | 2 |
| **Total** | **30** |

---

## [CRITIQUE] Securite

### SEC001 — innerHTML sans sanitization

**Description :** innerHTML peut injecter du HTML malicieux (XSS). Angular bypass la sanitization avec innerHTML.

**Correction :** Utiliser `DomSanitizer.bypassSecurityTrustHtml()` avec validation stricte, ou restructurer le template sans innerHTML.

**Occurrences (2) :**

- `projects/angular-datetimerangepicker/src/time/time-component.html:8`
  ```typescript
  <span><b [innerHTML]="getCurrentHour()"></b></span>
  ```
- `projects/angular-datetimerangepicker/src/time/time-component.html:22`
  ```typescript
  <span><b [innerHTML]="getCurrentMinute()" (mouseWheelUp)="addMinute(options.minuteInterval)"></b></span>
  ```

---

## [IMPORTANT] Type Safety

### TYPE001 — Usage de 'any' TypeScript

**Description :** Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.

**Correction :** Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.

**Occurrences (13) :**

- `src/test.ts:10`
  ```typescript
  declare const require: any;
  ```
- `src/app/app.component.ts:3`
  ```typescript
  declare var require: any;
  ```
- `src/app/app.component.ts:24`
  ```typescript
  initialConfigDatePickerOptions: any = {
  ```
- `src/app/app.component.ts:35`
  ```typescript
  startDateConfigDatePickerOptions: any = {
  ```
- `src/app/app.component.ts:38`
  ```typescript
  endDateConfigDatePickerOptions: any = {
  ```
- `src/app/app.component.ts:41`
  ```typescript
  minDateConfigDatePickerOptions: any = {
  ```
- `src/app/app.component.ts:44`
  ```typescript
  maxDateConfigDatePickerOptions: any = {
  ```
- `src/app/app.component.ts:47`
  ```typescript
  daterangepickerOptions: any = {
  ```
- `projects/angular-datetimerangepicker/src/public_api.ts:4`
  ```typescript
  declare var require: any;
  ```
- `projects/angular-datetimerangepicker/src/format-date-pipe.ts:4`
  ```typescript
  transform(value: any, format: string): string {
  ```

  _...et 3 autres occurrences._

---

## [IMPORTANT] Performance

### PERF003 — *ngFor sans trackBy

**Description :** *ngFor sans trackBy force Angular à recréer tout le DOM à chaque détection de changement. Sur une liste de 100+ items qui change fréquemment, c'est un gros frein perf.

**Correction :** Ajouter `; trackBy: trackByFn` dans le *ngFor, et définir `trackByFn(index, item) { return item.id; }` dans le composant. Sur Angular 17+, utiliser le new control flow `@for` avec `track item.id`.

**Occurrences (6) :**

- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:24`
  ```typescript
  <span *ngFor="let day of weekDays" class="day">{{ day }}</span>
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:27`
  ```typescript
  <div class="drp-calendar-row" *ngFor="let y of yearsList; let i=index">
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:34`
  ```typescript
  <div class="drp-calendar-row" *ngFor="let m of monthsList;">
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:41`
  ```typescript
  <div class="drp-calendar-row" *ngFor="let week of weekList; let i=index">
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:42`
  ```typescript
  <span *ngFor="let day of weekList[i]" (click)="dateSelected(day)"
  ```
- `projects/angular-datetimerangepicker/src/daterangepicker/daterangepicker.component.html:52`
  ```typescript
  <button type="button" *ngFor="let range of derivedOptions.preDefinedRanges" class="drp-btn outline"
  ```

---

## [IMPORTANT] Architecture

### ARCH002 — URL hardcodée dans le code

**Description :** Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. Force un commit pour changer un endpoint. Mauvaise pratique multi-environnements.

**Correction :** Déplacer l'URL dans `src/environments/environment.ts` et `environment.prod.ts`. Utiliser `environment.apiUrl` dans le code.

**Occurrences (4) :**

- `projects/angular-datetimerangepicker/src/img/chevron-left.ts:7`
  ```typescript
  xmlns="http://www.w3.org/2000/svg"
  ```
- `projects/angular-datetimerangepicker/src/img/chevron-left.ts:8`
  ```typescript
  xmlns:xlink="http://www.w3.org/1999/xlink"
  ```
- `projects/angular-datetimerangepicker/src/img/double-chevron-left.ts:7`
  ```typescript
  xmlns="http://www.w3.org/2000/svg"
  ```
- `projects/angular-datetimerangepicker/src/img/double-chevron-left.ts:8`
  ```typescript
  xmlns:xlink="http://www.w3.org/1999/xlink"
  ```

---

## [IMPORTANT] Accessibilite

### A11Y002 — Click sur element non-interactif

**Description :** Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clavier et aux lecteurs d'écran. L'utilisateur ne peut pas activer l'action sans souris.

**Correction :** Soit utiliser un vrai <button> (ou <a> si c'est une navigation), soit ajouter `role="button" tabindex="0"` + handler `(keydown.enter)` et `(keydown.space)`.

**Occurrences (3) :**

- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:28`
  ```typescript
  <span (click)="yearSelected(y)" [class.active]="year === y">
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:35`
  ```typescript
  <span (click)="monthSelected(m.value)" [class.active]="month === m.value">
  ```
- `projects/angular-datetimerangepicker/src/calendar/calendar-component.html:42`
  ```typescript
  <span *ngFor="let day of weekList[i]" (click)="dateSelected(day)"
  ```

---

## [MINEUR] Code Quality

### DEBUG001 — console.log en production

**Description :** Les console.log oubliés exposent des données internes en prod et polluent la console.

**Correction :** Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.

**Occurrences (2) :**

- `src/main.ts:12`
  ```typescript
  .catch(err => console.error(err));
  ```
- `projects/angular-datetimerangepicker/src/daterangepicker/daterangepicker.component.ts:260`
  ```typescript
  console.warn(
  ```

---

## Performance — Lazy Loading

| Metrique | Valeur |
|----------|--------|
| Routes eager (sans lazy) | 0 |
| Routes lazy | 0 |
| Ratio lazy loading | 0% |

> **Recommandation :** Moins de 50% des routes utilisent le lazy loading.
> Chaque route eager augmente le bundle initial charge au demarrage.
> Migrer vers `loadComponent` (Angular 15+) pour les routes les plus lourdes.

---

## Plan de refactoring — Par ou commencer

### Cette semaine (Critique)

- **innerHTML sans sanitization** (SEC001) — innerHTML peut injecter du HTML malicieux (XSS). Angular bypass la sanitization ...

### Ce mois-ci (Important)

- **Usage de 'any' TypeScript** (TYPE001) — Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereu...
- ***ngFor sans trackBy** (PERF003) — *ngFor sans trackBy force Angular à recréer tout le DOM à chaque détection de ch...
- **URL hardcodée dans le code** (ARCH002) — Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. For...
- **Click sur element non-interactif** (A11Y002) — Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clav...

### Sur la roadmap (Mineur)

- **console.log en production** (DEBUG001) — Les console.log oubliés exposent des données internes en prod et polluent la con...

---

*Rapport genere par Angular Code Audit v1.6.0 — 2026-05-08 18:25*  
*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  
*Pour un audit complet avec recommandations LLM : contact@[votre-email]*
