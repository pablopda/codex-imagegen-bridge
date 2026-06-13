---
description: Generate or edit one raster image through local Codex CLI $imagegen and save it to a requested path. Use only when the user explicitly asks to create, generate, edit, restyle, or save an image asset via Codex.
disable-model-invocation: true
argument-hint: "[image request and output path]"
---

# Generate Images Through Codex

Use this skill when the user explicitly invokes `/codex-image:generate` to generate a new raster image or edit/restyle an existing image by delegating to the local Codex CLI built-in `$imagegen` capability.

## Invocation Input

User arguments: `$ARGUMENTS`

Treat `$ARGUMENTS` as the primary image request and any user-supplied output/reference hints unless the surrounding conversation provides a clearer request.

## Safety Defaults

- Do not call the OpenAI Images API directly.
- Do not read or print Codex auth files, API keys, tokens, or environment dumps.
- The plugin script strips `OPENAI_API_KEY` and `CODEX_API_KEY` from the `codex exec` subprocess by default.
- Use `--allow-api-env` only after explicit user confirmation in the current conversation.
- Use `--dry-run` when the user wants to inspect the command before spending quota.

## Workflow

1. Extract the image request from `$ARGUMENTS` and relevant surrounding context.
2. Determine the output path. If the user did not provide one and no safe default is obvious, ask one concise clarifying question.
3. Detect any reference image paths and pass each with repeatable `--reference` / `-i`.
4. Include size, aspect, quality, and style values only when supplied or clearly implied.
5. Run the plugin-local bridge script with an absolute plugin-root path:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/codex-imagegen" -p "<request>" -f "<output-path>"
   ```

6. For reference edits, run:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/codex-imagegen" -p "<edit request>" -i "<reference-path>" -f "<output-path>"
   ```

7. Report the saved output path and relevant settings. Keep logs minimal.

## Useful Options

- `--size square|portrait|landscape|16:9|1024x1024` for requested size/aspect.
- `--quality low|medium|high|auto` for requested quality.
- `--style "..."` for reusable style direction.
- `--force` only when the user approves overwriting an existing output file.
- `--dry-run` to print the exact Codex command, generated prompt, and stripped env var names without calling Codex.
- `"${CLAUDE_PLUGIN_ROOT}/scripts/doctor"` to diagnose Codex CLI install/login and dry-run command construction without image generation.

## Examples

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/codex-imagegen" \
  -p "A clean square app icon for a personal finance app, teal and white, no text" \
  -f outputs/finance-icon.png \
  --size square \
  --quality high
```

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/codex-imagegen" \
  -p "Restyle this logo as a minimal flat app icon while preserving the silhouette" \
  -i logo.png \
  -f outputs/logo-icon.png
```
