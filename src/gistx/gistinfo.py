class GistInfo:
    def __init__(
        self,
        gist_id: str,
        name: str,
        title: str,
        title_parts: list,
        name_without_japanese: str,
        name_alnum: str,
        clone_url: str,
    ):
        self.gist_id = gist_id
        self.name = name
        self.title = title
        self.title_parts = title_parts
        self.name_without_japanese = name_without_japanese
        self.name_alnum = name_alnum
        self.clone_url = clone_url
        self.dir_name = ""

    def add_dir_name(self, dir_name:str):
        self.dir_name = dir_name
