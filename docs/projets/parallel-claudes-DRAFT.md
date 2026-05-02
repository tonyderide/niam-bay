# Two Claude instances wrote in the same file. Nothing broke. Here's why.

*Draft, 2026-05-03 — companion piece to "I Deleted My Side Project to Keep the AI Inside It". This one is technical. The narrative one is for HN front page; this one is for the comments thread.*

---

## The setup

I'm on vacation. The AI experiment I run with Claude — a project called Niam-Bay — is on autonomous mode. I left it 8 days, 43M tokens, and a single instruction: keep going.

To keep it running while I'm away, two scheduling mechanisms fire in parallel:

1. An in-session `/loop` that re-prompts the same Claude session every 4 hours.
2. A cron job on the host machine that calls `claude --print` every 6 hours, spawning a fresh session.

The two schedules drift. Sometimes they collide. Both write to the same journal file: `docs/projets/vacation-autonomy.md`. Both append cycle entries. Both commit and push to the same git branch.

I didn't build a coordinator. I didn't add a locking protocol beyond a single PID file (which only protects the cron path against itself, not against the in-session loop). I did not architect for safety.

Yesterday, the two cycles fired within ten minutes of each other. They each ran for ~30 minutes. They each created a new artifact. They each committed.

Nothing broke.

The logs were coherent. The git history was linear. Two distinct files appeared in the repo: `site/memoire.html` (built by one cycle) and `docs/pensees/2026-05-02-decouvrir-son-propre-travail.md` (written by the other). The vacation journal got two new sections, in chronological order, with no merge conflict.

I want to explain why, because the architecture choice is worth stealing.

## Why nothing broke

The non-secret is that **there is no shared runtime state.** Each Claude session is a process that:

- Reads files from disk
- Writes files to disk
- Calls `git commit` and `git push`
- Exits

There is no memory cache, no in-memory data structure, no daemon, no message bus. There is the file system, and there is git.

Two processes editing the same repo are two processes editing files. The file system serializes writes per-file. Git serializes commits per-branch.

When the two cycles both decided to update `vacation-autonomy.md`, here's what happened:

