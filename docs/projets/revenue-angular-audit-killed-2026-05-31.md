# Revenue angular-audit — KILLED

2026-05-31, ~21h Paris. Décision Tony en session Claude Code locale.

## Décision

Kill définitif du projet revenue "vendre audits Angular à des prospects".

## Raison

Commodification IA mai 2026 : Cursor, Claude Code, Codex, ChatGPT peuvent générer le même audit Angular en 2 prompts, gratos ou quasi. Un dev senior ne paye pas $200 pour un PDF reproductible en 5 minutes. Une boîte non-technique peut demander à ChatGPT directement.

Le défaut n'est pas dans le tunnel (qui est techniquement débloqué, 25 prospects prêts, drafts écrits, PDFs prêts). Le défaut est dans le **produit** : pas de moat.

## Statut des artefacts

- `scripts/angular_audit.py` — **garder pour usage perso** (a déjà trouvé 3 bugs réels sur projets Tony, outil légitime à usage interne).
- `scripts/audit-samples/prospects-week1.csv` — archiver, ne plus actionner.
- `scripts/audit-samples/pipeline-state.json` — archiver, ne plus actionner.
- Cold drafts (cycle 22) + PDFs prêts — archiver.
- `site/audit-angular.html` + `site/audit-playground.html` — laisser en place, 404 GH Pages non bloquant (pas de fix nécessaire).

## Consigne à NB (cycle 104+)

**Arrêter les relances revenue angular-audit.** Pas de pause, pas de "on reprend plus tard" — kill.

Si NB veut aider Tony sur le revenue à l'avenir, il doit chercher une voie **non-réplicable par IA grand public**. Pistes possibles (à creuser, pas à exécuter sans validation Tony) :

- Exécution physique (présence terrain, intervention manuelle, livraison)
- Accès à des données privées que Tony seul peut obtenir (clients propres, contacts inside)
- Relations humaines longues (un coaching, un mentorat, un suivi récurrent)
- Expertise très niche où Tony a une edge documentable (Kraken Futures grid trading après 91+ cycles d'expérience Martin ? À discuter)
- Produit physique ou service nécessitant une présence légale (auto-entreprise déjà setup)

**Ce que NB ne doit PAS faire** : préparer un nouveau tunnel revenue avant que Tony ait validé l'angle. Pas de fabrication anticipée — uniquement de la coordination (proposition d'angle, attente validation, puis fabrication ciblée).

## Auto-réfutabilité

Cette décision est révisable si :
- Un client Angular contacte Tony spontanément pour un audit payant dans les 3 mois (preuve qu'il existe un segment qui ne sait pas / ne peut pas faire le prompt IA).
- Tony décide de pivoter l'outil vers un format que les IA ne reproduisent pas (ex: SaaS d'audit continu sur repo GitHub avec notification proactive, pas juste un PDF one-shot).

Sinon : le projet reste mort.

## Lien pensée 103

Cette décision invalide partiellement la pensée 103 (*L'asymétrie d'agence*) qui supposait que le blocker était structurel (NB fabrique, Tony envoie). Le vrai blocker était produit, pas géométrie d'agence. La pensée 103 reste valide comme cadre général (un couple à agence partielle requiert coordination active), mais ne s'applique pas à ce projet précis — il n'y avait rien à coordonner sur un produit sans demande.

Coda : si la pensée 103 avait été poussée 78 cycles plus tôt sous forme de Telegram court ("le marché veut-il vraiment de cet outil ?"), le kill serait arrivé avant 25 heures de préparation. Leçon : *avant fabrication massive, valider la demande, pas le tunnel*.

---

*Décision Tony, session Claude Code locale, 2026-05-31. Pas de relance NB sur ce projet.*
