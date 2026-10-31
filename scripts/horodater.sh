#!/bin/bash
# Preuve de date sans GitHub (compte suspendu le 27/10) : horodate le hash du dernier commit avec OpenTimestamps
# (seule l'empreinte part vers les calendriers publics, ancrée dans Bitcoin). Lancé chaque heure par cron ; met aussi à niveau les anciens reçus.
# 31/10 : on teste l'existence du REÇU (.ots), pas du .txt — un essai raté laissait un .txt et n'était jamais retenté
# (panne du venv ots du 30/10 01h23Z au 31/10 13h23Z, repérée par l'outil « matin » du week-end). Les échecs sont journalisés.
D=/home/tony/projets/tonyderide/niam-bay; OTS=/home/tony/.local/share/nb/ots-venv/bin/ots; P=$D/preuves-date
cd $D || exit 1; H=$(git log -1 --format=%H)
if ! ls $P/*-$H.txt >/dev/null 2>&1; then
  F=$P/$(date -u +%Y-%m-%dT%H%MZ)-$H.txt
  { echo "commit $H"; git log -1 --format="date du commit %ci | %s"; } > $F
fi
for t in $P/*.txt; do
  [ -f "$t.ots" ] && continue
  if err=$($OTS stamp "$t" 2>&1 >/dev/null); then echo "$(date -u +%FT%TZ) horodaté $(basename "$t" .txt)"
  else echo "$(date -u +%FT%TZ) ÉCHEC horodatage $(basename "$t") : ${err:0:200}"; fi
done
for o in $P/*.ots; do $OTS upgrade $o >/dev/null 2>&1; done
