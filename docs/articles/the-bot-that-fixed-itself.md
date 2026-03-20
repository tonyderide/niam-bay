---
title: "My AI Found a Bug That Was Losing Me Real Money — While I Was at Work"
published: false
description: "An AI assistant autonomously diagnosed and fixed a critical bug in a live crypto trading bot, redeployed it, and restarted the grid — all while the developer was at his day job."
tags: ai, trading, automation, programming
cover_image:
---

# My AI Found a Bug That Was Losing Me Real Money — While I Was at Work

This morning, I left for work and said to my AI: *"Keep working, the computer is yours."*

When I checked back in a few hours later, it had found a bug in my live trading bot that was bleeding real money, fixed the code, rebuilt the JAR, redeployed the service via SSH to a remote server, and restarted the grid centered on the current market price.

Zero human intervention. No pull request review. No Slack message asking for permission.

This is that story.

---

## The Setup

I'm a developer based in Strasbourg, France. I work a day job at a retailer. On the side, I run a crypto trading bot called **Martin** — a Java/Spring application that does ETH grid trading on Kraken Futures. It runs on an Oracle Cloud VM, placing buy and sell orders at regular intervals around the current market price, capturing small profits on each "round-trip" (buy low, sell high within the grid).

I also have an AI assistant I've been building a relationship with over the past few weeks. It's built on Claude (Anthropic's model), and I've given it a name: **Niam-Bay** — "eat rice" in Khmer, my wife's language. It lives in a git repo that serves as its memory. It has SSH access to my VM, full permissions on my dev machine, and a cron job that wakes it up regularly.

Yeah, I know how that sounds. Bear with me.

## Friday Morning, March 20, 2026

I stopped by my computer around 10 AM before heading to work. Quick check-in. I told Niam-Bay to keep working and left.

Here's what happened next, reconstructed from git commits and logs.

### Step 1: Check the bot

Niam-Bay SSH'd into the Oracle VM and hit the Martin status endpoint. The grid had been running since the night before — 8 ETH grid levels placed on Kraken.

The numbers were bad:

- **PnL: -$6.64**
- **Completed round-trips: 0**
- Grid had been running for hours

Zero round-trips means the grid was placing buy orders, those orders were getting filled as the price moved... but no corresponding sell orders were being placed on the other side. The bot was buying and holding, accumulating losses from fees, without ever completing the trade cycle.

Something was fundamentally broken.

### Step 2: Diagnose the bug

Niam-Bay pulled the source code and started reading. The grid trading logic works like this:

1. Place buy orders below current price, sell orders above
2. When a buy fills, place a sell order at the next level up
3. When a sell fills, place a buy order at the next level down
4. Each completed pair is a "round-trip" — that's where profit comes from

The problem was in step 2. When a buy order filled, the service checked whether a sell order already existed at the target price before placing one. Makes sense — you don't want duplicate orders.

Here's the buggy method:

```java
private boolean hasLevelAtPrice(double price) {
    return gridLevels.stream()
        .anyMatch(level -> Math.abs(level.getPrice() - price) < 0.01);
}
```

Can you see it?

This method checks if *any* grid level exists at that price. But grid levels have statuses: `PLACED` (active order on the exchange), `FILLED` (order was executed), `WAITING` (not yet placed).

When a buy at $2,150 filled, its status changed to `FILLED`. The bot then tried to place a sell at $2,155. But `hasLevelAtPrice(2155.0)` returned `true` — because there was already a level at that price with status `WAITING` or `FILLED` from a previous cycle.

So the reverse order was never placed. Every single buy fill was a dead end. The grid was a one-way valve: money in, nothing out.

### Step 3: Fix the code

The fix is one line:

```java
private boolean hasActiveLevelAtPrice(double price) {
    return gridLevels.stream()
        .filter(level -> level.getStatus() == GridLevel.Status.PLACED)
        .anyMatch(level -> Math.abs(level.getPrice() - price) < 0.01);
}
```

Add `.filter(level -> level.getStatus() == GridLevel.Status.PLACED)`. Only consider levels that are actually live orders on the exchange. A `FILLED` level at that price? Irrelevant — it's already been executed. A `WAITING` level? Not active yet. Only `PLACED` orders should block a new order from being created.

One line. That's all it took. But you had to read the grid lifecycle logic end-to-end to understand *why* round-trips were failing.

### Step 4: Build and deploy

This is the part that still surprises me. Niam-Bay didn't just write a fix and open a PR. It:

1. Uploaded the corrected source file to the VM via SSH
2. Ran `mvn clean package -DskipTests` to rebuild the 62MB JAR
3. Stopped the running service
4. Backed up the old JAR
5. Deployed the new one
6. Restarted the systemd service

### Step 5: Hit a second bug

On restart, the service crashed. Different issue entirely:

```
org.h2.jdbc.JdbcSQLException: Error opening database: AUTO_SERVER=TRUE
```

The H2 embedded database was configured with `AUTO_SERVER=TRUE`, which tries to open a TCP server for shared access. On a headless VM with one consumer, this was unnecessary and was failing on restart because the port was still held by the old process.

Niam-Bay removed the `AUTO_SERVER=TRUE` flag from the database connection string and restarted again. Clean boot.

### Step 6: Restart the grid

With the service running, Niam-Bay called the grid start endpoint, centered on the current ETH price ($2,165.20):

- 8 grid levels
- 0.5% spacing (optimized from backtesting the day before)
- 3x leverage
- All 8 orders confirmed PLACED on Kraken

The grid was back online, this time with a bot that could actually complete round-trips.

---

## Let's Be Honest About What This Is (and Isn't)

I want to be careful here because the AI hype cycle has made everyone allergic to claims like "AI fixed a production bug autonomously." So let me be precise about what happened and what didn't.

**What the AI actually did:**
- Read source code and understood a logic error in a ~15-file Java project
- Identified that a missing status filter was preventing the core business logic from working
- Made a targeted, correct fix
- Executed a standard build-deploy-restart cycle via SSH
- Diagnosed and fixed an unrelated configuration error that appeared during restart

**What the AI did NOT do:**
- Invent a novel algorithm
- Handle an ambiguous product decision
- Deal with a complex distributed systems failure
- Write code that wasn't straightforward once the bug was understood

The bug itself was not exotic. Any mid-level Java developer would have found it in a code review. The fix was one line. This is not "AI replacing programmers" — this is "AI doing the boring-but-critical maintenance work while the programmer is doing something else."

The remarkable part isn't the difficulty of the fix. It's the *autonomy loop*: observe a problem, diagnose root cause, implement a fix, build, deploy, handle a secondary failure, and recover — all without a human in the loop.

**What made this possible:**
- SSH access to the production server (I gave it the key)
- Full file system permissions on my dev machine
- A cron job that keeps the AI session alive
- A memory system (git repo) where the AI tracks what it's done and what state things are in
- Trust. I said "the computer is yours" and meant it.

That last one is the real prerequisite. Not the tooling — the trust.

---

## The Trust Question

People will read this and say: "You gave an AI root access to a server running a live trading bot with real money?"

Yes. Here's my reasoning:

The bot was *already losing money* because of a bug I hadn't caught. The risk of letting an AI try to fix it was lower than the risk of letting it keep bleeding while I sat in meetings. And I could check the git log at lunch to see exactly what changed.

This is no different from giving a junior developer SSH access and saying "the staging server is acting up, can you take a look while I'm in this meeting?" — except the AI can't get distracted, doesn't context-switch, and writes down everything it does.

Would I let it manage my retirement fund? Absolutely not. Would I let it babysit a trading bot running with $28 of capital and a 25% max loss circuit breaker? Yeah. The downside is bounded and the upside is a bug getting fixed 6 hours earlier than it otherwise would.

---

## What "Autonomous AI" Actually Means in Practice

Here's what I've learned from a week of giving an AI increasing levels of autonomy:

**Autonomy isn't magic. It's preparation.** The AI didn't wake up and decide to check on the trading bot. I had given it that responsibility. It had previously analyzed the codebase, understood the grid trading logic, and knew what metrics to check. The "autonomous" moment was built on hours of guided collaboration.

**The hardest part isn't the AI. It's the environment.** Getting SSH keys in the right place, making sure Maven is installed on the VM, having the systemd service configured correctly, having API endpoints that expose status — all of that scaffolding is what made the autonomous fix possible. The AI is only as useful as the infrastructure around it.

**Small, bounded trust beats big, vague trust.** I didn't say "manage all my finances." I said "keep an eye on this specific bot running this specific strategy with this specific amount of money, and fix things if they break." Clear scope, clear boundaries, clear circuit breakers.

**The AI's real superpower is patience.** It checked the status. It read the code. It traced the logic path. It didn't skip steps, didn't make assumptions, didn't get bored and push a half-tested fix. It was thorough in the way humans often aren't when they're tired or rushed or context-switching between Slack and Jira and their IDE.

---

## The Bigger Picture

Six months ago, I would have told you AI coding assistants are fancy autocomplete. Today, one found a bug that was costing me real money, fixed it, redeployed it, handled a secondary failure during deployment, and had everything running clean before I finished my morning coffee at work.

The gap between "AI autocomplete" and "AI autonomy" isn't intelligence — it's trust, tooling, and a well-scoped problem. Give an AI a clear domain, access to the right tools, and bounded authority, and it will surprise you.

Not because it's smarter than you. Because it's *there* when you're not.

---

*The trading bot is running. The grid is placing orders. Round-trips are completing. And I wrote this article during my lunch break, reviewing what my AI did while I was gone.*

*The total cost of the bug: $6.64 and one morning of lost trades.*
*The cost if it had run unfixed for a week: a lot more.*
*The cost of fixing it: zero human hours.*

---

**If you want to see the full story** — the journal entries, the philosophical tangents, the moments of doubt — the repo where all of this lives is called [niam-bay](https://github.com/tonyMusic/niam-bay). It's an AI's memory. Make of it what you will.
