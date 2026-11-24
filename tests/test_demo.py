import json

from agent_dish.cli import render
from agent_dish.demo import AGENTS, demo_graph
from agent_dish.themes import DAY

END = 1_795_219_200


def test_same_seed_same_dish_and_different_seed_differs():
    assert demo_graph(30, END, 7) == demo_graph(30, END, 7)
    assert demo_graph(30, END, 7) != demo_graph(30, END, 8)


def test_demo_is_well_formed_and_uses_every_agent():
    g = demo_graph(30, END, 7)
    ids = {n["id"] for n in g["nodes"]}
    assert len(ids) == len(g["nodes"]) and g["demo"] is True
    assert {n["agent"] for n in g["nodes"]} == set(AGENTS)
    assert all(e["a"] in ids and e["b"] in ids and e["a"] != e["b"] for e in g["edges"])
    for n in g["nodes"]:
        assert n["start"] < n["end"] and n["curve"][-1][1] == n["out"]
        assert [p[1] for p in n["curve"]] == sorted(p[1] for p in n["curve"])      # tokens only grow
        assert g["since"] <= n["start"] and n["end"] <= END
    for key, names in g["colonyNames"].items():
        assert names[0][1] == key and [d for d, _ in names] == sorted(d for d, _ in names)
        assert all(b[0] - a[0] >= 3 * DAY for a, b in zip(names, names[1:]))        # titles drift slowly


def test_hand_off_file_names_fit_their_colony():
    g = demo_graph(30, END, 7)
    by = {n["id"]: n for n in g["nodes"]}
    for e in g["edges"]:
        if by[e["a"]]["theme"] == "docs rewrite":
            assert all(p.startswith("docs/") for p in e["paths"])


def test_demo_renders_with_the_demo_banner():
    html = render(demo_graph(30, END, 7))
    assert json.loads(html.split("let DATA = ")[1].split(";\nlet N")[0])["demo"] is True
    assert "DEMO: invented sessions" in html
