#!/usr/bin/env python3
"""Build agent-dish.pyz: the whole program as one runnable file (`python3 agent-dish.pyz serve --open`).

agent-dish is standard library only, so a zipapp needs no installer, no virtual environment and no pipx."""

import sys
import zipapp
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"


def build(out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    zipapp.create_archive(
        SRC,
        out,
        interpreter="/usr/bin/env python3",
        main="agent_dish.cli:main",
        compressed=True,
        filter=lambda p: "__pycache__" not in p.parts and p.suffix != ".pyc" and ".egg-info" not in str(p),
    )
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "dist-zipapp/agent-dish.pyz"))
