# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gistx` is a Python CLI tool that clones all public/private GitHub Gists from a configured user to a local directory. It uses the `gh` CLI to list and clone gists, records progress in YAML files, and handles naming conflicts.

## Commands

### Prerequisites

- Python 3.14+
- `gh` CLI authenticated (`gh auth login`)

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

### Running Tests
```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_command_clone_unit.py

# Run a single test by name
uv run pytest tests/test_command_clone_unit.py::test_parse_gh_gist_list_line_public_and_secret
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
- Constants: `BASE_NAME_LIST` (`list`), `BASE_NAME_GISTLIST_TOP` (`gistlist`), `BASE_NAME_WORKSPACES_TOP` (`workspaces`), `BASE_NAME_PROGRESS` (`progress`), `BASE_NAME_REPO` (`repo`)
- Config keys: `KEY_USER` (`user`), `KEY_URL_API`, `KEY_GISTS`; defaults: `DEFAULT_VALUE_URL_API` = `https://api.github.com`, `DEFAULT_VALUE_GISTS` = `gists`
- `file_type_dict` maps `FILE_TYPE_YAML` to `.yaml`; `file_synonym_dict` maps `.yml` → `.yaml` for legacy migration

**`CommandSetup`** (`command_setup.py`) — writes initial config and empty DB files via `AppStore`

**`CommandClone`** (`command_clone.py`) — main clone logic
- Module-level: `GIST_ID_PATTERN` (hex ≥7 chars), `TABLE_SPLIT_PATTERN` (tab or 2+ spaces), `WINDOWS_INVALID_DIR_CHARS_PATTERN`; `ConfigFileInfo` NamedTuple (`parent_path`, `assoc`)
- Runs `gh gist list --limit 1000` to get gist list, parses tab/whitespace-delimited output
- Writes list snapshots to `<ユーザディレクトリ>/workspaces/<ワークスペースID>/gists.yaml`
- Clones gists using `gh gist clone {gist_id} {target_dir}` under `<ユーザディレクトリ>/workspaces/<ワークスペースID>/gistrepo/<クローンID>/{public|private}/<gist_id>`
- Writes `<ユーザディレクトリ>/workspaces.yaml` with `<ワークスペースID>: [タイムスタンプ, clone対象件数]` when a new list is fetched
- Writes `<ユーザディレクトリ>/workspaces/<ワークスペースID>/gistrepo/progress.yaml` with per-run stats (success/failure counts)

**`CommandFix`** (`command_fix.py`) — maintenance logic
- **注意**: `gistlist/` と `fetch.yaml` はディレクトリ/ファイル定義に存在しないレガシーパス。現行の `workspaces/` アーキテクチャとは不整合。
- Operates on `<ユーザディレクトリ>/gistlist/` and `<ユーザディレクトリ>/fetch.yaml` (legacy paths)
- Removes empty directories under `gistlist/` without deleting the top directory itself
- Reconciles `fetch.yaml` so its numeric keys match the existing `gistlist/<数値>` directories
- Contains module-level helper functions (`remove_empty_directories`, `collect_existing_gistlist_counts`, `reconcile_fetch_entries`) — violates the class-method-only constraint

**`GistInfo`** (`gistinfo.py`) — data model for a single gist
- Fields: `gist_id`, `name`, `public` (bool), `dir_name` (set via `add_dir_name()` after clone)

### Key Behaviors

- `workspaces.yaml` cache prevents redundant `gh gist list` calls; bypassed with `--force`
- Already-cloned directories are counted as failures (no pull/update)
- `gh gist list` output parsing handles variable whitespace; visibility detected by `public`/`secret` token
- Numeric subdirectory counters (ワークスペースID, クローンID) start at 1 and increment from the current max

### Dependencies

- **yklibpy** (`../yklibpy`, editable): `AppStore`, `AppConfig`, `Loggerx`, `Timex`, `Command`, `Util`, `Cli`, `Storex`
- **mypy** + **ruff** (dev): static type checking and linting; `yklibpy.*` imports are set to `follow_imports = "skip"`

## ドキュメントディレクトリ・ファイル構成
### docs/spec 外部仕様書ディレクトリ

