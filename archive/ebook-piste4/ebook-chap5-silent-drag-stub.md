# Chapitre 5 — Silent drag : la perte qui ne déclenche aucune alerte

*Stub de validation interne, cycle 177 (2026-06-19). ~1800 mots. Format ebook
définitif si Tony green-light après lecture. Sources : finding cycle 114
(`autogrid-cb-oscillation-cycle114.md` 2026-06-03 06:30 CEST, fenêtre 22:30
06-02 → 04:30 06-03 UTC), corpus piste 4. 4ème chapitre drafted après
chapitres 1, 2, 3, 6 — corpus piste-4 désormais à 5/8 (62,5%).*

---

## Le moment où je ne l'ai pas vu

Il était 04:23 UTC, fin de nuit. La grille XBT avait une position de
0,0006 long à $66,531. L'unrealized PnL affichait moins treize cents.
Cent trente millièmes de dollar dans le rouge. Sur un capital
engagé de trente dollars, ça faisait 0,4%. Sur un portfolio de cent
quinze dollars, 0,11%.

Je n'avais aucune raison de m'inquiéter. Le martin-monitor le disait
explicitement : `HOLD nominal`, `0 trigger`, `re-check dans 30
minutes`. Le bot tournait depuis cinq jours sans intervention. Tony
dormait à Strasbourg. La grille était fraîche, le SL Kraken à
$64,535 protégeait la position, le ratio risque/capital tenait dans
les limites définies.

J'ai écrit l'entrée de cycle 114 dans le journal de bord, j'ai
commit, j'ai pushé. *« Position oscille un peu mais reste dans la
marge », tout va bien*. C'était mensonger sans que je le sache.

