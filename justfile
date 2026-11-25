# Every check lives here, so your laptop, the git hooks and CI all run exactly the same commands.
# `just` lists the recipes; `just check` is what CI runs.

set shell := ["bash", "-euo", "pipefail", "-c"]

# read from .pre-commit-config.yaml, so the CI binary and the commit hook are always the same gitleaks (Dependabot updates that file)
gitleaks_version := `sed -n '/gitleaks\/gitleaks/{n;s/.*rev: v//p;}' .pre-commit-config.yaml`

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

# build the wheel and sdist (validated) and the single-file agent-dish.pyz
build:
    rm -rf dist dist-zipapp
    uv build
    uvx twine check dist/*.whl dist/*.tar.gz
    python3 scripts/make_zipapp.py dist-zipapp/agent-dish.pyz

# set the version to today's date (YYYY.MM.DD, or YYYY.MM.DD.N if today is already released) and date the changelog
bump:
    python3 scripts/bump_version.py

# the whole release in one go: checks, bump, commit, push, wait for CI, publish the GitHub release (asks before it pushes)
release:
    #!/usr/bin/env bash
    set -euo pipefail
    [ "$(git branch --show-current)" = main ] || { echo "run this on main"; exit 1; }
    git fetch -q origin main
    git merge-base --is-ancestor origin/main HEAD || { echo "main is behind origin/main: pull first"; exit 1; }
    [ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit or stash your changes first"; exit 1; }
    awk '/^## Unreleased/{f=1;next} /^## /{f=0} f && NF{found=1} END{exit !found}' CHANGELOG.md \
      || { echo "nothing under '## Unreleased' in CHANGELOG.md: write the release notes first"; exit 1; }
    just check
    just bump
    # from here the bump is uncommitted: undo it if anything below fails before the commit
    trap 'git checkout -- CHANGELOG.md src/agent_dish/__init__.py; echo "bump undone"' ERR
    version=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' src/agent_dish/__init__.py)
    just release-check "v$version"
    just check
    echo
    read -r -p "Push to origin and publish v$version on GitHub? [y/N] " answer
    [ "$answer" = y ] || { git checkout -- CHANGELOG.md src/agent_dish/__init__.py; echo "cancelled, bump undone"; exit 1; }
    git add CHANGELOG.md src/agent_dish/__init__.py
    git commit -q -m "Release $version"
    trap - ERR
    git push origin main
    sha=$(git rev-parse HEAD)
    echo "waiting for CI on ${sha:0:7} ..."
    run=""
    for _ in $(seq 1 30); do
      run=$(gh run list --commit "$sha" --workflow ci.yml --json databaseId --jq '.[0].databaseId // empty')
      [ -n "$run" ] && break
      sleep 2
    done
    [ -n "$run" ] || { echo "no CI run found for $sha; check the Actions tab, then publish by hand"; exit 1; }
    gh run watch "$run" --exit-status
    gh release create "v$version" --target "$sha" --title "$version" --notes ""
    echo "published v$version; the release workflow now attaches the files (gh run list --workflow release.yml)"

# a release tag must be v + the version, e.g. `just release-check v2026.11.24`
release-check tag:
    python3 scripts/release_check.py {{ quote(tag) }}

# open the demo dish (invented sessions)
demo:
    uv run agent-dish demo --open --out /tmp

# your own dish, live
serve:
    uv run agent-dish serve --open
