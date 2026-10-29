# Pré-enregistrement 28 : SL fixe au départ, puis trailing stop dès qu'on gagne
Écrit le 29/10/2026 à 15h2x, avant tout calcul de cette règle (les bougies de PREREG-24 refait sont déjà téléchargées, mais aucune simulation de cette règle n'a été faite). Demande de Tony : « si tu fais le calcul avec des stats, est-ce qu'on gagne ou perd en faisant un trailing SL et un SL fixe au départ et dès qu'on gagne un trailing SL ».

## Ce que dit la théorie, avant les données
Sur un prix sans tendance ni mémoire (marche aléatoire), **aucune règle de sortie ne change l'espérance** (théorème d'arrêt optionnel) : avant frais, l'espérance est nulle, et après frais elle est négative, d'environ 0,1 % par trade aller-retour. Un SL fixe suivi d'un trailing change la forme des résultats : beaucoup de petites pertes et quelques gros gains. Il ne change pas la moyenne. La règle ne peut gagner que si les prix ont plus de **tendance** (momentum) que le hasard, assez pour payer les frais. Le test mesure donc exactement cela.

## Données
Celles de ai-lab/dca-martingale/refait : Binance USDT-M, bougies 1 h, 253 perpétuels cotés au 01/01/2024, morts compris, chaque pièce étant coupée à son retrait (48 h figées). Réglage sur 2024-2025, jugement unique sur 01/01 → 30/09/2026. Contrôle sur bougies 5 min : BTC, ETH, SOL en 2026.

## Règle (sans levier, toujours en position, sans signal d'entrée)
- **Entrée :** à l'ouverture de la bougie qui suit la sortie précédente (taker 0,05 %). Deux versions jugées séparément : **long** et **short**.
- **SL fixe :** placé à s de l'entrée.
- **Activation :** dès que le prix dépasse l'entrée de a dans le bon sens (« dès qu'on gagne »). Le stop devient alors max(SL fixe, pic × (1 − t)) pour un long, et l'équivalent pour un short. Le pic est le plus haut des bougies **précédentes** depuis l'activation.
- **Sortie :** quand le prix touche le stop, au prix du stop, ou à l'ouverture si elle est déjà au-delà (taker).
- **Ordre pessimiste dans une bougie :** si la bougie touche à la fois le SL fixe et le seuil d'activation, c'est le SL qui joue.
- **Fin de période ou retrait :** sortie au dernier prix connu.
- **Résultat d'une pièce :** somme des rendements nets des trades, avec une mise constante.

## Réglages (tous rapportés)
- s ∈ {1, 2, 3, 5, 8} %
- t ∈ {0,5, 1, 2, 3, 5} %
- a ∈ {0,1 % (frais couverts), 1 %}

Cela fait 50 réglages par sens. Le réglage jugé pour chaque sens est celui qui a le meilleur rendement moyen sur 2024-2025, figé avant 2026. Choisir le meilleur favorise la stratégie, et c'est voulu.

## Témoins (2026, mêmes pièces, même réglage figé)
- **(a) Acheter et garder,** pour le long ; ne rien faire (0) pour le short.
- **(b) Hasard (test statistique) :** la même règle sur 200 versions mélangées de chaque pièce. Les bougies, avec leur forme relative à l'ouverture, sont tirées dans un ordre aléatoire. Cela garde la volatilité et détruit la tendance. La valeur p est la part des mélanges qui font aussi bien ou mieux que le vrai résultat.

## Verdict (par sens, 2026, réglage figé)
- **GAGNE** seulement si les quatre conditions sont réunies :
  1. rendement moyen > 0 ;
  2. meilleur que (a) ;
  3. p < 0,05 contre (b) ;
  4. gains bruts > frais payés, avec au moins 3 pièces gagnantes.
- **NON DÉMONTRÉ** si le rendement est > 0 sans tout le reste.
- **PERD** sinon.

Rapporté en plus : taux de trades gagnants, gain moyen et perte moyenne, nombre de trades, résultat de tous les réglages.

## Relecture d'équité, avant le calcul
- Les mêmes frais s'appliquent partout, et le témoin hasard les paie aussi.
- Le réglage le plus favorable est choisi.
- Les deux sens sont testés.
- Le témoin (b) ne pénalise pas la stratégie : il garde la volatilité, il enlève seulement la tendance.
- Seul biais connu contre la stratégie : la bougie ambiguë est comptée en SL. Il est contrôlé par les bougies de 5 min.

## Addendum A (29/10, 15h3x, avant calcul) : la règle exacte de Tony
Tony précise : « SL à 1 % et trailing SL à 0,5 % dès que tu as gagné plus de 1 % », « tu es en trade 100 % du temps », « tu passes de short à long entre chaque retournement », « 1 000 € en misant 10 € et en faisant une martingale ».
- Règle : s = 1 %, a = 1 %, t = 0,5 %, sans réglage à choisir. Deux variantes : (i) on inverse le sens après **chaque** sortie ; (ii) on l'inverse seulement après une perte.
- Données : BTCUSDT perpétuel, bougies **1 min**, du 01/2024 au 09/2026. À cette échelle, la bougie ambiguë est presque inexistante ; on la compte quand même en SL.
- Mise : « 10 € » = ce qu'on perd si le SL est touché (position de 1 000 €). Les frais sont de 0,05 % par côté, soit 0,1 mise par trade aller-retour. Martingale : la mise double après une perte et revient à 10 € après un gain. Si la mise suivante dépasse le capital restant, c'est la **ruine** (le capital restant est noté).
- Rapporté :
  - la part des fois où +1 % arrive avant −1 % ;
  - le gain moyen par trade, en mises ;
  - la part de départs (un par jour) qui finissent en perte et la part qui finissent ruinés, après 1 mois, 3 mois et 9 mois ;
  - le résultat sans martingale (mise fixe de 10 €).
