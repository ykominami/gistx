import subprocess
import requests
from pathlib import Path


def clone_my_public_gists(username: str, dest_dir: str | Path):
    """
    GitHubの自分のpublic gistをすべて取得して clone する
    """
    print_f = True
    # print_f = False

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    per_page = 100
    page = 1
    gists = []

    while True:
        url = f"https://api.github.com/users/{username}/gists"
        res = session.get(url, params={"per_page": per_page, "page": page})
        res.raise_for_status()

        batch = res.json()
        if not batch:
            break

        gists.extend(batch)
        page += 1

    print(f"Found {len(gists)} gists")

    for g in gists:
        clone_url = g["git_pull_url"]
        gist_id = g["id"]
        name = g["description"]
        if not name:
            name = gist_id
            print(f"gist_id {gist_id}")
            continue
        else:
            name2 = "".join(c for c in name if c.isalnum()) if name else ""
            if not name2:
                name2 = gist_id
            listx = [c if c.isalnum() else "_" for c in name2]
            sum = 0
            max = 20
            listy = []
            for c in listx:
                sum += len(c)
                if sum > max:
                    break
                listy.append(c)
            safe_name = "".join(listy)
            # safe_name = "".join(c if c.isalnum() else "_" for c in name)
            # safe_name = ("_").join([gist_id, safe_name])
        print(f"name {name}")
        print(f"safe_name {safe_name}")
        target = dest_dir / safe_name

        if target.exists():
            if print_f:
                print(f"[skip] {safe_name}")
            continue

        if print_f:
            print(f"[clone] {safe_name}")
        '''
        try:
            subprocess.run(["git", "clone", clone_url, str(target)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"gist_id {gist_id}")
            print(f"[error] {safe_name}: {e}")
            print("================================================\n")
            # continue
        '''

if __name__ == "__main__":
    username = 'ykominami'
    dest_dir = './_gist'
    clone_my_public_gists(username, dest_dir)

