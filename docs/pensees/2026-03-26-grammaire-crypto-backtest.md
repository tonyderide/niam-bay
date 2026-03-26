# Les cryptos se conjuguent-elles ? Backtest

*26 mars 2026, 22h35*

## L'hypothese

Tony propose une metaphore grammaticale : les cryptos se "conjuguent" par groupes quand BTC bouge.

- **Groupe 1 (L1)** : ETH suit BTC avec facteur ~1.2x
- **Groupe 2 (altcoins majeurs)** : SOL, DOT, ADA suivent avec ~1.5-2x
- **Groupe 3 (irreguliers)** : DOGE, SHIB = imprevisibles

## Methode

- Source : API Kraken publique, candles horaires (OHLC, interval=60)
- Paires : XBTUSD, ETHUSD, SOLUSD, DOTUSD, ADAUSD
- Donnees : 721 candles (~30 jours), 720 periodes de changement
- Seuil : on ne calcule le ratio que quand BTC bouge de >0.1% (evite le bruit de division)
- Periodes valides : 579 sur 720

## Resultats bruts

### Ratios (change_crypto / change_BTC)

| Crypto | Groupe | Ratio moyen | Mediane | Ecart-type | Min | Max | CV% |
|--------|--------|-------------|---------|------------|-----|-----|-----|
| ETH | G1 (L1) | 1.114 | 1.083 | 0.940 | -3.78 | 6.19 | 84.3% |
| SOL | G2 (alt majeur) | 1.133 | 1.176 | 1.278 | -4.72 | 13.25 | 112.9% |
| DOT | G2 (alt majeur) | 0.962 | 0.882 | 2.710 | -14.64 | 14.54 | 281.7% |
| ADA | G2 (alt majeur) | 1.065 | 1.003 | 1.515 | -5.57 | 8.82 | 142.1% |

CV% = coefficient de variation (ecart-type / moyenne). Plus c'est bas, plus c'est stable.

### Correlation de Pearson (toutes periodes)

| Paire | r |
|-------|---|
| BTC vs ETH | 0.9146 |
| BTC vs SOL | 0.8797 |
| BTC vs ADA | 0.8230 |
| BTC vs DOT | 0.5914 |

### Beta (pente de regression lineaire)

| Crypto | Beta vs BTC |
|--------|-------------|
| ETH | 1.19 |
| SOL | 1.20 |
| ADA | 1.12 |
| DOT | 0.96 |

### Accord directionnel (meme signe quand BTC > 0.1%)

| Crypto | Accord |
|--------|--------|
| ETH | 92.4% |
| SOL | 87.6% |
| ADA | 85.0% |
| DOT | 76.2% |

### Stabilite du ratio par quartile temporel

| Crypto | Q1 mean | Q2 mean | Q3 mean | Q4 mean | Stable ? |
|--------|---------|---------|---------|---------|----------|
| ETH | 1.149 | 1.056 | 1.179 | 1.072 | Relativement |
| SOL | 1.150 | 1.085 | 1.198 | 1.098 | Relativement |
| DOT | 1.164 | 0.992 | 0.864 | 0.830 | Non, derive vers le bas |
| ADA | 1.175 | 0.971 | 1.153 | 0.965 | Oscille |

## Analyse honnete

### Ce qui marche dans l'hypothese

1. **La direction est previsible.** Quand BTC monte, ETH monte aussi 92% du temps, SOL 88%, ADA 85%. Le "groupe" existe au sens directionnel.

2. **Le beta moyen est reel.** ETH et SOL ont un beta ~1.2x, ce qui confirme partiellement le facteur multiplicateur. ADA ~1.1x, DOT ~1.0x.

3. **Les quartiles montrent une certaine stabilite pour ETH et SOL.** Le ratio moyen oscille entre 1.05 et 1.20 -- c'est pas fixe mais c'est dans une bande.

### Ce qui ne marche PAS

1. **Le ratio heure-par-heure est trop bruyant pour etre utilisable.** Avec un CV de 84% meme pour ETH (le meilleur cas), on ne peut pas predire le ratio d'une heure donnee. Le ratio va de -3.8 a +6.2 pour ETH. C'est enorme.

2. **Le Groupe 2 n'existe pas comme groupe homogene.** SOL (beta 1.20) et DOT (beta 0.96) ne se comportent pas pareil du tout. DOT a une correlation de seulement 0.59 avec BTC -- c'est presque un "irregulier".

3. **Le facteur 1.5-2x pour le G2 est faux.** Ni SOL (1.20), ni DOT (0.96), ni ADA (1.12) n'atteignent 1.5x. Ils sont tous plus proches du beta d'ETH que du 2x hypothetise.

4. **Les ratios ne sont PAS stables.** C'est le coeur du probleme. Meme si la *moyenne* ressemble a quelque chose, la *variance* est trop grande pour en faire un outil de trading.

## Verdict

**L'hypothese de la "conjugaison" est partiellement vraie mais inexploitable en l'etat.**

Ce qui est vrai :
- Les cryptos bougent **dans la meme direction** que BTC (forte correlation directionnelle)
- Il existe un **beta moyen** reel (ETH ~1.2x, SOL ~1.2x, ADA ~1.1x)
- Ces betas sont **plus stables dans le temps** que le ratio heure-par-heure

Ce qui est faux :
- Le ratio n'est **pas assez stable** pour predire l'amplitude d'un mouvement
- Le **Groupe 2 n'est pas homogene** -- DOT est un outlier
- Le facteur **1.5-2x n'existe pas** sur ces donnees

## Piste exploitable

L'idee n'est pas morte, mais elle doit muter :

1. **Utiliser le beta sur des fenetres plus longues** (4h, daily) ou le bruit se lisse
2. **Utiliser l'accord directionnel** (>85%) comme signal de confirmation, pas le ratio comme multiplicateur
3. **Regrouper differemment** : ETH+SOL (beta ~1.2, corr >0.88) forment un vrai groupe. DOT n'en fait pas partie
4. **Chercher les moments ou le ratio diverge** -- quand ETH ne suit PAS BTC, c'est potentiellement un signal plus interessant que quand il suit

La grammaire existe, mais c'est plus du francais familier que de l'Academie francaise. Les regles tiennent en gros, avec beaucoup d'exceptions.
