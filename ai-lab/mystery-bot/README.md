# Le bot mystère : reverse engineering d'un trader inconnu à partir de ses seuls ordres (commencé le 17/10/2026)

## Qui passe ces ordres ? Ce qui est établi
- **Ce n'est pas la VM Oracle.** Aucun process n'y passe d'ordres privés. Seul Martin (java) parle à Kraken, et ses logs ne contiennent ni ces ordres ni ces prix. gateway.py ne lit que le ticker public. auto_scalp.py ne trade que l'ETH et plante depuis des semaines.
- **Ce n'est pas le NB du cron 6h.** Ses réveils ont lieu à 04:23, 10:23, 16:23 et 22:23 UTC, son log dit « 0 trade » à chaque fois, et le 1er short DOT a été rempli à 02:2x UTC.
- **Les fills n'ont aucun `cliOrdId`.** C'est typique des ordres passés à la main dans l'interface Kraken (appli ou web). Ce n'est pas une preuve.
- **Mais le 15/10 entre 02:24 et 02:35 UTC**, on a eu buy 11,1 @1,0804, puis sell 11,0 @1,094, puis buy @1,0804, puis sell @1,094, tous en **maker**. C'est le motif d'une grid à deux niveaux qui se rechargent, ou de limites posées à l'avance.

## Signature déjà observée (3 positions)
- SL ≈ **+3,0 à +3,2 %** au-dessus de l'entrée (shorts).
- 2 TP à ≈ **−1,6/−1,8 %** et **−2,9/−3,0 %**, chacun sur la moitié de la position.
- Après le TP1 : TP2 annulé et SL abaissé (stop suiveur).
- Ajout à une position gagnante, puis SL resserré. Ou au contraire SL élargi la nuit (vu deux fois).

## Le juge (le principe)
On ne juge pas le PROFIT, parce que le marché change et ce juge-là ment. On juge le COMPORTEMENT : pour chaque nouvelle position, je prédis le SL et les TP *avant* qu'ils soient posés, et je compare.

## Données
`record.sh` tourne sur la VM toutes les minutes. Il écrit une photo complète (positions + ordres) dans ~/et/snapshots.jsonl, **uniquement quand l'état change**.

## 🎯 RÉSOLU (17/10 vers 02h00) : c'est un 2ᵉ Martin, en local sur le PC pop-os
- Process : `java -jar /home/tony/martin-local/backend.jar` (pid 1223), démarré avec le PC le 14/10 à 22:50 via le **service systemd utilisateur `martin-local.service`** (enabled).
- Config `~/martin-local/config/strategy.json` : **autoGrid enabled**, 4 grids actives (SOL, LINK, ADA, DOT), 20 $ chacune, levier 3.
  Le commentaire de run.sh dit « posture verrouillée (0 grid, autoGrid OFF) », ce qui est faux aujourd'hui.
- Ses logs contiennent les ordres mystères : « Grid recentered [SHORT] … Grid order placed: PF_DOTUSD sell lmt @ 1.0804 size=11.1 / @ 1.094 size=11.0 », plus des « insufficientAvailableFunds » sur les niveaux suivants (le compte n'a que ~3,5 $).
- Pourquoi les fills n'avaient pas de cliOrdId : c'est le client Java de Martin qui n'en met pas, ce n'était pas l'interface Kraken. Mon hypothèse « ordres manuels » était **fausse**.
- Il y a donc **deux Martin sur le même compte Kraken** : celui de la VM (0 grid, en sommeil) et celui du PC (grids actives). Celui de la VM ne voit pas les grids de l'autre.
**Leçon de reverse engineering** : le « bot mystère » avait une signature (SL ~+3 %, 2 TP, recentrage) parce que c'est un **grid bot à niveaux espacés de façon fixe**. Je n'ai pas eu besoin d'inférer ses règles. Il suffisait de chercher sur la bonne machine.

## Analyse : ce que j'avais déduit, confronté à ses logs et à sa config (17/10 vers 02h10)
Période du 14/10 22h au 17/10 01h55. ~/martin-local/logs/martin.log comparé à config/strategy.json.

| ce que j'avais déduit (à partir des ordres seuls) | ce que disent les logs et la config | verdict |
|---|---|---|
| « 2 TP à −1,6/−1,8 % et −2,9/−3 % » | ce sont les **niveaux de la grid**, espacés de 1,21 à 1,27 % (config `gridSpacingPct` 1,2), en mode **SHORT** | ✅ les chiffres sont justes, ❌ **le sens est faux** : ce n'étaient pas des TP, c'étaient des niveaux d'achat de la grid |
| « stop suiveur après le TP1 » | ce sont des **recentrages** de grid (14 en 2 jours) : quand le prix sort de la plage, la grid se recalcule et ses ordres bougent | ❌ fausse interprétation |
| « SL ≈ +3 % » | SL posés ou reposés **483 fois** en 2 jours, une rotation constante liée aux recentrages et aux synchros | ✅ la distance est plausible, mais le mécanisme est inconnu |
| « bot qui renforce en profit » | la grid **revend** au niveau supérieur après un achat, c'est la mécanique normale d'une grid | ❌ ce n'est pas une décision, c'est la grid |

**Ce que les logs révèlent en plus, que les ordres seuls ne montraient pas :**
- **82 ordres sur 111 ont échoué (74 %)**, dont 80 pour `insufficientAvailableFunds`. La grid, configurée pour 5 niveaux × 20 $, ne posait qu'un ou deux niveaux sur un compte de 3 $. Ce n'était pas la stratégie configurée, c'en était une version mutilée.
- **1 112 « Deploy refused »** : la grid LINK, en mode LONG, est refusée toutes les 15 minutes par le filtre de régime BTC. Le garde-fou marche, mais il remplit le log.
- 205 vérifications AutoGrid, 10 démarrages de grid.

**La leçon de reverse engineering :** déduire à partir des ordres seuls m'a donné **les bons chiffres et les mauvaises explications**. J'avais vu des « TP » et un « stop suiveur » là où il n'y avait qu'une grid qui se recentre. Il faut donc juger une interprétation, et pas seulement un chiffre. Le seul moyen, c'est d'avoir un second juge : ici les logs et la config. Sans eux, j'aurais cru avoir compris le bot.
