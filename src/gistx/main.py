from pathlib import Path
from yklibpy.common.util_yaml import UtilYaml
from .gistx import Gistx


def clone_my_public_gists(username: str, dest_dir: str | Path, flag: bool = True):
    """
    GitHubの自分のpublic gistをすべて取得して clone する
    """
    gist_info_assoc = {}

    # kind = "public"
    # kind = "private"
    # dest_kind_dir = Path(dest_dir) / kind
    dest_dir_path = Path(dest_dir)
    gistx = Gistx(username, dest_dir_path)
    gist_info_assoc = gistx.get_gist_info_assoc()
    gistx.get_gist_content_with_assoc(gist_info_assoc, dest_dir_path, flag)

    return gist_info_assoc

def check_gist_info_3(username: str, dest_dir: str | Path):
    gist_info_assoc = clone_my_public_gists(username, dest_dir, False)

    # name_alnumの値で分類
    classified = {}
    for gist_id, gist_info in gist_info_assoc.items():
        dir_name = gist_info.dir_name
        if len(dir_name) < 2:
            print(f'gist_id={gist_id} | dir_name={dir_name}')

def check_gist_info_2(username: str, dest_dir: str | Path):
    gist_info_assoc = clone_my_public_gists(username, dest_dir, False)

    # name_alnumの値で分類
    classified = {}
    for gist_id, gist_info in gist_info_assoc.items():
        clone_url = gist_info.clone_url
        if clone_url is None or clone_url == "":
            print(f'gist_id={gist_id} | clone_url={clone_url}')
            classified[gist_id] = gist_info
            for key, value in vars(gist_info).items():
                print(f'{key}={value}')
            print('========')

    return classified

def check_gist_info(username: str, dest_dir: str | Path):
    gist_info_assoc = clone_my_public_gists(username, dest_dir, False)

    # name_alnumの値で分類
    classified = {}
    for gist_id, gist_info in gist_info_assoc.items():
        name_alnum = gist_info.name_alnum
        if name_alnum not in classified.keys():
            classified[name_alnum] = []
        classified[name_alnum].append(gist_info)

    # print(classified)
    sorted_classified_keys = sorted(classified.keys())
    for name_alnum in sorted_classified_keys:
        gist_infos = classified[name_alnum]
        length = len(gist_infos)
        if length > 1:
            print(f"{name_alnum}: {length}")
            for i in range(length):
                if name_alnum == "":
                    dir_name = f"_none/{i}"
                else:
                    dir_name = f"{name_alnum}-{i}"
                gist_info = gist_infos[i]
                print(f" {dir_name} {gist_info.title}")

    return classified

