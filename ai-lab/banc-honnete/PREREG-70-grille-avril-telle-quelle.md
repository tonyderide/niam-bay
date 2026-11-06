# PREREG-70 — La grille d'avril telle qu'elle tournait vraiment (25/03 → 21/04/2026), puis corrigée

Écrit le 06/11/2026, **avant tout calcul**. Script : `t70.py`.

## Pourquoi
Sur le vrai compte Kraken, la seule période gagnante va du 25/03 au 21/04/2026 : **+21,9 $** pour environ 118 $ engagés sur 4 grilles (SOL 35, LINK 29, ADA 29, DOT 25). Le 25/04, une session a modifié la pose des ordres de reprise et passé l'écart à 0,6 %. Résultat : 45 ordres identiques en 7 minutes, puis −26 $ en 4 jours.
PREREG-69 simulait la grille « réparée », pas celle qui tournait. Ici, on simule le code reconstruit du programme en production (commit martin `77d994d`), sans le patch du 25/04 :
- `GridTradingService` ;
- `AutoGridScheduler` ;
- `SignalService`.

## Modèle R : « telle quelle »
Par paire, capital `cap`, levier 5, 5 niveaux. Notionnel par niveau = `cap / 5 × 5 = cap`.
- **Niveaux :** centre P, écart s = 1,2 % × P. Niveaux à P −1,5s, −0,5s (achats) et P +0,5s, +1,5s, +2,5s (ventes).
- **Exécution :** chaque niveau ne s'exécute qu'**une fois**. Son ordre de reprise tombe toujours sur le prix d'un autre niveau, donc l'ancien code le sautait (« log skip + return »). Ordre limite à franchissement strict, actif dès la minute de pose, frais maker 0,02 %.
- **Recentrage :** si la clôture d'une minute sort de [P−2s, P+2s], on annule les ordres et on repose 5 niveaux autour du nouveau prix. **La position est gardée.**
- **Toutes les 15 minutes** (à la clôture 15 min, action à la minute suivante) :
  - **Régime « tradable » :** ADX14 < 40 et BBW(20,2) < 4 % sur bougies 15 min. Même fonction que t69.
  - **DANGER :** RSI14 en 1 h < 25.
  - Grille active et DANGER : arrêt de la grille. Les ordres sont annulés, la position reste, sous sa protection.
  - Grille inactive, tradable et pas DANGER : démarrage au prix courant.
  - Grille active et non tradable :
    - si la position est nulle, arrêt ;
    - sinon, mode « fermeture seule » : les recentrages ne reposent que les ordres qui réduisent la position, et la grille s'arrête quand la position revient à 0.
  - **Protection de la position** (grille active, position non nulle, pas encore protégée de ce côté) : un objectif limite et un stop au marché pour la taille du moment, prix moyen d'entrée E, cours C.
    - Long perdant (C < E) : stop à E × 0,97, objectif à E × 1,002.
    - Long gagnant : stop à C × 0,994, objectif à C × 1,025.
    - Short : symétrique.
    - Le stop s'exécute à son prix, ou à l'ouverture si le prix l'a sauté, frais taker 0,05 %. L'objectif s'exécute comme une limite maker.
    - La protection disparaît quand la position revient à 0 ou change de côté.
- **Sans effet dans ce code, donc non modélisés :** le stop par grille (`checkStopLoss`) et le `DrawdownManager`. Ils se basent sur le gain théorique des allers-retours, qui reste à 0 quand les reprises sont sautées. Les heures de trading ne sont pas modélisées non plus.
- Si la valeur de la paire tombe à 0, la paire est liquidée et s'arrête.

## Modèle R+ : « telle quelle, bugs corrigés »
C'est la version que je déploierais. R, plus :
- position plafonnée à 5 × `cap` : un ordre qui la dépasserait est ignoré ;
- vrai stop : si la valeur de la paire tombe 15 % sous sa valeur au démarrage de la grille, fermeture au marché, pause de 24 h, puis la grille peut redémarrer ;
- arrêt définitif de la paire sous 60 % du capital initial.

## Témoin de fidélité (avant tout verdict)
R lancé sur le 25/03 → 21/04/2026 avec les vrais capitaux (35/29/29/25) doit donner un total **positif, entre +5,5 et +55 $**, soit entre 0,25 et 2,5 fois les +21,9 $ réels. S'il échoue, le modèle ne reproduit pas Martin : le résultat est **NON CONCLUANT**, il n'y a pas de verdict et donc pas de déploiement. Le nombre d'exécutions simulées et réelles sera aussi publié.

## Verdict (1 000 € par paire, SOL, LINK, ADA, DOT), règles de PREREG-69
- Périodes : P1 (02/2024 → 12/2025) et P2 (01 → 09/2026).
- Pour chacune : total > 0, au moins 3 paires sur 4 positives, aucune paire liquidée ni arrêtée définitivement, baisse maximale du portefeuille meilleure que −30 %.
- **TIENT** si P1 et P2 passent tous les critères. Sinon **NON**.
- Je prédis **NON** pour R, à cause des tendances de 2024-2025, et un résultat incertain pour R+.

## Conséquence écrite d'avance
- **R+ TIENT et témoin OK :** je reconstruis cette version depuis `77d994d`, je retire le patch du 25/04 et j'ajoute les trois corrections de R+. Elle tourne en **papier**. L'argent réel reste la décision de Tony, et seulement après la révocation des clés Kraken exposées dans Git.
- **R+ NON :** pas de déploiement, même en papier. Le gain d'avril est alors attribué au marché d'avril, pas à la version.

## Résultat (06/11/2026 — t70.py, t70.json)
**Témoin de fidélité ÉCHOUÉ : −4,95 $ simulés contre +21,9 $ réels sur le 25/03 → 21/04/2026. VERDICT : NON CONCLUANT pour R et R+.** Conformément à ce qui était écrit, aucun déploiement, même en papier.

| Paire | Réel | Simulé (R) | Exécutions réelles | Exécutions simulées |
|---|---|---|---|---|
| SOL | +12,2 $ | +8,2 $ | 147 | 188 |
| LINK | +1,1 $ | −4,5 $ | 105 | 183 |
| ADA | +5,7 $ | −4,7 $ | 80 | 227 |
| DOT | +3,6 $ | −4,0 $ | 183 | 223 |

Causes probables, constatées après coup :
- **Martin n'a pas tourné en continu.** Le journal de Niam-Bay note des grilles arrêtées le 27/03 et le service en plantage en boucle le 29/03. ADA n'a que 80 exécutions réelles, contre 227 simulées.
- **La config a changé pendant la période.** Fin mars, l'écart était d'environ 1 % ; le 1,2 % ne vient qu'ensuite.
- **Les reprises n'étaient pas toujours sautées.** 89 ordres limites réels s'exécutent au même prix qu'un ordre déjà exécuté, dont 66 sur DOT. Le programme de fin mars n'était donc pas exactement celui reconstruit le 25/04.

Pour information seulement, puisque le modèle n'est pas validé : sur 1 000 € par paire, R fait −3 272 € sur P1 et −2 401 € sur P2, R+ fait −1 631 € et −1 326 €. Le gain avant frais est positif sur P1, mais les frais, environ 0,2 € par exécution sur 12 000 à 18 000 exécutions, l'effacent largement.
