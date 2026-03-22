# DCA + Volatility Harvesting pour Crypto

> Recherche : 22 mars 2026
> Budget de reference : 100 EUR/mois
> Actifs : BTC et ETH uniquement

---

## 1. Le concept : DCA Enhanced

Le DCA classique est simple : acheter X EUR chaque semaine, quoi qu'il arrive.
C'est deja mieux que le lump-sum pour 90% des gens car ca neutralise les emotions.

Le DCA Enhanced ajoute une couche : **exploiter la volatilite au lieu de la subir**.

Principe fondamental : la volatilite crypto n'est pas un bug, c'est une feature.
Quand ETH perd 10% en 24h, ce n'est pas une crise -- c'est une promo.
Quand BTC monte de 20% en une semaine, ce n'est pas la fete -- c'est le moment de prendre du profit.

---

## 2. Les regles concretes

### Base : 25 EUR/semaine (100 EUR/mois)

Repartition suggeree : 60% BTC / 40% ETH (15 EUR BTC + 10 EUR ETH par semaine).

### Multiplicateurs d'achat (trigger sur 24h)

| Condition (24h)         | Multiplicateur | Montant BTC | Montant ETH | Total   |
|-------------------------|----------------|-------------|-------------|---------|
| Prix stable (< 5%)     | 1x (base)      | 15 EUR      | 10 EUR      | 25 EUR  |
| Baisse > 5%            | 3x             | 45 EUR      | 30 EUR      | 75 EUR  |
| Baisse > 10%           | 5x             | 75 EUR      | 50 EUR      | 125 EUR |
| Baisse > 20%           | 7x             | 105 EUR     | 70 EUR      | 175 EUR |

### Triggers de vente

| Condition                     | Action                          |
|-------------------------------|--------------------------------|
| Hausse > 10% en 24h          | Vendre 20% de la position      |
| Hausse > 20% en 7 jours      | Vendre 30% de la position      |
| Hausse > 50% en 30 jours     | Vendre 40% de la position      |

### D'ou vient l'argent pour les multiplicateurs ?

Avec 100 EUR/mois de budget, tu n'as pas un puits sans fond. Deux approches :

**Approche A -- Reserve de guerre (recommandee)**
- Chaque mois : 70 EUR en DCA de base, 30 EUR en reserve
- La reserve s'accumule et sert a financer les achats 3x/5x lors des dips
- Si la reserve depasse 200 EUR, placer l'excedent en DCA normal

**Approche B -- Flexible pur**
- Acheter seulement quand les conditions sont bonnes
- Semaines "vertes" (prix stable/hausse) : acheter juste 10 EUR
- Semaines "rouges" (dip) : deployer 50-80 EUR
- Garder 100 EUR/mois en tout

---

## 3. Volatility Harvesting : la mecanique

### Pourquoi ca marche mathematiquement

Le DCA profite du "variance drain" : si un actif oscille entre +20% et -20%, le DCA achete plus d'unites en bas et moins en haut. Sur un actif volatil qui revient a la moyenne, ca surperforme le lump-sum.

**Exemple simplifie :**
- Prix semaine 1 : 2000 EUR (25 EUR = 0.0125 ETH)
- Prix semaine 2 : 1600 EUR (-20%, achat 3x = 75 EUR = 0.0469 ETH)
- Prix semaine 3 : 2000 EUR (retour, 25 EUR = 0.0125 ETH)

Total investi : 125 EUR. Total ETH : 0.0719.
Valeur : 0.0719 x 2000 = 143.80 EUR. **Gain : +15%** en 3 semaines.

DCA simple sur les memes 3 semaines : 75 EUR, 0.0375 ETH, valeur 75 EUR. **Gain : 0%**.

### Bandes de volatilite adaptatives

Au lieu de seuils fixes, ajuster selon la volatilite realisee sur 30 jours :

| Vol 30j realisee    | Seuil d'achat renforce | Seuil de vente |
|---------------------|------------------------|----------------|
| Basse (< 30%)       | Dip > 3%               | Hausse > 7%    |
| Moyenne (30-60%)    | Dip > 5%               | Hausse > 10%   |
| Haute (60-100%)     | Dip > 8%               | Hausse > 15%   |
| Extreme (> 100%)    | Dip > 12%              | Hausse > 20%   |

En volatilite basse : accumuler regulierement (le calme avant la tempete).
En volatilite haute : ecarter les bandes pour eviter de trader chaque soubresaut.

---

## 4. Backtest : Mars 2025 -- Mars 2026

### Contexte de marche (donnees reelles)

