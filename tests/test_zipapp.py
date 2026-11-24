import subprocess
import sys
from pathlib import Path

from agent_dish import __version__

ROOT = Path(__file__).resolve().parent.parent


def run(*args, cwd=None):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd)  # noqa: S603


def test_the_single_file_build_runs_with_no_install(tmp_path):
    made = run(ROOT / "scripts" / "make_zipapp.py", tmp_path / "agent-dish.pyz")
    assert made.returncode == 0, made.stderr
    pyz = tmp_path / "agent-dish.pyz"
    assert pyz.stat().st_size < 400_000  # one small file

    version = run(pyz, "--version", cwd=tmp_path)  # a different folder than the repo: nothing but the .pyz is available
    assert version.returncode == 0 and version.stdout.strip() == __version__

    demo = run(
        pyz, "demo", "--out", tmp_path / "out", cwd=tmp_path
    )  # also proves the page template loads from inside the zip
    assert demo.returncode == 0, demo.stderr
    assert "DEMO: invented sessions" in (tmp_path / "out" / "agent-dish-demo.html").read_text()


def test_no_bytecode_or_egg_info_is_packed(tmp_path):
    import zipfile

    run(ROOT / "scripts" / "make_zipapp.py", tmp_path / "a.pyz")
    names = zipfile.ZipFile(tmp_path / "a.pyz").namelist()
    assert "__main__.py" in names and "agent_dish/web/template.html" in names
    assert not [n for n in names if "__pycache__" in n or n.endswith(".pyc") or ".egg-info" in n]
