# PRD: Claude Code Skill For Codex-Backed Image Generation

## Status

Draft for implementation.

## Summary

Build a production-ready Claude Code plugin and skill that lets Claude Code users generate and edit images by delegating to the local Codex CLI built-in `$imagegen` capability.

The core product promise is:

> From Claude Code, generate or edit image assets through Codex CLI so usage follows the user's Codex/ChatGPT authentication path and general Codex image-generation limits, without requiring a local `OPENAI_API_KEY` or direct Images API billing by default.

## Source Context

- Claude Code skills are `SKILL.md`-based workflows that can be invoked directly, loaded automatically, and distributed as standalone skills or plugins.
- Claude Code plugins are the right distribution unit for reusable team/community functionality and produce namespaced commands such as `/plugin-name:skill-name`.
- Codex CLI supports image generation/editing directly. Users can ask naturally or invoke `$imagegen`; built-in image generation uses `gpt-image-2`.
- Codex image generation counts toward general Codex usage limits when Codex is signed in with ChatGPT. API-key usage applies API pricing instead.

Primary docs:

- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/plugins-reference
- https://developers.openai.com/codex/cli/features
- https://developers.openai.com/codex/pricing

## Problem

Claude Code users do not have a first-party image generation tool in the same way Codex CLI does. Users who already have Codex/ChatGPT subscription access should be able to ask Claude Code to create assets, but route the actual image generation through Codex CLI rather than:

- manually switching tools,
- copying prompts between Claude Code and Codex,
- using direct OpenAI Images API billing,
- exposing `OPENAI_API_KEY` to arbitrary project commands,
- installing a large gallery/API-first image-generation project when they only want the Codex quota path.

## Goals

1. Provide a Claude Code plugin with a reliable image-generation skill.
2. Use local Codex CLI `$imagegen` as the generation engine.
3. Default to ChatGPT/Codex quota-backed usage.
4. Avoid OpenAI API-key usage by default.
5. Support text-to-image and reference-image edits.
6. Save generated files to explicit user/project paths.
7. Provide dry-run, diagnostics, and predictable errors.
8. Package the solution so it works when installed through Claude Code plugin cache.
9. Include tests that do not spend Codex quota.

## Non-Goals

- Do not build a direct OpenAI Images API client as the default path.
- Do not replace Codex `$imagegen` prompting or model behavior.
- Do not implement batch farming or high-volume generation in v1.
- Do not require users to clone large prompt-gallery repositories.
- Do not promise exact remaining quota visibility beyond what Codex exposes.
- Do not bypass Claude Code or Codex permission models.

## Target Users

Primary:

- Developers using Claude Code who want image assets for frontend work, slide decks, docs, games, icons, placeholders, or visual mockups.
- Users with ChatGPT/Codex subscription access who want to consume included Codex limits before paying API rates.

Secondary:

- Plugin maintainers who want a reusable Claude Code extension.
- Teams that want a controlled, auditable image-generation workflow.

## User Stories

1. As a Claude Code user, I can run `/codex-image:generate "square icon for a budgeting app"` and receive a saved image path.
2. As a user, I can provide a reference image and ask Claude Code to edit or restyle it through Codex.
3. As a user, I can specify output path, size/aspect, quality, and style direction.
4. As a user, I can run a dry run to see the exact Codex command and prompt before spending quota.
5. As a user, I get a clear diagnostic if Codex CLI is missing, not logged in, or not using ChatGPT auth.
6. As a team maintainer, I can install the plugin locally or through a marketplace.
7. As a security-conscious user, I can trust the plugin not to read or forward `OPENAI_API_KEY` unless explicitly enabled.

## Product Scope

### V1 Skill Commands

The plugin should expose one primary skill:

- `/codex-image:generate`

The skill covers both generation and editing. It decides edit mode when reference image paths are present.

Potential later split:

- `/codex-image:edit`
- `/codex-image:status`
- `/codex-image:prompt`

### CLI Surface

The underlying local command should remain scriptable:

```bash
codex-imagegen \
  -p "A clean square app icon for a personal finance app, teal and white, no text" \
  -f outputs/finance-icon.png \
  --size square \
  --quality high
```

Reference edit:

```bash
codex-imagegen \
  -p "Restyle this logo as a minimal flat app icon, preserve the silhouette" \
  -i logo.png \
  -f outputs/logo-icon.png
```

Dry run:

```bash
codex-imagegen -p "A moon poster" -f outputs/moon.png --dry-run
```

### Skill Behavior

When invoked in Claude Code, the skill must:

