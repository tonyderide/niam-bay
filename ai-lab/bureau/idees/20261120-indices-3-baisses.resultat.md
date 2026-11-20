# Acheter un indice après 3 séances de baisse, revendre 5 séances plus tard

Traduction : long = `baisse_suite(3)` · short = `None` · sortie = `{"max_bougies": 5}`
Marchés : QQQ, SPY, IWM, DIA, EFA, EEM (actions) · bougies 1d · frais 0,05 % par côté · pré-enregistrée : commit 13744990 du 20/11/2026 18:50

| Période | Trades | Somme | Hasard médiane | Hasard 95e | Rang | Marchés > 0 | Achat-conservation | Temps investi | Pire trade |
|---|---|---|---|---|---|---|---|---|---|
| 2005-2015 | 762 | +229,7 % | +67,8 % | +352,7 % | 84e | 5/6 | +108,3 % | 28 % | -10,9 % |
| 2016-2026 | 728 | +161,5 % | +138,3 % | +377,8 % | 56e | 6/6 | +280,2 % | 27 % | -22,2 % |

2005-2015 par marché : QQQ 130 trades +90,8 % (58% gagnants) · SPY 124 trades +25,9 % (54% gagnants) · IWM 137 trades +86,7 % (59% gagnants) · DIA 118 trades +9,5 % (52% gagnants) · EFA 124 trades -3,6 % (52% gagnants) · EEM 129 trades +20,4 % (50% gagnants)
2016-2026 par marché : QQQ 109 trades +16,5 % (54% gagnants) · SPY 121 trades +27,5 % (59% gagnants) · IWM 125 trades +39,7 % (55% gagnants) · DIA 124 trades +27,8 % (56% gagnants) · EFA 122 trades +23,8 % (58% gagnants) · EEM 127 trades +26,2 % (48% gagnants)

VERDICT : NON DÉMONTRÉ — 2005-2015 : pas au-dessus du hasard (84e centile, 95e requis) ; 2016-2026 : pas au-dessus du hasard (56e centile, 95e requis)

Lecture : « somme » = addition des rendements nets de chaque trade, mise égale, tous marchés. « Achat-conservation » = acheter au début et ne rien faire (moyenne des marchés), pour information.
Réserves : cours ajustés des dividendes. Un GAGNE ici n'autorise aucun ordre réel : il ouvre seulement un essai sur papier.
Relecture d'équité (écrite avant le calcul) : Pour l'idée : les six marchés montent et baissent souvent ensemble, donc « 4 marchés positifs sur 6 » est plus facile à obtenir qu'avec des marchés indépendants. Contre l'idée : frais de 0,05 % par côté, un peu élevés pour ces fonds très liquides. Neutre : la hausse de fond des actions profite aussi au témoin, qui achète au hasard et garde aussi longtemps.
