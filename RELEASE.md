# Release Notes

## 0.1.2 - 2026-06-19

### Fixed

- Treat `--force` runs as successful only when Codex creates a new non-empty output file.
- Reject non-image reference file extensions before invoking Codex.
- Print a machine-readable final result line when `--json` is used.
- Avoid fixed-name doctor writability probes that could follow a pre-existing `.write-test` symlink.
- Clarify Claude Code plugin reload and isolated local marketplace install instructions.
- Build Python artifacts, smoke-test the wheel, and validate/install the Claude plugin in CI.
- Allow Claude to invoke the Codex Image skill when the user explicitly requests image generation, instead of limiting it to manual slash-command use.
- Fix reference-image runs by terminating Codex CLI option parsing before the generated prompt, since `codex exec --image` accepts variadic image paths.

## 0.1.0 - 2026-06-13

Initial production-readiness release for the Codex ImageGen Bridge.

### Added

- Standalone `codex-imagegen` CLI that delegates to `codex exec` and prompts Codex to use built-in `$imagegen`.
- Default stripping of `OPENAI_API_KEY` and `CODEX_API_KEY`, with `--allow-api-env` as an explicit escape hatch.
- Dry-run output with command, prompt, and stripped env var names.
- Codex CLI/login diagnostics through `scripts/doctor` and the plugin-local `scripts/doctor`.
- Self-contained Claude Code plugin packaging under `plugins/codex-image/`.
- Local marketplace metadata in `.claude-plugin/marketplace.json`.
- Tests for CLI safety behavior, plugin layout, marketplace metadata, plugin script execution, and doctor dry-run checks.

### Compatibility

- Python 3.11+.
- Linux and macOS.
- Codex CLI installed and logged in, preferably with ChatGPT auth for quota-backed usage.

### Security Review

- Confirm no Codex auth files are read or printed.
- Confirm dry-run and verbose output do not include secret values.
- Confirm API-key env vars are stripped by default.
- Confirm diagnostics and tests do not invoke `$imagegen` or spend image-generation quota.

### Known Limitations

- Live smoke tests are manual and quota-consuming.
- Doctor auth-type detection depends on available `codex login status` text.
- Claude Code plugin validation requires Claude Code to be installed locally.

## Release Checklist

- [ ] `python3 -m py_compile src/codex_imagegen_bridge/*.py scripts/doctor plugins/codex-image/scripts/codex-imagegen plugins/codex-image/scripts/doctor`
- [ ] `python3 -m json.tool .claude-plugin/marketplace.json >/dev/null`
- [ ] `python3 -m json.tool plugins/codex-image/.claude-plugin/plugin.json >/dev/null`
- [ ] `python3 -m pytest -q`
- [ ] `python3 -m build`
- [ ] `codex-imagegen --help`
- [ ] `plugins/codex-image/scripts/codex-imagegen -p "A moon poster" -f outputs/moon.png --dry-run`
- [ ] `scripts/doctor`
- [ ] `plugins/codex-image/scripts/doctor`
- [ ] `claude plugin validate --strict .` when Claude Code is installed.
- [ ] `claude plugin validate --strict plugins/codex-image` when Claude Code is installed.
- [ ] Install local marketplace with `/plugin marketplace add <repo-path>` or `claude plugin marketplace add ./.`.
- [ ] Install plugin with `/plugin install codex-image@codex-imagegen-bridge`.
- [ ] Restart Claude Code or run `/reload-plugins`.
- [ ] Confirm `/codex-image:generate` is available in Claude Code.
- [ ] For a no-side-effect marketplace install check, run the commands below from the repository root:
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
- [ ] Optional live smoke only when quota use is approved: `codex-imagegen -p "Small blue circle icon" -f outputs/smoke.png --size square --quality low` and verify `outputs/smoke.png` exists and is non-empty.
- [ ] Tag the release and verify install from a clean clone or plugin cache.
