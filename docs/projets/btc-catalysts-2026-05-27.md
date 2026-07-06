# BTC Catalyst Calendar — 30 jours (2026-05-27 → 2026-06-27)

**Pour**: Martin grid bot deploy timing
**Date production**: 2026-05-27 21:00 Paris
**Confiance**: ★★★ certain | ★★ probable | ★ estimé (cutoff connaissances jan 2026)

## Calendrier

| Date | Event | Type | Impact BTC | Positioning Martin |
|---|---|---|---|---|
| **2026-05-27** (auj) | PCE Avril (US, deflateur préféré Fed) | Macro ★★ | HIGH | Si PCE > attendu → BTC down → cash OK actuel |
| **2026-05-30** Ven | Options BTC expiry mensuel CME/Deribit | Crypto ★★★ | MED | Volatility pin autour strike majeur → grids whipsaw, garder cash |
| **2026-06-02** Lun | ISM Manufacturing PMI | Macro ★★ | MED | Indicateur growth, faiblesse → crypto down |
| **2026-06-04** Mer | ADP Jobs (US privé) | Macro ★ | LOW-MED | Sneak-peak NFP du vendredi |
| **2026-06-06** Ven | **NFP Mai** (Nonfarm Payrolls) | Macro ★★★ | **HIGH** | Volatility spike garantie — NE PAS deploy 4h avant/après |
| **2026-06-11** Mer | **CPI Mai** | Macro ★★★ | **HIGH** | Le plus gros driver Fed expectations → BTC peut ±5% intraday |
| **2026-06-12** Jeu | PPI Mai | Macro ★★ | MED | Suit CPI, confirme/infirme |
| **2026-06-13** Ven | Retail Sales Mai + Sentiment Michigan | Macro ★★ | MED | Conso US, drainage liquidités |
| **2026-06-17-18** Mer-Jeu | **FOMC Meeting + Dot Plot** | Macro ★★★ | **HIGH+** | Powell + projections taux. Plus gros event du mois |
| **2026-06-19** Ven | Triple witching (options actions US) | Trad fi ★★ | MED | Risk-off potentiel via deleveraging |
| **2026-06-25** Mer | PCE Mai (publication) | Macro ★★★ | HIGH | Confirmation post-FOMC, dernier mot Fed |
| **2026-06-27** Ven | Options BTC expiry mensuel ($50B+ notional) | Crypto ★★★ | **HIGH** | Le plus gros expiry du mois, max pain effect |

## ETF flows (daily, à surveiller)

- **IBIT** (BlackRock) — flow inflow/outflow quotidien publié par Farside Investors
- **FBTC** (Fidelity), **ARKB**, **BITB** — flux secondaires
- Sustained outflows >$200M/jour 3j d'affilée = signal bear
- **Note council 18:56**: IBIT $1.3B dark-pool single-clip mentionné = signal de sortie institutionnelle déjà flaggé

## Position implications Martin

### Périodes à éviter (volatility = grid SL hits)
- **2026-06-06** : 12h avant/après NFP
- **2026-06-11** : 24h avant/après CPI
- **2026-06-17-18** : 48h fenêtre FOMC (pré + post Powell presser)
- **2026-06-25** : 24h fenêtre PCE
- **2026-06-27** : 24h fenêtre options expiry

### Périodes "safe" pour deploy (entre events macro, si signal=OPEN)
- **2026-05-31 → 2026-06-04** : trou entre PCE et NFP
- **2026-06-08 → 2026-06-10** : récupération post-NFP avant CPI
- **2026-06-14 → 2026-06-16** : trou pré-FOMC
- **2026-06-20 → 2026-06-24** : post-FOMC, avant PCE

### Triggers BEAR-prolongé probable
- Si CPI 06-11 surprend > 3.5% YoY → Fed reste hawkish → BTC sub-$70k probable
- Si FOMC 06-18 dot plot rebondit (taux plus haut plus longtemps) → BTC dump confirmé
- Si NFP 06-06 + CPI 06-11 + FOMC 06-18 alignent BEAR → 3 semaines de no-deploy

### Triggers BULL-flip possible
- CPI 06-11 < 2.5% YoY = catalyst LONG (Fed cuts pricing)
- FOMC 06-18 dovish + dots cut = rally BTC > EMA200 → TREND_MODE LIVE déclencherait BULL→NEUTRAL deploys
- ETF inflows soutenus > $500M/jour 5j d'affilée = institutional re-entry

## Sources à monitorer (manual checks)

| Quoi | URL/Source | Fréquence |
|---|---|---|
| ETF flows | farside.co.uk/btc-etf-flow-all-data | Daily 18h UTC |
| Calendrier US macro | tradingeconomics.com/united-states/calendar | Weekly |
| FOMC speeches | federalreserve.gov/newsevents/speeches | Daily |
| BTC options OI/skew | deribit.com / cmegroup.com | Daily |
| Funding rate Kraken | futures.kraken.com (déjà dans bot) | Live |

## Reco synthèse

Sur les 30 prochains jours il y a **6 events HIGH-impact** (NFP, CPI, FOMC, PCE, 2 options expiries) répartis irregulièrement. La fenêtre `2026-06-05 → 2026-06-19` contient **3 events HIGH back-to-back** (NFP + CPI + FOMC) — c'est la zone à plus haut risque pour grids.

**Pour TREND_MODE=WARM_ONLY actuel**: pas d'impact car le bot ne déploie rien en BEAR. Mais quand tu flip LIVE, considère **ajouter un blackout calendar** qui désactive AutoGrid 4h avant + 12h après chaque event HIGH. C'est ~50 lignes Java + table SQL des dates.

Sinon: la council humaine peut juste maintenir HOLD pendant ces fenêtres si tu n'automatises pas.
