# Pré-enregistrement 56 : réplication de PREREG-46 sur Hyperliquid (morts compris)
Écrit le 02/11/2026 vers 15h CET, avant de télécharger les bougies et avant tout calcul. Hypothèse H19 de FILE-HYPOTHESES.md. Regardé avant ce commit (faisabilité) : la liste publique `meta` (235 contrats dont 56 retirés, `isDelisted`) et deux bougies de contrats retirés (MATIC, RNDR : historique encore servi ; MATIC a des bougies dès 2020, antérieures au lancement d'Hyperliquid — d'où la date plancher ci-dessous).

## Pourquoi
PREREG-46 (GAGNE), PREREG-53 et 54 (RÉPLIQUÉ). Quatrième population, avec un avantage de méthode : les contrats retirés sont dans la liste, donc **morts compris**.

## Données (publiques, sans clé)
- `info` → `meta` (liste, retirés compris) ; `candleSnapshot` 1d de chaque contrat.
- Date de cotation = première bougie journalière, **seulement si elle est postérieure au 01/06/2023** (avant, l'historique servi ne reflète pas une cotation sur Hyperliquid).
- **Financement non compté** (l'historique demande des dizaines de milliers de requêtes limitées) : déclaré, comme PREREG-54.

## Règle (celle de PREREG-46, N = 90)
Short à l'ouverture de la 2e bougie, 90 jours (ou jusqu'à la dernière bougie si retrait), rendement = −(sortie / entrée − 1) − 2 × 0,045 % (taker Hyperliquid palier 0), plancher −100 %. Entrées du **01/06/2023 au 29/07/2026**.

## Jugement
- **Témoin** : pour chaque trade, short d'un contrat Hyperliquid dont la première bougie précède l'entrée de plus de 365 jours (bougie le jour d'entrée), tiré au hasard, même date ; 1 000 tirages, graine 56. Retirés compris des deux côtés.
- **RÉPLIQUÉ** si rendement moyen > 0 **ET** p < 0,05. **NON RÉPLIQUÉ** sinon. **NON ÉVALUABLE** si moins de 30 trades.
- **Information** (ne change pas le verdict) : Hyperliquid cote souvent des pièces déjà anciennes ailleurs ; on rapporte aussi le résultat restreint aux pièces **absentes du comptant et des perpétuels Binance** avant leur cotation sur Hyperliquid (fichiers comptant/premiers_mois.json et data-univers/klines.json).

## Relecture d'équité
N, frais, date plancher et témoin fixés ici. Aucun compte, aucune clé, aucune action sur Martin ni Kraken.

## Résultat (02/11/2026, 15h3x — t56.py → t56.log, chiffres dans t56.json)
Lancé une seule fois après le commit 34f42d7, `nice -n 10`. 235 contrats (56 retirés), tous avec bougies ; 157 trades, dont **45 sur des contrats retirés depuis** (morts compris).

| | Trades | Moyenne | Médiane | Positifs | Au plancher | Témoin (anciens, même date) | p |
|---|---|---|---|---|---|---|---|
| **Toutes entrées 06/2023 → 07/2026** | 157 | **+12,7 %** | +29,2 % | 64 % | **20 (13 %)** | −1,7 % | **< 0,001** |
| Info : pièces absentes de Binance avant | 134 | +16,0 % | +36,0 % | 66 % | 16 | +2,6 % | < 0,001 |

Par année : **2023 −36,9 % (42 trades)** · 2024 +23,1 % (59) · 2025 +39,3 % (51) · 2026 +36,4 % (5). Sans financement.

**VERDICT (pré-enregistré) : RÉPLIQUÉ** — rendement moyen > 0, p < 0,001 contre le témoin, morts compris.

**Ce que ça montre :**
- Quatrième population, et la première où les morts sont dans les deux camps : l'effet tient (+12,7 % par trade contre −1,7 % pour le short d'un contrat ancien).
- Mais la **queue est lourde** : 13 % des trades perdent toute la mise (×2 ou plus en 90 jours), et toute la cohorte du second semestre 2023 (42 trades, reprise du marché) perd −37 % en moyenne. Le même schéma qu'OKX 2023 : dans une reprise forte, les jetons neufs s'envolent et le short est ruiné. C'est le risque à mesurer avant toute idée d'exploitation (prochain tick : H20).
