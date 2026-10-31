# PREREG-33 : le carry du financement tient-il sur Hyperliquid ?

Écrit le 31/10/2026 (heure du commit), AVANT de télécharger le financement et les prix d'Hyperliquid et AVANT tout calcul. Seules choses regardées avant : la liste des contrats (`meta` : 235 noms dont 56 marqués `isDelisted`), la page des frais, la page des limites de débit, et 3 lignes d'exemple de l'API (premier financement BTC le 2023-05-12 ; les bougies journalières remontent avant le lancement avec un volume nul).

Question de Tony : « mathématiquement il y a forcément un moyen ». Le carry est le seul avantage démontré du labo (PREREG-25 Binance +476 %, PREREG-27 sans biais du survivant +372 %, p 0,031, irrégulier), mais il a échoué sur Kraken (PREREG-26 A : −21,9 %, p 0,47). Hyperliquid : accessible sans KYC, financement horaire.

## Données (lecture seule, API publique `POST https://api.hyperliquid.xyz/info`, aucun compte, aucune clé, aucun ordre)
- Liste : `meta` (contrats actifs ET retirés, `isDelisted`).
- Prix : `candleSnapshot` journalier (ouverture 00:00 UTC, clôture au 00:00 suivant) pour chaque contrat. Une bougie compte comme « réelle » seulement si `n` (nombre de trades) > 0 ; les bougies antérieures au lancement (volume nul) sont ignorées.
- Financement : `fundingHistory` (horaire ; toutes les 8 h au tout début), pour chaque contrat qui entre au moins une fois dans un univers, depuis 8 jours avant sa première entrée.
- Cache : `data_hl/` (ignoré par git). Pauses pour rester sous 1 200 de poids par minute.

## Règle (PREREG-27 transposée telle quelle, aucun réglage nouveau)
- **Univers** : les **30 contrats au plus gros volume en dollars** sur les 30 jours précédents (volume = Σ `v` × `c` des bougies journalières réelles), parmi ceux ayant au moins 60 jours de bougies réelles. Exclu : NFTI (indice NFT, pas une crypto — même logique que BTCDOM exclu en PREREG-27). Contrats retirés compris (sans savoir qui survivra).
- **Dates de choix de l'univers** : chaque 1er janvier, comme PREREG-27. Hyperliquid ayant démarré en mai 2023, un **univers initial** est choisi au premier 1er du mois où au moins 30 contrats remplissent la condition des 60 jours ; c'est aussi le **début de la période testée**. Il tient jusqu'au 1er janvier suivant.
- Un contrat de l'univers est éligible un jour d s'il a une bougie réelle ce jour-là et un financement antérieur à d − 7 jours. Un contrat retiré sort le jour où sa bougie manque.
- Chaque jour à 00:00 UTC : somme du financement des 7 jours précédents (paiements strictement avant 00:00) ; **short les 3 plus élevés, long les 3 plus bas**, 1 $ par côté (1/3 $ par contrat), tenu 24 h.
- Rendement d'un jour = prix (clôture/ouverture − 1 de la bougie du jour, signé) + financement réellement payé/reçu pendant la détention (paiements dans (d, d + 24 h], le short reçoit un taux positif).
- **Couverture** : comme PREREG-27, neutre en dollars (1 $ long, 1 $ short), pas de couverture bêta en plus.
- **Frais** : **0,045 % par côté** sur la part qui change (taker, palier 0 d'Hyperliquid : « Tier 0 … Taker 0.045%, Maker 0.015% », https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees , consulté le 31/10/2026). Entrée initiale comprise. Pas de remise de staking HYPE (Tony n'en a pas). Variante maker 0,015 % pour information seulement.
- Rendements en % de 1 $ par côté, additionnés jour après jour sans capitalisation (comme PREREG-25/26/27).

## Périodes
- Historique disponible = début de la période testée (ci-dessus) → dernier jour complet (bougie du jour close).
- **Réglage** = première moitié de cet historique (en jours). Rien n'y est réglé (la règle est figée) : elle sert de contrôle « avant ».
- **JUGEMENT UNIQUE = 2026-01-01 → dernier jour complet.** Un seul calcul, pas de reprise.
- La tranche entre la fin du réglage et le 31/12/2025 est rapportée pour information.

