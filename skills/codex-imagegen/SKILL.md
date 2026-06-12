---
name: codex-imagegen
description: "Generate or edit raster images through Codex CLI built-in $imagegen so usage goes through ChatGPT/Codex subscription limits instead of OpenAI API billing. Use this when the user wants image assets, reference-image edits, icons, posters, banners, UI placeholders, sprites, or generated visual files and explicitly wants Codex quota/subscription usage."
---

# Codex ImageGen Bridge

Use this skill to generate or edit images through Codex built-in `$imagegen`.
This is for users who want subscription-backed Codex usage instead of local
`OPENAI_API_KEY` API billing.

## Workflow

1. Require an output path. Prefer `outputs/<short-name>.png` when the user does not specify one.
2. Use the local CLI from this project:

```bash
codex-imagegen -p "PROMPT" -f outputs/result.png
```

3. For reference images, pass each one with `-i`:

```bash
codex-imagegen -p "Restyle this as a clean app icon" -i reference.png -f outputs/icon.png
```

4. Add `--size`, `--quality`, or `--style` only when useful.
5. Do not set or rely on `OPENAI_API_KEY`. The CLI strips `OPENAI_API_KEY` and `CODEX_API_KEY` by default before launching `codex exec`.
6. Report the saved output path.

## Important Behavior

- The bridge runs `codex exec` and asks Codex to use `$imagegen`.
- Built-in Codex image generation uses `gpt-image-2` and counts toward general Codex usage limits when Codex is signed in with ChatGPT.
- API-key usage is intentionally avoided by default. Only use `--allow-api-env` if the user explicitly asks to allow API-key-backed Codex execution.
- The command refuses to overwrite existing output files unless `--force` is provided.

## Preflight

Before first use, check:

```bash
codex login status
codex --version
codex-imagegen --help
```

If Codex is not signed in with ChatGPT, ask the user to run:

```bash
codex login
```

