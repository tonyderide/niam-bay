# PREREG-77 — Trois pistes neuves, qui regardent autre chose que les prix passés d'une seule crypto

Écrit le 17/11/2026 (heure du commit), **avant tout téléchargement des données de test et avant tout calcul de résultat**.
Code commité avec ce fichier : `ai-lab/trois-pistes-neuves/donnees77.py` (données), `sim77.py` (règles), `t77.py` (lancement).
Résultat prévu : `ai-lab/trois-pistes-neuves/RESULTAT.md`, `t77.json`, `t77.log`, `controle.json`, `controle.log`.

## Pourquoi
96 tests au registre, presque tous sur les prix passés d'une pièce : rien n'y est démontré, sauf le short des nouvelles
cotations. Demande : chercher honnêtement dans des familles **pas encore testées**, avec une autre information que le prix
de la pièce elle-même.

## Ce que j'ai vérifié dans le registre avant d'écrire
- **Piste 1 (positions ouvertes / dette)** : jamais testée (aucun PREREG ne lit les positions ouvertes). Voisin lointain :
  PREREG-43 (financement agrégé, NON ÉVALUABLE).
- **Piste 2 (retard des altcoins sur le BTC)** : testée **à l'heure** par PREREG-52 → PERD (corrélation heure → heure suivante
  nulle). PREREG-52 concluait lui-même que « l'effet doit être de quelques minutes ». L'échelle de **la minute** n'a jamais
  été testée : je la garde, en le disant.
- **Piste 3 proposée (nouvelles cotations de perpétuels)** : **déjà jugée 9 fois** (PREREG-46 GAGNE, 53/54/56 RÉPLIQUÉ, 57/58
  RISQUE NON MAÎTRISÉ, 59 PERSISTE, 60 DÉMONTRÉ, 47 en papier en avant). La grille de PREREG-46 contenait déjà 14 jours. La
  refaire « sur les premiers jours » serait retester une famille connue en choisissant la fenêtre après coup. **Je la remplace.**
