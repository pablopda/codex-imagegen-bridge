# Codex ImageGen Bridge

Generate or edit images through the Codex CLI built-in `$imagegen` path, so usage goes through ChatGPT/Codex subscription limits instead of direct OpenAI API billing by default.

Website: <https://pablopda.github.io/codex-imagegen-bridge/>

This project provides:

- `codex-imagegen`: a dependency-free Python CLI wrapper around `codex exec`.
- `plugins/codex-image`: a self-contained Claude Code plugin exposing `/codex-image:generate` and model-invocable Codex Image generation when the user explicitly asks for it.
- `skills/codex-imagegen`: a Codex skill for Codex-native use.
- Tests that verify command construction, plugin packaging, and safety defaults without live image generation.

See [PRD.md](PRD.md) for the production-readiness plan and [COMPARISON.md](COMPARISON.md) for how this differs from GPT-Image2-Skill.

## Requirements

- Linux or macOS.
- Python 3.11+.
- Codex CLI installed on `PATH`.
- Codex signed in, preferably with ChatGPT auth for subscription/quota-backed usage:

```bash
codex login
codex login status
```

Avoid API-key login if your goal is subscription quota. The bridge strips `OPENAI_API_KEY` and `CODEX_API_KEY` from the `codex exec` subprocess by default.

## Install For Local Development

```bash
git clone https://github.com/pablopda/codex-imagegen-bridge.git
cd codex-imagegen-bridge
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

For a standalone CLI install from a checkout, use an isolated virtualenv and
then verify the console entry point:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install .
codex-imagegen --help
```

The Python package installs the standalone CLI only. Install the Claude Code
plugin from this repository or a local marketplace checkout.

## Standalone CLI Usage

Generate a new image:

```bash
codex-imagegen \
  -p "A clean square app icon for a personal finance app, teal and white, no text" \
  -f outputs/finance-icon.png \
  --size square \
  --quality high
```

Edit or restyle a reference image:

```bash
codex-imagegen \
  -p "Restyle this logo as a minimal flat app icon, preserve the main silhouette" \
  -i logo.png \
  -f outputs/logo-icon.png
```

Inspect command construction without spending quota:

```bash
codex-imagegen -p "A moon poster" -f outputs/moon.png --dry-run
```

`--dry-run` prints the exact `codex exec` command, the generated Codex prompt, and the **names** of API-key environment variables that will be stripped, never their values.

## Claude Code Plugin Installation

The production plugin lives in `plugins/codex-image/` and is self-contained for Claude Code's plugin cache.

For direct local development, launch Claude Code with the plugin directory:

```bash
claude --plugin-dir ./plugins/codex-image
```

Install from this repository as a local marketplace inside Claude Code:

```text
/plugin marketplace add /path/to/codex-imagegen-bridge
/plugin install codex-image@codex-imagegen-bridge
/reload-plugins
```

The equivalent non-interactive Claude CLI commands from the repository root are:

```bash
claude plugin validate --strict .
claude plugin validate --strict plugins/codex-image
claude plugin marketplace add ./.
claude plugin install codex-image@codex-imagegen-bridge --scope local
claude plugin details codex-image
```

Use `./.` for the relative marketplace path. The installed Claude CLI rejects a
bare `.` source. Restart Claude Code, or run `/reload-plugins` in the active
session, before invoking a newly installed plugin command.

Then invoke:

```text
/codex-image:generate square icon for a budgeting app, save to outputs/budget-icon.png
```

The plugin skill delegates to:

```bash
plugins/codex-image/scripts/codex-imagegen
```

You can run plugin diagnostics directly:

```bash
plugins/codex-image/scripts/doctor
```

## How It Works

The wrapper runs `codex exec` with a least-privilege workspace sandbox:

```bash
codex exec --sandbox workspace-write --skip-git-repo-check --cd <output-directory> \
  -- 'Use $imagegen to generate or edit exactly one raster image...'
```

Reference images are passed to Codex with repeatable `--image <path>` arguments.
Reference paths must exist and use a common image extension such as `.png`,
`.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`, `.tif`, `.tiff`, `.avif`, `.heic`,
or `.heif`.