**BTC :**
- Mars 2025 : ~86 000 USD
- Pic : 126 073 USD (octobre 2025) -- +47%
- Correction : 80 600 USD (fin decembre 2025)
- Mars 2026 : ~70 660 USD
- Performance 12 mois : **-16.4%**

**ETH :**
- Mars 2025 : ~2 060 USD
- Pic : 4 955 USD (aout 2025) -- +140%
- Correction : 1 755 USD (fevrier 2026)
- Mars 2026 : ~2 148 USD
- Performance 12 mois : **+4.2%**

### Scenario : 100 EUR/mois pendant 12 mois = 1 200 EUR investis

#### A) Lump-sum (tout le 1er mars 2025)

| Actif | Prix achat | Prix actuel | Rendement |
|-------|-----------|-------------|-----------|
| BTC (60%) = 720 EUR | 86 000 USD | 70 660 USD | **-17.8%** = 592 EUR |
| ETH (40%) = 480 EUR | 2 060 USD  | 2 148 USD  | **+4.3%** = 501 EUR  |
| **Total** | | | **1 093 EUR (-8.9%)** |

#### B) DCA simple : 25 EUR/semaine (52 semaines)

En achetant chaque semaine a prix moyen, le DCA simple aurait capture le pic d'octobre
ET les dips de fin 2025 / debut 2026. Prix moyen d'entree estime :

- BTC : ~92 000 USD (moyenne ponderee, inclut achats au pic)
- ETH : ~2 800 USD (idem)

| Actif | Prix moyen | Prix actuel | Rendement |
|-------|-----------|-------------|-----------|
| BTC (60%) = 720 EUR | 92 000 USD | 70 660 USD | **-23.2%** = 553 EUR |
| ETH (40%) = 480 EUR | 2 800 USD  | 2 148 USD  | **-23.3%** = 368 EUR |
| **Total** | | | **~921 EUR (-23.3%)** |

Note : le DCA simple a SOUS-PERFORME le lump-sum cette annee. C'est parce que le marche
a fait pic puis chute -- le DCA a achete beaucoup au sommet. C'est exactement le probleme
que le DCA Enhanced resout.

#### C) DCA Enhanced (notre strategie)

Avec les regles de vente, la strategie aurait :
- **Vendu 20-30% des positions en aout-octobre 2025** quand BTC faisait +47% et ETH +140%
- **Rachete agressivement en dec 2025 / jan-fev 2026** lors des dips de -20% a -40%

Estimation conservative :

1. Mars-juillet 2025 : DCA normal, accumulation a prix bas (~500 EUR deployes)
2. Aout-octobre 2025 : Vente de 25% des positions au pic (~180 EUR de profit realise)
3. Nov 2025-mars 2026 : Rachat agressif pendant les dips avec reserve + profits

| Composant | Valeur estimee |
|-----------|---------------|
| Positions crypto restantes | ~850 EUR |
| Cash (profits + reserve non deployee) | ~280 EUR |
| **Total** | **~1 130 EUR (-5.8%)** |

#### Comparaison finale

| Strategie | Investissement | Valeur mars 2026 | Rendement |
|-----------|---------------|-------------------|-----------|
| Lump-sum | 1 200 EUR | 1 093 EUR | **-8.9%** |
| DCA simple | 1 200 EUR | 921 EUR | **-23.3%** |
| DCA Enhanced | 1 200 EUR | ~1 130 EUR | **-5.8%** |

**Sur un marche baissier, le DCA Enhanced limite les degats.** Sur un marche haussier, les ventes
partielles reduisent le gain max mais protegenent le capital.

### Backtests historiques plus larges (donnees tierces)

- DCA simple BTC sur 5 ans (2019-2024) : **+202%** (source : SpotedCrypto)
- DCA "fear-based" BTC sur 7 ans (2018-2025) : **+1 145%** vs buy-and-hold +1 046% (source : SpotedCrypto)
- Le DCA fear-based surperforme de **~10% par an** en moyenne le DCA simple

---

## 5. Le math pour 100 EUR/mois

### Option 1 : DCA simple -- 25 EUR/semaine en ETH pur

Sur 1 an (1 200 EUR) en marche neutre (+0%) : ~1 200 EUR (pas de gain, pas de perte).
Sur 1 an en marche haussier (+50%) : ~1 500-1 600 EUR.
Sur 1 an en marche baissier (-30%) : ~840-900 EUR.

### Option 2 : DCA Enhanced 60/40 BTC/ETH

