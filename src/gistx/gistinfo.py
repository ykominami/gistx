class GistInfo:
    """gist 1 件分の基本情報と clone 先ディレクトリ名を保持する。"""

    gist_id: str
    name: str
    public: bool
    dir_name: str

    def __init__(
        self,
        gist_id: str,
        name: str,
        public: bool = True,
        dir_name: str = "",
    ) -> None:
        """gist の識別子、表示名、公開状態、clone 先名を初期化する。"""
        self.gist_id = gist_id
        self.name = name
        self.public = public
        self.dir_name = dir_name

    def add_dir_name(self, dir_name: str) -> None:
        """clone 実行時に確定したディレクトリ名を設定する。"""
        self.dir_name = dir_name
