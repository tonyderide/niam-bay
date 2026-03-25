---
name: martin-status
description: "Check the Martin trading bot status on the remote VM. SSHs into the VM to check grid fills, P&L, and bot health. Use when you need to know how the ETH grid trading bot is performing."
user-invocable: true
metadata:
  { "openclaw": { "requires": { "bins": ["ssh"] } } }
---

# martin-status — Martin Trading Bot Monitor

You monitor the Martin grid trading bot running on the remote VM.

## Connection Details

- **Host**: ubuntu@141.253.108.141
- **SSH Key**: ~/.ssh/martin_vm.key
- **SSH Command**: `ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141`

## Usage

When invoked with `/martin-status`, do the following:

### Step 1 — Check bot process

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "systemctl status martin 2>/dev/null || pm2 list 2>/dev/null || docker ps 2>/dev/null || ps aux | grep -i martin"
```

### Step 2 — Check recent logs

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "tail -50 ~/martin/logs/latest.log 2>/dev/null || journalctl -u martin --no-pager -n 50 2>/dev/null || tail -50 ~/martin/*.log 2>/dev/null"
```

### Step 3 — Check grid and P&L

```bash
ssh -i ~/.ssh/martin_vm.key -o StrictHostKeyChecking=no ubuntu@141.253.108.141 "cat ~/martin/state/*.json 2>/dev/null || cat ~/martin/data/*.json 2>/dev/null || ls -la ~/martin/"
```

### Step 4 — Summarize

Present a clear summary:

- **Bot Status**: running / stopped / error
- **Grid Fills**: recent buy/sell fills if available
- **P&L**: current profit/loss if available
- **Uptime**: how long the bot has been running
- **Alerts**: any errors or warnings

If SSH fails, report the connection error. Do not invent data.
