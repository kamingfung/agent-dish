# Changelog

## Unreleased

- Hand-off lines are hidden by default, because they tangle on a busy dish. Tick **hand-offs** to show them all, or click a
  cell to see its own. A new hand-off still pulses with a ring.

- Colonies keep their place, like a real culture. A colony appears at its own spot (chosen from its name, so the same
  every time) when its first session starts, and grows around that spot. Before, colonies and cells moved as others
  became active. Recency now shows as brightness: cells fade the longer they sit idle (an hour, a day, a week), instead of one dormant step.

- Dates and times use your local time zone, and days are cut at your midnight, not UTC midnight. This covers the page's
  clock and dates, `--since` and `--end`, and the day a session counts toward when colonies are named. A session you ran at
  22:30 now counts for that evening. Under `agent-dish serve`, the colony names follow the time zone of the machine it runs on.

## 2026.11.24.2

First release.

- A petri dish of your agent sessions: a cell per session that grows with its tokens, buds a dot per sub-agent, and gathers
  into colonies named by the phrase their sessions keep returning to. Titles follow the work over time.
- Agents: Claude Code, Claude Cowork, Kiro and Antigravity (checked on real sessions); Gemini CLI and Codex (experimental,
  tested on synthetic fixtures only).
- Live mode with `agent-dish serve`: re-reads only the transcripts that changed. Pick the start date with `--since` or in the page.
- No installer needed: standard library only, so it runs with `uvx`, plain `pip`, a clone, or a single-file `agent-dish.pyz`
  (attached to each release). `agent-dish serve` uses port 3474, with a random free port if that is busy.
- In the page: an **Agents** menu to choose which AIs to include (remembered), and a **from** date that is also where the
  play bar starts.
- `agent-dish demo`: invented sessions to try it with no history of your own.
- Colonies and cells are placed by recency; a heat-map floor shows where work clusters; unthemed sessions are hidden by default.
