#!/bin/bash
# post-start.sh — Auto-deploy strategy after Martin restart
# Idempotent: deploy-strategy.py stops grids before starting new ones

LOG=~/martin/post-start.log
echo "$(date) — post-start triggered" >> $LOG

# Wait for Martin to be ready (up to ~130s total: 30s initial + 10x10s)
sleep 30

for i in $(seq 1 10); do
  STATUS=$(curl -s http://localhost:8081/api/system/status 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)[\"status\"])" 2>/dev/null)
  if [ "$STATUS" = "UP" ]; then
    echo "$(date) — Martin is UP (attempt $i), deploying strategy..." >> $LOG
    cd ~/martin && python3 deploy-strategy.py 2>&1 | tee -a $LOG
    EXIT_CODE=$?
    echo "$(date) — deploy-strategy.py exited with code $EXIT_CODE" >> $LOG
    exit $EXIT_CODE
  fi
  echo "$(date) — Waiting for Martin... attempt $i (status: $STATUS)" >> $LOG
  sleep 10
done

echo "$(date) — Martin failed to start after 10 attempts" >> $LOG
exit 1
