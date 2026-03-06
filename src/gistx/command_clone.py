from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any, NamedTuple

import requests
from yklibpy.command.command import Command
from yklibpy.command.fetchcount import FetchCount
from yklibpy.db.appstore import AppStore
from yklibpy.common.loggerx import Loggerx

from gistx.appconfigx import AppConfigx
from gistx.gistinfo import GistInfo

class CommandClone(Command):
    REPO_KIND_PUBLIC = "public"
    REPO_KIND_PRIVATE = "private"
    REPO_KIND_ALL = "all"
    REPO_COUNT_ALL = -1
    PER_PAGE = 100
    MAX_REPOS_IS_UNLIMITED = -1
    BLANK_LIST = -1

    def __init__(self, appstore: AppStore, needness_of_refresh: bool, needness_of_top_dir: bool):
        self.appstore = appstore
        self.user = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_USER)
        self.url_api = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_URL_API)
        self.gists = self.appstore.get_from_config(AppConfigx.BASE_NAME_CONFIG, AppConfigx.KEY_GISTS)
        self.url = f"{self.url_api}/{self.user}/{self.gists}"
        self.call_git_clone = True
        self.fetchcount = FetchCount(needness_of_refresh, needness_of_top_dir, self.appstore)
        self.fetchcount_value = self.fetchcount.get()
        self.args: argparse.Namespace | None = None

    def run(self, args: argparse.Namespace, repo_kind: str) -> None:
        self.args = args
        max_repos = args.max_repos
        ret = self.clone_my_all_gists(max_repos, repo_kind)
        if ret:
            self.fetchcount.output_db()

    def get_dir_list(self, path: Path) -> list[Path]:
        return [item for item in list(path.glob("*")) if item.is_dir()]

    def get_dir_list_x(self, top_directory_path: Path) -> list[int]:
        fullpath_dir_list = self.get_dir_list(top_directory_path)
        Loggerx.debug(f"get_dir_list | fullpath_dir_list={fullpath_dir_list}", __name__)
        Loggerx.debug(f"fullpath_dir_list={fullpath_dir_list}", __name__)
        sorted_dir_list = sorted([int(p.name) for p in fullpath_dir_list], reverse=True)
        Loggerx.debug(f"sorted_dir_list={sorted_dir_list}", __name__)
        return sorted_dir_list

    def get_next_top_dir_path(self, top_directory_path: Path) -> Path :
        next_top_dir_path = None
        sorted_dir_list = self.get_dir_list_x(top_directory_path)
        if len(sorted_dir_list) == 0:
            next_top_dir = 1
            next_top_dir_path = top_directory_path / str(next_top_dir)
        else:
            current_top_dir = sorted_dir_list[0]

            if self.fetchcount.needness_of_top_dir:
                next_top_dir = current_top_dir + 1
                next_top_dir_path = top_directory_path / str(next_top_dir)
                Loggerx.debug(f"CommandClone 1 next_top_dir_path={next_top_dir_path}", __name__)
            else:
                next_top_dir_path = top_directory_path / str(current_top_dir)

        next_top_dir_path.mkdir(parents=True, exist_ok=True)

        return next_top_dir_path

    def is_valid_next_top_dir_path(self, next_top_dir_path: Path) -> bool:
        return next_top_dir_path.exists()

    class PublicAndPrivateGistInfoAssoc(NamedTuple):
        public_gist_info_assoc: dict[str, GistInfo]
        private_gist_info_assoc: dict[str, GistInfo]

    def get_public_and_private_gist_info_assoc(self, gist_info_assoc: dict[str, GistInfo]) -> PublicAndPrivateGistInfoAssoc:
        public_gist_info_assoc = {}
        private_gist_info_assoc = {}
        for k, v in gist_info_assoc.items():
            if v.public:
                public_gist_info_assoc[k] = v
            else:
                private_gist_info_assoc[k] = v
        return self.PublicAndPrivateGistInfoAssoc(public_gist_info_assoc, private_gist_info_assoc)

    def clone_my_all_gists(
        self, max_repos: int, repo_kind: str) -> bool:
        """
        GitHubの自分のpublic gistをすべて取得して clone する
        """

        Loggerx.debug(f"clone_my_all_gists | max_repos={max_repos}", __name__)
        [self.gist_info_assoc, count_of_all_repo] = self.get_gist_info_assoc(max_repos)

        publicAndPrivateGistInfoAssoc = self.get_public_and_private_gist_info_assoc(self.gist_info_assoc)
        public_gist_info_assoc = publicAndPrivateGistInfoAssoc.public_gist_info_assoc
        private_gist_info_assoc = publicAndPrivateGistInfoAssoc.private_gist_info_assoc

        repo_limit = count_of_all_repo

        repo_directory_assoc = self.appstore.get_directory_assoc_from_db(AppConfigx.BASE_NAME_REPO)
        repo_directory_path = Path( repo_directory_assoc[AppConfigx.PATH] )

        next_top_dir_path = self.get_next_top_dir_path(repo_directory_path)

        dir_level2 = 0

        dir_level1 = int(next_top_dir_path.name)
        Loggerx.debug(f"dir_level1={dir_level1}", __name__)
        sorted_dir_list_level2 = self.get_dir_list_x(next_top_dir_path)
        if len(sorted_dir_list_level2) > 0:
            dir_level2 = sorted_dir_list_level2[0]
        else:
            dir_level2 = self.fetchcount_value

        Loggerx.debug(f"dir_level1={dir_level1}", __name__)
        Loggerx.debug(f"dir_level2={dir_level2}", __name__)
        Loggerx.debug(f"sorted_dir_list_level2={sorted_dir_list_level2}", __name__)
        Loggerx.debug(f"self.fetchcount_value={self.fetchcount_value}", __name__)
        Loggerx.debug(f"self.fetchcount.needness_of_refresh={self.fetchcount.needness_of_refresh}", __name__)
        Loggerx.debug(f"self.fetchcount.needness_of_top_dir={self.fetchcount.needness_of_top_dir}", __name__)

        assert next_top_dir_path is not None

        if self.fetchcount.needness_of_refresh:
            # Githubから新規にダウンロードする必要があるのに、既存のダウンロード先をさしている場合はエラー
            if dir_level2 == self.fetchcount_value:
                raise ValueError(f"fetchcount_value={self.fetchcount_value} exists")
        else:
            # Githubから新規にダウンロードする必要がないのに、既存のダウンロード先をさしていない場合はエラー
            if dir_level2 != self.fetchcount_value:
                raise ValueError(f"fetchcount_value={self.fetchcount_value} does not exist")

        fetch_dir_path = next_top_dir_path / str(self.fetchcount_value)
        Loggerx.debug(f"CommandClone 2 fetch_dir_path={fetch_dir_path}", __name__)
        fetch_dir_path.mkdir(parents=True, exist_ok=True)

        Loggerx.debug(f"fetch_dir_path={fetch_dir_path}", __name__)
        if repo_kind == self.REPO_KIND_PUBLIC or repo_kind == self.REPO_KIND_ALL:
            public_dest_dir_path = fetch_dir_path / self.REPO_KIND_PUBLIC
            collected_public_gist_info_assoc = self.get_gist_content_with_assoc(public_gist_info_assoc, public_dest_dir_path, repo_limit)
            repo_limit -= len(list(collected_public_gist_info_assoc.keys()))
        if repo_kind == self.REPO_KIND_PRIVATE or repo_kind == self.REPO_KIND_ALL:
            private_dest_dir_path = fetch_dir_path / self.REPO_KIND_PRIVATE
            collected_private_gist_info_assoc = self.get_gist_content_with_assoc(private_gist_info_assoc, private_dest_dir_path, repo_limit)
            repo_limit -= len(list(collected_private_gist_info_assoc.keys()))

        return True

    def is_valid_gist_info_assoc(self, gist_info_assoc) -> bool:
        Loggerx.debug(f"is_valid_gist_info_assoc | gist_info_assoc={gist_info_assoc}", __name__)
        Loggerx.debug(f"is_valid_gist_info_assoc | len(gist_info_assoc)={len(gist_info_assoc)}", __name__)
        return gist_info_assoc is not None and len(gist_info_assoc) > 0

    def adjust_gist_info_assoc(self, gist_info_assoc, repo_limit: int) -> tuple[dict[str, GistInfo], int]:
        keys = gist_info_assoc.keys()
        len_of_keys = len(keys)
        if repo_limit == self.MAX_REPOS_IS_UNLIMITED:
            repo_limit = len(keys)
        else:
            if len_of_keys >= repo_limit:
                new_keys = list(keys)[:repo_limit]
                gist_info_assoc = {k: v for k, v in gist_info_assoc.items() if k in new_keys}
            else:
                repo_limit = len_of_keys

        return (gist_info_assoc, repo_limit)

    def get_gist_info_assoc(self, repo_limit: int) -> tuple[dict[str, GistInfo], int]:
        # dbディレクトリで、BASE_NAME_LISTで指定されたファイルの内容を連想配列で取得
        gist_info_assoc = self.appstore.get_file_assoc_from_db(AppConfigx.BASE_NAME_LIST)
        force = bool(getattr(self.args, "force", False))
        Loggerx.debug(f"get_gist_info_assoc | force={force} self.args={self.args}", __name__)
        ret = self.is_valid_gist_info_assoc(gist_info_assoc)
        Loggerx.debug(f"get_gist_info_assoc | ret={ret}", __name__)

        # まだ一度もGithubから取得していない、または、強制的にGithubから取得を指示された場合は、Githubから取得
        if not ret or force:
            gists = self.get_gists_from_github(repo_limit)
            # Githubから取得した結果を、GistInfoオブジェクトに変換
            from_github = True
            gist_info_assoc = self.analyze_gists(gists, from_github)
            self.appstore.output_db("list", gist_info_assoc)
            # gist_info_assocに代入された連想配列の要素数を、リミット分にする
            repo_limit = len( list(gist_info_assoc.keys()) )            

            Loggerx.debug(f"get_gist_info_assoc | gist_info_assoc={gist_info_assoc}", __name__)
        else:
            [gist_info_assoc, repo_limit] = self.adjust_gist_info_assoc(gist_info_assoc, repo_limit)
            from_github = False
            gist_info_assoc = self.analyze_gists(gist_info_assoc, from_github)

        return (gist_info_assoc, repo_limit)

    def get_gists_from_github(self, repo_limit: int) -> dict[str, dict[str, Any]]:
        session = requests.Session()
        remain_repo_count = repo_limit
        per_page = self.PER_PAGE
        if per_page > repo_limit:
            per_page = repo_limit
        page = 1
        gist_list = []
        gists: dict[str, dict[str, Any]] = {}
        kind = "public"

        while True:
            res = session.get(self.url, params={"per_page": per_page, "page": page})
            #  res.raise_for_status()
            if res.status_code != 200:
                Loggerx.error(f"Error: {res.status_code}")
                break

            batch = res.json()
            if not batch:
                break
            for g in batch:
                g["kind"] = kind

            gist_list.extend(batch)
            page += 1
            remain_repo_count -= len(batch)
            if remain_repo_count <= 0:
                break

        '''
         ['url', 'forks_url', 'commits_url', 'id', 'node_id', 'git_pull_url', 'git_push_url',
         'html_url', 'files', 'public', 'created_at', 'updated_at', 'description', 'comments',
         'user', 'comments_enabled', 'comments_url', 'owner', 'truncated', 'kind']
        '''
        # ページ単位でリモートリポジトリを取得しているため、以下でより正確にリミットを守る
        gist_list_2 = gist_list[:repo_limit]
        for g in gist_list_2:
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

        Loggerx.debug(f"get_gists_from_github | Found {len(gists)} gists", __name__)
        return gists

    def analyze_gists(self, gists: dict[str, Any], from_github:bool = False) -> dict[str, GistInfo]:
        gist_info_assoc = {}
        params: list[Any] | None = []

        for gist_id, g in gists.items():
            if isinstance(g, GistInfo):
                clone_url = g.clone_url
                if not clone_url:
                    raise ValueError(f'clone_url={clone_url}')
                gist_info_assoc[gist_id] = g
            else:
                params = self.prepare_gist_info_params(g, from_github)
                if params is not None:
                    gist_info_assoc[gist_id] = GistInfo(*params)

        return gist_info_assoc

    def prepare_gist_info_params(self, g: dict[str, Any], from_github: bool = False) -> list[Any] | None:
        gist_id = g["gist_id"]

        if from_github:
            clone_url = g['git_pull_url']
            if clone_url is None or clone_url == "":
                clone_url = g["git_push_url"]
                if clone_url is None or clone_url == "":
                    raise ValueError(f'clone_url={clone_url}')

            name = g["description"]
            if not name:
                return None
            match = re.match(r"\[(.*)\]", name)
            if not match:
                title = ""
                title_parts: list[str] = []
            else:
                title = match.group(1)
                title_parts = title.split("|")

            name_without_japanese = (
                re.sub(
                    r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F]", "", name
                )
                if name
                else ""
            )
            if not name_without_japanese:
                return None

            name_alnum = (
                "".join(c for c in name_without_japanese if c.isalnum())
                if name_without_japanese
                else ""
            )
        else:
            clone_url = g["clone_url"]
            if not clone_url:
                raise ValueError(f'clone_url={clone_url}')
            title = g["title"]
            title_parts = g["title_parts"]
            name = g["name"]
            name_without_japanese = g["name_without_japanese"]
            name_alnum = g["name_alnum"]

        public = g.get("public", True)
        return [gist_id, name, title, title_parts, name_without_japanese, name_alnum, clone_url, public]

    def get_sorted_classified(self, gist_info_assoc: dict[str, GistInfo]) -> dict[str, list[GistInfo]]:
        classified: dict[str, list[GistInfo]] = {}
        for gist_id, gist_info in gist_info_assoc.items():
            name_alnum = gist_info.name_alnum
            if name_alnum not in classified:
                classified[name_alnum] = []
            classified[name_alnum].append(gist_info)
        return classified

    def get_gist_content(self, gist_id: str, gist_info: GistInfo, dest_dir_path: Path, dir_name: str) -> None:
        safe_name = dir_name
        target_dir_path = dest_dir_path / safe_name
        Loggerx.debug(f"CommandClone 3get_gist_content | target_dir_path={target_dir_path}", __name__)
        dest_dir_path.mkdir(parents=True, exist_ok=True)

        if target_dir_path.exists():
            return

        Loggerx.debug(f"get_gist_content | [clone] {safe_name}", __name__)

        if self.call_git_clone:
            try:
                subprocess.run(
                    ["git", "clone", gist_info.clone_url, str(target_dir_path)],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                Loggerx.error(f"gist_id {gist_id}")
                Loggerx.error(f"[error] {safe_name}: {e}")
                Loggerx.error("================================================\n")
                exit(10)

    def get_gist_content_with_assoc(self, gist_info_assoc: dict[str, GistInfo], dest_dir_path: Path, repo_limit: int) -> dict[str, list[GistInfo]]:
        collected_gist_info_assoc = {}
        if repo_limit == self.MAX_REPOS_IS_UNLIMITED:
            repo_limit = len(gist_info_assoc)

        classified = self.get_sorted_classified(gist_info_assoc)
        for key, gist_infos in classified.items():
            length = len(gist_infos)
            if length > 1:
                for i in range(length):
                    if key == "":
                        dir_name = f"_none/{i}"
                    else:
                        dir_name = f"{key}-{i}"
                    gist_info = gist_infos[i]
                    gist_id = gist_info.gist_id
                    self.get_gist_content(gist_id, gist_info, dest_dir_path, dir_name)
                    gist_info.add_dir_name(dir_name)
            else:
                dir_name = f"{key}"
                gist_info = gist_infos[0]
                gist_id = gist_info.gist_id
                self.get_gist_content(gist_id, gist_info, dest_dir_path, dir_name)
                gist_info.add_dir_name(dir_name)

            collected_gist_info_assoc[key] = gist_infos

        self.appstore.output_db(AppConfigx.BASE_NAME_LIST, gist_info_assoc)

        return collected_gist_info_assoc