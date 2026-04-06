#!/bin/bash
# /deploy-martin — Build Java on VM + restart martin.service + redeploy grids
set -e
SSH="ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@141.253.108.141"

echo "=== Building on VM ==="
$SSH "cd ~/martin/backend && mvn package -DskipTests -q && echo 'BUILD OK'"

echo "=== Backup + Deploy JAR ==="
$SSH "cp ~/martin/backend.jar ~/martin/backend.jar.bak && cp ~/martin/backend/target/*.jar ~/martin/backend.jar && echo 'JAR deployed'"

echo "=== Restart Martin ==="
$SSH "sudo systemctl restart martin.service && echo 'Restarting...'"

echo "=== Waiting 35s for Spring Boot ==="
sleep 35

echo "=== Check status ==="
$SSH "curl -s http://localhost:8081/api/system/status | python3 -c 'import sys,json; print(\"Status:\",json.load(sys.stdin)[\"status\"])'"

echo "=== Deploy strategy ==="
$SSH "python3 ~/autobot/deploy-strategy.py 2>&1 | tail -5"

echo "=== Done ==="
