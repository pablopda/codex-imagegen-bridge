# Comparison: GPT-Image2-Skill vs Codex ImageGen Bridge

## Baseline Evaluated

Baseline project:

- Repository: https://github.com/wuyoscar/GPT-Image2-Skill
- Local evaluation commit: `46c47d2`
- Evaluated focus: Claude Code/Codex image-generation workflow, CLI behavior, skill packaging, quota/auth behavior, and production readiness.

## Short Version

`GPT-Image2-Skill` is a broad prompt-gallery plus API-backed CLI and agent skill.

`codex-imagegen-bridge` is a narrow Claude Code/Codex bridge whose default job is to call Codex CLI `$imagegen` so image generation uses Codex/ChatGPT subscription limits rather than direct OpenAI API billing.

We are not trying to beat the gallery. We are improving the workflow for a different production use case: Claude Code users who want generated image files through Codex CLI with safe defaults, installable plugin packaging, diagnostics, and no API-key requirement.

## Product Difference

| Area | GPT-Image2-Skill | Codex ImageGen Bridge |
|---|---|---|
| Primary job | Prompt gallery, reusable examples, GPT Image 2 CLI, agent skill | Claude Code plugin/skill that delegates image generation to Codex CLI |
| Default backend | OpenAI Images API through Python SDK/CLI | Codex CLI built-in `$imagegen` |
| Default billing/auth path | `OPENAI_API_KEY` and API billing | ChatGPT/Codex login and Codex usage limits |
| Best for | Prompt inspiration, API users, direct image API workflows | Claude Code users wanting subscription-backed image generation |
| Prompt assets | Large curated gallery and craft references | Minimal prompt shaping; relies on Codex `$imagegen` |
| Distribution target | Codex/Claude skill plus CLI | Production Claude Code plugin plus standalone CLI |
| Output contract | CLI writes generated files from API response | Codex must save exact requested file path; wrapper verifies it |
| API-key safety | Loads `.env`/`~/.env` for `OPENAI_API_KEY` | Strips `OPENAI_API_KEY` and `CODEX_API_KEY` by default |
| Setup size | Large repo because gallery images are included | Small bridge-only project |
| Live generation cost control | API pricing controls | Codex quota/credits controls |

## What GPT-Image2-Skill Does Well

1. Strong reference gallery with concrete prompt patterns.
2. Good progressive disclosure in `skills/gpt-image/SKILL.md`.
3. Useful prompt-craft references for UI mockups, posters, diagrams, research figures, and visual styles.
4. Direct API-backed CLI is appropriate for users who want reproducible API behavior or large batches.
5. Cross-agent positioning is useful: Codex, Claude Code, and other skill-capable runtimes.

## Gaps We Are Improving

### 1. Subscription Quota Instead Of API Billing

GPT-Image2-Skill is API-first. Its CLI reads `OPENAI_API_KEY` and calls OpenAI Images endpoints.

Our improvement:

- Default to `codex exec`.
- Explicitly invoke `$imagegen`.
- Use the user's Codex CLI ChatGPT auth path.
- Strip `OPENAI_API_KEY` and `CODEX_API_KEY` by default.

### 2. Claude Code Production Packaging

GPT-Image2-Skill has Claude Code install notes, but the evaluated repo is not centered on a production Claude Code plugin with a complete local marketplace, doctor command, and plugin-cache-safe scripts.

Our improvement:

- PRD requires `plugins/codex-image/.claude-plugin/plugin.json`.
- PRD requires `.claude-plugin/marketplace.json`.
- Skill command will be namespaced as `/codex-image:generate`.
- Plugin scripts must be self-contained because Claude Code copies plugins into a cache.

### 3. Safer Secret Handling

GPT-Image2-Skill intentionally reads `OPENAI_API_KEY` from env, `.env`, then `~/.env`.

Our improvement:

- Avoid API keys by default.
- Strip API-key env vars before launching Codex.
- Add an explicit opt-in only: `--allow-api-env`.
- Never print auth files or environment dumps.

### 4. Diagnostics Before Spending Quota

GPT-Image2-Skill has useful docs, but our use case needs a clear preflight for the Codex path.

Our improvement:

- `doctor` command in the PRD.
- Checks `codex` exists, `codex --version`, `codex login status`, writable output path, and dry-run construction.
- Doctor must not invoke `$imagegen` or spend quota.

### 5. Output Contract

In the API path, the CLI controls the response bytes and writes files directly.

With Codex delegation, the child Codex run controls generation, so the wrapper must enforce the file contract.

Our improvement:

- Require `-f/--file`.
- Prompt Codex with an exact absolute output path.
- Create parent output directory.
- Refuse overwrite unless `--force`.
- Verify the file exists after Codex exits.

### 6. Small Install Footprint

The evaluated GPT-Image2-Skill checkout was large because it includes generated gallery images.

Our improvement:

- Keep the bridge small.
- No bundled gallery images in v1.
- Add prompt templates later only if they directly improve generation quality without bloating install size.

### 7. Tests Without Image Calls

GPT-Image2-Skill had no automated tests in the evaluated checkout.

Our improvement:

- Current project already has unit tests for prompt construction, env stripping, overwrite refusal, dry-run behavior, and subprocess invocation.
- PRD requires CI and plugin layout validation.
- Live image generation tests are explicitly gated behind an opt-in env var.

## What We Are Not Improving Yet

We are not replacing GPT-Image2-Skill's prompt gallery.

Potential future integration:

- Add a lightweight optional prompt-reference module.
- Link to GPT-Image2-Skill gallery as inspiration.
- Let users paste gallery prompts into our bridge.

But v1 should stay focused on reliability and Claude Code/Codex quota routing.

## Recommended Positioning

Use `GPT-Image2-Skill` when:

- you want a broad prompt gallery,
- you are comfortable with direct OpenAI API usage,
- you need API-level image-generation parameters,
- you are doing larger batch workflows.

Use `codex-imagegen-bridge` when:

- you are in Claude Code,
- you want image generation through Codex CLI,
- you want ChatGPT/Codex subscription-backed usage,
- you do not want to expose or use `OPENAI_API_KEY`,
- you want a production plugin with diagnostics and safe defaults.

## Production Improvement Thesis

The core improvement is not "better prompts." It is "better routing."

We are turning image generation into a safe, repeatable Claude Code workflow:

```text
Claude Code skill
  -> local bridge script
  -> codex exec
  -> Codex built-in $imagegen
  -> verified output file
```

That makes the behavior easier to install, audit, test, and explain to users who specifically want Codex subscription quota rather than direct API billing.

