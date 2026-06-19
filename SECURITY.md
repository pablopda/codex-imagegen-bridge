# Security Notes

## Supported Versions

Security fixes are provided for the latest released version of this project.

## Safety Guarantees

- This project does not read or print Codex auth files such as `~/.codex/auth.json`.
- The bridge does not print full environment dumps, access tokens, or API keys.
- `OPENAI_API_KEY` and `CODEX_API_KEY` are removed from the `codex exec` subprocess environment by default.
- `--allow-api-env` is an explicit escape hatch for users who intentionally want API-key-backed Codex execution.
- This is not full process isolation: `codex exec` still inherits other environment variables from the invoking shell.
- The default Codex sandbox is `workspace-write`; avoid `danger-full-access` unless you have a separate reason and understand the risk.
- Tests and diagnostics are designed not to call `$imagegen` or spend image-generation quota.

## Reporting A Vulnerability

Report security issues privately to the repository maintainer. Do not include API keys, Codex auth files, access tokens, or other secrets in the report.

Include:

- affected version or commit,
- operating system and Python version,
- minimal reproduction steps,
- whether any live Codex generation was involved.

Expected initial response target: within 7 days for maintained releases.
