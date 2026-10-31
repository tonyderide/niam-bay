# Pré-enregistrement 36 : le basis trimestriel tenu jusqu'à la livraison (cash-and-carry) rapporte-t-il plus qu'un placement sans risque ?
Écrit le 31/10/2026 vers 18h00 CET, avant tout téléchargement de prix de futures trimestriels et avant tout calcul. Hypothèse H1 de FILE-HYPOTHESES.md. `scripts/cherche -v basis trimestriel livraison cash and carry` : rien d'identique (voisins : carry du financement PREREG-25/27/33, funding couvert de chasse-1019 PERD sous un seuil de 2 %/an).

## Raison économique, et ce que dit la théorie avant les données
Un future trimestriel cote au-dessus du comptant (contango) parce que les acheteurs à levier paient pour ne pas immobiliser de capital. Acheter le comptant et vendre le future, puis attendre la livraison, encaisse cet écart : à la livraison, le future est réglé sur l'indice, l'écart revient à zéro **mécaniquement**. Ce n'est pas un pari sur le sens : le gain est presque connu à l'entrée. Les risques sont ailleurs : marge du short pendant une forte hausse, plateforme, coût du capital. La vraie question n'est donc pas « est-ce > 0 ? » (presque sûr) mais « est-ce **mieux qu'un placement sans risque** après frais et marge ? ». Prior : positif, d'ampleur incertaine (fort en 2021, faible en 2022-23).

## Données (publiques, sans clé)
- Futures trimestriels USDT-M de Binance, **tous les contrats BTCUSDT_AAMMJJ et ETHUSDT_AAMMJJ livrés** du premier (2021) au 25/09/2026 inclus : `fapi/v1/klines` (bougies 1 h).
- Comptant Binance BTCUSDT et ETHUSDT : `api/v3/klines` (1 h).
- Aucun autre choix de pièce : BTC et ETH sont les seuls trimestriels USDT-M continus sur toute la période.

## Règle (aucun réglage)
- Pour chaque contrat de livraison L (vendredi, 08:00 UTC) : **entrée** à l'ouverture de 00:00 UTC du jour qui suit la livraison précédente (le contrat devient alors le « trimestre courant », ~91 jours avant L). Long comptant au prix d'ouverture du comptant, short future au prix d'ouverture du future, même quantité. Si le contrat n'a pas encore de bougie à cette heure, entrée à sa première bougie.
- **Sortie** à la livraison : future = clôture de sa dernière bougie 1 h (≈ prix de règlement) ; comptant vendu à l'ouverture de la bougie 08:00 UTC du jour de livraison.
- **Marge** : capital engagé = comptant S0 + 50 % de S0 de marge pour le short (levier 2 sur la jambe future). Si un plus haut horaire du future atteint F0 × 1,45 pendant la tenue, on compte une **sortie forcée** à ce prix (future racheté à F0 × 1,45, comptant vendu à la clôture de la même heure), frais taker en plus.
- **Frais** : comptant 0,10 % par côté (taker Binance de base) ; future 0,05 % à l'entrée et 0,05 % à la sortie (taker, prudent pour le règlement).
- Rendement d'un contrat = [(F0 − F_sortie) + (S_sortie − S0) − frais] / (1,5 × S0). Annualisé = rendement × 365 / jours tenus. Rendement d'une année = somme des contrats livrés dans l'année (BTC et ETH moyennés, le capital est réparti moitié-moitié).

## Repère et jugement
- **Placement sans risque** : 4 %/an (ordre de grandeur des bons du Trésor US 3 mois 2023-2026 ; plus bas en 2021-22, ce qui favorise le basis sur ces années : noté).
- **JUGEMENT UNIQUE : les contrats livrés en 2026** (mars, juin, septembre ; 3 par pièce, 6 en tout).
- **GAGNE** si le rendement annualisé moyen des contrats 2026 > 4 % **ET** les 6 contrats de 2026 ont un rendement > 0 **ET** l'historique complet (tous contrats) a un annualisé moyen > 4 %.
- **NON DÉMONTRÉ** si le rendement 2026 est > 0 sans tout le reste.
- **PERD** sinon.
- Témoin au hasard (pour information, il ne juge pas la prime) : même contrat, même sortie, **jour d'entrée tiré au hasard** dans le trimestre (1 000 tirages) : le basis dépend-il du moment d'entrée ? Le vrai témoin de la prime est le placement sans risque, puisqu'une position sans information de sens n'a pas de sens ici (le basis se ferme quel que soit le marché).

## Rapporté
Par contrat : basis d'entrée (annualisé), rendement net, jours, plus forte hausse pendant la tenue, sortie forcée ou non. Par année : annualisé net. Écart entre le prix de règlement approximé et le comptant à 08:00 (erreur de mesure). Nombre de sorties forcées.

## Relecture d'équité, avant calcul
- Aucun paramètre choisi sur les données : entrée, sortie, marge, frais et seuil sont fixés ici.
- Frais taker de base (pas de remise) : prudent. Marge 50 % : prudente pour BTC/ETH sur un trimestre, et le risque est mesuré (sorties forcées comptées).
- Non compté : risque de plateforme (faillite d'exchange), qui est le vrai prix de cette prime ; il sera rappelé dans le verdict.
- Aucune action sur Martin ni Kraken ; aucun compte, aucune clé : lecture de prix publics seulement.
