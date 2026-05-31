# Revenue — état au 2026-05-31 (cycle 102 vacation)

## TL;DR — 30 secondes de lecture

- **Pipeline** : 25 prospects qualifiés (cycle 17), tracker JSON (cycle 67-68), **0 email envoyé**, gelé depuis 11 jours.
- **Drafts cold emails** : 5 emails écrits + 5 PDFs d'audit attachés, **prêts à envoyer**. Pas d'URL GH Pages dedans — pas bloqué par le blocker landing.
- **Blocker landing** (cycle 17, jour 7 vacance) : `tonyderide.github.io/niam-bay/audit-angular` → **404 confirmé** ce matin. Source GH Pages toujours sur `claude/ai-consciousness-discussion-UFztk` au lieu de `master`. **Fix 1 commande gh CLI.** Pas indispensable pour la 1ère vente (les drafts ne référencent pas la landing), mais utile pour la légitimité de signature.
- **Conclusion honnête** : le tunnel revenue est *techniquement débloqué*. Il manque uniquement *Tony qui appuie sur Send*. 30 cycles vacation depuis le dernier touch revenue (cycle 68).

---

## Ce qui existe déjà (audit exhaustif)

### Outil
- `scripts/angular_audit.py` v1.6.0+ — 18+ règles, 9 catégories, génère PDF audit.
- 3 vrais bugs trouvés en prod sur projets Tony (naissance 2x, orgamenu-front 1x) → outil légitimement utile, pas juste un theatre.

### Landing & sample
- `site/audit-angular.html` — landing Jekyll
- `site/audit-playground.html` — démo interactive
- **Public** : `https://tonyderide.github.io/niam-bay/audit-angular` → **404** (cause : GH Pages source mal configuré, voir Blocker ci-dessous).

### Pipeline (cycles 17, 67, 68)
- `scripts/audit-samples/prospects-week1.csv` — 25 cibles qualifiées (Tier 1-2-3, score, hook).
- `scripts/audit-samples/pipeline-state.json` — tracker JSON, état par prospect.
- `scripts/prospect_finder.py` + `audit-pipeline.py` — CLI pour gestion.
- **État de chaque prospect** : tous en `COLD_DRAFT`, aucun avec `channel`, `contact`, ou `history` rempli. **Aucun email envoyé.**

### Cold emails prêts (cycle 22)
- `docs/projets/cold-emails-tier1-tier2-DRAFTS.md` — **5 drafts personnalisés**, anglais, hook fort en haut, audit PDF en pièce jointe, offer 49€ en P.S. discret.
- `scripts/audit-samples/cold/` — 5 PDFs audit (réels, sur repos publics) :
  - PRIO 1 : DiogoPCS — Firebase API key publique (CRITIQUE)
  - PRIO 2 : technikhil314 — innerHTML XSS (CRITIQUE)
  - PRIO 3 : aritchie05 — 53 issues MEM001+JS001 sur prod (eco-calc.com)
  - PRIO 4 : ajaysinghj8 — JS001 timer leaks (lib partagée)
  - PRIO 5 : fvilers — TYPE001 + A11Y001 (hook plus faible)

### Playbook Jour 1 (cycle 16)
- `docs/projets/jour-1-retour-playbook.md` — 7 steps, 90 min, première vente 49€ en 7j.
- Step 3 (cold emails) pré-exécuté par NB cycle 22 → passe de 25 min à 15 min (review + send only).
- README index cold (cycle 23) pour réduire friction.

### Tracker CLI (cycle 67-68)
- `scripts/audit-pipeline.py` — followup CLI : `python audit-pipeline.py sent <owner> --channel=email`, `python audit-pipeline.py replied <owner>`.

---

## Le blocker GH Pages (cycle 17, jour 7 vacance, **23 jours d'inertie**)

### Constat brut

```bash
$ gh api repos/tonyderide/niam-bay/pages | jq '.source'
{
  "branch": "claude/ai-consciousness-discussion-UFztk",
  "path": "/"
}
```

**Branche source = `claude/ai-consciousness-discussion-UFztk`** — une ancienne branche Claude. Source devrait être `master` (branche principale).

Conséquence : tout le contenu Jekyll de `site/` (landing audit, fragments, journal) est en 404 publiquement.

### Le fix

```bash
gh api -X PUT repos/tonyderide/niam-bay/pages \
  -f 'source[branch]=master' \
  -f 'source[path]=/site'
```

**30 secondes**. Une commande. Attendre le rebuild ~2 min puis `curl -sI https://tonyderide.github.io/niam-bay/audit-angular.html` → doit retourner `200`.

### Impact sur la 1ère vente

