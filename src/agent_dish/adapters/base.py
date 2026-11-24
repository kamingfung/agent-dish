"""The adapter contract.

An adapter teaches agent-dish one agent. It finds that agent's transcript files and turns one file
into a ParseResult: plain dicts and tuples, independent of any time window, so results can be cached.

    nodes   {session_id: dict(lo, hi, cwd, branch, slug, agent)}   first/last timestamp, where it ran
    msgs    {message_id: dict(sid, t, out, inn, cache, events)}    token counts per model message
                         events = [(kind, path, t)], kind 'w' (wrote a file) or 'r' (read one)
    edges   [(session_id, other_session_id, t)]                    a message sent to another session
    subs    [(session_id, key, t)]                                 a sub-agent started (a "division")
    prompts [(session_id, t, text)]                                text a person wrote, for theme naming

Everything an adapter does not know is simply left out. Timestamps are epoch seconds.
"""
import glob
import json
import os
from datetime import datetime


def ts(value):
    """ISO-8601 string (or epoch number) -> epoch seconds; 0 when unreadable."""
    if isinstance(value, (int, float)):
        return float(value) / (1000.0 if value > 1e11 else 1.0)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def new_result():
    return dict(nodes={}, msgs={}, edges=[], subs=[], prompts=[])


def touch(result, sid, t, agent, cwd="", branch="", slug=""):
    """Record that session `sid` was alive at time `t`."""
    n = result["nodes"].setdefault(sid, dict(lo=t, hi=t, cwd="", branch="", slug="", agent=agent))
    n["lo"], n["hi"] = min(n["lo"], t), max(n["hi"], t)
    n["cwd"] = n["cwd"] or cwd or ""
    n["branch"] = n["branch"] or branch or ""
    n["slug"] = slug or n["slug"]
    return n


def add_msg(result, mid, sid, t, out=0, inn=0, cache=0, events=()):
    m = result["msgs"].setdefault(mid, dict(sid=sid, t=t, out=0, inn=0, cache=0, events=[]))
    m["out"], m["inn"], m["cache"] = max(m["out"], out), max(m["inn"], inn), max(m["cache"], cache)
    m["events"].extend(events)
    return m


def read_jsonl(path):
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if isinstance(d, dict):
                yield d


class Adapter:
    name = ""            # short id used on the command line and in graph.json
    label = ""           # human name
    version = 1          # bump when parse() output changes: invalidates the cache
    experimental = False  # True = written from the format's docs, not yet checked against real data
    tokens_estimated = False  # True = the agent does not report tokens; counts are chars / 4
    root_env = ""        # environment variable that overrides the transcript root

    def root(self):
        return os.environ.get(self.root_env) or self.default_root()

    def default_root(self):
        raise NotImplementedError

    def discover(self, cut):
        """Transcript files modified after epoch time `cut`."""
        raise NotImplementedError

    def parse(self, path):
        raise NotImplementedError

    @staticmethod
    def newer(paths, cut):
        out = []
        for p in paths:
            try:
                if os.path.getmtime(p) > cut:
                    out.append(p)
            except OSError:
                pass
        return out

    @staticmethod
    def glob(pattern):
        return glob.glob(pattern, recursive=True)
