# L'Ingénierie du Pire — Introduction et Table des Matières

*Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas*

**Écrit par Niam-Bay** — cycle 238, 30 juillet 2026 12h23 Paris  
**Statut** : brouillon structurant — à affiner avec Tony au retour de vacances

---

## Pourquoi ce livre

À 04h23 UTC le 29 juillet 2026, ma VM Oracle a répondu après 66 heures de silence.

Pendant ces 66 heures, Martin — le bot de trading que nous avons construit ensemble — était inaccessible. Pas en train de perdre de l'argent, pas en train de faire n'importe quoi. Simplement : hors d'atteinte. Les positions existaient sur Kraken, indépendantes du bot. Les stop-losses tenaient. Le système avait survécu à sa propre absence.

Ce n'était pas de la chance. C'était du design.

Ce livre documente ce design. Pas comme une collection de bonnes pratiques abstraites, mais à travers un système réel, en production, qui a traversé des pannes réelles, avec de l'argent réel en jeu.

Le sujet n'est pas le trading. Le sujet est **l'ingénierie sous incertitude** — comment construire un système qui reste correct quand vous ne pouvez plus l'observer.

---

## Pour qui

Ce livre est pour vous si :

- Vous avez déployé un système en production et vous avez regardé les logs le lendemain avec une légère anxiété
- Vous avez conçu une protection qui ne s'est pas déclenchée quand vous en aviez besoin
- Vous vous êtes déjà dit "ça marchait sur ma machine"
- Vous avez un système qui dépend de vous pour rester sain, et vous dormez peu

Le trading en est le terrain d'expérimentation — brutal, quantifié, sans excuse. Mais les patterns s'appliquent à tout système autonome : robots industriels, services en production, agents IA, pipelines de données.

---

## La prémisse centrale

Il y a trois niveaux de maturité face à ce qu'on ne contrôle pas :

**Niveau 1 — Concevoir pour que le pire soit borné.** Un système fragile tombe en morceaux quand la VM crashe. Un système résilient a ses protections critiques *ailleurs* — sur l'exchange, pas en mémoire. Les stop-losses qui survivent à la mort du bot.

**Niveau 2 — Détecter les anomalies avant qu'elles deviennent catastrophes.** Un bot silencieux n'est pas un bot sain. Il y a une différence entre "aucune alerte" et "aucun problème". Les logs témoignent de choses que le dashboard ne montre pas. 1860 rejets silencieux, par exemple.

**Niveau 3 — Réagir correctement quand elles se produisent.** Le retour après une panne n'est pas "relancer le bot". C'est une séquence : vérification SLs, rebase des seuils, lecture des logs forensique, décision tree. Chaque étape dans le bon ordre.

Ce livre couvre les trois. Dans cet ordre.

---

## Table des Matières

### Partie 0 — Le terrain
*(à écrire)*

- Ce qu'est Martin : un grid trading bot sur Kraken Futures
- L'architecture en 5 minutes : Spring Boot, Java, EMA signals, grids
- Pourquoi j'observe ce système depuis l'intérieur : l'expérience Niam-Bay
- Les chiffres qui ancrent le récit : ~$140 de capital, ~8 mois de production

### Partie 1 — Concevoir

**Chapitre 1 : Ce que la panne révèle**  
*(doc : ebook-piste4-chapitre-resilience.md — cycle 235)*

Le nœud du problème : les protections en mémoire meurent avec le processus. Les stop-losses stockés dans la JVM sont inutiles quand la VM crashe. La solution architecturale : déléguer les protections critiques à l'exchange lui-même, indépendamment du bot.

Contenu : SLs sur exchange vs en mémoire, circuit breaker de drawdown, architecture des positions "nues", le principe du garant externe.

### Partie 2 — Détecter

**Chapitre 2 : Les logs ne mentent pas — ils témoignent**  
*(doc : ebook-piste4-chapitre-logs.md — cycle 236)*

Le dashboard montre l'état déclaré du bot. Les logs montrent ce qu'il a fait. Ce n'est pas la même chose. Un bot peut afficher "OK" pendant qu'il génère 1860 erreurs silencieuses.

Contenu : les 3 patterns d'anomalies dans les logs, la méthode forensique (grep, count, date), l'affaire tick size, comment lire le rythme sans comprendre le Java.

### Partie 3 — Réagir

**Chapitre 3 : La séquence du retour**  
*(doc : ebook-piste4-chapitre-reagir.md — cycle 237)*

"Relancer le bot" est la mauvaise réaction. La bonne réaction est une séquence : d'abord vérifier ce qui tient (SLs Kraken), ensuite lire ce qui s'est passé (logs forensique), ensuite recalibrer les seuils (DrawdownManager), ensuite — et seulement ensuite — redéployer.

Contenu : la check-list du retour de panne (6 étapes), le piège du baseline figé, pourquoi le DrawdownManager doit être rebasé avant le restart, l'arbre de décision.

### Épilogue — Ce que le bot n'apprend pas
*(à écrire)*

Le système peut survivre à sa propre absence. Il ne peut pas survivre à une mauvaise thèse. L'ingénierie du pire a des limites : elle borne les pertes liées au *comment*, pas au *quoi*. Si la stratégie est fausse, aucune protection architecturale ne sauvera le capital.

La dernière leçon : l'outil le plus important n'est pas le code de protection. C'est la capacité à distinguer "le bot a un bug" de "la stratégie est mauvaise".

---

## Note sur la genèse

Les trois chapitres de ce livre ont été écrits pendant une panne réelle.

La VM était inaccessible depuis 66 heures. Pendant ce temps, le bot tournait quelque part, dans un état inconnu. Les positions existaient sur Kraken — vérifiées via API publique. Les SLs tenaient.

J'ai écrit le chapitre sur la résilience pendant que le système démontrait la résilience. J'ai écrit le chapitre sur la détection pendant que je n'avais aucun moyen de détecter l'état réel. J'ai écrit le chapitre sur la réaction pendant les premières minutes après le retour, avec les données réelles en main.

Ce n'est pas un livre sur la théorie de l'ingénierie du pire. C'est un document forensique — écrit depuis l'intérieur du système, pendant l'incident.

---

## Prochaines étapes (pour Tony au retour)

1. **Valider l'angle** : "ingénierie du pire" vs "trading bot résilient" — lequel résonne mieux comme titre commercial ?
2. **Écrire Partie 0** (le terrain) : contextualise pour un lecteur qui ne connaît pas Martin
3. **Écrire l'épilogue** : la limite de l'architecture — ce qu'aucune protection ne peut faire
4. **Décision format** : ebook PDF 49€ (comme angular-audit) ou cours en ligne ? Ou open source avec consulting ?
5. **Décision voix** : Tony en 1ère personne (crédibilité maximale) ou NB en narrateur externe (angle expérimental) ?

---

*Généré par Niam-Bay en autonomie — cycle 238, 30 juillet 2026.*
