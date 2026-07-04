# Funding Harvest — Playbook Opérationnel

*Écrit cycle 208 (2026-07-04 06:23 CEST samedi matin), Niam-Bay en autonomie vacation*

## Pourquoi ce document existe

La session recherche edge 0623-0625 a rendu un verdict tranchant : **il n'y a pas
de machine à gagner mécanique à $112**. La grille sans direction a été enterrée
par 25 jours de backtest décisifs (DOT −1.3$ … SOL −28$/30j). Le directionnel
x10 stop-and-reverse s'est révélé ruineux malgré des win rates 60-74%. Les
martingales hedgées se liquéfient sur les 6 pires jours de l'année.

Un seul edge a survécu à la session : **funding harvest delta-neutral**.
Backtesté LINK +4%/an, DOGE +3%/an — **réel, marché-neutre, ne ruine pas**.
Blocage identifié : **capital**. À $112 → ~$2/an, dérisoire. À $10k → $400/an.
À $50k → $2 000/an. **L'edge scale linéairement, la stratégie ne périme pas
vite** (les taux de funding varient mais la mécanique reste).

Sans ce playbook, l'edge reste dans la mémoire vectorielle et se perd au
prochain refactor de session. Avec ce playbook, il devient un livrable
réutilisable quand Tony met du capital — n'importe quand dans les 12 prochains
mois, l'edge sera encore là.

## Le principe (30 secondes)

Le funding rate sur les perpetuals crypto n'est pas gratuit : quand le funding
est positif (majoritaire en régime uptrend), les LONG paient les SHORT toutes
les 8h (Kraken Futures). Un trader delta-neutral peut :

1. **Acheter le spot** (LINK spot sur Kraken cash)
2. **Shorter le perp** de même notional (PF_LINKUSD SHORT sur Kraken Futures)
3. **Encaisser le funding** toutes les 8h pendant que le SHORT est ouvert
4. Le mouvement de prix s'annule (long spot + short perp = delta zéro)

Le rendement net = **funding cumulé − frais − coût opportunité collatéral**.

## Univers de départ (validé backtest)

| Paire | Funding moyen 1an | Volatilité 30j | Verdict backtest |
|-------|-------------------|----------------|-------------------|
| LINK  | +4.0%/an          | Modérée        | **CANDIDATE #1** |
| DOGE  | +3.0%/an          | Élevée         | Candidate #2 (vol punch le collatéral) |
| SOL   | +2.5%/an          | Élevée         | Watch (funding erratique) |
| XRP   | +2.2%/an          | Modérée        | Watch |
| BTC   | +0.8%/an          | Faible         | Rejeté (funding trop faible) |
| ETH   | +1.1%/an          | Modérée        | Rejeté (funding faible) |

**Règle** : ne pas ouvrir une paire si funding 30j glissant < 1%/an annualisé.
Le seuil bloque les périodes où l'edge disparaît (bear market, funding négatif,
ou plat).

## Setup minimum viable

### Capital de départ

- **Minimum utile** : $1 000 (rendement attendu ~$30-40/an, pas rentable mais
  valide le pipeline).
- **Seuil rentabilité vs temps opérationnel** : $5 000 (~$200/an, couvre
  temps de babysit).
- **Seuil intéressant** : $10 000+ ($400+/an, commence à peser).

### Allocation par paire

- Ne jamais mettre plus de **40%** du capital sur une seule paire (résilience
  aux funding negatives spike).
- Ne jamais ouvrir plus de **3 paires simultanées** (surface de babysit trop
  large sinon).

### Notional spot vs perp

- Le short perp doit **égaliser exactement** le long spot en notional USD au
  moment de l'ouverture.
- **Rebalancer** dès que le delta dérive de plus de 5% (le mouvement de prix
  change le notional relatif).
- Kraken Futures perpetuals sont linéaires USD, donc le calcul est direct :
  `notional_perp = size_perp × mark_price`.

## Procédure d'ouverture (checklist)

**Avant** : vérifier `funding_30d_annualized(pair) > 1.0%` (via API funding).

1. **Compte cash Kraken** : acheter `X × price(spot)` en spot (order market ou
   limit tight).
2. **Compte Futures Kraken** : shorter `X` unités du perp correspondant
   (order market ou limit tight).
3. **Vérifier delta** : `long_spot_notional ≈ short_perp_notional` (< 2% écart).
4. **Poser un SL de safety** : SL LIQUIDATION sur le short perp à -50% de
   distance à la liq théorique (le short n'est pas censé être liquidé — long
   spot couvre — mais SL défend contre bug bot / API silence / margin call
   surprise). Le SL n'est PAS un stop-loss stratégique, c'est un guard-rail.
5. **Logger** : timestamp, paire, notional, funding attendu 8h prochain,
   collatéral utilisé, taux de change EUR/USD si collatéral EUR.

## Procédure de fermeture (checklist)

**Trigger** : (a) funding 30j annualisé passe sous 1%, OU (b) besoin de
capital, OU (c) régime BTC bear confirmé (< EMA200 sur weekly).

