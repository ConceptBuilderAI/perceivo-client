# Releasing `perceivo-client`

`perceivo-client` is released to PyPI from this repository by
`.github/workflows/release.yml`, through PyPI trusted publishing, TestPyPI first.
No package upload happens any other way: there is no API token, and nothing is
uploaded from a workstation.

The pipeline is the same one the `perceivo` repository runs, by owner directive
(2026-10-03): *"I want these two repos to have the exactly same CI pipelines -
this is confusing and could lead to errors."* Where this file differs from
`perceivo`'s `RELEASING.md`, the difference is one the client requires, and it is
named where it occurs.

## Source and artifact preflight

A release candidate must pass every repository check from one exact commit:

1. Pass Ruff lint and format checks with no outstanding diagnostics.
2. Pass the unit suite with branch coverage, the unpacked-sdist suite, and the
   dependency-floor suite on Python 3.11, 3.12 and 3.13.
3. Build a wheel and source distribution in the canonical Linux job described
   below, with `SOURCE_DATE_EPOCH` taken from the archived source commit.
4. Pass `twine check --strict`, the archive checks
   (`scripts/verify_public_tree.py archives`: every tracked `perceivo_client/`
   file present byte for byte in both archives, `py.typed` and `LICENSE`
   shipped, no denied path or secret pattern), the two-build member/hash
   comparison, and the two-build raw archive SHA-256 comparison.
5. Install the wheel and source distribution separately in empty environments;
   verify metadata, version, `perceivo_client.__version__`, import origin, and
   the `Client`/`AsyncClient` imports.
6. Pass the API contract check (below) on the release pull request's head.
7. Obtain final independent reviewer and Security verdicts over the exact tree,
   CI evidence and artifacts.

CI runs these checks without upload credentials. A failing or skipped required
check blocks the release candidate.

*Client difference:* `perceivo` also verifies a `SOURCE-PROVENANCE.json` seal of
its export from the source repository. This repository is not an export and has
no seal, so `verify_public_tree.py` checks the archives against the git index
instead and offers no `seal`/`verify` subcommands.

### The API contract check

Download the API's published public OpenAPI document into the root of the
repository checkout, then run, on the release pull request's head and with
`SRC` set to the downloaded file's name:

```bash
python openapi/regen.py --check --release --upstream "$SRC"
```

It must end `check OK (legs: models, spec_sha256, upstream; ...)`. It exits 2
without `--upstream`, when the document cannot be read, or when `SRC` is a URL
or anything other than a file name in the current directory, and exits 1 when the
document's SHA-256 is not the `upstream.sha256` recorded in
`openapi/spec_provenance.json`, or when `openapi/openapi-v1.json` is not the
transform of that document. CI runs only `--check`, which has no upstream
document and so cannot show the vendored spec is current; this step is where
that is shown.

If the check reports that the upstream document has moved, refresh the vendored
spec in a pull request of its own before the release:

```bash
python openapi/regen.py --refresh --upstream "$SRC"
```

The refresh rewrites `openapi/openapi-v1.json`, `openapi/spec_provenance.json`
and `perceivo_client/generated/models/`. Review the diff as an API change, and do
not commit the downloaded document.

## The canonical Linux build

**Only the artifacts produced by `.github/workflows/build-distributions.yml` are
release candidates.** `ci.yml` calls it on every pull request and push to `dev`,
and `release.yml` calls it on a release tag, so a release uploads the output of
exactly the job definition CI exercises. A build produced anywhere else —
including a maintainer's Windows or macOS workstation — is a smoke test. Its
archive hashes are not comparable to the candidate hashes and must never be
quoted as reproduction evidence.

| Input | Value | Why it is pinned |
|---|---|---|
| Runner OS label | `ubuntu-24.04` | Selects the Ubuntu release explicitly; it does not pin an immutable hosted-runner image. |
| Interpreter | Python `3.12.14` | A patch bump changes `zipfile`, `tarfile` and `gzip` behaviour. |
| Build closure | `.github/requirements-build.txt`, installed `--only-binary :all: --require-hashes` | Different setuptools releases emit different archive metadata; the hashes fix the exact bytes, and `--only-binary` stops an sdist's `setup.py` running in the build job. |
| Check tool | `.github/requirements-twine.txt`, in a separate venv, same flags | Keeps the metadata check fixed without sharing the build interpreter. |
| Isolation | `python -m build --no-isolation` | Without it `build` resolves its own backend and the pins above do not apply. |
| `SOURCE_DATE_EPOCH` | `git show -s --format=%ct HEAD` of the **archived source commit** | The default pull-request checkout is a synthetic merge commit whose time changes on every re-run. |

*Client difference:* `perceivo` pins the four build tools as `==` versions in
workflow environment variables. This repository already carried hash-pinned
requirement files for the same tools, which are the stronger control, so they
are kept.

