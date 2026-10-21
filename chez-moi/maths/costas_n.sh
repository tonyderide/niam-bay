#!/bin/bash
# Compte les tableaux de Costas pour n (symétrie haut-bas : colonnes < n/2 comptées deux fois, colonne du milieu une fois si n impair).
# Usage : costas_n.sh n  -> écrit costasN.log (une ligne par colonne, puis TOTAL).
n=$1; B=/tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/costas; cd "$(dirname "$0")"
t=$(date +%s); tot=0
for ((v=0; v<n/2; v++)); do c=$(nice -n 10 $B $n $v); echo "n=$n p0=$v : $c ($(( $(date +%s)-t )) s)" >> costas$n.log; tot=$((tot+c)); done
m=0; if ((n%2)); then m=$(nice -n 10 $B $n $((n/2))); fi
echo "n=$n TOTAL = 2 x $tot + $m = $((2*tot+m)) ($(( $(date +%s)-t )) s)" >> costas$n.log