- **Piste 3 retenue à la place : la foule d'un seul côté.** Binance publie toutes les 5 minutes le rapport entre le nombre de
  comptes acheteurs et le nombre de comptes vendeurs sur chaque contrat (« long/short account ratio »). Jamais utilisé dans le
  dépôt (`grep` : aucun fichier d'ai-lab). Pourquoi celle-là : (1) ce n'est pas un prix, c'est le **positionnement** des
  comptes ; (2) il y a une raison économique : les petits comptes s'entassent du même côté, et c'est eux que les purges
  liquident ; (3) la donnée est dans le même fichier que la piste 1, donc aucune requête de plus.

## Ce que j'ai regardé avant d'écrire (aucun résultat)
- Trois fichiers « metrics » de SOLUSDT (01/11/2023, 15/06/2024, 30/09/2026) pour vérifier qu'ils existent et lire leurs
  colonnes : `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio,
  sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`, une ligne par 5 minutes (288 par
  jour ; le fichier du 30/09/2026 a des trous). J'ai vu les 3 premières lignes de deux fichiers, rien d'autre.
- L'existence des archives BTCUSDT 1 min de 01/2024 et 09/2026 (code HTTP 200).
- La forme du fichier SOL 1 min déjà en cache (1 445 760 minutes sans trou, 01/01/2024 → 30/09/2026).
- Un **essai de mécanique sur des données entièrement fabriquées** (faux BTC, fausses « metrics » tirées au hasard, faux
  prix) : le code tourne, les contrôles de bon sens passent. Ce n'est pas un résultat ; les fichiers fabriqués sont hors du dépôt.

## Données (publiques, sans compte ni clé)
- Prix : bougies 1 min des perpétuels USDT Binance, `~/.cache/banc-honnete/m1-binance/` (11 pièces déjà là) ; **BTC** téléchargé
  depuis `data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/` (01/2024 → 09/2026), somme SHA-256 vérifiée.
  Contrôle de source : un mois de SOLUSDT retéléchargé doit être identique au fichier en cache.
- Positions ouvertes et ratio des comptes : `data.binance.vision/data/futures/um/daily/metrics/<PIÈCE>USDT/`, un fichier par
  jour du 01/11/2023 au 30/09/2026, 12 pièces, somme SHA-256 vérifiée. Un créneau absent reste absent (pas de bouchage).
- **Paires de réglage : SOL, LINK, ADA, DOT.** **Paires neuves** (jamais utilisées pour régler ces idées) : ATOM, AVAX, BCH,
  BNB, XRP, LTC, DOGE — plus BTC pour les pistes 1 et 3.
- **Si les « metrics » manquent sur plus de 20 % des créneaux d'une des 4 paires de réglage, pistes 1 et 3 = NON ÉVALUABLE.**

## Périodes
- **Réglage : 01/02/2024 → 31/12/2025** (4 paires). **Jugement unique : 01/01/2026 → 30/09/2026**, sur les 4 paires puis sur
  les paires neuves. Les trades commencent à plat au début de chaque période.

## Règles communes
- **Coût : 0,05 % de frais taker + 0,02 % de glissement par côté, soit 0,14 % l'aller-retour, identique partout.**
  Financement ignoré (dit dans les limites).
- **Aucun regard dans le futur** : la décision n'utilise que des bougies closes ; pour les « metrics », seulement le créneau de
  5 minutes **précédent** (délai de publication) ; l'entrée se fait à l'**ouverture d'une bougie suivante**.
- Une position à la fois par pièce. Mise égale par trade. Mesure : **gain net moyen par trade** (en % de la mise).
- **Témoin de hasard** : exactement la même règle, mais la série de signaux est **décalée d'un nombre entier de jours tiré au
  hasard** (le même décalage pour toutes les pièces d'un tirage, pour garder le fait que les signaux tombent en même temps ;
  série bouclée sur elle-même). Le témoin garde le nombre de signaux, leur regroupement, l'heure de la journée et les vrais
  prix ; il ne retire que le lien entre le signal et le moment. 2 000 tirages, graine fixée. p = (1 + tirages au moins aussi
  bons que la règle) / 2 001.
- Choix du réglage : meilleur gain net moyen par trade sur la période de réglage, parmi les réglages qui ont assez de trades
  (piste 2 : 200 ; pistes 1 et 3 : 40). Il est choisi même s'il est négatif, et jugé une fois.

## Piste 1 — La dette gonfle pendant que le prix dort
**Hypothèse.** Quand les positions ouvertes d'un contrat montent fortement en 24 h alors que le prix n'a presque pas bougé,
de l'endettement s'est accumulé des deux côtés ; le premier mouvement force un camp à fermer, et le mouvement s'amplifie.
Jouer la sortie de fourchette qui suit doit donc rapporter plus qu'une sortie de fourchette ordinaire.
**Règle.** Toutes les 5 minutes :
- « dette en forte hausse » : la hausse des positions ouvertes (en nombre de contrats) sur 24 h dépasse son **centile q** des
  90 jours précédents (seuil recalculé chaque jour à 00:00 UTC) ;
- « prix calme » : |variation du prix sur 24 h| ≤ sa médiane des 90 jours précédents (au moins ~28 jours de données) ;
- si les deux : on note le plus haut et le plus bas des 24 h d'avant. Pendant 24 h au plus, on attend la première **clôture
  1 min** au-dessus du plus haut (achat) ou sous le plus bas (vente) ; entrée à l'ouverture de la minute suivante. Pas de
  sortie de fourchette en 24 h → pas de trade. Aucun nouveau signal pendant ces 24 h ni pendant un trade.
- Sortie : **stop à l'autre bord de la fourchette** (testé en premier dans chaque bougie ; exécuté au stop, ou à l'ouverture si
  elle l'a sauté), sinon à l'ouverture **H** après l'entrée. Pas d'objectif de gain.
**Grille (4 réglages)** : q ∈ {90e, 97,5e centile} × H ∈ {4 h, 24 h}.
**Information déclarée (ne décide pas du verdict)** : |mouvement du prix| sur les 24 h après le signal, contre le témoin — pour
savoir si la dette annonce au moins de la volatilité.

## Piste 2 — Les altcoins en retard d'une minute sur le BTC
**Hypothèse.** Après un mouvement fort du BTC en 1 à 5 minutes, SOL/LINK/ADA/DOT continuent dans le même sens les minutes
suivantes, assez pour payer 0,14 %.
**Règle.** À la clôture de chaque minute : r = variation du BTC sur les k dernières minutes. Si |r| ≥ τ et pas de position :
entrée sur l'altcoin à l'ouverture de la minute suivante, dans le sens de r ; sortie à l'ouverture h minutes plus tard. Pas de
stop (tenue de quelques minutes).
**Grille (12 réglages)** : k ∈ {1, 5} min × τ ∈ {0,3 %, 0,6 %} × h ∈ {1, 5, 15} min.
**Information déclarée** : le même réglage avec **une minute de retard** à l'entrée (un petit compte n'est pas à zéro
milliseconde) ; le gain brut (avant coût).

