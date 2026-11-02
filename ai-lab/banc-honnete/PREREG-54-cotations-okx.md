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
