from __future__ import annotations

import json
import os
import runpy
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-image"


def write_fake_codex(path: Path, login_output: str = "Signed in with ChatGPT") -> None:
    path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo codex 1.0; exit 0; fi\n"
        f"if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then echo '{login_output}'; exit 0; fi\n"
        "echo unexpected >&2; exit 99\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_plugin_layout_files_exist_and_are_executable() -> None:
    required = [
        PLUGIN / ".claude-plugin/plugin.json",
        PLUGIN / "skills/generate/SKILL.md",
        PLUGIN / "scripts/codex-imagegen",
        PLUGIN / "scripts/doctor",
        PLUGIN / "README.md",
        ROOT / ".claude-plugin/marketplace.json",
        ROOT / "scripts/doctor",
    ]

    for path in required:
        assert path.is_file(), path

    assert os.access(PLUGIN / "scripts/codex-imagegen", os.X_OK)
    assert os.access(PLUGIN / "scripts/doctor", os.X_OK)
    assert os.access(ROOT / "scripts/doctor", os.X_OK)


def test_marketplace_points_to_local_plugin_with_current_schema_fields() -> None:
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))

    assert marketplace["name"] == "codex-imagegen-bridge"
    assert marketplace["owner"] == {"name": "arkat"}
    assert marketplace["description"]
    assert marketplace["plugins"] == [
        {
            "name": "codex-image",
            "source": "./plugins/codex-image",
            "description": "Generate and edit images through Codex CLI built-in imagegen",
        }
    ]
    assert (ROOT / marketplace["plugins"][0]["source"]).is_dir()


def test_plugin_metadata_uses_current_schema_and_default_skill_discovery() -> None:
    metadata = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))

    assert metadata["name"] == "codex-image"
    assert metadata["displayName"] == "Codex Image"
    assert metadata["version"] == "0.1.0"
    assert metadata["description"]
    assert metadata["author"] == {"name": "arkat"}
    assert metadata["license"] == "MIT"
    assert "skills" not in metadata


def test_skill_frontmatter_and_plugin_root_script_paths() -> None:
    skill = (PLUGIN / "skills/generate/SKILL.md").read_text(encoding="utf-8")

    assert skill.startswith("---\n")
    assert "description:" in skill.split("---", 2)[1]
    assert "disable-model-invocation: true" in skill.split("---", 2)[1]
    assert "$ARGUMENTS" in skill
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/codex-imagegen" in skill
    assert "scripts/codex-imagegen -p" not in skill


def test_plugin_cli_script_is_synced_with_package_cli() -> None:
    package_cli = (ROOT / "src/codex_imagegen_bridge/cli.py").read_text(encoding="utf-8")
    plugin_cli = (PLUGIN / "scripts/codex-imagegen").read_text(encoding="utf-8")

    assert plugin_cli == "#!/usr/bin/env python3\n" + package_cli


def test_plugin_script_runs_dry_run_without_package_install_or_secret_leaks(tmp_path: Path) -> None:
    fake_codex = tmp_path / "codex"
    fake_codex.write_text("#!/bin/sh\necho codex fake\n", encoding="utf-8")
    fake_codex.chmod(0o755)
    script = PLUGIN / "scripts/codex-imagegen"

    result = subprocess.run(
        [
            str(script),
            "--codex-bin",
            str(fake_codex),
            "-p",
            "a moon poster",
            "-f",
            str(tmp_path / "moon.png"),
            "--dry-run",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "OPENAI_API_KEY": "sk-test-secret", "CODEX_API_KEY": "codex-test-secret"},
    )

    assert result.returncode == 0, result.stderr
    assert "Codex command:" in result.stdout
    assert "Generated Codex prompt:" in result.stdout
    assert str(fake_codex.resolve()) in result.stdout
    assert str((tmp_path / "moon.png").resolve()) in result.stdout
    assert "OPENAI_API_KEY" in result.stdout
    assert "codex fake" not in result.stdout
    assert "sk-test-secret" not in result.stdout
    assert "codex-test-secret" not in result.stdout


def test_plugin_scripts_run_from_copied_cache_directory(tmp_path: Path) -> None:
    cached_plugin = tmp_path / "cache" / "codex-image"
    shutil.copytree(PLUGIN, cached_plugin)
    fake_codex = tmp_path / "codex"
    write_fake_codex(fake_codex)

    dry_run = subprocess.run(
        [
            str(cached_plugin / "scripts/codex-imagegen"),
            "--codex-bin",
            str(fake_codex),
            "-p",
            "cache dry run",
            "-f",
            str(tmp_path / "out.png"),
            "--dry-run",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    doctor = subprocess.run(
        [str(cached_plugin / "scripts/doctor"), "--codex-bin", str(fake_codex), "--output-dir", str(tmp_path / "doctor")],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert dry_run.returncode == 0, dry_run.stderr
    assert "Generated Codex prompt:" in dry_run.stdout
    assert doctor.returncode == 0, doctor.stderr + doctor.stdout
    assert "bridge dry-run prints command and prompt" in doctor.stdout


def test_doctor_uses_bridge_dry_run_without_image_generation(tmp_path: Path) -> None:
    fake_codex = tmp_path / "codex"
    write_fake_codex(fake_codex)
    doctor = PLUGIN / "scripts/doctor"

    result = subprocess.run(
        [str(doctor), "--codex-bin", str(fake_codex), "--output-dir", str(tmp_path / "out")],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "[ok] codex found" in result.stdout
    assert "[ok] bridge dry-run prints command and prompt without invoking $imagegen" in result.stdout
    assert "unexpected" not in result.stderr


def test_doctor_auth_status_rejects_negative_auth_output() -> None:
    for path in [ROOT / "scripts/doctor", PLUGIN / "scripts/doctor"]:
        ns = runpy.run_path(str(path))
        status, message = ns["auth_status"]("not authenticated")
        assert status == "fail"
        assert "not authenticated" in message


def test_doctor_expands_output_dir_with_tilde(tmp_path: Path) -> None:
    fake_codex = tmp_path / "codex"
    write_fake_codex(fake_codex)
    home = tmp_path / "home"
    home.mkdir()
    doctor = PLUGIN / "scripts/doctor"

    result = subprocess.run(
        [str(doctor), "--codex-bin", str(fake_codex), "--output-dir", "~/doctor-out"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "HOME": str(home)},
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert str((home / "doctor-out").resolve()) in result.stdout


def test_plugin_doctor_fails_if_sibling_bridge_is_missing(tmp_path: Path) -> None:
    cached_plugin = tmp_path / "cache" / "codex-image"
    shutil.copytree(PLUGIN, cached_plugin)
    (cached_plugin / "scripts/codex-imagegen").unlink()
    fake_codex = tmp_path / "codex"
    write_fake_codex(fake_codex)

    result = subprocess.run(
        [str(cached_plugin / "scripts/doctor"), "--codex-bin", str(fake_codex), "--output-dir", str(tmp_path / "doctor")],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert "bridge script was not found" in result.stdout
