from pathlib import Path

from yklibpy.tomlop.tomlop import Tomlop

def main() -> None:
    """既定ファイルを使って `Tomlop` を実行する。"""
    tomlop = Tomlop()
    tomlop.setup(Path("pyproject.toml"), Path("x.toml"))
    tomlop.exec()