The sdist is not byte-identical between two clean builds even in one container,
and `compare-archives` — which hashes member payloads only — passes on those
non-reproducible sdists. So the build job canonicalizes both archives
(`verify_public_tree.py canonicalize-sdist` / `canonicalize-wheel`: names and
payloads preserved, ownership, modes, times, gzip header and zip attributes
normalized, unsafe members refused with the input left untouched) and asserts
the raw archive SHA-256 comparison alongside the member comparison.

## Release sequence

1. **Source.** The release pull request sets the `pyproject.toml` version and
   `perceivo_client/_version.py` to the release version and carries the
   `CHANGELOG.md` section. *Client difference:* there is no `VERSION` file; the
   version lives in those two places, and `check_release_tag.py` and
   `tests/test_release_workflow_structure.py` both require them to agree. The
   version must be strictly above `highest_client_version` in
   `.github/release-floor.toml` (the highest version published from the
   previous repository); the structure test refuses one at or below it.
2. **Settings read-back.** Immediately before the tag push, run the
   maintainers' release-settings read-back (kept with the organisation's private
   release tooling, not in this repository) against the release reviewer and
   **every** name in *Required checks on `dev`* below. If it reports any control
   missing or changed, **do not tag**.
3. **Tag.** Push `v<version>` (for example `v0.27.0rc1` or `v0.27.0`) on the
   merge commit of the release pull request, from an account that is **not** the
   `pypi` reviewer (see *Approving*). `scripts/check_release_tag.py` refuses a
   tag that is not in PEP 440 normal form, that differs from the
   `pyproject.toml` version or `_version.py`, or whose commit is not on the
   repository's default branch. `release.yml` reads that branch from the event
   (`github.event.repository.default_branch`), so ancestry is checked against
   `origin/dev` where `dev` is the default branch and `origin/main` where `main`
   is; the same file serves both.
4. **Publish.** `release.yml` runs `verify` → `build` → `install-matrix`
   (Python 3.11, 3.12 and 3.13) → `testpypi` → `testpypi-smoke` → `pypi` (waits
   for the reviewer) → `pypi-verify` → `github-release`. The `build` job records
   each file's name and sha256 as **job outputs**. Every job that handles the
   files, and every upload, first checks them byte for byte against those
   outputs. Run artifacts are only carriers: any later job in the run can
   replace an artifact, but no job can change another job's outputs, so no
   digest is ever read from an artifact (`check_workflow_policy.py` enforces
   this). `testpypi-smoke` downloads what TestPyPI serves, proves each file's
   sha256 equals the built one (`sha256 match <file> <sha256>`), and installs
   that wheel with its dependencies from pypi.org only. `SHA256SUMS` on the
   GitHub release is written from the same outputs.
5. **Approve** (below).

A `workflow_dispatch` run of `release.yml` is a dry run: it verifies the
`pyproject.toml` version as `v<version>` against the dispatched commit, builds
and installs, and every upload job is skipped.

A version is a promise about bytes. Never replace or republish an occupied
version; a PyPI file can never be replaced in any case.

## The upload gate

`release.yml` is read from the tagged commit, so the checks inside it are mistake
guards. What decides whether bytes reach PyPI is:

1. the `release-tags` ruleset, which decides who may create a `v*` tag;
2. the `pypi` environment: exactly one required reviewer, a human account that no
   automation uses; "Prevent self-review" on; administrators may **not** bypass;
   deployments limited to tags `v*`;
3. the PyPI trusted publisher, bound to this repository, `release.yml` **and**
   the environment `pypi` (on TestPyPI, `testpypi`). A publisher with a blank
   environment would let any job of `release.yml` upload without a reviewer.

The release-settings read-back reads 1 and 2 back, together with the
`testpypi` tag policy and the `dev` protection ruleset. It only reads, and never
changes a setting. The publisher binding is read back by hand on pypi.org and
test.pypi.org.

Warning: An `environment:` naming an environment that does not exist does **not** fail
the run: GitHub creates it implicitly, with no reviewers. A deleted environment
is recreated **unprotected** the same way, so the environment is never deleted.

Known limits:
- A repository administrator can change or delete an environment.
- The tag ruleset admits repository administrators.

Both are settings changes recorded in the audit log, and the reviewer approves
only a `pypi` job that is waiting.

### Required checks on `dev`

These are the exact check names the release depends on. Every one must be a
required status check on `dev`, and the release-settings read-back checks every
one:

```
"Source, coverage, and build" "Clean wheel install" "Clean sdist install"
"Full suite from the unpacked sdist" "Dependency floors on Python 3.11"
"Dependency floors on Python 3.12" "Dependency floors on Python 3.13"
"Analyze (python)" "Analyze (actions)" "SonarCloud Code Analysis"
"Workflow policy" "Release tag self-test"
"Build / Build and reproduce distributions"
"Install smoke (wheel)" "Install smoke (sdist)"
```

The last five are the release jobs; they mirror perceivo's `main-protection`.
If one is missing, a change that breaks the workflow policy or the build merges
green and fails only at tag time.

### Adding required checks to `main-protection`

`main-protection` is the ruleset name the read-back checks; in this repository
it targets `dev`. Edit the ruleset only from a fresh read, guarded:

