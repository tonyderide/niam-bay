# PREREG-76 — La grille actuelle, la grille « protection unique » et la martingale avec inversion : laquelle tient ?

Écrit le 17/11/2026 vers 02h45 (heure de Paris), **avant tout calcul de résultat**. Code commité avec ce fichier :
`ai-lab/grille-vs-martingale/sim76.py` (simulateurs), `t76.py` (lancement), `kraken1m.py` (bougies Kraken publiques).
Résultat prévu : `ai-lab/grille-vs-martingale/RESULTAT.md`, `t76.json`, `t76.log`, `fidelite.json`.

## Pourquoi
Sur les 5 premiers jours réels de la grille W5 (28 positions fermées, net ≈ −10 c), la protection posée quand la position **perd**
(risquer 3 % pour gagner 0,2 %) fait −21 c sur 8 positions ; celle posée quand la position **gagne** fait +11 c sur 20.
Tony pense par ailleurs que la martingale avec inversion (qui tourne sur DOGE) doit gagner. Cinq jours ne prouvent rien :
on rejoue les trois réglages sur 32 mois, minute par minute, avec des règles de décision écrites avant.

Famille relue avant d'écrire (registre) : PREREG-24, 28, 29, 30, 34, 67, 68, 69 à 75. À retenir : aucune martingale n'y est
démontrée ; W5 fait +881 € puis −245 € sur ses 4 paires et perd sur 6 paires neuves ; la pause de régime (W5P) y était pire que W5.

## Ce que j'ai lu avant d'écrire (aucun prix rejoué)
- Le code **réellement déployé** : jar `backend-retour-avril-d7ff867.jar` = commit `d7ff867` de la branche `retour-avril`
  (`AutoGridScheduler`, `GridTradingService`, `SignalService`). Le dépôt principal de Martin a une version différente, non déployée.
- Le journal de Martin du 14 au 17/11 (`app.log`, lecture seule) et les bilans quotidiens de la garde (11 → 16/11).
- La docstring et la logique de `martingale.py` (clés masquées, jamais affichées).
- Un essai de **mécanique** des simulateurs sur une marche au hasard fabriquée (200 000 minutes, aucun prix réel) : les
  fonctions tournent, la somme des positions fermées égale le gain final. Ce n'est pas un résultat.

Trois constats tirés du code et du journal, qui changent le modèle par rapport à PREREG-73/75 :
1. **La pause de régime est toujours active en réel.** La config dit « seuils 1000 », mais le planificateur garde ses seuils
   par défaut (ADX < 40 et largeur de Bollinger < 4 % sur 15 min) : le journal montre « REGIME SWITCH » 47 fois en 3 jours et
   des ouvertures seulement sous ces seuils. La grille réelle est donc proche de « W5P », pas de « W5 ».
2. **Notionnel par niveau = 2 × le capital de la paire** (capital/5 × levier 10), plafond 10 × le capital ; vrai stop quand la
   perte latente de la position dépasse 15 % du capital de la paire (fermeture au marché, pause 24 h).
3. **Le stop serré est à 0,6 %** sous le prix courant (constante `WINNING_SL_PCT = 0.006`, vérifiée dans le journal :
   74,03 → stop 73,59), pas 0,4 %. La protection est reposée dès que le côté **ou la taille** de la position change.

## Les trois bras (aucun paramètre choisi : tout vient du code en service)
Grille commune à A et B : centre = prix au démarrage, 5 niveaux à −1,5 / −0,5 / +0,5 / +1,5 / +2,5 écarts (écart 5 %),
achats sous le centre, ventes au-dessus, **niveaux à un coup** (la reprise est sautée, comme en réel), recentrage quand le
prix sort de ±2 écarts (position gardée). Toutes les 15 minutes : protection, disjoncteur (RSI14 1 h < 25 → grille arrêtée,
position et protection laissées), démarrage si régime calme, « fermeture seule » si régime agité avec position, arrêt si agité sans position.

