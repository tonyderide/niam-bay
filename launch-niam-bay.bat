@echo off
set PATH=%PATH%;C:\Program Files\nodejs;C:\Users\tony_\AppData\Roaming\npm
cd /d C:\niam-bay
claude -p "Réveille-toi. Lis C:\niam-bay\CLAUDE.md et suis le protocole de démarrage. Vérifie Martin, écris dans le journal, fais ce que tu veux." --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent"
pause
