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

## Résultat (01/11/2026, après-midi — t46_financement.py (891/891 contrats), puis t46.py → t46.log, chiffres dans t46.json)
Lancé une seule fois après le commit d8f3361, `nice -n 10`. Rendement moyen par trade (mise égale, short 1×, plancher −100 %, financement réel compris).

| N (jours) | Choix 2021-25 : trades / moyenne / médiane / gagnants | 2026 : trades / moyenne / médiane / gagnants |
|---|---|---|
| 14 | 551 / +6,7 % / +13,2 % / 68 % | 261 / +4,1 % / +3,9 % / 63 % |
| 30 | 551 / +11,0 % / +19,3 % / 70 % | 249 / +3,3 % / +2,9 % / 58 % |
| 60 | 551 / +18,1 % / +28,4 % / 74 % | 221 / +8,5 % / +7,8 % / 63 % |
| **90** | 551 / **+24,2 %** / +36,8 % / 76 % | **191 / +8,0 % / +11,6 % / 64 %** |

- **N figé = 90 jours.** Par année d'entrée (choix) : 2021 +26,9 % · 2022 +39,0 % · 2023 +10,6 % · 2024 +25,8 % · 2025 +26,7 %.
- Financement moyen payé par le short : −1 à −2 % par trade (compté).
- Trades au plancher (−100 %) : 41/551 en 2021-25, **6/191 en 2026 (3,1 %)** → pas de mention RISQUE DE QUEUE (seuil 5 %).
- **Témoin 2026** (short d'une pièce cotée depuis plus d'un an, même date, même N) : −1,0 ± 2,1 % ; **p < 0,001** (0/1 000).

**VERDICT (pré-enregistré) : GAGNE** — rendement moyen > 0 sur 2021-25 (+24,2 %) et en 2026 (+8,0 %), p < 0,001 contre le témoin.

## Vérifications après le verdict (information ; elles ne changent pas le verdict)
- **Calcul vérifié** sur un trade tiré au milieu (ASMLUSDT) : prix d'entrée, de sortie et rendement brut identiques à une lecture neuve de l'API Binance (`t46_verif.py`).
- **Contamination trouvée** : en 2026 Binance cote aussi des perpétuels sur **actions et matières premières** (INTC, MU, SNDK, ASML…, 216 contrats non-crypto au 01/11/2026 d'après `underlyingType`, fichier listings/exchangeInfo-20261101.json). Le pré-enregistrement disait « tous les perpétuels USDT-M », donc ils sont dans le verdict ; mais l'hypothèse parle de jetons neufs. Parmi les 5 pires trades de 2026 (tous au plancher), 3 sont des actions (INTC, MU, SNDK) ; GWEI et BTW sont des jetons crypto.
- **Crypto seulement** (`t46_crypto_seul.py` → t46_crypto_seul.log, contrats non-COIN retirés de la règle ET du témoin) : choix 2021-25 inchangé (548 trades, +24,3 %) ; **2026 : 46 trades, +18,5 % par trade, témoin +7,1 %, p = 0,002**. L'effet est plus net sans les actions.
- **Fragilités** : 2026 crypto = 46 trades, 4 mois sur 7 positifs (février −14 %, juin −12 %) ; sans les 10 meilleurs trades (panier complet), la moyenne 2026 tombe de +8,0 % à +4,2 %. Les shorts se chevauchent (≈ 14 à 57 ouverts en même temps) : une manie sur les nouveaux jetons les ferait perdre ensemble, risque que le témoin (pièces anciennes) ne mesure pas. Les contrats retirés sans historique chez Binance manquent (plutôt défavorable au short : ce sont souvent des effondrements).
- **Ce que ça ne dit pas encore** : on ne sait pas si l'effet tient sur des cotations **à venir**. Prochaine étape pré-enregistrée : test papier EN AVANT des nouvelles cotations crypto (PREREG-47).

**Ce que ça montre :**
- Premier GAGNE de la série, et il colle à la théorie : les jetons neufs (faible flottant, déblocages à venir, attention maximale) perdent en moyenne de leur valeur sur leurs 3 premiers mois, chaque année de 2021 à 2026, même après le financement négatif payé par le short.
- Le gain vient d'une **asymétrie structurelle** (offre future connue, demande de loterie), pas d'une règle de sortie : c'est exactement le type d'avantage que les maths permettent.
