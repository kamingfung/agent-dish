"""Turn agent transcripts into graph.json: one cell per session, plus the data the dish animates."""
import collections
import hashlib
import json
import os
import pickle
import time

from .adapters import selected
from .themes import DAY, colony_names, path_terms, terms, themes_for


def data_dir():
    d = os.environ.get("AGENT_DISH_HOME") or os.path.expanduser("~/.cache/agent-dish")
    os.makedirs(d, exist_ok=True)
    return d


def project_of(cwd):
    parts = cwd.split("/repos/", 1)
    return parts[1].split("/")[0] if len(parts) == 2 else (os.path.basename(cwd.rstrip("/")) or "other")


def cached_parse(adapter, path, cache_dir):
    """Parse one transcript once per (mtime, size): a live refresh only re-reads what changed."""
    st = os.stat(path)
    key = hashlib.md5(f"{adapter.name}|{adapter.version}|{path}|{st.st_mtime_ns}|{st.st_size}".encode()).hexdigest()
    cp = os.path.join(cache_dir, key + ".pkl")
    try:
        with open(cp, "rb") as fh:
            return pickle.load(fh), False
    except Exception:
        pass
    result = adapter.parse(path)
    os.makedirs(cache_dir, exist_ok=True)
    with open(cp + ".tmp", "wb") as fh:
        pickle.dump(result, fh)
    os.replace(cp + ".tmp", cp)
    return result, True


def curve(points):
    """Cumulative output tokens over time, at most ~60 points."""
    points.sort()
    cum, out = 0, []
    for t, o in points:
        cum += o
        out.append([round(t), cum])
    step = max(1, len(out) // 60)
    return out[::step] + ([out[-1]] if out and (len(out) - 1) % step else [])


def build(days=30, agents="all", out_dir=None, now=None, log=print, since=None):
    """`since` (epoch seconds) wins over `days`: the window starts there."""
    now = now or time.time()
    cut = since if since else now - days * DAY
    days = max(1, round((now - cut) / DAY))
    out_dir = out_dir or data_dir()
    cache_dir = os.path.join(out_dir, "cache")
    t0, fresh_files, total_files = time.time(), 0, 0

    S, msgs, by_day, sub_starts = {}, {}, collections.defaultdict(lambda: collections.defaultdict(collections.Counter)), []
    est = {}
    for adapter in selected(agents):
        files = adapter.discover(cut)
        total_files += len(files)
        if adapter.experimental and files:
            log(f"note: {adapter.label} support is experimental (written from the format's docs, not checked against real data)")
        for f in files:
            r, fresh = cached_parse(adapter, f, cache_dir)
            fresh_files += fresh
            for sid, n in r["nodes"].items():
                if n["hi"] < cut:
                    continue
                s = S.setdefault(sid, dict(id=sid, label=sid[:8], project="?", branch="", agent=n["agent"], start=n["lo"], end=n["hi"],
                                           out=0, inn=0, cache=0, subs=0, est=adapter.tokens_estimated))
                s["start"], s["end"] = min(s["start"], max(n["lo"], cut)), max(s["end"], n["hi"])
                if n["cwd"] and s["project"] == "?":
                    s["project"] = project_of(n["cwd"])
                s["branch"] = s["branch"] or n["branch"]
                if n["slug"]:
                    s["label"] = n["slug"]
                if n["branch"]:
                    by_day[sid][int(n["lo"] // DAY)] += terms(n["branch"].replace("/", " ").replace("-", " "))
            for sid, key, t in r["subs"]:
                if sid in S and t >= cut:
                    sub_starts.append((sid, (adapter.name, key), t))
            for mid, m in r["msgs"].items():
                if m["t"] < cut or m["sid"] not in S:
                    continue
                cur = msgs.setdefault((adapter.name, mid), dict(sid=m["sid"], t=m["t"], out=0, inn=0, cache=0, events=m["events"]))
                cur["out"], cur["inn"], cur["cache"] = max(cur["out"], m["out"]), max(cur["inn"], m["inn"]), max(cur["cache"], m["cache"])
                if len(m["events"]) > len(cur["events"]):
                    cur["events"] = m["events"]
                for _, p, t in m["events"]:
                    by_day[m["sid"]][int(t // DAY)] += path_terms(p)
            for sid, t, txt in r["prompts"]:
                if t >= cut and sid in S:
                    by_day[sid][int(t // DAY)] += terms(txt)

    growth, events, written = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(set)
    for rec in msgs.values():
        s = S[rec["sid"]]
        s["out"] += rec["out"]; s["inn"] += rec["inn"]; s["cache"] += rec["cache"]
        growth[rec["sid"]].append((rec["t"], rec["out"]))
        for kind, p, t in rec["events"]:
            events[p].append((t, rec["sid"], kind))
            if kind == "w":
                written[rec["sid"]].add(p)

    # hand-off: session A wrote a file, session B (not A) read or edited it later
    hand = collections.defaultdict(lambda: dict(n=0, t=0, paths=collections.Counter()))
    taker = collections.defaultdict(lambda: collections.defaultdict(set))
    for p, evs in events.items():
        evs.sort()
        first_write = {}
        for t, sid, kind in evs:
            if kind == "w":
                first_write.setdefault(sid, t)
        for t, sid, kind in evs:
            for a, tw in first_write.items():
                if a != sid and t > tw:
                    h = hand[(a, sid)]
                    h["n"] += 1; h["paths"][p] += 1
                    h["t"] = min(h["t"] or t, t)
                    taker[a][p].add(sid)

    totals = {sid: sum(days_.values(), collections.Counter()) for sid, days_ in by_day.items() if sid in S}
    theme = themes_for(totals)
    names = colony_names({s: d for s, d in by_day.items() if s in S}, theme, int(cut // DAY), int(now // DAY))

    divs = collections.defaultdict(list)
    for sid, _, t in sub_starts:
        divs[sid].append(round(t))
    nodes = []
    for sid, s in S.items():
        s["theme"] = theme.get(sid, "unthemed")
        s["curve"] = curve(growth[sid])
        s["divs"] = sorted(divs[sid])[:80]
        s["subs"] = len(divs[sid])
        s["kids"] = len({b for p in written[sid] for b in taker[sid].get(p, ())})
        nodes.append(s)
    edges = [dict(a=a, b=b, n=h["n"], t=round(h["t"]), paths=[p for p, _ in h["paths"].most_common(5)])
             for (a, b), h in hand.items() if a in S and b in S]

    graph = dict(days=days, since=cut, generated=now, agents=sorted({n["agent"] for n in nodes}), nodes=nodes, edges=edges, colonyNames=names)
    tmp = os.path.join(out_dir, "graph.json.tmp")
    with open(tmp, "w") as fh:
        json.dump(graph, fh)
    os.replace(tmp, os.path.join(out_dir, "graph.json"))
    themed = collections.Counter(n["theme"] for n in nodes)
    log(f"{total_files} transcripts ({fresh_files} read, {total_files - fresh_files} cached) -> {len(nodes)} sessions, "
        f"{len(edges)} hand-offs, {len(themed) - ('unthemed' in themed)} colonies, {time.time() - t0:.1f}s")
    return graph