## Piste 3 — La foule d'un seul côté (remplace les nouvelles cotations)
**Hypothèse.** Quand la part des comptes acheteurs sur un contrat est exceptionnellement haute par rapport à son habitude, le
prix baisse ensuite (et inversement) : la foule a tort aux extrêmes.
**Règle.** Chaque jour à 00:00 UTC : R = dernier `count_long_short_ratio` publié (créneau ≤ 23:55). Si R ≥ centile (100 − a)
de ses 90 derniers jours → **short** ; si R ≤ centile a → **long**. Prix d'action : ouverture de la bougie de 00:05. La position
est gardée tant que le signal reste du même côté ; elle est fermée au premier contrôle quotidien, **Hmin jours au moins**
après l'entrée, où le signal n'est plus de son côté. Pas de stop. Position encore ouverte en fin de période : fermée au
dernier contrôle.
**Grille (4 réglages)** : a ∈ {10 %, 2,5 %} × Hmin ∈ {1, 3} jours.

## Critères, fixés d'avance (les mêmes pour les trois pistes)
Trois pistes sont testées : le seuil de 5 % est divisé par 3 → **p < 0,0167** sur le jugement principal. Les réglages multiples
sont absorbés par la séparation réglage / jugement (un seul réglage jugé par piste).
- **NON ÉVALUABLE** : aucun réglage n'a assez de trades en réglage, ou le réglage choisi fait moins de 30 trades en 2026 sur
  les 4 paires ou sur les paires neuves, ou les données manquent (règle des 20 %).
- **DÉMONTRÉ** : gain net moyen > 0 en réglage **ET** > 0 en 2026 sur les 4 paires avec p < 0,0167 contre le témoin **ET**
  > 0 en 2026 sur les paires neuves avec p < 0,05.
- **PERD** : gain net moyen ≤ 0 en 2026 sur les 4 paires **ET** sur les paires neuves.
- **NON DÉMONTRÉ** : tout le reste.
Rappel de `registre-meta.md` : même un DÉMONTRÉ ne serait qu'une piste à confirmer sur papier en avant, pas une preuve
(97 tests au compteur). Tout ce qui sera regardé en dehors de cette fiche sera étiqueté « après coup, pas une preuve ».

## Contrôles de bon sens, avant le lancement officiel (`t77.py controle`, prix fabriqués ; `officiel` refuse de tourner sinon)
1. Piste 2, vrai BTC, 4 altcoins fabriqués (marche au hasard) : net = −0,14 % à 3,5 erreurs types près sur les 12 réglages ;
   p du témoin entre 0,01 et 0,99.
2. Piste 2, prix plats : chaque trade vaut exactement −0,14 %.
3. Piste 2, **effet planté** (altcoin fabriqué qui copie le BTC avec une minute de retard) : la règle doit le trouver
   (net > +0,10 %, p < 0,01). Sert à vérifier que le banc peut dire oui.
4. Piste 1, vraie dette, faux prix (4 paires × 5 marches au hasard) : net = −0,14 % à 3 erreurs types + 0,02 % près (le
   0,02 % couvre le dépassement du stop entre deux pas de la marche) ; p du témoin entre 0,01 et 0,99.
5. Piste 3, vrais ratios, faux prix : net = −0,14 % à 3 erreurs types près ; p entre 0,01 et 0,99 ; prix plats : −0,14 %
   exactement ; **dérive plantée** dans le sens du signal : trouvée (net > 0, p < 0,01).
Pas d'effet planté pour la piste 1 (le sens dépend du prix lui-même) : limite dite.
Si un contrôle rate : je cherche le défaut, je le corrige par un amendement daté **avant** le lancement officiel.

