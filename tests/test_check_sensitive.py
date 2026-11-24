import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_sensitive", Path(__file__).parent.parent / "scripts" / "check_sensitive.py"
)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

# built from pieces so this file does not trip the checker it tests
HOME = "/Us" + "ers/"
EMAIL = "jane.roe@" + "corp.example.io"


def kinds(text, terms=()):
    return [what for _, what in cs.scan_text(text, terms)]


def test_flags_real_looking_email_but_not_noreply_example_or_git_remote():
    assert kinds(f"contact {EMAIL}") == ["email address"]
    assert kinds("a@users.noreply.github.com b@example.com git@github.com:o/r.git") == []


def test_flags_home_paths_with_a_real_name_only():
    assert kinds(f"see {HOME}priya/projects/x") == ["home-directory path with a user name"]
    assert kinds("see /ho" + "me/priya/x and C:\\Us" + "ers\\priya\\x") != []
    assert kinds(f"{HOME}x/repos and /home/runner/work and {HOME}you/.config") == []


def test_private_terms_are_case_insensitive_and_report_the_term():
    assert kinds("Working for ACME Corp today", ["acme corp"]) == ["private term 'acme corp'"]
    assert kinds("nothing here", ["acme corp"]) == []


def test_marker_suppresses_a_line():
    assert kinds(f"{EMAIL}  # sensitive-ok") == []


def test_main_exit_codes_terms_file_and_binary_files(tmp_path, monkeypatch, capsys):
    clean, dirty, binary = tmp_path / "a.md", tmp_path / "b.md", tmp_path / "c.png"
    clean.write_text("hello\n")
    dirty.write_text("owner: Globex\n")
    binary.write_bytes(b"\x89PNG\xff\xfe" + bytes(range(256)))
    terms = tmp_path / "terms.txt"
    terms.write_text("# private\nglobex\n")
    monkeypatch.setenv("AGENT_DISH_SENSITIVE_TERMS", str(terms))
    assert cs.main([str(clean), str(binary)]) == 0
    assert cs.main([str(dirty)]) == 1
    assert "private term 'globex'" in capsys.readouterr().out
    monkeypatch.setenv("AGENT_DISH_SENSITIVE_TERMS", str(tmp_path / "missing.txt"))
    assert cs.main([str(dirty)]) == 0  # no private list: generic checks only (as in CI)
