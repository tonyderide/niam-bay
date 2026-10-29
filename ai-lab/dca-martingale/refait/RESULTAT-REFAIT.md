# PREREG-24 refait entièrement à neuf (29/10/2026, 14h46 → 15h0x)
Demande de Tony : « Refais tes calculs entièrement à neuf ». Rien de la 1re version n'est réutilisé :
- **univers** reconstruit depuis l'index de data.binance.vision (univers.py) : 253 perpétuels USDT ayant une archive 1 h en 12/2023 et en 01/2024. La 1re liste (tirée du dossier carry) en avait 245 : il manquait BTCST, CTK, CVC, CVX, LIT, MDT, SLP, SXP ;
- **bougies** re-téléchargées dans un nouveau dossier, SHA-256 de chaque archive vérifiée contre le .CHECKSUM de Binance (7 512 archives 1 h ok, 0 fausse ; 375 mois absents = pièce pas encore ou plus cotée ; 27 archives 5 min ok) ;
- **simulateur** réécrit depuis le texte du pré-enregistrement (simu.py), en deux versions indépendantes (Python pur et compilée) : identiques sur 215 715 cycles synthétiques (verifier.py), et égales à deux cycles calculés à la main (cas_a_la_main.py) ;
- règle un peu plus stricte : un OS limite se remplit à son prix, même si la bougie ouvre dessous (sans effet mesurable en 1 h).

## Défaut trouvé dans les données (touchait aussi la 1re version)
Après un retrait de la cote, Binance continue d'archiver des bougies **figées** (haut = bas) pendant des mois : 81 pièces sur 253. Pire, un nom peut être **réutilisé** par une nouvelle pièce : LIT, figé à 0,59 $ de janvier à décembre 2025, « repart » à 3,73 $ ; le bot y gagnait +223 % fictifs. Dans la 1re version, ces périodes figées comptaient comme des pièces à rendement ~0 (d'où la médiane « −0,0 »), ce qui diluait les moyennes.
Correction : chaque pièce est coupée à sa première série de 48 h figées (= retrait ; le pré-enregistrement dit « sortie au dernier prix connu »). Même résultat avec un seuil de 12 h ou de 168 h. En 2026 il reste 188 pièces réellement cotées (et non 230).
Contrôle : sans cette coupure et sur les 245 pièces de la 1re liste, le nouveau code redonne exactement le +0,37 % de la 1re version (réglage figé, 2024-2025).

## Résultats (refait, données coupées au retrait)
| | 1re version | **Refait** |
|---|---|---|
| Réglage figé (choisi sur 2024-2025) | d 3 %, TP 2,5 %, trailing 0,5 %, 5 OS, SL 8 % | **le même** |
| Réglages positifs en 2024-2025 | 1 / 72 | 2 / 72 |
| Figé, 2024-2025 | +0,37 % | +0,49 % (243 pièces) |
| **Figé, 2026 (jugement)** | −0,46 % (230 pièces) | **−0,57 %** (188 pièces) |
| Cycles gagnants 2026 | 94,0 % | 94,2 % |
| Pièces positives 2026 | 89 / 230 | 89 / 188 |
| Gains bruts / frais 2026 | — / 1,37 | **0,30 / 1,37** |
| Pire cycle | −19,9 % | −19,9 % |
| Témoin (a) acheter et garder 2026 | −11,4 % | −13,9 % |
| Témoin (b) sans martingale 2026 | −1,6 % | −1,9 % |
| Classique 2024-2025 / 2026 | −10,4 % / +3,0 % | −10,5 % / +3,7 % |
| Réglages positifs en 2026 | 25 / 72, médiane −1,2 % | 25 / 72, médiane −1,5 % |

Critères : rendement > 0 **non** ; > (a) oui ; > (b) oui ; gains > frais **non** (les gains bruts ne paient qu'un quart des frais). **VERDICT : PERD**, confirmé.

## Contrôle 5 min (inchangé : BTC, ETH, SOL n'ont pas de période figée)
Figé : BTC +3,4 → +3,4 % ; ETH −11,0 → −12,6 % ; SOL −7,9 → −10,4 % (SUSPECT). Classique : BTC −6,6 → −9,1 % (SUSPECT) ; ETH −0,8 → **+1,9 %** (SUSPECT, signe changé, ici le 5 min est *meilleur*) ; SOL −16,4 → −14,5 %.
Correction de la 1re version, qui disait « le 5 min compte, il est pire » : c'est vrai pour SOL et BTC, pas pour ETH classique. Aucun de ces écarts ne change le verdict.
