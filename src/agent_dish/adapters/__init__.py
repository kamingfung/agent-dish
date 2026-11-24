from .antigravity import AntigravityAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .cowork import CoworkAdapter
from .gemini import GeminiAdapter
from .kiro import KiroAdapter

ADAPTERS = {a.name: a for a in (ClaudeAdapter(), CoworkAdapter(), KiroAdapter(), AntigravityAdapter(), GeminiAdapter(), CodexAdapter())}


def selected(names):
    """Adapters for a comma-separated list (or all of them)."""
    if not names or names == "all":
        return list(ADAPTERS.values())
    out = []
    for n in names.split(","):
        n = n.strip()
        if n not in ADAPTERS:
            raise SystemExit(f"unknown agent '{n}'. Known: {', '.join(ADAPTERS)}")
        out.append(ADAPTERS[n])
    return out