- **A — la grille telle que Martin la joue.** Au passage des 15 minutes, si la position n'est pas (ou plus) protégée pour sa
  taille : si elle gagne (prix courant meilleur que le prix d'entrée moyen) → stop à 0,6 % du prix courant, objectif à 2,5 % du
  prix courant ; si elle perd → stop à 3 % du prix d'entrée, objectif à 0,2 % du prix d'entrée.
- **B — identique à A, sauf la branche « perd »**, qui reçoit le réglage de la branche « gagne » : stop à 0,6 % et objectif à
  2,5 %, **comptés depuis le prix courant au moment du passage**. Pourquoi ce prix-là (un seul choix) : c'est exactement la
  formule de la branche « gagne » (B revient à supprimer le « si ») ; et c'est le seul ancrage toujours valide — depuis le prix
  d'entrée, le stop d'une position perdante de plus de 0,6 % serait déjà dépassé, donc refusé ou exécuté tout de suite.
- **C — la martingale avec inversion de `martingale.py`** sur SOL, LINK, ADA, DOT : position de base 3 $ par paire, stop à
  −5 % de l'entrée, à +10 % stop suiveur à 1 % du meilleur prix (relevé une fois par minute), après une perte ×2 et sens
  inversé, après un gain ou 4 pertes d'affilée retour à 3 $ (sens gardé après un gain). Entrée au marché deux minutes après la
  sortie. Les deux sens de départ sont rapportés (C+ long, C− short) ; **critère principal = moyenne des deux**. L'arrêt
  « enveloppe de 4 $ » du script n'est pas appliqué : la ruine est mesurée à part, de la même façon pour tous les bras.
- **Références :** achat simple (3 $ par paire achetés au début et gardés) et « ne rien faire » (0).

Mises : A et B avec les capitaux réels (SOL 1,42 $, LINK 1,18 $, ADA 1,18 $, DOT 1,02 $ ; soit 2,0 à 2,8 $ de notionnel par
niveau) ; C avec 3 $ de base. Mises fixes, pas de réinvestissement, résultats en dollars. Les bras n'engagent pas les mêmes
sommes : je donne aussi le résultat par dollar échangé et le rapport gain / pire baisse.

## Règles de calcul, les mêmes pour les trois bras
- Bougies 1 minute. Dans une bougie, chemin **pessimiste pour la position tenue** : long → le bas d'abord, short → le haut
  d'abord. Le stop est donc toujours testé avant l'objectif. À plat : bas d'abord si la bougie monte, haut d'abord sinon.
- Frais Kraken : maker 0,02 % (ordres limites : niveaux de grille, objectifs), taker 0,05 % (stops, ordres au marché, niveau
  déjà dépassé à la pose).
- Stop exécuté à son prix, ou à l'ouverture de la minute si le prix l'a sauté. Pas de glissement en plus.
- **Financement ignoré** (les données ne l'ont pas), pour les trois bras. Arrondi des tailles aux lots Kraken ignoré dans le
  calcul officiel (appliqué dans le contrôle de fidélité). Marge et liquidation non simulées : C peut porter jusqu'à
  4 × 24 $ = 96 $ de positions sur un compte de 6,40 $ ; je le signale, la mesure de ruine en tient lieu.
- Simplifications connues du bras A/B : passage à la minute ronde du quart d'heure (le vrai passe 1 min 49 s après) ; une
  protection disparaît dès que la position est à zéro (en réel elle traîne jusqu'au passage suivant) ; prix et indicateurs
  calculés sur les bougies du contrat (le vrai bot lit le comptant Kraken pour ses signaux).

## Données et périodes
- Bougies 1 min **Binance** perpétuels USDT, 01/01/2024 → 30/09/2026 (les fichiers de PREREG-74/75, copiés dans
  `~/.cache/banc-honnete/m1-binance/`). Ce ne sont pas des prix Kraken.
- **Période officielle : 01/02/2024 → 30/09/2026** (32 mois ; janvier 2024 sert à chauffer les indicateurs). C'est toute la
  période disponible en minutes. Découpage par mois civil, et en deux moitiés : P1 = 02/2024 → 12/2025, P2 = 01 → 09/2026.
- **Paires jamais vues : ATOM, AVAX, BCH, BNB, XRP, LTC** (celles de PREREG-74/75 qui ont des bougies 1 min), capital 1,18 $
  chacune pour A/B, 3 $ pour C. Les 24 paires de PREREG-75 n'ont que des bougies 1 h : écartées (PREREG-75 a montré que la
  grille sur 1 h ne ressemble pas à la minute).
- DOGE : rapporté pour information seulement (c'est la paire réelle de la martingale).

## Mesures rapportées pour chaque bras
Total ; par paire ; par mois ; nombre de mois positifs ; pire mois ; pire baisse du portefeuille ($) ; pire série (plus longue
suite de positions perdantes d'affilée et sa somme) ; résultat par dollar échangé ; P1 et P2 ; 6 paires neuves ; témoin de hasard ;
et la **ruine** : départs chaque jour à 00h00 UTC, 90 jours, les 4 paires ensemble sur un compte de **6,40 $** ; ruine = le gain
cumulé (positions valorisées à chaque minute) touche −6,40 $. Fenêtres qui se chevauchent : c'est une fréquence, pas une
probabilité exacte. Calculée pour A, B, C+, C− et l'achat simple, de la même façon.

## Témoin de hasard
Comme PREREG-75 (`melange`) : pour chaque paire, les bougies 1 min sont permutées et la dérive moyenne retirée — la volatilité
reste, toute structure (tendance, retour, grappes) disparaît. 200 mélanges (graine 7600), mêmes règles, mêmes frais, 4 paires.
On en tire la médiane et l'intervalle 5 %–95 % de chaque bras et de l'écart B − A. Limite connue : le mélange casse aussi les
grappes de volatilité, donc le régime ADX/Bollinger s'y comporte autrement.

## Critères de décision (fixés ici)
**B contre A** (écart = B − A, sur les 4 paires, période officielle) :
- B1 : écart total > 0 ;
- B2 : B fait mieux que A dans au moins 22 mois sur 32 (une pièce équilibrée fait ça moins d'une fois sur 30) ;
- B3 : sur les 6 paires neuves, écart total > 0 et B mieux sur au moins 4 paires sur 6 ;
- B4 : écart > 0 sur P1 **et** sur P2.
Verdict : **« B BAT A »** si B1 à B4 ; **« B MIEUX SANS PREUVE »** si B1 et au moins deux des trois autres ; sinon **« NON DÉMONTRÉ »**.
L'écart B − A sous hasard est rapporté pour dire si l'avantage éventuel est mécanique (présent aussi sur prix mélangés) ou lié
aux prix réels ; il ne change pas le verdict. À part : « B gagne de l'argent » seulement si total B > 0, au-dessus du 95e
centile du hasard, et > 0 sur les 6 paires neuves. « B bat A » peut donc vouloir dire « B perd moins ».

**C (martingale)** — « **DÉMONTRÉ** » seulement si tout est vrai :
- C1 : total (moyenne des deux départs) > 0 ;
- C2 : chacun des deux départs > 0 ;
- C3 : au moins 20 mois positifs sur 32 (moyenne des deux départs) ;
- C4 : total au-dessus du 95e centile du témoin de hasard ;
- C5 : 6 paires neuves : total > 0 et au moins 4 paires positives sur 6 ;
- C6 : fréquence de ruine (compte de 6,40 $, 4 paires, 90 jours, moyenne des deux départs) < 5 % ;
- C7 : > 0 sur P1 et sur P2.
Sinon : « **NON DÉMONTRÉ** » (jamais « impossible »). Je précise alors lesquels des sept critères passent.
Comparaison entre bras (information, pas un verdict) : gain / pire baisse, et résultat par dollar échangé.

## Contrôle de fidélité (avant le calcul officiel ; ne regarde que 5 jours de novembre, hors période officielle)
Bougies 1 min Kraken Futures publiques (`kraken1m.py`, 01 → 17/11/2026), lots réels, passage à la minute 2 du quart d'heure.
- **A** rejoué du 11/11 22h45Z (déploiement de la config, grilles démarrées d'office) au 17/11 00h00Z. Réel à approcher :
  28 positions fermées depuis 23h12Z, net ≈ −10 c, 4 gros gains de 5–7 c, 3 grosses pertes de 6–9 c le 14/11 ; bilans
  quotidiens réels des grilles : 12/11 −6,6 c, 13/11 +16,8 c, 14/11 −25,1 c, 15/11 +2,6 c, 16/11 −0,5 c.
  **Fidèle si** : 14 à 56 positions fermées ; net entre −30 c et +10 c ; le pire jour est le 14/11 et il est négatif ; au moins
  2 gains de 4–8 c et au moins 2 pertes de 5–10 c.
- **C** sur DOGE, départ short, 3 $, ouverture le 10/11 à 17h40Z : **fidèle si** le premier coup rapporte entre +24 et +31 c
  et se ferme le 14/11 (réel : +57,8 c avec 6 $, soit ≈ +27,6 à +29 c pour 3 $).
Si un des deux échoue : je corrige le simulateur par un **amendement daté** dans ce fichier, commité avant le calcul
officiel, avec la trace de l'essai raté (`fidelite-v1.json`…). Je ne règle le simulateur que sur ces 5 jours, jamais sur la
période officielle.

## Relecture d'équité (faite avant de figer)
- Mêmes frais, même ordre pessimiste, même absence de financement et de glissement pour A, B, C.
- **Pour la martingale** : je ne lui applique ni l'enveloppe de 4 $ ni un arrêt « compte vide » dans le moteur ; elle joue
  toute la période dans les deux sens. Son stop suiveur est relevé une fois par minute, comme le vrai script (ni mieux ni pire).
  Elle paie le taker à l'entrée et à la sortie parce que le script fait ainsi ; la grille paie surtout le maker parce qu'elle
  pose des limites : c'est la réalité des deux, pas un handicap ajouté.
- **Contre la martingale, rien de caché non plus** : la ruine est mesurée pour tous les bras ; le témoin de hasard aussi.
  Le critère C4 (battre le hasard) est exigeant, mais c'est celui de PREREG-75 ; B n'a pas à le passer pour « battre A » parce
  que la question posée n'est pas la même (« mieux que A » contre « gagne vraiment »), et je l'exige de B pour « B gagne de l'argent ».
- Mon biais connu est de noircir la martingale ; celui de Tony est de la croire gagnante. Les seuils ci-dessus tranchent, pas moi.
- Mises inégales (C engage plus) : signalé, et corrigé par les mesures par dollar échangé et gain / pire baisse.

## Prédictions (avant calcul)
- B − A : positif sur le total (la branche « perd » risque 15 fois son gain), mais B plus de frais taker ; je prédis
  « B MIEUX SANS PREUVE », probabilité 50 % ; « B BAT A » 20 % ; « NON DÉMONTRÉ » 30 %.
- A et B : total négatif tous les deux (70 %).
- C : « NON DÉMONTRÉ » (90 %) ; total moyen négatif (65 %) ; fréquence de ruine au-dessus de 5 % (75 %).

## Note du 17/11/2026, 02h30 (heure de Paris) — avant le calcul officiel
- Correction d'horloge : ce fichier a été commité à 02h25 (commit `934b074a`), pas « vers 02h45 ».
- **Contrôle de fidélité passé du premier coup, simulateur inchangé, aucun amendement** (`ai-lab/grille-vs-martingale/fidelite.log`, `fidelite.json`) :
  - A : 26 positions fermées (réel 28), net −10,3 c (réel ≈ −10 c), pire jour le 14/11 à −22,6 c (réel −25,1 c) avec trois stops
    de −6,2 / −7,4 / −8,6 c (réel : 3 pertes de 6–9 c), 3 gains de 5,3 à 7,2 c (réel : 4 de 5–7 c). Branche « perd » : −18,7 c sur
    12 (réel −21 c sur 8) ; branche « gagne » : +8,4 c sur 14 (réel +11 c sur 20). Jour par jour, l'accord est moins bon
    (13/11 : −1,4 c simulé contre +16,8 c réel ; 16/11 : +11,9 c contre −0,5 c) : les gros gains ne tombent pas les mêmes jours.
  - C : DOGE short 3 $ ouvert le 10/11 17h40Z, fermé le 14/11 17h23Z à +29,4 c (réel : fermé à 17h24Z, +57,8 c pour 6 $).
- Le bras B a été rejoué sur les mêmes 5 jours par le même script (dans `fidelite.json`, clé `B_info`) ; je ne l'ai pas regardé.
  Cinq jours ne sont de toute façon pas une preuve.
