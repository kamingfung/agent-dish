"""Claude Cowork (Claude Desktop's non-coding agent mode).

Desktop agent-mode sessions keep ordinary Claude transcripts, one folder per session:
~/Library/Application Support/Claude/local-agent-mode-sessions/<org>/<user>/local_<id>/.claude/projects/<p>/<id>.jsonl
so the Claude parser reads them unchanged; only where they live and what they are called differ."""

import os
import sys

from .claude import ClaudeAdapter


class CoworkAdapter(ClaudeAdapter):
    name, label, root_env, version = "cowork", "Claude Cowork", "AGENT_DISH_COWORK_ROOT", 1

    def default_root(self):
        if sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support/Claude")
        elif sys.platform.startswith("win"):
            base = os.path.join(os.environ.get("APPDATA", ""), "Claude")
        else:
            base = os.path.expanduser("~/.config/Claude")
        return os.path.join(base, "local-agent-mode-sessions")

    def discover(self, cut):
        r = self.root()
        return self.newer(
            self.glob(f"{r}/*/*/local_*/.claude/projects/*/*.jsonl")
            + self.glob(f"{r}/*/*/local_*/.claude/projects/*/*/subagents/*.jsonl"),
            cut,
        )
