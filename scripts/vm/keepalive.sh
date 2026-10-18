#!/bin/bash
# Relance le bot Telegram de NB s'il n'est pas vivant (cron chaque minute sur la VM).
pgrep -f "[n]b_vm_bot.py" >/dev/null || (cd ~/nb && setsid nohup python3 -u nb_vm_bot.py >> ~/nb/bot.log 2>&1 < /dev/null &)
