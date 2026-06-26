# Final Release Audit

Status: release candidate approved and tagged.

Date: 2026-06-26

## Scope

- Default release surface: `phantom_quant` package and offline research-only commands.
- Excluded scan noise: `.git`, `.ensemble`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `reports`, `dist`, and `build`.

## Secret And Private-Data Scan

Command class: `rg` high-confidence patterns for private keys, AWS access keys, GitHub tokens, OpenAI-shaped keys, Slack tokens, and Google API keys.

Result: `high_conf_secret_hits=0`.

## Dependency/License Review

- Project license: Apache-2.0.
- Default runtime dependencies:
  - `pandas>=2`; metadata sample reviewed as `pandas==3.0.3`, BSD 3-Clause.
  - `numpy>=1.26`; metadata sample reviewed as `numpy==2.4.6`, permissive BSD/MIT/Zlib/0BSD/CC0 license expression.
  - `pyarrow>=15`; metadata sample reviewed as `pyarrow==24.0.0`, Apache-2.0.
- Optional broker dependency `shioaji>=1` is not part of the default offline release path and requires separate broker/live-trading approval before use.

Direct default release-scope dependency/license review result: pass.

## Remaining Publication Gates

- Manual maintainer approval is recorded in `docs/PUBLIC_RELEASE_APPROVAL.md`.
- Local annotated tag `v0.1.0-alpha.0` was created after the root strict approval verifier and conductor sign-off passed.
- Optional broker extra requires separate dependency/license, credential, and live-trading safety review before publication as a supported path.
