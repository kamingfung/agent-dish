# How to read the dish

The dish replays your agent sessions as living cells, then keeps growing live when served by `agent-dish serve`.
Pick the start date with the **from** box in the header (a snapshot can only start at or after the date it was built from).

## What you are looking at

| You see | It means |
|---|---|
| A cell | One session (Claude Code, Kiro, Antigravity or Codex). Sub-agent work is counted in its parent. |
| Cell appears | The session's first message. |
| Cell size | Output tokens produced so far, on a log scale (the legend shows 1k, 10k, 100k, 1M). A cell grows while its session works. Kiro sizes are estimated. |
| Colour | The colony the cell belongs to. **Shuffle colours** picks a new set. |
| Colony title | The phrase that colony has been about over the last few days. It changes as the work does, crossfading from the old title to the new. The count is how many of its cells exist at the dish clock. |
| Floor glow | A heat map: each cell tints the dish around it in its colour, stronger where more or bigger cells cluster. Dormant cells glow at about a third strength. |
| Position | The colony with the newest activity sits in the middle and older colonies ring outward. Inside a colony the newest cell is at its centre and older ones spiral out. |
| Ring around a cell | It produced output in the last 10 minutes of dish time. |
| Faded cell | Dormant: over an hour since its last message. |
| Black dots | Sub-agents it has spawned so far (divisions). |
| Orange line | A hand-off: a later session read or edited a file this one wrote. The expanding ring marks the session that built on it. |
| Grey cells (when shown) | Sessions with no recurring phrase. Hidden by default; tick **unthemed** to show them as an outer band. |

## Controls

- **Play / Pause**, the **scrubber** (drag to any moment), and **speed**. Normal plays 30 days in about a minute.
- **Now** jumps to the newest activity and follows it. A served dish refreshes itself every 10 seconds.
- Click a cell for its details: agent, project, branch, tokens, who built on it and what it built on.
- **Legend** shows or hides the legend panel.

## What it does not show

- Hand-offs through git, pull requests or documents.
- Sessions with no output tokens.
- Anything before the start date.
