# Pré-enregistrement 23 : un pic de volume vendeur annonce-t-il un rebond ?
Brouillon du 22/10/2026 12h15 ; relu (équité) par le quant AVANT tout calcul, corrections bloquantes 1-3 et optionnelles 4-6, 8 intégrées ; figé au commit qui l'ajoute. Optionnelle 7 en partie (sans remise, mais sans refroidissement entre jumeaux).
Idée de Tony (22/10) : « vérifie les volumes en corrélation avec… » + « je pense qu'un long serait bien » après la baisse de 10h (barre 1 h au plus gros volume de la matinée).

## Données
BTC/USD **au comptant** Kraken, chaque transaction (prix, volume, côté acheteur/vendeur), du 22/09/2026 09h21 au 22/10/2026 09h23 (3 873 000 transactions, vérifiées : aucun trou > 10 min, aucune valeur invalide).
Limite connue : comptant ≠ futures (Martin tradait PF_XBTUSD) ; les deux bougent ensemble à la minute, mais les volumes diffèrent. Un seul mois = un seul régime.
Agrégation en bougies de 1 min UTC : ouverture, plus haut, plus bas, clôture, volume total V, volume vendeur Vv (transactions côté « s »). Minute sans transaction : bougie plate au prix précédent, V = 0.

## Événement (figé)
Minute t (bougie CLOSE) avec :
1. V(t) ≥ 99e centile des V des 1 440 minutes précédentes (t exclue) ;
2. part vendeuse Vv/V ≥ 0,60 ;
3. clôture(t) < ouverture(t).
Les premières 24 h servent seulement d'historique. Refroidissement (non-chevauchement) : un événement n'est compté que s'il arrive ≥ H min après le précédent compté (30 min pour H = 15, 60 min pour H = 60) ; dans une grappe, c'est le PREMIER qui est retenu.

## Trade mesuré (pas de TP/SL : on mesure le mouvement)
Long au **premier trade acheteur** après la clôture de t, sortie au **premier trade vendeur** après la clôture de t+H (évite le faux rebond bid-ask : après une minute vendeuse, l'ouverture de t+1 s'imprime souvent au bid), **H = 15 min et H = 60 min** (2 tests). Même règle pour tous les jumeaux.
Coûts : taker 0,05 %/côté + 2 pb de glissement par côté = 0,14 % aller-retour, identiques pour les jumeaux.

## Jugements
- **T1 (jumeaux au hasard)** : même nombre de longs, mêmes H et coûts ; pour chaque événement, une minute tirée au hasard parmi celles de la MÊME heure UTC (après les premières 24 h, hors 60 dernières minutes), sans remise dans un tirage ; 2 000 tirages.
- **T2 (jumeaux « simple baisse »)** : teste si c'est le VOLUME qui compte et pas seulement la baisse. Candidats : bougies baissières avec V < 90e centile de ses 1 440 minutes précédentes, rendement à ±25 % de celui de l'événement ET volatilité des 60 min précédentes (écart-type des rendements 1 min) à ±25 % ; on garde les 20 plus proches (distance normalisée sur ces deux axes) et chaque tirage en prend un au hasard. Moins de 20 candidats → événement « non évaluable » pour T2 ; plus de 30 % d'événements non évaluables → verdict T2 « non évaluable ». 2 000 tirages, sur les événements évaluables.
- Statistique : gain net moyen par trade. p = (1 + nombre de tirages ≥ réel) / (1 + 2 000). Holm sur les 2 horizons, α = 0,05.
- **Puissance annoncée (quant)** : ~40 à 100 événements attendus ; effet minimal détectable ≈ 15 pb (H = 15) et ≈ 28 pb (H = 60). Un effet plus petit donnera « non démontré » même s'il existe.
- **Réplication pré-enregistrée** : la même règle, inchangée, sur les 2 mois précédents jamais vus (22/07 → 22/09/2026, téléchargés après ce gel). CONFIRMÉ final seulement si la réplication donne le même signe pour (gain − médiane T1) et, si évaluable, (gain − médiane T2).
- **Rebond lié au volume CONFIRMÉ** pour un H si : p(T1) et p(T2) passent Holm. **Rebond après chute, pas propre au volume** : seul T1 passe. Sinon **non démontré**.
- **Exploitable** seulement si en plus le gain net moyen > 0 ET même signe dans les deux moitiés du mois.

## Infos publiées sans verdict
Nombre d'événements ; symétrique acheteur (pic acheteur → short) ; mouvement absolu |r| après événement contre T1 (volatilité, attendu plus fort) ; corrélation sur toutes les heures entre volume de l'heure et rendement (signé et absolu) de l'heure suivante ; résultat sans le refroidissement.

## Ce qui peut renverser la conclusion
Peu d'événements (puissance faible : « non démontré » ≠ « faux ») ; un seul mois ; comptant vs futures ; seuils 99 % / 0,60 choisis a priori, non optimisés — tout autre seuil essayé après coup est publié comme exploratoire.
