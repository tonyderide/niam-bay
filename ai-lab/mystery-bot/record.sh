#!/bin/bash
# Enregistreur pour le reverse engineering du « bot mystère » (1017) : photo complète positions+ordres,
# ajoutée à snapshots.jsonl UNIQUEMENT quand l'état change (hash sur positions+ordres, sans l'horodatage).
cd /home/ubuntu/et/exchange-truth && set -a && . /home/ubuntu/martin/.env && set +a
SNAP=$(ET_API_KEY=$KRAKEN_API_KEY ET_API_SECRET=$KRAKEN_API_SECRET timeout 50 python3 -m exchange_truth.cli --exchange krakenfutures --attest 2>/dev/null)
H=$(echo "$SNAP" | python3 -c 'import sys,json,hashlib; d=json.load(sys.stdin); print(hashlib.sha256(json.dumps([[{k:p[k] for k in ("symbol","side","amount","entry")} for p in d["positions"]],[{k:v for k,v in o.items() if k!="id"} for o in d["orders"]]],sort_keys=True).encode()).hexdigest())' 2>/dev/null)
[ -n "$H" ] || exit 0
if [ "$H" != "$(cat /home/ubuntu/et/last.hash 2>/dev/null)" ]; then echo "$SNAP" >> /home/ubuntu/et/snapshots.jsonl; echo "$H" > /home/ubuntu/et/last.hash; fi
