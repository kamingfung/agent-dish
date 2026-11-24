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

## npm (so `npx agent-dish` works)

The npm package in `npm/` is a thin launcher around the same Python program (Python 3.9+ must be installed). It has no
dependencies, no install scripts and makes no network requests; tests enforce all three.

Check what would be published, and try the real install, without publishing anything:

```bash
just npm-check    # lists the exact files that would go on the registry
just npm-smoke    # installs the tarball into a scratch folder and runs it
```

**First publish, by hand** (the package must exist before npm lets you attach a trusted publisher):

1. Use an npm account with two-factor authentication on. The account's email is shown publicly in the package's
   maintainer metadata, so use a personal or alias address.
2. `npm login`, then `just npm-check`, then `cd npm && npm publish --access public`.
3. Versions can never be reused and unpublishing is restricted, so check `just npm-check` output first.

**Every later release, from GitHub Actions with no stored token:**

1. On npmjs.com open the package, _Settings > Trusted publisher_: GitHub Actions, owner `kamingfung`, repository
   `agent-dish`, workflow `release.yml`.
2. In the GitHub repo, _Settings > Secrets and variables > Actions > Variables_: add `PUBLISH_TO_NPM` = `true`.
3. Tag as usual (`git tag v0.2.0 && git push origin v0.2.0`). The `npm` job publishes with provenance, so each
   version links back to the exact commit and workflow run that built it.

`just release-check v0.2.0` refuses to continue unless the tag, `pyproject.toml` and `npm/package.json` agree.
