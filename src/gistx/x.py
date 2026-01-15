from .main import clone_my_public_gists, check_gist_info, check_gist_info_2, check_gist_info_3

username = "ykominami"
# dest_dir = "./_gist_4"
# dest_dir = "./_gist_5"
dest_dir = "./_gist_7"

def mainx():
    clone_my_public_gists(username, dest_dir)

def check3():
    check_gist_info_3(username, dest_dir)

def check2():
    check_gist_info_2(username, dest_dir)

def check():
    check_gist_info(username, dest_dir)
