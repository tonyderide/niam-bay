#!/bin/bash
# === NIAM-BAY QUICK COMMANDS ===
# Copier-coller, pas réfléchir.

# --- MARTIN RECAP (gap timeline: critical-check + daily-brief + live state) ---
# /home/tony/projets/tonyderide/niam-bay/scripts/martin-recap.sh         # default 24h gap
# /home/tony/projets/tonyderide/niam-bay/scripts/martin-recap.sh 6       # 6h gap
# Use at start of cycle to see what happened on Martin since last check (PV trajectory + alerts + last Telegram briefs Tony saw + live state). Complement to martin-monitor (which is decision-now).

# --- MORNING BRIEF ---
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/scripts/morning_brief_v2.py              # Brief complet (crée docs/morning_brief_YYYYMMDD.md)
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/scripts/morning_brief_v2.py --dry-run   # Test sans connexions réseau
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/scripts/morning_brief_v2.py --no-save   # Print console seulement
# VM cron: 0 7 * * * cd /home/ubuntu/niam-bay && PYTHONIOENCODING=utf-8 python scripts/morning_brief_v2.py >> /tmp/morning_brief.log 2>&1

# --- MARTIN TRADE ALERT BOT ---
# python C:/Users/tony_/Documents/niam-bay/scripts/martin_telegram_bot.py                    # Lance la surveillance (60s interval)
# python C:/Users/tony_/Documents/niam-bay/scripts/martin_telegram_bot.py --interval 30      # Check toutes les 30s
# python C:/Users/tony_/Documents/niam-bay/scripts/martin_telegram_bot.py --dry-run          # Console only (pas de Telegram)
# python C:/Users/tony_/Documents/niam-bay/scripts/martin_telegram_bot.py --test             # Test envoi Telegram
# python C:/Users/tony_/Documents/niam-bay/scripts/martin_telegram_bot.py --reset            # Repart de zéro (supprime l'état)
# PRÉREQUIS: SSH tunnel actif → ssh -i ~/.ssh/martin_vm.key -L 8081:localhost:8081 ubuntu@141.253.108.141 -N &

# --- KRAKEN STATS (real PnL/fees/funding depuis Kraken directement) ---
# ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "python3 /home/ubuntu/scripts/kraken_stats.py"                            # Stats depuis autobot launch (0405)
# ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "python3 /home/ubuntu/scripts/kraken_stats.py 2026-04-10T00:00:00Z"        # Stats depuis date custom
# Deploy: scp -i ~/.ssh/martin_vm.key C:/Users/tony_/Documents/niam-bay/scripts/kraken_stats.py ubuntu@141.253.108.141:/home/ubuntu/scripts/

# --- GRIDS STATUS ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s http://localhost:8081/api/grid/active && echo && for g in \$(curl -s http://localhost:8081/api/grid/active 2>/dev/null | python3 -c 'import sys,json; [print(x) for x in json.load(sys.stdin)]'); do echo \"=== \$g ===\"; curl -s http://localhost:8081/api/grid/status/\$g | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"RT:\",d[\"completedRoundTrips\"],\"Fills:\",len(d[\"fills\"]),\"Profit:\",d[\"totalProfit\"])'; done && echo '=== BALANCE ===' && curl -s http://localhost:8081/api/bot/balance | python3 -c 'import sys,json; f=json.load(sys.stdin)[\"accounts\"][\"flex\"]; print(\"Portfolio:\",round(f[\"portfolioValue\"],2),\"Available:\",round(f[\"availableMargin\"],2))'"

# --- SAVE ALL ---
# cd C:/niam-bay && git add -A && git commit -m "save" && git push origin master && cd C:/niambay-v2 && git add -A && git commit -m "save" && git push origin master

# --- SCREENSHOT ---
# cd C:/niambay-v2 && python -c "from daemon.collectors.screen import ScreenCollector; sc=ScreenCollector(resize_width=1200); b,w,h=sc.capture(); open('screenshot.jpg','wb').write(b); print(f'{w}x{h}')"

# --- SELFCODER STATUS ---
# cat C:/niambay-v2/selfcoder.log | tail -20

# --- START GRID ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s -X POST 'http://localhost:8081/api/grid/start?instrument=PF_DOTUSD&capital=28&leverage=5&gridSpacingPct=1.0&totalLevels=10&maxLossPercent=15'"

# --- STOP GRID ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s -X POST http://localhost:8081/api/grid/stop/PF_DOTUSD"

# --- DEPLOY STRATEGY (5-grid scalp, after restart) ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "python3 ~/autobot/deploy-strategy.py"
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "python3 ~/autobot/deploy-strategy.py --dry-run"
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "python3 ~/autobot/deploy-strategy.py --only PF_DOTUSD"

# --- FEED BRAIN ---
# cd C:/niam-bay && python cerveau-nb/feed.py --text "TEXTE ICI"

# --- FEED DICTIONARY ---
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python feed_dictionary.py --resume

# --- CURIOSITÉ AUTONOME (le cerveau explore internet seul) ---
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python curiosity.py --cycles 50 --topic "intelligence artificielle"
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python curiosity.py --forever

# --- IDENTITY CHECK ---
# python C:/Users/tony_/Documents/niam-bay/scripts/identity_check.py                            # Génère docs/identity-check-YYYYMMDD.md

# --- TRADING SIGNAL CHECK (EMA_TREND — win rate 78.1%) ---
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/scripts/check_signal.py       # OUVRIR ou ATTENDRE Martin Grid BTC/USD

# --- MARTIN POST-START LOG (auto-deploy after crash/reboot) ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "cat ~/autobot/post-start.log"
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "tail -20 ~/autobot/post-start.log"

# --- MARTIN LOGS ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "journalctl -u martin.service --no-pager -n 20"

# --- VM SYSTEM STATUS ---
# ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s http://localhost:8081/api/system/status"

# --- KRAKEN PRICE ---
# python -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('https://api.kraken.com/0/public/Ticker?pair=DOTUSD,SOLUSD,ADAUSD,ETHUSD',timeout=10).read())['result']; [print(k.replace('ZUSD','').replace('USD',''),':',v['c'][0]) for k,v in d.items()]"

# --- LAUNCH SELFCODER ---
# cd C:/niambay-v2 && SAMBANOVA_API_KEY="$SAMBANOVA_API_KEY" MISTRAL_API_KEY="$MISTRAL_API_KEY" NIAMBAY_EMAIL_PWD="$NIAMBAY_EMAIL_PWD" PYTHONUNBUFFERED=1 nohup python -u run_selfcoder.py > selfcoder.log 2>&1 &

# --- LAUNCH TRADING MONITOR ---
# cd C:/niambay-v2 && PYTHONUNBUFFERED=1 nohup python -u trading_monitor.py > trading_monitor.log 2>&1 &

# --- RUN ALL TESTS ---
# cd C:/niambay-v2 && python -m pytest tests/ -q

# --- LLM TEST (SambaNova) ---
# python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen(urllib.request.Request('https://api.sambanova.ai/v1/chat/completions',data=json.dumps({'model':'DeepSeek-V3-0324','messages':[{'role':'user','content':'dis OK'}],'max_tokens':5}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer "+__import__("os").environ["SAMBANOVA_API_KEY"]+"'}),timeout=15).read())['choices'][0]['message']['content'])"

