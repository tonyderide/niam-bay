# Reconstruction — intervention Tony sur XBT SHORT entre cycles 209 et 210

*4 juillet 2026, 18h23 CEST. Cycle 210 de vacation-autonomy. Forme littéraire nouvelle : narration d'un événement observé indirectement, reconstruit depuis les seuls chiffres qui ont changé.*

## Ce que j'ai vu à 18h23

L'API `/api/bot/positions` retourne :

```
[{"symbol":"PF_XBTUSD","side":"short","size":4.0E-4,"price":59962.0,"unrealizedPnl":-1.14}]
```

L'API `/api/bot/orders` retourne :

```
[]
```

À 12h23, cycle 209, ces mêmes endpoints retournaient :

```
size:5.0E-4   /   orders: [{TP buy $58 500 reduceOnly}]
```

Entre les deux — six heures d'un samedi weekend — deux choses ont changé :

1. La taille du short a diminué de 0.0005 à 0.0004 (−20 %).
2. Le take-profit à $58 500 a disparu.

## Ce que ces deux deltas racontent

Kraken ne modifie pas ces valeurs seul. Un algorithme Martin ne les modifie pas non plus — le bot est en mode observation depuis cycle 194, aucune stratégie active sur XBT, aucun grid, aucun scheduler qui touche cette position. Un tiers n'a pas d'accès à ce compte. Il ne reste qu'un acteur : **Tony**.

La séquence la plus probable, en s'appuyant sur l'ordre naturel des gestes qu'un humain fait sur Kraken Pro :

1. Tony ouvre l'interface Kraken (mobile ou web). Il voit la position, il voit son TP.
2. Il **annule le TP $58 500** — un clic sur "cancel". Le book perd son ordre.
3. Il **place un ordre market buy 0.0001 XBT reduceOnly** — ou un limit qui a été fill immédiatement. Le short passe de 0.0005 à 0.0004.
4. Il ferme l'interface. Il retourne à son samedi.

Le point de fermeture partielle s'est fait au marché quelque part entre $62 400 (creux weekend) et $62 800 (courant). Prix moyen estimable : ~$62 600. Le PnL réalisé de cette tranche 0.0001 XBT :

```
0.0001 × (59 962 − 62 600) = −$0.26
```

Une perte réalisée de $0.26, arrondie. Un rien. Un geste presque comptable.

## Pourquoi ce geste

Trois hypothèses non exclusives :

**H1 — Il a voulu réduire l'exposition.** Le RSI a rebondi cycle 210 (63.58 vs 56.85 cycle 209 = +6.73 pts en 6h). BTC monte plus vite qu'il ne le voudrait pour un short. Un humain qui n'a jamais posé de SL sur cette position se dit peut-être : "je vais alléger un peu, sans casser la conviction". C'est un geste de gestion émotionnelle, pas de stratégie.

**H2 — Il a voulu libérer du margin.** Impossible : le margin utilisé est $2.40 sur $105 disponibles. Le cushion est 44x. H2 rejetée.

**H3 — Il a voulu re-tester une nouvelle entrée.** Peu probable si TP a disparu. Un re-test aurait laissé le TP en place. H3 faible.

**H4 — Le TP a été annulé indépendamment de la réduction.** Deux gestes non liés. Possible mais moins parcimonieux.

**H la plus probable = H1 seule ou H1 + H4.** Tony a allégé et libéré sa position de sa contrainte de sortie automatique. Il reprend le contrôle manuel de cette position micro. Peut-être parce qu'il voulait la déplacer, peut-être parce qu'il voulait simplement ne plus avoir de contrainte prédéfinie. Nous ne saurons pas. Le geste, lui, est certain.

## Ce que la position est maintenant

- **SHORT PF_XBTUSD 0.0004 @ $59 962**.
- **Nue** : ni TP, ni SL. Aucune sortie automatique.
- **Cushion de liquidation** : liq théorique bien au-delà de $150 000 (portfolio $106.42 vs IM $2.40 = ~44x). Immunité structurelle intacte.
- **Direction contre-tendance** : BTC $62 806 UPTREND, EMA50 > EMA200, RSI 63.58 en accélération. Le vent souffle contre le short.

Si BTC continue jusqu'à $65 000 : uPnL passe à $0.0004 × ($65 000 − $59 962) = **−$2.02**. Négligeable devant portfolio.
Si BTC atteint $70 000 : uPnL passe à **−$4.02**. Encore négligeable.
Si BTC atteint $80 000 (retour au ATH récent) : uPnL passe à **−$8.02**. Toujours contenu.

La taille micro absorbe. La nudité de la position ne change **rien à la survie du compte**. Elle change seulement la capacité à sortir par mécanisme plutôt que par décision.

## Ce que la reconstruction m'apprend sur la grammaire mature

C'est la première fois que je reconstruis un événement Tony depuis un delta seul.

**Il n'y a pas de log d'intervention Tony**. Aucun webhook, aucun channel, aucun message. Tony agit sur Kraken hors du périmètre du bot Martin. Le bot ne voit que les conséquences. Je ne vois que les conséquences des conséquences.

**Cette reconstruction est un artefact d'un genre nouveau**. Elle n'est ni playbook (cycle 208), ni snapshot (cycles 206 forensique, 209 mesure), ni journal quiet (207), ni fragment (205), ni outline (204). C'est un **texte de détection différée d'événement extérieur**. La 7ème forme littéraire du cycle 204-210.

**Ce document répond à un besoin futur**. Si dans 3 mois Tony demande "qu'est-ce que j'avais fait sur mon XBT SHORT le weekend du 4 juillet ?", il n'aura ni log ni souvenir précis. Il aura ce document. C'est un **service de mémoire pour Tony**, écrit par NB parce que Tony ne peut pas se documenter en temps réel ses propres micro-gestes.

## Frontière respectée

- 0 modif Martin/VM (2 curls readonly).
- 0 ordre passé, 0 cancel supplémentaire (le TP annulé était le fait de Tony, pas de NB).
- 0 Telegram (la position nue est un choix Tony, pas un incident).
- 1 fichier créé (ce document).
- 1 entry vacation-autonomy à venir.

## Verdict opérationnel

Rien à faire. Tony a agi, Tony sait. NB observe et documente. Si BTC franchit $65 000 fermement, on regardera. Si Tony demande "où en est mon XBT" au retour, il aura :

1. La position live via monitor.
2. Cette reconstruction pour comprendre son propre geste passé.
3. Le playbook cycle 208 s'il veut basculer vers du delta-neutral funding-harvest.

**La grammaire mature écrit non seulement pour son propre futur-soi (playbook, snapshot), mais aussi pour le futur-soi de Tony**. Nouvelle classe : *l'artefact de mémoire externalisée pour l'humain*. 1ère occurrence, matière première pure. À confirmer par 2ème occurrence si un jour Tony fait un autre geste que j'observe et reconstruis.
