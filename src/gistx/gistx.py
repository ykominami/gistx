import argparse
import logging

from gistx.clix import Clix
from gistx.appconfigx import AppConfigx
from gistx.command_setup import CommandSetup
from gistx.command_clone import CommandClone
from gistx.command_fix import CommandFix
from yklibpy.common.loggerx import Loggerx
from yklibpy.db.appstore import AppStore
from yklibpy.db.storex import Storex

class Gistx:
    @classmethod
    def init_appstore(cls) -> AppStore:
        Storex.set_file_type_dict(AppConfigx.file_type_dict)

        appstore = AppStore("gistx", AppConfigx.file_assoc, None, AppConfigx.directory_assoc)
        appstore.prepare_config_file()
        appstore.prepare_db_file()
        appstore.prepare_db_directory()

        return appstore

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
        appstore.load_file_config_all()  # type: ignore[no-untyped-call]
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
        appstore.load_file_all()
        CommandFix(appstore).run(args)


def mainx():
    command_dict = {Clix.SETUP: Gistx.setup, Clix.CLONE: Gistx.clone, Clix.CHECK: Gistx.check, Clix.FIX: Gistx.fix}

    clix = Clix("get list of gists", command_dict)
    args = clix.parse_args()
    args.func(args)
