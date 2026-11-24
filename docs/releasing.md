# Releasing

Versions are dates: `YYYY.MM.DD`, or `YYYY.MM.DD.N` for a second release on the same day (`2026.11.24`, `2026.11.24.1`).
The tag is `v` plus the version. The version lives in one place, `__version__` in `src/agent_dish/__init__.py`.

## A GitHub release

1. Put the release notes under `## Unreleased` in `CHANGELOG.md`.
2. `just bump` sets the version to today's date (or the next `.N` if today is taken) and dates that changelog section.
3. Commit and push to `main`.
4. Publish a release on GitHub with the tag `v` + the version `just bump` printed. Use the Releases page (create the tag
   there, targeting `main`) or `gh release create v2026.11.24 --target main --generate-notes`.
5. The `release` workflow runs: it checks the tag matches the version, runs the tests, builds the wheel, the sdist and the
   single-file `agent-dish.pyz`, and attaches all three to your release. If the release has no notes, it fills them in from
   the changelog.

`just release-check v2026.11.24` runs the tag check locally. It compares numbers, so `2026.01.05` and `2026.1.5` count as
the same version.

If the workflow fails, the release exists but has no files. Fix the cause, then re-run the workflow from the Actions tab (or
delete the release and tag and publish again).

## PyPI (so `pip install agent-dish` works)

GitHub Packages has no registry for Python, so the usual home is PyPI. One-time setup, about five minutes:

1. Create an account at pypi.org with two-factor authentication on.
2. On PyPI add a **pending publisher** (_Your projects > Publishing_): owner `kamingfung`, repository `agent-dish`, workflow
   `release.yml`, environment `pypi`. The project name is `agent-dish`.
3. In the GitHub repo, _Settings > Environments_: create an environment named `pypi`.
4. _Settings > Secrets and variables > Actions > Variables_: add `PUBLISH_TO_PYPI` = `true`.

From the next release on, the `pypi` job publishes the same files that were attached to the GitHub release. PyPI versions can
never be reused or truly deleted, so check the attached files first.