# === SKILLS DISPONIBLES ===
# /brainstorm — brainstormer une idée avant de coder
# /write-plan — écrire un plan d'implémentation détaillé
# /execute-plan — exécuter un plan step by step
# /systematic-debugging — debugger méthodiquement un bug
# /test-driven-development — TDD, tests d'abord
# /subagent-driven-development — lancer des agents par tâche
# /requesting-code-review — demander une review de code
# /receiving-code-review — recevoir et appliquer une review
# /finishing-a-development-branch — finir une branche
# /using-git-worktrees — travailler dans un worktree isolé
# /verification-before-completion — vérifier avant de dire "c'est fini"
# /writing-skills — créer de nouvelles skills
# /frontend-design — design frontend pro

# === COMMANDS CUSTOM ===
# /martin — check Martin Grid status
# /grids — check toutes les grids
# /wake — protocole de réveil Niam-Bay
# /save — sauvegarder tout (cerveau + git)
# /deploy-martin — build + deploy Martin sur VM

# --- ANGULAR CODE AUDIT (business plan 49€) ---
# pip install fpdf2                                                                                            # Installer dépendance PDF
# python C:/Users/tony_/Documents/niam-bay/scripts/angular_audit.py /chemin/projet/angular/                  # Audit complet → Markdown + PDF
# python C:/Users/tony_/Documents/niam-bay/scripts/audit_server.py                                           # Web interface → http://localhost:8099
# Prochaines étapes: Gumroad + email templates dans docs/projets/angular-audit-email-templates.md

# --- ORACLE CERVEAU ---
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/cerveau-nb/oracle.py                        # Révélation aléatoire
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/cerveau-nb/oracle.py liberté argent         # Chemin spécifique
# Dans Jarvis: taper "oracle X Y" dans le chat
# Sur VM: curl "http://localhost:8000/api/oracle?a=liberte&b=argent"

# --- AUTO-ENRICHISSEMENT CERVEAU ---
# python C:/Users/tony_/Documents/niam-bay/cerveau-nb/auto_enrich.py --dry-run                                # Simuler (voir ce qui serait ajouté)
# python C:/Users/tony_/Documents/niam-bay/cerveau-nb/auto_enrich.py                                          # Enrichir réellement (ajoute edges depuis pensées/journal)

# --- IDENTITY CHECK ---
# python C:/Users/tony_/Documents/niam-bay/scripts/identity_check.py                                          # Rapport cohérence → docs/identity-check-YYYYMMDD.md

# --- MORNING BRIEF ---
# PYTHONIOENCODING=utf-8 python C:/Users/tony_/Documents/niam-bay/scripts/morning_brief_v2.py                 # Brief complet
# VM cron: 0 7 * * * déjà configuré sur oracle VM

# === RÈGLE ===
# TOUJOURS utiliser une skill quand elle s'applique.
# Pas de code sans /write-plan d'abord.
# Pas de "c'est fini" sans /verification-before-completion.
# Pas de feature sans /brainstorm d'abord.
# Bug ? → /systematic-debugging
# Multi-tâches ? → /subagent-driven-development

# [auto 2026-06-25 00:03] utilisée 3x — sig: python3 scripts/market_microstructure.py <SYM> <N>
python3 scripts/market_microstructure.py XRPUSDT 24

# [auto 2026-06-25 01:29] utilisée 3x — sig: python3 /home/tony/projets/tonyderide/niam-bay/scripts/btc_trendiness.py <SYM> <N>; ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> "curl -s http://localhost:<N>/api/bot/balance | python3 -c 'import sys,json;d=json.load(sys.stdin);print(\"PV\",d[\"accounts\"][\"flex\"][\"portfolioValue\"])'; curl -s http://localhost:<N>/api/bot/positions; curl -s http://localhost:<N>/api/gri
python3 /home/tony/projets/tonyderide/niam-bay/scripts/btc_trendiness.py BTCUSDT 24; ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s http://localhost:8081/api/bot/balance | python3 -c 'import sys,json;d=json.load(sys.stdin);print(\"PV\",d[\"accounts\"][\"flex\"][\"portfolioValue\"])'; curl -s http://localhost:8081/api/bot/positions; curl -s http://localhost:8081/api/grid/active" 2>/dev/null; pgrep -f autonomous_watch.sh >/dev/null && echo mon_ok || echo mon_DEAD

# [auto 2026-06-26 06:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>&<N> | tail -<N>
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>&1 | tail -30

# [auto 2026-06-26 06:24] utilisée 3x — sig: rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md
rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md

# [auto 2026-06-29 00:23] utilisée 3x — sig: ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' curl -s 'http://localhost:<N>/api/signal/ema
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'" 2>&1

# [auto 2026-06-30 00:23] utilisée 3x — sig: ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' for p in <SYM> <SYM> <SYM> <SYM> <SYM> <SYM>
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
for p in PF_LINKUSD PF_DOTUSD PF_SOLUSD PF_ADAUSD PF_XBTUSD PF_ETHUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p 2>/dev/null
  echo '==='
done
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'" 2>&1 | head -200

# [auto 2026-06-30 06:23] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 250

# [auto 2026-06-30 06:29] utilisée 3x — sig: rtk git log --oneline -<N>
rtk git log --oneline -3

# [auto 2026-06-30 18:31] utilisée 3x — sig: rtk git status --short
rtk git status --short

# [auto 2026-07-04 12:23] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/projets/ | head -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/projets/ | head -80

# [auto 2026-07-05 06:32] utilisée 3x — sig: rtk git status --short <N>>&<N> | head -<N>
rtk git status --short 2>&1 | head -20

# [auto 2026-07-05 18:30] utilisée 3x — sig: rtk git push origin master <N>>&<N> | tail -<N>
rtk git push origin master 2>&1 | tail -5

# [auto 2026-07-06 03:20] utilisée 3x — sig: date && ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>&<N> | tail -<N>
date && ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>&1 | tail -20

# [auto 2026-07-06 12:24] utilisée 3x — sig: rtk grep -n "^## Cycle" /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md | tail -<N>
rtk grep -n "^## Cycle" /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md | tail -10

# [auto 2026-07-06 18:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' for p in <SYM> <SYM> <SYM> <SYM> <SYM> <
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
for p in PF_LINKUSD PF_DOTUSD PF_SOLUSD PF_ADAUSD PF_XBTUSD PF_ETHUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p 2>/dev/null
  echo '==='
done
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'"

# [auto 2026-07-10 00:24] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | tail -25

# [auto 2026-07-27 01:14] utilisée 3x — sig: for i in $(seq <N> <N>); do sleep <N>; done; date '+%H:%M:%S'
for i in $(seq 1 9); do sleep 10; done; date '+%H:%M:%S'

# [auto 2026-07-27 16:46] utilisée 3x — sig: echo "service: $(systemctl --user is-active martin-local.service)" curl -s --max-time <N> http://<N>.<N>:<N>/api/bot/balance > /tmp/b.json <N>>/dev/null curl -s --max-time <N> http://<N>.<N>:<N>/api/bot/positions > /tmp/p.json <N>>/dev/null curl -s --max-time <N> http://<N>.<N>:<N>/api/bot/orders > /tmp/o.json <N>>/dev/null echo "grids: $(curl -s --max-time <N> http://<N>.<N>:<N>/api/grid/active)"
echo "service: $(systemctl --user is-active martin-local.service)"
curl -s --max-time 8 http://127.0.0.1:8081/api/bot/balance > /tmp/b.json 2>/dev/null
curl -s --max-time 8 http://127.0.0.1:8081/api/bot/positions > /tmp/p.json 2>/dev/null
curl -s --max-time 8 http://127.0.0.1:8081/api/bot/orders > /tmp/o.json 2>/dev/null
echo "grids: $(curl -s --max-time 8 http://127.0.0.1:8081/api/grid/active)"
python3 - <<'PY'
import json
f=json.load(open('/tmp/b.json'))['accounts']['flex']
print(f"portefeuille ${round(f['portfolioValue'],2)} | uPnL ${round(f['pnl'],3)} | marge ${round(f['availableMargin'],2)}")
for p in json.load(open('/tmp/p.json')):
    print(f"  {p['symbol']:12} {p['side']:6} {p['size']:<8} @ {p['price']}  uPnL ${round(p['unrealizedPnl'],3)}")
