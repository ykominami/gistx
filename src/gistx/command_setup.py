import os
import sys
from pathlib import Path

from yklibpy.command.command import Command
from yklibpy.command.command_gh_user import CommandGhUser
from yklibpy.common.util import Util
from yklibpy.db.appstore import AppStore

from gistx.appconfigx import AppConfigx


class CommandSetup(Command):
    """`gistx` の初期設定とユーザ workspace 準備を担当する。"""

    def __init__(self, appstore: AppStore) -> None:
        """設定出力に使う `AppStore` を保持する。"""
        self.appstore = appstore

    def run(self) -> None:
        """GitHub ユーザを決定し、設定ファイルと workspace を初期化する。

        `gh` から有効なユーザ名を取得できない場合は既定値を使う。
        """
        user_value = CommandGhUser().run()
        if not isinstance(user_value, str) or Util.is_empty(user_value):
            user = CommandGhUser.DEFAULT_VALUE_USER
        else:
            user = user_value
        print(f"user={user}")
        data: dict[str, str] = {
            AppConfigx.KEY_USER: user,
            AppConfigx.KEY_URL_API: AppConfigx.DEFAULT_VALUE_URL_API,
            AppConfigx.KEY_GISTS: AppConfigx.DEFAULT_VALUE_GISTS,
        }

        self.appstore.output_config(AppConfigx.KIND_CONFIG, data)
        self._prepare_user_workspace(user)

    def _prepare_user_workspace(self, user: str) -> None:
        """ユーザ別 workspace、`gistlist`、`fetch.yaml` を初期化する。"""
        workspace_path = self._get_workspace_path(user)
        gistlist_top_dir = workspace_path / AppConfigx.BASE_NAME_GISTLIST_TOP
        workspace_path.mkdir(parents=True, exist_ok=True)
        gistlist_top_dir.mkdir(parents=True, exist_ok=True)
        fetch_path = workspace_path / "fetch.yaml"
        fetch_path.write_text("", encoding="utf-8")

    def _get_workspace_path(self, user: str) -> Path:
        """指定ユーザの workspace パスを OS ごとのデータ領域から解決する。"""
        if sys.platform == "win32":
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            )
        else:
            local_app_data = Path.home() / ".local" / "share"
        return local_app_data / "gistx" / user
