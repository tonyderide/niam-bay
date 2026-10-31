# Pré-enregistrement 35 : la règle d'inversion journalière, en papier EN AVANT (01/11/2026 → 30/04/2027)
Écrit le 31/10/2026 vers 17h30 CET, avant le premier jour de données (la période commence le 01/11/2026 à 00:00 UTC = 01h00 CET). Demande de Tony du 31/10 : « continue de chercher la meilleure stratégie ».

## Pourquoi
PREREG-32 : en bougies journalières, l'inversion après perte, réglage figé sur 2024-25 (SL 15 % / activation +5 % / trailing 3 %), fait **+8,6 % en 2026, p = 0,007** contre le sens au hasard, mais **−29,2 % en 2024-25** (pire que le hasard, p = 0,88). Verdict NON DÉMONTRÉ. Un avantage qui change de période selon l'échelle ressemble à du bruit de régime. Le seul juge que le choix de période ne peut pas tromper : des jours qui n'existent pas encore.

## Ce que dit la théorie, avant les données
Sur une marche aléatoire, aucune règle de sortie ni d'inversion ne crée d'espérance (théorème d'arrêt optionnel) : la règle ne peut gagner que si les prix journaliers ont de l'autocorrélation (tendance) que « garder le sens après un gain » capterait. Prior honnête : **plutôt NON DÉMONTRÉ ou PERD**. Puissance faible (10 pièces, ~6 mois, ~15-35 trades par pièce) : seul un avantage gros (de l'ordre de celui de 2026) peut passer le seuil.

## Règle (figée, aucun réglage)
- Exactement la variante (i) de PREREG-32 : toujours en position ; entrée à l'ouverture du jour UTC qui suit la sortie ; SL fixe 15 % ; dès que le prix dépasse l'entrée de 5 % dans le bon sens, stop = max(SL, pic × (1 − 3 %)) (symétrique en short), pic = extrême des jours précédents depuis l'activation ; sortie au prix du stop (ou à l'ouverture si elle est déjà au-delà) ; **jour ambigu = SL d'abord** ; on garde le sens après un gain, on l'inverse après une perte (trade net ≤ 0) ; premier trade : long, à l'ouverture du 01/11/2026.
- Frais taker 0,05 % par côté, sans levier, mise égale constante par pièce (non composée), **sans funding** (même convention que PREREG-32).
- Code : `papier-inversion/papier.py`, fonction `chaine` = transcription ligne à ligne de `t32.py`. Vérifié avant ce commit : sur les 10 pièces du panier en 2026 (données historiques de PREREG-32), les trades de `papier.py` et de `t32.py` sont identiques (10/10 pièces, mêmes trades, mêmes rendements). Transparence : cette vérification a affiché les résultats 2026 par pièce du panier (moyenne ≈ +3,8 %) ; **la liste du panier était déjà écrite dans papier.py avant**, et ces résultats passés ne touchent pas la période jugée.

## Panier (fixé ici)
BTC, ETH, SOL, XRP, BNB, DOGE, ADA, LINK, AVAX, LTC — perpétuels USDT-M de Binance. Choix : les grandes capitalisations historiques non stables, toutes présentes dans le panier de PREREG-32, choisies pour la liquidité, **pas** sur leurs résultats. Une pièce retirée de la cote garde ses gains/pertes et reste au dénominateur (sortie au dernier prix connu).

## Données et journal
- Prix publics seulement : `https://fapi.binance.com/fapi/v1/klines?interval=1d` (sans clé, sans compte). Bougies journalières UTC **terminées** uniquement, gardées dans `papier-inversion/donnees/`.
- Cron local chaque jour à 03h17 (heure de Paris) : `papier.py` recalcule tout depuis le 01/11 (sans état, donc un jour manqué est rattrapé), ajoute une ligne à `papier-inversion/journal.md` et commite localement le journal et les données. Aucun ordre, aucune action sur Martin ni Kraken.
- Le journal montre chaque jour le net du panier (trades fermés, et avec la position latente) et l'acheter-garder du panier, **pour information** : rien n'est décidé avant la fin.

## Jugement (UNIQUE, le 01/05/2027 ou après : `papier.py juger`)
- Période : jours UTC du 01/11/2026 au 30/04/2027 inclus (181 jours). Position encore ouverte le 30/04 : sortie à la clôture de ce jour.
- Net du panier = moyenne des 10 pièces de la somme des rendements nets de leurs trades.
- **Témoin** : même règle de sortie, mêmes frais, mêmes jours, sens de chaque trade au hasard avec P(long) = part de longs de la règle sur la pièce ; 1 000 tirages (graine 35). p = part des tirages dont le net du panier est ≥ celui de la règle.
- **GAGNE** si net du panier > 0 **ET** p < 0,05. **NON DÉMONTRÉ** si net > 0 sans p < 0,05. **PERD** sinon.
- Rapporté en plus (sans changer le verdict) : acheter-garder du panier, net par pièce, nombre de trades, contrôle du jour ambigu sur bougies 1 h si les données sont récupérables.
- Aucune prolongation, aucun changement de réglage ni de panier en cours de route. Si le cron casse plus de 30 jours d'affilée sans rattrapage possible des données publiques : NON ÉVALUABLE.

## Relecture d'équité, avant le premier jour
- Rien n'est choisi : réglage, panier, période, critère et témoin sont fixés ici. Le choix du réglage sur 2024-25 (PREREG-32) est hors période.
- Le témoin garde la volatilité et les frais, retire seulement l'information de sens.
- Le jour ambigu compté en SL pénalise la règle et le témoin à égalité.
- Les frais réels d'un compte (taker 0,05 %) sont ceux de PREREG-32 ; funding non compté (il ne changeait aucun signe en PREREG-32, il sera rapporté si les données publiques le permettent).
