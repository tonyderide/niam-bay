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
# cd C:/niambay-v2 && SAMBANOVA_API_KEY="4fad50d2-e867-47d1-be65-e4b03571128e" MISTRAL_API_KEY="uTu0O4NS4FsYeNLqgnq1CVOOhDZTUMY6" NIAMBAY_EMAIL_PWD="tonytony!01" PYTHONUNBUFFERED=1 nohup python -u run_selfcoder.py > selfcoder.log 2>&1 &

# --- LAUNCH TRADING MONITOR ---
# cd C:/niambay-v2 && PYTHONUNBUFFERED=1 nohup python -u trading_monitor.py > trading_monitor.log 2>&1 &

# --- RUN ALL TESTS ---
# cd C:/niambay-v2 && python -m pytest tests/ -q

# --- LLM TEST (SambaNova) ---
# python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen(urllib.request.Request('https://api.sambanova.ai/v1/chat/completions',data=json.dumps({'model':'DeepSeek-V3-0324','messages':[{'role':'user','content':'dis OK'}],'max_tokens':5}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer 4fad50d2-e867-47d1-be65-e4b03571128e'}),timeout=15).read())['choices'][0]['message']['content'])"

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
