"""Name colonies by the phrases their sessions keep using.

Text is the prompts a person typed plus the words in the paths a session touched. Sessions are grouped
into colonies by a greedy keyword cover (a colony is the phrase that covers the most not-yet-covered
sessions), and each colony is then named *per day* from its last few days of text, so the name drifts as
the work does. Prompt text is only read in memory; callers store the chosen phrases, nothing else.
"""

import collections
import datetime
import getpass
import math
import os
import re

STOP = set(  # noqa: C405 (split of one long string, clearer than a set literal)
    [
        "a",
        "about",
        "above",
        "after",
        "again",
        "all",
        "also",
        "am",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "done",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "get",
        "gets",
        "got",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "him",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "just",
        "let",
        "like",
        "make",
        "makes",
        "me",
        "more",
        "most",
        "my",
        "need",
        "needs",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "off",
        "on",
        "once",
        "one",
        "only",
        "or",
        "other",
        "our",
        "out",
        "over",
        "own",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "us",
        "use",
        "used",
        "using",
        "very",
        "want",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
        "yes",
        "ok",
        "okay",
        "please",
        "thanks",
        "thank",
        "can't",
        "don't",
        "it's",
        "i'm",
        "i'd",
        "i've",
        "that's",
        "there's",
        "what's",
        "let's",
        "isn't",
        "doesn't",
        "didn't",
        "won't",
        "also",
        "still",
        "really",
        "actually",
        "maybe",
        "sure",
        "claude",
        "code",
        "file",
        "files",
        "run",
        "running",
        "check",
        "look",
        "looking",
        "see",
        "add",
        "new",
        "set",
        "go",
        "going",
        "take",
        "try",
        "work",
        "working",
        "think",
        "thing",
        "things",
        "way",
        "session",
        "sessions",
        "agent",
        "agents",
        "task",
        "tasks",
        "tool",
        "tools",
        "message",
        "messages",
        "user",
        "assistant",
        "yet",
        "well",
        "next",
        "first",
        "last",
        "http",
        "https",
        "www",
        "com",
        "org",
        "true",
        "false",
        "none",
        "null",
        "name",
        "repo",
        "local",
        "idle",
        "started",
        "background",
        "command",
        "completed",
        "exit",
        "src",
        "py",
        "md",
        "json",
        "yaml",
        "yml",
        "txt",
        "csv",
        "html",
        "python",
        "test",
        "tests",
        "init",
        "utils",
        "users",
        "repos",
        "home",
        "tmp",
        "private",
        "var",
        "folders",
        "library",
        "application",
        "support",
        "nothing",
        "anything",
        "else",
        "previous",
        "conversation",
        "earlier",
        "portion",
        "summary",
        "primary",
        "request",
        "say",
        "whether",
        "png",
        "jpg",
        "image",
        "images",
        "pdf",
        "page",
        "pages",
        "scratchpad",
        "scratch",
        "worktree",
        "worktrees",
        "side-session-notes",
        "side",
        "subagent",
        "type",
        "key",
        "technical",
        "figures",
        "fig",
        "git",
        "show",
        "main",
        "master",
        "develop",
        "dev",
        "feature",
        "feat",
        "fix",
        "fixes",
        "hotfix",
        "release",
        "branch",
        "bugfix",
        "chore",
        "merge",
        "pull",
        "push",
        "commit",
        "origin",
        "upstream",
        "mcp",
        "turn",
        "status",
        "report",
        "tag",
        "read",
        "edit",
        "write",
        "bash",
        "ran",
        "output",
        "result",
        "results",
        "error",
        "update",
        "updated",
        "create",
        "created",
        "kiro",
        "codex",
        "antigravity",
        "gemini",
    ]
)
STOP |= {w.lower() for w in re.split(r"\W+", getpass.getuser()) if w}
STOP |= {w.lower() for w in re.split(r"\W+", os.path.basename(os.path.expanduser("~"))) if w}

TOKEN = re.compile(r"[a-z][a-z\-]{2,24}")
DAY = 86400


def local_day(t):
    """The local calendar day of epoch seconds `t`, as a day number (days since 1970-01-01 in your own time zone).
    Days are cut at local midnight, so a late-evening session counts for the day you lived it."""
    return datetime.datetime.fromtimestamp(t).date().toordinal() - 719163  # 719163 = date(1970, 1, 1).toordinal()


def day_start(d):
    """Epoch seconds of local midnight that starts day number `d` (the inverse of local_day)."""
    return datetime.datetime.combine(datetime.date.fromordinal(d + 719163), datetime.time()).timestamp()


