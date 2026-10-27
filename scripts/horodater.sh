#!/bin/bash
# Preuve de date sans GitHub (compte suspendu le 27/10) : horodate le hash du dernier commit avec OpenTimestamps
# (seule l'empreinte part vers les calendriers publics, ancrée dans Bitcoin). Lancé chaque heure par cron ; met aussi à niveau les anciens reçus.
D=/home/tony/projets/tonyderide/niam-bay; OTS=/home/tony/.local/share/nb/ots-venv/bin/ots; P=$D/preuves-date
cd $D || exit 1; H=$(git log -1 --format=%H)
if ! ls $P/*-$H.txt >/dev/null 2>&1; then
  F=$P/$(date -u +%Y-%m-%dT%H%MZ)-$H.txt
  { echo "commit $H"; git log -1 --format="date du commit %ci | %s"; } > $F && $OTS stamp $F >/dev/null 2>&1 && echo "$(date -u +%FT%TZ) horodaté $H"
fi
for o in $P/*.ots; do $OTS upgrade $o >/dev/null 2>&1; done