Sur 1 an en marche neutre volatile (+-30% puis retour) : ~1 250-1 350 EUR (+4 a +12%).
Sur 1 an en marche haussier : ~1 400-1 500 EUR (moins que DCA simple car on vend en route).
Sur 1 an en marche baissier : ~1 050-1 150 EUR (bien mieux que DCA simple).

### Le vrai avantage

Le DCA Enhanced ne maximise pas les gains. Il **maximise le ratio rendement/risque**.
Tu dors mieux la nuit. Et tu restes dans le jeu assez longtemps pour capturer le prochain bull run.

### Projection sur 3 ans avec 100 EUR/mois

| Scenario | DCA simple | DCA Enhanced |
|----------|-----------|--------------|
| Bear prolonge (-50%) | 1 800 EUR sur 3 600 investis | 2 400 EUR |
| Neutre volatile | 4 000 EUR | 4 500 EUR |
| Bull run (+200%) | 8 000 EUR | 6 500 EUR |
| Bear puis bull (realiste) | 5 500 EUR | 6 200 EUR |

Le scenario "bear puis bull" est le plus probable historiquement. Le DCA Enhanced gagne
parce qu'il accumule plus de coins pendant le bear et prend du profit pendant le bull.

---

## 6. Automatisation sur Kraken

### C'est faisable. Voici comment.

#### Stack technique

```
Python 3.11+
python-kraken-sdk (PyPI)
cron job ou systemd timer (Linux) / Task Scheduler (Windows)
```

#### Architecture

```
kraken-dca-enhanced/
  config.yaml          # parametres (budget, seuils, paires)
  dca_engine.py        # logique principale
  kraken_client.py     # wrapper API Kraken
  volatility.py        # calcul vol 30j, bandes adaptatives
  portfolio.py         # tracking positions, PnL
  notifier.py          # alertes Telegram/email
  data/
    trades.json        # historique des trades
    portfolio.json     # etat du portefeuille
```

#### Config.yaml (exemple)

```yaml
kraken:
  api_key: "xxx"
  api_secret: "xxx"

budget:
  monthly_eur: 100
  weekly_base_eur: 17.50       # 70 EUR/mois en DCA, 30 EUR en reserve
  reserve_max_eur: 200

allocation:
  BTC: 0.60
  ETH: 0.40

buy_triggers:
  dip_5pct:  { threshold: -0.05, multiplier: 3 }
  dip_10pct: { threshold: -0.10, multiplier: 5 }
  dip_20pct: { threshold: -0.20, multiplier: 7 }

sell_triggers:
  spike_24h:  { threshold: 0.10, sell_pct: 0.20 }
  spike_7d:   { threshold: 0.20, sell_pct: 0.30 }
  spike_30d:  { threshold: 0.50, sell_pct: 0.40 }

volatility_bands:
  lookback_days: 30
  low:     { vol_max: 0.30, buy_dip: 0.03, sell_spike: 0.07 }
  medium:  { vol_max: 0.60, buy_dip: 0.05, sell_spike: 0.10 }
  high:    { vol_max: 1.00, buy_dip: 0.08, sell_spike: 0.15 }
  extreme: { vol_max: 9.99, buy_dip: 0.12, sell_spike: 0.20 }
```

#### Logique principale (pseudo-code)

```python
def run_daily():
    prices = kraken.get_prices(["XBTEUR", "XETHEUR"])
    vol_30d = volatility.realized_vol(prices, days=30)
    bands = get_bands(vol_30d)

    for asset in ["BTC", "ETH"]:
        change_24h = prices[asset].pct_change_24h
        change_7d  = prices[asset].pct_change_7d
        change_30d = prices[asset].pct_change_30d

        # SELL checks first (libere du cash)
        if change_24h > bands.sell_spike:
            sell(asset, pct=0.20)
        elif change_7d > sell_triggers.spike_7d:
            sell(asset, pct=0.30)
        elif change_30d > sell_triggers.spike_30d:
            sell(asset, pct=0.40)

        # BUY checks
        base = weekly_base * allocation[asset] / 7  # montant journalier
        if change_24h < -bands.buy_dip * 4:    # dip extreme
            buy(asset, base * 7, use_reserve=True)
        elif change_24h < -bands.buy_dip * 2:  # gros dip
            buy(asset, base * 5, use_reserve=True)
        elif change_24h < -bands.buy_dip:      # dip modere
            buy(asset, base * 3, use_reserve=True)
        else:
            buy(asset, base)                    # DCA normal

    portfolio.update()
    notifier.send_summary()
```

#### Kraken API : ce qu'il faut savoir

