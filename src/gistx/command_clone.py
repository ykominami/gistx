from __future__ import annotations

import argparse
import locale
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, NamedTuple, cast

import yaml
from yklibpy.command.command import Command
from yklibpy.common.loggerx import Loggerx
from yklibpy.common.timex import Timex
from yklibpy.db.appstore import AppStore

from gistx.appconfigx import AppConfigx
from gistx.gistinfo import GistInfo

GIST_ID_PATTERN = re.compile(r"^[0-9a-f]{8,}$", re.IGNORECASE)
TABLE_SPLIT_PATTERN = re.compile(r"\t+|\s{2,}")
WINDOWS_RESERVED_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

class ConfigFileInfo(NamedTuple):
    """設定ファイルの親ディレクトリと内容をまとめて保持する。"""

    parent_path: Path
    assoc: dict[str, dict[str, Any]]

class CommandClone(Command):
    """gist 一覧の取得、clone 実行、進捗記録を担当する。"""

    REPO_KIND_PUBLIC = "public"
    REPO_KIND_PRIVATE = "private"
    REPO_KIND_ALL = "all"
    GH_GIST_LIST_LIMIT = 1000

    def __init__(self, appstore: AppStore) -> None:
        """設定済みユーザを前提に clone コマンドを初期化する。

        Raises:
            ValueError: GitHub ユーザが未設定の場合。
        """
        self.appstore = appstore
        user_value = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_USER)
        if not isinstance(user_value, str) or not user_value:
            raise ValueError("GitHub user is not configured. Run `gistx setup` first.")
        self.user: str = user_value
        self.args: argparse.Namespace | None = None

    def _prepare_clone(self, force: bool) -> tuple[dict[str, GistInfo], Path, int, Path, str, int]:
        """clone 実行に必要な作業ディレクトリと gist 一覧を準備する。

        Args:
            force: 既存キャッシュを無視して gist 一覧を再取得するかどうか。

        Returns:
            gist 一覧、clone 先ディレクトリ、clone 回数、`gistlist` ディレクトリ、
            実行時刻、一覧取得回数を返す。

        Raises:
            FileNotFoundError: キャッシュ読込対象が消失し、再取得にも失敗した場合。
        """
        workspace_path = self._ensure_user_workspace()
        fetch_path = workspace_path / "fetch.yaml"
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        fetched_new_list = self._should_refresh_list(fetch_path, gistlist_top_dir, force)
        timestamp = Timex.get_now()

        if fetched_new_list:
            list_count, gist_info_assoc = self._fetch_list_snapshot(gistlist_top_dir)
        else:
            try:
                list_count, gist_info_assoc = self._load_latest_list_snapshot(gistlist_top_dir)
            except FileNotFoundError:
                # If the latest cache disappears between refresh judgment and load,
                # fall back to a fresh gist list fetch.
                fetched_new_list = True
                list_count, gist_info_assoc = self._fetch_list_snapshot(gistlist_top_dir)

        list_dir = gistlist_top_dir / str(list_count)
        gistrepo_top_dir = list_dir / "gistrepo"
        gistrepo_top_dir.mkdir(parents=True, exist_ok=True)
        clone_count = self._get_next_clone_count(gistrepo_top_dir)
        clone_dir = gistrepo_top_dir / str(clone_count)
        clone_dir.mkdir(parents=True, exist_ok=True)

        return gist_info_assoc, clone_dir, clone_count, gistlist_top_dir, timestamp, list_count

    def run(self, args: argparse.Namespace, repo_kind: str) -> None:
        """指定された公開範囲の gist を clone し、進捗情報を記録する。

        Args:
            args: `clone` サブコマンドの引数。
            repo_kind: `public`、`private`、`all` のいずれか。

        Raises:
            RuntimeError: `gh gist list` や `gh gist clone` の前提が満たせない場合。
            ValueError: 不正な `repo_kind` や設定値を検出した場合。
        """
        self.args = args
        fetch_path = self._ensure_user_workspace() / "fetch.yaml"
        fetched_new_list = self._should_refresh_list(
            fetch_path,
            self._get_workspace_path() / AppConfigx.BASE_NAME_GISTLIST_TOP,
            bool(args.force),
        )
        gist_info_assoc, clone_dir, clone_count, gistlist_top_dir, timestamp, list_count = self._prepare_clone(
            bool(args.force)
        )
        gistrepo_top_dir = clone_dir.parent

        gist_infos = self._filter_gists(gist_info_assoc, repo_kind)
        gist_infos = self._limit_gists(gist_infos, args.max_gists)

        success_count, failure_count = self._clone_gists(gist_infos, clone_dir)
        self._write_progress_yaml(
            gistrepo_top_dir / "progress.yaml",
            clone_count,
            {
                "timestamp": timestamp,
                "repo_kind": repo_kind,
                "requested_count": len(gist_infos),
                "success_count": success_count,
                "failure_count": failure_count,
                "list_count": list_count,
            },
        )

        if fetched_new_list:
            self._write_fetch_yaml(fetch_path, list_count, timestamp, len(gist_infos))

    def _parse_gh_gist_list_output(self, stdout_str: str) -> dict[str, GistInfo]:
        """`gh gist list` の標準出力全体を `GistInfo` の辞書へ変換する。

        解釈できない空行やヘッダ行は読み飛ばし、行単位の解析は
        `_parse_gh_gist_list_line()` に委譲する。
        """
        gist_info_assoc: dict[str, GistInfo] = {}
        for raw_line in stdout_str.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            print(f'CommandClone _parse_gh_gist_list_output line: {line}')
            gist_info = self._parse_gh_gist_list_line(line)
            if gist_info is None:
                continue
            gist_info_assoc[gist_info.gist_id] = gist_info
        return gist_info_assoc

    def _parse_gh_gist_list_line(self, line: str) -> GistInfo | None:
        """`gh gist list` の 1 行を解析して `GistInfo` を返す。

        Args:
            line: `gh gist list` が出力した 1 行分の文字列。

        Returns:
            解析に成功した場合は `GistInfo`、ヘッダ行や空行相当なら `None` を返す。

        Raises:
            ValueError: 可視性や gist 名を抽出できない場合。
        """
        parts = [part.strip() for part in TABLE_SPLIT_PATTERN.split(line) if part.strip()]
        if not parts:
            return None

        gist_id = parts[0]
        if not GIST_ID_PATTERN.match(gist_id):
            lowered = gist_id.lower()
            if lowered in {"id", "gist", "gistid"}:
                return None
            # raise ValueError(f"Unable to parse gh gist list line: {line}")

        visibility_idx = -1
        visibility = ""
        for idx, part in enumerate(parts):
            lowered = part.lower()
            if lowered in {"public", "secret"}:
                visibility_idx = idx
                visibility = lowered
                break

        if visibility_idx == -1:
            match = re.search(r"\b(public|secret)\b", line, flags=re.IGNORECASE)
            if match is None:
                raise ValueError(f"Visibility not found in gh gist list line: {line}")
            visibility = match.group(1).lower()
            prefix = line[: match.start()].strip()
            prefix_parts = [part.strip() for part in TABLE_SPLIT_PATTERN.split(prefix) if part.strip()]
            if len(prefix_parts) < 2:
                raise ValueError(f"Unable to parse gist name from line: {line}")
            name_parts = prefix_parts[1:-1] or prefix_parts[1:]
        else:
            if visibility_idx >= 2:
                name_parts = parts[1 : visibility_idx - 1]
                if not name_parts:
                    name_parts = parts[1:visibility_idx]
            else:
                name_parts = parts[1:2]

        name = " ".join(name_parts).strip()
        if not name:
            name = gist_id
        return GistInfo(gist_id=gist_id, name=name, public=(visibility == "public"))

    def _sanitize_gist_name(self, name: str) -> str:
        """gist 名を Windows でも使えるディレクトリ名へ正規化する。

        禁止文字を `_` に置換し、空文字になった場合は `_none` を返す。
        """
        sanitized = WINDOWS_RESERVED_PATTERN.sub("_", name).strip().rstrip(".")
        if not sanitized:
            return "_none"
        return sanitized

    def _make_unique_dir_name(self, base_name: str, used_names: set[str]) -> str:
        """重複を避ける clone 用ディレクトリ名を決定する。

        既出名と衝突する場合は `-1` 以降の連番を付与する。
        """
        if base_name not in used_names:
            used_names.add(base_name)
            return base_name

        suffix = 1
        while True:
            candidate = f"{base_name}-{suffix}"
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            suffix += 1

    def _load_yaml_file(self, path: Path) -> dict[str, object]:
        """YAML ファイルを読み込み、mapping として返す。

        ファイルが存在しない場合は空辞書を返し、ルートが mapping でない場合は
        失敗する。
        """
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

    def _serialize_gist_info_assoc(self, gist_info_assoc: dict[str, GistInfo]) -> dict[str, dict[str, object]]:
        """`GistInfo` の辞書を YAML 保存用の連想配列へ変換する。"""
        return {
            gist_id: {
                "gist_id": gist_info.gist_id,
                "name": gist_info.name,
                "public": gist_info.public,
                "dir_name": gist_info.dir_name,
            }
            for gist_id, gist_info in gist_info_assoc.items()
        }

    def _deserialize_gist_info_assoc(self, data: dict[str, object]) -> dict[str, GistInfo]:
        """YAML 由来の連想配列を `GistInfo` の辞書へ復元する。

        既に `GistInfo` が入っている場合も受け入れ、各エントリが mapping でない
        場合は失敗する。
        """
        gist_info_assoc: dict[str, GistInfo] = {}
        for gist_id, item in data.items():
            if isinstance(item, GistInfo):
                gist_info_assoc[gist_id] = item
                continue
            if not isinstance(item, dict):
                raise ValueError(f"Invalid gist entry for {gist_id}: {item}")
            item_dict = cast(dict[str, object], item)
            gist_id_value = item_dict.get("gist_id", gist_id)
            name_value = item_dict.get("name", gist_id)
            public_value = item_dict.get("public", True)
            dir_name_value = item_dict.get("dir_name", "")
            gist_info_assoc[gist_id] = GistInfo(
                gist_id=gist_id_value if isinstance(gist_id_value, str) else gist_id,
                name=name_value if isinstance(name_value, str) else gist_id,
                public=bool(public_value),
                dir_name=dir_name_value if isinstance(dir_name_value, str) else "",
            )
        return gist_info_assoc

    def _ensure_user_workspace(self) -> Path:
        """ユーザ別 workspace と初期ファイルを存在する状態にする。

        `gistlist` トップディレクトリと空の `fetch.yaml` が未作成なら生成する。
        """
        workspace_path = self._get_workspace_path()
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        workspace_path.mkdir(parents=True, exist_ok=True)
        gistlist_top_dir.mkdir(parents=True, exist_ok=True)
        fetch_path = workspace_path / "fetch.yaml"
        if not fetch_path.exists():
            fetch_path.write_text("", encoding="utf-8")
        return workspace_path

    def _get_workspace_path(self) -> Path:
        """現在のユーザに対応する workspace パスを OS ごとに解決する。"""
        if sys.platform == "win32":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            )
        else:
            local_app_data = Path.home() / ".local" / "share"
        return local_app_data / "gistx" / self.user

    def _should_refresh_list(self, fetch_path: Path, gistlist_top_dir: Path, force: bool) -> bool:
        """gist 一覧を再取得する必要があるかを判定する。

        `force` が真なら常に再取得し、それ以外では `fetch.yaml` と最新
        `list.yaml` の存在有無で判断する。
        """
        if force:
            return True
        fetch_assoc = self._load_yaml_file(fetch_path)
        if not fetch_assoc:
            return True
        latest_list_path = self._get_latest_list_path(gistlist_top_dir)
        return latest_list_path is None or not latest_list_path.exists()

    def _execute_gh_gist_list(self, limit: int) -> str:
        """`gh gist list` を実行し、標準出力を文字列で返す。

        Raises:
            RuntimeError: コマンドが失敗した場合。
        """
        result = subprocess.run(
            ["gh", "gist", "list", "--limit", str(limit)],
            check=False,
            capture_output=True,
            text=False,
        )
        stdout_text = self._decode_command_output(result.stdout, "stdout", "gh gist list", "H1")
        stderr_text = self._decode_command_output(result.stderr, "stderr", "gh gist list", "H1")
        if result.returncode != 0:
            message = stderr_text.strip() or stdout_text.strip() or "gh gist list failed"
            raise RuntimeError(message)
        return stdout_text

    def _fetch_list_snapshot(self, gistlist_top_dir: Path) -> tuple[int, dict[str, GistInfo]]:
        """最新の gist 一覧を取得して新しい `list.yaml` を作成する。"""
        stdout_str = self._execute_gh_gist_list(self.GH_GIST_LIST_LIMIT)
        return self._create_list_snapshot(gistlist_top_dir, stdout_str or "")

    def _decode_command_output(
        self,
        data: bytes | None,
        stream_name: str,
        command_name: str,
        hypothesis_id: str,
    ) -> str:
        """コマンド出力の bytes を優先エンコーディング順にデコードする。

        UTF-8 とロケール既定エンコーディングを順に試し、どちらも失敗した場合は
        置換付き UTF-8 で返す。
        """
        if not data:
            return ""

        preferred_encoding = locale.getpreferredencoding(False)
        tried_encodings = ["utf-8"]
        if preferred_encoding.lower() != "utf-8":
            tried_encodings.append(preferred_encoding)

        for encoding in tried_encodings:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue

        return data.decode("utf-8", errors="replace")

    def _create_list_snapshot(self, gistlist_top_dir: Path, stdout_str: str) -> tuple[int, dict[str, GistInfo]]:
        """取得した gist 一覧から新しい `gistlist/<count>/list.yaml` を作成する。"""
        gist_info_assoc = self._parse_gh_gist_list_output(stdout_str)
        list_count = self._get_next_numeric_dir_value(gistlist_top_dir)
        list_dir = gistlist_top_dir / str(list_count)
        list_dir.mkdir(parents=True, exist_ok=True)
        self._save_yaml_file(list_dir / "list.yaml", self._serialize_gist_info_assoc(gist_info_assoc))
        (list_dir / "gistrepo").mkdir(parents=True, exist_ok=True)
        return list_count, gist_info_assoc

    def _load_latest_list_snapshot(self, gistlist_top_dir: Path) -> tuple[int, dict[str, GistInfo]]:
        """最新の `list.yaml` を読み込み、その回数と gist 一覧を返す。

        Raises:
            FileNotFoundError: 読み込むべき `list.yaml` が存在しない場合。
        """
        latest_list_path = self._get_latest_list_path(gistlist_top_dir)
        if latest_list_path is None or not latest_list_path.exists():
            raise FileNotFoundError(f"Latest list.yaml not found under {gistlist_top_dir}")
        list_count = int(latest_list_path.parent.name)
        data = self._load_yaml_file(latest_list_path)
        return list_count, self._deserialize_gist_info_assoc(data)

    def _get_latest_list_path(self, gistlist_top_dir: Path) -> Path | None:
        """`gistlist` 配下で最大の数値ディレクトリにある `list.yaml` を返す。"""
        numeric_dirs = self._get_numeric_subdirs(gistlist_top_dir)
        if not numeric_dirs:
            return None
        return gistlist_top_dir / str(max(numeric_dirs)) / "list.yaml"

    def _filter_gists(self, gist_info_assoc: dict[str, GistInfo], repo_kind: str) -> list[GistInfo]:
        """公開範囲の指定に応じて gist 一覧を絞り込む。

        Raises:
            ValueError: 想定外の `repo_kind` が渡された場合。
        """
        gist_infos = list(gist_info_assoc.values())
        if repo_kind == self.REPO_KIND_PUBLIC:
            return [gist_info for gist_info in gist_infos if gist_info.public]
        if repo_kind == self.REPO_KIND_PRIVATE:
            return [gist_info for gist_info in gist_infos if not gist_info.public]
        if repo_kind == self.REPO_KIND_ALL:
            return gist_infos
        raise ValueError(f"Invalid repo_kind: {repo_kind}")

    def _limit_gists(self, gist_infos: list[GistInfo], max_gists: int | None) -> list[GistInfo]:
        """上限件数が指定されていれば先頭からその件数に制限する。"""
        if max_gists is None:
            return gist_infos
        return gist_infos[:max_gists]

    def _get_next_clone_count(self, gistrepo_top_dir: Path) -> int:
        """次に使う clone 回数ディレクトリ名を返す。"""
        return self._get_next_numeric_dir_value(gistrepo_top_dir)

    def _get_next_numeric_dir_value(self, top_dir: Path) -> int:
        """数値名ディレクトリ群の最大値に 1 を足した値を返す。"""
        numeric_dirs = self._get_numeric_subdirs(top_dir)
        if not numeric_dirs:
            return 1
        return max(numeric_dirs) + 1

    def _get_numeric_subdirs(self, top_dir: Path) -> list[int]:
        """直下にある数値名ディレクトリを整数一覧として収集する。"""
        if not top_dir.exists():
            return []
        values: list[int] = []
        for child in top_dir.iterdir():
            if child.is_dir() and child.name.isdigit():
                values.append(int(child.name))
        return values

    def _clone_gists(self, gist_infos: list[GistInfo], clone_dir: Path) -> tuple[int, int]:
        """指定された gist 群を clone し、成功件数と失敗件数を返す。

        既に clone 先ディレクトリが存在する gist は失敗として数える。
        """
        used_names: set[str] = set()
        success_count = 0
        failure_count = 0

        for gist_info in gist_infos:
            visibility_dir = self.REPO_KIND_PUBLIC if gist_info.public else self.REPO_KIND_PRIVATE
            dest_dir = clone_dir / visibility_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            dir_name = self._make_unique_dir_name(self._sanitize_gist_name(gist_info.name), used_names)
            gist_info.add_dir_name(dir_name)
            target_dir = dest_dir / dir_name

            if target_dir.exists():
                failure_count += 1
                Loggerx.error(f"Clone target already exists: {target_dir}", __name__)
                continue

            result = subprocess.run(
                ["gh", "gist", "clone", gist_info.gist_id, str(target_dir)],
                check=False,
                capture_output=True,
                text=False,
            )
            stdout_text = self._decode_command_output(result.stdout, "stdout", "gh gist clone", "H2")
            stderr_text = self._decode_command_output(result.stderr, "stderr", "gh gist clone", "H2")
            if result.returncode == 0:
                success_count += 1
            else:
                failure_count += 1
                Loggerx.error(
                    f"Failed to clone gist {gist_info.gist_id}: {stderr_text.strip() or stdout_text.strip()}",
                    __name__,
                )

        return success_count, failure_count

    def _write_fetch_yaml(
        self,
        fetch_path: Path,
        list_count: int,
        timestamp: str,
        clone_target_count: int,
    ) -> None:
        """`fetch.yaml` に一覧取得回数ごとの取得時刻と対象件数を記録する。"""
        fetch_assoc = self._load_yaml_file(fetch_path)
        fetch_assoc[str(list_count)] = [timestamp, clone_target_count]
        self._save_yaml_file(fetch_path, fetch_assoc)

    def _write_progress_yaml(
        self,
        progress_path: Path,
        clone_count: int,
        summary: dict[str, object],
    ) -> None:
        """`progress.yaml` に clone 回ごとの実行結果要約を記録する。"""
        progress_assoc = self._load_yaml_file(progress_path)
        progress_assoc[str(clone_count)] = summary
        self._save_yaml_file(progress_path, progress_assoc)
