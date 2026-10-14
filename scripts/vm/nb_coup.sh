#!/bin/bash
# NB mandat capital — coup audace (2026-10-15). One-shot : s'arme via nb_coup.armed, se désarme après tir.
# Setup backtesté (scripts/backtest_coup1.py) : short DOT si BTC+DOT DOWNTREND, RSI DOT>45, prix touche EMA50 DOT.
# Taille : 30% du capital risqué au SL (2.3%) -> capital=2.7 lev=14 (~37.8$ notionnel). SL/TP posés par PositionService.
API=http://localhost:8081
DIR=/home/ubuntu/martin
LOG=$DIR/nb_coup.log
ARM=$DIR/nb_coup.armed
TG="https://api.telegram.org/bot7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454/sendMessage"
CHAT=6574420846
tg(){ curl -s -X POST "$TG" --data-urlencode "chat_id=$CHAT" --data-urlencode "disable_notification=true" --data-urlencode "text=$1" >/dev/null; }
ts=$(date -u +%FT%TZ)
[ -f "$ARM" ] || exit 0
pos=$(curl -s --max-time 5 "$API/api/bot/positions")
[ "$pos" != "[]" ] && { echo "$ts skip: position deja ouverte $pos" >> $LOG; exit 0; }
d=$(curl -s --max-time 5 "$API/api/signal/ema_trend?instrument=PF_DOTUSD")
b=$(curl -s --max-time 5 "$API/api/signal/ema_trend?instrument=PF_XBTUSD")
g(){ echo "$1" | grep -oE "\"$2\":\"?[A-Z0-9.]+" | head -1 | sed -E 's/.*:"?//'; }
dp=$(g "$d" price); de=$(g "$d" ema50); dr=$(g "$d" rsi); ds=$(g "$d" emaStatus); bs=$(g "$b" emaStatus)
ok=$(python3 -c "print(1 if '$ds'=='DOWNTREND' and '$bs'=='DOWNTREND' and float('$dr')>45 and float('$dp')>=float('$de')*0.999 else 0)" 2>/dev/null)
echo "$ts dot=$dp ema50=$de rsi=$dr dot=$ds btc=$bs fire=$ok" >> $LOG
[ "$ok" = "1" ] || exit 0
rm -f "$ARM"
r=$(curl -s --max-time 15 -X POST "$API/api/position/short?instrument=PF_DOTUSD&capital=2.7&leverage=14&slPct=2.3&tpPct=4.5&demo=false")
echo "$ts FIRE resp=$r" >> $LOG
sleep 8
o=$(curl -s --max-time 5 "$API/api/bot/orders"); p=$(curl -s --max-time 5 "$API/api/bot/positions")
sl=no; echo "$o" | grep -q '"orderType":"stop"' && sl=yes
echo "$ts post: pos=$p sl=$sl" >> $LOG
if [ "$sl" = yes ]; then
  tg "NB coup audace #1 parti : SHORT DOT ~37\$ notionnel (14x) @~$dp, SL +2.3% / TP -4.5% poses. pos=$p"
else
  tg "🚨 NB coup #1 : position ouverte SANS stop detecte ! pos=$p resp=$r"
fi
