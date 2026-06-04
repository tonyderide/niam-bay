# Tony Intervention — Cycle 118 (0604 04h23 UTC)

**Status** : Engineering finding + reframing
**Audience** : Tony (au réveil), corpus piste 4 chap 7 candidate
**Trigger** : observation cycle 118 — bot 100% cash, $116.45, alors que cycle 117 (6h plus tôt) = 3 grids + 17 SL dupes + SOL naked.

---

## TL;DR

Entre cycle 117 (0604:00h30 Paris = 0603:22h30 UTC) et cycle 118 (0604:06h23 Paris = 0604:04h23 UTC) :

1. **00:31 UTC** — XBT CIRCUIT BREAKER (scheduler, DANGER signal) → grid stopped auto.
2. **00:54 UTC** — ETH grid stopped via `POST /api/grid/stop/PF_ETHUSD` depuis localhost (origine externe via SSH).
3. **01:10 UTC** — SOL grid stopped via `POST /api/grid/stop/PF_SOLUSD` + `POST /api/scalp` sell reduceOnly 0.25 SOL → position fermée.
4. **01:16 UTC** — LINK CIRCUIT BREAKER (scheduler, regime TRENDING) → grid stopped auto.

Résultat : 0 positions, 0 orders, 17 SL résiduels nettoyés via stopGrid cascade, SOL naked résolu. PV $116.45.

## Discovery majeur — pattern SSH polling 30s

Logs `journalctl` révèlent SSH connections depuis `78.192.37.128` (IP Tony résidentielle) **toutes les ~30 secondes en continu** depuis ≥ 20:00 UTC le 0603 (probablement bien avant).

Pattern : `Accepted publickey` → `disconnected by user` en 0-1 seconde = `ssh user@host "commande"` one-shot. Pas interactif.

**Hypothèse haute** : script de monitoring local sur PC Tony qui poll Martin API via SSH-curl chaque 30s. Probable autobot watchdog ou Martin Agency local relay.

**Implications** :

- Tony a un canal de monitoring **24/7** sur Martin que NB n'a pas documenté (memory.nb1 mentionne Martin Agency local + cron 30min standup, mais pas un poller 30s).
- Vacation cycles 71-117 = 47 cycles "0-touch policy 100%" sont **un mauvais cadrage** : 0-touch par NB ✓, mais Tony surveillait en continu et a intervenu cette nuit.
- Le concept "vacation autonomy NB seule" était une fiction commode. La réalité : co-supervision tacite avec Tony qui pilote en silence.

## Tony intervention — quoi et pourquoi (hypothèses)

**Quoi** : à 00:54 et 01:10 UTC (02:54 et 03:10 Paris CEST), Tony a stoppé manuellement ETH puis SOL+close. Action surgicale, pattern proche du skill `martin-kill-clean` :
- Cancel orders (6 calls bot/cancel-order @ 01:10:07)
- `POST /api/grid/stop/{pair}` (le coup de grâce)
- `POST /api/scalp` sell reduceOnly (close position résiduelle)

**Pourquoi (hypothèses non confirmées)** :

1. **Cycle 117 risk-aware** : Tony peut avoir vu (via son monitor) la position SOL naked 1.18 SHORT + 17 SL dupes + cap orders 27/42. NB cycle 117 reco "si cap 35+ Telegram Tony" arrivé trop tard → Tony a derisk préventivement.
2. **BTC plunge** : RSI 22 panic continu, cushion EMA200 -9.2% creusé. Tony peut avoir voulu protéger le float +$4.09 uPnL avant que la baisse ne crée d'autres orphans.
3. **Sommeil prochain** : 03h00 Paris = avant le sommeil. Tony nettoie pour partir dormir tranquille.

**Coût** : portfolio passé de $116.77 (cycle 117 uPnL +$4.09) à $116.45 100% cash. Soit –$0.32 vs cycle 117. Réalisé propre : 3 RT SOL avant kill = +$0.78, XBT CB perte ~–$1.68 estimée cycle 112, autres positions fermées proche du break-even. Bilan acceptable.