- Verdict de l'addendum : **« ne peut pas perdre dans 90 % des cas »** est VRAI si au moins 90 % des départs de 3 mois finissent en gain. FAUX sinon.

## Addendum B (29/10, écrit avant calcul) : changement de sens après une perte, plusieurs pourcentages
Tony : « test après une perte changement de sens et essaie plusieurs pourcentages ».
- **Règle :** celle de l'addendum A, variante (ii). On garde le sens après un gain et on l'inverse après une perte.
- **Réglages :**
  - SL s ∈ {0,5, 1, 1,5, 2, 3, 5} % ;
  - activation a ∈ {0,5, 1, 1,5, 2, 3, 5} % ;
  - trailing t ∈ {0,25, 0,5, 1, 1,5, 2, 3} % avec t ≤ a.
  - Tous les réglages sont rapportés.
- **Données :** BTC 1 min. Le réglage est choisi sur 2024-2025 (meilleure espérance par trade, en mises), figé, puis jugé une seule fois sur 01/01 → 30/09/2026. Choisir le meilleur sur 2026 directement serait le piège des « 3 mois qui marchent ».
- **Témoin hasard :** 200 mélanges des minutes de 2026, qui gardent la volatilité et retirent la tendance. p = part des mélanges qui font aussi bien ou mieux.
- **Martingale du réglage figé :** 10 € / 1 000 €, départs quotidiens de 1, 3 et 9 mois, sur toute la période (comme dans l'addendum A).
- **Verdict B :**
  - **GAGNE** si, en 2026, l'espérance est > 0, les gains bruts sont > aux frais et p < 0,05.
  - **NON DÉMONTRÉ** si l'espérance est > 0 sans le reste.
  - **PERD** sinon.
  - « Ne peut pas perdre dans 90 % des cas » est VRAI si au moins 90 % des départs de 3 mois finissent en gain avec la martingale.

## Addendum C (29/10, écrit avant calcul) : chercher le réglage qui a le moins de chances de perdre
Tony : « le pourcentage de chance que cela plante : vérifie plusieurs possibilités afin d'avoir le pourcentage de chance le plus faible possible de perdre ».
- **Règle :** celle de l'addendum B, sens inversé après une perte, sur BTC 1 min.
- **Paramètres explorés :**
  - les 156 réglages (s, a, t) de l'addendum B ;
  - multiplicateur après une perte m ∈ {1 (pas de martingale), 1,5, 2, 3} ;
  - plafond k ∈ {2, 4, 6, ∞} : après k pertes d'affilée, on encaisse et la mise revient à la base ;
  - mise de base ∈ {2, 5, 10} € de risque sur 1 000 €.
  - Cela fait 7 488 combinaisons.
- **Contraintes :**
  - une position ne peut pas dépasser 10 × le capital du moment, sinon la mise est ramenée à ce maximum ;
  - si le capital tombe sous 50 €, c'est la ruine et on s'arrête.
- **Mesure :** P(perte) = part des départs quotidiens dont le capital, au bout de **3 mois**, est sous 1 000 €. Également rapportés : le résultat médian, le 5 % le pire et la part de ruines.
- **Choix et jugement :**
  - on choisit sur les départs de 2024-2025 (fenêtres finies avant le 01/01/2026) la combinaison de P(perte) minimale ;
  - en cas d'égalité, on prend le meilleur résultat médian, et seules les combinaisons avec un résultat médian > 0 sont candidates (sinon « ne jamais perdre » se réduirait à presque ne rien miser) ;
  - on la juge une seule fois sur les départs de 2026 (fenêtres de 3 mois finies au plus tard le 30/09/2026).
- **Mise en garde écrite d'avance :** les départs de 2026 se chevauchent. Ils ne valent qu'environ 3 fenêtres indépendantes de 3 mois, donc le chiffre de 2026 sera peu précis.
- **Verdict C :** « moins de 10 % de chances de perdre » est VRAI si P(perte) en 2026 est ≤ 10 % **et** si le 5 % le pire ne dépasse pas −20 %. Sinon FAUX.

## Addendum D (29/10, avant calcul) : la combinaison choisie en C, testée sur d'autres pièces
- **Combinaison figée par C :** SL 5 %, activation +1 %, trailing 1 %, ×3 après une perte, retour à la base après 4 pertes, mise de 10 €.
- **Test :** sans rien changer, sur ETHUSDT et SOLUSDT en bougies 1 min, du 01/2024 au 09/2026 (archives vérifiées SHA-256).
- **Mesure :** même P(perte à 3 mois) sur des départs quotidiens.
- **Rapporté en plus :** la pire série de pertes, le pire résultat à 3 mois et la pire baisse depuis un sommet sur un parcours continu.
- **Verdict D :** la combinaison « tient » si P(perte à 3 mois) ≤ 10 % sur ETH **et** sur SOL. Sinon, la réussite sur le BTC est attribuée à la chance du choix parmi 6 084 combinaisons.
