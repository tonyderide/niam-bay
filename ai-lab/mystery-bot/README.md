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
