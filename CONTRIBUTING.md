# Contributing

Needs [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). Everything goes through `just`:

```bash
just setup    # Python environment and git hooks
just check    # what CI runs: hooks, tests, history secret scan
just --list   # every recipe
```

## Keep it free of secrets and personal information

The pre-commit hooks (and CI) refuse a commit that contains a credential (gitleaks, private keys), a large file, a
home-directory path with a real user name, or an email address that is not a GitHub no-reply. To also catch **your own**
names, employers or project code names, put them one per line in `~/.config/agent-dish/sensitive-terms.txt`. That file
lives outside the repository so it can never be committed. Use `sensitive-ok` on a line to allow an intentional match.

Also: commit with your GitHub no-reply address (`git config user.email ID+USER@users.noreply.github.com`), and never
commit real transcripts, `graph.json` or a generated HTML snapshot. Tests and README images use invented data only.

If you already have a global `core.hooksPath` (a company scanner, say), `just setup` installs the repo hooks anyway and
your global hooks keep running as long as they chain to the repo's own hook.

## Adding an agent

See [docs/adding-an-agent.md](docs/adding-an-agent.md). Add a synthetic fixture and a test; never real data.

## Releasing

See [docs/releasing.md](docs/releasing.md).
