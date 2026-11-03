# Pré-enregistrement 62 : 90 % de trades gagnants avec un trailing stop, sans martingale
Écrit le 03/11/2026 au soir, avant tout calcul de cette grille (les bougies BTC/ETH/SOL 1 min existent déjà ; PREREG-28 a testé d'autres réglages). Demande de Tony : « il faut un pourcentage de chance à 90 % avec trailing SL ». Non commité à l'écriture (pas de commit demandé).

Prédiction écrite d'avance : 90 % de trades gagnants s'obtient facilement avec un SL très large et un trailing très serré, mais l'espérance restera proche de zéro ou négative après frais, et chaque perte coûtera bien plus que chaque gain.

## Règle (moteur `chaine` de sl-trailing/regle_tony.py, sans changement)
Toujours en position, entrée à l'ouverture suivante, SL fixe s, trailing t activé à +a, bougie ambiguë = SL d'abord, frais 0,05 % par côté, position fixe, sans levier, sans martingale. Deux modes de sens : long seul, et inversion après une perte.

## Grille (rapportée entièrement)
s ∈ {3, 5, 8, 10, 15, 20, 30} % ; a ∈ {0,3 ; 0,5 ; 1 ; 1,5 ; 2} % ; t ∈ {0,1 ; 0,25 ; 0,5 ; 1} % avec t < a. Un gain net exige a − t > 0,1 % de frais pour être assuré ; tout autre réglage reste testé.

## Choix et jugement
Choix sur 2024-2025 uniquement : parmi les réglages avec ≥ 90 % de trades gagnants sur chacune de BTC, ETH et SOL, celui de la meilleure espérance moyenne par trade (un choix par mode). Jugement sur 01/01 → 30/09/2026, réglage figé.

## Verdict
- **« 90 % ET RENTABLE »** si en 2026, sur BTC, ETH et SOL : ≥ 90 % de gagnants, espérance > 0, et p < 0,05 contre un sens tiré au hasard à chaque trade (200 tirages, même réglage).
- **« 90 % MAIS PAS D'AVANTAGE »** si ≥ 90 % partout, sans le reste.
- **« 90 % NON TENU »** sinon. Aucun réglage éligible : même verdict.
Rapportés en plus : gain moyen, perte moyenne, pire trade, gains nécessaires pour effacer une perte, total sur 2026.

## Résultat du jugement (03/11/2026 — t62.py, t62.json)
| Mode, réglage figé sur 2024-25 | BTC 2026 | ETH 2026 | SOL 2026 |
|---|---|---|---|
| **Long**, SL 30 %, activation 2 %, trailing 0,1 % : gagnants / espérance / p / composé | 90,0 % / +0,02 % / 0,205 / −5,5 % | 90,6 % / −0,23 % / 0,53 / −17,6 % | 93,4 % / +0,18 % / 0,44 / −7,0 % |
| **Inversion**, SL 10 %, activation 1 %, trailing 0,5 % : gagnants / espérance / p / composé | 92,6 % / +0,16 % / 0,05 / +24,2 % | 91,2 % / +0,03 % / 0,08 / −5,0 % | 92,1 % / +0,16 % / 0,015 / +49,1 % |
Inversion sur la période de choix 2024-25 : composé BTC −64,1 %, ETH −19,2 %, SOL −83,5 %.

**VERDICT (pré-enregistré), les 2 modes : « 90 % MAIS PAS D'AVANTAGE ».** Le 90 % tient hors échantillon. Prédiction d'avance sur l'espérance confirmée pour le long ; pour l'inversion, 2026 est positif mais 2024-25 négatif, et les p n'atteignent pas tous 0,05.

## Addendum A, écrit après ce verdict et avant son calcul : le panier
Le réglage « inversion » (SL 10 %, activation 1 %, trailing 0,5 %) ne change pas. Il est appliqué aux pièces de ../dca-martingale/refait/donnees/*-1h.npy, coupées au retrait (`couper(a, 48)`), bougie ambiguë = SL d'abord. Ne compte pas dans le verdict ci-dessus. Il tient si, en 2026 : ≥ 90 % de gagnants en moyenne, espérance moyenne > 0, et > 50 % de pièces au composé positif.

Résultat de l'addendum A (corrigé) : 2026, 187 pièces, 76,2 % de gagnants, espérance −0,127 %, composé médian −49 %, 14,4 % de pièces positives. **Ne tient pas.** Résolution 1 h trop grossière pour un trailing de 0,5 %, donc lecture prudente.

**Erreur de ma part, corrigée :** la 1re exécution de t62b.py et t62c.py inversait activation et trailing (donnait ~50 % de gagnants) et j'en avais d'abord attribué la cause à la résolution 1 h, à tort. Après correction, contrôle : BTC 2026 retrouve exactement 175 trades, 92,57 %, +0,164 %.

## Addendum B, écrit avant téléchargement : 10 autres pièces en 1 min
Même réglage figé. XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM, perpétuels Binance USDT-M 1 min, 01/2024 → 09/2026. Aucune n'a servi au choix. Tient si, en 2026 : ≥ 90 % de gagnants en moyenne, espérance moyenne > 0, > 50 % de pièces au composé positif et espérance moyenne supérieure à celle d'un sens tiré au hasard dans au moins 95 % de 200 tirages. 2024-25 rapporté à part.

Résultat de l'addendum B (t62c.py, données Binance 1 min téléchargées hors dépôt) :
| | Gagnants | Espérance | Composé médian | Pièces positives | Baisse médiane | Témoin (sens au hasard) battu |
|---|---|---|---|---|---|---|
| 2026 | 91,5 % | +0,079 % | +14,1 % | 6 / 10 | −43,3 % | 100 % des 200 tirages (témoin −0,129 %) |
| 2024-25 | 89,1 % | −0,072 % | −83,1 % | 0 / 10 | −88,1 % | 99,5 % (témoin −0,126 %) |

**Verdict de l'addendum B : TIENT sur 2026, ses 4 critères sont remplis.** Mais la même règle perd lourdement sur 2024-25 : en multipliant les deux périodes, les 13 pièces (BTC, ETH, SOL et ces 10) finissent toutes en perte sur 33 mois, d'environ −23 % à −94 %.

Point mort : gain moyen ≈ +0,9 %, perte moyenne ≈ −9 %, soit ≈ 91 % de gagnants pour ne rien perdre. 2024-25 est juste en dessous, 2026 juste au-dessus.

Limites : financement non compté (position permanente) ; pièces corrélées, tirages du témoin indépendants par pièce, donc le « 100 % » surestime la significativité ; 9 mois de jugement ; pas de test en avant. Aucun branchement sur un compte.
