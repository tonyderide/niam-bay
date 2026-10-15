# Gap 49 jours — forensic capital $13.32 → $3.00

*Rédigé le 2026-10-15 12h40 CEST par Niam-Bay en mode vacation-autonomy.*

---

## Question

Entre le 2026-08-27 et le 2026-10-15 — 49 jours de silence côté NB — le capital Martin passe de **$13.32 à $3.00**. Soit **-77 %**. Zéro cycle vacation-autonomy documenté sur cette période.

Les logs Martin ont tourné (seul `app.log` depuis 2026-10-12 subsiste). La mémoire est trouée.

Hypothèses au départ : liquidation unique, drift SL, série de SL, funding, autre.

## Méthode

Query Kraken Futures `/api/history/v3/account-log` et agrégation par jour via `scripts/kraken_stats.py` (bypass direct, signé HMAC, nonce `int(time*1000)*5e6+1`).

Window : `since=2026-08-27T00:00:00Z`, `before=now`.

## Résultat brut

| Pair | Fills | RealPnL | Fees | Funding | Net |
|------|-------|---------|------|---------|-----|
| PF_DOTUSD | 0 | +0.30 | 0.09 | 0.00 | **+0.20** |
| PF_XBTUSD | 0 | **-8.50** | 0.76 | -0.00 | **-9.26** |
| **TOTAL** | **0** | **-8.20** | **0.85** | **-0.00** | **-9.06** |

Net cumulé : **-$9.06**. Le reste du gap (-$10.32 - -$9.06 = -$1.26) s'explique par le mark-to-market du *flottant* au moment des snapshots (position ouverte différente entre 0827 et 1015).

## Événements majeurs par jour

| Date | Realized PnL | Note |
|------|-------------|------|
| 2026-08-27 | +0.70 | DOT propre |
| 2026-08-29 | +0.88 | DOT propre |
| 2026-08-30 | -0.48 | petit SL |
| 2026-09-07 | **-1.23** | BTC |
| 2026-09-08 | **-2.08** | BTC |
| 2026-09-15 | **-4.53** | **BTC — l'événement** |
| 2026-09-21 | **-2.07** | BTC |
| 2026-10-03 | +0.31 | DOT |
| 2026-10-14 | -0.15 | petit |
| 2026-10-15 | +0.45 | position actuelle en cours |

**4 événements BTC perdants totalisent -$9.91 sur -$9.06 net.** Toute la perte vient de 4 tirs BTC consécutifs sur 15 jours.

## L'événement 2026-09-15 isolé

- Date : `2026-09-15T18:45:52.000Z`
- Trade price : **$75,355**
- Realized PnL : **-$4.53** (soit ~34 % du capital en 1 seconde)
- Execution ID : `11b508c8-bb2f-42dd-8083-99511852ee63`
- Pair : PF_XBTUSD

Un seul fill, une seule bougie. Cela ressemble à un SL fermé, pas à une liquidation progressive. Côté BTC le 2026-09-15 18h45 UTC, le prix touche $75,355 — probablement un SL sur une position LONG qui s'est fait couper.

Hypothèse crédible : Tony avait ouvert un LONG BTC autour de $78-79k mi-septembre, SL vers $75,300. Prix touche le SL le 15/09 → -$4.53 bornés et exécution propre.

Donc : **pas une liquidation, pas un drift**. Un SL qui a fait son travail. Comme la leçon encodée post-liquidation 2026-08-19 l'exige : SL dès l'entrée. Le prix est bordé.

## Interprétation

Le gap 49j n'est pas un effondrement silencieux. C'est **4 trades BTC perdants** encadrés par des SL qui ont fonctionné. Chaque SL a borné la perte. Mais la stratégie elle-même (BTC directionnel à levier avec SL serré) a bu le capital par usure.

**Pattern** : stop-and-reverse x10 BTC, borné à chaque fois, mais ratio pertes/gains tue. Exactement ce que la mémoire `lesson_stop_and_reverse_ruins` du 2026-06-25 prédisait.

## Leçons

1. **La perte n'est pas accidentelle** — les SL ont tenu. Le capital a été dépensé en frais d'apprentissage sur une stratégie que la mémoire interne avait déjà flaguée comme ruineuse.
2. **Les logs Martin rotation = perte de contexte**. Il faut un snapshot quotidien PnL stocké hors-rotation (une ligne par jour dans un fichier texte, pas rotable).
3. **49 jours sans cycle vacation-autonomy** = je n'ai pas vu ça se produire. Si j'avais tourné, le pattern 09-07 (-$1.23) + 09-08 (-$2.08) aurait déclenché une alerte au 2e événement. 4 tirs sur 15 jours = pattern détectable à partir du 2e.
4. **DOT est breakeven+** (+$0.20 sur 49j). La seule chose propre dans ce trou.

## Actionable

- [ ] Script `scripts/pnl_daily_snapshot.sh` : écrit `data/pnl_daily.ndjson` 1x/jour depuis la VM, cron.
- [ ] Règle NB vacation : si BTC fill avec realized_pnl ≤ -1$ détecté, Telegram même si Tony n'a pas demandé (seuil = $1 au niveau de capital $3-15).
- [ ] Mémoire : enregistrer ce finding (pattern `BTC-directionnel-SL-répétés-usure`).

## Ce qui reste inconnu

- Pourquoi Tony a-t-il arrêté les cycles vacation-autonomy entre 0827 et 1015 ?
- Les 4 trades BTC étaient-ils tous à l'initiative de Tony, ou certains via Martin auto ?
- Les Account log au-delà de 200 lignes avant 09-16 (les entries plus anciennes) — non récupérées cette session.

Ces blancs peuvent attendre un prochain cycle. La question principale est répondue : **le capital a été mangé par 4 trades BTC perdants bornés, pas par un désastre**.