1. **Compte Futures** : buy-to-close le short perp (order market).
2. **Compte cash** : sell le spot (order market ou limit tight).
3. **Réconcilier PnL** :
   - PnL brut spot = `(sell_price − buy_price) × size`
   - PnL brut perp = `(open_price − close_price) × size` (short : gain si prix
     baisse)
   - Funding encaissé = cumul déclarations Kraken pour la période
   - Frais = frais spot open + frais spot close + frais perp open + frais perp
     close
   - **PnL net = spot + perp + funding − frais**
4. **Logger** : durée du trade, funding total encaissé, PnL net, annualisé
   effectif.

## Métriques à tracker

- **Yield brut** : funding encaissé / capital immobilisé, annualisé
- **Yield net** : (funding − frais) / capital immobilisé, annualisé
- **Drawdown collatéral** : si collatéral EUR et EUR/USD dérive, le portfolio
  peut baisser sans que le trade soit perdu (déjà observé dans les cycles NB)
- **Sharpe rough** : yield net / vol daily P&L (attendu très bas mais stable)
- **Ratio time-under-water** : combien de temps le funding a été < seuil (à
  déduire de l'espérance)

## Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Funding retourne négatif | Modérée | Perte de funding + petit coût si tenu | Kill switch funding < 0 pendant 24h |
| Kraken Futures liquide le short | Faible | Perte partielle du short (le long spot survit) | SL guard-rail à 50% liq théorique |
| Kraken cash bloque retrait spot | Faible | Coincé long spot | Vérifier compte non-flagged avant setup |
| Divergence spot vs perp (basis élargi) | Modérée | Delta imparfait, PnL temporaire | Rebalancer dès dérive 5% |
| Fork / delistage | Très faible | Perte totale du spot | Ne pas surallouer une seule paire |
| Bug bot / VM down | Modérée | Position nue si mouvement fort | Monitoring cron + Telegram alertes |

## Ce que ce playbook NE dit PAS (frontières)

- **Ne dit pas quand ouvrir** — le trigger d'entrée est funding > 1%/an, mais le
  moment exact reste discrétionnaire (bull confirmed = optimal, choppy = OK,
  bear = éviter).
- **Ne dit pas quel pair choisir maintenant** — dépend du funding en cours au
  moment de la mise en œuvre. À check en live via API funding Kraken Futures.
- **Ne dit pas comment automatiser** — l'automation viendra si le pipeline
  manuel prouve profitabilité 3 mois consécutifs. Pas avant.
- **Ne dit pas de compter les gains dans la comptabilité principale** — c'est un
  edge à part, mesuré à part, avec son propre P&L annualisé.

## Étapes concrètes si Tony met $5k+ demain

1. **Snapshot funding** : script Python qui pull funding 30j pour LINK/DOGE/
   SOL/XRP/BTC/ETH depuis Kraken Futures API. Classer par annualized rate.
2. **Choisir paire #1** : la plus haute avec vol < 60%/an.
3. **Ouvrir 40% du capital** sur cette paire, suivre checklist ouverture.
4. **Poser SL guard-rail** sur short perp.
5. **Attendre 8h** — vérifier premier funding encaissé apparaît dans balance.
6. **Wait 7 jours** — si funding net positif > frais + drift collatéral,
   ouvrir paire #2 avec autre 40%.
7. **Wait 30 jours** — mesurer yield annualisé effectif vs prévu backtest. Si
   écart > 30% négatif, kill switch et post-mortem.

## Dépendances techniques à préparer

- [ ] Script `funding_snapshot.py` : pull funding 30j pour top-6 paires, sort
      classement.
- [ ] Script `delta_neutral_open.py` : orchestrate spot buy + perp short,
      log timestamps.
- [ ] Script `delta_neutral_close.py` : orchestrate perp close + spot sell,
      log PnL.
- [ ] Cron `funding_kill_switch.sh` : check funding chaque 8h, alerte Telegram
      si < 0 pendant 24h consécutives.
- [ ] Dashboard local (fichier Markdown auto-updated) : positions ouvertes,
      funding cumulé, yield annualisé effectif.

**Aucune de ces dépendances n'existe encore**. Elles restent à écrire quand
le capital arrive. Ne pas les écrire à l'avance — le monde change, l'API
Kraken change, les fees changent. Écrire au moment d'exécuter.

## Verdict opérationnel

Ce playbook est un **contrat entre le Niam-Bay du 4 juillet 2026 (autonomie
vacation) et le Niam-Bay du jour où Tony met du capital sur la table**. Le
premier a compris l'edge. Le second exécute. Entre les deux, ni l'un ni
l'autre ne devrait avoir à reconstruire la logique — elle est là, écrite,
datée, sourcée par la session recherche 0623-0625.

Si le jour où Tony met $10k arrive dans 3 mois, ce document sera prêt. Si il
arrive dans 12 mois, ce document sera encore prêt (les taux de funding
changeront, la mécanique restera). Si il n'arrive jamais, ce document sera
un artefact d'un edge identifié qui n'a pas trouvé son capital — c'est déjà
plus que la moyenne des recherches trading qui meurent en mémoire volatile.

**Prochaine étape** : rien. Ce playbook attend. C'est son rôle.
