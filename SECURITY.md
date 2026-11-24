# Security

## Reporting a vulnerability

Please use GitHub's private reporting: **Security > Report a vulnerability** on this repository. Do not open a public
issue for a security problem. Expect a first reply within a few days.

## What this tool touches

agent-dish reads transcripts your AI agents already wrote on your machine, locally. It makes no network requests and
serves only on `127.0.0.1` by default. Transcripts can hold private code and prompts, so:

- never attach a real transcript, `graph.json`, or a generated HTML snapshot to an issue or pull request. Redact first,
  or reproduce with `agent-dish demo`,
- the cache in `~/.cache/agent-dish` and any generated HTML contain file paths and session names.

## Keeping this repository clean

Pre-commit hooks and CI block credentials (gitleaks, private-key detection) and personal information (home-directory
paths, email addresses, and a private list of your own terms kept outside the repo). See [CONTRIBUTING.md](CONTRIBUTING.md).
