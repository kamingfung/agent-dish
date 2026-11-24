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

# build the wheel and sdist (validated) and the single-file agent-dish.pyz
build:
    rm -rf dist dist-zipapp
    uv build
    uvx twine check dist/*.whl dist/*.tar.gz
    python3 scripts/make_zipapp.py dist-zipapp/agent-dish.pyz

# release only if the tag matches the Python and npm versions, e.g. `just release-check v0.1.0`
release-check tag:
    @python3 -c "import json,re,sys; t=sys.argv[1]; py=re.search(r'^version\s*=\s*\"([^\"]+)\"', open('pyproject.toml').read(), re.M).group(1); js=json.load(open('npm/package.json'))['version']; sys.exit(0 if t==f'v{py}'==f'v{js}' else f'tag {t}, pyproject {py}, npm {js}: they must all match')" {{ tag }}

# copy the Python sources into the npm package (npm/ is a thin launcher around them)
npm-sync:
    rm -rf npm/python npm/LICENSE
    mkdir -p npm/python
    cp -R src/agent_dish npm/python/agent_dish
    find npm/python -name __pycache__ -type d -prune -exec rm -rf {} +
    cp LICENSE npm/LICENSE

# list exactly what would be published to npm and fail on anything unexpected
npm-check: npm-sync
    python3 scripts/check_npm_pack.py

# build the npm tarball into dist-npm/
npm-pack: npm-sync
    rm -rf dist-npm && mkdir dist-npm
    cd npm && npm pack --ignore-scripts --pack-destination ../dist-npm

# install the tarball into a scratch folder and run the real command (needs Node and Python)
npm-smoke: npm-check npm-pack
    #!/usr/bin/env bash
    set -euo pipefail
    d=$(mktemp -d)
    tgz=$(ls "$PWD"/dist-npm/agent-dish-*.tgz)   # an absolute path: npm reads a bare relative one as a GitHub shorthand
    npm install --prefix "$d" --ignore-scripts --no-audit --no-fund "$tgz"
    "$d/node_modules/.bin/agent-dish" --version
    "$d/node_modules/.bin/agent-dish" demo --out "$d/out"
    test -s "$d/out/agent-dish-demo.html"
    echo "npm smoke test passed ($d)"

# open the demo dish (invented sessions)
demo:
    uv run agent-dish demo --open --out /tmp

# your own dish, live
serve:
    uv run agent-dish serve --open
