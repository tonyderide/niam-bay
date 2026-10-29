# Résultat PREREG-30 : règle de Tony, sens donné par l'EMA (29/10/2026, 21h4x)
Pré-enregistrement : ../banc-honnete/PREREG-30-ema-sens.md (commit 1660701 à 21h47, avant calcul). Code : etude.py ; chiffres : resultats.json.

**Réglage figé sur BTC 2024-2025 :** EMA 50 horaire, SL 5 %, trailing activé à +3 %, trailing 1 %. C'est le meilleur des 468 réglages, et seuls 19 sur 468 étaient positifs.

| Terrain (jugement unique) | Trades | Gagnants | Espérance / trade | Mise fixe 10 € | Brut / frais | Mois positifs (fixe / martingale ×2 plafonnée à 3) | Pire mois (fixe / martingale) | Contre le hasard (sens tiré au sort) |
|---|---|---|---|---|---|---|---|---|
| BTC 2026 | 88 | 65 % | +0,042 mise | **+37 €** | 27 % / 9 % | 6/9 · 6/9 | −44 € / −17 € | p = 0,28 |
| ETH 2024-2026 | 806 | 65 % | +0,020 mise | **+161 €** | 161 % / 81 % | 16/33 · 21/33 | −81 € / −308 € | **p = 0,04** |
| SOL 2024-2026 | 1 284 | 62 % | −0,029 mise | **−374 €** | −58 % / 128 % | 14/33 · 15/33 | −92 € / −257 € | p = 0,54 |

**VERDICT : NON DÉMONTRÉ.**
- Deux terrains sur trois sont positifs, mais seul ETH bat le hasard (p = 0,04), et SOL perd.
- Pour un vrai avantage, il faudrait les trois terrains positifs et au-dessus du hasard.

**Krach SOL du 10/10/2025 avec l'EMA :**
- 21 trades, tous à la vente (l'EMA dit « baisse »), aucun achat.
- Mise fixe : **+23 €**. Martingale plafonnée : 913 €, sans ruine. Sans l'EMA et avec ta martingale, c'était 602 € et la ruine.

**Ce que ça montre :** l'EMA empêche de se retourner à contre-tendance dans un krach, et c'est la vraie amélioration. Mais sur 33 mois, la règle reste proche de zéro : légèrement positive sur BTC et ETH, négative sur SOL. Ce n'est pas encore distinguable de la chance.
