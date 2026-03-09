from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from gistx.command_fix import CommandFix
from gistx.gistx import Gistx


def test_command_fix_run_creates_fetch_yaml_when_missing(
    isolated_fix_env: dict[str, Path | str],
    monkeypatch,
) -> None:
    timestamp = "2026-03-09 12:34:56"
    monkeypatch.setattr("gistx.command_fix.Timex.get_now", lambda: timestamp)

    gistlist_top = isolated_fix_env["gistlist_top"]
    assert isinstance(gistlist_top, Path)
    (gistlist_top / "2").mkdir()
    (gistlist_top / "2" / "list.yaml").write_text("{}", encoding="utf-8")

    appstore = Gistx.init_appstore()
    Gistx._load_config_with_legacy_fallback(appstore)
    CommandFix(appstore).run(argparse.Namespace(verbose=False))

    fetch_path = isolated_fix_env["fetch_path"]
    assert isinstance(fetch_path, Path)
    with open(fetch_path, "r", encoding="utf-8") as f:
        fetch_assoc = yaml.safe_load(f)

    assert fetch_assoc == {"2": [timestamp, 0]}