1. Extract the user's image request.
2. Choose or ask for an output path.
3. Detect reference-image paths if present.
4. Ask at most one clarifying question only when required for path/scope.
5. Run the bridge script with explicit arguments.
6. Report the output path and relevant generation settings.
7. Never paste secrets or tokens into prompts/logs.

## Functional Requirements

### FR1: Claude Code Plugin Packaging

The repository must include a Claude Code plugin layout:

```text
plugins/codex-image/
  .claude-plugin/plugin.json
  skills/generate/SKILL.md
  scripts/codex-imagegen
  scripts/doctor
  README.md
```

The plugin must be self-contained. Claude Code installs plugins into a cache, so plugin scripts must not depend on files outside the plugin directory unless they call installed system commands like `codex`.

### FR2: Marketplace Packaging

The repository must include a local marketplace catalog:

```text
.claude-plugin/marketplace.json
```

It must point to the local plugin path:

```json
{
  "name": "codex-imagegen-bridge",
  "plugins": [
    {
      "name": "codex-image",
      "source": "./plugins/codex-image",
      "description": "Generate and edit images through Codex CLI built-in imagegen"
    }
  ]
}
```

### FR3: Codex CLI Delegation

The bridge must call `codex exec` with:

- `--sandbox workspace-write`
- `--skip-git-repo-check`
- `--cd <output-directory>`
- `--image <reference>` for each reference image
- a prompt that explicitly says to use `$imagegen`
- an exact output path

The generated Codex prompt must include:

- user prompt,
- output path,
- reference image list,
- size/aspect request when supplied,
- quality request when supplied,
- explicit instruction not to use the OpenAI Images API or custom scripts.

### FR4: ChatGPT/Codex Quota Default

The default mode must strip these variables from the Codex subprocess environment:

- `OPENAI_API_KEY`
- `CODEX_API_KEY`

This reduces accidental API-key-backed execution. The plugin may offer an explicit opt-in flag:

```bash
--allow-api-env
```

The skill must describe this as an escape hatch, not the normal path.

### FR5: Authentication Diagnostics

Provide a diagnostic command:

```bash
scripts/doctor
```

It must check:

- `codex` exists on `PATH`,
- `codex --version` exits successfully,
- `codex login status` exits successfully,
- login output indicates ChatGPT auth when detectable,
- writable output directory can be created,
- dry-run command construction works.

It must not call `$imagegen` or spend quota.

### FR6: Output Safety

The bridge must:

- require `-f/--file`,
- create parent directories,
- refuse overwrite unless `--force` is provided,
- verify output file exists after Codex returns,
- return non-zero if the output is missing,
- print the final saved path on success.

### FR7: Reference Image Support

The bridge must:

- accept repeatable `-i/--reference`,
- validate each reference path exists,
- pass references to Codex via `--image`,
- include reference paths in the prompt as context.

### FR8: Dry Run

`--dry-run` must print:

- the exact `codex exec` command,
- the exact generated Codex prompt,
- which environment variables will be stripped.

It must not call Codex.

### FR9: Logging

V1 must keep logging minimal:

- stdout: final image path on success.
- stderr: diagnostics/errors.
- optional `--verbose`: command summary with secrets redacted.

Do not log full auth files, environment dumps, access tokens, or API keys.

### FR10: Documentation

Documentation must include:

- install as local Claude Code plugin,
- install through local marketplace,
- standalone CLI usage,
- ChatGPT-auth versus API-key-auth behavior,
- quota/cost behavior,
- common errors,
- reference edit examples,
- troubleshooting `codex login`.

## Non-Functional Requirements

### Reliability

- Must work on Linux and macOS.
- Should work with Python 3.11+.
- Should not require Node.
- Should not require a Python virtualenv for plugin usage if using a bundled executable script.

### Security

- Do not read or print `~/.codex/auth.json`.
- Do not print environment variables.
- Strip API-key env vars by default.
- Use least-privilege Codex sandbox: `workspace-write`.
- Avoid `danger-full-access`.

### Performance

- Command startup should be under 1 second before the Codex process starts.
- Doctor checks should finish under 5 seconds in a healthy environment.
- Dry run should finish under 1 second.

### Maintainability

- Keep the skill body under 150 lines.
- Put complex shell/Python behavior in scripts.
- Keep tests independent from live Codex service calls.

## Proposed Architecture

```text
Claude Code
  |
  | /codex-image:generate
  v
Claude Code skill instructions
  |
  | shell command
  v
plugin scripts/codex-imagegen
  |
  | codex exec --image refs... "Use $imagegen..."
  v
Codex CLI authenticated with ChatGPT
  |
  | built-in $imagegen
  v
generated image file
```

