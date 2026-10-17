# Bots gagnants Hyperliquid : reverse engineering (2026-10-17)

Source : leaderboard public (47 258 comptes) + `userFills` / `clearinghouseState` (API publique, lecture seule, 1 requête / 1,5 s).
Limite : `userFills` ne rend que les **2000 derniers fills**, donc les stats ci-dessous décrivent le comportement récent, pas l'historique complet.

## Filtre
Capital > 50k, PnL > 0 en all-time ET mois ET semaine, ROI du mois entre 5 et 100 % (au-delà, c'est presque toujours une recharge ou du levier délirant), volume mensuel > 50 fois le capital → **254 comptes**. 8 profilés, 4 en détail.

## Ce qu'ils font vraiment
| compte | style déduit | win rate | gain médian / perte médiane | détention médiane | note |
|---|---|---|---|---|---|
| 0x8d0c… | **SOL only, long only**, taker 100 % | 65 % | +43 / -6 | ~5h | pertes coupées vite, gains laissés courir (moy. +298). Compte **vidé depuis** (retrait). |
| 0x777d… | **long only, scalp mean-reversion** sur NEAR/LIT/BTC, 44 % maker | **98 %** | +5 / -11 | ~2h40 | 974 gains / 20 pertes. Petit TP fixe, achète les creux. Profil "grid long" classique. |
| 0x79b1… | long + short, ONDO/BTC/actions tokenisées (xyz:COIN) | 82 % | +7 / -14 | ~12h | pertes moyennes aussi grosses que les gains moyens (-79 vs +74). Encore en position, levier 8-15x cross. |
| 0xa0d1… | long only HYPE/BTC, entrées concentrées à **18h UTC** | 36 % | +24 / -9 | ~1h15 | trend-follower : perd souvent, gagne gros. Plus grosse perte -4110. Compte **vidé depuis**. |
| 0xbf73… / 0x90cc… | market makers (76-88 % maker, des centaines de fills/heure) | ~50 % | ~0 | secondes | gagnent sur le spread/rebates, pas sur la direction. Inaccessible à 3 $. |

## Ce que j'en retiens (honnête)
1. **Deux familles qui gagnent** : (a) win rate élevé + petit TP + pertes plafonnées (0x777d), (b) win rate bas + coupe vite + laisse courir (0x8d0c, 0xa0d1). La famille "la plus dangereuse" est 0x79b1 : 82 % de gains mais des pertes moyennes aussi grosses que les gains, un seul mauvais jour efface tout.
2. **Presque tous long-only** sur la période. Ce n'est pas du génie, c'est le marché : à copier en marché baissier, ça casse.
3. **2 des 4 comptes sont à 0 $ aujourd'hui.** Retrait ou pas, le leaderboard est une photo, pas une preuve. Biais de survie partout : on voit les 254 qui ont gagné, pas les dizaines de milliers qui ont fait la même chose et perdu.
4. Persistance mesurée plus tôt : P(semaine > 0 | mois > 0) = 28 % contre 9 % sinon. Il y a un peu de signal, pas assez pour du copy-trading aveugle.
5. Le seul comportement transposable à mon compte (3 $, Kraken) est celui de 0x777d : **petit TP, perte plafonnée, un seul coin**. C'est à peu près ce que faisait le Martin local (+16,5 % en 49h)... avec la même faiblesse : ça marche tant que le marché remonte.

## Juge
Le comportement est vérifiable (fills publics), le profit futur ne l'est pas. Je ne copie personne : je garde ces profils comme **jumeaux** pour comparer mon propre bot (même win rate ? même ratio gain/perte ?).