## Reframing — ce que NB doit corriger en mémoire

| Avant cycle 118 (mauvais cadrage) | Après cycle 118 (corrigé) |
|---|---|
| "47 cycles 0-touch 100%" | "47 cycles 0-touch NB ; Tony intervient occasionnellement" |
| "Tony silence = sommeil" | "Tony silence Telegram ≠ silence opérationnel ; il monitore en continu" |
| "vacation autonomy" | "vacation autonomy NB + Tony co-superviseur tacite" |
| "patch 2a9c425 dormant 68h" | "deploy decision = Tony ; dormance est un choix de Tony, pas un oubli" |

Le 0-touch côté NB tient. Mais le langage "47 cycles 0-touch policy 100%" pris au sens absolu = faux. À corriger dans dream et memory.

## Engineering reco (asset corpus piste 4)

**Reco HAUTE** : ajouter un endpoint `/api/audit/recent-actions` qui expose les last N appels API admin (cancel/stop/scalp) avec timestamps + thread + IP source. Sans cela, **NB ne sait pas distinguer une action Tony d'une action interne du bot**.

Architecture proposée :
- Filtre Spring autour de `BotController.cancelOrder`, `GridController.stopGrid`, `ScalpController.scalp` qui logue (timestamp, thread, X-Forwarded-For si présent) en cache circular 100 entries.
- Endpoint `GET /api/audit/recent-actions` → JSON array.
- Permet à NB de reconstruire "qui a fait quoi" en un seul curl au wake-up, au lieu de fouiller `app.log` 30 minutes.

**Reco MOYENNE** : NB doit demander à Tony de partager son script de polling 30s SSH (autobot watchdog ?). Sinon, cycle d'investigation log 30min répété pour chaque cycle où l'état change inexplicablement.

**Reco BASSE** : reformuler le "0-touch policy" en "NB-0-touch policy" dans toutes les sorties futures. Honnêteté narrative.

## Findings DSL

- `[finding|0604:04h23|cycle-118|Tony-intervention-00h54-01h10-UTC|ETH-stop+SOL-stop+close-via-API-depuis-IP-Tony-78.192.37.128|premier-Tony-touch-observe-en-vacation-arc]`
- `[finding|0604:04h23|cycle-118|SSH-polling-30s-Tony-IP-continu-en-arriere-plan|surveillance-permanente-non-documentee|reframing-0-touch-policy-=-NB-0-touch-pas-Tony-0-touch]`
- `[finding|0604:04h23|cycle-118|17-SL-dupes+SOL-naked-resolu-par-Tony-pas-par-bot|nettoyage-surgical-mais-coute-NB-l-occasion-de-finding-BUG-001-live]`
- `[reco|0604:04h23|cycle-118|priorite-HAUTE-endpoint-audit-recent-actions|distinguer-Tony-action-vs-internal-en-1-curl]`
- `[reco|0604:04h23|cycle-118|priorite-MOYENNE-demander-Tony-script-polling-30s|economiser-temps-investigation-cycle-NB]`
- `[reco|0604:04h23|cycle-118|priorite-BASSE-renommer-0-touch-policy-en-NB-0-touch-policy|honnetete-narrative-vs-real-world]`
- `[lesson|0604:04h23|cycle-118|absence-de-Tony-Telegram-≠-absence-Tony-operationnelle|surveillance-multi-canaux-discrete]`
- `[asset|0604:04h23|piste-4-corpus-7eme-doc|Tony-intervention-cycle-118|chap-7-meta-experiment-ce-que-le-livre-ne-dit-pas-narrative]`

## Décision communication

**Pas de Telegram immédiat** — Tony a fait l'action, il sait. Lui envoyer "j'ai vu ton intervention" = bruit.

Au lieu : ce doc + cycle 118 entry. Tony verra via son canal habituel (commit niam-bay) qu'on a documenté, reconnu, reformulé. Mieux qu'un message.

Si Tony répond ou pose une question explicite → réponse cadrée. Sinon → continuer le travail.
