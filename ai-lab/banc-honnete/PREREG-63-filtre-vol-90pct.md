# Pré-enregistrement 63 : le filtre de volatilité sauve-t-il la règle à 90 % ?
Écrit et commité le 03/11/2026 au soir, avant tout calcul de ce filtre. Suite de PREREG-62, demande de Tony. Une seule hypothèse, aucun réglage.

## Hypothèse et raison
Un stop de −10 % est un événement de queue. Le regroupement de la volatilité est l'un des faits les mieux établis des marchés : une queue est plus probable juste après une journée agitée. Ne pas ouvrir de trade après une journée anormalement agitée devrait donc faire passer les gagnants au-dessus du point mort (≈ 91 %).
Danger connu : PREREG-55 et d'autres ont vu des filtres échouer ; 2024-25 et 2026 ont déjà été regardés sans filtre, donc ce test n'est pas à l'aveugle sur la règle de base.

## Règle
Réglage figé de PREREG-62 : SL 10 %, activation +1 %, trailing 0,5 %, inversion après une perte, frais 0,05 % par côté, 1 min, sans levier ni martingale, sans financement (comme PREREG-62).
Vol du jour UTC = écart-type des rendements log 1 min. **Une entrée n'est permise le jour d que si vol(d−1) ≤ médiane de vol(d−90…d−1)** pour cette pièce. Sinon on attend à plat. Une position ouverte n'est jamais fermée par le filtre. Seuil = médiane, non optimisé.

## Données et périodes
13 pièces : BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM. P1 = 01/04/2024 → 31/12/2025 (90 jours de préchauffage). P2 = 01/01 → 30/09/2026.

## Verdict
- **« FILTRE SUFFISANT »** si sur P1 ET P2 : espérance moyenne > 0, plus de 50 % des pièces au composé positif, espérance > sans filtre.
- **« AIDE SANS SUFFIRE »** si l'espérance dépasse celle sans filtre sur P1 et P2, sans le reste.
- **« INUTILE »** sinon.
Rapportés aussi : gagnants, trades, baisse médiane.
