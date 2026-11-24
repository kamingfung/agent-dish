#!/usr/bin/env python3
"""Refuse a release whose tag and version disagree.

Versions are dates: YYYY.MM.DD, or YYYY.MM.DD.N for a second release on the same day. The release tag is `v` plus the
version. This keeps the wheel, the single-file .pyz and the GitHub release from ever being labelled differently.
Usage: release_check.py TAG   (exit 1 with a message when something is off)
"""

import re
import sys
from pathlib import Path

INIT = Path(__file__).resolve().parent.parent / "src" / "agent_dish" / "__init__.py"
CALVER = re.compile(r"^\d{4}\.\d{2}\.\d{2}(\.\d+)?$")


def package_version():
    return re.search(r'^__version__\s*=\s*"([^"]+)"', INIT.read_text(), re.M).group(1)


def normal(version):
    """2026.01.05 and 2026.1.5 are one version to Python's packaging tools, so compare the numbers."""
    return tuple(int(part) for part in version.removeprefix("v").split("."))


def problems(tag, version):
    found = []
    if not CALVER.match(version):
        found.append(f"version {version!r} must look like YYYY.MM.DD or YYYY.MM.DD.N")
    if not re.fullmatch(r"v\d+(\.\d+)*", tag):
        found.append(f"tag {tag!r} must be v followed by the version")
    elif normal(tag) != normal(version):
        found.append(f"tag {tag} does not match the package version {version} (run `just bump`, commit, then release)")
    return found


def main(argv):
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    version = package_version()
    errors = problems(argv[0], version)
    for e in errors:
        print("release check failed:", e, file=sys.stderr)
    if not errors:
        print(f"ok: {argv[0]} is version {version}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
