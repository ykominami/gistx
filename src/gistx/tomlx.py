from pathlib import Path

from yklibpy.tomlop.tomlop import Tomlop

class Tomlx:
    """`Tomlop` を既定の呼び出し方で包む薄いラッパークラス。"""

    def __init__(self, toml_flle_path: Path, config_file_path: Path) -> None:
        """TOML 入力パスと設定ファイルパスで `Tomlop` を初期化する。"""
        self.tomlop = Tomlop()
        # self.tomlop.main()
        self.tomlop.setup(toml_flle_path, config_file_path)

    def run(self) -> None:
        """設定済みの `Tomlop` 変換処理を実行する。"""
        self.tomlop.exec()

def main() -> None:
    """既定ファイルを使って `Tomlx` を起動する。"""
    tomlx = Tomlx(Path("pyproject.toml"), Path("x.toml"))
    tomlx.run()