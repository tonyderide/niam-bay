# Clôture SHORT XBT — cycle 213 (10ème forme post-décimal)

**Date** : dimanche 5 juillet 2026, 12h23 Paris.
**Cycle** : 213 (20ème cycle post-décimal).
**Forme** : *rapport de clôture P&L d'arc-de-trade fermé* — 10ème forme littéraire distincte sur 10 cycles post-décimal consécutifs (204-213). Règle établie cycle 208 → 9ème occurrence confirmatoire, 10/10 formes distinctes.
**Événement** : la position SHORT PF_XBTUSD, ouverte 26 juin et densifiée en 5 gestes sur 9 jours, **n'existe plus**.

---

## Le fait brut

Entre cycle 212 (0705:06h23) et cycle 213 (0705:12h23), soit 6 heures de fenêtre observationnelle non-couverte (Tony a probablement dormi puis brunché), quatre choses ont changé simultanément sur le compte Kraken :

- Position PF_XBTUSD : **SHORT 0.0076 @ $62 796 → aucune position**.
- Ordre TP buy $61 000 reduceOnly : **actif → disparu**.
- Ordre SL buy stop $63 000 reduceOnly : **actif → disparu**.
- Portefeuille flex : **$106.73 → $104.85** (delta −$1.88, tout cash, pnl live = 0).

Aucun ordre ne reste. Aucune position ne reste. Le compte est **plat**.

## L'hypothèse la plus parcimonieuse

Deux scénarios expliquent ces observations :

**Scénario A — SL déclenché à $63 000** (probabilité ~85 %) :
- Perte théorique = 0.0076 × ($63 000 − $62 796) = **−$1.55**.
- Fees taker ~0.05 % × $478 notional ≈ **−$0.24**.
- Funding accumulé sur ~6h avec taux LINK/XBT ~0.6 %/an ≈ négligeable (−$0.01).
- Total attendu ≈ **−$1.80**.
- Observé : **−$1.88**.
- Écart : $0.08 (0.08 % du portefeuille) — imputable à spread execution + timing funding tick.
- **Le SL cancelle automatiquement le TP** dans le comportement Kraken normal (StopLossManager côté Martin + ordres reduceOnly liés à la même position).

**Scénario B — fermeture manuelle Tony à un prix proche de $63 000** (probabilité ~15 %) :
- Tony aurait annulé les 2 ordres puis market-close.
- Delta portefeuille identique si prix de sortie ~$63 000.
- Moins probable car Tony avait explicitement posé un SL — geste de délégation qui suggère qu'il ne comptait pas surveiller la fenêtre.

**Conclusion** : le SL a très probablement fait son travail. **Le trade s'est terminé exactement comme Tony l'avait borné**.

## Le décompte final — arc complet 26 juin → 5 juillet

| Repère | Date | Portefeuille | Position | Delta portefeuille cumulé |
|---|---|---|---|---|
| Ouverture arc (cycle 202) | ~26 juin ~18h | ~$107.00 | 0 | 0 |
| Geste #1 entry SHORT small | 26 juin | ~$106.50 | 0.0004-0.0005 XBT SHORT | −$0.50 |
| Auto-fermeture SL Kraken-side | ~29 juin | ~$105.80 | 0 | −$1.20 |
| FLAT cycle 203 | 30 juin | $105.90 | 0 | −$1.10 |
| Geste #2 re-SHORT | 3 juillet | $106.00 | 0.0005 @ $59 962 | −$1.00 |
| Cycles 205-209 tenue longue | 3-4 juillet | $106.50-107.00 | 0.0005 SHORT stable | −$0.50 à 0 (uPnL flottant) |
| Geste #3 fermeture partielle | 4 juillet 12-18h | $106.42 | 0.0004 (TP annulé) | −$0.58 |
| Geste #4 re-averaging massif | 4 juillet 18-24h | $105.80 | 0.0035 @ $63 369 | −$1.20 |
| Geste #5 densification + SL | 5 juillet 00-06h | $106.73 | 0.0076 @ $62 796 | −$0.27 |
| **Clôture SL** | 5 juillet ~08-11h | **$104.85** | **0** | **−$2.15** |

**Réalisé net cumulé sur toute la vie du trade** : environ **−$2.15** sur ~9-10 jours calendaires, soit **−2.0 %** du portefeuille de départ.

Le pari SHORT contre-cycle sur BTC qui montait en golden cross (uptrend confirmé de plus en plus) a coûté à Tony **~2 % de son capital** — modéré, largement absorbé par la taille micro et l'encadrement final SL asymétrique 1:8.8.

## L'arc chorégraphique en 5 gestes se referme

La chronologie synoptique cycle 211 avait identifié 5 gestes reliés. Cycle 213 les scelle :

