# Releasing `perceivo-client`

Releases are published to PyPI by `.github/workflows/release.yml` using PyPI
trusted publishing, with TestPyPI first. No API token is used and nothing is
uploaded from a workstation.

## Before tagging

1. The release pull request sets the version in `pyproject.toml` and
   `perceivo_client/_version.py` and adds the `CHANGELOG.md` section. The
   version must be above `highest_client_version` in
   `.github/release-floor.toml`.
2. Every check listed under *Required checks on `dev`* is green on the release
   pull request.
3. The vendored OpenAPI spec is current. Download the API's published public
   OpenAPI document into the repository root and run, with `SRC` set to its
   file name:

   ```bash
   python openapi/regen.py --check --release --upstream "$SRC"
   ```

   If the upstream document has changed, refresh the spec in a separate pull
   request first:

   ```bash
   python openapi/regen.py --refresh --upstream "$SRC"
   ```

   This rewrites `openapi/openapi-v1.json`, `openapi/spec_provenance.json` and
   `perceivo_client/generated/models/`. Do not commit the downloaded document.

## Build

Only the artifacts built by `.github/workflows/build-distributions.yml` are
release candidates. CI and `release.yml` both call it. It builds on
`ubuntu-24.04` with Python 3.12.14, installs the build tools from the
hash-pinned `.github/requirements-build.txt`, builds with
`python -m build --no-isolation`, takes `SOURCE_DATE_EPOCH` from the source
commit, and canonicalizes both archives so that two builds produce identical
bytes.

## Publishing

1. Push the tag `v<version>` (for example `v1.0.0` or `v1.1.0rc1`) on the
   merge commit of the release pull request. `scripts/check_release_tag.py`
   refuses a tag that is not in PEP 440 normal form, does not match the
   package version, or is not on the default branch.
2. `release.yml` runs `verify`, `build`, `install-matrix` (Python 3.11, 3.12
   and 3.13), `testpypi`, `testpypi-smoke`, `pypi`, `pypi-verify` and
   `github-release`. Every job that handles the files checks their SHA-256
   against the `build` job's outputs.
3. The `pypi` job waits for approval in the `pypi` environment. Approve it
   once `testpypi-smoke` is green on all three Python versions.

A `workflow_dispatch` run of `release.yml` is a dry run: it verifies, builds
and installs, and skips every upload job.

A published version is never replaced. A bad release candidate is followed by
the next `rcN`; a bad final release is yanked on PyPI and followed by a patch
release.

### Required checks on `dev`

```
"Source, coverage, and build" "Clean wheel install" "Clean sdist install"
"Full suite from the unpacked sdist" "Dependency floors on Python 3.11"
"Dependency floors on Python 3.12" "Dependency floors on Python 3.13"
"Analyze (python)" "Analyze (actions)"
"Workflow policy" "Release tag self-test"
"Build / Build and reproduce distributions"
"Install smoke (wheel)" "Install smoke (sdist)"
```
