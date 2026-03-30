#!/bin/bash
# === NIAM-BAY QUICK COMMANDS ===
# Copier-coller, pas réfléchir.

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

# --- FEED BRAIN ---
# cd C:/niam-bay && python cerveau-nb/feed.py --text "TEXTE ICI"

# --- FEED DICTIONARY ---
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python feed_dictionary.py --resume

# --- CURIOSITÉ AUTONOME (le cerveau explore internet seul) ---
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python curiosity.py --cycles 50 --topic "intelligence artificielle"
# cd C:/niam-bay/cerveau-nb && PYTHONIOENCODING=utf-8 python curiosity.py --forever

# --- IDENTITY CHECK ---
# python C:/Users/tony_/Documents/niam-bay/scripts/identity_check.py                            # Génère docs/identity-check-YYYYMMDD.md

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

# === RÈGLE ===
# TOUJOURS utiliser une skill quand elle s'applique.
# Pas de code sans /write-plan d'abord.
# Pas de "c'est fini" sans /verification-before-completion.
# Pas de feature sans /brainstorm d'abord.
# Bug ? → /systematic-debugging
# Multi-tâches ? → /subagent-driven-development
