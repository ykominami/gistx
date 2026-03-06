import argparse
from typing import Any

from yklibpy.cli import Cli
from gistx.command_clone import CommandClone

class Clix:
    SETUP = "setup"
    CLONE = "clone"
    CHECK = "check"
    FIX = "fix"
    MAX_REPOS_IS_UNLIMITED = -1

    def __init__(self, description: str, command_dict: dict[str, Any]) -> None:
        self.cli = Cli(description)
        self.args: argparse.Namespace | None = None

        self.parser = self.cli.get_parser()
        subparsers = self.cli.get_subparsers('command')

        # サブコマンド "setup"
        p_setup = subparsers.add_parser(self.SETUP, help="Setup for config file")
        # setup()
        p_setup.set_defaults(func=command_dict[self.SETUP])

        # サブコマンド "clone"
        p_clone = subparsers.add_parser(self.CLONE, help="Clone all gists")
        p_clone.set_defaults(func=command_dict[self.CLONE])
        p_clone.add_argument("--public", action="store_true", help="Clone only public gists")
        p_clone.add_argument("--private", action="store_true", help="Clone only private gists")
        p_clone.add_argument("--all", action="store_true", help="Clone only all gists")
        p_clone.add_argument("--max_repos", type=int, default=CommandClone.MAX_REPOS_IS_UNLIMITED, help="Maximum number of repos to clone (-1 for all)")
        p_clone.add_argument("-v", "--verbose", action="store_true")
        p_clone.add_argument("-f", "--force", action="store_true")

        # サブコマンド "check"
        p_check = subparsers.add_parser(self.CHECK, help="Check for duplicates")
        p_check.set_defaults(func=command_dict[self.CHECK])
        p_check.add_argument("-v", "--verbose", action="store_true")
        # p_check.set_defaults(func=cmd_check)

        # サブコマンド "fix"
        p_fix = subparsers.add_parser(self.FIX, help="Fix repo directory and fetch.yml")
        p_fix.set_defaults(func=command_dict[self.FIX])
        p_fix.add_argument("-v", "--verbose", action="store_true")

    def parse_args(self) -> argparse.Namespace:
        self.args = self.parser.parse_args()
        return self.args
    
    def get_args(self) -> argparse.Namespace | None:
        return self.args

