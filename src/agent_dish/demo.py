"""Invented sessions, so you can try agent-dish before you have any history of your own.

Everything here is made up: projects, branches, colony names and numbers. The same seed always gives the same dish.
"""

import math
import random
import time

from .themes import DAY

AGENTS = ("claude", "cowork", "kiro", "antigravity", "gemini", "codex")  # the order of the weights below

# key, project, (agent weights), first day, last day, sessions, how the colony's title drifts: (day, title)
COLONIES = [
    ("login flow", "web-app", (6, 0, 2, 1, 1, 1), 0, 11, 16, [(6, "oauth tokens"), (10, "session cookies")]),
    (
        "data pipeline",
        "analytics",
        (4, 0, 5, 1, 1, 1),
        0,
        30,
        26,
        [(7, "schema drift"), (14, "backfill job"), (23, "partition costs")],
    ),
    ("checkout api", "web-app", (5, 0, 2, 2, 1, 2), 3, 21, 20, [(8, "payment retries"), (15, "refund webhook")]),
    ("flaky tests", "web-app", (3, 0, 4, 1, 1, 1), 8, 19, 12, [(13, "ci runners"), (17, "test fixtures")]),
    ("docs rewrite", "docs", (2, 5, 4, 1, 1, 0), 12, 27, 14, [(19, "api reference"), (24, "quickstart guide")]),
    ("mobile release", "mobile-app", (5, 0, 2, 1, 2, 3), 16, 30, 16, [(22, "app store review"), (27, "crash fixes")]),
    ("billing report", "analytics", (3, 3, 2, 1, 1, 2), 21, 30, 10, [(26, "invoice export")]),
]
ADJ = [
    "amber",
    "brisk",
    "calm",
    "daring",
    "eager",
    "fuzzy",
    "gentle",
    "hasty",
    "ivory",
    "jolly",
    "keen",
    "lively",
    "mellow",
    "nimble",
    "opal",
    "plucky",
    "quiet",
    "rustic",
    "sunny",
    "tidy",
    "umber",
    "vivid",
    "witty",
    "zesty",
]
VERB = [
    "building",
    "chasing",
    "drafting",
    "fixing",
    "hatching",
    "mapping",
    "nudging",
    "pruning",
    "racing",
    "sorting",
    "tracing",
    "trimming",
    "weaving",
]
NOUN = [
    "badger",
    "comet",
    "dahlia",
    "ember",
    "falcon",
    "garnet",
    "harbor",
    "iris",
    "juniper",
    "kestrel",
    "lantern",
    "meadow",
    "nectar",
    "orchid",
    "pebble",
    "quartz",
    "river",
    "thicket",
    "willow",
]
FILES = {  # what each colony's sessions write, so hand-offs read plausibly
    "login flow": ["src/auth/login.py", "src/auth/tokens.py", "src/auth/session.py", "tests/test_login.py"],
    "data pipeline": ["pipelines/ingest.py", "pipelines/schema.yaml", "pipelines/backfill.sql", "tests/test_ingest.py"],
    "checkout api": ["src/api/checkout.py", "src/api/payments.py", "src/api/refunds.py", "tests/test_checkout.py"],
    "flaky tests": ["tests/test_flaky.py", "ci/runner.yaml", "tests/conftest.py", "ci/retry.sh"],
    "docs rewrite": ["docs/quickstart.md", "docs/api.md", "docs/concepts.md", "docs/index.md"],
    "mobile release": ["app/release_notes.md", "app/build.gradle", "app/store_listing.md", "app/Info.plist"],
    "billing report": ["reports/billing.sql", "reports/invoice.py", "reports/summary.md"],
    "unthemed": ["notes.md", "scratch.py", "TODO.md"],
}


def pick(rng, weights):
    return rng.choices(AGENTS, weights=weights)[0]


