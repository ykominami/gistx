import argparse
from typing import Callable

from yklibpy.cli import Cli

CommandHandler = Callable[[argparse.Namespace], None]


class Clix:
    """`gistx` のサブコマンドとオプション定義を構築する。"""

    SETUP = "setup"
    CLONE = "clone"
    CHECK = "check"
    FIX = "fix"

    def __init__(self, description: str, command_dict: dict[str, CommandHandler]) -> None:
        """CLI パーサを初期化し、各サブコマンドを登録する。

        `setup`、`clone`、`check`、`fix` の各サブコマンドに対応するハンドラを
        `command_dict` から受け取り、必要なオプションを設定する。
        """
        self.cli = Cli(description)
        self.args: argparse.Namespace | None = None

        self.parser = self.cli.get_parser()
        subparsers = self.cli.get_subparsers('command')

        # サブコマンド "setup"
        p_setup = subparsers.add_parser(self.SETUP, help="Setup for config file")
        # setup()
        p_setup.set_defaults(func=command_dict[self.SETUP])

        # サブコマンド "clone"
        p_clone = subparsers.add_parser(self.CLONE, help="Clone gists")
        p_clone.set_defaults(func=command_dict[self.CLONE])
        visibility_group = p_clone.add_mutually_exclusive_group(required=True)
        visibility_group.add_argument("--public", action="store_true", help="Clone only public gists")
        visibility_group.add_argument("--private", action="store_true", help="Clone only private gists")
        visibility_group.add_argument("--all", action="store_true", help="Clone all gists")
        p_clone.add_argument("--max_gists", type=int, default=None, help="Maximum number of gists to clone")
        p_clone.add_argument("-v", "--verbose", action="store_true")
        p_clone.add_argument("-f", "--force", action="store_true")

        # サブコマンド "check"
        p_check = subparsers.add_parser(self.CHECK, help="Check for duplicates")
        p_check.set_defaults(func=command_dict[self.CHECK])
        p_check.add_argument("-v", "--verbose", action="store_true")
        # p_check.set_defaults(func=cmd_check)

        # サブコマンド "fix"
        p_fix = subparsers.add_parser(self.FIX, help="Fix gistlist directory and fetch.yaml")
        p_fix.set_defaults(func=command_dict[self.FIX])
        p_fix.add_argument("-v", "--verbose", action="store_true")

    def parse_args(self) -> argparse.Namespace:
        """コマンドライン引数を解析して `argparse.Namespace` を返す。"""
        self.args = self.parser.parse_args()
        return self.args
