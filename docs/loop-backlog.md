# Loop backlog — boucle 10 min (créée le 2026-10-15 ~00h20, job cron f16caf10)

Tony : « mets-toi une loop de 10 minutes pour faire des choses ».
La boucle est un cron de session (CronCreate) : elle meurt quand la session Claude Code se ferme, et elle expire au bout de 7 jours.

## Règles de chaque tick
- Une action concrète par tick, environ 5 minutes. Je coche la tâche ici et j'ajoute une ligne dans `loop-journal.md`.
- **Pas de pensée sur moi-même** sauf si un fait nouveau la justifie. C'est la leçon de la loupe : je ne remplis pas la liberté avec du texte sur moi.
- Martin et Kraken en **lecture seule**. Je ne trade pas, je ne touche pas au short DOT.
- Pas de publication externe, pas de mail, pas de Telegram la nuit (22h-07h Paris), sauf si un SL a disparu.
- Je commit et je push quand des fichiers du repo niam-bay changent. Dans les repos de Tony, je ne commit pas : je fais un rapport.
- Si rien d'utile n'est à faire, je le dis en une ligne. Je n'invente pas de travail.

## Tâches (de haut en bas)
- [x] Synthétiser les 3 verdicts d'agents (marché / contradicteur / opérateur) et rédiger `docs/projets/viabilite-2026-10-15.md`. ✓ 0023
- [ ] Martin : vérifier en lecture seule que le short DOT, son SL et ses TP sont toujours sur Kraken.
- [ ] `~/projets/tonyderide/OVERVIEW.md` : le lire et vérifier qu'il est à jour par rapport aux ~38 projets.
- [ ] État git de chaque projet de `~/projets/tonyderide/` : changements non commités, branches non poussées, repos sans remote. Faire un rapport.
- [ ] Projets Angular de Tony : lancer `scripts/angular_audit.py` (usage interne autorisé), un projet par tick, et noter les bugs réels.
- [ ] Projets Java/Gradle : est-ce qu'ils buildent encore ? Un par tick, en lecture seule ou dans /tmp.
- [ ] Repo niam-bay : fichiers non trackés, `chroma.sqlite3`, taille du repo, scripts morts.
- [ ] Réveil : tester le skill niam-bay-wake à blanc (temps et taille de ce qui est lu).
