from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def isolated_fix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path | str]:
    user = "fix-test-user"
    appdata = tmp_path / "appdata"
    localappdata = tmp_path / "localappdata"
    config_dir = appdata / "gistx"
    workspace = localappdata / "gistx" / user
    gistlist_top = workspace / "gistlist"
    fetch_path = workspace / "fetch.yaml"

    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("LOCALAPPDATA", str(localappdata))

    config_dir.mkdir(parents=True, exist_ok=True)
    gistlist_top.mkdir(parents=True, exist_ok=True)

    with open(config_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "gists": "gists",
                "url_api": "https://api.github.com",
                "user": user,
            },
            f,
            allow_unicode=True,
            sort_keys=False,
        )

    return {
        "repo_root": ROOT,
        "appdata": appdata,
        "localappdata": localappdata,
        "workspace": workspace,
        "gistlist_top": gistlist_top,
        "fetch_path": fetch_path,
        "user": user,
    }