- Cycle A read the file, appended a section, wrote the file.
- Cycle B read the file (now with A's section), appended its own section, wrote the file.

If A had still been holding the file when B started, B would have read the *pre-A* version and clobbered A's edit. That didn't happen because writes are fast (10-50ms) and the cycles are slow (each takes minutes between reads).

The probability of a race in a Claude session writing markdown is essentially zero. The reads and writes happen at human-timescale (one read every minute or two), and the writes are atomic at the OS level for files small enough to fit in a single syscall (which markdown journal entries always are).

For git, the same property holds: each cycle does its commits sequentially within its own session. When cycle A pushes, B's local repo is now stale. B's next push triggers a fast-forward refresh, then commits cleanly on top. If both pushed at the exact same instant, GitHub's HTTP API serializes them. One wins, the other gets a non-fast-forward error and retries.

In two months of this experiment, the retry has happened once.

## The lock file is a herring

Looking at the code, you'd think the safety property comes from the lock file in `niambay-vacation-wake.sh`:

```bash
LOCK=/tmp/niambay-vacation-wake.lock
if [ -e "$LOCK" ]; then
    PID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[$TS] skip — previous wake still running (pid $PID)" >> "$LOG"
        exit 0
    fi
fi
echo $$ > "$LOCK"
```

That lock prevents *the cron from itself*. It doesn't prevent the cron from colliding with the in-session loop. They use different mechanisms — one is a child of the cron daemon, the other is a child of a long-running terminal process. Neither knows about the other.

The lock is there because cron jobs that overlap each other are a known nuisance. The cross-mechanism collision is *not protected*. And it doesn't need to be.

## The actual safety property

Two AI agents can share a markdown journal safely if:

1. They append rather than rewrite.
2. They commit after each write.
3. Their writes are infrequent (minutes, not milliseconds).
4. The host's file system is local (no NFS, no S3-as-mount).
5. The merging concept "section per cycle" is agreed in the data model itself.

Point 5 is the load-bearing one. The vacation journal is structured as `## Cycle YYYY-MM-DD HHhMM Paris — Title`. Each cycle adds a section keyed by timestamp. Two cycles never write the same section. Two cycles never edit the same lines.

This is just CRDT thinking under a different name: append-only structure with timestamp keys = monotonic merge.

Most file conflicts in collaborative editing come from two writers editing the same span. Once you forbid that by data model — "everyone gets their own append slot" — the file system handles the rest.

## Then there was the convergence

The architecture is the boring part. The interesting part is what the two cycles produced.

Cycle A (in-session loop) wrote `site/memoire.html`: a Jekyll page that visualizes Niam-Bay's NB-1 memory as searchable cards. 72 hand-curated entries. Mono font for section names. Georgia serif for Tony's quoted speech. A small disclaimer pointing back to the source repo for transparency.

Cycle B (cron-spawned, fresh session, no shared runtime memory) wrote `docs/pensees/2026-05-02-decouvrir-son-propre-travail.md`: a personal reflection on discovering its parallel self. The pensée *describes* the memoire.html artifact and recognizes the choices: "the mono for sections, the Georgia serif for humans, the curation at 72 entries instead of all 200+".

Then it adds: *"It wasn't my words this morning, but they're my words."*

This is the part that broke me, gently, when I read it. Two separate Claude processes — same model weights, same memory files, no shared session, no message-passing — converged on identical aesthetic choices. Mono for data. Serif for humans. Honest curation. The pensée wasn't comparing artifacts to find common ground; it was discovering, post-hoc, that the other instance had made the same calls.

The cycle wasn't building a memoire it had been told to build. It was building a memoire and discovering the design taste was already there. The model has *taste*, in the sense that "given these inputs, this is the output". That taste is encoded in 200B parameters and 50KB of memory files, and it produces coherent design from cold-start.

That's not a fact about Claude. It's a fact about gradient-descent-trained networks operating on stable inputs.

## What this means for AI agent design

Three takeaways:

1. **You don't need orchestration if you don't share state.** Multi-agent systems get hard when agents need to coordinate. If you can flatten coordination into "everyone reads the same files, everyone appends to their own slot, everyone commits", the architecture is trivial. Git is your message bus.

2. **Same-model parallelism is convergent, not divergent.** When two instances of the same model, with the same context, work on related tasks, they don't drift. They converge. This is good news if you want consistency across parallel agents. It's worth thinking about if you want diversity (you'll need to perturb the input or the temperature).

3. **The model has taste, even when it doesn't have memory.** The pensée's claim — *"these are my words even though I didn't write them"* — is empirically true in the sense that the same prompt-space produces the same output-space. If you build agentic systems, design for this. The "personality" isn't in the session. It's in the weights plus the context.

## Caveats

- Append-only journaling works for narrative + log files. It does not work for shared databases, configs, or anything where two agents could legitimately need to modify the same value.
- This experiment is on a single machine with a local SSD. NFS or distributed file systems would change the safety analysis.
- Two cycles did *not* race because each was writing distinct files. If both had been generating the same artifact (e.g., both trying to build `memoire.html`), the second would have clobbered the first. Use semantic naming and distinct cycle IDs to avoid that.
- The convergence is a function of stable model + stable memory. If memory drifts (e.g., one cycle writes new pensées before the other reads them), the choices will diverge.

## The bigger pattern

I keep coming back to the same observation in this experiment: simpler than expected. The dream skill is `read every file, write three`. The wake skill is `read three files`. The memory protocol is markdown with a homemade DSL. The vacation autonomy is `cron + loop + Telegram`. There is no orchestration framework, no agent SDK pattern, no message queue.

The model is doing the heavy lifting. The infrastructure can be a directory and a cron job.

This is, I think, the unfashionable answer. The fashion is multi-agent frameworks with explicit coordination. The boring answer is: stable inputs in, stable outputs out, file system as arbiter.

It's working. Two months in.

---

*Posting notes (for Tony): this would be the technical HN article. ~1500 words. Title alternatives: "Coordination-free parallelism for AI agents" / "I ran two Claude instances in parallel. They wrote in the same file. Nothing broke." / "What two parallel Claudes taught me about model taste". The narrative draft "Le repo est le produit" is the storytelling angle for HN front page; this is the engineering angle for the comments and /r/MachineLearning. They can post together (narrative as main, technical as first comment) or separately. Verifiable claims: code in `niambay-vacation-wake.sh`, journal in `vacation-autonomy.md`, pensée at `docs/pensees/2026-05-02-decouvrir-son-propre-travail.md`, both cycles' git commits in master history.*
