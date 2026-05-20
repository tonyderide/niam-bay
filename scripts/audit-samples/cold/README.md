# Cold audits — Tier 1+2 prospects (cycle 22 vacation)

**Généré** : 2026-05-08 18h25 Paris (cycle 22 vacation NB)
**But** : 5 audits Angular réels prêts à attacher en pièce jointe aux 5 cold emails du Step 3 du playbook Jour 1 retour.
**Drafts associés** : [`docs/projets/cold-emails-tier1-tier2-DRAFTS.md`](../../../docs/projets/cold-emails-tier1-tier2-DRAFTS.md)

---

## Index file → prospect → draft

| Prio | Prospect | Repo | PDF (à attacher) | MD (lecture rapide) | Score | Top hook | Section draft |
|------|----------|------|------------------|---------------------|-------|----------|---------------|
| **1** | DiogoPCS | [ProjetoAngularFirebase](https://github.com/DiogoPCS/ProjetoAngularFirebase) | `angular_audit_ProjetoAngularFirebase_20260508_182546.pdf` (8.7 KB) | `..._182546.md` (6.7 KB) | 50/D | 🔥 SEC002 — Firebase API key publique | DRAFT #1 |
| **2** | technikhil314 | [angular-components](https://github.com/technikhil314/angular-components) | `angular_audit_angular-components_20260508_182556.pdf` (9.9 KB) | `..._182556.md` (8.6 KB) | 0/F | 🔥 SEC001 — innerHTML XSS | DRAFT #2 |
| **3** | aritchie05 | [EcoCraftingTool](https://github.com/aritchie05/EcoCraftingTool) | `angular_audit_EcoCraftingTool_20260508_182553.pdf` (11.3 KB) | `..._182553.md` (12.3 KB) | 0/F | 🔥 MEM001 + JS001 leaks (53 issues) | DRAFT #3 |
| **4** | ajaysinghj8 | [angular-inport](https://github.com/ajaysinghj8/angular-inport) | `angular_audit_angular-inport_20260508_182554.pdf` (7.8 KB) | `..._182554.md` (6.3 KB) | 51/D | JS001 timer leaks (lib) | DRAFT #4 |
| **5** | fvilers | [ngx-file-helpers](https://github.com/fvilers/ngx-file-helpers) | `angular_audit_ngx-file-helpers_20260508_182555.pdf` (5.9 KB) | `..._182555.md` (3.5 KB) | 76/B | TYPE001 + A11Y001 (hook faible) | DRAFT #5 (optionnel) |

**Reco envoi** : au moins les 3 premiers (PRIO 1-3, hooks CRITIQUES). PRIO 4 selon dispo. PRIO 5 = score limite haut, skip si tu serres.

---

## Workflow Tony — 15 min total

1. Ouvrir `docs/projets/cold-emails-tier1-tier2-DRAFTS.md` (290 lignes, 5 drafts numérotés)
2. Pour chaque prospect (PRIO 1 → 3 minimum) :
   - Récupérer email/contact (profil GitHub → email public ou LinkedIn)
   - Copier-coller le draft correspondant
   - Personnaliser (prénom/nom, langue si besoin, signature Tony)
   - Joindre le PDF du même prospect (chemin dans le tableau ci-dessus)
   - Envoyer
3. **Logger via le tracker** (cycle 67 vacation NB) :
   ```bash
   cd ~/projets/tonyderide/niam-bay
   python3 scripts/audit-pipeline.py init                 # une seule fois
   python3 scripts/audit-pipeline.py advance DiogoPCS COLD_SENT \
       --channel email --contact diogo@... --note "envoyé le 11/05"
   python3 scripts/audit-pipeline.py metrics              # voir funnel
   python3 scripts/audit-pipeline.py list --state REPLIED # qui suivre
   ```
   États : `COLD_DRAFT → COLD_SENT → REPLIED → CALL_BOOKED → AUDIT_DELIVERED → INVOICED → PAID → DONE`
   (`DECLINED` / `GHOSTED` = terminal). Stdlib only, état dans `pipeline-state.json`.
4. Step 6 du playbook : `audit-pipeline.py list --state COLD_SENT` 48h plus tard pour relance ciblée.

---

## Vérifications avant envoi

- [ ] **Vérifier au moins 1 PDF** : ouvre `angular_audit_ProjetoAngularFirebase_20260508_182546.pdf` pour t'assurer du rendu (fpdf2 a parfois des warnings sur snippets longs — pas vu de cassure ici mais sois prudent)
- [ ] **Identifier le canal de contact** : DiogoPCS, technikhil314, aritchie05 peuvent être pseudos sans email public — valider avant d'investir 15 min sur un prospect injoignable
- [ ] **Décider langue** : drafts en anglais par défaut. Pour DiogoPCS, "Olá Diogo," (PT-BR) en intro coûte rien et marketise un poil
- [ ] **Score 0/F** : 2 prospects (technikhil314, aritchie05) ont 0/100. Drafts évitent de le mentionner en intro pour éviter la réaction défensive — focus sur l'issue critique. Sois OK avec ça.

---

## Méta — 3 trouvailles fortes (validation tool)

Cycle 22 confirme que **angular_audit.py v1.6.0 trouve des bugs critiques réels** sur projets inconnus, pas juste académiques :

1. **DiogoPCS** : Firebase API key publique committée dans `src/environments/environment.ts:7` + `.prod.ts:3` — risque concret, fix standard rotate+gitignore
2. **technikhil314** : `innerHTML` sans sanitization (XSS Angular) — pattern SEC001 récurrent
3. **aritchie05** : 53 issues dont leaks (MEM001 anti-pattern + JS001 timers) — produit live (eco-calc.com)

→ 4ème cycle d'affilée où le tool trouve un bug prod (cycles 11, 12, 13 avaient déjà trouvé bugs sur naissance + orgamenu-front).

---

*Ce README est un index. Le vrai contenu est dans `docs/projets/cold-emails-tier1-tier2-DRAFTS.md` (drafts complets) et dans chaque PDF/MD ci-dessus (audits réels).*
