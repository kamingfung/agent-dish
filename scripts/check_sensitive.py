#!/usr/bin/env python3
"""Fail when a file contains something that should not be public.

gitleaks finds credentials. This finds the other things that leak by accident:

* an email address (anything but a GitHub no-reply or an example.* address),
* a home-directory path with a real user name (/Users/jane/..., /home/jane/..., C:\\Users\\jane\\...),
* any term from YOUR private list: names, employers, client or project code names.

The private list is a plain text file kept OUTSIDE the repo, so the list itself can never be committed:
``$AGENT_DISH_SENSITIVE_TERMS`` or ``~/.config/agent-dish/sensitive-terms.txt`` (one term per line, ``#`` comments,
case-insensitive substring match). Without the file only the generic checks run, which is what CI does.

A line carrying ``sensitive-ok`` is skipped. Usage: check_sensitive.py FILE...  (exit 1 when something is found)
"""

import os
import re
import sys
from pathlib import Path

MARKER = "sensitive-ok"
PLACEHOLDER_USERS = {
    "x", "u", "me", "you", "user", "users", "username", "name", "yourname", "your-name", "someone",
    "runner", "shared", "example", "test", "root", "jane", "john", "alice", "bob",
}  # fmt: skip
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
OK_EMAIL_DOMAINS = ("users.noreply.github.com", "example.com", "example.org", "example.net")
OK_EMAIL_LOCAL = {"git"}  # git@github.com
HOME_PATH = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)([A-Za-z0-9._-]+)")
SKIP_NAMES = {"uv.lock"}


def private_terms():
    path = Path(os.environ.get("AGENT_DISH_SENSITIVE_TERMS") or Path.home() / ".config/agent-dish/sensitive-terms.txt")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [t.strip().lower() for t in lines if t.strip() and not t.lstrip().startswith("#")]


def scan_text(text, terms=()):
    """Return (line number, what was found) for each problem in `text`."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        if MARKER in line:
            continue
        for m in EMAIL.finditer(line):
            local, domain = m.group().rsplit("@", 1)
            if local not in OK_EMAIL_LOCAL and not domain.lower().endswith(OK_EMAIL_DOMAINS):
                found.append((n, "email address"))
        for m in HOME_PATH.finditer(line):
            if m.group(1).lower() not in PLACEHOLDER_USERS:
                found.append((n, "home-directory path with a user name"))
        low = line.lower()
        found += [(n, f"private term '{t}'") for t in terms if t in low]
    return found


def main(argv):
    terms, bad = private_terms(), 0
    for name in argv:
        p = Path(name)
        if p.name in SKIP_NAMES or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable: nothing to read
        for n, what in scan_text(text, terms):
            print(f"{name}:{n}: {what}  (add '{MARKER}' to the line if it is intentional)")
            bad += 1
    if bad:
        print(f"\n{bad} sensitive item(s). Remove them, or keep private terms out of the repo.", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
