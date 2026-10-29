# Pré-enregistrement 24 : la martingale « 90 % de cycles gagnants » (bot DCA à ordres de sécurité) avec SL et trailing stop
Écrit le 29/10/2026 à 09h1x, avant tout téléchargement de bougies horaires et tout calcul. Demande de Tony : « le Martingale imperdable à 90 % de chance… à toi de trouver », « en plaçant du sl et du trailing stop ».

## Pourquoi celle-là
La martingale testée le 22/10 (martingale-verif.md) était le « stop et retournement » de Martin. Celle qu'on vend comme « gagnante 90 % du temps » est l'autre : le bot DCA à ordres de sécurité (3Commas, Pionex, Binance…). On achète ; si le prix baisse, on rachète plus gros à des paliers ; on revend dès un petit rebond au-dessus du prix moyen. Presque tous les cycles finissent gagnants ; la question est ce que coûtent les autres.

## Données
Binance USDT-M, bougies 1 h (data.binance.vision, archives mensuelles), **tous** les perpétuels USDT cotés au 01/01/2024 et encore cotés à cette date, **y compris ceux retirés depuis** (pas de biais du survivant ; liste : data-univers de PREREG-27). Période 01/01/2024 → 30/09/2026 (dernier mois complet archivé). Réglage sur 2024-2025, jugement unique sur 01/01 → 30/09/2026.

## Règle (long seulement, sans levier : le capital d'un cycle = la somme de tous ses ordres)
- Ordre de base : 1 unité, au prix d'ouverture de la bougie qui suit la fin du cycle précédent (taker 0,05 %).
- Ordres de sécurité (OS) : N paliers sous le prix d'entrée ; écart du 1er = d ; chaque écart suivant ×1,5 (écarts cumulés pour d = 2 % : 2 ; 5 ; 9,5 ; 16,25 ; 26,4 %) ; taille ×2 à chaque palier (1, 2, 4, 8, 16, 32 : la martingale). Limites : exécutées si le bas de la bougie touche le palier (maker 0,02 %).
- Trailing stop : armé quand le haut d'une bougie atteint prix moyen × (1 + TP). Ensuite, le stop = plus haut des bougies **précédentes** depuis l'armement × (1 − t). Sortie quand le bas touche le stop, au prix du stop, ou à l'ouverture si elle est déjà dessous (taker).
- SL : une fois tous les OS exécutés, stop à s sous le prix du dernier OS (taker). Pas de SL avant.
- Ordre pessimiste dans une bougie : si la même bougie peut toucher le SL et le trailing, c'est le SL ; un OS et une sortie gagnante dans la même bougie : l'OS d'abord, la sortie seulement à la bougie suivante.
- Retrait de la cote en plein cycle : sortie au dernier prix connu.
- Résultat d'une pièce = somme des gains nets des cycles / capital maximal d'un cycle (somme des tailles) : rendement du capital réservé.

## Réglages (tous rapportés, aucun ajouté après coup)
d ∈ {1, 2, 3} % ; TP ∈ {1, 1,5, 2,5} % ; t ∈ {0,5, 1} % ; N ∈ {3, 5} ; s ∈ {3, 8} % → 72 réglages. Le réglage « classique » (d 2 %, TP 1,5 %, t 0,5 %, N 5, s 8 %) est rapporté quoi qu'il arrive. Le réglage jugé est celui qui a le meilleur rendement moyen sur l'univers en 2024-2025, figé avant de regarder 2026.

## Témoins (2026, mêmes pièces)
(a) acheter et garder : le même capital investi au 01/01/2026, revendu au 30/09 (ou au retrait) ;
(b) la même règle sans martingale (taille ×1 à chaque palier), même capital total réservé.

## Verdict (sur 2026, réglage figé)
**GAGNE** seulement si les quatre : rendement moyen > 0 ; > (a) ; > (b) ; au moins 3 pièces gagnantes ET gains totaux > frais totaux payés (critère de Tony du 26/10). Sinon **PERD** (ou **NON DÉMONTRÉ** si > 0 mais pas les témoins).
Rapporté en plus : taux de cycles gagnants (le « 90 % »), pire cycle, part des pièces positives, rendement 2024-2025.

## Contrôle d'artefact (leçon du 22/10 : un trailing serré sur de grosses bougies fabrique des gains)
Le réglage jugé est rejoué en bougies 5 min sur BTC, ETH, SOL en 2026. Si le résultat 1 h et le résultat 5 min diffèrent de signe, ou de plus de 30 % relatifs, le verdict 1 h est marqué SUSPECT et c'est le 5 min qui compte pour ces pièces.
