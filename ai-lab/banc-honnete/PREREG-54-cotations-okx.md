# Pré-enregistrement 54 : réplication de PREREG-46 sur OKX — vendre à découvert les nouvelles cotations y rapporte-t-il ?
Écrit le 02/11/2026 vers 11h CET, avant de télécharger les bougies et avant tout calcul. Hypothèse H17 de FILE-HYPOTHESES.md. Regardé avant ce commit (pour savoir si le test est faisable, pas les prix) : la liste publique des perpétuels OKX (`public/instruments`, 517 perpétuels USDT dont 304 crypto, `instCategory` = 1) et le fait que l'historique public du financement ne remonte que de quelques mois.

## Pourquoi
PREREG-46 (GAGNE, perpétuels Binance) et PREREG-53 (RÉPLIQUÉ, comptant Binance 2018-2026). Troisième population : une **autre plateforme** (autre clientèle, autre politique de cotation).

## Données (publiques, sans clé)
- Perpétuels **USDT, `instCategory` = 1 (crypto)** de `api/v5/public/instruments`, `listTime` comme date de cotation.
- Bougies journalières UTC : `api/v5/market/history-candles` (bar 1Dutc).
- **Limites déclarées** : (1) seuls les contrats **encore cotés** sont listés : les retirés manquent, des deux côtés (règle et témoin) — biais symétrique de survie, probablement défavorable au short (les jetons neufs retirés se sont souvent effondrés) ; (2) **pas de financement** (historique public trop court) : rapporté comme non compté ; en PREREG-46 il coûtait 1 à 2 % par trade au short.

## Règle (celle de PREREG-46, N = 90 figé)
Short à l'ouverture de la 2e bougie journalière suivant `listTime`, 90 jours (clôture de la 90e bougie), rendement = −(sortie / entrée − 1) − 2 × 0,05 % (taker OKX de base), plancher −100 %. Entrées du **01/01/2021 au 29/07/2026**.

## Jugement
- **Témoin** : pour chaque trade, short d'un perpétuel crypto OKX coté depuis plus de 365 jours (bougie le jour d'entrée), tiré au hasard, même date, même règle ; 1 000 tirages, graine 54.
- **RÉPLIQUÉ** si rendement moyen > 0 **ET** p < 0,05 sur toutes les entrées 2021-2026. **NON RÉPLIQUÉ** sinon. Rapporté aussi : 2026 seul, par année.
- Si moins de 30 trades : NON ÉVALUABLE.

## Relecture d'équité
N, frais, période et témoin fixés ici. Aucun compte, aucune clé, aucune action sur Martin ni Kraken.

## Résultat (02/11/2026, midi — t54.py → t54.log, chiffres dans t54.json)
Lancé une seule fois après le commit dfb339b, `nice -n 10`. 289 perpétuels crypto USDT encore cotés, tous avec bougies.

| | Trades | Moyenne | Médiane | Positifs | Au plancher | Témoin (anciennes, même date) | p |
|---|---|---|---|---|---|---|---|
| **Toutes entrées 2021 → 07/2026** | 230 | **+23,1 %** | +37,8 % | 72 % | 17 | +9,7 % | **< 0,001** |
| 2026 seul (info) | 37 | +28,9 % | +51,0 % | 81 % | 3 | +6,7 % | < 0,001 |

Par année : 2021 +18,2 % (22) · 2022 +37,6 % (8) · **2023 −11,9 % (28)** · 2024 +4,0 % (45) · 2025 +40,9 % (90) · 2026 +28,9 % (37). Sans financement (non disponible).

**VERDICT (pré-enregistré) : RÉPLIQUÉ** — rendement moyen > 0 et p < 0,001 contre le témoin.

**Ce que ça montre :**
- Troisième population, même résultat : les jetons neufs cotés sur OKX perdent en moyenne bien plus que les pièces anciennes sur leurs 90 premiers jours (+23 % pour le short contre +10 % pour le short d'une pièce ancienne).
- Pas tous les ans : 2023 est négative (−12 %, année de reprise où les jetons neufs ont monté) et 2024 faible. Un short systématique peut donc perdre une année entière.
- Limites : survivants seulement (des deux côtés) et financement non compté (en PREREG-46 il coûtait 1 à 2 % par trade) : l'ordre de grandeur reste très au-dessus de ces coûts.
