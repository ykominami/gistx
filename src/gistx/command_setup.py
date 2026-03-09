import os
import sys
from pathlib import Path

from yklibpy.command.command import Command
from yklibpy.command.command_gh_user import CommandGhUser
from yklibpy.common.util import Util
from yklibpy.db.appstore import AppStore

from gistx.appconfigx import AppConfigx


class CommandSetup(Command):
    def __init__(self, appstore: AppStore) -> None:
        self.appstore = appstore

    def run(self) -> None:
        user = CommandGhUser().run()
        if Util.is_empty(user):
            user = CommandGhUser.DEFAULT_VALUE_USER
        print(f"user={user}")
        data = {
            AppConfigx.KEY_USER: user,
            AppConfigx.KEY_URL_API: AppConfigx.DEFAULT_VALUE_URL_API,
            AppConfigx.KEY_GISTS: AppConfigx.DEFAULT_VALUE_GISTS,
        }

        self.appstore.output_config(AppConfigx.KIND_CONFIG, data)
        self._prepare_user_workspace(user)

    def _prepare_user_workspace(self, user: str) -> None:
        workspace_path = self._get_workspace_path(user)
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        workspace_path.mkdir(parents=True, exist_ok=True)
        gistlist_top_dir.mkdir(parents=True, exist_ok=True)
        fetch_path = workspace_path / "fetch.yaml"
        fetch_path.write_text("", encoding="utf-8")

    def _get_workspace_path(self, user: str) -> Path:
        if sys.platform == "win32":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            )
        else:
            local_app_data = Path.home() / ".local" / "share"
        return local_app_data / "gistx" / user
