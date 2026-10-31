# PREREG-40 : l'écart de financement entre Binance et Hyperliquid se récolte-t-il, couvert en prix ?
Écrit le 01/11/2026 vers 00h55 CET, avant tout calcul. Hypothèse H5 de ai-lab/banc-honnete/FILE-HYPOTHESES.md. `scripts/cherche -v écart financement plateformes Binance Hyperliquid arbitrage` : voisins PREREG-33 (carry sur Hyperliquid seul, NON DÉMONTRÉ) et chasse-1019/funding-couvert (écart **Kraken**/Hyperliquid, BTC/ETH/SOL seulement, PERD sous 2 %/an). Ici : Binance contre Hyperliquid, toutes les pièces communes, sans réglage.

## Raison économique, et ce que dit la théorie avant les données
Le capital est segmenté : une marge chez Binance ne couvre pas une position chez Hyperliquid. Quand la demande de levier diffère entre les deux publics (Hyperliquid : plus de particuliers, de nouvelles pièces), le financement diffère, et l'arbitrer immobilise de la marge des deux côtés — donc l'écart peut persister. Être long sur la plateforme qui paie peu et short sur celle qui reçoit beaucoup est presque neutre en prix (même pièce). Risques : l'écart se retourne, les frais de 4 jambes, l'écart de prix entre plateformes. Prior : petit positif brut ; la question est l'après-frais et la comparaison au taux sans risque.

## Données (déjà là, aucun téléchargement)
- Financement Binance : carry-financement/data-univers/funding.json (paiements toutes les 8 h) ; prix journaliers Binance : data-univers/klines.json (ouverture, clôture à 00:00 UTC).
- Financement Hyperliquid : carry-financement/data_hl/funding.json (horaire) ; prix journaliers : data_hl/klines.json.
- **Pièces : les 45 présentes dans les deux fichiers** (kPEPE ↔ 1000PEPEUSDT, kSHIB ↔ 1000SHIBUSDT). Limite connue : ces fichiers viennent des univers « top 30 du volume » de PREREG-27 et PREREG-33 (choisis chaque année à l'époque, morts compris de chaque côté), pas de tout ce qui a existé.
- Période : 01/10/2023 → 26/10/2026 (fin des données Binance).

## Règle (aucun réglage)
- Chaque jour à 00:00 UTC, pour chaque pièce ayant des deux côtés 7 jours de financement passé et un prix ce jour : écart e = (somme du financement Hyperliquid − somme du financement Binance) sur les 7 jours précédents, ramené à l'année (× 365/7).
- Si |e| > **10 %/an** : position pour 24 h, 1 $ par jambe : si e > 0, short Hyperliquid + long Binance ; si e < 0, l'inverse. Sinon pas de position.
- Gain du jour par pièce = financement reçu − payé pendant les 24 h (paiements dont l'heure est dans [jour, jour + 24 h)) + prix : sens × (rendement Binance − rendement Hyperliquid) du jour (clôture / ouverture − 1 sur chaque plateforme).
- Frais sur ce qui change : 0,05 % (Binance taker) et 0,045 % (Hyperliquid taker) par jambe ouverte, fermée ou retournée.
- Rendement du portefeuille : moyenne par jour sur les pièces en position (capital = 1 $ de marge par paire, levier 1 par jambe… soit 2 $ de notionnel pour 1 $ ; rapporté aussi par $ de notionnel). Jours sans position : 0.

## Jugement
- Historique (info + condition) : 01/10/2023 → 31/12/2025. **JUGEMENT UNIQUE : 01/01/2026 → 26/10/2026.**
- **Témoin** : mêmes jours, mêmes pièces en position, même nombre de positions, **sens au hasard** (1/2), frais recalculés ; 1 000 tirages, graine 40. p = part des tirages ≥ la règle en 2026.
- **GAGNE** si net annualisé (sur capital) > 0 dans l'historique **ET** > **4 %/an** en 2026 **ET** p < 0,05 en 2026.
- **NON DÉMONTRÉ** si net 2026 > 0 sans tout le reste. **PERD** sinon.

## Rapporté
Financement net, prix (écart entre plateformes), frais, net ; annualisé ; jours avec position, positions moyennes ; pire mois ; pièces les plus contributrices ; par année.

## Relecture d'équité, avant calcul
- Seuil 10 %/an, 7 jours et 24 h fixés ici (repris de PREREG-25/27 pour la fenêtre).
- Le témoin garde les mêmes pièces et le même calendrier : il ne retire que le sens donné par l'écart passé.
- Écart de prix mesuré à 00:00 UTC sur les deux plateformes (bougies journalières) : l'heure exacte peut différer de quelques secondes, bruit noté.
- Aucune action sur Martin ni Kraken ; aucun compte, aucune clé.