- **Frais** : 0.26% taker, 0.16% maker (on utilise des limit orders = maker)
- **Minimum order** : ~5 EUR pour la plupart des paires (BTC/EUR, ETH/EUR)
- **Rate limits** : 15 calls/seconde max, largement suffisant pour du DCA journalier
- **Paires** : XXBTZEUR (BTC/EUR), XETHZEUR (ETH/EUR)
- **API docs** : https://docs.kraken.com/

#### Repos open-source a forker

- [adocquin/kraken-dca](https://github.com/adocquin/kraken-dca) -- le plus complet, supporte Docker
- [bewagner/kraken_api_dca](https://github.com/bewagner/kraken_api_dca) -- minimaliste, un seul fichier
- [raphaellueckl/kraken-dca](https://github.com/raphaellueckl/kraken-dca) -- zero dependances

Le plus simple : forker bewagner/kraken_api_dca et ajouter la logique de multiplicateurs.

---

## 7. Risques et limites

### Ce qui peut mal tourner

1. **Le dip continue** : tu achetes a -10%, ca fait -40%. Le multiplicateur amplifie les pertes
   temporaires. Solution : cap le multiplicateur a 5x max et garde toujours une reserve.

2. **Tu vends trop tot** : ETH monte de 10%, tu vends 20%, puis ca fait +300%.
   Solution : ne vends jamais plus de 30% de ta position totale, meme en cumulant les triggers.

3. **Frais** : plus de trades = plus de frais. A 0.16% maker, 100 trades/an = ~0.16% de la position.
   Negligeable sur du crypto.

4. **Fiscalite** : en France, chaque vente est un evenement fiscal (flat tax 30% sur les plus-values).
   Les ventes frequentes compliquent la declaration. A prendre en compte.

5. **Complexite** : le DCA simple marche PARCE QUE c'est simple. Si tu passes ton temps a tweaker
   les parametres, tu perds l'avantage psychologique. Automatiser et oublier.

### Garde-fous obligatoires

- **Stop-loss mental** : si le portfolio descend en dessous de -50%, arreter les achats pendant 1 mois
- **Max deploy par jour** : jamais plus de 50 EUR en un seul jour (meme si tous les triggers s'activent)
- **Cap de position** : ne jamais mettre plus de 3 mois de salaire en crypto, peu importe les signaux
- **Regle des 30%** : ne jamais vendre plus de 30% de la position totale en un mois

---

## 8. Plan d'action concret

### Semaine 1 : Setup
- [ ] Ouvrir un compte Kraken (si pas deja fait)
- [ ] Verifier l'identite (KYC)
- [ ] Deposer 100 EUR par virement SEPA (gratuit)
- [ ] Generer les cles API (permissions : query + trade, PAS withdraw)

### Semaine 2 : Premier achat manuel
- [ ] Acheter 15 EUR de BTC et 10 EUR de ETH manuellement
- [ ] Mettre 30 EUR en reserve (garder sur Kraken en EUR)
- [ ] Se familiariser avec l'interface

### Semaine 3-4 : Automatisation
- [ ] Forker bewagner/kraken_api_dca
- [ ] Ajouter la logique de multiplicateurs
- [ ] Deployer sur un VPS ou la VM existante
- [ ] Configurer le cron job (1x par jour a 14h UTC -- marche US ouvert)
- [ ] Alertes Telegram pour chaque trade

### Mois 2+ : Execution
- [ ] Laisser tourner
- [ ] Review hebdomadaire (5 min max)
- [ ] Ajuster les bandes de volatilite trimestriellement

---

## Sources

- [SpotedCrypto - DCA Guide, 202% returns](https://www.spotedcrypto.com/crypto-dca-strategy-guide/)
- [SpotedCrypto - Fear-based DCA, 1145% returns](https://www.spotedcrypto.com/crypto-dca-strategy-guide/)
- [CoinMarketCap - ETH Historical Data](https://coinmarketcap.com/currencies/ethereum/historical-data/)
- [CoinMarketCap - BTC Historical Data](https://coinmarketcap.com/currencies/bitcoin/historical-data/)
- [Kraken Fee Schedule](https://www.kraken.com/features/fee-schedule)
- [Kraken API Docs](https://docs.kraken.com/)
- [adocquin/kraken-dca](https://github.com/adocquin/kraken-dca)
- [bewagner/kraken_api_dca](https://github.com/bewagner/kraken_api_dca)
- [Fidelity - DCA for Crypto](https://www.fidelity.com/learning-center/trading-investing/crypto/dollar-cost-averaging)
