# Contributing to perceivo-client

Thank you for your interest in contributing to `perceivo-client`, the Python client for the Perceivo
Platform API. This document explains how to get set up, our expectations for contributions, and how
changes are reviewed.

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).
Please report unacceptable behavior to conduct@perceivo.ai.

## Ways to Contribute

- **Report bugs** - open an issue using the bug report template. Include the client version
  (`pip show perceivo-client`), your Python version and a minimal example.
- **Request features** - open an issue using the feature request template.
- **Improve documentation** - corrections to
  [perceivo.ai/docs](https://perceivo.ai/docs), this repository's README and the
  [HMAC request signing guide](./docs/HMAC_REQUEST_SIGNING.md) are welcome.
- **Submit code** - fix a bug or implement a feature through a pull request.

Please do not report security vulnerabilities in public issues; follow [SECURITY.md](./SECURITY.md)
instead.

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/perceivo-client.git
cd perceivo-client

# Create a virtual environment and install the development tools
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]" twine
```

Use Python 3.11, 3.12, or 3.13. The `codegen` extra (`pip install -e ".[dev,codegen]"`) installs
the exact generator and formatter versions needed to run `python openapi/regen.py --check`.

## Generated Code

The request and response models in `perceivo_client/generated/` are generated from the vendored
OpenAPI document `openapi/openapi-v1.json` by `openapi/regen.py`. Do not edit them by hand: a hand
edit is reverted by the next regeneration and fails the `regen.py --check` step in CI. If a model is
wrong, open an issue so that the source (the API contract or the generator configuration) can be
fixed.

To regenerate the models, install the `codegen` extra and run:

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
published public OpenAPI document, given as a file name in the current directory.
[RELEASING.md](./RELEASING.md) describes it.

## Before You Open a Pull Request

- **Format and lint** - run `ruff check .` and `ruff format --check .`.
- **Generated models** - run `python openapi/regen.py --check` with the `codegen` extra installed.
- **Test** - add tests for new behavior and run `pytest tests`; the repository configuration
  collects coverage. A test should fail without your change.
- **Wrapper paths** - every resource method must call an operation in the vendored OpenAPI
  document; `tests/test_spec_conformance.py` enforces this.
- **Build** - run `python -m build` and `python -m twine check dist/*`.
- **Docstrings** - give every public symbol type hints and a clear, accurate docstring.
- **Changelog** - add an entry under an `## [Unreleased]` heading at the top
  of [CHANGELOG.md](./CHANGELOG.md).
- **Keep it focused** - submit one logical change per pull request.

## Pull Request Process

1. Fork the repository and create a topic branch from the default branch.
2. Make your change, with tests and documentation.
3. Ensure lint, format, generated models, tests, and build all pass locally. CI runs the same
   gates.
4. Open a pull request using the template and describe the motivation and
   approach.
5. A maintainer will review. Address feedback with additional commits on your
   branch.

## Commit Messages

Write clear, imperative commit messages ("Add X", "Fix Y"). Reference related
issues where relevant, for example `Fixes #123`.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](./LICENSE), the same license that covers this project.