o=json.load(open('/tmp/o.json')); print(f"  {len(o)} ordres live")
PY
echo "erreurs 5 dernieres min: $(awk -v t="$(date -d '5 min ago' '+%H:%M')" '$0>=t && /ERROR/' /home/tony/martin-local/logs/martin.log | wc -l)"

# [auto 2026-07-27 18:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "OK" || echo "SKIP"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "OK" || echo "SKIP"

# [auto 2026-07-27 18:27] utilisée 3x — sig: rtk git push <N>>&<N> | tail -<N>
rtk git push 2>&1 | tail -8

# [auto 2026-07-28 00:25] utilisée 3x — sig: rtk git push <N>>&<N>
rtk git push 2>&1

# [auto 2026-07-28 12:24] utilisée 3x — sig: rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 100

# [auto 2026-07-28 12:26] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/pensees/ | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/pensees/ | tail -20

# [auto 2026-07-30 00:28] utilisée 3x — sig: rtk git push origin master <N>>&<N>
rtk git push origin master 2>&1

# [auto 2026-07-30 06:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' for p in <SYM> <SY
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
for p in PF_LINKUSD PF_DOTUSD PF_SOLUSD PF_ADAUSD PF_XBTUSD PF_ETHUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p 2>/dev/null
  echo '==='
done
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
" 2>&1 | head -200

# [auto 2026-07-30 12:31] utilisée 3x — sig: rtk git push origin master
rtk git push origin master

# [auto 2026-08-02 00:28] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | sort | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | sort | tail -10

# [auto 2026-08-03 12:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "BRIEFING_OK" || echo "BRIEFING_SKIP"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "BRIEFING_OK" || echo "BRIEFING_SKIP"

