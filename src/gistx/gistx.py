import argparse
import logging

from yklibpy.common.util_yaml import UtilYaml

from gistx.clix import Clix
from yklibpy.db.appstore import AppStore
from yklibpy.db.storex import Storex
from yklibpy.common.loggerx import Loggerx
from gistx.appconfigx import AppConfigx
from gistx.command_setup import CommandSetup
from gistx.command_clone import CommandClone
from gistx.command_fix import CommandFix

class Gistx:
    _constructors_registered = False

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
        print(f"args={args}")
        if args.verbose:
            Loggerx._set_log_level(logging.DEBUG)
            print(f"verbose=True")
        else:
            print(f"verbose=False")
            Loggerx._set_log_level(logging.INFO)

        repo_kind = None
        if args.public:
            if args.private:
                if args.all:
                    raise ValueError("Only one of --public, --private, --all can be specified")
                else:
                    raise ValueError("Only one of --public, --private, --all can be specified")
            else:
                if args.all:
                    raise ValueError("Only one of --public, --private, --all can be specified")
                else:
                    repo_kind = CommandClone.REPO_KIND_PUBLIC

        else:
            if args.private:
                if args.all:
                    raise ValueError("Only one of --public, --private, --all can be specified")
                else:
                    repo_kind = CommandClone.REPO_KIND_PRIVATE
            else:
                if args.all:
                    repo_kind = CommandClone.REPO_KIND_ALL
                else:
                    raise ValueError("Only one of --public, --private, --all can be specified")

        if not cls._constructors_registered:
            list = ["tag:yaml.org,2002:python/object:gistx.gistinfo.GistInfo"]
            UtilYaml._register_constructors(list)
            Gistx._constructors_registered = True

        appsstore = cls.init_appstore()
        appsstore.load_file_all()  # type: ignore[no-untyped-call]
        list_assoc = appsstore.get_file_assoc_from_db(AppConfigx.BASE_NAME_LIST)

        needness_of_top_dir = len(list_assoc) == 0
        print(f"needness_of_top_dir={needness_of_top_dir}")
        needness_of_refresh = needness_of_top_dir or args.force
        print(f"needness_of_refresh={needness_of_refresh}")
        # exit()
        Loggerx.debug(f"needness_of_top_dir={needness_of_top_dir}", __name__)
        Loggerx.debug(f"needness_of_refresh={needness_of_refresh}", __name__)
        # exit()
        command = CommandClone(appsstore, needness_of_refresh, needness_of_top_dir)

        command.run(args, repo_kind)

    @classmethod
    def check(cls, args: argparse.Namespace) -> None:
        raise NotImplementedError

    @classmethod
    def fix(cls, args: argparse.Namespace) -> None:
        if args.verbose:
            Loggerx._set_log_level(logging.DEBUG)
        else:
            Loggerx._set_log_level(logging.INFO)
        appstore = cls.init_appstore()
        appstore.load_file_all()
        CommandFix(appstore).run(args)


def mainx():
    command_dict = {Clix.SETUP: Gistx.setup, Clix.CLONE: Gistx.clone, Clix.CHECK: Gistx.check, Clix.FIX: Gistx.fix}

    clix = Clix("get list of gists", command_dict)
    args = clix.parse_args()
    args.func(args)
