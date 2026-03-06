from yklibpy.tomlop.tomlop import Tomlop
from pathlib import Path

class Tomlx:
    def __init__(self, toml_flle_path: Path, config_file_path: Path):
        self.tomlop = Tomlop()
        # self.tomlop.main()
        self.tomlop.setup(toml_flle_path, config_file_path)

    def run(self) -> None:
        self.tomlop.exec()

def main():
    tomlx = Tomlx("pyproject.toml", "x.toml")
    tomlx.run()