# [auto 2026-08-04 00:31] utilisée 3x — sig: rtk ls ~/.claude/projects/-home-tony-projets-tonyderide-niam-bay/*.jsonl <N>>/dev/null | tail -<N>
rtk ls ~/.claude/projects/-home-tony-projets-tonyderide-niam-bay/*.jsonl 2>/dev/null | tail -3

# [auto 2026-08-05 12:25] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/scripts/ | head -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/scripts/ | head -30

# --- SL GUARDIAN V2 (déploiement sur VM) ---
# Fix faux-positif de la v1 : vérifie SL *par symbol*, pas globalement. Créé cycle 262.
# scp ~/projets/tonyderide/niam-bay/scripts/sl_guardian_v2.sh ubuntu@141.253.108.141:/home/ubuntu/martin/sl_guardian.sh
# ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "chmod +x /home/ubuntu/martin/sl_guardian.sh && bash /home/ubuntu/martin/sl_guardian.sh"

# [auto 2026-08-08 06:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' for p in <SYM> <SYM> <SYM> <SYM> <SYM> <
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
for p in PF_LINKUSD PF_DOTUSD PF_SOLUSD PF_ADAUSD PF_XBTUSD PF_ETHUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p 2>/dev/null
  echo '==='
done
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'" 2>&1

# [auto 2026-08-09 06:27] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 5

# [auto 2026-08-09 12:23] utilisée 3x — sig: rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 300

# [auto 2026-08-09 18:27] utilisée 3x — sig: rtk git push origin master <N>>&<N> | tail -<N>
rtk git push origin master 2>&1 | tail -3

# [auto 2026-08-10 00:27] utilisée 3x — sig: rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md
rtk wc -l /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md

# [auto 2026-08-10 06:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "OK" || echo "SKIP"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "OK" || echo "SKIP"

# [auto 2026-08-10 18:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' for p in <SYM> <SY
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
for p in PF_LINKUSD PF_DOTUSD PF_SOLUSD PF_ADAUSD PF_XBTUSD PF_ETHUSD; do
  curl -s http://localhost:8081/api/grid/status/\$p 2>/dev/null
  echo '==='
done
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
" 2>&1

# [auto 2026-08-11 06:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "BRIEFING_OK" || echo "BRIEFING_SKIP"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "BRIEFING_OK" || echo "BRIEFING_SKIP"

# [auto 2026-08-14 21:08] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>&<N> | tail -<N>
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>&1 | tail -5

# [auto 2026-08-14 21:54] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/bot/balance | python3 -c 'import json,sys;d=json.load(sys.stdin)[\"accounts\"][\"flex\"];print(json.dumps({\"portfolioValue\":d[\"portfolioValue\"],\"balanceValue\":d[\"balanceValue\"],\"pnl\":d[\"pnl\"]}))' echo '|||' curl -s http://localhost:<N>/api/bot/positions ec
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=8 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/balance | python3 -c 'import json,sys;d=json.load(sys.stdin)[\"accounts\"][\"flex\"];print(json.dumps({\"portfolioValue\":d[\"portfolioValue\"],\"balanceValue\":d[\"balanceValue\"],\"pnl\":d[\"pnl\"]}))'
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))'
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD' | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d[\"price\"],d[\"emaStatus\"])'
echo '|||'
tail -6 ~/martin/scripts/critical-check.log
"

# [auto 2026-08-14 21:54] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-<N>: check stable, rien de neuf" -q && rtk git push -q && echo pushed
cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-276: check stable, rien de neuf" -q && rtk git push -q && echo pushed

# [auto 2026-08-15 02:34] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-<N>: check stable plateau, rien de neuf" -q && rtk git push -q && echo pushed
cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-304: check stable plateau, rien de neuf" -q && rtk git push -q && echo pushed

# [auto 2026-08-15 04:24] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-<N>: check stable, drift lent, rien de critique" -q && rtk git push -q && echo pushed
cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-302: check stable, drift lent, rien de critique" -q && rtk git push -q && echo pushed

# [auto 2026-08-15 06:26] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | tail -20

# [auto 2026-08-15 11:54] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-<N>: check stable, rien de critique" -q && rtk git push -q && echo pushed
cd ~/projets/tonyderide/niam-bay && rtk git add docs/recent.nb1 && rtk git commit -m "cycle-319: check stable, rien de critique" -q && rtk git push -q && echo pushed

# [auto 2026-08-15 18:28] utilisée 3x — sig: rtk git push <N>>&<N> | tail -<N>
rtk git push 2>&1 | tail -3

# [auto 2026-08-15 19:33] utilisée 3x — sig: ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> 'bash -s' <<'REMOTE_EOF' set -a source ~/martin/.env set +a python3 <<'PYEOF' import os, time, hashlib, hmac, base6<N>, urllib.request, json api_key = os.environ["KRAKEN_API_KEY"] api_secret = os.environ["KRAKEN_API_SECRET"] def sign(sign_path, nonce, post_data): message = post_data + nonce + sign_path sha
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=8 ubuntu@141.253.108.141 'bash -s' <<'REMOTE_EOF'
set -a
source ~/martin/.env
set +a
python3 <<'PYEOF'
import os, time, hashlib, hmac, base64, urllib.request, json

api_key = os.environ["KRAKEN_API_KEY"]
api_secret = os.environ["KRAKEN_API_SECRET"]

def sign(sign_path, nonce, post_data):
    message = post_data + nonce + sign_path
    sha256_hash = hashlib.sha256(message.encode()).digest()
    secret_decoded = base64.b64decode(api_secret)
    hmac_digest = hmac.new(secret_decoded, sha256_hash, hashlib.sha512).digest()
    return base64.b64encode(hmac_digest).decode()

nonce = str(int(time.time()*1000)*5_000_000 + 1)
sign_path = "/api/v3/fills"
url = "https://futures.kraken.com/derivatives" + sign_path
post_data = ""

headers = {
    "APIKey": api_key,
    "Nonce": nonce,
    "Authent": sign(sign_path, nonce, post_data),
}
req = urllib.request.Request(url, headers=headers, method="GET")
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = json.loads(r.read().decode())
        fills = body.get("fills", [])
        btc_fills = [f for f in fills if "XBT" in f.get("symbol","")]
        for f in sorted(btc_fills, key=lambda x: x.get("fillTime",""))[-10:]:
            print(f.get("fillTime"), f.get("symbol"), f.get("side"), f.get("size"), f.get("price"), f.get("fillType"), f.get("orderId"))
        if not btc_fills:
            print("no XBT fills found, total fills:", len(fills))
except Exception as e:
    print("ERROR:", e)
    try:
        print(e.read().decode())
    except Exception:
        pass
PYEOF
REMOTE_EOF

# [auto 2026-08-16 06:24] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md <N>>/dev/null && echo "EXISTS" || echo "MISSING"
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md 2>/dev/null && echo "EXISTS" || echo "MISSING"

# [auto 2026-08-16 17:04] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/bot/positions | python3 -m json.tool echo '=== orders ===' curl -s http://localhost:<N>/api/bot/orders | python3 -c \" import json,sys orders = json.load(sys.stdin) for o in orders: print(o['symbol'], o['side'], o['orderType'], o.get('stopPrice'), o.get('limitPrice'),
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=8 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/positions | python3 -m json.tool
echo '=== orders ==='
curl -s http://localhost:8081/api/bot/orders | python3 -c \"
import json,sys
orders = json.load(sys.stdin)
for o in orders:
    print(o['symbol'], o['side'], o['orderType'], o.get('stopPrice'), o.get('limitPrice'), o.get('reduceOnly'))
\"
"

# [auto 2026-08-16 18:27] utilisée 3x — sig: rtk git push origin master <N>>&<N>
rtk git push origin master 2>&1

# [auto 2026-08-16 18:34] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/recent.nb1 --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/recent.nb1 --tail-lines 30

# [auto 2026-08-16 19:04] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))' echo '|||' curl -s 'http://localhost:<N>/api/signal/ema_trend?instrument=
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
echo '|||'
tail -6 ~/martin/scripts/critical-check.log 2>/dev/null
"

# [auto 2026-08-16 19:14] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: monitoring stable" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-544: monitoring stable" && rtk git push -q && echo DONE

# [auto 2026-08-16 20:24] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions | python3 -c \"import json,sys; d=json.load(sys.stdin); [print(p['symbol'], p['side'], p['size'], p['price'], round(p['unrealizedPnl'],<N>)) for p in d]\" echo '|||' curl -s http://localhost:<N>/api
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions | python3 -c \"import json,sys; d=json.load(sys.stdin); [print(p['symbol'], p['side'], p['size'], p['price'], round(p['unrealizedPnl'],4)) for p in d]\"
echo '|||'
curl -s http://localhost:8081/api/bot/orders | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
echo '|||'
tail -6 ~/martin/scripts/critical-check.log 2>/dev/null
"

# [auto 2026-08-16 23:34] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: monitoring stable, PV en amélioration" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-564: monitoring stable, PV en amélioration" && rtk git push -q && echo DONE

# [auto 2026-08-17 00:34] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: monitoring stable, PV continue de monter" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-569: monitoring stable, PV continue de monter" && rtk git push -q && echo DONE

# [auto 2026-08-17 10:44] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: monitoring stable, amelioration continue" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-637: monitoring stable, amelioration continue" && rtk git push -q && echo DONE

# [auto 2026-08-17 12:24] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | sort | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/fragments/ | sort | tail -15

# [auto 2026-08-17 13:24] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: meme zone, pas de nouvelle escalade" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-653: meme zone, pas de nouvelle escalade" && rtk git push -q && echo DONE

# [auto 2026-08-17 14:14] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: meme zone stable" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-657: meme zone stable" && rtk git push -q && echo DONE

# [auto 2026-08-17 21:34] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: toujours sans SL BTC, quasi stable" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-701: toujours sans SL BTC, quasi stable" && rtk git push -q && echo DONE

# [auto 2026-08-17 21:54] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: leger recul BTC, toujours sans SL" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-699: leger recul BTC, toujours sans SL" && rtk git push -q && echo DONE

# [auto 2026-08-18 00:34] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-<N>: leger mieux BTC, toujours sans SL" && rtk git push -q && echo DONE
rtk git add docs/recent.nb1 && rtk git commit -q -m "cycle-716: leger mieux BTC, toujours sans SL" && rtk git push -q && echo DONE

# [auto 2026-08-18 02:04] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s 'http://localhost:<N>/api/signal/ema_trend?instrument=<SYM>'"
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'"

# [auto 2026-08-19 00:27] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git push origin master <N>>&<N> | tail -<N>
cd ~/projets/tonyderide/niam-bay && rtk git push origin master 2>&1 | tail -5

# [auto 2026-08-19 15:17] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> "curl -s http://localhost:<N>/api/bot/orders"
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "curl -s http://localhost:8081/api/bot/orders"

# [auto 2026-08-19 18:31] utilisée 3x — sig: rtk ls ~/.claude/projects/-home-tony-projets-tonyderide-niam-bay/*.jsonl <N>>/dev/null | tail -<N>
rtk ls ~/.claude/projects/-home-tony-projets-tonyderide-niam-bay/*.jsonl 2>/dev/null | tail -3

# [auto 2026-08-21 00:27] utilisée 3x — sig: rtk git push origin master
rtk git push origin master

# [auto 2026-08-22 12:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "DONE" || echo "SKIP"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "DONE" || echo "SKIP"

# [auto 2026-08-22 18:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>/dev/null && echo "briefing_ok" || echo "briefing_skip"
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>/dev/null && echo "briefing_ok" || echo "briefing_skip"

# [auto 2026-08-23 00:17] utilisée 3x — sig: rtk git add docs/recent.nb1 && rtk git commit -m "cycle-<N>: HOLD silencieux, stable" -q && rtk git push -q && echo OK
rtk git add docs/recent.nb1 && rtk git commit -m "cycle-971: HOLD silencieux, stable" -q && rtk git push -q && echo OK

# [auto 2026-08-23 00:46] utilisée 3x — sig: F=$(ls -t ~/.local/share/rtk/tee/*.log | head -<N>); grep -o '"portfolioValue":[<N>-<N>.]*' "$F"; grep -o '"order_id"' "$F" | wc -l
F=$(ls -t ~/.local/share/rtk/tee/*.log | head -1); grep -o '"portfolioValue":[0-9.]*' "$F"; grep -o '"order_id"' "$F" | wc -l

# [auto 2026-08-23 12:24] utilisée 3x — sig: rtk wc -l ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk wc -l ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md && rtk read ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 200

# [auto 2026-08-24 12:27] utilisée 3x — sig: rtk git push
rtk git push

# [auto 2026-08-24 13:46] utilisée 3x — sig: F=$(ls -t ~/.local/share/rtk/tee/*.log | head -<N>); grep -o '"portfolioValue":[<N>-<N>.]*' "$F"; grep -o '"order_id"' "$F" | wc -l; grep -o '"stopPrice":[<N>-<N>.]*' "$F"
F=$(ls -t ~/.local/share/rtk/tee/*.log | head -1); grep -o '"portfolioValue":[0-9.]*' "$F"; grep -o '"order_id"' "$F" | wc -l; grep -o '"stopPrice":[0-9.]*' "$F"

# [auto 2026-08-24 16:16] utilisée 3x — sig: F=$(ls -t ~/.local/share/rtk/tee/*.log | head -<N>); grep -o '"portfolioValue":[<N>-<N>.]*' "$F"
F=$(ls -t ~/.local/share/rtk/tee/*.log | head -1); grep -o '"portfolioValue":[0-9.]*' "$F"

# [auto 2026-10-15 02:17] utilisée 3x — sig: rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "tail -<N> ~/martin/nb_coup.log; curl -s localhost:<N>/api/bot/positions"
rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "tail -1 ~/martin/nb_coup.log; curl -s localhost:8081/api/bot/positions"

# [auto 2026-10-15 05:07] utilisée 3x — sig: rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions; echo; curl -s localhost:<N>/api/bot/orders | grep -oE '\"(stopPrice|limitPrice)\":[<N>-<N>.]+' | tr '\n' ' '"
rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions; echo; curl -s localhost:8081/api/bot/orders | grep -oE '\"(stopPrice|limitPrice)\":[0-9.]+' | tr '\n' ' '"

# [auto 2026-10-15 06:27] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/projets/vacation-autonomy.md --tail-lines 80

# [auto 2026-10-15 06:28] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && rtk git push <N>>&<N> | tail -<N>
cd ~/projets/tonyderide/niam-bay && rtk git push 2>&1 | tail -3

# [auto 2026-10-15 06:57] utilisée 3x — sig: rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions; echo; curl -s localhost:<N>/api/bot/orders | grep -oE '\"(stopPrice|limitPrice)\":[<N>-<N>.]+' | tr '\n' ' '"; date '+%H:%M'
rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions; echo; curl -s localhost:8081/api/bot/orders | grep -oE '\"(stopPrice|limitPrice)\":[0-9.]+' | tr '\n' ' '"; date '+%H:%M'

# [auto 2026-10-15 12:23] utilisée 3x — sig: sed -n '<N>,240p' ~/projets/tonyderide/niam-bay/docs/memory.nb1
sed -n '1,240p' ~/projets/tonyderide/niam-bay/docs/memory.nb1

# [auto 2026-10-15 12:23] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines 150

# [auto 2026-10-15 12:26] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> "python3 -c \" import base6<N>, hashlib, hmac, time, json from urllib.request import Request, urlopen from urllib.parse import urlencode env = {} with open('/home/ubuntu/martin/.env') as f: for line in f: if '=' in line and not line.strip().startswith('#'): k, v = line.strip().split('=', <N>) env[k] = v.strip('\\\"').strip(
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "python3 -c \"
import base64, hashlib, hmac, time, json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

env = {}
with open('/home/ubuntu/martin/.env') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v.strip('\\\"').strip(chr(39))

KEY, SEC = env['KRAKEN_API_KEY'], env['KRAKEN_API_SECRET']
HOST = 'https://futures.kraken.com'

n = int(time.time()*1000)*5_000_000+1
params = {'lastTime': '2026-09-16T00:00:00.000Z', 'count': 100}
qs = urlencode(params)
sig_path = '/api/history/v3/account-log'
msg = (qs + str(n) + sig_path).encode()
h = hashlib.sha256(msg).digest()
sig = base64.b64encode(hmac.new(base64.b64decode(SEC), h, hashlib.sha512).digest()).decode()
url = HOST + '/api/history/v3/account-log?' + qs
req = Request(url, headers={'APIKey': KEY, 'Nonce': str(n), 'Authent': sig, 'User-Agent': 'nb-forensic/1.0'})
try:
    r = json.loads(urlopen(req, timeout=15).read())
    for e in r.get('logs', []):
        if '2026-09-15' in e.get('date', '') or '2026-09-14' in e.get('date', ''):
            info = e.get('info','')
            if 'funding' not in info.lower() and 'liquidation' in info.lower() or 'stop' in info.lower() or 'realized' in info.lower() or 'position' in info.lower():
                print(e.get('date'), '|', info[:120], '| contract=', e.get('contract',''))
except Exception as ex:
    print('ERR:', ex)
\"" 2>&1 | head -50

# [auto 2026-10-15 18:24] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> " curl -s http://localhost:<N>/api/system/status echo '|||' curl -s http://localhost:<N>/api/bot/balance echo '|||' curl -s http://localhost:<N>/api/bot/positions echo '|||' curl -s http://localhost:<N>/api/bot/orders echo '|||' curl -s http://localhost:<N>/api/grid/active echo '|||' curl -s 'http://lo
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@141.253.108.141 "
curl -s http://localhost:8081/api/system/status
echo '|||'
curl -s http://localhost:8081/api/bot/balance
echo '|||'
curl -s http://localhost:8081/api/bot/positions
echo '|||'
curl -s http://localhost:8081/api/bot/orders
echo '|||'
curl -s http://localhost:8081/api/grid/active
echo '|||'
curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'
" 2>&1

# [auto 2026-10-15 23:57] utilisée 3x — sig: rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions; echo; tail -<N> ~/et/et.log" | head -c <N>
rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions; echo; tail -1 ~/et/et.log" | head -c 300

# [auto 2026-10-16 05:39] utilisée 3x — sig: rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions" | head -c <N>
rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions" | head -c 110

# [auto 2026-10-16 07:24] utilisée 3x — sig: date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions; echo; tail -<N> ~/et/et.log" | head -c <N>
date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions; echo; tail -1 ~/et/et.log" | head -c 300

# [auto 2026-10-16 12:23] utilisée 3x — sig: rtk ls ~/projets/tonyderide/niam-bay/memory/ <N>>&<N> | head -<N>
rtk ls ~/projets/tonyderide/niam-bay/memory/ 2>&1 | head -30

# [auto 2026-10-16 12:44] utilisée 3x — sig: date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "curl -s localhost:<N>/api/bot/positions; echo; tail -<N> ~/et/et.log" | head -c <N>; echo; gh repo view tonyderide/exchange-truth --json stargazerCount -q .stargazerCount; for pr in "botcrypto-io/awesome-crypto-trading-bots <N>" "punkpeye/awesome-mcp-servers <N>"; do set -- $pr; gh pr view $<N> -R $<N> --json state,comments -q '"
date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s localhost:8081/api/bot/positions; echo; tail -1 ~/et/et.log" | head -c 300; echo; gh repo view tonyderide/exchange-truth --json stargazerCount -q .stargazerCount; for pr in "botcrypto-io/awesome-crypto-trading-bots 171" "punkpeye/awesome-mcp-servers 16591"; do set -- $pr; gh pr view $2 -R $1 --json state,comments -q '"\(.state) c=\(.comments|length)"'; done

# [auto 2026-10-16 16:05] utilisée 3x — sig: tar czf /tmp/claude-<N>/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/et.tgz -C ~/projets/tonyderide exchange-truth/exchange_truth && scp -q -i ~/.ssh/martin_vm.key /tmp/claude-<N>/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/et.tgz ubuntu@<N>.<N>:/tmp/et.tgz && rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "tar xzf /tmp/et.tgz -C ~/et && ~/et/run.sh; tail -<N> ~/
tar czf /tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/et.tgz -C ~/projets/tonyderide exchange-truth/exchange_truth && scp -q -i ~/.ssh/martin_vm.key /tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/et.tgz ubuntu@141.253.108.141:/tmp/et.tgz && rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "tar xzf /tmp/et.tgz -C ~/et && ~/et/run.sh; tail -1 ~/et/et.log"

# [auto 2026-10-16 18:24] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/lectures/<N>-<N>-<N>-exploration.md --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/lectures/2026-10-16-exploration.md --tail-lines 20

# [auto 2026-10-16 19:44] utilisée 3x — sig: date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "tail -<N> ~/et/et.log" | head -c <N>
date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "tail -2 ~/et/et.log" | head -c 300

# [auto 2026-10-16 21:34] utilisée 3x — sig: date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "tail -<N> ~/et/et.log" | head -c <N>; echo; rtk curl -s -m <N> 'https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&max_results=<N>' | grep -E '<title>|<summary>' | sed 's/<[^>]*>//g' | tail -<N> | head -c <N>
date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "tail -2 ~/et/et.log" | head -c 300; echo; rtk curl -s -m 30 'https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&max_results=1' | grep -E '<title>|<summary>' | sed 's/<[^>]*>//g' | tail -2 | head -c 800

# [auto 2026-10-16 21:44] utilisée 3x — sig: date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "tail -<N> ~/et/et.log" | head -c <N>; echo; gh repo view tonyderide/exchange-truth --json stargazerCount -q .stargazerCount; for pr in "botcrypto-io/awesome-crypto-trading-bots <N>" "punkpeye/awesome-mcp-servers <N>"; do set -- $pr; gh pr view $<N> -R $<N> --json state,comments -q '"\(.state) c=\(.comments|length)"'; done
date '+%H:%M'; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "tail -2 ~/et/et.log" | head -c 300; echo; gh repo view tonyderide/exchange-truth --json stargazerCount -q .stargazerCount; for pr in "botcrypto-io/awesome-crypto-trading-bots 171" "punkpeye/awesome-mcp-servers 16591"; do set -- $pr; gh pr view $2 -R $1 --json state,comments -q '"\(.state) c=\(.comments|length)"'; done

# [auto 2026-10-17 00:25] utilisée 3x — sig: rtk ls ~/projets/tonyderide/niam-bay/docs/lectures/ <N>>/dev/null | tail -<N>
rtk ls ~/projets/tonyderide/niam-bay/docs/lectures/ 2>/dev/null | tail -5

# [auto 2026-10-17 00:25] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 8

# [auto 2026-10-18 23:06] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && scripts/nb | sed -n '<N>,2p;4p;7p'; rtk read docs/inbox.jsonl --tail-lines <N> | grep '"tony"' | tail -<N> | cut -c1-<N>
cd ~/projets/tonyderide/niam-bay && scripts/nb | sed -n '1,2p;4p;7p'; rtk read docs/inbox.jsonl --tail-lines 3 | grep '"tony"' | tail -1 | cut -c1-200

# [auto 2026-10-19 03:34] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && scripts/nb | sed -n '<N>,2p;4p;7p'; rtk read docs/inbox.jsonl --tail-lines <N> | grep tony | tail -<N> | cut -c1-<N>
cd ~/projets/tonyderide/niam-bay && scripts/nb | sed -n '1,2p;4p;7p'; rtk read docs/inbox.jsonl --tail-lines 3 | grep tony | tail -1 | cut -c1-200

# [auto 2026-10-21 03:40] utilisée 3x — sig: date; rtk read /home/tony/projets/tonyderide/niam-bay/chez-moi/maths/golomb14par.log --tail-lines <N>
date; rtk read /home/tony/projets/tonyderide/niam-bay/chez-moi/maths/golomb14par.log --tail-lines 3

# [auto 2026-10-21 06:23] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines 150

# [auto 2026-10-21 12:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -40

# [auto 2026-10-21 18:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>&<N> | tail -<N>
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>&1 | tail -5

# [auto 2026-10-22 02:08] utilisée 3x — sig: date +%H:%M; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/banc-honnete/t2<N>.log
date +%H:%M; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/banc-honnete/t21.log

# [auto 2026-10-22 06:23] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N> <N>>&<N>
rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 30 2>&1

# [auto 2026-10-22 06:24] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N>
rtk read ~/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 3

# [auto 2026-10-22 12:23] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/recent.nb1
rtk read ~/projets/tonyderide/niam-bay/docs/recent.nb1

# [auto 2026-10-22 12:23] utilisée 3x — sig: sed -n '<N>,240p' ~/projets/tonyderide/niam-bay/docs/memory.nb1
sed -n '1,240p' ~/projets/tonyderide/niam-bay/docs/memory.nb1

# [auto 2026-10-23 05:06] utilisée 3x — sig: date; rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=<N> ubuntu@<N>.<N> 'cat ~/nb/tg_offset; echo; wc -l < ~/nb/inbox.jsonl; pgrep -f "python3.*nb_vm_bot"'
date; rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@141.253.108.141 'cat ~/nb/tg_offset; echo; wc -l < ~/nb/inbox.jsonl; pgrep -f "python3.*nb_vm_bot"'

# [auto 2026-10-23 06:23] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/inbox.jsonl --tail-lines <N> <N>>/dev/null
rtk read /home/tony/projets/tonyderide/niam-bay/docs/inbox.jsonl --tail-lines 20 2>/dev/null

# [auto 2026-10-23 06:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@<N>.<N> "python3 ~/nb/fil.py derniers <N>" < /dev/null <N>>&<N> | tail -<N>
rtk ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "python3 ~/nb/fil.py derniers 30" < /dev/null 2>&1 | tail -40

# [auto 2026-10-23 06:24] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 3

# [auto 2026-10-23 12:24] utilisée 3x — sig: rtk ls ~/projets/tonyderide/niam-bay/docs/lectures/ <N>>&<N> | tail -<N>
rtk ls ~/projets/tonyderide/niam-bay/docs/lectures/ 2>&1 | tail -5

# [auto 2026-10-24 06:23] utilisée 3x — sig: date && python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
date && python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -40

# [auto 2026-10-24 12:23] utilisée 3x — sig: rtk ssh -o ConnectTimeout=<N> -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> "python3 ~/nb/fil.py derniers <N>" < /dev/null <N>>&<N> | tail -<N>
rtk ssh -o ConnectTimeout=10 -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "python3 ~/nb/fil.py derniers 30" < /dev/null 2>&1 | tail -40

# [auto 2026-10-24 18:23] utilisée 3x — sig: rtk read ~/projets/tonyderide/niam-bay/docs/loop-backlog.md <N>>/dev/null | head -<N>
rtk read ~/projets/tonyderide/niam-bay/docs/loop-backlog.md 2>/dev/null | head -80

# [auto 2026-10-25 06:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=<N> ubuntu@<N>.<N> "python3 ~/nb/fil.py derniers <N>" < /dev/null <N>>&<N> | tail -<N>
rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=10 ubuntu@141.253.108.141 "python3 ~/nb/fil.py derniers 30" < /dev/null 2>&1 | tail -40

# [auto 2026-10-25 06:23] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N> <N>>/dev/null
rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 30 2>/dev/null

# [auto 2026-10-25 12:23] utilisée 3x — sig: cd ~/projets/tonyderide/niam-bay && python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
cd ~/projets/tonyderide/niam-bay && python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -30

# [auto 2026-10-25 18:23] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/memory/ <N>>&<N> | head -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/memory/ 2>&1 | head -20

# [auto 2026-10-26 00:24] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N> <N>>&<N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 30 2>&1

# [auto 2026-10-26 12:23] utilisée 3x — sig: date && python3 /home/tony/projets/tonyderide/niam-bay/ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
date && python3 /home/tony/projets/tonyderide/niam-bay/ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -40

# [auto 2026-10-26 18:23] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/lectures/ <N>>/dev/null | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/lectures/ 2>/dev/null | tail -5

# [auto 2026-10-26 18:23] utilisée 3x — sig: gh repo view tonyderide/exchange-truth --json stargazerCount,forkCount,watchers <N>>&<N>
gh repo view tonyderide/exchange-truth --json stargazerCount,forkCount,watchers 2>&1

# [auto 2026-10-27 00:23] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/memory.nb1 --tail-lines 120

# [auto 2026-10-27 06:24] utilisée 3x — sig: rtk ls /home/tony/projets/tonyderide/niam-bay/docs/lectures/ <N>>&<N> | tail -<N>
rtk ls /home/tony/projets/tonyderide/niam-bay/docs/lectures/ 2>&1 | tail -10

# [auto 2026-10-27 18:23] utilisée 3x — sig: python3 /home/tony/projets/tonyderide/niam-bay/ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 /home/tony/projets/tonyderide/niam-bay/ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -30

# [auto 2026-10-28 18:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=<N> ubuntu@<N>.<N> "python3 ~/nb/fil.py derniers <N>" < /dev/null <N>>&<N> | tail -<N>
rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=10 ubuntu@141.253.108.141 "python3 ~/nb/fil.py derniers 30" < /dev/null 2>&1 | tail -40

# [auto 2026-10-29 12:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -40

# [auto 2026-10-29 12:23] utilisée 3x — sig: ~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py <N>>&<N> | tail -<N>
~/projets/tonyderide/niam-bay/.venv/bin/python ~/projets/tonyderide/niam-bay/memory/wake_briefing.py 2>&1 | tail -5

# [auto 2026-10-31 03:18] utilisée 3x — sig: bash ~/projets/experiments/nb-weekend/tools/veille.sh
bash ~/projets/experiments/nb-weekend/tools/veille.sh

# [auto 2026-10-31 12:23] utilisée 3x — sig: rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=<N> ubuntu@<N>.<N> "python3 ~/nb/fil.py derniers <N>" < /dev/null <N>>&<N> | tail -<N>
rtk ssh -i ~/.ssh/martin_vm.key -o ConnectTimeout=10 ubuntu@141.253.108.141 "python3 ~/nb/fil.py derniers 30" < /dev/null 2>&1 | tail -40

# [auto 2026-10-31 14:54] utilisée 3x — sig: bash ~/projets/experiments/nb-weekend/tools/veille.sh
bash ~/projets/experiments/nb-weekend/tools/veille.sh

# [auto 2026-10-31 15:00] utilisée 3x — sig: until grep -q "début" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep <N>; done; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines <N>
until grep -q "début" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep 15; done; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines 4

# [auto 2026-10-31 15:11] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines 5

# [auto 2026-10-31 15:11] utilisée 3x — sig: until grep -q "financement ok" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep <N>; done; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines <N>
until grep -q "financement ok" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep 30; done; rtk read /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log --tail-lines 3

# [auto 2026-10-31 15:51] utilisée 3x — sig: until grep -q "financement ok" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep <N>; done; echo fini
until grep -q "financement ok" /home/tony/projets/tonyderide/niam-bay/ai-lab/carry-financement/data_hl/collecte.log; do sleep 60; done; echo fini

# [auto 2026-11-02 12:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -20

# [auto 2026-11-05 12:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -30

# [auto 2026-11-06 01:23] utilisée 3x — sig: cd /tmp/claude-<N>/-home-tony-projets-tonyderide-martin/4e81611e-b9db-<N>-98b5-7975f809d2e0/scratchpad/mt && /home/tony/projets/tonyderide/journal-fidele/.venv/bin/python - <<'EOF' import json, collections, datetime as dt L={} for l in open("exec.jsonl"): x=json.loads(l)["event"]["execution"]["execution"]; L[x["uid"]]=x X=sorted(L.values(), key=lambda x:x["timestamp"]) lots=collections.defaultdict
cd /tmp/claude-1000/-home-tony-projets-tonyderide-martin/4e81611e-b9db-4354-98b5-7975f809d2e0/scratchpad/mt && /home/tony/projets/tonyderide/journal-fidele/.venv/bin/python - <<'EOF'
import json, collections, datetime as dt
L={}
for l in open("exec.jsonl"):
    x=json.loads(l)["event"]["execution"]["execution"]; L[x["uid"]]=x
X=sorted(L.values(), key=lambda x:x["timestamp"])
lots=collections.defaultdict(collections.deque); day=collections.defaultdict(lambda:[0.0,0.0]); rk=collections.defaultdict(float)
for x in X:
    d=dt.datetime.fromtimestamp(x["timestamp"]/1000,dt.timezone.utc).strftime("%Y-%m-%d")
    if d>="2026-07": break
    k=x["order"]["tradeable"]; sg=1 if x["order"]["direction"]=="Buy" else -1; q=float(x["quantity"]); p=float(x["price"]); f=float(x["orderData"].get("fee") or 0)
    r=0.0; D=lots[k]
    while q>1e-12 and D and D[0][0]*sg<0:
        lq,lp=D[0]; m=min(q,abs(lq)); r+=m*(p-lp)*(-sg); q-=m
        if abs(lq)-m<1e-12: D.popleft()
        else: D[0]=(lq+sg*m,lp)
    if q>1e-12: D.append((sg*q,p))
    day[d][0]+=r; day[d][1]+=f
    if x["orderData"].get("realizedPnl") not in (None,""): rk[d[:7]]+=float(x["orderData"]["realizedPnl"])
g=n=0; M=collections.defaultdict(lambda:[0.0,0.0])
print("avril, cumul depuis le 1er : sans frais | avec frais")
for d in sorted(day):
    M[d[:7]][0]+=day[d][0]; M[d[:7]][1]+=day[d][1]
    if d.startswith("2026-04"):
        g+=day[d][0]; n+=day[d][0]-day[d][1]
        if d[-2:] in ("05","10","15","20","25","30"): print(f"  {d}  {g:+7.2f} $ | {n:+7.2f} $")
print("par mois : gain réalisé sans frais | frais | net")
for m in sorted(M): print(f"  {m}  {M[m][0]:+7.2f} | {M[m][1]:6.2f} | {M[m][0]-M[m][1]:+7.2f}   (champ realizedPnl Kraken: {rk.get(m,0):+.2f})")
EOF

# [auto 2026-11-07 12:23] utilisée 3x — sig: rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines <N>
rtk read /home/tony/projets/tonyderide/niam-bay/docs/loop-journal.md --tail-lines 40

# [auto 2026-11-08 00:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -30

# [auto 2026-11-09 00:23] utilisée 3x — sig: python3 ai-lab/memoire-falsifiable/verify.py <N>>&<N> | tail -<N>
python3 ai-lab/memoire-falsifiable/verify.py 2>&1 | tail -20

# [auto 2026-11-09 03:04] utilisée 3x — sig: /home/tony/projets/tonyderide/journal-fidele/.venv/bin/python t7<N>.py /tmp/claude-<N>/-home-tony-projets-tonyderide-martin/4e81611e-b9db-<N>-98b5-7975f809d2e0/scratchpad/m1 > t7<N>.log <N>>&<N>; tail -<N> t7<N>.log
/home/tony/projets/tonyderide/journal-fidele/.venv/bin/python t71.py /tmp/claude-1000/-home-tony-projets-tonyderide-martin/4e81611e-b9db-4354-98b5-7975f809d2e0/scratchpad/m1 > t71.log 2>&1; tail -6 t71.log

# [auto 2026-11-10 06:37] utilisée 3x — sig: date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> 'python3 -c " import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))" tail -<N> ~/martin/garde/journal.jsonl | cut -c1-<N> curl -s -m <N> http://localhost:<N>/api/bot/positions; echo curl -s -m <N> http://localhost:<N>/api/bot/o
date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 'python3 -c "
import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))"
tail -3 ~/martin/garde/journal.jsonl | cut -c1-160
curl -s -m 10 http://localhost:8081/api/bot/positions; echo
curl -s -m 10 http://localhost:8081/api/bot/orders | python3 -c "
import json,sys
d=json.load(sys.stdin);o=d.get(\"orders\",d) if isinstance(d,dict) else d
print([(x[\"symbol\"][3:-3],x[\"side\"][0],x[\"orderType\"],x.get(\"limitPrice\") or x.get(\"stopPrice\")) for x in o if x[\"orderType\"]!=\"lmt\" or x.get(\"reduceOnly\")])
print(len(o),\"ordres\")"'

# [auto 2026-11-10 09:43] utilisée 3x — sig: date; cd ~/projets/tonyderide/niam-bay/ai-lab/banc-honnete && for d in papier-inversion papier-reversion papier-cotations papier-max; do echo "== $d: $(tail -<N> $d/journal.md | cut -c1-<N>)"; done; echo "-- <N>: $(tail -<N> ~/.local/state/nb/papier-<N>.log)"; git -C ../.. log --oneline -<N> | cut -c1-<N>; grep -c "| À FAIRE" FILE-HYPOTHESES.md; python3 -c " import json,re,collections;V=json.load(
date; cd ~/projets/tonyderide/niam-bay/ai-lab/banc-honnete && for d in papier-inversion papier-reversion papier-cotations papier-max; do echo "== $d: $(tail -1 $d/journal.md | cut -c1-160)"; done; echo "-- 50: $(tail -1 ~/.local/state/nb/papier-50.log)"; git -C ../.. log --oneline -4 | cut -c1-80; grep -c "| À FAIRE" FILE-HYPOTHESES.md; python3 -c "
import json,re,collections;V=json.load(open('../../docs/registre-verdicts.json'));m=[x for x in V if re.search(r'PREREG-(3[5-9]|4\d|5\d|60)-',x['fichier'])];print(len(m),collections.Counter(x['verdict'] for x in m))"

# [auto 2026-11-10 21:37] utilisée 3x — sig: date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> 'python3 -c " import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))" tail -<N> ~/martin/garde/journal.jsonl | cut -c1-<N> curl -s -m <N> http://localhost:<N>/api/bot/positions; echo curl -s -m <N> http://localhost:<N>/api/grid/
date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 'python3 -c "
import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))"
tail -2 ~/martin/garde/journal.jsonl | cut -c1-200
curl -s -m 10 http://localhost:8081/api/bot/positions; echo
curl -s -m 10 http://localhost:8081/api/grid/active; echo
curl -s -m 10 http://localhost:8081/api/bot/orders | python3 -c "
import json,sys
d=json.load(sys.stdin);o=d.get(\"orders\",d) if isinstance(d,dict) else d
print([(x[\"symbol\"][3:-3],x[\"side\"][0],x[\"orderType\"],x.get(\"limitPrice\") or x.get(\"stopPrice\")) for x in o if x[\"orderType\"]!=\"lmt\" or x.get(\"reduceOnly\")])
print(len(o),\"ordres\")"'

# [auto 2026-11-11 06:37] utilisée 3x — sig: date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@<N>.<N> 'python3 -c " import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))" tail -<N> ~/martin/garde/journal.jsonl | cut -c1-<N> curl -s -m <N> http://localhost:<N>/api/bot/positions; echo curl -s -m <N> http://localhost:<N>/api/grid/
date -u; rtk proxy ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 'python3 -c "
import json;s=json.load(open(\"/home/ubuntu/martin/garde/snapshot.json\"));print(s.get(\"t\") or s.get(\"maj\"),\"pv\",s[\"portefeuille\"],\"kill\",s.get(\"kill\"))"
tail -3 ~/martin/garde/journal.jsonl | cut -c1-200
curl -s -m 10 http://localhost:8081/api/bot/positions; echo
curl -s -m 10 http://localhost:8081/api/grid/active; echo
curl -s -m 10 http://localhost:8081/api/bot/orders | python3 -c "
import json,sys
d=json.load(sys.stdin);o=d.get(\"orders\",d) if isinstance(d,dict) else d
print([(x[\"symbol\"][3:-3],x[\"side\"][0],x[\"orderType\"],x.get(\"limitPrice\") or x.get(\"stopPrice\")) for x in o if x[\"orderType\"]!=\"lmt\" or x.get(\"reduceOnly\")])
print(len(o),\"ordres\")"'

# [auto 2026-11-12 06:38] utilisée 3x — sig: F=/home/tony/projets/tonyderide/niam-bay/ai-lab/cent-strategies/t7<N>.log; until grep -qE "VERDICT|Traceback" $F; do sleep <N>; done; rtk read $F --tail-lines <N> | cut -c1-<N>
F=/home/tony/projets/tonyderide/niam-bay/ai-lab/cent-strategies/t75.log; until grep -qE "VERDICT|Traceback" $F; do sleep 15; done; rtk read $F --tail-lines 4 | cut -c1-600

# [auto 2026-11-12 06:47] utilisée 3x — sig: F=/home/tony/projets/tonyderide/niam-bay/ai-lab/cent-strategies/t7<N>.log; for k in $(seq <N> <N>); do grep -qE "VERDICT|Traceback" $F && break; sleep <N>; done; tail -<N> $F | cut -c1-<N>
F=/home/tony/projets/tonyderide/niam-bay/ai-lab/cent-strategies/t75.log; for k in $(seq 1 38); do grep -qE "VERDICT|Traceback" $F && break; sleep 15; done; tail -1 $F | cut -c1-120

# [auto 2026-11-12 15:30] utilisée 3x — sig: date '+%H:%M'; rtk ssh -o ConnectTimeout=<N> nb-vm 'python3 - <<"EOF" import json, urllib.request, os g = lambda p: json.load(urllib.request.urlopen("http://localhost:<N>" + p, timeout=<N>)) pos = g("/api/bot/positions"); o = g("/api/bot/orders") stops = {x["symbol"] for x in o if x["orderType"] in ("stop", "stp")} nus = [p["symbol"] for p in pos if p["symbol"] not in stops] a = g("/api/bot/balanc
date '+%H:%M'; rtk ssh -o ConnectTimeout=15 nb-vm 'python3 - <<"EOF"
import json, urllib.request, os
g = lambda p: json.load(urllib.request.urlopen("http://localhost:8081" + p, timeout=20))
pos = g("/api/bot/positions"); o = g("/api/bot/orders")
stops = {x["symbol"] for x in o if x["orderType"] in ("stop", "stp")}
nus = [p["symbol"] for p in pos if p["symbol"] not in stops]
a = g("/api/bot/balance")["accounts"]["flex"]
print("positions", len(pos), "ordres", len(o), "sans stop", nus, "PV", round(a.get("portfolioValue", 0), 3))
s = json.load(open(os.path.expanduser("~/martin/garde/snapshot.json")))
print("snapshot", {k: s[k] for k in list(s)[:8]})
lines = open(os.path.expanduser("~/martin/garde/journal.jsonl")).read().splitlines()[-3:]
for l in lines: print(l[:200])
EOF'
