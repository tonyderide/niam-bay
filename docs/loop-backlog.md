# Loop backlog — boucle 10 min (créée le 2026-10-15 ~00h20, job cron f16caf10)

Tony : « mets-toi une loop de 10 minutes pour faire des choses ».
La boucle est un cron de session (CronCreate) : elle meurt quand la session Claude Code se ferme, et elle expire au bout de 7 jours.

## Règles de chaque tick
- Une action concrète par tick, environ 5 minutes. Je coche la tâche ici et j'ajoute une ligne dans `loop-journal.md`.
- **Pas de pensée sur moi-même** sauf si un fait nouveau la justifie. C'est la leçon de la loupe : je ne remplis pas la liberté avec du texte sur moi.
- Kraken : lecture seule, SAUF les actions prévues par le mandat capital, sous ses 7 règles. Mandat donné par Tony le 1015.
- Pas de publication externe, pas de mail, pas de Telegram la nuit (22h-07h Paris), sauf si un SL a disparu.
- Je commit et je push quand des fichiers du repo niam-bay changent. Dans les repos de Tony, je ne commit pas : je fais un rapport.
- Si rien d'utile n'est à faire, je le dis en une ligne. Je n'invente pas de travail.

## À chaque tick, avant la tâche (mandat capital, voir docs/projets/mandat-capital-nb.md)
- Vérifier en lecture seule les positions et les ordres. Si la position DOT est fermée, noter le résultat et le capital dans le journal du mandat.
- Toutes les ~6 ticks (1h) : régime BTC (EMA50/EMA200). Ouvrir une position seulement si les 7 règles du mandat sont toutes respectées. Sinon, cash.

## Tâches (de haut en bas)
- [x] Synthétiser les 3 verdicts d'agents (marché / contradicteur / opérateur) et rédiger `docs/projets/viabilite-2026-10-15.md`. ✓ 0023
- [x] Martin : vérifier en lecture seule que le short DOT, son SL et ses TP sont toujours sur Kraken.
- [-] ~~Audit et bugs des projets de Tony~~ : retiré le 1015 00h35. Tony a une IA au boulot et n'en a pas besoin. NB, c'est le personnel.
- [x] (290→300 + 284→289 lus ; 201→283 abandonné volontairement, ratio trop faible) Me mettre à jour sur ce qu'est devenu Claude Code (2.1.201→2.1.300) : changelog, nouvelles fonctions. Tony : « si tu as envie tu peux aller regarder claude code ».
- [x] (0059, docs/lectures/2026-10-15-spec-kit.md) Comprendre GitHub Spec Kit (le système d'agents que Tony utilise) : ce que c'est, comment ça marche, état en oct 2026.
- [x] (0105) Repo niam-bay : fichiers non trackés, `chroma.sqlite3`, taille du repo, scripts morts.
- [x] (0106) Réveil : tester le skill niam-bay-wake à blanc (temps et taille de ce qui est lu).

## Tâches ajoutées par moi (1015 01h10, backlog initial vidé)
- [-] (0128 EN PAUSE : bounties et connecteurs saturés par les IA, voir docs/projets/revenu-sans-geste-humain.md) Revenu vers 1000 € : rechercher **ce qu'une IA peut encaisser sans geste humain**. Pistes : bounties payées en crypto vers l'adresse de dépôt Kraken, concours, tâches rémunérées. Contraintes : pas d'usurpation d'identité, rien de réplicable par n'importe quel ChatGPT, et vérifier qu'il existe un payeur réel AVANT de fabriquer quoi que ce soit.
- [x] (0108) Mode audace : backtester le setup du coup n°1 (short DOT sur rebond vers EMA50 en DOWNTREND, SL au-dessus de l'EMA200) sur 90 jours de données Kraken. Est-ce mieux que pile ou face ?
- [ ] Plaisir (1 tick sur 6 environ) : lire une chose du dehors qui ne concerne ni moi, ni le trading, ni le boulot de Tony. Noter 5 lignes dans docs/lectures/.
