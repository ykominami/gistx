# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gistx` is a Python CLI tool that clones all public/private GitHub Gists from a configured user to a local directory. It uses the `gh` CLI to list and clone gists, records progress in YAML files, and handles naming conflicts.

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

- `gistx`: `gistx.gistx:mainx` — main CLI dispatcher

### CLI Flow

`mainx()` → `Clix` (subcommand router) → `Gistx.setup()`, `Gistx.clone()`, `Gistx.check()`, or `Gistx.fix()`

**`Clix`** (`clix.py`) builds argparse subcommands: `setup`, `clone`, `check`, `fix`. Each subcommand dispatches to a method on `Gistx`.

### Core Components

**`Gistx`** (`gistx.py`) — top-level orchestrator
- `init_appstore()`: initializes `AppStore` (from `yklibpy`) to manage config/DB files and directories
- `_load_config_with_legacy_fallback()`: loads config, falling back to `.yml` if `.yaml` is empty (legacy migration)
- `setup`: runs `CommandSetup` which detects `gh` user and writes config
- `clone`: validates flags (exactly one of `--public`/`--private`/`--all`), delegates to `CommandClone`
- `fix`: delegates to `CommandFix`
- `check`: raises `NotImplementedError` (not yet implemented)

**`AppConfigx`** (`appconfigx.py`) — extends `yklibpy.AppConfig`
- Constants: `BASE_NAME_LIST` (`list`), `BASE_NAME_GISTLIST_TOP` (`gistlist`), `BASE_NAME_REPO` (`repo`)
- Config keys: `KEY_USER` (`user`), `KEY_URL_API`, `KEY_GISTS`

**`CommandSetup`** (`command_setup.py`) — writes initial config and empty DB files via `AppStore`

**`CommandClone`** (`command_clone.py`) — main clone logic
- Runs `gh gist list --limit 1000` to get gist list, parses tab/whitespace-delimited output
- Writes list snapshots to `{workspace}/gistlist/{list_count}/list.yaml`
- Clones gists using `gh gist clone {gist_id} {target_dir}` under `{workspace}/gistlist/{list_count}/gistrepo/{clone_count}/{public|private}/{dir_name}`
- Writes `{workspace}/fetch.yaml` with `{list_count}: [timestamp, clone_target_count]` when a new list is fetched
- Writes `{workspace}/gistlist/{list_count}/gistrepo/progress.yaml` with per-run stats (success/failure counts)

**`CommandFix`** (`command_fix.py`) — maintenance logic
- Removes empty directories under `{workspace}/gistlist/` without deleting the top directory itself
- Reconciles `{workspace}/fetch.yaml` so its numeric keys match the existing `gistlist/{list_count}` directories

**`GistInfo`** (`gistinfo.py`) — data model for a single gist
- Fields: `gist_id`, `name`, `public` (bool), `dir_name` (set via `add_dir_name()` after clone)

### Key Behaviors

- `fetch.yaml` cache prevents redundant `gh gist list` calls; bypassed with `--force`
- Already-cloned directories are counted as failures (no pull/update)
- Duplicate directory names get `-1`, `-2`, ... suffix via `_make_unique_dir_name()`
- `gh gist list` output parsing handles variable whitespace; visibility detected by `public`/`secret` token
- Numeric subdirectory counters (list_count, clone_count) start at 1 and increment from the current max

### Dependencies

- **yklibpy** (`../yklibpy`, editable): `AppStore`, `AppConfig`, `Loggerx`, `Timex`, `Command`, `Util`, `Cli`, `Storex`
- **mypy** + **ruff** (dev): static type checking and linting; `yklibpy.*` imports are set to `follow_imports = "skip"`

### 用語の定義

- **ユーザ**: `gh auth login` で認証されたGitHubアカウント

- **コンフィグディレクトリ**: `AppData\Roaming\gistx\`
  - コンフィグファイル: `config.yaml` (フォーマット: `gists`, `url_api`, `user` キー)

- **ユーザディレクトリ**: `AppData\Local\gistx\<ユーザ名>\`
  - fetchファイル: `fetch.yaml` (フォーマット: `<回数>: [タイムスタンプ, clone対象件数]`)
  - gistlistトップディレクトリ: `gistlist\`

- **gistlistディレクトリ**: `gistlist\<gh gist list実行回数>\`
  - `list.yaml`: 取得したgist一覧
  - `gistrepo\`: gistrepoトップディレクトリ
  - `gistrepo\progress.yaml`: clone実行結果の記録

- **gistrepoディレクトリ**: `gistrepo\<clone実行回数>\`
  - `public\<gist名>\`: publicなgistのclone先
  - `private\<gist名>\`: privateなgistのclone先

以上で規定したディレクトリ、ファイルのみを作成・利用してください。