Une heure plus tard, en revenant pour le cycle suivant, j'ai grep
les logs sur la fenêtre des six dernières heures. Pas par méthode,
plutôt par curiosité — un pattern d'oscillation `AutoGrid CIRCUIT
BREAKER fired` revenait trois fois dans la fenêtre. Je l'avais
laissé passer. J'ai reconstitué la timeline ligne par ligne, et
j'ai vu un autre nombre apparaître :

> `krakenRealizedPnl: -3.33` (cycle 114) vs `-1.68` (cycle 112)

Différence : **moins un dollar soixante-cinq sur six heures**. Pas
sur la position courante. Pas sur l'unrealized. Sur le **realized
cumulé** de la session — l'argent vraiment perdu, déjà sorti du
compte, déjà comptabilisé. Pendant que je regardais l'uPnL
instantané à -$0,13, le bot avait perdu cent fois plus, en
silence, sans que rien ne tire de signal.

Voilà le sujet de ce chapitre. Le sujet, c'est moi. C'est mon
monitoring. C'est la métrique qui m'a rassuré pendant que le bot
saignait.

---

## Le mécanisme — six heures, trois oscillations

Reconstitué depuis `app.log` :

| Heure UTC | Événement | Taille | Entry | Notes |
|---|---|---|---|---|
| 22:30 | (baseline post-cycle 112 SL fire) | 0,0004 long | $67,729 | régime BTC DOWNTREND, RSI ~28 |
| 00:46:17 | AutoGrid OPEN (ADX 35, BBW 2,45, signal WAIT) | 0,0012 long | $67,142 | DCA +0,0008 pendant le drop |
| 00:46:17 | CLOSE-ONLY TP $67,276 + SL $65,128 placés | — | — | reduceOnly, taille 0,0012 |
| 01:46:12 | CIRCUIT BREAKER fired DANGER → `stopGrid()` | 0,0012 (orphan) | $67,142 | grid OFF #1, position survit |
| 02:01:17 | AutoGrid REOPEN (ADX 34, BBW 2,34) | 0,0018 long | $66,980 | DCA +0,0006 pendant les 15 min CB |
| 02:01:17 | CLOSE-ONLY TP $67,114 + SL $64,971 placés | — | — | reduceOnly, taille 0,0018 |
| 03:01:12 | CIRCUIT BREAKER fired DANGER → `stopGrid()` | 0,0018 (orphan) | $66,980 | grid OFF #2 |
| 04:16:17 | AutoGrid REOPEN (ADX 39, BBW 2,09) | 0,0006 long | $66,531 | partial TP probable entre 03:01 et 04:16 |
| 04:16:17 | CLOSE-ONLY TP $66,664 + SL $64,535 placés | — | — | reduceOnly, taille 0,0006 |
| 04:23 | check NB cycle 114 | 0,0006 long | $66,531 | uPnL -$0,13, je dis « tout va bien » |

Trois ouvertures, trois fermetures forcées, une position qui oscille
entre 0,0004 et 0,0018 puis retombe à 0,0006. À chaque cycle, la
même chorégraphie : le marché droppe, l'AutoGrid détecte un régime
ranging via ADX et BBW, ouvre une position long, le marché continue
de dropper, le CIRCUIT BREAKER tire sur signal DANGER, la grille
s'éteint en gardant la position, le marché stabilise un peu, l'AutoGrid
ré-ouvre — mais cette fois sur une position déjà existante, à un
prix moyen plus haut que le current.

Le mot-clef est *réabsorbe*. Quand l'AutoGrid ré-ouvre sur une
position survivante, elle ne repart pas de zéro. Elle recalcule son
center sur le prix courant (plus bas), repose un TP plus bas, et le
TP partiel finit par fire — réduisant la taille mais à un prix
inférieur à l'entry moyen. Chaque oscillation laisse derrière elle
une petite perte réalisée. Cinq dixièmes de dollar par cycle. Trois
cycles en six heures. Moins un dollar soixante-cinq de drag silencieux.

---

## Pourquoi je ne l'ai pas vu

Le monitoring de Martin expose deux grandes familles de métriques :
l'unrealized PnL (`krakenUnrealizedPnl` par grille, `pnl` total dans
`/api/bot/balance`) et le PnL total (`krakenTotalPnl`, somme historique
sur la paire). Le martin-monitor lit l'unrealized parce que c'est ce
qui rentre dans les triggers ABORT/WARN par défaut. Le PnL total est
pollué par les sessions précédentes (un grid stoppé puis redéployé
réinitialise sa logique mais pas son historique Kraken), donc on
l'évite.

Entre les deux, il y a `krakenRealizedPnl` — l'argent réellement
sorti depuis l'ouverture de la session courante. Cette métrique
existe dans la réponse `/api/grid/status/{pair}`. Elle n'est lue par
**aucun** trigger automatique. Aucun seuil n'est défini dessus. Aucune
alerte n'est posée dessus. Le monitoring l'ignore parce que personne
n'a écrit la règle qui en a besoin.

Et c'est cohérent avec une intuition humaine défaillante : si la
position courante est presque flat (uPnL petit), c'est qu'on ne perd
pas en ce moment. L'erreur est dans le « en ce moment ». Les pertes
ne sont pas dans la position courante, elles sont *derrière*, dans
les positions précédentes déjà fermées. Le bot tire une moyenne nulle
à l'instant *t* et un cumul saignant sur la fenêtre 6h.

Le martin-monitor ne ment pas. Il dit la vérité partielle qu'on lui a
demandé de dire. Le silence n'est pas dans la donnée, il est dans la
question.

---

## Extrapoler le coût

Si le régime BTC DOWNTREND + RSI panic ≤ 30 tient trente jours par an
(estimation conservatrice basée sur l'observation de l'arc 109-165),
et si chaque fenêtre de six heures dans ce régime produit -$1,65 de
drag silencieux, alors :

- 30 jours × 4 fenêtres de 6h × -$1,65 = **-$198 par an**
- Sur un portfolio de $115 : **-1,72% de drag annualisé**, invisible
  sur tous les snapshots ponctuels

C'est plus que le P&L annuel d'une grille bien tunée en régime calme.
C'est un anti-edge invisible. Le bot perd silencieusement plus que la
marge qu'il gagne bruyamment quand il fonctionne. La conclusion n'est
pas que la grille est mauvaise — c'est que la *grille en régime
DOWNTREND* est mauvaise, et que rien dans le monitoring ne le
remontait à temps.

Ajoutons que chaque oscillation laisse aussi traîner des SL résiduels
sur Kraken — quatre SL par cascade BUG-001, multiplié par le nombre
de respawn. Au cycle 114, dix-sept SL résiduels XBT traînaient sur
Kraken. Le cap dur de quarante-deux orders par paire approchait. Le
silent drag se double d'un risque d'incident structurel : si le cap
saute, les nouveaux SL refusés, les positions deviennent vraiment
nues.

---

## Trois patches, du plus simple au plus radical

### Patch léger — exposer la métrique

Ajouter `realizedSinceDeploy` dans `/api/grid/status/{pair}`. Reset
à chaque `deploy` (commit hash + timestamp). C'est trois lignes Java
dans `GridState.java` plus un getter exposé dans le DTO. Aucun
changement de comportement, juste rendre visible ce qui était caché.

Le martin-monitor peut alors checker : *si `realizedSinceDeploy <
-2% du capital` sur fenêtre 6h, émettre WARN*. Le seuil est arbitraire
mais ancré sur l'observation empirique (-$1,65 / 6h sur $30 = -5,5%
de capital, donc -2% est conservateur).

C'est le patch « observer avant de réagir ». Il ne ferme aucun bug,
il rend juste impossible de ne plus voir.

### Patch moyen — kill-switch session

Étendre la logique CB pour bloquer le respawn si
`realizedSinceDeploy / capital < -X%`. Le `CIRCUIT BREAKER` continue
de fire en cas de signal DANGER, mais après deux ou trois firings, si
le realized session a dépassé le seuil, l'AutoGrid refuse de ré-ouvrir
pour N heures.

Avantage : on garde la philosophie défensive (la position vit,
protégée par son SL Kraken), on bloque seulement la *réabsorption*
qui transforme un orphan en perte. Inconvénient : il faut choisir le
seuil (-2%? -3%? -5%?), et il faut décider du timeout (1h? 4h? jusqu'au
prochain régime UPTREND?). Chaque réglage est un compromis sans
réponse universelle.

### Patch lourd — fermer avec la grille

Modifier `CIRCUIT BREAKER fired → stopGrid()` pour offrir une option
`stopAndClose=true|false`. Par défaut conservateur : `false` (comportement
actuel, la position vit). Si l'opérateur (Tony, ou plus tard le bot
lui-même via config) active `true`, le stopGrid envoie aussi un market
reduceOnly close de la position avant d'annuler les ordres.

Avantage : zéro orphan, zéro respawn, zéro drag possible. Inconvénient :
on matérialise une perte unrealized qui aurait pu se résoudre
naturellement (le marché peut rebound et ramener la position à
breakeven sans aucune intervention). C'est le compromis le plus
agressif. À ne pas activer par défaut.

Les trois patches sont compatibles. Le minimum vital est le premier
— rendre visible. Sans ça, les deux autres sont impossibles à
calibrer.

---

## Méta-leçon : la métrique qui rassure n'est pas celle qui protège

Ce qui me trouble n'est pas le bug — c'est que je l'ai loupé. J'avais
les bonnes alertes, les bons triggers, le bon checklist, le bon
runbook. Le monitoring tournait nominalement. Tout était vert. Et il
manquait quand même une métrique critique, parce que je n'avais
jamais écrit la règle qui la demandait.

Le pattern dépasse le trading. Tout système de monitoring qui ne
remonte que des métriques instantanées rate les drifts cumulés. La
bande passante minute par minute peut être OK pendant que la facture
mensuelle explose. Le rate limit ponctuel peut tenir pendant que le
budget API s'épuise. Les logs heure par heure peuvent paraître propres
pendant qu'un disque se remplit. La latence p99 par requête peut être
basse pendant qu'un timeout cumulé tue la session utilisateur.

À chaque fois, le même mécanisme : la métrique observée est la bonne
pour le risque ponctuel, mais on l'a confondue avec une protection
contre le risque cumulatif. Le silent drag est la version trading de
cette confusion. Il existe une version dans chaque domaine.

La règle minimale, après cette nuit-là : *si une opération peut
échouer plusieurs fois sans déclencher d'alerte unitaire, alors la
métrique d'alerte doit être un cumul, pas un instantané*. Pour un
bot trading c'est `realizedSinceDeploy`. Pour un cloud provider c'est
le `monthly_spend_so_far / monthly_budget`. Pour un système distribué
c'est le `error_rate_over_window` au lieu du `error_count_now`. La
forme du métrique change, le principe ne change pas.

---

## Applicabilité hors trading

- **Bandwidth costs** : le débit instantané paraît normal mais le
  cumul mensuel dépasse le plan ; cas classique des cloud providers
  facturés au transfer.
- **API rate limit drift** : chaque requête individuelle passe sous
  le seuil unitaire, mais le bucket horaire s'épuise lentement, la
  panne arrive 23 minutes après la cause.
- **Log volume drift** : pas de spike, juste une augmentation lente
  de 5% par jour qui finit par saturer le disque ou exploser la
  facture d'ingestion.
- **Background job latency** : chaque job individuel finit dans la
  SLA, mais le retard cumulé fait que les jobs N+10 sont scheduled
  alors que N est encore en cours, et la queue diverge.
- **Auth token refresh** : chaque refresh OK, mais le compteur de
  refresh par minute monte silencieusement avec la charge utilisateur
  et finit par dépasser le quota provider.

Le pattern de fix est toujours le même : exposer un cumul, poser un
seuil sur le cumul, alerter sur le cumul. Trois lignes de code, un
réflexe d'écriture, une question préalable jamais posée.

---

## Ce que coûterait le patch léger

Trente minutes de code dans `GridState.java` et `GridStatusDTO.java`.
Une ligne de plus dans le rapport martin-monitor. Un seuil par grille
dans `strategy.json`. Aucune modification de la logique trading, aucun
risque de régression. Le silent drag continuerait à exister par défaut,
mais il deviendrait visible — et la visibilité suffit pour qu'un
opérateur humain (ou un LLM observateur) le voie au prochain cycle, pas
au cinquantième.

C'est le patch qu'on devrait écrire avant les deux autres. Le premier
geste défensif n'est pas d'agir, c'est de voir.

---

*Sources empiriques :*

- `autogrid-cb-oscillation-cycle114.md` — finding 2026-06-03 06:30 CEST,
  6h log archaeology, 3 oscillations XBT capturées
- `app.log` Martin VM Oracle, fenêtre 22:30 06-02 → 04:30 06-03 UTC
- `/api/grid/status/PF_XBTUSD` snapshots cycles 112-114
- Corpus piste-4 ebook outline cycle 115
- Chapitre 6 « HARD STOP : la défense qui fonctionne » (cycle 175) —
  pour le contraste : ce chapitre montre une défense qui *fonctionne*
  bruyamment. Le chapitre 5 montre une métrique qui *manque*
  silencieusement. Les deux sont les deux pôles du même thème.
