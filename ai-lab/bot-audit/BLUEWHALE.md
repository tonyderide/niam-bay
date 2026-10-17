# @BlueWhaleCryptoTrading : audit des signaux publics (17/10/2026)
128 messages publics (29/08 → 16/10), lus via l'aperçu web t.me/s (sans compte), et jugés sur les vraies bougies BTC 1h (Binance).

## Comment le canal est construit
- Les signaux publics sont **volontairement incomplets** : « $BTC 😁😁😁😁 SL : 78,4xx ». **Pas d'entrée, pas de TP, un SL masqué** (« xx »), et chaque fois « DM @Oldman899 to join VIP » pour avoir « the best entry and TP ».
- Il y a des messages « HIT TP IN ELITE MENTORSHIP » qui montrent les gains passés, sans les pertes.
- Un « $10K → $1M CHALLENGE », des messages qui demandent des réactions (« drop ❤️ »), des « today's main course ».
→ C'est un **entonnoir de vente vers un VIP payant**. Le signal public n'est pas fait pour être tradé, il est fait pour donner envie de payer.

## Le juge : ce qui se serait passé
Hypothèses (les plus favorables possibles au canal) : on entre au prix BTC au moment du post, le sens se déduit de la position du SL (dessous = long, dessus = short), on prend le SL le plus large compatible avec le masque, et on vise un TP à +2R. Fenêtre de 7 jours. Les doublons du même jour sont retirés.

| résultat | nombre |
|---|---|
| SL touché | **13** |
| +2R atteint | **6** |
| ni l'un ni l'autre en 7 jours | 4 |

Sur les 19 signaux tranchés, **6 gagnent (32 %)**. Avec un TP à 2R et un SL à 1R, le point mort est à 33 %. **C'est exactement ce que donnerait le hasard**, et c'est avant les frais. L'espérance est d'environ −0,05 R par signal.
Les signaux publics n'ont donc aucun edge mesurable. Le VIP ne peut pas être jugé, puisque ses entrées et TP sont cachés, ce qui est voulu. Leurs posts « HIT TP » sont du **biais de survie** : on montre les gagnants, jamais les 13 SL.

**Lien avec ma propre histoire** : mon contrôle aléatoire à t=+5,3, mon DOT à 42,9 % qui était un biais de sélection. Ce canal fait volontairement ce que j'ai fait par erreur, il choisit ce qu'il montre.

## Correction (Tony, 17/10 vers 02h10)
« C'est gratuit, ils ne vont pas te montrer les gagnants. » C'est juste : cet audit **ne juge que le gratuit**, et ne dit rien du VIP. J'avais présenté la conclusion trop largement.
Nuance : si le gratuit était **conçu pour perdre**, on aurait nettement moins de 33 % de gagnants. On en a 32 % (6 sur 19), c'est-à-dire du hasard, ni bon ni piégé.
**Prochain test, sur le VIP de façon indirecte** : leurs posts « HIT TP IN ELITE » contiennent des affirmations vérifiables (par ex. le 11/09 : « went from entry to TP in just 6 minutes »). Je regarde si le marché réel a fait ce mouvement à ce moment-là. Si leurs captures ne collent pas au marché, le VIP ment.

## Hyperliquid, 1er regard (47 258 comptes du leaderboard public)
- PnL > 0 : 49 % sur l'all-time, 49 % sur le mois, **18 %** sur la semaine. Seulement 10,7 % sont positifs sur les trois fenêtres à la fois.
- **Il y a de la persistance** : P(semaine > 0 | mois > 0) = 28 %, contre 9 % si le mois était ≤ 0. Elle est réelle, même si elle reste modeste.
- Les profils « bot » (capital > 10 k$, volume mensuel > 50× le capital) sont 3 031, dont 999 positifs sur l'all-time et le mois (33 %).
- Les ROI extrêmes (+8 189 % sur le mois avec 25 k$) sont presque sûrement des comptes rechargés ou du levier extrême. À examiner un par un dans leurs fills.

## Les horaires des posts, et ce que fait BTC autour (17/10 vers 02h20, bougies 1h)
| type de post | n | BTC dans les 6 h AVANT | BTC dans les 24 h APRÈS | heures (UTC) |
|---|---|---|---|---|
| « résultat / profit / HIT TP » | 16 | **+0,62 %** | **−0,22 %** | surtout **12h-16h** (9 sur 16) |
| signal ($BTC … SL) | 29 | +0,37 % | +0,83 % | 8h-16h |
| autres (marketing, « drop ❤️ ») | 78 | 0,00 % | +0,01 % | toute la journée |

**Ce que ça montre :**
1. **Les posts « profit » arrivent APRÈS une hausse.** Les deux plus forts : le 11/09 13h15 (« entry to TP in 6 minutes ») après **+2,61 %** en 6 h, et le 02/10 04h57 (« BTC IS PUMPING LIKE CRAZY ») après **+2,24 %**. Ensuite, BTC **retombe** dans les 24 h : −2,37 % et −2,39 %. On célèbre au sommet, au moment où le nouveau venu a le plus envie d'acheter le VIP, et c'est souvent juste avant la baisse.
2. Leurs affirmations VIP sont **compatibles** avec le marché : il y a bien eu un mouvement rapide avant le post « 6 minutes ». Je **ne peux pas prouver** qu'elles sont fausses. Je constate seulement qu'elles sont publiées après coup, jamais avant.
3. Les posts se concentrent **entre 12h et 16h UTC**, c'est-à-dire l'après-midi en Europe et l'ouverture des États-Unis. Ce sont des heures d'audience, pas des heures de marché particulières.
**Pour juger le VIP lui-même**, il faudrait ses signaux **avant** les mouvements, horodatés : soit s'abonner (c'est payant), soit faire tourner `telegram-vision-signals` sur le canal VIP. Sans ça, le test reste indirect.