| ファイル | 対象クラス/モジュール | 概要 |
|----------|----------------------|------|
| [spec_appconfigx.md](docs/spec/spec_appconfigx.md) | `AppConfigx` | `yklibpy.AppConfig` を継承し、`gistx` 固有の設定名・DB 名・ディレクトリ名・既定値を定義するクラス |
| [spec_clix.md](docs/spec/spec_clix.md) | `Clix` | CLI サブコマンド定義と `argparse` オプション解析を担当するクラス |
| [spec_command_clone.md](docs/spec/spec_command_clone.md) | `CommandClone` | `gistx clone` の実装。gist 一覧取得・clone・YAML 記録を行うクラス |
| [spec_command_fix.md](docs/spec/spec_command_fix.md) | `CommandFix` | `gistx fix` の実装。空ディレクトリ削除と `fetch.yaml` 修復を行うクラス |
| [spec_command_setup.md](docs/spec/spec_command_setup.md) | `CommandSetup` | `gistx setup` の実装。設定ファイル書き出しと初期ディレクトリ作成を行うクラス |
| [spec_gistinfo.md](docs/spec/spec_gistinfo.md) | `GistInfo` | gist 1 件分の基本情報（ID・表示名・公開状態・clone 先ディレクトリ名）を保持するデータクラス |
| [spec_gistx.md](docs/spec/spec_gistx.md) | `Gistx` / `mainx` | CLI 最上位調停クラス。`AppStore` 初期化と各サブコマンドの委譲を行うクラス |

### docs/req 要求仕様書ディレクトリ


### 用語の定義

- **ユーザ**: `gh auth login` で認証されたGitHubアカウント
- **コンフィグディレクトリ**: 
  - Windows: `%APPDATA%/gistx/`
  - Unix 系: `~/.config/gistx/`
- **コンフィグファイル**: `config.yaml` 
  (キー: `gists`, `url_api`, `user`)

- **ユーザディレクトリ**:
  - Windows: `%LOCALAPPDATA%/gistx/<user>/`
  - Unix 系: `~/.local/share/gistx/<user>/`

- **ワークスペース作成記録ファイル**: `workspaces.yaml`
  - (フォーマット: `<ワークスペースID>: [タイムスタンプ, clone対象件数]`)
- **ワークスペーストップディレクトリ**: `workspaces`
- **個別ワークスペースディレクトリ**: <ワークスペースID>
  - ワークスペースID: ワークスペースを作成する回数であり、1から始まる整数
- **取得済gist一覧ファイル**: `gists.yaml`
  - フォーマット:
    - <gist id>:
      - gist_id: <gist_id>
      - name: <gist名>
      - public: true|false (publicなgist/privateなgist)	  
- **gistrepoトップディレクトリ**: `gistrepo`
- **clone実行結果記録ファイル**: `progress.yaml`
  - フォーマット:
    - <クローンID>: {timestamp, repo_kind, requested_count, success_count, failure_count, ワークスペースID}

- **個別クローンディレクトリ**: <クローンID>
 - クローンID: クローンした回数。1から始まる整数。
- **private gistトップディレクトリ**: `private`
- **個別private gistディレクトリ**; <gist_id>
- **public gistトップディレクトリ**: `public`
- **個別public gistディレクトリ**; <gist_id>

### ディレクトリ/ファイル定義
<コンフィグディレクトリ>
  <コンフィグファイル>

<ユーザディレクトリ>
  <ワークスペース作成記録ファイル>
  <ワークスペーストップディレクトリ>
    <個別ワークスペースディレクトリ>
	  <取得済gist一覧ファイル>
	  <gistrepoトップディレクトリ>
	    <clone実行結果記録ファイル>
		<個別クローンディレクトリ>
		  <private gistトップディレクトリ>
		    <個別private gistディレクトリ>
		  <public gistトップディレクトリ>
		    <個別public gistディレクトリ>

以上で規定したディレクトリ、ファイルのみを作成・利用してください。

ArchitectureのEntory Points以外は、機能をクラスのインスタンスメソッド、クラスメソッドとして実装し、独立した関数としては実装しないでください。
