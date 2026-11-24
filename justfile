# Every check lives here, so your laptop, the git hooks and CI all run exactly the same commands.
# `just` lists the recipes; `just check` is what CI runs.

set shell := ["bash", "-euo", "pipefail", "-c"]

gitleaks_version := "8.30.0"

# list the recipes
default:
    @just --list

# one-time setup: Python environment and git hooks
setup:
    uv sync
    # Installs the hooks into .git/hooks. If you have a global core.hooksPath, pre-commit refuses; this ignores the
    # global config for the install only (global hooks that chain to the repo's own hooks keep working).
    GIT_CONFIG_GLOBAL=/dev/null uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# lint and format check (fast, no network)
lint:
    uv run ruff check .
    uv run ruff format --check .

# apply the formatter and safe lint fixes
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# run the tests, e.g. `just test -k themes`, or `just test-on 3.9`
test *args:
    uv run pytest -q {{ args }}

# run the tests on one Python version
test-on version:
    uv run --python {{ version }} pytest -q

# files, formatting, private keys, personal paths and emails, in every tracked file
hooks:
    uv run pre-commit run --all-files --show-diff-on-failure

# scan the whole git history for credentials (needs gitleaks, see `just install-gitleaks`)
secrets:
    gitleaks git --no-banner --redact --verbose .

# personal paths, emails and your private terms (see scripts/check_sensitive.py) in tracked files
sensitive:
    git ls-files -z | xargs -0 python3 scripts/check_sensitive.py

# what CI runs
check: hooks test secrets

# install gitleaks into /usr/local/bin (Linux x64; elsewhere use brew install gitleaks)
install-gitleaks:
    curl -sSL https://github.com/gitleaks/gitleaks/releases/download/v{{ gitleaks_version }}/gitleaks_{{ gitleaks_version }}_linux_x64.tar.gz | sudo tar -xz -C /usr/local/bin gitleaks

# build the wheel and sdist and validate them
build:
    rm -rf dist
    uv build
    uvx twine check dist/*

# release only if the tag matches pyproject.toml, e.g. `just release-check v0.1.0`
release-check tag:
    @v=$(python3 -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"); \
      [ "v$v" = "{{ tag }}" ] || { echo "tag {{ tag }} does not match version v$v"; exit 1; }

# open the demo dish (invented sessions)
demo:
    uv run agent-dish demo --open --out /tmp

# your own dish, live
serve:
    uv run agent-dish serve --open