1. Snapshot the ruleset.
2. Immediately before the edit, compare the live ruleset with the snapshot. If
   it has changed, take a new snapshot and start again.
3. Edit the freshly loaded ruleset, or PUT the full ruleset with the checks appended.
4. Compare the saved ruleset with the snapshot and confirm the only change is
   the added checks.

The guard cannot see a change made between its read and the save. The
release-settings tooling provides the snapshot, guard and verify steps.

## One-time owner steps

Repository and PyPI settings, not a diff. Agents do not perform any of them. In
this order, then run the settings read-back until it exits 0:

1. **GitHub — the `pypi` environment** (*Settings* → *Environments*, name
   exactly `pypi`): required reviewer the human-only account, **Prevent
   self-review** on, **Allow administrators to bypass** **off** (GitHub's default
   is on), deployment branches and tags: *Selected*, one **tag** rule `v*`.
2. **GitHub — the `testpypi` environment:** administrators may not bypass, and
   exactly one deployment rule, tag `v*` (replacing any branch rule).
3. **GitHub — the `release` environment is retired.** It belonged to the
   retired `client-v*` workflow; `release.yml` uses only `testpypi` and `pypi`,
   and no workflow in this repository references `release`. Delete it from
   *Settings* → *Environments* if it is still listed (unlike `pypi` and
   `testpypi`, nothing can recreate it implicitly, because nothing names it).
4. **GitHub — the `release-tags` tag ruleset** on `refs/tags/v*` (creation,
   update, deletion), bypass actor: the repository admin role, and retire the
   `client-release-tags` ruleset on `client-v*`.
5. **GitHub — the `main-protection` branch ruleset** on `dev` (pull request,
   no force push, no deletion, required status checks: **every** name in
   *Required checks on `dev`*), if the read-back still reports it missing (`dev` is protected today by classic branch protection,
   which the read-back does not read).
6. **PyPI and TestPyPI — trusted publishers.** The project `perceivo-client`
   already exists on both indexes (a `0.0.1` name-reservation placeholder), so
   the publisher is added to the existing project, not as a pending publisher:
   pypi.org and test.pypi.org → *Your projects* → `perceivo-client` → *Manage* →
   *Publishing* → *Add a new publisher* → *GitHub*: owner `ConceptBuilderAI`,
   repository `perceivo-client`, workflow `release.yml`, environment `pypi`
   (TestPyPI: `testpypi`). On the same page, **remove** any publisher bound to
   the name-reservation repository `perceivo-client-pypi`, so this repository
   and environment are the only upload path.
7. **PyPI and TestPyPI — revoke the placeholder token.** Revoke the API token
   used for the `0.0.1` placeholder upload (*Account settings* → *API tokens*).
   Releases upload through trusted publishing only; no token is needed.

Note: **Not verified before the first real run:** the OIDC exchange with PyPI and
TestPyPI, the publish action's container pull, and the uploads. None of them can
run before these steps exist, and nothing in CI exercises them.

## Approving a PyPI deployment

Signed in as the release reviewer:

1. On the release pull request, note the merge commit, and confirm the Publish
   run's commit equals it. If it does not, **Reject**.
2. Confirm `testpypi-smoke` is green on all three Python versions, with a
   `sha256 match` line for the wheel and one for the sdist.
3. Review deployments → `pypi` → **Approve and deploy**.

If anything is red or missing, or the `pypi` job was **not** waiting for review,
**Reject** and report it.

Warning: "Prevent self-review" stops the account that pushed the tag from approving the
run it started, and the reviewer is the only required reviewer. So the tag is
pushed by another account; a run started by the reviewer waits with no eligible
approver and is cancelled and re-tagged as the next `rcN`.

## Yank and stop-uploads runbooks

- **Yank.** On pypi.org, open the release → Options → Yank, and give a reason. A
  PyPI file can never be replaced:
  - a bad release candidate is followed by the next `rcN`;
  - a bad final release is yanked and followed by the next patch release.
- **Stop uploads.** Remove the GitHub trusted publisher on pypi.org (and on
  test.pypi.org), or set the `pypi` environment's tag rule to a pattern no tag
  matches while keeping its reviewer. **Never delete the environment.**

## Conditions for making this repository public

The visibility change is one act and must carry all of these with it:

1. **Reserve or verify the PyPI name.** `perceivo-client` is unregistered
   (`https://pypi.org/pypi/perceivo-client/json` returns 404 as of 2026-09-19).
   Publishing the repository before the name is held invites someone to
   register it and receive readers' API keys and signing secrets.
2. **Enable Private Vulnerability Reporting.** `SECURITY.md` advertises it.
3. **Set the repository Actions policy to require SHA-pinned actions**, which
   makes the property this repository already maintains by hand enforceable.
4. **Decide the commit-author metadata**, and squash into `main`: that squash is
   what is open-sourced, and it is where tracked ticket references are removed.

## Publication boundary

The workflow publishes only the `perceivo-client` distribution. Platform and
`perceivo` framework source, artifacts and credentials are outside this
repository.