def curve(rng, start, end, total, points=30):
    """Cumulative output tokens over the session: bursts of work with pauses."""
    steps = sorted(rng.uniform(start, end) for _ in range(points))
    weights = [rng.random() ** 2.2 + 0.02 for _ in steps]
    scale = total / sum(weights)
    out, cum = [], 0.0
    for t, w in zip(steps, weights):
        cum += w * scale
        out.append([round(t), round(cum)])
    out[-1][1] = total
    return out


def demo_graph(days=30, end=None, seed=7):
    rng = random.Random(seed)
    end = end or time.time()
    cut = end - days * DAY
    first_day = int(cut // DAY)
    used, nodes, by_colony = set(), [], {}

    def label():
        while True:
            s = f"{rng.choice(ADJ)}-{rng.choice(VERB)}-{rng.choice(NOUN)}"
            if s not in used:
                used.add(s)
                return s

    def session(theme, project, agent, start, tokens, branch):
        dur = min(end - start, math.exp(rng.gauss(math.log(75 * 60), 0.9)))
        stop = max(start + 600, start + dur)
        total = max(1500, int(tokens))
        divs = sorted(
            round(rng.uniform(start, stop)) for _ in range(rng.choice([0, 0, 0, 1, 2, 3, 5]) if agent != "codex" else 0)
        )
        node = dict(
            id=f"{agent[:2]}-{len(nodes):03d}",
            label=label(),
            project=project,
            branch=branch,
            agent=agent,
            start=round(start),
            end=round(stop),
            out=total,
            inn=total * 3,
            cache=total * 40,
            subs=len(divs),
            est=agent == "kiro",
            curve=curve(rng, start, stop, total),
            divs=divs,
            kids=0,
            theme=theme,
        )
        nodes.append(node)
        return node

    names = {}
    for key, project, weights, d0, d1, n, drift in COLONIES:
        lo, hi = cut + d0 * DAY, min(end, cut + d1 * DAY)
        members = [
            session(
                key,
                project,
                pick(rng, weights),
                rng.uniform(lo, hi),
                math.exp(rng.gauss(math.log(55000), 1.0)),
                "feature/" + key.replace(" ", "-"),
            )
            for _ in range(n)
        ]
        by_colony[key] = sorted(members, key=lambda m: m["start"])
        names[key] = [[first_day * DAY, key]] + [[(first_day + d) * DAY, name] for d, name in drift]
    for _ in range(46):  # sessions with no recurring phrase
        session(
            "unthemed",
            rng.choice(["web-app", "analytics", "docs", "scratch"]),
            pick(rng, (5, 1, 5, 1, 1, 1)),
            rng.uniform(cut, end),
            math.exp(rng.gauss(math.log(9000), 0.9)),
            "main",
        )

    edges, seen = [], set()

    def link(a, b):
        if a["id"] == b["id"] or (a["id"], b["id"]) in seen or b["start"] <= a["start"]:
            return
        seen.add((a["id"], b["id"]))
        edges.append(
            dict(
                a=a["id"],
                b=b["id"],
                n=rng.randint(1, 4),
                t=round(b["start"] + rng.uniform(60, 900)),
                paths=rng.sample(FILES[a["theme"]], rng.randint(1, min(3, len(FILES[a["theme"]])))),
            )
        )

    for members in by_colony.values():
        for i, b in enumerate(members[1:], 1):
            if rng.random() < 0.45:
                link(members[max(0, i - 1 - int(rng.random() ** 2 * 5))], b)
    allm = sorted((m for ms in by_colony.values() for m in ms), key=lambda m: m["start"])
    for _ in range(9):  # a few hand-offs across colonies
        link(*sorted(rng.sample(allm, 2), key=lambda m: m["start"]))
    by_id = {n["id"]: n for n in nodes}
    for e in edges:
        by_id[e["a"]]["kids"] += 1
    return dict(
        days=days,
        since=cut,
        generated=end,
        demo=True,
        agents=sorted({n["agent"] for n in nodes}),
        nodes=nodes,
        edges=edges,
        colonyNames=names,
    )
