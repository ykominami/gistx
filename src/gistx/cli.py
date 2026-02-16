import argparse
from typing import Any

# from gistx.appconfig import AppConfig
# from gistx.appstore import AppStore
# from gistx.storex import Storex
# from gistx.command_user import CommandUser


class Cli:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="get list of gists"
        )
        self.parser.add_argument(
            "--setup", action="store_true", help="setup for config file"
        )
        self.parser.add_argument(
            "-u", "--user", action="store_true", help="GitHub user name"
        )
        self.parser.add_argument(
            "-o","--output", default=default_output_file, help="Output file name"
        )
        self.args = self.parser.parse_args()

    def get_args(self) -> argparse.Namespace:
        return self.args

