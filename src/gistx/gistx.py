import re
import subprocess
from pathlib import Path

import requests
from yklibpy.common.util import Util
from yklibpy.common.util_yaml import UtilYaml

from .gistinfo import GistInfo


class Gistx:
    _constructors_registered = False

    def __init__(self, username, dest_dir_path: Path):
        self.username = username
        self.dest_dir_path = dest_dir_path
        self.dest_none_dir_path = dest_dir_path / "_none"

        self.gists = []
        self.gist_info_assoc = {}
        self.yaml_file_name = "gist_info_3.yaml"
        self.yaml_file = Path(self.yaml_file_name)
        parent = self.yaml_file.parent
        # stem = self.yaml_file.stem
        # suffix = self.yaml_file.suffix
        # fname = f"{stem}{suffix}"
        # self.yaml_file_2 = parent / fname
        self.url = f"https://api.github.com/users/{username}/gists"
        self.print_f = True
        # self.print_f = False
        if not Gistx._constructors_registered:
            list = ["tag:yaml.org,2002:python/object:gistx.gistinfo.GistInfo"]
            UtilYaml._register_constructors(list)
            Gistx._constructors_registered = True

        self.dest_dir_path.mkdir(parents=True, exist_ok=True)
        self.dest_none_dir_path.mkdir(parents=True, exist_ok=True)

    def mkdir_dest_none_dir_path(self):
        self.dest_none_dir_path.mkdir(parents=True, exist_ok=True)

        return self.gist_info_assoc

    def get_gist_info_assoc(self):
        # python/object:gistx.gistinfo.GistInfoa
        GistInfo.yaml_file_name = self.yaml_file_name
        GistInfo.yaml_file = self.yaml_file
        # return GistInfo.load_yaml()

        if not self.yaml_file.exists():
            gists = self.get_gists_from_github()
            from_github = True
            self.gist_info_assoc = self.analyze_gists(gists, from_github)
            self.output_gist_info(self.gist_info_assoc, self.yaml_file)
        else:
            # カスタムタグを無視して辞書として読み込む
            with open(self.yaml_file, "r", encoding="utf-8") as f:
                gists = UtilYaml.safe_load(f)
                # print(f"gists={gists}")
                if isinstance(gists, list):
                    if len(gists) > 0:
                        gists = {g["gist_id"]: g for g in gists}
                    else:
                        gists = {}
                elif isinstance(gists, dict):
                    if len(gists) > 0:
                        gists = {g["gist_id"]: g for g in gists.values()}
                    else:
                        gists = {}
                else:
                    gists = {g["gist_id"]: g for g in gists}

            if gists is None:
                gists = {}

            # 辞書からGistInfoオブジェクトを構築
            self.gist_info_assoc = self.analyze_gists(gists)
        return self.gist_info_assoc

    def get_gists_from_github(self):
        session = requests.Session()
        per_page = 100
        page = 1
        gist_list = []
        gists = {}
        kind = "public"

        while True:
            res = session.get(self.url, params={"per_page": per_page, "page": page})
            res.raise_for_status()

            batch = res.json()
            if not batch:
                break
            for g in batch:
                g["kind"] = kind

            gist_list.extend(batch)
            page += 1

        if self.print_f:
            print(f"Found {len(gists)} gists")

        '''
         ['url', 'forks_url', 'commits_url', 'id', 'node_id', 'git_pull_url', 'git_push_url',
         'html_url', 'files', 'public', 'created_at', 'updated_at', 'description', 'comments',
         'user', 'comments_enabled', 'comments_url', 'owner', 'truncated', 'kind']
        '''
        for g in gist_list:
            # print(g.keys())
            if 'clone_url' in g.keys():
                clone_url = g['clone_url']
            else:
                clone_url = g['git_pull_url']
                if clone_url is None or clone_url == "":
                    clone_url = g['git_push_url']
                    if clone_url is None or clone_url == "":
                        raise ValueError(f'clone_url={clone_url}')
            g['gist_id'] = g['id']
            gists[g['id']] = g

        return gists

    def prepare_gist_info_params(self, g: dict, from_github:bool = False):
        if 'clone_url' in g.keys():
            clone_url = g["clone_url"]
        else:
            clone_url = g['git_pull_url']
            if clone_url is None or clone_url == "":
                clone_url = g['git_push_url']
                if clone_url is None or clone_url == "":
                    raise ValueError(f'clone_url={clone_url}')

        gist_id = g["gist_id"]
        name = ""
        title = ""
        title_parts = []
        name_without_japanese = ""
        name_alnum = ""

        if from_github:
            name = g["description"]
            if not name:
                # name = gist_id
                # print(f"not name | gist_id {gist_id}")
                return None
            match = re.match(r"\[(.*)\]", name)
            if not match:
                # print(f"not match | gist_id {gist_id}")
                pass
            else:
                title = match.group(1)
                # print(f"match | gist_id {gist_id} | title={title} | name={name}")
                title_parts = title.split("|")

            # 日本語文字を削除
            name_without_japanese = (
                re.sub(
                    r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F]", "", name
                )
                if name
                else ""
            )
            if not name_without_japanese:
                # name = gist_id
                # print(f"not name_without_japanese | gist_id {gist_id}")
                return None

            name_alnum = (
                "".join(c for c in name_without_japanese if c.isalnum())
                if name_without_japanese
                else ""
            )
        else:
            title = g["title"]
            title_parts = g["title_parts"]
            name = g["name"]
            name_without_japanese = g["name_without_japanese"]
            name_alnum = g["name_alnum"]

        return [gist_id, name, title, title_parts, name_without_japanese, name_alnum, clone_url]

    def analyze_gists(self, gists: dict, from_github:bool = False):
        title_parts = {}
        gist_info_assoc = {}

        for gist_id, g in gists.items():
        # for gist_id, g in gists:
            # print(f'g={g}')
            params = self.prepare_gist_info_params(g, from_github)
            if params is not None:
                gist_info_assoc[gist_id] = GistInfo(*params)
            continue
        return gist_info_assoc

    def get_sorted_classified(self, gist_info_assoc: dict):
        classified = {}
        for gist_id, gist_info in gist_info_assoc.items():
            name_alnum = gist_info.name_alnum
            if name_alnum not in classified:
                classified[name_alnum] = []
            classified[name_alnum].append(gist_info)
        return classified

    def get_gist_content_with_assoc(self, gist_info_assoc, dest_dir_path: Path, execute_f: bool):
        classified = self.get_sorted_classified(gist_info_assoc)
        for key, gist_infos in classified.items():
            length = len(gist_infos)
            if length > 1:
                # print(f"{key}: {length}")
                for i in range(length):
                    if key == "":
                        dir_name = f"_none/{i}"
                    else:
                        dir_name = f"{key}-{i}"
                    gist_info = gist_infos[i]
                    gist_id = gist_info.gist_id
                    # print(f" {dir_name} {gist_id} {gist_info.title}")
                    self.get_gist_content(gist_id, gist_info, dest_dir_path, dir_name, execute_f)
                    gist_info.add_dir_name(dir_name)
            else:
                dir_name = f"{key}"
                gist_info = gist_infos[0]
                gist_id = gist_info.gist_id
                self.get_gist_content(gist_id, gist_info, dest_dir_path, dir_name, execute_f)
                gist_info.add_dir_name(dir_name)

        self.output_gist_info(gist_info_assoc, self.yaml_file)

    def get_gist_content(self, gist_id: str, gist_info: GistInfo, dest_dir_path: Path, dir_name:str, execcute_f:bool = True):
        target_dir_path = self.dest_dir_path
        target_dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = dir_name
        target_dir_path = dest_dir_path / safe_name

        if target_dir_path.exists():
            if self.print_f:
                # print(f"[skip] {safe_name}")
                pass
            return

        if self.print_f:
            print(f"[clone] {safe_name}")

        if execcute_f:
            try:
                # for key, value in vars(gist_info).items():
                #    print(f'key={key} value={value}')

                # exit(0)
                #print(f"target_dir_path={target_dir_path}")
                subprocess.run(
                    ["git", "clone", gist_info.clone_url, str(target_dir_path)],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"gist_id {gist_id}")
                print(f"[error] {safe_name}: {e}")
                print("================================================\n")
                exit(10)
                return

    def output_gist_info(self, gist_info_assoc: dict, yaml_file: Path):
        Util.save_yaml(gist_info_assoc, yaml_file)
