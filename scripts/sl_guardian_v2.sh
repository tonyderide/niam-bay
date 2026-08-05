#!/bin/bash
# Gardien SL v2 — cycle 262, 2026-08-05
# Fix faux-positif v1 : vérification SL *par symbol* au lieu de grep global.
# v1 disait "SL OK" si n'importe quelle paire avait un stop, même si XBT était nue.
#
# Déployer sur VM : scp scripts/sl_guardian_v2.sh ubuntu@141.253.108.141:/home/ubuntu/martin/sl_guardian.sh
# (remplace l'existant — même nom, même cron)

API=http://localhost:8081
TG="https://api.telegram.org/bot7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454/sendMessage"
CHAT=6574420846
MAXLOSS=10

tg(){ curl -s -X POST "$TG" --data-urlencode "chat_id=$CHAT" --data-urlencode "text=$1" >/dev/null; }

pos=$(curl -s "$API/api/bot/positions")
[ -z "$pos" ] && exit 0
[ "$pos" = "[]" ] && exit 0   # aucune position = rien à garder

ord=$(curl -s "$API/api/bot/orders")

# Vérifie qu'un stop reduceOnly existe pour chaque symbol en position
missing=$(python3 - <<PYEOF
import sys, json

pos = json.loads('''$pos''')
ord = json.loads('''$ord''')

# Symboles avec au moins un stop reduceOnly
protected = {
    o["symbol"]
    for o in ord
    if o.get("orderType") == "stop" and o.get("reduceOnly", False)
}

missing = [p["symbol"] for p in pos if p["symbol"] not in protected]
print("\n".join(missing))
PYEOF
)

if [ -z "$missing" ]; then
  n=$(echo "$pos" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
  echo "$(date -u) SL OK ($n positions protégées)"
  exit 0
fi

# SL manquant — re-pose par symbol
for instr in $missing; do
  echo "$(date -u) SL MANQUANT: $instr -> repose"
  curl -s -X POST "$API/api/grid/sl/config/$instr?maxLossPercent=$MAXLOSS&stopLossOnExchangeEnabled=true" >/dev/null
done
sleep 4

# Re-vérifie
ord2=$(curl -s "$API/api/bot/orders")
still_missing=$(python3 - <<PYEOF
import sys, json

pos = json.loads('''$pos''')
ord = json.loads('''$ord2''')

protected = {
    o["symbol"]
    for o in ord
    if o.get("orderType") == "stop" and o.get("reduceOnly", False)
}

missing = [p["symbol"] for p in pos if p["symbol"] not in protected]
print(",".join(missing))
PYEOF
)

if [ -z "$still_missing" ]; then
  tg "🛡️ Gardien SL v2: stops manquants → REPOSÉS avec succès ($(echo $missing | tr '\n' ','))."
else
  tg "🚨 ALERTE Gardien SL v2: positions OUVERTES SANS STOP pour $still_missing après 2 tentatives. Intervention requise. pos=$pos"
fi
