# Contributing to perceivo-client

Thank you for your interest in improving `perceivo-client`, the Python client for the Perceivo
Platform API. This guide explains how to set up a development environment, what we expect from a
change, and how pull requests are reviewed.

The package is published to PyPI as [`perceivo-client`](https://pypi.org/project/perceivo-client/).

## Code of Conduct

Everyone who participates in this project is expected to follow the
[Code of Conduct](./CODE_OF_CONDUCT.md). It explains how to report unacceptable behavior.

## Ways to contribute

- **Report a bug.** Open an issue with the bug report template. Include the client version
  (`pip show perceivo-client`), your Python version and a minimal example.
- **Suggest a feature.** Open an issue with the feature request template.
- **Improve the documentation.** The user documentation is at
  [perceivo.ai/docs](https://perceivo.ai/docs). Corrections to this repository's README, the
  [HMAC request signing guide](./docs/HMAC_REQUEST_SIGNING.md) are welcome as pull requests.
- **Submit code.** Fix a bug or implement an agreed feature in a pull request.

Please do not report security vulnerabilities in public issues. Follow [SECURITY.md](./SECURITY.md)
instead.

## Generated code

The request and response models in `perceivo_client/generated/` are generated from the vendored
OpenAPI document `openapi/openapi-v1.json` by `openapi/regen.py`. Do not edit them by hand: a hand
edit is reverted by the next regeneration and fails the `regen.py --check` step in CI. If a model is
wrong, open an issue so that the source (the API contract or the generator configuration) can be
fixed.

### Regenerating the models

Install the pinned generator and formatters with `pip install -e ".[codegen]"`, then run:

```bash
python openapi/regen.py           # regenerate the models from openapi/openapi-v1.json
python openapi/regen.py --check   # prove the committed models equal a fresh generation (CI runs this)
```

`--spec PATH` generates from another spec file, for example to preview a candidate document. Every
generated module's header names its spec by file name, declared version and SHA-256.

If you cannot install the generator, run the "Regenerate models" workflow
(`.github/workflows/regenerate.yml`) on your branch; it returns the regenerated files as a patch.

Updating the vendored document itself is a maintainer task, done with
`python openapi/regen.py --refresh --upstream SRC`, where `SRC` is a downloaded copy of the API's
published public OpenAPI document, given as a file name in the current directory. `RELEASING.md`
describes it.

## Development setup

```bash
git clone https://github.com/<your-username>/perceivo-client.git
cd perceivo-client

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Python 3.11 or later is required. The `codegen` extra (`pip install -e ".[dev,codegen]"`) installs
the exact generator and formatter versions needed to run `python openapi/regen.py --check`.

## Before you open a pull request

Run the same checks CI runs:

```bash
ruff check .
ruff format --check .
pytest tests
```

- **Tests.** Add or update tests for every behavior change. A test should fail without your change.
- **Wrapper paths.** Every resource method must call an operation in the vendored OpenAPI
  document; `tests/test_spec_conformance.py` enforces this.
- **Public API.** Public functions, methods and classes need type hints and a docstring.
- **Changelog.** Describe user-visible changes under `## [Unreleased]` in
  [CHANGELOG.md](./CHANGELOG.md).
- **Scope.** Keep each pull request to one logical change.

## Pull request process

1. Fork the repository and create a topic branch from the default branch.
2. Make your change, with tests and documentation.
3. Run the checks above and make sure they pass.
4. Open a pull request using the template, and describe the motivation and the approach.
5. A maintainer reviews it. Address feedback by pushing further commits to your branch.

## Commit messages

Write clear, imperative commit messages ("Add X", "Fix Y"). Reference related issues where relevant,
for example `Fixes #123`.

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](./LICENSE), the license that covers this project.
