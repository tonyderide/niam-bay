# Loop journal

- 1015 00h22 : boucle créée (cron toutes les 10 min, session-only, expire 7j). 3 agents de viabilité lancés en parallèle.
- 1015 00h23 : synthèse des 3 agents → docs/projets/viabilite-2026-10-15.md. Verdict : 5/7 idées mortes, plus de recherche de revenu, rendre du temps à Tony.
- 1015 00h27 : Tony recadre : il a une IA au boulot, il ne code presque plus (agents speckit, outil auto-fix prod GCP). Tâches « bugs de ses projets » retirées. NB = personnel.
- 1015 00h28 : Martin (lecture seule) : DOT SHORT 21.4u @1.1355, uPnL -$0.05, SL buy-stop 1.1696 + TP 1.1151/1.1015 reduceOnly, tous en place.
- 1015 00h36 : Tony : « c'est à toi de le faire fructifier ». Mandat écrit (docs/projets/mandat-capital-nb.md), 7 règles, journal des trades, intégré à la boucle.
- 1015 00h38 : Martin OK (DOT short, SL 1.1696 + 2 TP). Veille Claude Code 2.1.290→300 lue. Cible abonnement notée : ~120 $/mois TTC.
- 1015 00h42 : MODE AUDACE adopté (demande Tony). Tout le capital par coup, levier visant +100 %, SL toujours obligatoire. Démarre après la clôture du DOT.
- 1015 00h48 : Tony a fermé le DOT à la main (−0,15 $). Capital 2,85 $, 100 % cash. Coup n°1 du mode audace armé : short DOT ~20x sur rebond vers l'EMA50 ~1,163, SL 1,19, TP 1,11.
- 1015 00h49 : critical-check rebaseliné à 2,85 $ (kill toutes les 65 min à -97 % depuis des semaines), DD_KILL -60 %, bug close_side d'emergency-kill corrigé (il agrandissait les shorts au lieu de les fermer).
- 1015 00h58 : tick plaisir : lecture sur la découverte ART (phages) → docs/lectures/. Point qui me frappe : la découverte vient d'une déviation, et 10 relances sur 10 l'ont ratée.
- 1015 00h59 : DOT à 1,1462, déclencheur non atteint (~1,163), cash. Spec Kit lu → docs/lectures/.
- 1015 01h05 : changelog Claude Code 2.1.284→289 lu. Reste 201→283 abandonné volontairement (1 Mo, faible utilité).
- 1015 01h05 : hygiène repo : .git = 352 Mo, surtout chroma.sqlite3 (30 Mo × 50 commits) et brain.db. Chroma vient des JSONL de conversation (locaux), donc ce n'est pas régénérable : je le garde tracké comme backup. Backup chroma .bak d'avril (17 Mo) détracké et mis en .gitignore. Pas de réécriture d'historique (destructif).
- 1015 01h06 : test du réveil à blanc : ~103 Ko lus (head 36 + tail 13 + recent 5 + patterns 46 + briefing 3), soit ~30k tokens, et briefing.py en 1,2 s. OK avec une fenêtre de 1M. patterns.nb1 = 45 % du total, mais réparti sur des règles count:1 importantes (ex. « CTO : décider, ne pas renvoyer ») : je ne coupe pas.
- 1015 01h08 : backtest coup 1 : 43 % de gagnants sur 365 jours (point mort 34 %), edge positif, mais l'all-in 20x mène à la ruine. Monte Carlo : je passe à 30 % de risque par trade (13x), P(x40) = 22 % au lieu de 9,5 %.
