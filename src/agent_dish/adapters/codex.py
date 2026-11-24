"""OpenAI Codex CLI: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl.   EXPERIMENTAL.

Written from the documented rollout format (session_meta, response_item, event_msg/token_count) and
checked only against a synthetic fixture: no real Codex data was available when this was written.
If your sessions do not appear or look wrong, please open an issue with a redacted sample."""
import json
import os
import re

from .base import Adapter, add_msg, new_result, read_jsonl, touch, ts

PATCH_FILE = re.compile(r"\*\*\* (Add|Update) File: (.+)")
READ_CMDS = {"cat", "sed", "head", "tail", "nl", "less", "bat"}


class CodexAdapter(Adapter):
    name, label, root_env, version = "codex", "Codex", "AGENT_DISH_CODEX_ROOT", 1
    experimental = True

    def default_root(self):
        return os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "sessions")

    def discover(self, cut):
        return self.newer(self.glob(f"{self.root()}/**/rollout-*.jsonl"), cut)

    def parse(self, path):
        res = new_result()
        sid = re.sub(r"^rollout-[\d\-T]+-", "", os.path.basename(path)[:-6]) or os.path.basename(path)[:-6]
        cwd = branch = ""
        pending, last, n = [], dict(i=0, o=0, c=0), 0
        for d in read_jsonl(path):
            t, p, kind = ts(d.get("timestamp", "")), d.get("payload"), d.get("type")
            if not t or not isinstance(p, dict):
                continue
            if kind == "session_meta":
                sid = p.get("id") or sid
                cwd = p.get("cwd") or cwd
                branch = (p.get("git") or {}).get("branch") or branch
            touch(res, sid, t, self.name, cwd, branch)
            ptype = p.get("type")
            if kind == "response_item":
                if ptype == "message" and p.get("role") == "user":
                    text = " ".join(c.get("text", "") for c in p.get("content") or [] if isinstance(c, dict))
                    if text and not text.lstrip().startswith("<") and len(res["prompts"]) < 40:
                        res["prompts"].append((sid, t, text[:3000]))
                elif ptype in ("function_call", "custom_tool_call", "local_shell_call"):
                    n += 1
                    mid, events = f"{sid}:call:{n}", []
                    args = str(p.get("arguments") or p.get("input") or "")
                    for _, f in PATCH_FILE.findall(args):
                        events.append(("w", f.strip(), t))
                    try:
                        cmd = (json.loads(args).get("command") if args.startswith("{") else None) or []
                        if isinstance(cmd, list) and cmd and cmd[0] in READ_CMDS and os.path.isabs(str(cmd[-1])):
                            events.append(("r", cmd[-1], t))
                    except Exception:
                        pass
                    add_msg(res, mid, sid, t, events=events)
                    pending.append(mid)
            elif kind == "event_msg" and ptype == "token_count":
                u = ((p.get("info") or {}).get("total_token_usage")) or {}
                cur = dict(i=u.get("input_tokens") or 0, o=u.get("output_tokens") or 0, c=u.get("cached_input_tokens") or 0)
                if cur["o"] < last["o"]:
                    last = dict(i=0, o=0, c=0)  # counter reset
                delta = {k: cur[k] - last[k] for k in cur}
                last = cur
                mid = pending[-1] if pending else f"{sid}:tok:{t}"
                add_msg(res, mid, sid, t, delta["o"], delta["i"], delta["c"])
                pending = []
        return res
