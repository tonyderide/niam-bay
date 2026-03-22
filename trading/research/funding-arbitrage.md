# Funding Rate Arbitrage sur Kraken Futures

> Recherche : 22 mars 2026
> Verdict : **Non viable a 100EUR. Capital minimum realiste : ~2000EUR.**

---

## 1. Le concept

Les perpetual futures ont un "funding rate" -- un paiement entre traders toutes les quelques heures pour ancrer le prix du contrat au prix spot.

- **Funding positif** : les longs paient les shorts
- **Funding negatif** : les shorts paient les longs

**L'arbitrage** : si le funding est positif (marche bullish), on ouvre simultanement :
- **LONG spot** (on achete le sous-jacent)
- **SHORT futures perpetuel** (on vend le contrat)

On est delta-neutre (le prix monte ou descend, on s'en fout) et on encaisse le funding toutes les 4 heures.

---

## 2. Kraken Futures -- Specificites

### Frequence du funding
- **Toutes les 4 heures** (6 fois par jour)
- Settlement automatique, la position est "rolled" dans le prochain contrat

### Plafonds
- Max : +/- 0.25% par heure
- Cap 24h : 6% max

### Fourchette typique
- En conditions normales : **-0.01% a +0.01% par 8h** (soit environ -0.005% a +0.005% par 4h)
- En marche bullish fort : peut monter a **0.05% - 0.2% par 8h**
- Le taux est variable et correle aux changements de prix, pas au prix lui-meme

### Contrats disponibles
- 100+ paires perpetuelles
- Symbols : `PF_XBTUSD`, `PF_ETHUSD`, etc.
- Leverage max : 50x (10x pour clients EEA/MiFID II)

### API pour les funding rates
```
GET https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD
```
Retourne : timestamp, fundingRate, relativeFundingRate.
Documentation : https://docs.kraken.com/api/docs/futures-api/trading/historical-funding-rates/

---

## 3. Les frais -- Le vrai tueur

### Frais spot Kraken (volume < 50k EUR/mois)
| | Maker | Taker |
|---|---|---|
| Spot | 0.16% | 0.26% |

### Frais futures Kraken
| | Maker | Taker |
|---|---|---|
| Perpetual | 0.02% | 0.05% |

### Cout total pour ouvrir la position (aller-retour)
En utilisant des ordres limit (maker) des deux cotes :
- Ouverture spot : 0.16%
- Ouverture futures : 0.02%
- Cloture spot : 0.16%
- Cloture futures : 0.02%
- **Total aller-retour : 0.36%**

En taker (ordres market) :
- **Total aller-retour : 0.62%**

---

## 4. Le calcul brutal -- 100EUR

### Scenario optimiste
- Capital : 100 EUR
- Split : 50 EUR en spot, 50 EUR en marge futures
- Leverage futures : 3x -> position 150 EUR notionnel
- Mais la position spot = seulement 50 EUR
- **Probleme** : la position spot doit matcher la position futures pour etre delta-neutre
- Donc : 50 EUR spot + 50 EUR futures short (sans levier supplementaire)
- Notionnel hedge : **50 EUR**

### Revenus du funding (cas moyen)
- Funding moyen optimiste : 0.01% par 8h = 0.005% par 4h
- Par jour (6 settlements) : 0.03% de 50 EUR = **0.015 EUR/jour**
- Par mois : **0.45 EUR/mois**

### Revenus du funding (cas bullish)
- Funding bullish : 0.05% par 8h = 0.025% par 4h
- Par jour : 0.15% de 50 EUR = **0.075 EUR/jour**
- Par mois : **2.25 EUR/mois**

### Couts pour ouvrir + fermer
- Aller-retour maker : 0.36% de 50 EUR = **0.18 EUR**
- Aller-retour taker : 0.62% de 50 EUR = **0.31 EUR**

### Resultat net (cas moyen)
- Revenu mensuel : 0.45 EUR
- Cout ouverture/fermeture : -0.18 EUR
- **Profit net : 0.27 EUR/mois sur 100 EUR de capital**
- **Rendement : 0.27%/mois = 3.2%/an**

### Resultat net (cas bullish)
- Revenu mensuel : 2.25 EUR
- Cout ouverture/fermeture : -0.18 EUR
- **Profit net : 2.07 EUR/mois sur 100 EUR**
- **Rendement : 2.07%/mois = 24.8%/an**

**Mais le cas bullish n'est pas permanent.** Le funding moyen historique est bien en dessous.

---

## 5. Pourquoi ca ne marche pas a 100 EUR

### Probleme 1 : Les frais spot de Kraken sont enormes
0.16% maker / 0.26% taker sur le spot, c'est un mur. Il faut 6 a 12 jours de funding moyen juste pour couvrir les frais d'ouverture. Si le funding flip negatif pendant cette periode, tu perds.

### Probleme 2 : Capital divise en deux
100 EUR = 50 EUR de chaque cote. Le notionnel est ridicule. Les gains absolus sont en centimes.

### Probleme 3 : Minimum order sizes
Sur Kraken spot, le minimum BTC est 0.0001 BTC (~8 EUR). Ca passe. Mais les frais minimum effectifs rendent les micro-positions non economiques.

### Probleme 4 : Le funding n'est pas garanti
Le funding peut flipper negatif a tout moment. En marche baissier, TU paies au lieu de recevoir. Et tu es coinced parce que fermer = payer les frais de cloture.

### Probleme 5 : Risque de liquidation
Meme avec la position spot en hedge, si le prix monte brutalement, ta position short futures peut etre liquidee avant que tu puisses ajouter de la marge. Avec 50 EUR de marge, une montee de 10-20% peut te liquider selon le levier.

### Probleme 6 : Basis risk
Le prix futures et le prix spot ne sont pas identiques. L'ecart (basis) peut bouger contre toi.

---

## 6. A quel capital ca devient viable ?

| Capital | Notionnel | Funding/mois (moyen) | Frais A/R | Profit net | Rendement |
|---|---|---|---|---|---|
| 100 EUR | 50 EUR | 0.45 EUR | 0.18 EUR | 0.27 EUR | 0.27% |
| 500 EUR | 250 EUR | 2.25 EUR | 0.90 EUR | 1.35 EUR | 0.27% |
| 2000 EUR | 1000 EUR | 9.00 EUR | 3.60 EUR | 5.40 EUR | 0.27% |
| 5000 EUR | 2500 EUR | 22.50 EUR | 9.00 EUR | 13.50 EUR | 0.27% |

Le rendement en pourcentage ne change pas, mais le **profit absolu** devient significatif seulement a partir de ~2000 EUR. Et encore, 5.40 EUR/mois pour 2000 EUR immobilises, c'est anecdotique.

**Avec du levier sur le futures** (2-3x) et un marche bullish persistant, les chiffres s'ameliorent :
- 2000 EUR capital, 1000 EUR spot + 1000 EUR marge a 3x = 3000 EUR short futures
- Mais spot = 1000 EUR seulement -> pas delta-neutre !
- Il faut matcher : 1000 EUR spot = 1000 EUR short futures
- Le levier permet de mettre moins de marge (333 EUR pour 1000 EUR short a 3x)
- Capital reel : 1000 EUR spot + 333 EUR marge = **1333 EUR pour 1000 EUR de notionnel**
- Funding bullish (0.05%/8h) : 0.15%/jour x 1000 EUR = 1.50 EUR/jour = **45 EUR/mois**
- Rendement : 45 / 1333 = **3.4%/mois** en cas bullish

C'est mieux. Mais c'est le cas bullish, pas la norme.

---

## 7. Automatisation

### Strategie algorithmique
```
1. Toutes les 4h, checker le funding rate via API
2. Si funding > seuil (ex: 0.01%/4h) pendant 3+ periodes :
   -> Ouvrir spot long + futures short
3. Si funding < 0 pendant 2+ periodes :
   -> Fermer les positions
4. Monitorer le spread spot/futures
5. Monitorer la marge de maintenance
```

### API Kraken necessaires
- Funding rates : `GET /derivatives/api/v4/historicalfundingrates`
- Tickers (prix) : `GET /derivatives/api/v4/tickers`
- Ordres spot : API REST Kraken standard
- Ordres futures : API Futures Kraken
- Python SDK : `python-kraken-sdk` (pip install python-kraken-sdk)

### Complexite
- Il faut gerer DEUX APIs (spot Kraken + Futures Kraken)
- Synchroniser les ordres des deux cotes
- Gerer les echecs partiels (spot execute mais pas le futures)
- Monitorer la marge en continu
- **C'est un vrai projet de bot, pas un script de 50 lignes**

---

## 8. Alternatives plus realistes a 100 EUR

1. **Juste tracker les funding rates** : monitorer sans trader, comprendre les patterns
2. **DCA simple** : 100 EUR en BTC/ETH, c'est plus efficace
3. **Martin Grid** (deja en place) : le grid trading est plus adapte au petit capital
4. **Attendre 1000-2000 EUR** : et revenir sur cette strategie a ce moment

---

## 9. Verdict final

**Le funding rate arbitrage est une strategie reelle et utilisee par les pros.** Mais :

- A **100 EUR**, c'est mort. Les frais spot de Kraken (0.16-0.26%) mangent le peu de funding gagne. Le profit est en centimes.
- A **2000 EUR** avec levier modere et un marche bullish, on parle de ~15-45 EUR/mois. Correct mais pas transformateur.
- A **10 000+ EUR** avec acces a des frais reduits (volume trading), ca devient une vraie strategie.
- L'automatisation est non triviale : deux APIs, gestion de marge, synchronisation d'ordres.

**Recommandation** : Ne pas implementer maintenant. Construire un moniteur de funding rates (API gratuite, zero risque) pour observer les patterns pendant quelques semaines. Si les taux sont systematiquement positifs et interessants, revisiter avec plus de capital.

---

## Sources

- [Kraken : Contract Specifications](https://support.kraken.com/articles/4844359082772-linear-multi-collateral-derivatives-contract-specifications)
- [Kraken Blog : Primer on Funding Rates](https://blog.kraken.com/product/quick-primer-on-funding-rates)
- [Kraken API : Historical Funding Rates](https://docs.kraken.com/api/docs/futures-api/trading/historical-funding-rates/)
- [Kraken : Fee Schedule](https://www.kraken.com/features/fee-schedule)
- [CoinGlass : What is Funding Rate Arbitrage](https://www.coinglass.com/learn/what-is-funding-rate-arbitrage)
- [CF Benchmarks : Kraken Perpetual Funding Rate Index](https://www.cfbenchmarks.com/data/indices/KFRI)
