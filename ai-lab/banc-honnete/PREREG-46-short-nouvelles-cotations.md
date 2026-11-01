# Pré-enregistrement 46 : vendre à découvert les nouvelles cotations de Binance rapporte-t-il, contre un short au hasard sur des pièces anciennes ?
Écrit le 01/11/2026 vers 13h CET, avant de télécharger le financement et avant tout calcul. Hypothèse H11 de FILE-HYPOTHESES.md. `scripts/cherche -v nouvelles cotations listing récentes short` et `… introduction en bourse nouveaux jetons surévalués déblocage` : rien d'identique. Seule information regardée avant ce commit : le nombre de perpétuels USDT cotés par année (2021 : 55 ; 2022 : 25 ; 2023 : 99 ; 2024 : 129 ; 2025 : 245 ; 2026 : 260).

## Raison économique, et ce que dit la théorie avant les données
Les jetons neufs arrivent avec un faible flottant, des déblocages programmés (équipe, investisseurs) et l'attention maximale : la demande de « billet de loterie » les surévalue, puis l'offre arrive. Analogue des introductions en bourse qui sous-performent sur les mois suivants (Ritter 1991). La vente à découvert est d'abord chère (financement négatif) : c'est le prix du risque, compté ici. Risque : envolées (une pièce peut faire ×5). Prior : moyenne positive plausible, queue dangereuse.

## Données
- Prix : ai-lab/carry-financement/data-univers/klines.json (tous les perpétuels USDT-M listés par data.binance.vision, morts compris, bougies journalières fapi : ouverture, clôture ; 01/09/2020 → 27/10/2026). Limite connue : quelques contrats retirés n'ont plus d'historique chez Binance (absents malgré eux).
- **Date de cotation** = première bougie journalière (seulement si elle est postérieure au 02/09/2020).
- Financement : `fapi/v1/fundingRate` (public) des pièces concernées, téléchargé après ce commit dans ai-lab/banc-honnete/listings/.

## Règle
- Pour chaque nouvelle cotation : **short à l'ouverture de la 2e bougie journalière** (premier jour complet), tenu **N jours** (sortie à la clôture du N-ième jour) ou jusqu'au retrait (dernière clôture).
- Rendement d'un trade = −(sortie / entrée − 1) + financement reçu par le short pendant la tenue (somme des taux, positif = reçu) − 2 × 0,05 % ; **plancher −100 %** (la mise est perdue, liquidation).
- Mise égale par trade. Mesure : **rendement moyen par trade**.
- Grille : **N ∈ {14, 30, 60, 90} jours**.

## Choix et jugement
- Choix de N sur les trades **entrés du 01/01/2021 au 31/12/2025**, au meilleur rendement moyen.
- **JUGEMENT UNIQUE : trades entrés du 01/01/2026 au (27/10/2026 − N jours)** (sortie connue).
- **Témoin** : pour chaque trade, même date d'entrée, même N, short d'une pièce **ancienne** tirée au hasard (cotée depuis plus de 365 jours, avec une bougie à l'entrée), mêmes frais, son financement réel, même plancher. 1 000 tirages, graine 46. Il garde le marché et le calendrier ; il retire seulement « être neuf ». p = part des tirages au rendement moyen ≥ la règle.
- **GAGNE** si rendement moyen > 0 sur la période de choix **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si > 0 en 2026 sans le reste. **PERD** sinon.
- **Mention de queue (pré-enregistrée)** : part des trades au plancher (−100 %) et pire trade rapportés ; « RISQUE DE QUEUE » si plus de 5 % des trades de 2026 perdent plus de 100 % avant plancher.

## Rapporté
Les 4 N sur les deux périodes, nombre de trades, médiane, part gagnante, financement moyen reçu, pire trade, trades au plancher ; par année d'entrée ; témoin (moyenne, écart-type).

## Relecture d'équité, avant calcul
- Entrée au 2e jour (pas au premier prix, souvent erratique) : fixé ici. N choisi sur 2021-25, jugement 2026 unique.
- Le financement compte contre le short quand il est négatif (fréquent sur les jetons neufs).
- Le plancher à −100 % est favorable au short (un compte réel serait liquidé plus tôt avec levier) ; la mention de queue mesure ce risque.
- Aucune action sur Martin ni Kraken ; aucun compte, aucune clé.
