# Codex ImageGen Bridge

Generate images through the Codex CLI built-in `$imagegen` path, so usage goes
through ChatGPT/Codex subscription limits instead of direct OpenAI API billing.

See [PRD.md](PRD.md) for the production-readiness plan for a Claude Code plugin.
See [COMPARISON.md](COMPARISON.md) for how this differs from GPT-Image2-Skill.

This project is intentionally small:

- `codex-imagegen`: CLI wrapper around `codex exec`.
- `skills/codex-imagegen`: Codex skill that tells agents to use the wrapper.
- Tests that verify command construction without making real image-generation calls.

## Requirements

- Codex CLI installed.
- Codex signed in with ChatGPT:

```bash
codex login
codex login status
```

Avoid API-key login if your goal is subscription quota. The wrapper strips
`OPENAI_API_KEY` and `CODEX_API_KEY` from the `codex exec` subprocess by default.

## Install For Local Development

```bash
cd ~/soft/codex-imagegen-bridge
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

## Usage

```bash
codex-imagegen \
  -p "A clean square app icon for a personal finance app, teal and white, no text" \
  -f outputs/finance-icon.png \
  --size square \
  --quality high
```

Reference image edit:

```bash
codex-imagegen \
  -p "Restyle this logo as a minimal flat app icon, preserve the main silhouette" \
  -i logo.png \
  -f outputs/logo-icon.png
```

Dry run:

```bash
codex-imagegen -p "A moon poster" -f outputs/moon.png --dry-run
```

## How It Works

The wrapper runs:

```bash
codex exec --sandbox workspace-write --skip-git-repo-check \
  'Use $imagegen to generate or edit exactly one raster image...'
```

Reference images are passed to Codex with `--image`.

The prompt explicitly tells Codex to use built-in `$imagegen`, save the file at
the requested path, and avoid the OpenAI API/custom scripts.

## Codex Skill

To make the skill globally available to Codex, symlink it into your user skills
directory:

```bash
mkdir -p ~/.agents/skills
ln -s ~/soft/codex-imagegen-bridge/skills/codex-imagegen ~/.agents/skills/codex-imagegen
```

Then start a new Codex session and invoke:

```text
$codex-imagegen generate a square icon for...
```

## API-Key Escape Hatch

The default is subscription-backed Codex usage. If you explicitly want to allow
API-key-backed Codex execution for a run:

```bash
codex-imagegen -p "..." -f outputs/out.png --allow-api-env
```

This does not call the OpenAI Images API directly; it only stops the wrapper from
removing API-key environment variables before launching `codex exec`.

## Verify

```bash
python3 -m py_compile src/codex_imagegen_bridge/*.py
pytest
```
