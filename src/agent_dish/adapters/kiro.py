"""Kiro CLI/IDE: ~/.kiro/sessions/<workspace hash>/sess_<id>/{messages.jsonl, session.json}.

Kiro does not record token counts, so output tokens are estimated as characters / 4 of what the agent
wrote (text and tool arguments). Sizes are comparable between Kiro sessions, not with other agents."""

import json
import os

from .base import Adapter, add_msg, new_result, read_jsonl, touch, ts

WRITE_TOOLS = {"str_replace", "fs_write", "fs_append"}
READ_TOOLS = {"read_file", "readFile", "read_files", "read_code"}
BOOKKEEPING = {"tool_load", "fetch_cloud_config", "update_session_information", "disclose_context"}


def _paths(args):
    out = []
    for key in ("path", "file_path", "filePath"):
        if isinstance(args.get(key), str):
            out.append(args[key])
    for key in ("paths", "files"):
        if isinstance(args.get(key), list):
            out += [x if isinstance(x, str) else (x.get("path") if isinstance(x, dict) else None) for x in args[key]]
    return [p for p in out if isinstance(p, str) and p]


class KiroAdapter(Adapter):
    name, label, root_env, version = "kiro", "Kiro", "AGENT_DISH_KIRO_ROOT", 1
    tokens_estimated = True

    def default_root(self):
        return os.path.expanduser("~/.kiro/sessions")

    def discover(self, cut):
        return self.newer(self.glob(f"{self.root()}/[!_]*/sess_*/messages.jsonl"), cut)

    def parse(self, path):
        res = new_result()
        sdir = os.path.dirname(path)
        sid = os.path.basename(sdir)
        cwd, title = "", ""
        try:
            with open(os.path.join(sdir, "session.json")) as fh:
                meta = json.load(fh)
            cwd = (meta.get("workspacePaths") or [""])[0]
            title = meta.get("title") or ""
        except Exception:
            pass
        for d in read_jsonl(path):
            t, p = ts(d.get("timestamp", "")), d.get("payload")
            if not t or not isinstance(p, dict):
                continue
            touch(res, sid, t, self.name, cwd, "", title)
            kind, mid = p.get("type"), d.get("id") or f"{sid}:{t}"
            if kind == "user" and isinstance(p.get("content"), str) and len(res["prompts"]) < 40:
                res["prompts"].append((sid, t, p["content"][:3000]))
            elif kind == "assistant" and p.get("operationType") == "Say":
                add_msg(res, mid, sid, t, out=len(str(p.get("content") or "")) // 4)
            elif kind == "tool_call":
                name, args = p.get("toolName") or "", p.get("args") if isinstance(p.get("args"), dict) else {}
                if name in BOOKKEEPING:
                    continue
                events = []
                for path_ in _paths(args):
                    full = path_ if os.path.isabs(path_) or not cwd else os.path.join(cwd, path_)
                    if name in WRITE_TOOLS:
                        events.append(("w", full, t))
                    elif name in READ_TOOLS:
                        events.append(("r", full, t))
                add_msg(res, mid, sid, t, out=len(json.dumps(args)) // 4, events=events)
                if name == "invoke_sub_agent":
                    res["subs"].append((sid, mid, t))
        if title and res["nodes"].get(sid):
            res["prompts"].append((sid, res["nodes"][sid]["lo"], title))
        return res
