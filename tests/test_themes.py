from agent_dish.themes import DAY, colony_names, terms, themes_for


def test_terms_drop_noise_and_make_phrases():
    c = terms("Please check the weekly forecast at /Users/x/repos/foo.py and https://example.com <b>tag</b> deadbeef")
    assert c["weekly forecast"] == 1 and c["weekly"] == 1
    assert "please" not in c and "foo" not in c and "example" not in c and "tag" not in c and "deadbeef" not in c


def test_themes_group_sessions_by_shared_phrase():
    docs = {f"s{i}": terms("weekly production forecast review " * 3) for i in range(5)}
    docs.update({f"t{i}": terms("climate outlook scenario names " * 3) for i in range(5)})
    docs.update(
        {f"u{i}": terms(f"unrelated words {w} " * 3) for i, w in enumerate(["alpha", "bravo", "charlie", "delta"])}
    )
    out = themes_for(docs)
    assert len({out[f"s{i}"] for i in range(5)}) == 1 and len({out[f"t{i}"] for i in range(5)}) == 1
    assert out["s0"] != out["t0"]


def test_colony_name_changes_with_the_work_but_not_every_day():
    a, b = terms("alpha report " * 3), terms("bravo review " * 3)
    noise = {f"n{i}": {0: terms(f"noise{i} filler word")} for i in range(30)}
    by_day = {
        "s1": dict.fromkeys(range(0, 6), a) | dict.fromkeys(range(6, 20), b),
        "s2": dict.fromkeys(range(0, 6), a) | dict.fromkeys(range(6, 20), b),
        **noise,
    }
    names = colony_names(by_day, {"s1": "alpha report", "s2": "alpha report"}, 0, 19)["alpha report"]
    assert names[0] == [0, "alpha report"]
    later = [n for _, n in names[1:]]
    assert later and set(later[-1].split()) <= {"bravo", "review"}  # it followed the work (either word order)
    assert len(names) <= 4  # and did not flicker
    assert all(b2[0] - a2[0] >= 3 * DAY for a2, b2 in zip(names, names[1:]))  # at least 3 days apart
