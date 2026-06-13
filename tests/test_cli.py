from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from codex_imagegen_bridge import cli


def test_build_prompt_prefers_codex_builtin_imagegen(tmp_path: Path) -> None:
    output = (tmp_path / "icon.png").resolve()
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"png")
    args = cli.parse_args(
        [
            "-p",
            "a small app icon",
            "-f",
            str(output),
            "-i",
            str(ref),
            "--size",
            "square",
            "--quality",
            "high",
        ]
    )

    prompt = cli.build_prompt(args, output)

    assert "Use $imagegen" in prompt
    assert "not the OpenAI API" in prompt
    assert "a small app icon" in prompt
    assert f"Save the final image exactly at this path: {output}" in prompt
    assert f"- {ref.resolve()}" in prompt
    assert "Requested size/aspect: square" in prompt
    assert "Requested quality: high" in prompt


def test_build_codex_command_attaches_references_in_exact_order(tmp_path: Path) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"png")
    args = cli.parse_args(["-p", "restyle it", "-f", str(tmp_path / "out.png"), "-i", str(ref)])
    args.codex_bin = "/usr/bin/codex"

    cmd = cli.build_codex_command(args, "PROMPT", tmp_path)

    assert cmd == [
        "/usr/bin/codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--cd",
        str(tmp_path),
        "--ephemeral",
        "--image",
        str(ref.resolve()),
        "PROMPT",
    ]


def test_build_codex_command_attaches_multiple_references(tmp_path: Path) -> None:
    refs = [tmp_path / "a.png", tmp_path / "b.png"]
    for ref in refs:
        ref.write_bytes(b"png")
    args = cli.parse_args(
        ["-p", "restyle it", "-f", str(tmp_path / "out.png"), "-i", str(refs[0]), "-i", str(refs[1])]
    )
    args.codex_bin = "/usr/bin/codex"

    cmd = cli.build_codex_command(args, "PROMPT", tmp_path)

    assert cmd[-5:] == ["--image", str(refs[0].resolve()), "--image", str(refs[1].resolve()), "PROMPT"]


def test_clean_env_strips_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("CODEX_API_KEY", "secret")

    env = cli.clean_env(allow_api_env=False)

    assert "OPENAI_API_KEY" not in env
    assert "CODEX_API_KEY" not in env


def test_clean_env_can_keep_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")

    env = cli.clean_env(allow_api_env=True)

    assert env["OPENAI_API_KEY"] == "secret"


def test_validate_refuses_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "out.png"
    out.write_bytes(b"existing")
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    args = cli.parse_args(["-p", "x", "-f", str(out)])

    with pytest.raises(SystemExit, match="output file exists"):
        cli.validate_args(args)


def test_validate_rejects_missing_explicit_codex_path(tmp_path: Path) -> None:
    args = cli.parse_args(["--codex-bin", str(tmp_path / "missing-codex"), "-p", "x", "-f", str(tmp_path / "out.png")])

    with pytest.raises(SystemExit, match="codex executable not found or not executable"):
        cli.validate_args(args)


def test_validate_normalizes_reference_paths_with_expanduser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    ref = home / "ref.png"
    ref.write_bytes(b"png")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    args = cli.parse_args(["-p", "x", "-f", str(tmp_path / "out.png"), "-i", "~/ref.png"])

    cli.validate_args(args)

    assert args.reference == [ref.resolve()]
    prompt = cli.build_prompt(args, tmp_path / "out.png")
    cmd = cli.build_codex_command(args, prompt, tmp_path)
    assert str(ref.resolve()) in prompt
    assert str(ref.resolve()) in cmd


def test_main_dry_run_does_not_call_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")

    def fail_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr(cli.subprocess, "run", fail_run)
    rc = cli.main(["-p", "a moon poster", "-f", str(tmp_path / "moon.png"), "--dry-run"])

    assert rc == 0
    assert "/usr/bin/codex exec" in capsys.readouterr().out


def test_main_passes_clean_env_and_prints_saved_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    out = tmp_path / "out.png"
    seen_env: dict[str, str] = {}

    def fake_run(cmd: list[str], check: bool, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
        assert check is False
        assert cmd[0] == "/usr/bin/codex"
        assert str(out.resolve()) in cmd[-1]
        seen_env.update(env)
        out.write_bytes(b"image")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["-p", "a moon poster", "-f", str(out)])

    assert rc == 0
    assert "OPENAI_API_KEY" not in seen_env
    assert out.is_file()
    assert capsys.readouterr().out.strip() == str(out.resolve())


def test_main_returns_nonzero_when_output_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    out = tmp_path / "missing.png"

    def fake_run(cmd: list[str], check: bool, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["-p", "a moon poster", "-f", str(out)])

    assert rc == 1
    assert "output file was not created" in capsys.readouterr().err


def test_main_handles_subprocess_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise OSError("boom")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["-p", "a moon poster", "-f", str(tmp_path / "out.png")])

    assert rc == 1
    assert "codex exec could not run" in capsys.readouterr().err


def test_main_can_pass_api_env_when_requested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    monkeypatch.setenv("CODEX_API_KEY", "secret")
    out = tmp_path / "out.png"
    seen_env: dict[str, str] = {}

    def fake_run(cmd: list[str], check: bool, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
        seen_env.update(env)
        out.write_bytes(b"image")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["-p", "a moon poster", "-f", str(out), "--allow-api-env"])

    assert rc == 0
    assert seen_env["CODEX_API_KEY"] == "secret"


def test_dry_run_prints_command_prompt_and_stripped_env_names_not_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("CODEX_API_KEY", "codex-test-secret")

    rc = cli.main(["-p", "a moon poster", "-f", str(tmp_path / "moon.png"), "--dry-run"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "Codex command:" in out
    assert "/usr/bin/codex exec" in out
    assert "Generated Codex prompt:" in out
    assert "a moon poster" in out
    assert "Environment variables stripped from codex exec:" in out
    assert "OPENAI_API_KEY" in out
    assert "CODEX_API_KEY" in out
    assert "sk-test-secret" not in out
    assert "codex-test-secret" not in out


def test_verbose_prints_redacted_command_without_secret_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    out = tmp_path / "out.png"

    def fake_run(cmd: list[str], check: bool, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
        out.write_bytes(b"image")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["-p", "secret prompt text", "-f", str(out), "--verbose"])

    err = capsys.readouterr().err
    assert rc == 0
    assert "<generated prompt>" in err
    assert "secret prompt text" not in err
    assert "sk-test-secret" not in err


def test_dry_run_reports_allow_api_env_escape_hatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")

    rc = cli.main(["-p", "x", "-f", str(tmp_path / "out.png"), "--dry-run", "--allow-api-env"])

    assert rc == 0
    assert "none (--allow-api-env was supplied)" in capsys.readouterr().out


def test_missing_reference_fails_before_codex_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    missing = tmp_path / "missing.png"
    args = cli.parse_args(["-p", "x", "-f", str(tmp_path / "out.png"), "-i", str(missing)])

    with pytest.raises(SystemExit, match="reference image not found"):
        cli.validate_args(args)


def test_validate_returns_absolute_output_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/codex")
    args = cli.parse_args(["-p", "x", "-f", str(tmp_path / "nested/out.png")])

    output_path, output_dir = cli.validate_args(args)

    assert output_path.is_absolute()
    assert output_path == (tmp_path / "nested/out.png").resolve()
    assert output_dir == output_path.parent
