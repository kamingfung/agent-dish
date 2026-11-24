"""agent-dish command line: build a snapshot, or serve the live dish."""

import argparse
import calendar
import http.server
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from importlib import resources

from . import __version__
from .adapters import ADAPTERS, selected
from .build import build, data_dir
from .themes import DAY


def parse_since(text):
    """YYYY-MM-DD -> epoch seconds (UTC midnight), or None when empty/invalid."""
    try:
        return calendar.timegm(time.strptime(text, "%Y-%m-%d")) if text else None
    except ValueError:
        raise SystemExit(f"--since must look like 2026-10-01, got '{text}'") from None


# "DISH" on a phone keypad: the primary port, so bookmarks and the page's saved choices (kept per address) stay put
DEFAULT_PORT = 3474


def bind(host, port, handler):
    """Serve on `port`; if it is taken, fall back to a random free port and say so. Port 0 asks for a random one.

    Returns (server, note). The primary port is stable; the fallback only happens when something else, or another
    agent-dish, already holds it."""
    try:
        return http.server.ThreadingHTTPServer((host, port), handler), None
    except OSError:
        if port == 0:
            raise
        server = http.server.ThreadingHTTPServer((host, 0), handler)
        return server, f"port {port} is busy (is agent-dish already running there?), using {server.server_address[1]}"


def render(graph):
    html = resources.files("agent_dish").joinpath("web/template.html").read_text(encoding="utf-8")
    return html.replace("/*DATA*/null", json.dumps(graph, separators=(",", ":")).replace("</", "<\\/"))


def newest(adapters, days):
    cut = time.time() - days * DAY
    m = 0
    for a in adapters:
        for f in a.discover(cut):
            try:
                m = max(m, os.path.getmtime(f))
            except OSError:
                pass
    return m


def cmd_agents(_):
    print("Agents and where their sessions are read from:")
    for a in ADAPTERS.values():
        root = a.root()
        found = len(a.discover(0)) if os.path.exists(root) else 0
        flag = " (experimental)" if a.experimental else ""
        print(
            f"  {a.name:12} {a.label}{flag}: {root}  [{found} transcripts]"
            if found
            else f"  {a.name:12} {a.label}{flag}: {root}  [not found]"
        )


def cmd_build(args):
    out = os.path.abspath(args.out or ".")
    os.makedirs(out, exist_ok=True)
    graph = build(args.days, args.agents, data_dir(), since=parse_since(args.since))
    path = os.path.join(out, "agent-dish.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(graph))
    print(f"wrote {path} (a snapshot; use `agent-dish serve` for live updates)")
    if args.open:
        webbrowser.open("file://" + path)


def cmd_demo(args):
    from .demo import demo_graph

    end = parse_since(args.end) if args.end else None
    graph = demo_graph(args.days, end, args.seed)
    out = os.path.abspath(args.out or ".")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "agent-dish-demo.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(graph))
    print(f"wrote {path}: invented sessions, nothing from your machine")
    if args.open:
        webbrowser.open("file://" + path)


def cmd_serve(args):
    adapters, home = selected(args.agents), data_dir()
    state = dict(since=parse_since(args.since))
    state["graph"] = build(args.days, args.agents, home, since=state["since"])

    def watch():
        seen = newest(adapters, args.days)
        while True:
            time.sleep(5)
            n = newest(adapters, args.days)
            if n != seen:  # something was written: re-read only the transcripts that changed
                seen = n
                state["graph"] = build(args.days, args.agents, home, log=lambda *_: None, since=state["since"])

    threading.Thread(target=watch, daemon=True).start()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path == "/graph.json":
                asked = urllib.parse.parse_qs(url.query).get("since", [""])[0]
                try:
                    since = parse_since(asked)
                except SystemExit:
                    since = None
                if (
                    since and since != state["since"]
                ):  # someone picked another start date: rebuild from it (cached, so quick)
                    state["since"] = since
                    state["graph"] = build(args.days, args.agents, home, log=lambda *_: None, since=since)
                body, kind = json.dumps(state["graph"]).encode(), "application/json"
            elif url.path in ("/", "/index.html"):
                body, kind = render(state["graph"]).encode(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server, note = bind(args.host, args.port, Handler)
    if note:
        print(note, flush=True)
    url = f"http://{args.host}:{server.server_address[1]}/"
    print(
        f"agent-dish live at {url}  (agents: {', '.join(a.name for a in adapters)}; "
        f"last {args.days} days; Ctrl+C to stop)",
        flush=True,  # a piped or redirected run must still show where the dish is
    )
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="agent-dish", description="Your AI coding-agent sessions as living cells in a petri dish."
    )
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--days", type=int, default=30, help="how far back to look (default 30)")
    common.add_argument("--since", metavar="YYYY-MM-DD", help="start from this date instead (wins over --days)")
    common.add_argument("--agents", default="all", help="comma-separated: " + ",".join(ADAPTERS) + " (default all)")
    common.add_argument("--open", action="store_true", help="open the result in your browser")
    b = sub.add_parser("build", parents=[common], help="write a one-file HTML snapshot")
    b.add_argument("--out", help="folder for agent-dish.html (default: current folder)")
    b.set_defaults(fn=cmd_build)
    s = sub.add_parser("serve", parents=[common], help="serve the live dish and keep it updating")
    s.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"primary port (default {DEFAULT_PORT}); a random free one is used if it is busy",
    )
    s.add_argument("--host", default="127.0.0.1")
    s.set_defaults(fn=cmd_serve)
    d = sub.add_parser("demo", help="a dish of invented sessions, to try it before you have any history")
    d.add_argument("--days", type=int, default=30)
    d.add_argument("--seed", type=int, default=7, help="same seed, same dish")
    d.add_argument("--end", metavar="YYYY-MM-DD", help="pin the last day (default: now)")
    d.add_argument("--out", help="folder for agent-dish-demo.html (default: current folder)")
    d.add_argument("--open", action="store_true")
    d.set_defaults(fn=cmd_demo)
    a = sub.add_parser("agents", help="show which agents' sessions were found on this machine")
    a.set_defaults(fn=cmd_agents)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
