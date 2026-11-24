import json

from agent_dish.build import build
from agent_dish.cli import parse_since, render
from tests.conftest import NOW


def test_build_end_to_end(roots):
    g = build(days=30, agents="all", now=NOW, log=lambda *_: None)
    by = {n["id"]: n for n in g["nodes"]}
    assert set(by) == {"A", "B", "sess_k1", "uuid-1", "cdx-1", "cw1", "gem-1"}
    assert {n["agent"] for n in g["nodes"]} == {"claude", "cowork", "kiro", "antigravity", "gemini", "codex"}
    assert by["A"]["out"] == 155 and by["A"]["subs"] == 1  # sub-agent tokens fold into the parent
    assert by["sess_k1"]["est"] and not by["A"]["est"]
    assert g["agents"] == ["antigravity", "claude", "codex", "cowork", "gemini", "kiro"]
    # B read a file A wrote, and the Kiro session edited it: hand-offs A -> B and A -> Kiro (edits count too)
    assert sorted((e["a"], e["b"]) for e in g["edges"] if e["a"] == "A") == [
        ("A", "B"),
        ("A", "gem-1"),
        ("A", "sess_k1"),
    ]
    assert by["A"]["kids"] == 3 and by["B"]["kids"] == 0
    assert all(set(n) >= {"curve", "divs", "theme", "label", "project", "start", "end"} for n in g["nodes"])
    assert by["A"]["curve"][-1][1] == 155  # cumulative tokens end at the total


def test_since_beats_days_and_filters_old_sessions(roots):
    g = build(days=30, agents="claude", now=NOW, since=NOW - 3 * 86400 + 400, log=lambda *_: None)
    assert {n["id"] for n in g["nodes"]} == {"B"}  # A's activity ended before the start date
    assert g["since"] == NOW - 3 * 86400 + 400


def test_agent_selection(roots):
    g = build(days=30, agents="kiro,codex", now=NOW, log=lambda *_: None)
    assert {n["agent"] for n in g["nodes"]} == {"kiro", "codex"}


def test_second_build_reads_from_cache(roots):
    logs = []
    build(days=30, now=NOW, log=logs.append)
    build(days=30, now=NOW, log=logs.append)
    assert "0 read" in logs[-1]


def test_render_embeds_data_safely(roots):
    g = build(days=30, now=NOW, log=lambda *_: None)
    g["nodes"][0]["label"] = "</script><b>x"
    html = render(g)
    assert "</script><b>x" not in html and "<\\/script>" in html
    assert json.loads(html.split("let DATA = ")[1].split(";\nlet N")[0].replace("<\\/", "</"))["days"] == 30


def test_parse_since():
    assert parse_since("2026-10-01") == 1_790_812_800
    assert parse_since(None) is None
