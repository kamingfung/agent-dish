"""Gemini CLI: ~/.gemini/tmp/<project hash>/chats/session-*.json.   EXPERIMENTAL.

Written from the chat-recording format (a JSON document per session with a `messages` list; model messages
carry `tokens` and `toolCalls`) and checked only against a synthetic fixture: no Gemini CLI data was
available when this was written. If your sessions do not appear or look wrong, please open an issue with a
redacted sample. The folder a session ran in is not recorded, only a hash of it, so its project shows as '?'."""

import json
import os

from .base import Adapter, add_msg, new_result, touch, ts

WRITE_TOOLS = {"write_file", "replace", "edit_file", "edit"}
READ_TOOLS = {"read_file", "read_many_files"}


class GeminiAdapter(Adapter):
    name, label, root_env, version = "gemini", "Gemini CLI", "AGENT_DISH_GEMINI_ROOT", 1
    experimental = True

    def default_root(self):
        return os.path.join(os.path.expanduser("~/.gemini"), "tmp")

    def discover(self, cut):
        return self.newer(self.glob(f"{self.root()}/*/chats/session-*.json"), cut)

    def parse(self, path):
        res = new_result()
        try:
            with open(path, errors="ignore") as fh:
                doc = json.load(fh)
        except Exception:
            return res
        sid = doc.get("sessionId") or os.path.basename(path)[:-5]
        touch(res, sid, ts(doc.get("startTime")) or ts(doc.get("lastUpdated")), self.name)
        for i, m in enumerate(doc.get("messages") or []):
            t = ts(m.get("timestamp"))
            if not t:
                continue
            touch(res, sid, t, self.name)
            if m.get("type") == "user":
                text = m.get("content")
                if isinstance(text, list):
                    text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
                if isinstance(text, str) and len(res["prompts"]) < 40:
                    res["prompts"].append((sid, t, text[:3000]))
                continue
            if m.get("type") != "gemini":
                continue
            tk, events = m.get("tokens") or {}, []
            for call in m.get("toolCalls") or []:
                name, args = call.get("name") or "", call.get("args") or {}
                paths = [args.get(k) for k in ("file_path", "absolute_path", "path") if isinstance(args.get(k), str)]
                paths += [p for p in (args.get("paths") or []) if isinstance(p, str)]
                kind = "w" if name in WRITE_TOOLS else "r" if name in READ_TOOLS else None
                events += [(kind, p, t) for p in paths if kind]
            add_msg(
                res,
                m.get("id") or f"{sid}:{i}",
                sid,
                t,
                (tk.get("output") or 0) + (tk.get("thoughts") or 0),
                tk.get("input") or 0,
                tk.get("cached") or 0,
                events,
            )
        return res