## Témoin (sélections de pièces au hasard)
2 000 tirages (graine 33). Chaque tirage tient lui aussi 3 shorts et 3 longs parmi les contrats éligibles du jour, 1 $ par côté, et **change le même nombre de contrats, du même côté, les mêmes jours que la règle** (les remplaçants sont tirés au hasard parmi les éligibles non détenus ; un contrat qui devient inéligible est remplacé au hasard). Même calendrier et même rotation, donc des frais comparables ; seul le choix des pièces diffère. Le témoin repart de zéro au début de chaque période évaluée.
p (unilatéral) = (nombre de tirages au net ≥ net de la règle + 1) / 2 001, calculé sur la période de jugement.
Pour information : p au test des décalages circulaires de PREREG-27 (≥ 30 jours, 2 000 tirages), sur la période de jugement.

## Verdict
- **GAGNE** si net > 0 sur le réglage ET net > 0 sur le jugement ET p < 0,05 en jugement.
- **NON DÉMONTRÉ** si net > 0 en jugement sans le reste.
- **PERD** sinon (net ≤ 0 en jugement).

## Rapporté aussi (ne change pas le verdict)
Rendement annualisé (simple, net × 365 / jours) sur réglage et jugement ; pire mois civil ; pire baisse (sur la somme cumulée) ; part du prix, du financement et des frais ; contributions par contrat et nombre de contrats gagnants ; et ce que ça donnerait sur **100 $** et **1 000 $** de capital (capital = long + short à levier 1, donc 50 $ / 500 $ par côté ; gain = net % × capital / 2). Rappel : le capital de Tony est ~6 $, et le minimum d'ordre d'Hyperliquid est de 10 $ par ordre (1/3 de côté ≥ 10 $ exige ≥ 60 $ de capital).

## Résultat (31/10/2026 17:10, t33.py)

Historique : 2023-10-01 → 2026-10-30, 1126 jours ; 62 contrats dans les univers. Univers : 2023-10-01: APE, CFX, BTC, ETH, FTM, DYDX, CRV, COMP, WLD, SNX, SUI, SOL, GMX, XRP, APT, LINK, MKR, AAVE, FXS, MATIC, INJ, ARB, STX, DOGE, ATOM, LTC, kPEPE, AVAX, LDO, BCH | 2024-01-01: ETH, BTC, SOL, TIA, AVAX, INJ, SEI, OP, ARB, WLD, kPEPE, MATIC, DOGE, STX, SUI, APT, BNB, LINK, NEAR, RNDR, BIGTIME, LDO, FTM, ATOM, DYDX, BLUR, TRB, FET, MINA, ADA | 2025-01-01: BTC, ETH, SOL, kPEPE, XRP, DOGE, SUI, LINK, FTM, AVAX, AAVE, ENA, kBONK, LTC, BNB, LDO, WLD, GOAT, kSHIB, TRX, WIF, CRV, TIA, POPCAT, ONDO, APT, SEI, TAO, MOODENG, UNI | 2026-01-01: BTC, ETH, SOL, HYPE, ZEC, FARTCOIN, XRP, SUI, XPL, PUMP, ASTER, MON, AAVE, PAXG, ENA, DOGE, BCH, BNB, UNI, LINK, TAO, AVAX, ADA, kPEPE, PENGU, LTC, CRV, ARB, NEAR, WIF

### Réglage (1re moitié) : 2023-10-01 → 2025-04-15 (563 jours)
- Prix -118.7 % · financement +75.2 % · frais 15.9 % · **net -59.4 %** (en % de 1 $ par côté)
- Annualisé -38.5 %/an par côté, soit -19.2 %/an du capital (long + short à levier 1)
- Pire mois 2024-03 -48.8 % (11/19 mois positifs) · pire baisse -218.3 %
- Contrats gagnants 23/51 · variante maker 0,015 % : net -48.7 %
- Témoin pièces au hasard (2000 tirages) : médiane -18.7 %, 95e centile +116.8 % → **p = 0.7081** · (info) décalages circulaires : p = 0.6047

