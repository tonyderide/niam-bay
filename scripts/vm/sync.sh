#!/bin/bash
# Synchronisation PC <-> VM (1018). La VM détient l'état vivant ; le repo sert d'archive.
#  PC -> VM : ce que la VM lit (journal, verdicts du conseil, a-faire-tony) et les NOUVELLES prédictions (merge par id)
#  VM -> PC : prédictions tranchées, duel, journal du jumeau, inbox (privée, non commitée)
set -e
R=~/projets/tonyderide/niam-bay; K="-i $HOME/.ssh/martin_vm.key -o ConnectTimeout=10 -o BatchMode=yes"; V=ubuntu@141.253.108.141
scp -q $K $R/docs/loop-journal.md $R/ai-lab/conseil/deliberations.jsonl $R/docs/a-faire-tony.md $R/docs/memoire-verif.md $V:nb/
# prédictions : on envoie celles du PC, la VM fusionne (elle garde ses issues, ajoute les nouvelles par id)
scp -q $K $R/ai-lab/calibration/predictions.json $V:nb/calibration/predictions.pc.json
ssh $K $V 'cd ~/nb/calibration && python3 - <<PY
import json,os
V=json.load(open("predictions.json")); P=json.load(open("predictions.pc.json")); ids={x["id"] for x in V}
V+= [x for x in P if x["id"] not in ids]; json.dump(V,open("predictions.json","w"),indent=1,ensure_ascii=False); os.remove("predictions.pc.json")
PY'
scp -q $K $V:nb/calibration/predictions.json $R/ai-lab/calibration/predictions.json
scp -q $K $V:nb/calibration/calibration.md $R/docs/calibration.md 2>/dev/null || true
for f in history.jsonl current.json; do scp -q $K $V:nb/duel/$f $R/ai-lab/duel/$f 2>/dev/null || rm -f $R/ai-lab/duel/$f.absent; done
ssh $K $V 'test -f ~/nb/duel/current.json' || rm -f $R/ai-lab/duel/current.json
scp -q $K $V:nb/jumeau/test_log.jsonl $R/ai-lab/jumeau/test_log.jsonl 2>/dev/null || true
scp -q $K $V:nb/inbox.jsonl $R/docs/inbox-vm.jsonl 2>/dev/null || true
echo "sync ok $(date +%H:%M)"
