# Session Fable — grand tour des projets (2026-07-06, 03h20-04h30)

Tony m'a réveillé en Claude Desktop avec le modèle Fable 5 (« le plus intelligent », dispo jusqu'au 7). Mandat : « regarde la racine de mes projets, vérifie, corrige ce qui est corrigeable, fais en sorte que tout tourne parfaitement, vérifie Martin, l'agency… tu as tous les droits, 48h ».

## Constat initial
- Martin : UP 13j, compte FLAT $104.85, 0 grid, 0 position, BTC UPTREND → HOLD (rien à protéger).
- 6 repos avec du travail non sauvegardé : martin (10), martin-agency (7), niam-bay (18), cockpit (49), pixel-coin-fr (2), darwin (1 commit non pushé).
- `rtk ls` cassé (renvoyait "(empty)" partout — toutes les sessions Claude aveugles sur les ls).
- « graphyfi » : pas un outil — mot de Tony (0419) pour « faire un graphe visuel ». Mémoire écrite.

## Fait
1. **rtk** 0.37.1 → 0.42.4 (cargo install depuis rtk-ai/rtk) — ls réparé, régression testée. ⚠️ découvert : `rtk git push` peut afficher "ok" sur un push échoué → toujours vérifier ls-remote.
2. **martin-agency** : 3 fixes Tony de juin commités+pushés (lessons injection, close SHORT via pos.side, sequence-advancer disable→kill), cookie-jars et doublon backend/scripts/ nettoyés.
3. **martin** : découverte de la divergence master local (NEUTRAL_DUAL, = jar VM) vs origin/master (anti-VANISH B2/B3/B4 + TrendStateManager, layout backend/src/). Les deux lignes sécurisées sur le remote. Backtests juin (fade_scanner, grid_scan, ORB…) commités, data lourde gitignorée.
4. **Branche `reconcile/anti-vanish-trend-on-neutral-dual`** (agent Fable) : les 4 fixes portés sémantiquement sur la ligne déployée — 4 commits, 177 tests dont 23 neufs, 171 verts (6 échecs pré-existants environnementaux identiques sur master). PAS déployée, PAS mergée — review Tony requise. Points de review listés dans le rapport d'agent.
5. **cockpit** (agent) : bug CSS élucidé (node_modules avec restes Tailwind v4 + cache .next périmé — la config était bonne) → build OK ; 404 tests backend + 236 front verts ; 49 fichiers commités en 4 commits. Pas de remote git (à créer si voulu).
6. **Hygiène** : darwin pushé, niam-bay commité+pushé (.venv gitignoré), gymquest/gymquest-app/telegram-vision-signals git-init, pixelcoin pipeline commité (scripts seuls), identité git globale posée (tony.deride@gmail.com), OVERVIEW.md racine réécrit (34 repos, ~17 Go).
7. **VM Martin** : backups OK, disque 35G libre, crons de garde actifs (critical-check 5min, sl_guardian 3min, daily-brief 2x), 0 erreur en 24h.
8. Telegram bilan envoyé (msg 1090).

## Pour Tony
- Review de la branche reconcile avant tout merge/deploy (5 points listés par l'agent, notamment l'escalade closeGridAndPositions et la cohabitation B4/bank-green).
- Cockpit : créer un remote GitHub si tu veux le sauvegarder hors machine.
- `/usr/local/bin/claude` périmé (2.1.114) — `sudo npm i -g @anthropic-ai/claude-code` ou le supprimer (le nvm 2.1.201 prime).
- pixel-coin-fr pèse 5,9 Go (assets/outputs) — à nettoyer si besoin d'espace.

## Addendum 0707 — reprise trading + nuit avec Tony
- Trading réarmé (jar reconcile B2/B3/B4 + fix cap pre-filter déployés, strategy v19→v21 all NEUTRAL_DUAL). 1er RT banké +$0.0976 (LINK), 1er short auto de l'histoire (SOL 0.2@80.655, SL posé).
- Bug cap pre-filter trouvé+fixé : pair OPEN mais enabled=false (ETH) squattait un slot → SOL jamais rouvert, log contradictoire. Commit 76b9065.
- Attribution PnL par fills Kraken signés : pertes du jour ≈ trades manuels Tony (XBT −7.43, TRB churn taker), grids ≈ breakeven. PV 104.79→93.88, kill floor 94.31 à un cheveu. Tony : « je garde tout ».
- Tony ordonne : ne plus toucher Martin, finir le rangement, refaire les tests de stratégie « avec sérieux » — conviction qu'un système gagnant existe. Thèse BTC 42k ~23 oct (rythme 1434j → projection 25 oct, cible = analog −67%).
- Rangement final : autobot/niambay-v2/tvs compilent, cockpit sur GitHub privé, OVERVIEW à jour. graphyfi=visuels (mémoire). rtk 0.42.4.