### Entre-deux (information) : 2025-04-16 → 2025-12-31 (260 jours)
- Prix -37.3 % · financement +26.0 % · frais 7.7 % · **net -19.0 %** (en % de 1 $ par côté)
- Annualisé -26.7 %/an par côté, soit -13.3 %/an du capital (long + short à levier 1)
- Pire mois 2025-07 -23.7 % (2/9 mois positifs) · pire baisse -97.5 %
- Contrats gagnants 13/29 · variante maker 0,015 % : net -13.9 %

### JUGEMENT UNIQUE : 2026-01-01 → 2026-10-30 (303 jours)
- Prix +39.2 % · financement +12.9 % · frais 9.7 % · **net +42.4 %** (en % de 1 $ par côté)
- Annualisé +51.1 %/an par côté, soit +25.5 %/an du capital (long + short à levier 1)
- Pire mois 2026-01 -15.5 % (6/10 mois positifs) · pire baisse -41.6 %
- Contrats gagnants 16/30 · variante maker 0,015 % : net +48.9 %
- Témoin pièces au hasard (2000 tirages) : médiane -9.2 %, 95e centile +67.4 % → **p = 0.1279** · (info) décalages circulaires : p = 0.0175

1. net réglage > 0 : ❌
2. net jugement > 0 : ✅
3. p < 0,05 en jugement : ❌

**VERDICT (pré-enregistré) : NON DÉMONTRÉ**

Jugement : bruts (prix + financement) +52.1 % contre frais 9.7 %. Sur 100 $ de capital : +21.20 $ sur 303 jours (≈ +25.53 $/an) ; sur 1 000 $ : +211.97 $ sur 303 jours (≈ +255.34 $/an) ; sur 6 $ : +1.27 $ sur 303 jours (≈ +1.53 $/an) (mais impossible : ordre minimum 10 $).
Contributions en jugement : XPL +30.4 %, ARB +27.4 %, MON +9.0 %, LTC +8.9 %, WIF +8.6 %, BCH +7.6 %, AAVE +6.6 %, CRV +6.5 %, SUI +4.9 %, ASTER +4.9 %, ADA +4.1 %, ENA +2.6 %, AVAX +2.3 %, PENGU +2.1 %, BTC +0.3 %, BNB +0.3 %, ETH -0.5 %, TAO -1.4 %, UNI -3.0 %, SOL -3.1 %, kPEPE -3.6 %, PAXG -3.7 %, FARTCOIN -4.1 %, LINK -4.2 %, HYPE -4.2 %, XRP -6.7 %, PUMP -6.8 %, DOGE -7.3 %, NEAR -14.6 %, ZEC -20.8 %

## Lecture (31/10/2026 17h15)
- **NON DÉMONTRÉ** : positif en jugement (+42,4 % par côté, soit +25,5 %/an du capital), mais **négatif sur le réglage (−59,4 %)** et sur l'entre-deux (−19,0 %), et **p = 0,13** contre des pièces tirées au hasard (le test des décalages, pour information, donne 0,018 : le hasard qui garde la même rotation est un témoin plus exigeant).
- Le gain 2026 vient surtout du **prix (+39,2 %)**, pas du financement (+12,9 %) ; deux contrats (XPL +30 %, ARB +27 %) font plus que tout le net. Ce n'est pas le portrait d'un carry qui « encaisse » : c'est un pari long/short qui a eu de la chance cette année.
- Sur tout l'historique (2023-10 → 2026-10) : −59,4 − 19,0 + 42,4 = **−36 % par côté**. Pire baisse du réglage : −218 % de 1 $ par côté, soit plus que tout le capital à levier 1 : le compte aurait été liquidé en 2024 avant de voir 2026.
- Le financement encaissé est bien positif sur chaque période (+75 %, +26 %, +13 %) et dépasse les frais (16 %, 8 %, 10 %), mais il est écrasé par le risque de prix des contrats choisis. Même conclusion qu'avec Kraken : l'effet Binance ne se transporte pas.
