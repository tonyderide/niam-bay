# Pré-enregistrement 04 : le stop suiveur (idée de Tony, 1020 ~04h25)
Figé avant tout calcul.

Données : bougies 1h de Kraken (prix des trades) pour BTC, ETH et SOL. Frais de 0,05 % par côté.
Si le stop est touché, la sortie se fait au niveau du stop. Si l'ouverture de la bougie a déjà franchi le stop (gap), la sortie se fait à l'ouverture.

## Version A : stop suiveur en %, avec retournement
- On démarre long au premier instant de la période.
- Le stop suit le plus haut atteint (en long) ou le plus bas atteint (en short), à une distance de X %.
- Quand le stop est touché, on se retourne aussitôt dans l'autre sens, au prix du stop.
- X est pris dans {1, 2, 3, 5, 8} %. On le **choisit sur janvier-juin 2026**, et on garde la meilleure somme des 3 marchés.
- On le **juge ensuite sur 2024-2025 et sur juillet-octobre 2026**.

## Version B : façon Turtles
- Entrée sur une cassure du canal de Donchian 20 : long si le close dépasse le plus haut des 20 bougies précédentes, short s'il passe sous leur plus bas. On entre à l'ouverture de la bougie suivante.
- Sortie avec un stop « chandelier » : 3 × ATR(22) depuis l'extrême atteint. Une fois sorti, on attend une nouvelle cassure.
- Paramètres standards, sans aucun réglage. On teste sur 2024-2025 et sur 2026 (jusqu'au 16/10).
- Les entrées se font sur bougies 1h. Les mêmes calculs sont refaits sur bougies 4h, et ces résultats 4h comptent aussi : il faut gagner sur les deux.

## Hasard
500 tirages qui gardent le même mécanisme de stop suiveur, mais avec des entrées tirées au hasard :
- version A : on part dans un sens aléatoire ;
- version B : autant d'entrées que la vraie stratégie, à des instants aléatoires et dans un sens aléatoire.

On mesure ainsi si les entrées (version B) ou le choix de X (version A) apportent quelque chose par rapport au stop suiveur seul.

## Critère pour dire GAGNE
Il faut, sur chaque période jugée :
- une somme > 0 sur les 3 marchés ;
- un résultat au-dessus du 95e centile du hasard ;
- au moins 2 marchés positifs sur 3.
