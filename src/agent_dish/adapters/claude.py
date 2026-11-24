"""Claude Code: ~/.claude/projects/<project>/<session>.jsonl, sub-agents in <session>/subagents/*.jsonl."""
import os
import re

from .base import Adapter, add_msg, new_result, read_jsonl, touch, ts

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
MSG_TOOL = "mcp__ccd_session_mgmt__send_message"


def prompt_text(d):
    """Human-typed text of a user record, or ''. Tool results and machine wrappers are skipped."""
    if d.get("type") != "user" or d.get("isMeta"):
        return ""
    c = (d.get("message") or {}).get("content")
    if isinstance(c, list):
        c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(c, str):
        return ""
    if c.lstrip().startswith("<") or "task-notification" in c or re.search(r"local_[0-9a-f]{8}", c):
        return ""
    return c[:3000]


class ClaudeAdapter(Adapter):
    name, label, root_env, version = "claude", "Claude Code", "AGENT_DISH_CLAUDE_ROOT", 5

    def default_root(self):
        return os.path.expanduser("~/.claude/projects")

    def discover(self, cut):
        r = self.root()
        return self.newer(self.glob(f"{r}/*/*.jsonl") + self.glob(f"{r}/*/*/subagents/*.jsonl"), cut)

    def parse(self, path):
        res = new_result()
        is_sub = "/subagents/" in path
        sub_first = {}
        for d in read_jsonl(path):
            t = ts(d.get("timestamp", ""))
            if not t:
                continue
            sid = d.get("sessionId") or os.path.basename(path)[:-6]
            touch(res, sid, t, self.name, d.get("cwd"), d.get("gitBranch"), d.get("slug"))
            if is_sub:
                sub_first[sid] = min(sub_first.get(sid, t), t)
            txt = prompt_text(d)
            if txt and len(res["prompts"]) < 40:
                res["prompts"].append((sid, t, txt))
            m = d.get("message")
            if not isinstance(m, dict) or d.get("type") != "assistant":
                continue
            u = m.get("usage") or {}
            events = []
            for b in m.get("content") or []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                p = inp.get("file_path") or inp.get("notebook_path")
                if p and "/.claude/" in p:  # shared agent config and memory, not one session's work
                    p = None
                if b["name"] in WRITE_TOOLS and p:
                    events.append(("w", p, t))
                elif b["name"] == "Read" and p:
                    events.append(("r", p, t))
                elif b["name"] == MSG_TOOL and inp.get("session_id"):
                    res["edges"].append((sid, inp["session_id"], t))
            add_msg(res, m.get("id") or d.get("uuid"), sid, t, u.get("output_tokens") or 0,
                    (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0),
                    u.get("cache_read_input_tokens") or 0, events)
        res["subs"] = [(sid, path, t) for sid, t in sub_first.items()]
        return res
