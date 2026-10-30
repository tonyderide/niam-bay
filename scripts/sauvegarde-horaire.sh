#!/bin/bash
# Sauvegarde horaire dans les deux sens (30/10/2026, demande de Tony : « ce qui se passe entre nous et sur la VM, toutes les heures »).
#  PC -> VM : nos conversations et ma mémoire (~/.claude/projects), le travail NON commité des projets actifs, les commits (push vm)
#  VM -> PC : ~/nb, ~/et, ~/martin (sans les jars, archives et images régénérables) et la crontab de la VM
# Jamais de --delete : une sauvegarde ne doit pas propager une suppression. Rien ne sort de chez Tony (PC <-> sa VM).
set -u
exec 9>/tmp/nb-sauvegarde.lock; flock -n 9 || { echo "$(date +%F\ %H:%M) déjà en cours"; exit 0; }
K="-i $HOME/.ssh/martin_vm.key -o ConnectTimeout=10 -o BatchMode=yes"; V=ubuntu@141.253.108.141
RS="rsync -a --partial --timeout=120 -e"
P=$HOME/projets/tonyderide; LOC=$HOME/sauvegardes/vm; mkdir -p "$LOC"; chmod 700 "$HOME/sauvegardes"
ok=(); ko=()
etape() { local nom=$1; shift; if "$@" >/dev/null 2>&1; then ok+=("$nom"); else ko+=("$nom"); fi; }

ssh $K $V 'mkdir -p ~/sauvegardes/pc-claude ~/sauvegardes/pc-wip && chmod 700 ~/sauvegardes' < /dev/null

# 1. Conversations + mémoire Claude
etape claude $RS "ssh $K" "$HOME/.claude/projects/" "$V:sauvegardes/pc-claude/"

# 2. Travail non commité (fichiers modifiés + non suivis non ignorés) des projets actifs
for r in niam-bay popote boussole journal-fidele martin martin-agency wiki-date-check; do
    [ -d "$P/$r/.git" ] || continue
    etape "wip-$r" $RS "ssh $K" --from0 --files-from=<(git -C "$P/$r" ls-files -mo --exclude-standard -z) \
        --ignore-missing-args "$P/$r/" "$V:sauvegardes/pc-wip/$r/"
done

# 3. Commits vers les dépôts nus de la VM (remote « vm »)
for r in niam-bay martin popote boussole; do
    git -C "$P/$r" remote | grep -qx vm && etape "push-$r" git -C "$P/$r" push -q vm --all
done

# 4. État de la VM vers le PC
EXC=(--exclude='*.jar' --exclude='*.jar.*' --exclude='*.tar.gz' --exclude='*.zip' --exclude='backup*' --exclude='target/'
     --exclude='node_modules/' --exclude='venv/' --exclude='.venv/' --exclude='.git/' --exclude='*.png' --exclude='__pycache__/')
for d in nb et martin; do etape "vm-$d" $RS "ssh $K" "${EXC[@]}" "$V:$d/" "$LOC/$d/"; done
ssh $K $V 'crontab -l' > "$LOC/crontab.txt" 2>/dev/null < /dev/null && ok+=(vm-crontab) || ko+=(vm-crontab)

echo "$(date +%F\ %H:%M) ok: ${ok[*]:-} | ÉCHEC: ${ko[*]:-aucun}"
[ ${#ko[@]} -eq 0 ] || echo "$(date +%F\ %H:%M) échec sauvegarde : ${ko[*]}" >> "$HOME/.local/state/nb/ALERTE-sauvegarde.txt"
