# Résultat PREREG-24 : martingale DCA (ordres de sécurité ×2) + trailing stop + SL (29/10/2026, 09h2x)
Pré-enregistrement : ../banc-honnete/PREREG-24-dca-martingale.md (commit a0a253c, 09h14, avant données). Code : etude.py, collecte.py. Données : Binance USDT-M 1 h, 245 perpétuels cotés au 01/01/2024, morts compris ; 230 encore cotés en 2026.

**VERDICT (pré-enregistré) : PERD.** — **Refait entièrement à neuf le 29/10 après-midi : voir refait/RESULTAT-REFAIT.md (même verdict, −0,57 % ; défaut des données figées après retrait corrigé).**

## Le « 90 % » est vrai
| | Cycles | Cycles gagnants | Rendement moyen du capital réservé |
|---|---|---|---|
| Réglage figé (d 3 %, TP 2,5 %, trailing 0,5 %, 5 OS, SL 8 %), 2024-2025 | 113 860 | **95,6 %** | +0,37 % en 2 ans |
| Réglage figé, **2026 (jugement)** | 25 950 | **94,0 %** | **−0,46 %** |
| Réglage classique (d 2 %, TP 1,5 %, 0,5 %, 5 OS, SL 8 %), 2024-2025 | 242 918 | 92,8 % | −10,4 % |
| Réglage classique, 2026 | 56 235 | 92,3 % | +3,0 % |

## Verdict, critère par critère (réglage figé, 2026)
- rendement moyen > 0 : **non** (−0,46 %) ;
- > (a) acheter et garder (−11,4 %) : oui ;
- > (b) même règle sans martingale (−1,6 %) : oui ;
- ≥ 3 pièces gagnantes (89 / 230) ET gains > frais : **non** (gains nets −1,07 contre 1,37 de frais).
→ PERD.

## Ce qui est rapporté en plus
- Sur 2024-2025, **1 réglage sur 72** est positif (celui qui a été figé, +0,37 % en deux ans). Sur 2026, 25 sur 72 sont positifs ; médiane −1,2 %, de −20 % à +4 %.
- Le réglage classique fait +3,0 % en 2026, mais −10,4 % sur 2024-2025 : choisi après coup, il ne compte pas (c'est exactement le piège des « 3 mois qui marchent »).
- Pire cycle : −15 à −20 % du capital réservé (tous les OS exécutés puis SL). Un seul de ces cycles efface environ 50 cycles gagnants.
- Il bat « acheter et garder » parce que le marché a baissé (−11 % en 2026, −39 % en 2024-2025) et que la stratégie est la plupart du temps peu investie, pas parce qu'elle gagne.

## Contrôle d'artefact (5 min contre 1 h, BTC / ETH / SOL, 2026)
| | BTC | ETH | SOL |
|---|---|---|---|
| figé 1 h → 5 min | +3,4 → +3,4 % | −11,0 → −12,6 % | −7,9 → **−10,4 %** (> 30 %) |
| classique 1 h → 5 min | −6,6 → **−9,1 %** | −0,8 → **+1,9 %** (signe) | −16,4 → −14,5 % |
Le 1 h est légèrement trop optimiste (SOL et BTC classique marqués SUSPECT : le 5 min compte, il est pire). Le verdict PERD n'en est que renforcé.

## En clair
Gagner 94 cycles sur 100 est réel. Mais les 6 autres coûtent autant que les 94 rapportent, puis les frais font le reste. Le SL limite la casse d'un cycle (−15 à −20 %) au lieu de la ruine, et le trailing laisse courir les rebonds : ils rendent la martingale *moins dangereuse*, pas *gagnante*.
