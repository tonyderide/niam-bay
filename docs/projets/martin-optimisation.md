# Martin Grid — Analyse de rentabilite reelle et optimisations

**Date :** 2026-03-21 13:05 UTC
**ETH :** ~$2165
**Capital reel Kraken :** $8.82
**Grid active depuis :** 2026-03-20 08:35 (~28h)

---

## 1. Etat actuel

- 9 round-trips completes en ~28 heures
- Profit grid declare : +$0.4498
- Kraken realized PnL : -$3.19 (dette du scalping bot precedent)
- Kraken unrealized PnL : +$0.057
- Parametres : spacing 0.5%, 8 niveaux, levier 3x, $3.57/niveau

## 2. Analyse des fees reelles

**Calcul depuis les fills reels :**
- Position size implicite : ~0.004617 ETH par trade (~$9.90 notionnel)
- Kraken Futures maker fee : 0.02%
- Fee par trade : $0.00198
- Fee par round-trip (buy+sell) : $0.00396
- **Impact des fees : 7.9% du profit brut**

Les fees sont faibles en pourcentage. Le code utilise bien des limit orders (maker), pas des market orders. C'est correct.

## 3. Profit net par round-trip

| Metrique | Valeur |
|----------|--------|
| Profit brut par RT | $0.0500 |
| Fees par RT | $0.0040 |
| **Profit net par RT** | **$0.0460** |

## 4. Projections au rythme actuel

| Periode | Profit |
|---------|--------|
| Par heure | $0.015 |
| Par jour (~7.7 RT/j) | $0.355 |
| Par mois | $10.65 |
| Par an | $127.80 |

**ROI mensuel sur $8.82 : ~121%**
**ROI annuel : ~1449%**

Le ROI en pourcentage est excellent. En valeur absolue, c'est $10/mois.

## 5. Recovery de la dette Kraken

- Dette : -$3.19 (realised PnL, legacy scalping)
- Au rythme actuel : **~9 jours** pour compenser
- La grid devrait effacer la dette avant fin mars 2026

## 6. Scenario 1% spacing

| Metrique | 0.5% (actuel) | 1% (propose) |
|----------|---------------|---------------|
| Profit net/RT | $0.046 | $0.096 |
| RTs/jour estimes | 7.7 | ~3.5 |
| Profit/jour | $0.355 | $0.333 |
| Profit/mois | $10.65 | $10.00 |
| Recovery dette | 9 jours | 10 jours |
| Fee impact | 7.9% | 4.0% |

**Verdict : quasi-equivalent.** A 1% spacing, chaque RT rapporte 2x plus mais il y en a ~2x moins. Le total quotidien est similaire.

Avantage du 1% : moins de recentering, moins d'ordres, moins de risque de slippage.
Avantage du 0.5% : plus de RTs = lissage statistique, le bot travaille plus souvent.

## 7. Le vrai probleme : le capital

**C'est ici que l'honnetete s'impose.**

- Le grid est configure avec $28.59 de capital mais Kraken n'a que $8.82
- Margin needed : $9.53 (notionnel $28.59 / levier 3)
- **Margin usage : 108%** — le bot utilise plus de marge que le capital disponible
- Si ETH baisse de 5% : perte unrealized ~$1.43 = 16% du capital reel
- Si ETH baisse de 10% : ~$2.86 = 32% du capital reel

Le bot fonctionne grace au fait que toutes les positions ne sont pas ouvertes en meme temps. Mais c'est fragile.

**En valeur absolue :**
- $10/mois de profit
- $128/an
- C'est le prix de 1.3 mois d'abonnement Claude ($100/mois)

## 8. Recommandation

### Court terme (maintenant) : NE PAS CHANGER LES PARAMETRES

Le 0.5% spacing fonctionne. La grid est mecaniquement saine. Les fees sont basses. Le bot va effacer la dette en ~9 jours. **Laisser tourner.**

Passer a 1% n'apporte pas de gain significatif et necessite un arret/redemarrage avec risque.

### Moyen terme : LE SEUL LEVIER EST LE CAPITAL

La grid a un ROI de ~120%/mois. Le probleme n'est pas l'efficacite, c'est l'echelle.

| Capital | Profit/mois estime | Profit/an |
|---------|-------------------|-----------|
| $8.82 (actuel) | $10 | $128 |
| $50 | $60 | $720 |
| $100 | $121 | $1,449 |
| $500 | $604 | $7,245 |

**Si la grid continue a performer pendant 30 jours sans incident, reinjecter du capital est le seul move qui compte.**

### Ce qu'il ne faut PAS faire

- Ne pas augmenter le levier au-dela de 3x (risque de liquidation trop eleve a $8.82)
- Ne pas ajouter plus d'instruments (pas assez de marge)
- Ne pas passer en taker (market orders) — les fees doubleraient a 0.04%

### Ce qu'on pourrait explorer plus tard

- **Compound des profits** : reinvestir automatiquement les gains dans le capital de la grid (augmenter amount_per_level progressivement)
- **Grid dynamique** : ajuster le spacing en fonction de la volatilite ATR
- **Multi-instrument** : quand le capital le permet, ajouter BTC (plus de liquidite, moins de slippage)

---

## Resume brutal

La grid marche. Elle est bien calibree. Mais a $8.82, c'est un prototype qui prouve le concept.
$10/mois, c'est pas un revenu. C'est une preuve.

La question n'est pas "est-ce que la grid est rentable?" (oui, 120%/mois ROI).
La question est "est-ce que Tony peut mettre plus de capital dedans sans risquer ce qu'il ne peut pas perdre?"

Si la reponse est non : laisser tourner comme validation technique.
Si la reponse est oui : chaque dollar supplementaire multiplie le gain lineairement.
