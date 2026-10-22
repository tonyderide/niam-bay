# Pré-enregistrement 11 : le déséquilibre du carnet d'ordres (scalping « comme les pros »)
Écrit et commité le 21/10/2026 à 23h53 (Paris, heure du commit), AVANT d'avoir regardé une seule donnée du carnet.

## Pourquoi
Tony : « apprends à scalper avec 10 scalpeurs pros ». Les familles 07-08 (bougies + frais taker) ont échoué : les frais mangent tout. Les vrais scalpeurs ont deux choses que je n'ai jamais testées : (1) le carnet d'ordres en direct, (2) les ordres limites (frais maker 0,02 % au lieu de 0,05 %). Référence : Cont, Kukanov & Stoikov (2014), « The Price Impact of Order Book Events » : le déséquilibre des ordres prédit le prix à très court terme.

## Données
PF_XBTUSD, carnet public Kraken Futures, 10 meilleurs niveaux de chaque côté, un instantané toutes les 2 s, enregistré sur la VM du 21/10 21h52 UTC (23h52 Paris) pendant 9 h, donc jusqu'à ~08h52 Paris (`~/nb/carnet/`). Première moitié (dans le temps) = réglage ; seconde moitié = jugement unique.

## Signal
I = (somme des quantités des 5 meilleurs bids − somme des 5 meilleurs asks) / (somme des deux). Horizon H = 10 s. Mouvement futur = (mid(t+H) − mid(t)) / mid(t).

## Stratégie testée
Quand I > +θ : long ; quand I < −θ : short ; sortie à t+H. θ choisi sur la 1re moitié parmi {0,3 ; 0,5 ; 0,7 ; 0,9} (le meilleur gain net), puis figé.
Coûts : HYPOTHÈSE OPTIMISTE « tout en maker » = 0,04 % aller-retour (0,02 % × 2), entrée et sortie au mid. C'est un plafond : en vrai, un ordre limite n'est pas toujours exécuté, et quand il l'est, c'est souvent contre toi (sélection adverse). Version réaliste aussi affichée : maker en entrée + taker en sortie = 0,07 %.

## Témoin au hasard
500 tirages : mêmes instants d'entrée, sens tiré au hasard, mêmes coûts. Rang de la stratégie parmi eux.

## Verdict (seconde moitié uniquement)
**GAGNE** seulement si, avec les coûts optimistes à 0,04 % : gain net total > 0 ET rang > p95 du témoin ET au moins 200 trades.
Sinon ÉCHEC. Si ça ne gagne qu'avec les coûts optimistes et perd à 0,07 %, je le dirai : ça voudrait dire « possible seulement avec des ordres limites vraiment exécutés », à tester ensuite en papier.
Je n'ajoute ni filtre, ni autre horizon, ni autre crypto après coup. Si ça échoue, c'est noté tel quel.

(Correction du 21/10 23h59 : seules les heures ont été rectifiées, j'avais daté sans lancer `date`. Le protocole lui-même n'a pas changé.)

## Précisions avant jugement (22/10/2026 ~22h, relecture d'équité du scalpeur, AVANT tout calcul sur la seconde moitié)
Le scalpeur n'a lu que la 1re moitié (format). Constat : |mouvement du mid à 10 s| moyen ≈ 1,27 pb < 4 pb de coût optimiste ⇒ même un devin parfait perd ; le verdict argent ne peut donc rien dire du carnet lui-même. Ajouts, sans changer signal, horizon ni seuils :
1. **Info (deux moitiés)** : plafond du devin = moyenne |mouvement| − coût. **2e verdict, sans argent** : taux de bon sens de signe(I) (mouvements nuls exclus) contre le même témoin (mêmes instants, sens au hasard, 500 tirages) ; « prédit le sens » si > p95.
2. Un seul trade à la fois : sortie au 1er instantané ≥ t+10 s ; aucun avant t+14 s → trade annulé ; entrée suivante au 1er instantané ≥ heure de sortie.
3. θ choisi seulement parmi les seuils qui font ≥ 200 trades sur la 1re moitié.
4. Témoin principal inchangé (mêmes instants, sens au hasard) ; témoin à instants au hasard en info.
5. Info : exécution maker « réaliste » — long compté seulement si un bid plus bas que l'entrée apparaît dans les 10 s (miroir short).
6. Fenêtres exclues : écart > 4 s entre instantanés, ou > 3 instantanés identiques d'affilée (carnet figé) ; nombre publié.
7. « ÉCHEC » → « non démontré ».
Limite notée : réglage (21h53-02h23 UTC) et jugement (02h23-06h52 UTC) sont deux sessions de marché différentes.