## Implementation Plan

### Milestone 1: Productionize Current Prototype

- Move current `src/codex_imagegen_bridge/cli.py` behavior into plugin-safe script packaging.
- Add `scripts/doctor`.
- Improve `--dry-run` output.
- Add shell-safe command rendering.
- Preserve existing Python package for standalone CLI.

Acceptance:

- `pytest` passes.
- `codex-imagegen --dry-run` prints command and prompt.
- `scripts/doctor` passes on this machine without generating images.

### Milestone 2: Claude Code Plugin

- Add `plugins/codex-image/.claude-plugin/plugin.json`.
- Add `plugins/codex-image/skills/generate/SKILL.md`.
- Bundle script under `plugins/codex-image/scripts/`.
- Add local marketplace `.claude-plugin/marketplace.json`.
- Add installation docs:

```text
/plugin marketplace add ~/soft/codex-imagegen-bridge
/plugin install codex-image@codex-imagegen-bridge
/codex-image:generate
```

Acceptance:

- Claude Code discovers the plugin locally.
- `/codex-image:generate` is available.
- The skill can run a dry-run path without quota usage.

### Milestone 3: Live Image Generation Smoke Test

- Generate one small test image into `outputs/smoke.png`.
- Confirm file exists and is non-empty.
- Confirm no `OPENAI_API_KEY` was used by the bridge environment.

Acceptance:

- `outputs/smoke.png` exists.
- Command exits 0.
- README includes the exact smoke-test command and expected result.

### Milestone 4: Release Readiness

- Add GitHub Actions:
  - Python compile.
  - pytest.
  - plugin layout validation.
  - marketplace JSON validation.
- Add versioned release notes.
- Add license and security notes.

Acceptance:

- CI passes.
- Plugin can be installed from a local marketplace.
- Repo has a release checklist.

## Test Plan

### Unit Tests

- prompt construction includes `$imagegen`;
- output path is absolute and exact;
- `OPENAI_API_KEY` and `CODEX_API_KEY` are stripped by default;
- reference image args map to `codex exec --image`;
- overwrite refusal works;
- dry run avoids subprocess execution;
- missing reference image fails before Codex call.

### Integration Tests Without Quota

- `codex --version`;
- `codex login status`;
- `codex-imagegen --dry-run`;
- plugin script path can execute;
- doctor command reports all checks.

### Optional Live Tests With Quota

Run only when explicitly enabled:

```bash
CODEX_IMAGEGEN_LIVE=1 pytest tests/live
```

Live test creates one low-cost image and verifies file creation.

## Acceptance Criteria

The project is production-ready when:

1. A user can install the Claude Code plugin locally.
2. A user can invoke `/codex-image:generate`.
3. The skill generates an image through Codex CLI `$imagegen`.
4. The generated image is saved to the requested path.
5. The default path does not use `OPENAI_API_KEY` or `CODEX_API_KEY`.
6. Doctor and dry-run commands work without spending quota.
7. Tests and CI pass.
8. Docs clearly explain ChatGPT/Codex quota versus API pricing.
9. Errors are actionable and do not leak secrets.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Codex CLI changes `$imagegen` behavior | High | Keep prompt explicit, pin minimum Codex CLI version in docs, add doctor check |
| Claude Code plugin cache cannot access repo files | High | Bundle scripts inside plugin directory |
| User is logged in with API key instead of ChatGPT | High | Doctor warns; docs explain `codex login`; bridge strips API env vars |
| Live tests spend quota unexpectedly | Medium | Gate live tests behind `CODEX_IMAGEGEN_LIVE=1` |
| Image generation creates file in wrong location | Medium | Require exact output path, verify file exists |
| Claude skill over-triggers | Medium | Narrow skill description to image generation/editing only |
| Secret leakage through debug logs | High | Redact env, never print auth files |

## Open Questions

1. Should v1 include only `/codex-image:generate`, or split `/generate` and `/edit`?
2. Should the plugin bundle Python scripts, shell scripts, or both?
3. Should the project publish to a Claude Code marketplace immediately, or keep local install first?
4. Should live smoke tests default to `--quality low` if Codex accepts that prompt-level hint?
5. Should we add prompt templates for common assets like icons, banners, and UI placeholders?

## Recommended V1 Decision

Ship one plugin with one namespaced skill:

```text
/codex-image:generate
```

Keep the backend as a local Python CLI and bundle a plugin-local launcher script. Focus the first production release on reliability, installation, diagnostics, and quota-safe defaults before adding prompt galleries or advanced batching.

