# Repository Guidelines

## Project Purpose

This project provides a small Python CLI and Codex skill for generating or
editing images through Codex CLI built-in `$imagegen`, while defaulting away
from direct OpenAI API-key billing.

## Commands

Run these checks before handing off code changes:

```bash
python3 -m py_compile src/codex_imagegen_bridge/*.py
python3 -m pytest -q
```

For an isolated packaging smoke test:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
codex-imagegen --help
```

## Development Notes

- Keep the CLI dependency-free unless there is a clear reason to add a package.
- Do not run live image generation unless the user explicitly asks for it.
- Do not read or print Codex auth files, API keys, or full environment dumps.
- Preserve the default behavior that strips `OPENAI_API_KEY` and `CODEX_API_KEY`
  from the `codex exec` subprocess.
- Prefer focused tests that verify command construction and safety behavior
  without spending Codex quota.

## Current Priorities

The PRD describes the production target. The next useful work is:

1. Add `scripts/doctor` for Codex CLI/login diagnostics.
2. Improve `--dry-run` output to include command, prompt, and stripped env vars.
3. Add Claude Code plugin packaging under `plugins/codex-image/`.
4. Add local marketplace metadata and layout validation tests.
