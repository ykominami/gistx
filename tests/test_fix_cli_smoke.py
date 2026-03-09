from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def test_fix_cli_smoke_creates_missing_fetch_yaml(
    isolated_fix_env: dict[str, Path | str],
) -> None:
    repo_root = isolated_fix_env["repo_root"]
    gistlist_top = isolated_fix_env["gistlist_top"]
    fetch_path = isolated_fix_env["fetch_path"]
    appdata = isolated_fix_env["appdata"]
    localappdata = isolated_fix_env["localappdata"]

    assert isinstance(repo_root, Path)
    assert isinstance(gistlist_top, Path)
    assert isinstance(fetch_path, Path)
    assert isinstance(appdata, Path)
    assert isinstance(localappdata, Path)

    (gistlist_top / "2").mkdir()
    (gistlist_top / "2" / "list.yaml").write_text("{}", encoding="utf-8")

    env = os.environ.copy()
    env["APPDATA"] = str(appdata)
    env["LOCALAPPDATA"] = str(localappdata)

    result = subprocess.run(
        ["uv", "run", "gistx", "fix", "-v"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    with open(fetch_path, "r", encoding="utf-8") as f:
        fetch_assoc = yaml.safe_load(f)

    assert list(fetch_assoc.keys()) == ["2"]
    assert isinstance(fetch_assoc["2"], list)
    assert len(fetch_assoc["2"]) == 2
    assert fetch_assoc["2"][1] == 0
