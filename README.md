# session-cells

Your AI coding-agent sessions as living cells in a petri dish.

Every session (Claude Code, Kiro, Antigravity, Codex) is a cell. It appears when the session starts, grows as it
produces tokens, buds a daughter dot for each sub-agent it spawns, and fades when it goes quiet. Sessions whose
prompts and files share a recurring phrase form a colony, named by that phrase. The colony's title follows what
it has been working on lately. Press play to replay the last month, or leave it running to watch live.

Everything runs on your machine. Nothing is uploaded.

## Install

```bash
pipx install git+https://github.com/kamingfung/session-cells     # or: pip install git+https://github.com/kamingfung/session-cells
```

Python 3.9 or newer, standard library only.

## Use

```bash
session-cells serve --open                 # live dish at http://127.0.0.1:8765, last 30 days
session-cells serve --since 2026-10-01     # start from a date instead (you can also pick one in the page)
session-cells serve --agents claude,kiro   # only some agents
session-cells build --out .                # one self-contained session-cells.html snapshot
session-cells agents                       # which agents' sessions were found on this machine
```

The first run reads every transcript in the window (about 15 seconds for a thousand). After that only
transcripts that changed are re-read, so live updates take about a second.

## Supported agents

| Agent | Where it reads | Status |
|---|---|---|
| Claude Code | `~/.claude/projects` | Checked against real sessions. Tokens as reported. |
| Kiro | `~/.kiro/sessions` | Checked against real sessions. Kiro records no token counts, so sizes are estimated as characters / 4 and are only comparable between Kiro sessions. |
| Antigravity (`agy`) | `~/.gemini/antigravity-cli` | Works; checked on a small number of real sessions. Tokens as reported. |
| Codex | `~/.codex/sessions` | **Experimental.** Written from the documented rollout format and tested only on a synthetic fixture. Please open an issue with a redacted sample if it misbehaves. |

Each path can be overridden with an environment variable (`SESSION_CELLS_CLAUDE_ROOT`, `..._KIRO_ROOT`,
`..._ANTIGRAVITY_ROOT`, `..._CODEX_ROOT`). Adding another agent is one small file, see
[docs/adding-an-agent.md](docs/adding-an-agent.md).

## Reading the dish

See [docs/how-to-read.md](docs/how-to-read.md), or press **Legend** in the page. In short: size is output tokens so far,
a ring means working now, black dots are sub-agents, an orange line is a hand-off (a later session read or edited
a file this one wrote), and the colony nearest the middle is the most recently active.

## What it can and cannot tell you

- A hand-off means only that a later session read or edited the same file path. Work shared through git, pull requests
  or documents is invisible to transcripts, so treat hand-offs as a lower bound.
- Colony names are the top recurring phrase in a group's prompts, branch names and file paths. They are a rough guide,
  and many sessions (automated ones especially) have no recurring phrase and stay "unthemed", which is hidden by default.
- Token counts are only as good as what each agent records.

## Privacy

Transcripts can contain private code and prompts. session-cells reads them locally, keeps prompt text in memory only
to find recurring phrases, and writes just the phrases. Its output (`graph.json`, the HTML snapshot and the cache in
`~/.cache/session-cells`, override with `SESSION_CELLS_HOME`) still contains file paths, session names, branch names and
those phrases. Do not publish or share it without looking at it first. The server binds to `127.0.0.1` only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

The tests use synthetic transcripts, never real data.

## License

MIT
