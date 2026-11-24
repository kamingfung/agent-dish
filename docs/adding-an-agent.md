# Adding an agent

An adapter is one file in `src/agent_dish/adapters/`. It finds an agent's transcripts and turns one file into a
plain result. Copy the closest existing adapter (`kiro.py` for a per-session folder, `claude.py` for one file per session).

```python
from .base import Adapter, add_msg, new_result, read_jsonl, touch, ts


class MyAgentAdapter(Adapter):
    name, label = "myagent", "My Agent"
    root_env = "AGENT_DISH_MYAGENT_ROOT"  # lets users and tests point somewhere else
    version = 1  # bump when parse() output changes: invalidates the cache
    experimental = False  # True if not yet checked against real data
    tokens_estimated = False  # True if the agent records no token counts

    def default_root(self):
        return os.path.expanduser("~/.myagent/sessions")

    def discover(self, cut):  # transcript files modified after epoch time `cut`
        return self.newer(self.glob(f"{self.root()}/**/*.jsonl"), cut)

    def parse(self, path):  # one file -> the result below
        res = new_result()
        for d in read_jsonl(path):
            t = ts(d["timestamp"])
            touch(res, session_id, t, self.name, cwd="/where/it/ran", branch="main")
            add_msg(
                res,
                message_id,
                session_id,
                t,
                out=120,
                inn=900,
                cache=30,
                events=[("w", "/path/it/wrote", t), ("r", "/path/it/read", t)],
            )
            res["prompts"].append((session_id, t, "text a person typed"))  # feeds colony names
            res["subs"].append((session_id, sub_agent_key, t))  # a sub-agent started
        return res
```

Then register it in `adapters/__init__.py`. Leave out anything the agent does not record. Add a synthetic fixture to
`tests/conftest.py` and a test in `tests/test_adapters.py`. Never commit real transcripts.

The result fields are documented in `adapters/base.py`.
