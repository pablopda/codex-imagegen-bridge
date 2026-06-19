# Codex Image Claude Code Plugin

This plugin exposes `/codex-image:generate`, a Claude Code skill for generating or editing one raster image through the local Codex CLI built-in `$imagegen` flow. Claude can invoke the skill when the user explicitly asks for Codex Image generation, and users can also run the slash command directly.

## Requirements

- Claude Code with plugin support.
- Codex CLI installed on `PATH`.
- `codex login` completed, preferably with ChatGPT sign-in for subscription/quota-backed usage.
- Python 3.11+ available as `python3` for the bundled scripts.

## Local Plugin Development

From the repository root, load this plugin directly for development:

```bash
claude --plugin-dir ./plugins/codex-image
```

Then invoke the skill inside Claude Code:

```text
/codex-image:generate A square app icon for a budgeting app, save to outputs/budget-icon.png
```

## Local Marketplace Install

From this repository as a local marketplace:

```text
/plugin marketplace add ./.
/plugin install codex-image@codex-imagegen-bridge
/reload-plugins
```

The equivalent Claude CLI commands from the repository root are:

```bash
claude plugin validate --strict plugins/codex-image
claude plugin marketplace add ./.
claude plugin install codex-image@codex-imagegen-bridge --scope local
claude plugin details codex-image
```

Use `./.` for the relative marketplace path. The installed Claude CLI rejects a
bare `.` source. Restart Claude Code, or run `/reload-plugins` in the active
session, before invoking a newly installed plugin command.

After installation, invoke:

```text
/codex-image:generate Restyle logo.png as a minimal app icon and save to outputs/logo-icon.png
```

## Safe Development Commands From This Plugin Directory

```bash
scripts/doctor
scripts/codex-imagegen -p "A moon poster" -f outputs/moon.png --dry-run
```

Run live generation only when you explicitly accept that it can spend image-generation quota:

```bash
scripts/codex-imagegen -p "A square app icon, teal and white, no text" -f outputs/icon.png --size square --quality high
scripts/codex-imagegen -p "Restyle this logo as a minimal app icon" -i logo.png -f outputs/logo-icon.png
```

When called from the installed skill, bundled scripts are referenced with `${CLAUDE_PLUGIN_ROOT}` so they work from Claude Code's plugin cache instead of assuming the shell is in the plugin directory.

## Quota And Billing Behavior

By default, `scripts/codex-imagegen` removes `OPENAI_API_KEY` and `CODEX_API_KEY` from the `codex exec` subprocess environment. This is intended to keep generation on the user's Codex/ChatGPT authentication path when available.

Use `--allow-api-env` only when you explicitly want API-key-backed Codex execution for that run. The plugin never calls the OpenAI Images API directly.

## Troubleshooting

Run diagnostics without spending image-generation quota:

```bash
scripts/doctor
```

Common errors:

- `codex not found`: install Codex CLI and ensure it is on `PATH`.
- `codex login status failed`: run `codex login`, then prefer ChatGPT sign-in for quota-backed usage.
- `auth type was not detectable`: inspect `codex login status` output and confirm the desired auth path.
- `output file exists`: pass `--force` only if replacing the file is intentional.
- `reference image not found`: verify each `-i/--reference` path exists and has a supported image extension.
- `output file was not created`: inspect Codex output, permissions, and the requested save path.
- `output file is empty`: inspect Codex output and retry; empty files are treated as failed generation.
