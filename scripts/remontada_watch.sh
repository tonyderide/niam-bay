#!/usr/bin/env bash
# Autonomous remontada watcher — zero LLM tokens.
# Pulls BTC EMA signal, sends Telegram on each upside palier, sets GO flag on EMA200 reclaim.
set -u
BOT_PY=/home/tony/projets/tonyderide/niam-bay/scripts/martin_telegram_bot.py
STATE=/tmp/remontada_state
GOFLAG=/tmp/remontada_GO
KEY=~/.ssh/martin_vm.key
VM=ubuntu@141.253.108.141

TOKEN=$(python3 -c "import re;print(re.search(r'TELEGRAM_TOKEN\", \"([^\"]+)',open('$BOT_PY').read()).group(1))")
CHAT=$(python3 -c "import re;print(re.search(r'TELEGRAM_CHAT\",  \"([^\"]+)',open('$BOT_PY').read()).group(1))")

tg() { curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" -d chat_id="${CHAT}" --data-urlencode text="$1" >/dev/null; }

SIG=$(ssh -i "$KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$VM" "curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'" 2>/dev/null)
[ -z "$SIG" ] && { echo "$(date -u +%H:%M) no-signal"; exit 0; }

read PRICE EMA200 STATUS < <(python3 -c "
import json,sys
d=json.loads('''$SIG''')
print(d['price'], d['ema200'], d['emaStatus'])
" 2>/dev/null)
[ -z "${PRICE:-}" ] && { echo "$(date -u +%H:%M) parse-fail"; exit 0; }

LAST=$(cat "$STATE" 2>/dev/null || echo 0)
EMA_INT=$(python3 -c "print(int(float('$EMA200')))")

# Upside paliers (ema200 last so GO handled separately too)
for P in 64000 64500 65000 "$EMA_INT"; do
  awk_ok=$(python3 -c "print(1 if float('$PRICE')>=$P and $P>$LAST else 0)")
  if [ "$awk_ok" = "1" ]; then
    if [ "$P" = "$EMA_INT" ] || python3 -c "exit(0 if float('$PRICE')>=$EMA_INT else 1)"; then :; fi
    tg "📈 BTC franchit \$$P (prix \$$(python3 -c "print(f'{float(\"$PRICE\"):,.0f}')")) — DOWNTREND tant que < EMA200 \$$EMA_INT."
    echo "$P" > "$STATE"
    LAST=$P
  fi
done

# GO: reclaim EMA200
if [ "$STATUS" = "UPTREND" ] || python3 -c "exit(0 if float('$PRICE')>=float('$EMA200') else 1)"; then
  if [ ! -f "$GOFLAG" ]; then
    tg "🚀 GO REMONTADA : BTC a reclaim l'EMA200 (\$$(python3 -c "print(f'{float(\"$PRICE\"):,.0f}')")). Reclaim UPTREND — dis à Claude de convoquer le conseil pour le gros coup."
    echo "$PRICE" > "$GOFLAG"
  fi
fi

echo "$(date -u +%H:%M) BTC=$PRICE EMA200=$EMA_INT $STATUS last_palier=$LAST"
