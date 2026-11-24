"""Guards on the npm package: it is a thin launcher, with no dependencies, no install scripts and no network code."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import tomllib

ROOT = Path(__file__).resolve().parent.parent
PKG = json.loads((ROOT / "npm" / "package.json").read_text())
NODE = shutil.which("node")
PYTHON = shutil.which("python3")
NETWORK_IMPORT = re.compile(
    r"^\s*(import|from)\s+(urllib\.request|urllib3|http\.client|requests|httpx|aiohttp|socket|ssl|ftplib|smtplib|telnetlib|xmlrpc)\b"
    r"|urlopen|create_connection|require\(\s*['\"](https?|net|tls|dgram|dns)['\"]",
    re.M,
)


def test_npm_and_python_versions_match():
    py = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert PKG["version"] == py


def test_no_install_scripts_and_no_dependencies():
    lifecycle = {
        "preinstall",
        "install",
        "postinstall",
        "prepare",
        "prepublish",
        "prepublishOnly",
        "prepack",
        "postpack",
    }
    assert not lifecycle & set(PKG.get("scripts", {}))
    assert not any(PKG.get(k) for k in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"))


def test_only_an_allowlist_of_files_is_published():
    assert PKG["files"] == ["bin/", "python/", "LICENSE", "README.md"]
    assert PKG["bin"] == {"agent-dish": "bin/agent-dish.js"}
    assert "author" not in PKG  # no personal details in the package metadata


def test_shipped_code_has_no_outbound_network_access():
    code = [ROOT / "npm" / "bin" / "agent-dish.js", *(ROOT / "src" / "agent_dish").rglob("*.py")]
    offenders = [str(p.relative_to(ROOT)) for p in code if NETWORK_IMPORT.search(p.read_text())]
    assert offenders == []


@pytest.mark.skipif(not NODE, reason="node is not installed")
def test_launcher_explains_itself_when_python_is_missing():
    run = subprocess.run(  # noqa: S603
        [NODE, str(ROOT / "npm" / "bin" / "agent-dish.js"), "--version"],
        env={"PATH": "/nonexistent"},
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1 and "Python 3.9 or newer" in run.stderr


@pytest.mark.skipif(not (NODE and PYTHON), reason="node or python3 is not installed")
def test_launcher_runs_the_bundled_python_program(tmp_path):
    (tmp_path / "bin").mkdir()
    shutil.copy(ROOT / "npm" / "bin" / "agent-dish.js", tmp_path / "bin")
    shutil.copytree(
        ROOT / "src" / "agent_dish", tmp_path / "python" / "agent_dish", ignore=shutil.ignore_patterns("__pycache__")
    )
    run = subprocess.run([NODE, str(tmp_path / "bin" / "agent-dish.js"), "--version"], capture_output=True, text=True)  # noqa: S603
    assert run.returncode == 0 and run.stdout.strip() == PKG["version"]
