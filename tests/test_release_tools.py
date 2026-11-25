import datetime
import importlib.util
import re
from pathlib import Path

from agent_dish import __version__

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check, bump = load("release_check"), load("bump_version")


def test_the_package_version_is_a_date():
    assert check.CALVER.match(__version__), __version__
    assert check.package_version() == __version__


def test_a_tag_must_be_v_plus_the_version():
    assert check.problems("v2026.11.24", "2026.11.24") == []
    assert check.problems("v2026.11.24.1", "2026.11.24.1") == []
    assert check.problems("v2026.11.24", "2026.11.24.1")  # the old tag for a newer version is refused
    assert check.problems("2026.11.24", "2026.11.24")  # no v
    assert check.problems("v0.1.0", "2026.11.24")  # the old scheme
    assert check.problems("v2026.11.24; rm -rf /", "2026.11.24")  # a hostile tag name never matches


def test_zero_padding_in_the_tag_does_not_cause_false_mismatches():
    # the source version is always the padded date; the tag may be written either way (wheel names are unpadded)
    assert check.problems("v2026.01.05", "2026.01.05") == []
    assert check.problems("v2026.1.5", "2026.01.05") == []
    assert check.problems("v2026.1.6", "2026.01.05")  # but a different day is still refused


def test_a_version_that_is_not_a_date_is_refused():
    assert check.problems("v1.2.3", "1.2.3")


def test_main_exit_codes():
    assert check.main([f"v{__version__}"]) == 0
    assert check.main(["v1999.01.01"]) == 1
    assert check.main([]) == 2


def test_bump_picks_todays_date_then_the_next_free_suffix():
    day = datetime.date(2026, 11, 24)
    assert bump.next_version(day, set()) == "2026.11.24"
    assert bump.next_version(day, {"v2026.11.23"}) == "2026.11.24"
    assert bump.next_version(day, {"v2026.11.24"}) == "2026.11.24.1"
    assert bump.next_version(day, {"v2026.11.24", "v2026.11.24.1"}) == "2026.11.24.2"
    assert bump.next_version(datetime.date(2026, 1, 5), set()) == "2026.01.05"  # zero padded, as written


def test_bump_dates_the_unreleased_section_only():
    text = "# Changelog\n\n## Unreleased\n\n- a\n\n## 2026.10.01\n\n- b\n"
    out = bump.date_changelog(text, "2026.11.24")
    assert "## 2026.11.24\n" in out and "## 2026.10.01" in out
    assert out.count("## Unreleased") == 1 and out.index("## Unreleased") < out.index(
        "## 2026.11.24"
    )  # a fresh one on top
    assert bump.date_changelog("# Changelog\n\n## 2026.10.01\n", "2026.11.24") is None
    assert re.search(r"^## 2026\.11\.24$", out, re.M)


def test_bump_keeps_the_blank_line_and_leaves_a_fresh_unreleased_heading():
    out = bump.date_changelog("# Changelog\n\n## Unreleased\n\nFirst release.\n", "2026.11.24")
    assert out == "# Changelog\n\n## Unreleased\n\n## 2026.11.24\n\nFirst release.\n"
    again = bump.date_changelog(out, "2026.11.25")  # the next bump finds the heading, and the old notes stay put
    assert again.count("## Unreleased") == 1 and "## 2026.11.25\n\n## 2026.11.24\n" in again


def test_a_hostile_tag_name_is_never_run_as_a_command(tmp_path):
    """CI passes the release tag to `just release-check`; git allows ; $ and backticks in tag names."""
    import shutil
    import subprocess

    import pytest

    just = shutil.which("just")
    if not just:
        pytest.skip("just is not installed")
    marker = tmp_path / "pwned"
    hostile = f"v2026.11.24; touch {marker}"
    run = subprocess.run([just, "release-check", hostile], cwd=SCRIPTS.parent, capture_output=True, text=True)  # noqa: S603
    assert run.returncode != 0 and not marker.exists()
