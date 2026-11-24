# Releasing

## A GitHub release (automatic)

1. Bump `version` in `pyproject.toml` and add a `## <version>` section to `CHANGELOG.md`.
2. Commit, then tag and push the tag:
   ```bash
   git tag v0.2.0 && git push origin v0.2.0
   ```
3. The `release` workflow (it only calls `just`) checks the tag matches the version, runs the tests, builds the wheel and sdist, and creates the
   GitHub release with them attached and the changelog section as its notes.

Install a release: `pipx install git+https://github.com/kamingfung/agent-dish@v0.2.0`, or from the attached wheel.

## PyPI (so `pipx install agent-dish` works)

GitHub Packages has no registry for Python, so the usual home for a Python tool is PyPI. One-time setup, about five minutes:

1. Create an account at pypi.org and turn on two-factor authentication.
2. On PyPI go to _Your projects > Publishing_ (or _Account settings > Publishing_) and add a **pending publisher**:
   owner `kamingfung`, repository `agent-dish`, workflow `release.yml`, environment `pypi`. The project name is `agent-dish`.
3. In the GitHub repo, _Settings > Environments_: create an environment named `pypi`.
4. _Settings > Secrets and variables > Actions > Variables_: add `PUBLISH_TO_PYPI` = `true`.

From the next tag on, the `pypi` job publishes the same files that went to the GitHub release. PyPI versions can never be
reused or truly deleted, so check the release artifacts first.
