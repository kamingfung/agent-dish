# agent-dish

Let's cultivate your AI agents. A living petri dish of your Claude Code, Claude Cowork, Kiro, Antigravity, Gemini and
Codex sessions: a cell per session that grows with its tokens, with colonies named by what they are about.

This is the npm packaging of [agent-dish](https://github.com/kamingfung/agent-dish): a small launcher around the Python
program, so **Python 3.9 or newer must be on your PATH**. The package has no dependencies, no install scripts, and makes
no network requests. It reads your agents' transcripts locally and serves the dish on `127.0.0.1` only.

```bash
npx agent-dish demo --open     # invented sessions, nothing from your machine
npx agent-dish serve --open    # your own dish, live
```

Full documentation, privacy notes and the list of supported agents: https://github.com/kamingfung/agent-dish
