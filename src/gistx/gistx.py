import argparse
import logging
from pathlib import Path

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

class Gistx:
    @classmethod
    def init_appstore(
        cls,
        *,
        prepare_db_file: bool = False,
        prepare_db_directory: bool = False,
    ) -> AppStore:
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
            legacy_data = yaml.safe_load(f) or {}
        if not isinstance(legacy_data, dict):
            raise ValueError(f"Config root must be a mapping: {legacy_config_path}")

        appstore.file_assoc[AppConfig.KIND_CONFIG][AppConfigx.BASE_NAME_CONFIG][AppConfig.VALUE] = legacy_data

    @classmethod
    def setup(cls, args: argparse.Namespace) -> None:
        appstore = Gistx.init_appstore()
        command = CommandSetup(appstore)
        command.run()

    @classmethod
    def clone(cls, args: argparse.Namespace) -> None:
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
        raise NotImplementedError

    @classmethod
    def fix(cls, args: argparse.Namespace) -> None:
        if args.verbose:
            Loggerx._set_log_level(logging.DEBUG)
            Loggerx.debug("verbose=True", __name__)
        else:
            Loggerx._set_log_level(logging.INFO)
            Loggerx.debug("verbose=False", __name__)

        appstore = cls.init_appstore()
        cls._load_config_with_legacy_fallback(appstore)
        CommandFix(appstore).run(args)


def mainx():
    command_dict = {Clix.SETUP: Gistx.setup, Clix.CLONE: Gistx.clone, Clix.CHECK: Gistx.check, Clix.FIX: Gistx.fix}

    clix = Clix("get list of gists", command_dict)
    args = clix.parse_args()
    args.func(args)
