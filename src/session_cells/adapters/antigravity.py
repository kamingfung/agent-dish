"""Google Antigravity CLI (agy): ~/.gemini/antigravity-cli/brain/<conversation>/.system_generated/logs/transcript.jsonl.

Each PLANNER_RESPONSE step carries input/output/cache token counts and its tool calls. The folder a
conversation ran in comes from cache/last_conversations.json."""
import json
import os

from .base import Adapter, add_msg, new_result, read_jsonl, touch, ts

WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "edit_file", "create_file"}
READ_TOOLS = {"view_file", "view_file_outline", "read_file", "view_code_item"}
PATH_KEYS = ("AbsolutePath", "TargetFile", "FilePath", "File", "Path", "filePath", "file_path", "path")


def _value(v):
    """Antigravity stores string arguments JSON-quoted ('"/a/b"'): unwrap them."""
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except Exception:
            pass
    return v


class AntigravityAdapter(Adapter):
    name, label, root_env, version = "antigravity", "Antigravity", "SESSION_CELLS_ANTIGRAVITY_ROOT", 1

    def default_root(self):
        return os.path.expanduser("~/.gemini/antigravity-cli")

    def discover(self, cut):
        return self.newer(self.glob(f"{self.root()}/brain/*/.system_generated/logs/transcript.jsonl"), cut)

    def _cwds(self):
        try:
            with open(os.path.join(self.root(), "cache", "last_conversations.json")) as fh:
                return {v: k for k, v in json.load(fh).items()}
        except Exception:
            return {}

    def parse(self, path):
        res = new_result()
        sid = path.split(os.sep)[-4]
        cwd = self._cwds().get(sid, "")
        for d in read_jsonl(path):
            t = ts(d.get("created_at", ""))
            if not t:
                continue
            touch(res, sid, t, self.name, cwd)
            kind, mid = d.get("type"), f"{sid}:{d.get('step_index')}"
            if kind == "USER_INPUT" and len(res["prompts"]) < 40:
                text = str(d.get("content") or "").replace("<USER_REQUEST>", " ").replace("</USER_REQUEST>", " ")
                res["prompts"].append((sid, t, text[:3000]))
            elif kind == "PLANNER_RESPONSE":
                events = []
                for call in d.get("tool_calls") or []:
                    name, args = call.get("name") or "", call.get("args") or {}
                    path_ = next((_value(args[k]) for k in PATH_KEYS if k in args), None)
                    if isinstance(path_, str) and path_:
                        if name in WRITE_TOOLS:
                            events.append(("w", path_, t))
                        elif name in READ_TOOLS:
                            events.append(("r", path_, t))
                    if "subagent" in name:
                        res["subs"].append((sid, f"{mid}:{name}", t))
                add_msg(res, mid, sid, t, d.get("output_tokens") or 0, d.get("input_tokens") or 0,
                        d.get("cache_read_tokens") or 0, events)
        return res
