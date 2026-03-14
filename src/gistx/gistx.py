import argparse
import logging
from pathlib import Path
from typing import Callable, cast

import yaml

from gistx.clix import Clix
from gistx.appconfigx import AppConfigx
from gistx.command_setup import CommandSetup
from gistx.command_clone import CommandClone
from gistx.command_fix import CommandFix
from yklibpy.common.loggerx import Loggerx
from yklibpy.config.appconfig import AppConfig
from yklibpy.db.appstore import AppStore
from yklibpy.db.storex import Storex

CommandHandler = Callable[[argparse.Namespace], None]

class Gistx:
    """`gistx` CLI の各サブコマンドを起動する調停クラス。"""

    @classmethod
    def init_appstore(
        cls,
        *,
        prepare_db_file: bool = False,
        prepare_db_directory: bool = False,
    ) -> AppStore:
        """`gistx` 用の `AppStore` を初期化して返す。

        設定ファイルは常に準備し、必要に応じて DB ファイルや DB ディレクトリ
        も作成する。
        """
        Storex.set_file_type_dict(AppConfigx.file_type_dict)

        appstore = AppStore("gistx", AppConfigx.file_assoc, None, AppConfigx.directory_assoc)
        appstore.prepare_config_file()
        if prepare_db_file:
            appstore.prepare_db_file()
        if prepare_db_directory:
            appstore.prepare_db_directory()

        return appstore

    @classmethod
    def _load_config_with_legacy_fallback(cls, appstore: AppStore) -> None:
        """設定を読み込み、空なら旧 `.yml` 設定へ後方互換でフォールバックする。

        旧設定ファイルが存在しても、YAML ルートが mapping でない場合は失敗する。
        """
        appstore.load_file_config_all()  # type: ignore[no-untyped-call]
        config_assoc = appstore.get_file_assoc_from_config(AppConfigx.BASE_NAME_CONFIG) or {}
        if config_assoc:
            return

        config_store = appstore.file_assoc[AppConfig.KIND_CONFIG][AppConfigx.BASE_NAME_CONFIG][
            AppConfig.PATH
        ]
        config_path = Path(config_store.get_path())
        legacy_config_path = config_path.with_suffix(".yml")
        if not legacy_config_path.exists():
            return

        with open(legacy_config_path, "r", encoding="utf-8") as f:
            legacy_data_obj = yaml.safe_load(f) or {}
        if not isinstance(legacy_data_obj, dict):
            raise ValueError(f"Config root must be a mapping: {legacy_config_path}")
        legacy_data = cast(dict[str, object], legacy_data_obj)

        appstore.file_assoc[AppConfig.KIND_CONFIG][AppConfigx.BASE_NAME_CONFIG][AppConfig.VALUE] = legacy_data

    @classmethod
    def setup(cls, args: argparse.Namespace) -> None:
        """`setup` サブコマンドを実行して初期設定を作成する。"""
        appstore = Gistx.init_appstore()
        command = CommandSetup(appstore)
        command.run()

    @classmethod
    def clone(cls, args: argparse.Namespace) -> None:
        """`clone` サブコマンドを実行して gist の clone を開始する。

        公開範囲の指定が不正な場合や `max_gists` が 0 以下の場合は失敗する。
        """
        if args.verbose:
            Loggerx._set_log_level(logging.DEBUG)
        else:
            Loggerx._set_log_level(logging.INFO)

        flag_count = sum(1 for flag in (args.public, args.private, args.all) if flag)
        if flag_count != 1:
            raise ValueError("Exactly one of --public, --private, --all must be specified")
        if args.max_gists is not None and args.max_gists <= 0:
            raise ValueError("--max_gists must be greater than 0")

        if args.public:
            repo_kind = CommandClone.REPO_KIND_PUBLIC
        elif args.private:
            repo_kind = CommandClone.REPO_KIND_PRIVATE
        else:
            repo_kind = CommandClone.REPO_KIND_ALL

        appstore = cls.init_appstore()
        cls._load_config_with_legacy_fallback(appstore)
        command = CommandClone(appstore)
        command.run(args, repo_kind)

    @classmethod
    def check(cls, args: argparse.Namespace) -> None:
        """未実装の `check` サブコマンド。

        Raises:
            NotImplementedError: 実装されていないため常に送出する。
        """
        raise NotImplementedError

    @classmethod
    def fix(cls, args: argparse.Namespace) -> None:
        """`fix` サブコマンドを実行して作業領域の整合性を修復する。"""
        if args.verbose:
            Loggerx._set_log_level(logging.DEBUG)
        else:
            Loggerx._set_log_level(logging.INFO)

        Loggerx.debug("verbose=True", __name__)

        appstore = cls.init_appstore()
        cls._load_config_with_legacy_fallback(appstore)
        CommandFix(appstore).run(args)


def mainx() -> None:
    """CLI 引数を解析し、対応するサブコマンドハンドラを起動する。"""
    command_dict: dict[str, CommandHandler] = {
        Clix.SETUP: Gistx.setup,
        Clix.CLONE: Gistx.clone,
        Clix.CHECK: Gistx.check,
        Clix.FIX: Gistx.fix,
    }

    clix = Clix("get list of gists", command_dict)
    args = clix.parse_args()
    args.func(args)
