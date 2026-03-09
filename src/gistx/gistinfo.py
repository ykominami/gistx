class GistInfo:
    def __init__(
        self,
        gist_id: str,
        name: str,
        public: bool = True,
        dir_name: str = "",
    ) -> None:
        self.gist_id = gist_id
        self.name = name
        self.public = public
        self.dir_name = dir_name

    def add_dir_name(self, dir_name: str) -> None:
        self.dir_name = dir_name