The generated prompt explicitly tells Codex to use built-in `$imagegen`, save the file at the requested path, verify it exists, and avoid the OpenAI Images API or custom scripts.

When `--json` is passed, the bridge forwards `--json` to `codex exec` and
prints a final JSON result line:

```json
{"type":"codex-imagegen-result","path":"/absolute/path/to/output.png"}
```

## ChatGPT Auth, API Keys, Quota, And Cost

By default, the bridge removes these variables from the Codex subprocess environment:

- `OPENAI_API_KEY`
- `CODEX_API_KEY`

This reduces accidental API-key-backed execution. If Codex is signed in through ChatGPT, image generation should follow Codex/ChatGPT usage limits rather than direct Images API billing.

If you explicitly want API-key-backed Codex execution for a run, use:

```bash
codex-imagegen -p "..." -f outputs/out.png --allow-api-env
```

This is an escape hatch. It does not make this project a direct OpenAI Images API client; it only stops the bridge from removing API-key environment variables before launching `codex exec`.

The bridge is not a full environment isolation tool. It strips the Codex/OpenAI
API-key variables listed above by default, while other environment variables are
still inherited by `codex exec`. Run from a clean shell if you need stricter
process isolation.

## Optional Live Smoke Test

Run live generation only when you explicitly accept Codex image-generation quota usage:

```bash
codex-imagegen -p "Small blue circle icon" -f outputs/smoke.png --size square --quality low
```

Expected result: the command exits 0 and `outputs/smoke.png` exists and is non-empty. The bridge still strips `OPENAI_API_KEY` and `CODEX_API_KEY` unless you pass `--allow-api-env`.

## Troubleshooting

Run diagnostics without generating images:

```bash
scripts/doctor
```

Common errors:

- `codex executable not found`: install Codex CLI and ensure `codex` is on `PATH`.
- `codex login status failed`: run `codex login`, then choose ChatGPT sign-in if you want quota-backed usage.
- `output file exists`: pass `--force` only if overwriting is intentional.
- `reference image not found`: verify each `-i/--reference` path exists and has a supported image extension.
- `codex completed but output file was not created`: inspect the Codex run output and retry with a clearer prompt/output path.
- `codex completed but output file is empty`: inspect the Codex run output and retry; empty files are treated as failed generation.

The doctor command checks Codex presence, `codex --version`, `codex login status`, detectable auth hints, writable output directory, and bridge dry-run construction. It never invokes `$imagegen`.

## Codex Skill

To make the Codex skill globally available to Codex, symlink it into your user skills directory:

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/codex-imagegen" ~/.agents/skills/codex-imagegen
```

Then start a new Codex session and invoke:

```text
$codex-imagegen generate a square icon for...
```

## Verify

```bash
python3 -m py_compile src/codex_imagegen_bridge/*.py scripts/doctor plugins/codex-image/scripts/codex-imagegen plugins/codex-image/scripts/doctor
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/codex-image/.claude-plugin/plugin.json >/dev/null
python3 -m pytest -q
python3 -m build
scripts/doctor
plugins/codex-image/scripts/doctor
```

When Claude Code is installed, also verify plugin packaging:

```bash
claude plugin validate --strict .
claude plugin validate --strict plugins/codex-image
```

To test marketplace installation without touching your normal Claude Code
settings or your real checkout, run it against a temporary repository copy.
Local-scope plugin installs write `.claude/settings.local.json` in the current
project, so changing only `HOME` is not enough to avoid checkout mutations:

```bash
tmp_home="$(mktemp -d)"
tmp_repo="$(mktemp -d)"
cp -a . "$tmp_repo/repo"
(
  cd "$tmp_repo/repo"
  HOME="$tmp_home" claude plugin marketplace add ./.
  HOME="$tmp_home" claude plugin install codex-image@codex-imagegen-bridge --scope local
  HOME="$tmp_home" claude plugin details codex-image
)
rm -rf "$tmp_home" "$tmp_repo"
```

Optional isolated packaging smoke test:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
codex-imagegen --help
```
