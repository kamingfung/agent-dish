#!/usr/bin/env python3
"""Set the version to today's date and date the changelog's "Unreleased" section.

Today is YYYY.MM.DD; if that is already released it becomes YYYY.MM.DD.1, .2, and so on.
Usage: bump_version.py [VERSION]   (an explicit version overrides the date)
"""

import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "src" / "agent_dish" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def next_version(today, tags):
    """The first free version for `today`, given the existing release tags (v2026.11.24, v2026.11.24.1, ...)."""
    base = today.strftime("%Y.%m.%d")
    taken = {t.removeprefix("v") for t in tags}
    candidate, n = base, 0
    while candidate in taken:
        n += 1
        candidate = f"{base}.{n}"
    return candidate


def date_changelog(text, version):
    """Rename the '## Unreleased' heading to the version. Returns the new text, or None if there is no such heading."""
    new, count = re.subn(r"^## Unreleased\s*$", f"## {version}", text, count=1, flags=re.M)
    return new if count else None


def existing_tags():
    tags = set()
    for cmd in (["git", "tag", "-l", "v*"], ["git", "ls-remote", "--tags", "--refs", "origin"]):
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False).stdout  # noqa: S603
        tags |= set(re.findall(r"v\d[\d.]*", out))
    return tags


def main(argv):
    version = argv[0] if argv else next_version(datetime.date.today(), existing_tags())
    INIT.write_text(
        re.sub(r'^__version__ = "[^"]+"', f'__version__ = "{version}"', INIT.read_text(), count=1, flags=re.M)
    )
    dated = date_changelog(CHANGELOG.read_text(), version)
    if dated is None:
        print(
            'note: CHANGELOG.md has no "## Unreleased" section to date; add the release notes under "## '
            + version
            + '"'
        )
    else:
        CHANGELOG.write_text(dated)
    print(f"version is now {version}\nnext: commit and push, then publish a release tagged v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
