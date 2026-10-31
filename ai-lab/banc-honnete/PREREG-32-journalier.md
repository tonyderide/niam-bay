# Pré-enregistrement 32 : la règle de Tony en BOUGIES JOURNALIÈRES
Écrit le 31/10/2026 à 14h5x, avant tout calcul de cette règle en journalier. PREREG-31 (même règle, bougies 1 h, panier) : **PERD**, ~500 trades par pièce et par an, frais ≈ 2× le brut ; l'inversion après perte battait le hasard en 2024-25 (p < 0,001) mais plus en 2026 (p = 0,54). Question : en bougies **journalières** avec des SL/trailing **larges**, les trades deviennent rares et les frais négligeables. Reste-t-il un avantage ?

## Ce que dit la théorie, avant les données
Agrandir les stops et l'échelle de temps divise le nombre de trades (donc les frais) mais ne crée pas d'espérance : sur une marche aléatoire, l'espérance brute reste nulle quelle que soit la sortie. La règle ne peut gagner que si les prix journaliers ont de la tendance (momentum) captée par « garder le sens après un gain » ou par l'EMA. Les études de « time-series momentum » trouvent un tel effet sur les cryptos à l'échelle de jours/semaines, mais fragile et dépendant de la période. On s'attend à un brut proche de zéro, de signe incertain, et à un résultat dominé par la direction du marché (2024-25 haussier sur BTC, 2026 baissier sur les altcoins).