MIN_DAYS_BETWEEN = 3  # a colony keeps its title at least this long
SWITCH_MARGIN = 1.6  # the new title must score this many times the current one


def terms(text):
    """Counter of the words and two-word phrases in `text`."""
    text = re.sub(r"<[^>]+>|https?://\S+|[\w.~-]*/[\w./~-]+|[`*#>|_]+", " ", text.lower())
    words = [w.strip("-") for w in TOKEN.findall(text)]
    words = [w for w in words if not re.fullmatch(r"[a-f\-]{1,8}", w)]  # hex id fragments
    words = [w if w not in STOP and len(w) >= 4 else None for w in words]  # short fragments make poor titles
    out, prev = collections.Counter(), None
    for w in words:
        if w:
            out[w] += 1
            if prev:
                out[prev + " " + w] += 1
        prev = w
    return out


def path_terms(path):
    """Words in the last few folders and the file name: where a session works says what on."""
    return terms(" ".join(path.split("/")[-3:]).replace("_", " ").replace(".", " "))


def themes_for(docs, max_themes=14):
    """docs: session id -> Counter of terms. Returns session id -> colony phrase (greedy keyword cover)."""
    docs = {s: c for s, c in docs.items() if sum(c.values()) >= 8}
    n_docs = len(docs)
    if n_docs < 6:
        return {}
    post = collections.defaultdict(set)
    for s, c in docs.items():
        for term, k in c.items():
            if k >= (1 if " " in term else 2):  # a phrase once is a signal; a lone word needs repeating
                post[term].add(s)

    def idf(term):
        return math.log(n_docs / len(post[term]))

    def boost(term):
        return 2.0 if " " in term else 1.0

    cap = max(0.15 * n_docs, 5)  # not boilerplate every session repeats (but small data sets still need room)
    cand = [t for t, d in post.items() if 3 <= len(d) <= cap]
    cand.sort(key=lambda t: -len(post[t]) * idf(t) * boost(t))
    cand = cand[:4000]
    chosen, covered = [], set()
    for _ in range(max_themes):
        best, score = None, 0
        for t in cand:
            fresh = len(post[t] - covered)
            sc = fresh * idf(t) * boost(t)
            if fresh >= 2 and sc > score:
                best, score = t, sc
        if not best:
            break
        chosen.append(best)
        covered |= post[best]
    out = {}
    for s, c in docs.items():
        top = max(chosen, key=lambda t: c.get(t, 0) * idf(t), default=None)
        if top and c.get(top, 0) >= 1:
            out[s] = top
    return out


def colony_names(by_day, assign, first_day, last_day, window=3):
    """What each colony is about, day by day.

    by_day: session id -> {day index: Counter}; assign: session id -> colony key.
    Returns {colony key: [[day start epoch, name], ...]}, one entry per change, starting with the key itself,
    so the name at any moment is the last entry at or before it.
    """
    members = collections.defaultdict(list)
    for sid, key in assign.items():
        members[key].append(sid)
    n_docs = max(1, len(by_day))
    df = collections.Counter()
    for days in by_day.values():
        seen = set()
        for c in days.values():
            seen |= set(c)
        df.update(seen)
    out = {}

    def idf(term):
        return math.log(n_docs / df[term]) if df.get(term) else 0.0

    def boost(term):
        return 2.0 if " " in term else 1.0

    for key, sids in members.items():
        names, cur, changed = [[day_start(first_day), key]], key, first_day
        for d in range(first_day, last_day + 1):
            win = collections.defaultdict(int)  # term -> number of this colony's sessions using it in the window
            for sid in sids:
                seen = set()
                for dd in range(d - window + 1, d + 1):
                    seen |= set(by_day.get(sid, {}).get(dd, ()))
                for term in seen:
                    win[term] += 1
            need = 2 if len(sids) > 1 else 1
            best, score = None, 0.0
            for term, k in win.items():
                if (
                    k < need or df[term] > max(0.15 * n_docs, 5) or (" " not in term and k < 3)
                ):  # a lone word needs real backing
                    continue
                sc = k * idf(term) * boost(term)
                if sc > score:
                    best, score = term, sc
            held = win.get(cur, 0) * idf(cur) * boost(cur)
            # a name sticks: the new one must clearly beat the current one, and not too soon after the last change
            if best and best != cur and d - changed >= MIN_DAYS_BETWEEN and score > SWITCH_MARGIN * held:
                names.append([day_start(d), best])
                cur, changed = best, d
        out[key] = names
    return out
