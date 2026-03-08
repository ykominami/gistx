from __future__ import annotations

import argparse
import os
from pathlib import Path

from yklibpy.command.command import Command
from yklibpy.common.loggerx import Loggerx
from yklibpy.common.timex import Timex
from yklibpy.config.appconfig import AppConfig
from yklibpy.db.appstore import AppStore

from gistx.appconfigx import AppConfigx


class CommandFix(Command):
    def __init__(self, appstore: AppStore) -> None:
        self.appstore = appstore

    def run(self, args: argparse.Namespace) -> None:
        repo_directory_assoc = self.appstore.get_directory_assoc_from_db(AppConfigx.BASE_NAME_REPO)
        repo_path = Path(repo_directory_assoc[AppConfigx.PATH])
        if not repo_path.exists():
            raise FileNotFoundError(f"repo directory not found: {repo_path}")
        removed = self._remove_empty_dirs(repo_path)
        Loggerx.debug(f"CommandFix.run | removed {removed} empty directories", __name__)
        self._fix_fetch_yaml(repo_path)

    def _remove_empty_dirs(self, path: Path) -> int:
        removed = 0
        for dirpath_str, dirnames, filenames in os.walk(str(path), topdown=False):
            # print(f"### dirpath_str={dirpath_str}, dirnames={dirnames}, filenames={filenames}")
            dirpath = Path(dirpath_str)
            if dirpath == path:
                continue
            if not any(dirpath.iterdir()):
                dirpath.rmdir()
                removed += 1
                Loggerx.debug(f"CommandFix._remove_empty_dirs | removed: {dirpath}", __name__)
        return removed

    def _get_max_numeric_dir(self, repo_path: Path) -> int | None:
        values: list[int] = []
        for level1 in repo_path.iterdir():
            if not level1.is_dir():
                continue
            for level2 in level1.iterdir():
                if not level2.is_dir():
                    continue
                name = level2.name
                if name.isdigit():
                    val = int(name)
                    if val > 0:
                        values.append(val)
        return max(values) if values else None

    def _fix_fetch_yaml(self, repo_path: Path) -> None:
        max_dir = self._get_max_numeric_dir(repo_path)
        if max_dir is None:
            Loggerx.debug("CommandFix._fix_fetch_yaml | no numeric dirs found, skipping", __name__)
            return

        fetch_assoc: dict[str, str] = self.appstore.get_file_assoc_from_db(AppConfig.BASE_NAME_FETCH) or {}

        if str(max_dir) not in fetch_assoc:
            fetch_assoc[str(max_dir)] = Timex.get_now()

        keys_to_remove = [k for k in fetch_assoc if k.isdigit() and int(k) > max_dir]
        for k in keys_to_remove:
            del fetch_assoc[k]
            Loggerx.debug(f"CommandFix._fix_fetch_yaml | removed key: {k}", __name__)

        self.appstore.output_db(AppConfig.BASE_NAME_FETCH, fetch_assoc)
        Loggerx.debug(f"CommandFix._fix_fetch_yaml | fetch.yml updated, max_dir={max_dir}", __name__)