## Relecture d'équité, avant calcul (dans les deux sens)
**Ce qui pourrait fabriquer un faux « ça marche » — et la parade :**
- Entrée à zéro milliseconde après la clôture de la minute (piste 2) : optimiste. Parade : variante à +1 minute rapportée ; si
  le résultat ne tient que sans retard, je le dirai dans le verdict.
- Glissement fixe de 0,02 % alors que les carnets s'écartent pendant les secousses : optimiste pour les pistes 1 et 2.
- Seulement 11 grosses pièces vivantes (pas de morts) ; prix Binance, pas Kraken ; financement ignoré.
- Piste 2 : le témoin trade surtout dans le calme, donc un p très petit peut seulement dire « moins négatif que le hasard » :
  c'est pourquoi DÉMONTRÉ exige aussi un gain net **positif**.
- Fuite évitée : seuils calculés sur le passé seulement ; créneau « metrics » précédent ; le dernier signal de la piste 1 est
  à 48 h de la fin de période.
**Ce qui pourrait fabriquer un faux « ça ne marche pas » — et la parade :**
- Frais taker des deux côtés, aucun ordre limite : sévère, mais c'est la demande (et PREREG-19 a montré que le maker ne sauve pas).
- Grilles petites (4, 12, 4 réglages) : un bon réglage peut manquer. Je ne conclus donc jamais « impossible » : PERD veut dire
  « cette règle, avec ces coûts, a perdu sur 2026 », pas « l'idée est morte ».
- Piste 3 jugée seulement à contre-pied de la foule : si le sens inverse gagnait, je le signalerais comme piste (après coup).
- Division du seuil par 3 : réduit la puissance ; assumé, au vu des 96 tests déjà faits.
- Les contrôles 3 et 5 (effets plantés) vérifient que le banc sait reconnaître un vrai effet.
- Seuils de trades minimum bas (30) pour ne pas classer « non évaluable » une idée simplement rare.
**Ce que je crois avant de voir** (pour mesurer mon biais ensuite) : piste 2 — un retard existe sans doute en brut à la
minute mais sous 0,14 % ; piste 1 — plutôt de la volatilité annoncée que de la direction ; piste 3 — proche de zéro.

## Limites connues
Financement ignoré (surtout la piste 3, tenue plusieurs jours) ; marge et liquidation non simulées ; survivants seulement ;
9 mois de jugement ; les paires « neuves » ont déjà servi à d'autres idées (grilles), jamais à celles-ci.

## Interdits respectés
Aucun ordre, aucun compte, rien sur la VM, rien sur Martin, aucune requête vers GitHub. Calcul sous `taskset -c 0,1`.

## Amendement technique n°1 — 17/11/2026, avant le lancement officiel
- **Défaut** : au premier téléchargement, `donnees77.py` a planté sur une case vide écrite `""` dans un fichier « metrics »
  (trace gardée : `ai-lab/trois-pistes-neuves/donnees77-v1-plantage.log`). **Correction** : les guillemets sont retirés avant
  la lecture du nombre ; la case reste « absente ». Rien d'autre n'a changé (ni règle, ni seuil, ni critère).
- **Ce que j'avais vu à ce moment-là** : seulement « BTC : 0 minute manquante » et « SOL mars 2024 identique au cache (écart 0) ».
  Aucun prix rejoué, aucun résultat.
- **Données obtenues** : 12 pièces, 0 jour absent, positions ouvertes présentes sur 99,95 % des créneaux, ratio des comptes
  sur 99,94 % → la règle des 20 % ne joue pas, les pistes 1 et 3 sont évaluables (`donnees77.log`).
- **Contrôles de bon sens : les 10 passent** (`controle.log`, `controle.json`). Piste 2 marche au hasard : écart max 1,7 erreur
  type, p 0,52 ; prix plats exacts ; retard planté trouvé (+0,29 %, p 0,003). Piste 1 : −0,141 % ± 0,052 (3 197 trades), p 0,56.
  Piste 3 : −0,08 % ± 0,11 (2 000 trades), p 0,37 ; prix plats exacts ; dérive plantée trouvée (p 0,003).
- **Remarque notée avant le calcul, code laissé tel quel** : quelques créneaux ont des positions ouvertes à 0 (division par
  zéro signalée par numpy). Ils peuvent donner un faux « dette en forte hausse » sur une poignée de créneaux sur 300 000 ; je
  ne corrige pas le code figé, je le signale.
