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
