from __future__ import annotations

import argparse
import locale
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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


class CommandClone(Command):
    REPO_KIND_PUBLIC = "public"
    REPO_KIND_PRIVATE = "private"
    REPO_KIND_ALL = "all"
    GH_GIST_LIST_LIMIT = 1000

    def __init__(self, appstore: AppStore) -> None:
        self.appstore = appstore
        self.user = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_USER)
        self.args: argparse.Namespace | None = None
        if not self.user:
            raise ValueError("GitHub user is not configured. Run `gistx setup` first.")

    def run(self, args: argparse.Namespace, repo_kind: str) -> None:
        self.args = args
        workspace_path = self._ensure_user_workspace()
        fetch_path = workspace_path / "fetch.yaml"
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        fetched_new_list = self._should_refresh_list(fetch_path, gistlist_top_dir, bool(args.force))
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

        gist_infos = self._filter_gists(gist_info_assoc, repo_kind)
        gist_infos = self._limit_gists(gist_infos, args.max_gists)

        list_dir = gistlist_top_dir / str(list_count)
        gistrepo_top_dir = list_dir / "gistrepo"
        gistrepo_top_dir.mkdir(parents=True, exist_ok=True)
        clone_count = self._get_next_clone_count(gistrepo_top_dir)
        clone_dir = gistrepo_top_dir / str(clone_count)
        clone_dir.mkdir(parents=True, exist_ok=True)

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
        gist_info_assoc: dict[str, GistInfo] = {}
        for raw_line in stdout_str.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            gist_info = self._parse_gh_gist_list_line(line)
            if gist_info is None:
                continue
            gist_info_assoc[gist_info.gist_id] = gist_info
        return gist_info_assoc

    def _parse_gh_gist_list_line(self, line: str) -> GistInfo | None:
        parts = [part.strip() for part in TABLE_SPLIT_PATTERN.split(line) if part.strip()]
        if not parts:
            return None

        gist_id = parts[0]
        if not GIST_ID_PATTERN.match(gist_id):
            lowered = gist_id.lower()
            if lowered in {"id", "gist", "gistid"}:
                return None
            raise ValueError(f"Unable to parse gh gist list line: {line}")

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
        sanitized = WINDOWS_RESERVED_PATTERN.sub("_", name).strip().rstrip(".")
        if not sanitized:
            return "_none"
        return sanitized

    def _make_unique_dir_name(self, base_name: str, used_names: set[str]) -> str:
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

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return data

    def _save_yaml_file(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def _serialize_gist_info_assoc(self, gist_info_assoc: dict[str, GistInfo]) -> dict[str, dict[str, Any]]:
        return {
            gist_id: {
                "gist_id": gist_info.gist_id,
                "name": gist_info.name,
                "public": gist_info.public,
                "dir_name": gist_info.dir_name,
            }
            for gist_id, gist_info in gist_info_assoc.items()
        }

    def _deserialize_gist_info_assoc(self, data: dict[str, Any]) -> dict[str, GistInfo]:
        gist_info_assoc: dict[str, GistInfo] = {}
        for gist_id, item in data.items():
            if isinstance(item, GistInfo):
                gist_info_assoc[gist_id] = item
                continue
            if not isinstance(item, dict):
                raise ValueError(f"Invalid gist entry for {gist_id}: {item}")
            gist_info_assoc[gist_id] = GistInfo(
                gist_id=item.get("gist_id", gist_id),
                name=item.get("name", gist_id),
                public=bool(item.get("public", True)),
                dir_name=item.get("dir_name", ""),
            )
        return gist_info_assoc

    def _ensure_user_workspace(self) -> Path:
        workspace_path = self._get_workspace_path()
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        workspace_path.mkdir(parents=True, exist_ok=True)
        gistlist_top_dir.mkdir(parents=True, exist_ok=True)
        fetch_path = workspace_path / "fetch.yaml"
        if not fetch_path.exists():
            fetch_path.write_text("", encoding="utf-8")
        return workspace_path

    def _get_workspace_path(self) -> Path:
        if sys.platform == "win32":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            )
        else:
            local_app_data = Path.home() / ".local" / "share"
        return local_app_data / "gistx" / self.user

    def _should_refresh_list(self, fetch_path: Path, gistlist_top_dir: Path, force: bool) -> bool:
        if force:
            return True
        fetch_assoc = self._load_yaml_file(fetch_path)
        if not fetch_assoc:
            return True
        latest_list_path = self._get_latest_list_path(gistlist_top_dir)
        return latest_list_path is None or not latest_list_path.exists()

    def _execute_gh_gist_list(self, limit: int) -> str:
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
        stdout_str = self._execute_gh_gist_list(self.GH_GIST_LIST_LIMIT)
        return self._create_list_snapshot(gistlist_top_dir, stdout_str or "")

    def _decode_command_output(
        self,
        data: bytes | None,
        stream_name: str,
        command_name: str,
        hypothesis_id: str,
    ) -> str:
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
        gist_info_assoc = self._parse_gh_gist_list_output(stdout_str)
        list_count = self._get_next_numeric_dir_value(gistlist_top_dir)
        list_dir = gistlist_top_dir / str(list_count)
        list_dir.mkdir(parents=True, exist_ok=True)
        self._save_yaml_file(list_dir / "list.yaml", self._serialize_gist_info_assoc(gist_info_assoc))
        (list_dir / "gistrepo").mkdir(parents=True, exist_ok=True)
        return list_count, gist_info_assoc

    def _load_latest_list_snapshot(self, gistlist_top_dir: Path) -> tuple[int, dict[str, GistInfo]]:
        latest_list_path = self._get_latest_list_path(gistlist_top_dir)
        if latest_list_path is None or not latest_list_path.exists():
            raise FileNotFoundError(f"Latest list.yaml not found under {gistlist_top_dir}")
        list_count = int(latest_list_path.parent.name)
        data = self._load_yaml_file(latest_list_path)
        return list_count, self._deserialize_gist_info_assoc(data)

    def _get_latest_list_path(self, gistlist_top_dir: Path) -> Path | None:
        numeric_dirs = self._get_numeric_subdirs(gistlist_top_dir)
        if not numeric_dirs:
            return None
        return gistlist_top_dir / str(max(numeric_dirs)) / "list.yaml"

    def _filter_gists(self, gist_info_assoc: dict[str, GistInfo], repo_kind: str) -> list[GistInfo]:
        gist_infos = list(gist_info_assoc.values())
        if repo_kind == self.REPO_KIND_PUBLIC:
            return [gist_info for gist_info in gist_infos if gist_info.public]
        if repo_kind == self.REPO_KIND_PRIVATE:
            return [gist_info for gist_info in gist_infos if not gist_info.public]
        if repo_kind == self.REPO_KIND_ALL:
            return gist_infos
        raise ValueError(f"Invalid repo_kind: {repo_kind}")

    def _limit_gists(self, gist_infos: list[GistInfo], max_gists: int | None) -> list[GistInfo]:
        if max_gists is None:
            return gist_infos
        return gist_infos[:max_gists]

    def _get_next_clone_count(self, gistrepo_top_dir: Path) -> int:
        return self._get_next_numeric_dir_value(gistrepo_top_dir)

    def _get_next_numeric_dir_value(self, top_dir: Path) -> int:
        numeric_dirs = self._get_numeric_subdirs(top_dir)
        if not numeric_dirs:
            return 1
        return max(numeric_dirs) + 1

    def _get_numeric_subdirs(self, top_dir: Path) -> list[int]:
        if not top_dir.exists():
            return []
        values: list[int] = []
        for child in top_dir.iterdir():
            if child.is_dir() and child.name.isdigit():
                values.append(int(child.name))
        return values

    def _clone_gists(self, gist_infos: list[GistInfo], clone_dir: Path) -> tuple[int, int]:
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
        fetch_assoc = self._load_yaml_file(fetch_path)
        fetch_assoc[str(list_count)] = [timestamp, clone_target_count]
        self._save_yaml_file(fetch_path, fetch_assoc)

    def _write_progress_yaml(
        self,
        progress_path: Path,
        clone_count: int,
        summary: dict[str, object],
    ) -> None:
        progress_assoc = self._load_yaml_file(progress_path)
        progress_assoc[str(clone_count)] = summary
        self._save_yaml_file(progress_path, progress_assoc)
