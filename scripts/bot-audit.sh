#!/usr/bin/env bash
# bot-audit.sh — defensive engineering audit for a Martin grid bot
#
# Read-only. Cross-checks the three sources of truth that can silently diverge
# in a running grid bot and detects BUG-001 (duplicate stop-loss orders on
# Kraken). Companion script to chapter 7 of the piste-4 ebook.
#
# What it checks:
#   1. Bot reachable + uptime
#   2. Per active grid, drift across:
#        - runtime  (/api/grid/active)
#        - strategy.json on VM (read-only cat over SSH)
#        - configs map (/api/signal/auto/status — RAM only, vidée au restart)
#   3. BUG-001 SL duplicate detector — counts stop orders per symbol on Kraken
#      via /api/bot/orders. N>=2 SL on same symbol = duplicate.
#   4. SL distance per active position (warn if cushion < 1% or > 8%).
#
# Read-only by design. Never POST. Never mutate strategy.json.
#
# Usage:
#   ./scripts/bot-audit.sh                # SSH to VM, defaults
#   MARTIN_HOST=localhost:8081 ./scripts/bot-audit.sh    # local bot
#
# Exit codes:
#   0 = no drift, no dupes
#   1 = drift detected or dupes present
#   2 = bot unreachable

set -u

MARTIN_HOST="${MARTIN_HOST:-localhost:8081}"
SSH_KEY="${SSH_KEY:-${HOME}/.ssh/martin_vm.key}"
SSH_HOST="${SSH_HOST:-ubuntu@141.253.108.141}"
STRATEGY_PATH="${STRATEGY_PATH:-/home/ubuntu/martin/config/strategy.json}"
SL_CUSHION_WARN_MIN_PCT="${SL_CUSHION_WARN_MIN_PCT:-1.0}"
SL_CUSHION_WARN_MAX_PCT="${SL_CUSHION_WARN_MAX_PCT:-8.0}"

run_remote() {
  if [[ "${MARTIN_HOST}" == "localhost:8081" ]] && [[ -n "${SSH_HOST}" ]]; then
    ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "${SSH_HOST}" "$1"
  else
    bash -c "$1"
  fi
}

curl_api() {
  run_remote "curl -s --max-time 5 http://${MARTIN_HOST}$1"
}

drift_count=0
dupe_count=0

echo "# bot-audit — $(date -u +%FT%TZ)"
echo "Target: ${MARTIN_HOST} via ${SSH_HOST:-local}"
echo

# 1. Bot reachable
status_json=$(curl_api "/api/system/status")
if [[ -z "${status_json}" ]]; then
  echo "FAIL: bot unreachable on ${MARTIN_HOST}"
  exit 2
fi
uptime=$(echo "${status_json}" | jq -r '.uptime_human // "?"')
echo "Bot UP — uptime ${uptime}"
echo

# 2. Sources of truth cross-check
active_grids=$(curl_api "/api/grid/active" | jq -r '.[]' 2>/dev/null)
auto_status=$(curl_api "/api/signal/auto/status")
configs_pairs=$(echo "${auto_status}" | jq -r '.configs | keys[]' 2>/dev/null | sort -u)
strategy_pairs=$(run_remote "cat ${STRATEGY_PATH} 2>/dev/null" | \
  jq -r '.grids[] | select(.enabled == true) | .instrument' 2>/dev/null | sort -u)

echo "## Sources of truth"
echo "- Runtime (DB H2):      $(echo ${active_grids} | tr '\n' ' ')"
echo "- configs map (RAM):    $(echo ${configs_pairs} | tr '\n' ' ')"
echo "- strategy.json (file): $(echo ${strategy_pairs} | tr '\n' ' ')"
echo

# Drift = symbol present in one set but not another
all_pairs=$(printf "%s\n%s\n%s\n" "${active_grids}" "${configs_pairs}" "${strategy_pairs}" | sort -u | grep -v '^$' || true)
for pair in ${all_pairs}; do
  in_runtime=$(echo "${active_grids}" | grep -qx "${pair}" && echo Y || echo .)
  in_configs=$(echo "${configs_pairs}" | grep -qx "${pair}" && echo Y || echo .)
  in_strategy=$(echo "${strategy_pairs}" | grep -qx "${pair}" && echo Y || echo .)
  combo="${in_runtime}${in_configs}${in_strategy}"
  case "${combo}" in
    YYY) ;;  # aligned
    ...) ;;  # none — impossible since we sort -u, skip
    *)
      drift_count=$((drift_count + 1))
      echo "DRIFT ${pair}: runtime=${in_runtime} configs=${in_configs} strategy=${in_strategy}"
      ;;
  esac
done
[[ ${drift_count} -eq 0 ]] && echo "No drift across sources of truth."
echo

# 3. BUG-001 duplicate stop-loss detector
orders=$(curl_api "/api/bot/orders")
dupe_report=$(echo "${orders}" | jq -r '
  [.[] | select(.orderType == "stop" and .reduceOnly == true)]
  | group_by(.symbol)
  | map({symbol: .[0].symbol, count: length, prices: [.[].stopPrice]})
  | .[] | select(.count >= 2)
  | "\(.symbol): \(.count) stops @ \(.prices | join(", "))"
' 2>/dev/null)

echo "## BUG-001 duplicate SL detector"
if [[ -n "${dupe_report}" ]]; then
  echo "${dupe_report}"
  dupe_count=$(echo "${dupe_report}" | wc -l)
else
  echo "No duplicate SL orders detected."
fi
echo

# 4. SL cushion check per active position
positions=$(curl_api "/api/bot/positions")
echo "## SL cushion per position"
echo "${positions}" | jq -r '.[] | "\(.symbol) \(.side) \(.size) @ \(.price)"' | while read -r line; do
  sym=$(echo "${line}" | awk '{print $1}')
  pos_price=$(echo "${line}" | awk '{print $5}')
  sl_price=$(echo "${orders}" | jq -r --arg sym "${sym}" '
    [.[] | select(.symbol == $sym and .orderType == "stop" and .reduceOnly == true)
       | .stopPrice] | min // empty')
  if [[ -z "${sl_price}" ]] || [[ "${sl_price}" == "null" ]]; then
    echo "${sym}: NO SL on Kraken — exposed."
    drift_count=$((drift_count + 1))
    continue
  fi
  cushion_pct=$(awk -v p="${pos_price}" -v s="${sl_price}" \
    'BEGIN { d = (p - s) / p * 100; if (d < 0) d = -d; printf "%.2f", d }')
  flag=""
  awk -v c="${cushion_pct}" -v lo="${SL_CUSHION_WARN_MIN_PCT}" -v hi="${SL_CUSHION_WARN_MAX_PCT}" \
    'BEGIN { exit !(c < lo || c > hi) }' && flag=" ⚠ out of band"
  echo "${sym}: pos ${pos_price} SL ${sl_price} cushion ${cushion_pct}%${flag}"
done
echo

# Summary
echo "## Summary"
echo "- drift count: ${drift_count}"
echo "- duplicate SL groups: ${dupe_count}"
if [[ ${drift_count} -eq 0 ]] && [[ ${dupe_count} -eq 0 ]]; then
  echo "Verdict: OK"
  exit 0
else
  echo "Verdict: REVIEW"
  exit 1
fi
