from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Mapping, cast

import yaml

from yklibpy.command.command import Command
from yklibpy.common.loggerx import Loggerx
from yklibpy.common.timex import Timex
from yklibpy.db.appstore import AppStore

from gistx.appconfigx import AppConfigx


def remove_empty_directories(root: Path) -> int:
    """指定ディレクトリ配下の空ディレクトリを再帰的に削除する。

    `root` 自体は削除せず、削除できたディレクトリ数を返す。
    """
    removed = 0
    for dirpath_str, _, _ in os.walk(str(root), topdown=False):
        dirpath = Path(dirpath_str)
        if dirpath == root:
            continue
        if not any(dirpath.iterdir()):
            dirpath.rmdir()
            removed += 1
            Loggerx.debug(f"remove_empty_directories | removed: {dirpath}", __name__)
    return removed


def collect_existing_gistlist_counts(gistlist_top_dir: Path) -> list[int]:
    """`gistlist` 直下の数値ディレクトリ名を昇順で返す。"""
    counts: list[int] = []
    for child in gistlist_top_dir.iterdir():
        if child.is_dir() and child.name.isdigit():
            counts.append(int(child.name))
    return sorted(counts)


def reconcile_fetch_entries(
    fetch_assoc: dict[str, object],
    existing_counts: list[int],
) -> dict[str, object]:
    """既存の `gistlist` 回数に合わせて `fetch.yaml` の内容を再構成する。

    `fetch_assoc` に存在しない回数は、現在時刻と 0 件を既定値として補う。
    """
    reconciled: dict[str, object] = {}
    timestamp = Timex.get_now()
    for count in existing_counts:
        key = str(count)
        if key in fetch_assoc:
            reconciled[key] = fetch_assoc[key]
        else:
            reconciled[key] = [timestamp, 0]
    return reconciled


class CommandFix(Command):
    """workspace 内の空ディレクトリと `fetch.yaml` の整合性を修復する。"""

    def __init__(self, appstore: AppStore) -> None:
        """設定済みユーザを前提に `fix` コマンドを初期化する。

        Raises:
            ValueError: GitHub ユーザが未設定の場合。
        """
        self.appstore = appstore
        user_value = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_USER)
        if not isinstance(user_value, str) or not user_value:
            raise ValueError("GitHub user is not configured. Run `gistx setup` first.")
        self.user: str = user_value

    def run(self, args: argparse.Namespace) -> None:
        """workspace を検査し、空ディレクトリ削除と `fetch.yaml` 修復を実行する。

        Raises:
            FileNotFoundError: ユーザ workspace または `gistlist` が存在しない場合。
        """
        workspace_path = self._get_workspace_path()
        if not workspace_path.is_dir():
            raise FileNotFoundError(f"user workspace not found: {workspace_path}")

        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        if not gistlist_top_dir.is_dir():
            raise FileNotFoundError(f"gistlist directory not found: {gistlist_top_dir}")

        fetch_path = workspace_path / "fetch.yaml"
        removed = self._remove_empty_dirs(gistlist_top_dir)
        Loggerx.debug(f"CommandFix.run | removed {removed} empty directories", __name__)
        existing_counts = self._collect_existing_counts(gistlist_top_dir)
        self._fix_fetch_yaml(fetch_path, existing_counts)

    def _remove_empty_dirs(self, path: Path) -> int:
        """空ディレクトリ削除のトップレベル関数を委譲実行する。"""
        return remove_empty_directories(path)

    def _collect_existing_counts(self, gistlist_top_dir: Path) -> list[int]:
        """既存 `gistlist` 回数を収集するトップレベル関数を委譲実行する。"""
        return collect_existing_gistlist_counts(gistlist_top_dir)

    def _fix_fetch_yaml(self, fetch_path: Path, existing_counts: list[int]) -> None:
        """既存回数一覧に合わせて `fetch.yaml` を保存し直す。"""
        fetch_assoc = self._load_yaml_file(fetch_path)
        reconciled = reconcile_fetch_entries(fetch_assoc, existing_counts)
        self._save_yaml_file(fetch_path, reconciled)
        Loggerx.debug(
            f"CommandFix._fix_fetch_yaml | fetch.yaml updated, counts={existing_counts}",
            __name__,
        )

    def _load_yaml_file(self, path: Path) -> dict[str, object]:
        """YAML ファイルを読み込み、mapping として返す。"""
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data_obj = yaml.safe_load(f) or {}
        if not isinstance(data_obj, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return cast(dict[str, object], data_obj)

    def _save_yaml_file(self, path: Path, data: Mapping[str, object]) -> None:
        """mapping を UTF-8 の YAML として保存する。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def _get_workspace_path(self) -> Path:
        """現在ユーザに対応する workspace パスを OS ごとに解決する。"""
        if sys.platform == "win32":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            )
        else:
            local_app_data = Path.home() / ".local" / "share"
        return local_app_data / "gistx" / self.user
