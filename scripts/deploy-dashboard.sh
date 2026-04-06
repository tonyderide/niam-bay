#!/bin/bash
# /deploy-dashboard — Push autobot repo + deploy index.html to VM
set -e
echo "=== Push autobot repo ==="
cd C:/Users/tony_/Documents/autobot-repo
git add -A && git commit -m "dashboard update" 2>/dev/null && git push origin master 2>/dev/null || echo "Nothing to push"
echo "=== Deploy to VM ==="
scp -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no C:/Users/tony_/Documents/autobot-repo/frontend/index.html ubuntu@141.253.108.141:~/autobot/frontend/index.html
echo "=== Done ==="
echo "Dashboard deployed. Refresh http://141.253.108.141/ to see changes."
