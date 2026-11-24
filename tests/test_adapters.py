import os

from agent_dish.adapters import ADAPTERS
from tests.conftest import NOW

CUT = NOW - 30 * 86400


def parse_all(name):
    a = ADAPTERS[name]
    files = a.discover(CUT)
    assert files, f"{name}: nothing discovered"
    return [a.parse(f) for f in files]


def test_claude_tokens_events_and_subagent(roots):
    a = ADAPTERS["claude"]
    by_file = {os.path.basename(f): a.parse(f) for f in a.discover(CUT)}
    sa, sb, sub = by_file["A.jsonl"], by_file["B.jsonl"], by_file["agent-1.jsonl"]
    assert sa["msgs"]["m1"]["out"] == 100 and sa["msgs"]["m1"]["inn"] == 10 and sa["msgs"]["m1"]["cache"] == 5
    assert sa["msgs"]["m1"]["events"][0][:2] == ("w", "/w/a.py")
    assert any(p[2].startswith("please review") for p in sa["prompts"])
    assert sb["msgs"]["m3"]["events"][0][:2] == ("r", "/w/a.py")
    assert sa["nodes"]["A"]["branch"] == "feature-weekly-report" and sa["nodes"]["A"]["agent"] == "claude"
    assert sub["nodes"]["A"] and [s[0] for s in sub["subs"]] == ["A"]  # a sub-agent file belongs to its parent session


def test_kiro_estimates_tokens_ignores_bookkeeping_and_counts_subagents(roots):
    [r] = parse_all("kiro")
    assert r["nodes"]["sess_k1"]["cwd"] == "/home/u/repos/proj/y" and ADAPTERS["kiro"].tokens_estimated
    assert r["msgs"]["r2"]["out"] == 100  # 400 chars / 4
    assert r["msgs"]["r3"]["events"][0][:2] == ("w", "/w/a.py")
    assert "r5" not in r["msgs"]  # tool_load is housekeeping
    assert [s[1] for s in r["subs"]] == ["r4"]
    assert any("weekly report" in p[2] for p in r["prompts"])  # the session title feeds theme naming


def test_antigravity_tokens_paths_and_cwd(roots):
    [r] = parse_all("antigravity")
    m = r["msgs"]["uuid-1:1"]
    assert (m["out"], m["inn"], m["cache"]) == (120, 900, 30)
    assert m["events"][0][:2] == ("w", "/w/b.py")  # the JSON-quoted argument is unwrapped
    assert r["nodes"]["uuid-1"]["cwd"] == "/home/u/repos/proj/z"
    assert "USER_REQUEST" not in r["prompts"][0][2]


def test_codex_patch_and_token_deltas(roots):
    [r] = parse_all("codex")
    assert "cdx-1" in r["nodes"] and r["nodes"]["cdx-1"]["branch"] == "main"
    assert sum(m["out"] for m in r["msgs"].values()) == 130  # the counter is cumulative: deltas add back up
    assert any(e[:2] == ("w", "/w/c.py") for m in r["msgs"].values() for e in m["events"])
    assert ADAPTERS["codex"].experimental


def test_missing_roots_find_nothing(monkeypatch, tmp_path):
    for a in ADAPTERS.values():
        monkeypatch.setenv(a.root_env, str(tmp_path / "nope"))
        assert a.discover(0) == []


def test_cowork_reads_desktop_agent_sessions_with_the_claude_parser(roots):
    [r] = parse_all("cowork")
    assert r["nodes"]["cw1"]["agent"] == "cowork"
    assert r["msgs"]["mc1"]["out"] == 300 and r["msgs"]["mc1"]["events"][0][:2] == ("w", "/w/summary.md")
    assert "quarterly summary" in r["prompts"][0][2]


def test_gemini_tokens_thoughts_and_tool_paths(roots):
    [r] = parse_all("gemini")
    m = r["msgs"]["g1"]
    assert (m["out"], m["inn"], m["cache"]) == (100, 700, 10)  # output includes thinking tokens
    assert [e[:2] for e in m["events"]] == [("w", "/w/d.py"), ("r", "/w/a.py")]
    assert r["prompts"][0][2].startswith("explain the weekly")
    assert ADAPTERS["gemini"].experimental
