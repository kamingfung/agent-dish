"""The colony-home layout is JavaScript in the page, so these tests run that block under node (skipped without node)."""

import json
import pathlib
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "src" / "agent_dish" / "web" / "template.html"
HARNESS = """
const code = %s;
const colonies = %s;
const make = n => { const REAL = []; let t = 1000;
  for (const [name, count] of n) for (let i = 0; i < count; i++)
    REAL.push({ id: name + i, theme: name, start: t += 10 });
  return REAL; };
const REAL = make(colonies.first);
const api = new Function('REAL', code + '; return { placeHomes, homes };')(REAL);
api.placeHomes();
const before = JSON.stringify([...api.homes]);
const out = { before: JSON.parse(before) };
if (colonies.later) {
  for (const x of make(colonies.later)) REAL.push(x);
  api.placeHomes(); out.after = [...api.homes];
}
console.log(JSON.stringify(out));
"""


def run(first, later=None):
    text = TEMPLATE.read_text(encoding="utf-8")
    code = text.split("// HOMES-BEGIN", 1)[1].split("// HOMES-END", 1)[0]
    script = HARNESS % (json.dumps(code), json.dumps({"first": first, "later": later}))
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout  # noqa: S603, S607
    return json.loads(out)


COLONIES = [[f"colony {c}", 6 + 3 * i] for i, c in enumerate("abcdefgh")]


def test_homes_are_the_same_every_time():
    assert run(COLONIES)["before"] == run(COLONIES)["before"]


def test_a_later_colony_never_moves_the_ones_already_there():
    out = run(COLONIES, later=[["colony late", 9]])
    before = dict(out["before"])
    after = dict(out["after"])
    assert "colony late" in after and "colony late" not in before
    assert all(after[k] == v for k, v in before.items())


def test_colonies_keep_clear_of_each_other_and_stay_in_the_dish():
    homes = dict(run(COLONIES)["before"])
    sizes = dict(COLONIES)
    names = list(homes)
    for i, a in enumerate(names):
        ha = homes[a]
        assert (ha["u"] ** 2 + ha["v"] ** 2) ** 0.5 <= 0.9
        for b in names[i + 1 :]:
            hb = homes[b]
            gap = ((ha["u"] - hb["u"]) ** 2 + (ha["v"] - hb["v"]) ** 2) ** 0.5
            ra, rb = (12 * (sizes[a] + 0.6) ** 0.5 + 8) / 400, (12 * (sizes[b] + 0.6) ** 0.5 + 8) / 400
            assert gap >= ra + rb, (a, b)
