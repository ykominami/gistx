# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gistx` is a Python CLI tool that clones all public/private GitHub Gists from a configured user to a local directory. It fetches gist metadata via the GitHub API, processes descriptions to extract titles, handles naming conflicts, and clones repositories using git.

## Commands

### Installation and Setup
```bash
uv sync
uv pip install -e .
```

### First-time Configuration
```bash
# Interactive setup: detects GitHub user via `gh` CLI and writes config
gistx setup
```

### Running the Tool
```bash
# Clone public gists
gistx clone --public

# Clone private gists
gistx clone --private

# Clone all gists
gistx clone --all

# Limit number of repos, verbose output, force refresh of cached list
gistx clone --public --max_gists 10 -v -f

# Repair gistlist/fetch metadata
gistx fix
```

### Type Checking and Linting
```bash
uv run ruff check src/
uv run mypy src/
```

## Architecture

### Entry Points (`pyproject.toml`)

- `gistx` / `x`: `gistx.gistx:mainx` — main CLI dispatcher
- `check`, `check2`, `check3`: `gistx.gistx:check*` — diagnostic stubs (not yet implemented)

### CLI Flow

`mainx()` → `Clix` (subcommand router) → `Gistx.setup()`, `Gistx.clone()`, or `Gistx.fix()`

**`Clix`** (`clix.py`) builds argparse subcommands: `setup`, `clone`, `check`, `fix`. Each subcommand dispatches to a method on `Gistx`.

### Core Components

**`Gistx`** (`gistx.py`) — top-level orchestrator
- Initializes `AppStore` (from `yklibpy`) to manage config/DB files and directories
- `setup` subcommand: runs `CommandSetup` which detects `gh` user and writes config
- `clone` subcommand: validates flags, registers YAML constructors once (class-level flag), then delegates to `CommandClone`
- `fix` subcommand: removes empty directories under `gistlist/` and reconciles `fetch.yaml` with existing list snapshots

**`AppConfigx`** (`appconfigx.py`) — extends `yklibpy.AppConfig`
- Declares two DB keys: `list` (YAML file of cached `GistInfo` objects) and `repo` (directory for cloned gists)
- Config key `user` stores the GitHub username

**`CommandSetup`** (`command_setup.py`) — writes initial config and empty DB files via `AppStore`

**`CommandClone`** (`command_clone.py`) — main clone logic
- Fetches gists from `https://api.github.com/users/{user}/gists` with pagination (100/page)
- Writes list snapshots under `{workspace}/gistlist/{list_count}/list.yaml`
- Clones public/private gists under `{workspace}/gistlist/{list_count}/gistrepo/{clone_count}/{public|private}/{dir_name}`
- Updates `{workspace}/fetch.yaml` with `{list_count}: [timestamp, clone_target_count]`

**`CommandFix`** (`command_fix.py`) — maintenance logic
- Removes empty directories under `{workspace}/gistlist/` without deleting the top directory itself
- Reconciles `{workspace}/fetch.yaml` so its numeric keys match the existing `gistlist/{list_count}` directories

**`GistInfo`** (`gistinfo.py`) — data model for a single gist
- Key derived fields: `title` (from `[title]` in description), `name_without_japanese` (CJK stripped), `name_alnum` (alphanumeric only, used as directory name)

### Naming Convention for Clone Directories

1. Description with `[title]` pattern → extracts title
2. CJK characters stripped → `name_without_japanese`
3. Non-alphanumeric stripped → `name_alnum` (used as `dir_name`)
4. Duplicate `name_alnum`: appended with `-0`, `-1`, `-2`, ...
5. Empty `name_alnum`: stored under `_none/0`, `_none/1`, ...
6. Gists with no description or all-Japanese descriptions are skipped

### Key Behaviors

- YAML cache (`AppConfigx.BASE_NAME_LIST`) prevents redundant API calls; bypassed with `--force`
- Already-cloned directories are skipped (no pull/update)
- YAML constructors for `GistInfo` deserialization are registered once via a class-level flag `Gistx._constructors_registered`
- `clone_my_all_gists` currently has an `exit()` call mid-function (line ~137 of `command_clone.py`) — the code below it is unreachable; this is in-progress work

### Dependencies

- **requests**: GitHub API calls
- **yklibpy** (`../yklibpy`, editable): `AppStore`, `AppConfig`, `Loggerx`, `Timex`, `FetchCount`, `Command`, `UtilYaml`, `Cli`, `Tomlop`
- **mypy** + **ty** (dev): static type checking; `yklibpy.*` imports are set to `follow_imports = "skip"`

### 用語の定義
- ユーザ
gh auth login　で認証されたGitHubのアカウント
指定されGitHubアカウントのアカウント名と同一のユーザ名を持つ

- コンフィグディレクトリ
ディレクトリ名は"gistx"
この下にYAML形式のコンフィグファイル(config.yaml)が存在する

以下の位置に存在する
　AppData\Roaming\gistx

- コンフィグファイル
アプリ全体に対するYAML形式のコンフィグファイル
ファイル名は"config.yaml"

ファイルのフォーマットは以下の通り
gists: gists
url_api: https://api.github.com
user: <ユーザ名>

以下の位置に存在する
　AppData\Roaming\gistx\config.yaml

- ユーザディレクトリ
ディレクトリ名はユーザ名
以下の位置に存在する
　AppData\Local\gistx\ユーザ名

この下にfetchファイル、gistlistトップディレクトリが存在する
gistlistトップディレクトリは1個のみ存在する。
以下の位置に存在する
　AppData\Local\gistx\ユーザ名\fetch.yaml
　AppData\Local\gistx\ユーザ名\gistlist

- fetchファイル
ファイル名は"fetch.yaml"
gh gist list を実行した回数とcloneしたgistの個数を記録するYAML形式ファイル
gh gist list の実行が成功した後に更新される。
1回のgh gist listですべてのgistの一覧を取得できるように、十分大きな最大個数を指定して実行する。

フォーマットは、以下の通り
　回数: 
　- 実行時のタイムスタンプ
  - clonesしたgistの個数

- gistlistトップディレクトリ
ディレクトリ名は"gistlist"
この下にgistlistディレクトリが存在する。
gistlistトップディレクトリは複数個存在してもよい。


- gistlistディレクトリ
ディレクトリ名はgh gist listを実行した回数
gh repo listの出力を格納するlist.yamlとgistrepoトップディレクトリをもつ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>

- gistrepoトップディレクトリ
ディレクトリ名は"gistrepo"
gh repo cloneの出力を格納するdb.yamlをもつ。
またgitrepoディレクトリも持つ。
gitrepoディレクトリは複数個存在する場合もある。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo

- gistrepoディレクトリ
ディレクトリ名はサブコマンドcloneを実行して、ghコマンドを用いて、指定個数分のgistのリポジトリをcloneしようとした回数

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>

- publicトップディレクトリ
ディレクトリ名は"public"
publicなgistのclone先ディレクトリを持つ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\public

- 個別publicなgistディレクトリ
ディレクトリ名はgistの名称
gistの名称は、gh gist listで取得する。
publicなgistのclone先ディレクトリ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\publc\<gistの名称>

- privateトップディレクトリ
ディレクトリ名は"private"
privateなgistのclone先ディレクトリを持つ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\private

- 個別privateなgistディレクトリ
ディレクトリ名はgistの名称
gistの名称は、gh gist listで取得する。
privatecなgistのclone先ディレクトリ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\private\<gistの名称>

以上で規定したディレクトリ、ファイルをのみを作成、利用してください。
