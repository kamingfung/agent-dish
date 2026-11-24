"""Synthetic transcripts for each agent, written under a temp dir. No real session data is ever used."""
import json
import os
import time
from datetime import datetime, timezone

import pytest

NOW = 1_800_000_000.0  # a fixed "now" so windows are deterministic


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    os.utime(path, (NOW - 60, NOW - 60))


@pytest.fixture
def roots(tmp_path, monkeypatch):
    """Claude: A writes /w/a.py, B reads it later. Kiro, Antigravity, Codex: one session each."""
    d = NOW - 3 * 86400
    claude = tmp_path / "claude"
    def cmsg(sid, t, mid, out, tool=None, **inp):
        content = [dict(type="tool_use", name=tool, input=inp)] if tool else []
        return dict(type="assistant", sessionId=sid, timestamp=iso(t), cwd="/home/u/repos/proj/x", gitBranch="feature-weekly-report",
                    message=dict(id=mid, usage=dict(output_tokens=out, input_tokens=10, cache_read_input_tokens=5), content=content))
    write_jsonl(str(claude / "-proj" / "A.jsonl"), [
        dict(type="user", sessionId="A", timestamp=iso(d), message=dict(content="please review the weekly report report")),
        cmsg("A", d + 10, "m1", 100, "Write", file_path="/w/a.py"),
        cmsg("A", d + 20, "m2", 50),
    ])
    write_jsonl(str(claude / "-proj" / "B.jsonl"), [cmsg("B", d + 500, "m3", 70, "Read", file_path="/w/a.py")])
    write_jsonl(str(claude / "-proj" / "A" / "subagents" / "agent-1.jsonl"), [cmsg("A", d + 15, "m4", 5)])
    monkeypatch.setenv("AGENT_DISH_CLAUDE_ROOT", str(claude))

    kiro = tmp_path / "kiro"
    k = str(kiro / "hash1" / "sess_k1")
    os.makedirs(k)
    json.dump(dict(workspacePaths=["/home/u/repos/proj/y"], title="Fix the weekly report pipeline"), open(k + "/session.json", "w"))
    write_jsonl(k + "/messages.jsonl", [
        dict(id="r1", timestamp=iso(d + 30), payload=dict(type="user", content="fix the pipeline")),
        dict(id="r2", timestamp=iso(d + 31), payload=dict(type="assistant", operationType="Say", content="x" * 400)),
        dict(id="r3", timestamp=iso(d + 32), payload=dict(type="tool_call", toolName="str_replace", args=dict(path="/w/a.py"))),
        dict(id="r4", timestamp=iso(d + 33), payload=dict(type="tool_call", toolName="invoke_sub_agent", args={})),
        dict(id="r5", timestamp=iso(d + 34), payload=dict(type="tool_call", toolName="tool_load", args={})),
    ])
    monkeypatch.setenv("AGENT_DISH_KIRO_ROOT", str(kiro))

    agy = tmp_path / "agy"
    write_jsonl(str(agy / "brain" / "uuid-1" / ".system_generated" / "logs" / "transcript.jsonl"), [
        dict(step_index=0, type="USER_INPUT", created_at=iso(d + 40), content="<USER_REQUEST>review weekly report</USER_REQUEST>"),
        dict(step_index=1, type="PLANNER_RESPONSE", created_at=iso(d + 41), input_tokens=900, output_tokens=120, cache_read_tokens=30,
             tool_calls=[dict(name="write_to_file", args=dict(TargetFile='"/w/b.py"'))]),
    ])
    os.makedirs(agy / "cache")
    json.dump({"/home/u/repos/proj/z": "uuid-1"}, open(agy / "cache" / "last_conversations.json", "w"))
    monkeypatch.setenv("AGENT_DISH_ANTIGRAVITY_ROOT", str(agy))

    codex = tmp_path / "codex"
    write_jsonl(str(codex / "2026" / "10" / "01" / "rollout-2026-10-01T00-00-00-cdx-1.jsonl"), [
        dict(timestamp=iso(d + 50), type="session_meta", payload=dict(id="cdx-1", cwd="/home/u/repos/proj/w", git=dict(branch="main"))),
        dict(timestamp=iso(d + 51), type="response_item", payload=dict(type="message", role="user", content=[dict(type="input_text", text="add weekly report")])),
        dict(timestamp=iso(d + 52), type="response_item", payload=dict(type="function_call", name="apply_patch", arguments="*** Add File: /w/c.py\n+x")),
        dict(timestamp=iso(d + 53), type="event_msg", payload=dict(type="token_count", info=dict(total_token_usage=dict(input_tokens=500, output_tokens=80, cached_input_tokens=20)))),
        dict(timestamp=iso(d + 54), type="event_msg", payload=dict(type="token_count", info=dict(total_token_usage=dict(input_tokens=900, output_tokens=130, cached_input_tokens=40)))),
    ])
    monkeypatch.setenv("AGENT_DISH_CODEX_ROOT", str(codex))
    cow = tmp_path / "cowork"
    write_jsonl(str(cow / "org" / "user" / "local_cw1" / ".claude" / "projects" / "-out" / "cw1.jsonl"), [
        dict(type="user", sessionId="cw1", timestamp=iso(d + 60), message=dict(content="draft the quarterly summary")),
        cmsg("cw1", d + 61, "mc1", 300, "Write", file_path="/w/summary.md"),
    ])
    monkeypatch.setenv("AGENT_DISH_COWORK_ROOT", str(cow))

    gem = tmp_path / "gemini"
    gp = gem / "hash1" / "chats"
    os.makedirs(gp)
    json.dump(dict(sessionId="gem-1", projectHash="hash1", startTime=iso(d + 70), messages=[
        dict(id="g0", timestamp=iso(d + 70), type="user", content="explain the weekly report job"),
        dict(id="g1", timestamp=iso(d + 71), type="gemini", content="ok", tokens=dict(input=700, output=90, cached=10, thoughts=10, tool=0, total=810),
             toolCalls=[dict(name="write_file", args=dict(file_path="/w/d.py")), dict(name="read_file", args=dict(absolute_path="/w/a.py"))]),
    ]), open(gp / "session-2026-10-01T00-00-gem1.json", "w"))
    os.utime(gp / "session-2026-10-01T00-00-gem1.json", (NOW - 60, NOW - 60))
    monkeypatch.setenv("AGENT_DISH_GEMINI_ROOT", str(gem))
    monkeypatch.setenv("AGENT_DISH_HOME", str(tmp_path / "home"))
    return tmp_path
