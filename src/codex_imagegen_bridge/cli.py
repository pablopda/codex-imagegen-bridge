from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

API_KEY_ENV_VARS = ("OPENAI_API_KEY", "CODEX_API_KEY")


def build_prompt(args: argparse.Namespace, output_path: Path) -> str:
    parts = [
        "Use $imagegen to generate or edit exactly one raster image.",
        f"Save the final image exactly at this path: {output_path}",
        "Use Codex built-in image generation, not the OpenAI API and not a custom image script.",
        "Create the parent directory if it does not exist.",
        "After generation, verify that the file exists at the requested path.",
        "",
        "Image request:",
        args.prompt,
    ]

    if args.size:
        parts.extend(["", f"Requested size/aspect: {args.size}"])
    if args.quality:
        parts.extend(["", f"Requested quality: {args.quality}"])
    if args.style:
        parts.extend(["", f"Style direction: {args.style}"])
    if args.reference:
        refs = "\n".join(f"- {Path(ref).resolve()}" for ref in args.reference)
        parts.extend(["", "Reference image files attached to this Codex turn:", refs])
    if args.extra_instruction:
        parts.extend(["", "Additional instructions:", args.extra_instruction])

    return "\n".join(parts)


def build_codex_command(args: argparse.Namespace, prompt: str, output_dir: Path) -> list[str]:
    cmd = [
        args.codex_bin,
        "exec",
        "--sandbox",
        args.sandbox,
        "--skip-git-repo-check",
        "--cd",
        str(output_dir),
    ]

    if args.ephemeral:
        cmd.append("--ephemeral")
    if args.model:
        cmd.extend(["--model", args.model])
    if args.json:
        cmd.append("--json")
    for ref in args.reference or []:
        cmd.extend(["--image", str(Path(ref).resolve())])

    cmd.append(prompt)
    return cmd


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codex-imagegen",
        description="Generate images through Codex CLI built-in $imagegen using ChatGPT/Codex quota.",
    )
    parser.add_argument("-p", "--prompt", required=True, help="Image generation/editing prompt.")
    parser.add_argument("-f", "--file", required=True, type=Path, help="Required output image path.")
    parser.add_argument(
        "-i",
        "--reference",
        action="append",
        type=Path,
        help="Reference image to attach to Codex. Repeat for multiple references.",
    )
    parser.add_argument("--size", help="Requested size or aspect ratio, e.g. square, portrait, 16:9, 1024x1024.")
    parser.add_argument("--quality", choices=["low", "medium", "high", "auto"], help="Requested image quality.")
    parser.add_argument("--style", help="Reusable style direction to include in the Codex prompt.")
    parser.add_argument("--extra-instruction", help="Additional instruction block for Codex.")
    parser.add_argument("--model", help="Optional Codex model override.")
    parser.add_argument("--codex-bin", default="codex", help="Codex executable path. Default: codex")
    parser.add_argument(
        "--sandbox",
        default="workspace-write",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox for codex exec. Default: workspace-write",
    )
    parser.add_argument("--ephemeral", action="store_true", default=True, help="Do not persist Codex session files.")
    parser.add_argument("--persist-session", dest="ephemeral", action="store_false", help="Persist Codex session files.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing output file.")
    parser.add_argument("--dry-run", action="store_true", help="Print the codex exec command and prompt without running it.")
    parser.add_argument("--json", action="store_true", help="Forward --json to codex exec.")
    parser.add_argument(
        "--allow-api-env",
        action="store_true",
        help="Do not strip OPENAI_API_KEY/CODEX_API_KEY from codex exec environment.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> tuple[Path, Path]:
    codex_bin = shutil.which(args.codex_bin) if os.sep not in args.codex_bin else args.codex_bin
    if not codex_bin:
        raise SystemExit("error: codex executable not found. Install Codex CLI and run `codex login`.")
    args.codex_bin = codex_bin

    for ref in args.reference or []:
        if not ref.is_file():
            raise SystemExit(f"error: reference image not found: {ref}")

    output_path = args.file.expanduser().resolve()
    if output_path.exists() and not args.force:
        raise SystemExit(f"error: output file exists, pass --force to overwrite: {output_path}")

    output_dir = output_path.parent
    if args.sandbox == "read-only" and not args.dry_run:
        raise SystemExit("error: read-only sandbox cannot write the output image")

    return output_path, output_dir


def clean_env(allow_api_env: bool) -> dict[str, str]:
    env = os.environ.copy()
    if not allow_api_env:
        for name in API_KEY_ENV_VARS:
            env.pop(name, None)
    return env


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_path, output_dir = validate_args(args)
    prompt = build_prompt(args, output_path)
    cmd = build_codex_command(args, prompt, output_dir)

    if args.dry_run:
        print(" ".join(subprocess.list2cmdline([part]) for part in cmd))
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(cmd, check=False, env=clean_env(args.allow_api_env))
    if completed.returncode != 0:
        return completed.returncode

    if not output_path.is_file():
        print(f"error: codex completed but output file was not created: {output_path}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

