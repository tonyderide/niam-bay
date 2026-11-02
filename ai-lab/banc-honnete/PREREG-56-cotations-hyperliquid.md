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
