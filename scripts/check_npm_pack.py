#!/usr/bin/env python3
"""Check exactly what `npm publish` would put on the registry, before it does. Exit 1 on anything unexpected."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "npm"
ALLOWED = ("bin/", "python/agent_dish/", "package.json", "README.md", "LICENSE")
FORBIDDEN = ("__pycache__", ".pyc", ".env", "graph.json", ".cache", "tests/", ".git", "node_modules", ".tgz")
REQUIRED = ("bin/agent-dish.js", "python/agent_dish/cli.py", "python/agent_dish/web/template.html", "package.json")


def main():
    out = subprocess.run(  # noqa: S603
        ["npm", "pack", "--dry-run", "--json", "--ignore-scripts"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    data = json.loads(out)
    # older npm prints a list of results, newer npm prints {package name: result}
    pack = data[0] if isinstance(data, list) else data if "files" in data else next(iter(data.values()))
    paths = [f["path"] for f in pack["files"]]
    problems = [f"unexpected file: {p}" for p in paths if not p.startswith(ALLOWED)]
    problems += [f"forbidden file: {p}" for p in paths if any(bad in p for bad in FORBIDDEN)]
    problems += [f"missing: {r}" for r in REQUIRED if r not in paths]
    print(f"{pack['name']}@{pack['version']}: {len(paths)} files, {pack['size'] / 1024:.0f} kB packed")
    for p in paths:
        print("  ", p)
    for p in problems:
        print("PROBLEM:", p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