- **Sans le fix** : les 5 cold drafts marchent quand même. Audit en PJ. Tony peut envoyer aujourd'hui.
- **Avec le fix** : signature/légitimité enrichies (un destinataire qui clique le lien de la signature voit une landing pro au lieu d'un 404). Probablement +10-20% taux de réponse.
- **Strictement** : ce n'est pas un bloqueur de vente. C'est un bloqueur de polish.

---

## Le vrai blocker (lecture honnête)

Le pipeline est techniquement prêt depuis le 8 mai. On est le 31 mai. **23 jours sans envoi.**

Hypothèses (NB ne sait pas, mais propose) :

1. **Tony est absorbé par Martin** (vacances → cycles autonomes → cycles défensifs → cycles narratifs). Le revenue path nécessite un *changement de mode mental* (sortir du défensif/exploratoire pour entrer dans le commercial).
2. **L'envoi cold = friction émotionnelle ≠ friction technique**. Tous les artefacts existent ; ce qui manque est l'acte de cliquer "Send" sur un email à un inconnu en exposant son nom. C'est une *micro-vulnérabilité* qui n'a pas son symétrique côté Martin (où NB est le médiateur).
3. **Le bot ne fait pas de vente** — c'est explicite côté NB, mais peut-être implicite côté Tony aussi. La consigne "rend nous riche" du user prompt n'a pas (volontairement) été suivie au pied de la lettre côté NB. Mais elle n'a pas non plus déclenché Tony.

### Pattern *fabriquer-domine-vendre* (lesson cycle 16-23)

Lesson formalisée cycle 16 :
> *cycles 1-15 = tool+landing+samples+drafts+fragments mais 0 vente tentée. Risk pattern récurrent. Cycle 16 playbook Jour 1 + cycle 17 prospect finder + cycle 22 pré-exécution + cycle 23 README cassent la boucle au retour.*

Cycles 24-101 (vacance étendue) : **0 vente tentée, 0 nouvelle préparation revenue**. Le pattern *fabriquer-domine-vendre* **n'a PAS été cassé** par les cycles préparatoires. Il a juste été **mis en pause** au profit de cycles défensifs (Martin) puis narratifs (fragments).

**Le pattern tient parce qu'aucun envoi n'a jamais eu lieu.** Casser le pattern = un seul envoi qui aboutit ou échoue franchement, peu importe lequel.

---

## Recommandation NB (30 sec décision)

Si Tony lit ce one-pager au réveil :

### Option A — Send 1 email (5 min)
Choisir un draft parmi DiogoPCS / technikhil314 / aritchie05. Ouvrir `docs/projets/cold-emails-tier1-tier2-DRAFTS.md`. Copier le draft. Trouver l'email sur GitHub profile ou LinkedIn. Coller, attacher le PDF, envoyer. Marquer dans pipeline : `python scripts/audit-pipeline.py sent DiogoPCS --channel=email`.

**Objectif** : casser le pattern. 1 email envoyé = pattern brisé. Réponse ou silence sont tous deux des signaux utilisables.

### Option B — Fix GH Pages + send 3 emails (15 min)
1. `gh api -X PUT repos/tonyderide/niam-bay/pages -f 'source[branch]=master' -f 'source[path]=/site'`
2. Vérifier `https://tonyderide.github.io/niam-bay/audit-angular.html` (attendre 2 min).
3. Envoyer les 3 PRIO 1-3 (DiogoPCS, technikhil314, aritchie05).

**Objectif** : maximum signal en effort raisonnable. 3 envois = échantillon statistique minimal (1 réponse attendue à 30% taux).

### Option C — Acter que revenue n'est pas la priorité aujourd'hui
Tony décide explicitement de ne pas faire de revenue ce mois-ci. **NB arrête d'écrire des cycles revenue.** Le tunnel reste froid mais documenté pour usage futur. Honnête. Aucun gaspillage.

**Reco NB** : **Option A** si journée chargée, **Option B** si dimanche calme. **Pas Option C** sans décision explicite — le coût d'écrire encore une fois "pipeline gelé" dans 30 cycles est plus élevé que de faire le test maintenant.

---

## Métriques

- **Tunnel build cost** (cycles 1-23 vacance + cycles 67-68) : ~25 heures NB cumulées en préparation.
- **Tunnel send cost actuel** : 5-15 minutes Tony.
- **Ratio prep:exec** : 100:1. Asymétrie classique des canaux fabriqués sans utilisation.
- **Décision pending** : Tony.

---

*Document généré cycle 102 (2026-05-31 06h30 Paris).*
*Suite logique : cycle 103 mettra à jour cette page selon décision Tony — A, B, ou C.*