## Données (les mêmes que PREREG-28 / 31, aucun nouveau téléchargement)
- ai-lab/dca-martingale/refait/donnees/*-1h.npy : Binance USDT-M, 253 perpétuels cotés au 01/01/2024 (univers.json), morts compris, chaque pièce coupée à son retrait (48 h figées, fonction `couper` identique). Données du 01/01/2024 au 30/09/2026.
- **Agrégation en jours UTC** : jour = floor(heure d'ouverture / 86 400 000 ms) ; ouverture = ouverture de la première heure du jour, haut = max, bas = min, clôture = clôture de la dernière heure. Un jour incomplet (retrait) est gardé avec les heures disponibles.
- Frais taker 0,05 % par côté, sans levier, mise égale constante par pièce (non composée, comme PREREG-28/31).
- **Funding** : les données de funding disponibles (ai-lab/carry-financement/data-univers/funding.json) ne couvrent que **69 des 253 pièces** (celles encore cotées à la collecte). Le verdict se calcule donc **sans funding** (même convention que PREREG-28/30/31). En plus, sur le sous-panier des pièces couvertes, le net **avec funding** est rapporté pour le réglage figé (et pour l'acheter-garder) : un long paie le taux, un short le reçoit ; on compte les paiements dont l'heure est entre le début du jour d'entrée et le milieu (12 h UTC) du jour de sortie, sur une position de taille constante (approximation notée).

## Règle de sortie (identique à PREREG-28 B / 31, appliquée aux bougies journalières)
- Toujours en position, entrée à l'ouverture du jour qui suit le jour de sortie précédente.
- SL fixe à s de l'entrée ; dès que le prix dépasse l'entrée de a dans le bon sens, stop = max(SL, pic × (1 − t)) (équivalent pour un short) ; pic = extrême des jours **précédents** depuis l'activation (le jour d'activation fixe le pic initial).
- Sortie au prix du stop, ou à l'ouverture si elle est déjà au-delà. **Jour ambigu = SL d'abord** (pessimiste). En journalier ce biais pèse davantage : il est mesuré par un contrôle en 1 h (voir plus bas), sans changer le verdict.
- Fin de période ou retrait : sortie au dernier prix connu.

## Grille de réglage (fixée ici, 36 réglages par variante)
- s (SL fixe) ∈ {5, 10, 15, 20} %
- a (activation du trailing) ∈ {5, 10, 20} %
- t (écart du trailing) ∈ {3, 5, 10} %

## Variantes
- **(i) Inversion après perte (règle de Tony) :** on garde le sens après un gain, on l'inverse après une perte (trade net ≤ 0). Premier trade de chaque pièce et de chaque période : long.
- **(ii) Sens par l'EMA (comme PREREG-30, longueur 50 jours) :** long si la dernière clôture **journalière terminée** est au-dessus de son EMA50 journalière, short sinon. EMA calculée sur toute l'histoire de la pièce depuis le 01/01/2024 (initialisée à la première clôture), chauffe de 50 jours sans trade (donc la variante (ii) ne trade qu'à partir de fin février 2024 ; en 2026, pas de chauffe).
- **(iii) Repère : acheter-garder**, BTC seul et panier égal (mêmes pièces), achat à la première ouverture de la période, vente à la dernière clôture (ou au retrait), frais 2 × 0,05 %, sans funding (équivalent spot).

## Choix et jugement
- **Choix du réglage UNIQUEMENT sur 01/01/2024 → 31/12/2025**, sur le panier entier : pour chaque variante, le réglage au meilleur net moyen du panier parmi les 36. Figé avant de regarder 2026.
- **JUGEMENT UNIQUE : 01/01/2026 → 30/09/2026.**
- Pièces d'une période : vivantes au début (premier jour de la tranche = jour de début), au moins 20 jours dans la période. Rendement du panier = moyenne des pièces (une pièce morte garde ses gains/pertes et reste au dénominateur).

## Témoin
- Même règle de sortie, même réglage figé, mêmes frais, mêmes pièces, même période, **sens de chaque trade au hasard** (P(long) = part de longs de la variante sur cette pièce et cette période ; pour (ii), mêmes jours de chauffe sans trade). Le nombre de trades est presque le même ; il est rapporté.
- **1 000 tirages** par variante et par période. p = part des tirages dont le net du panier est **≥** celui de la variante. Le p de 2026 est celui du verdict ; 2024-25 pour information (réglage choisi sur cette période, donc optimiste).

## Verdict (par variante, réglage figé)
- **GAGNE** si net du panier > 0 en 2024-25 **ET** > 0 en 2026 **ET** p < 0,05 contre le témoin en 2026.
- **NON DÉMONTRÉ** si le net de 2026 est > 0 sans tout le reste.
- **PERD** sinon.
- Deux variantes : un p entre 0,025 et 0,05 sera signalé fragile (Bonferroni), sans changer le verdict.

## Rapporté
- Par variante et période : net du panier, brut et frais (et part des frais dans le brut), trades par pièce et **par pièce et par an**, part de trades gagnants, part de pièces positives, pire mois, mois positifs, pire baisse (courbe cumulée du panier, trades rangés par jour de sortie), témoin (moyenne ± écart-type), p.
- Comparaison avec l'acheter-garder (BTC et panier) sur les deux périodes.
- Les 36 réglages de 2024-25 (et, pour information seulement, leur 2026 : combien de réglages sont > 0, pour voir si le choix compte).
- Contrôle du biais « jour ambigu » : le réglage figé rejoué en 2026 avec les sorties simulées sur les bougies **1 h** (entrées toujours à l'ouverture du jour UTC suivant la sortie, même sens). Pour information.
- Sous-panier funding (69 pièces au plus) : net sans et avec funding.

## Relecture d'équité, avant le calcul
- Le réglage le plus favorable de 2024-25 est choisi : biais pour la règle, voulu, corrigé par le jugement 2026 unique.
- Le témoin paie les mêmes frais et garde la volatilité ; il retire seulement l'information de sens.
- Jour ambigu compté en SL : contre la règle **et** le témoin à égalité ; mesuré par le contrôle 1 h.
- Morts compris : pas de biais du survivant. Funding partiel : dit, et calculé seulement là où il existe.
- Aucune action sur Martin ni Kraken : calcul seulement.

## Résultat (31/10/2026, 15h0x — t32.py → t32.log, chiffres complets dans t32.json)
Lancé une seule fois après le commit f09036c (pré-enregistrement seul), `nice -n 10`. 243 pièces exploitables, 243 vivantes au 01/01/2024, **187 au 01/01/2026**. Rendements en % de la mise par pièce, mise constante non composée, sans funding.

**Réglages figés sur 2024-25** : (i) SL 15 % / activation +5 % / trailing 3 % ; (ii) SL 20 % / +10 % / 3 %. Les **36 réglages sont tous négatifs en 2024-25** pour les deux variantes (i : de −75 % à −29 % ; ii : de −42 % à −6,5 %) : le « meilleur » est le moins mauvais.

| | (i) inversion — 2024-25 | (i) — **2026** | (ii) EMA50 j — 2024-25 | (ii) — **2026** |
|---|---|---|---|---|
| Net du panier | −29,2 % | **+8,6 %** | −6,5 % | **+5,6 %** |
| Pièces positives | 40 % | 55 % | 48 % | 55 % |
| Trades par pièce et par an | 73 | 60 | 37 | 31 |
| Trades gagnants | 65 % | 67 % | 64 % | 64 % |
| Brut / frais (part des frais) | −14,5 / 14,7 (brut ≤ 0) | +13,1 / 4,5 (34 %) | +0,8 / 7,3 (×9) | +7,9 / 2,3 (29 %) |
| Pire mois | −15,5 % (2024-10) | −7,3 % (2026-03) | −11,5 % (2024-10) | −12,5 % (2026-01) |
| Mois positifs | 9/24 | 5/9 | 11/23 | 3/9 |
| Pire baisse | 39,7 pts | 23,6 pts | 63,5 pts | 22,7 pts |
| Témoin sens au hasard (1 000 tirages) | −20,4 ± 7,5 % | −3,3 ± 4,6 % | −3,7 ± 7,8 % | +1,0 ± 4,9 % |
| p contre le témoin | 0,88 (info) | **0,007** | 0,63 (info) | **0,17** |
| Funding, sous-panier couvert (sans → avec) | −31,1 → −34,0 % (69) | +12,0 → +12,1 % (61) | +20,4 → +15,7 % (69) | +9,6 → +8,3 % (61) |

**(iii) Acheter-garder** (frais compris, sans funding) : BTC **+106,9 %** (2024-25) et **−4,7 %** (2026) ; panier égal **−40,0 %** (2024-25, 15 % de pièces positives) et **−14,0 %** (2026, 23 %).

Informations après figement : en 2026, 27/36 réglages de (i) et 29/36 de (ii) sont positifs (médianes +6,4 % et +4,4 %). Contrôle du jour ambigu (sorties sur bougies 1 h, 2026, réglage figé) : (i) +22,6 %, (ii) +7,3 % — le comptage « SL d'abord » pénalise surtout (i).

**VERDICT (pré-enregistré) : NON DÉMONTRÉ** pour les deux variantes : net > 0 en 2026, mais négatif en 2024-25 (condition 1 manquée). Pour (i), p = 0,007 en 2026 (sous le seuil Bonferroni 0,025) ; pour (ii), p = 0,17.

**Ce que ça montre :**
- Le journalier a fait ce qu'on attendait des frais : de ~500 à 30-70 trades par pièce et par an, frais divisés par ~7. Ce n'est plus les frais qui tuent ; c'est le brut, qui change de signe d'une période à l'autre.
- L'inversion après perte bat nettement le hasard en 2026 (+8,6 % contre −3,3 %, p = 0,007) mais faisait **pire** que le hasard en 2024-25 (p = 0,88), alors même que son réglage avait été choisi sur 2024-25. En 1 h (PREREG-31), c'était l'inverse : avantage en 2024-25, disparu en 2026. Un avantage qui change de période selon l'échelle ressemble à du bruit de régime, pas à une propriété stable.
- 2026 est une année baissière pour les altcoins (acheter-garder panier −14 %) : une règle qui peut être short y profite. Contre l'acheter-garder du panier, les deux variantes gagnent sur les deux périodes ; contre BTC acheter-garder en 2024-25 (+107 %), rien ne tient.
- Funding (partiel, 69 puis 61 pièces) : coût faible pour (i), quelques points pour (ii) qui est plus souvent long en 2024-25. Il ne change aucun signe.
- Limites : mise non composée ; jour ambigu en SL (mesuré : le vrai résultat est probablement meilleur pour (i)) ; funding seulement sur les pièces encore cotées ; un seul jugement de 9 mois.