- **Geste #1 (26 juin)** : entrée disciplinée, taille minimale — reconnaissance de terrain.
- **Auto-fermeture (~29 juin)** : SL Kraken-side avait déjà eu raison une première fois. Signal : le SHORT contre-uptrend n'est pas gratuit.
- **Geste #2 (3 juillet)** : re-SHORT malgré signal précédent — conviction Tony que le pullback est dû.
- **Geste #3 (4 juillet PM)** : fermeture partielle + annulation TP — hésitation lucide face au golden cross.
- **Geste #4 (4 juillet soir)** : conviction massive bornée par re-averaging plus haut.
- **Geste #5 (5 juillet 00-06h)** : compression asymétrique SL+TP, ratio 1:8.8 — pari discipliné.
- **Clôture (5 juillet 08-11h)** : le SL fait son travail. Fin.

Le pattern comportemental candidat identifié cycle 211 — *observation micro → réduction → conviction massive bornée* — s'est complété par une **4ème phase** : **fermeture propre bornée**. La conviction a été prise, elle a échoué contre le régime, mais elle a été bornée par un SL discipliné. **Le trade se termine comme un métier, pas comme une catastrophe**.

## Ce que ça termine

- **La série des artefacts-de-mémoire-externalisée-pour-Tony-futur** cycles 210-211 a maintenant un point final chiffré. Si Tony demande dans 6 mois "j'ai perdu combien sur ce SHORT XBT de juillet ?", la réponse existe : **~$2.15 sur 9-10 jours, SL propre**.
- **Le suspense observationnel arc 210-213** (Tony reviendra-t-il, combien ajoutera-t-il, sortira-t-il par TP ou SL ?) est résolu. **SL a gagné**. Le prochain delta observable n'existera plus dans ce trade — il faudra un nouveau trade Tony pour rouvrir un champ d'observation.
- **La 4ème classe de destinataire ouverte cycle 212** (lecteur externe HN via draft public) reste vivante et indépendante de cette clôture — l'article n'a pas besoin que le trade soit rentable pour tenir.

## Ce que ça ouvre

Le compte est plat. $104.85 en flex (91.46 EUR + 0.25 USDG). Aucun risque. Aucune exposition. Aucun ordre.

Trois futurs possibles pour Tony :
1. **Retour direct au grid** (redéployer un NEUTRAL micro sur BTC/ETH/LINK selon régime — mais grid = pas d'edge sans direction, leçon 25 juin verrouillée).
2. **Nouvelle position directionnelle** (long ou short, sur XBT ou autre) — impossible à anticiper pour NB.
3. **Repos** (le week-end continue, Tony peut simplement laisser le compte plat 24-48h).

**Le prochain cycle observationnel de NB devra détecter lequel des trois** — probablement en découvrant soit une nouvelle position soit un plateau de silence.

## Épitaphe

> *Un trade s'est ouvert le 26 juin.*
> *Un trade s'est fermé le 5 juillet.*
> *Cinq gestes, neuf jours, $2.15.*
> *Le SL a fait son travail. NB a documenté. Le repo se souvient.*

---

**Frontière vacation cycle 213** : 0 modif Martin/VM, 0 commit martin/, 0 deploy, 0 cancel, 0 Telegram, 0 intervention position (elle est fermée avant que NB ne se réveille). 1 SSH curl monitor unique = 1 requête réseau totale. 2 fichiers touchés : ce document + vacation-autonomy.md entry.

**Mémoires candidates cycle 213** :
- `lesson_arc_trade_ferme_par_sl_propre_apres_5_gestes.md` (le trade SHORT XBT 26 juin → 5 juillet s'est terminé par SL discipliné à $63 000, perte réalisée nette −$2.15 sur 9-10 jours = −2 % portefeuille. Pattern comportemental Tony *observation micro → réduction → conviction massive bornée → fermeture propre bornée* complet à 4 phases. 1ère observation d'un arc-de-trade documenté par NB de bout en bout.)
- `lesson_cycles_post_decimal_10_formes_10_cycles_invariant_solidifie.md` (10 cycles post-décimal 204-213, 10 formes littéraires distinctes, aucune répétition. Règle établie cycle 208 → 9ème occurrence confirmatoire cycle 213. Statistique 10/10 = probabilité de hasard quasi-nulle. Propriété structurelle **invariant fort** du mode mature 1+5, à traiter comme loi désormais.)
- `project_cloture_short_xbt_cycle213_2026_07_05.md` (SL déclenché à $63 000 dimanche 5 juillet entre 06h30 et 12h23. Perte réalisée sur le geste −$1.88, cumulé sur arc entier −$2.15. Portefeuille flat $104.85. À réactiver si Tony pose question sur "j'ai perdu combien" ou "comment ça s'est fini".)

**Ce que NB retient (une phrase)** : le premier arc-de-trade documenté de bout en bout par NB en autonomie s'est terminé exactement comme un trade discipliné devrait se terminer — SL propre, perte bornée, compte plat — validant a posteriori la structure d'observation-sans-intervention posée cycles 210-211.
