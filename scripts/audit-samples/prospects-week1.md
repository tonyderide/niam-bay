# Prospects week 1 — Angular audit 49€

**Généré** : 2026-05-07 cycle 17 vacation NB
**Source** : `scripts/prospect_finder.py` (gh search authentifié)
**Output** : `prospects-week1.csv` (25 prospects qualifiés, triés par score)

## Comment lire le CSV

| Colonne | Signification |
|---|---|
| `score` | Score composite (max ~85). Pondéré : angular.json présent (+30), solo-user (+15), stars 1-15 (+18 à +12), récence (+10 à +0), homepage (+8), anti-template (-35), org (-5) |
| `owner_type` | `User` = solo dev (cible idéale), `Organization` = équipe (taux conversion plus bas, mais possible si SaaS) |
| `stars` | Limité à 1..40 par construction. Sweet spot : 5-30 (ni inactif ni populaire à équipe technique propre) |
| `days_since_push` | Repos actifs (<30j) sont vivants → mainteneur joignable. >90j = projet probablement abandonné |
| `homepage` | Présence d'un site live = signal fort de produit (vs projet d'apprentissage) |
| `signals` | Trace de scoring lisible. `-NEG` indique un malus appliqué |

## Top candidats à examiner manuellement (filtre humain recommandé)

### Tier 1 — solo dev + produit live (homepage non-github.io)

Ces profils sont les plus susceptibles d'avoir 49€ de budget pour audit pro :

1. **DiogoPCS/ProjetoAngularFirebase** (★17, 2j) — homepage Vercel `projeto-angular-firebase-omega.vercel.app` → projet déployé
2. **aritchie05/EcoCraftingTool** (★30, 58j) — homepage `eco-calc.com` → calculateur Eco game, vrai produit avec domaine custom

### Tier 2 — solo dev maintainer de bibliothèque Angular

Ces profils ont une audience d'utilisateurs Angular → audit valorise leur lib :

3. **ajaysinghj8/angular-inport** (★34, 0j) — library `Angular In View Port Detector`, actif aujourd'hui
4. **fvilers/ngx-file-helpers** (★37, 0j) — `Angular File Helpers`, mainteneur actif
5. **technikhil314/angular-components** (★24, 3j) — Collection of all my open source angular components

### Tier 3 — solo dev projet personnel actif (intent à valider)

6. **DiogoPCS** déjà cité — Tier 1
7. **Intelligence08/Angular-Dashboard** (★1, 81j) — généré CLI 20.1.0, dashboard perso. Audit possible si on cherche un cas pour la landing
8. **ahmadullahmukhlis/angular-dashboard** (★1, 0j) — top du score brut mais pas de description ni homepage → **probablement projet d'apprentissage**, à filtrer

### Tier 4 — Org petite/moyenne (taux conversion plus bas)

- `CenterForOpenScience/angular-osf` (★4, 0j) → recherche scientifique, peut-être budget
- `imagekit-developer/imagekit-angular` (★18, 21j) → SDK officiel imagekit.io, contact possible via leur business
- `GSA/ngx-uswds` (★19, 0j) → US gov, exclu (taux réponse ~0%)

## Approche recommandée pour cold-emails (cf playbook Jour 1, step 3)

**Cible 5 cold sur Tier 1 + Tier 2** :
1. DiogoPCS (Tier 1, projet vivant)
2. aritchie05 (Tier 1, vraie boîte derrière eco-calc.com peut-être)
3. ajaysinghj8 (Tier 2, library)
4. fvilers (Tier 2, library)
5. technikhil314 (Tier 2, collection)

**Pour chacun** : `python scripts/angular_audit.py <repo cloné>` → PDF nominal en pièce jointe → email "J'ai audité votre projet Angular pour vous montrer mon outil. Voici votre rapport. Si vous voulez le pro avec 18 règles + suivi, c'est 49€."

**Ne PAS spammer Tier 4 orgs** sur premier essai — taux de réponse trop bas, message peut être perçu comme cold-email mass.

## Limites du scoring (à reconnaître)

- **Pas de détection de tests** (skip volontaire pour économiser API calls). Repo avec tests ou non, pas su par le scoring → certains "low-score" pourraient être des projets très propres déjà couverts
- **Pas d'extraction email mainteneur** : Tony doit aller chercher sur le profil GitHub de l'owner
- **Templates partiellement filtrés** : keyword matching simple, pas de NLP. `angular-tutorial` est filtré, mais `dashboard-perso` ne l'est pas
- **Pas de signal "active dev account"** : un compte avec 50 repos abandonnés n'est pas pénalisé vs un compte focused

**Conclusion** : score = baseline raisonnable, **filtre humain obligatoire** sur top 10 avant cold-email.

## Reproductibilité

```bash
cd ~/projets/tonyderide/niam-bay
python3 scripts/prospect_finder.py
# Output: scripts/audit-samples/prospects-week1.csv
```

Rate limit consommé : ~50 calls / 5000h. Réexécutable plusieurs fois par heure.

Pour élargir le pool, modifier `QUERIES` dans le script (ajouter "angular saas", "angular admin", etc.).
