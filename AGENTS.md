# Repository Guidelines

## Project Purpose

This project provides a small Python CLI and Codex skill for generating or
editing images through Codex CLI built-in `$imagegen`, while defaulting away
from direct OpenAI API-key billing.

## Commands

Run these checks before handing off code changes:

```bash
python3 -m py_compile src/codex_imagegen_bridge/*.py scripts/doctor plugins/codex-image/scripts/codex-imagegen plugins/codex-image/scripts/doctor
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/codex-image/.claude-plugin/plugin.json >/dev/null
python3 -m pytest -q
scripts/doctor
plugins/codex-image/scripts/doctor
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

The PRD describes the production target. After `v0.1.0`, keep work focused on:

1. Installability through the standalone CLI, Claude Code plugin, and local
   marketplace paths.
2. Diagnostics and tests that do not invoke `$imagegen` or spend image quota.
3. Documentation that accurately reflects the installed `claude plugin` CLI.
4. Optional live smoke testing only after explicit user approval.
5. Regression fixes that preserve the default API-key stripping behavior.
