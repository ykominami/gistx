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
gistx clone --public --max_repos 10 -v -f
```

### Type Checking and Linting
```bash
uv run ruff check src/
uv run mypy src/
```

## Architecture

### Entry Points (`pyproject.toml`)

- `gistx` / `x`: `gistx.gistx:mainx` — main CLI dispatcher
- `tomlx`: `gistx.tomlx:main` — TOML utility
- `check`, `check2`, `check3`: `gistx.gistx:check*` — diagnostic stubs (not yet implemented)

### CLI Flow

`mainx()` → `Clix` (subcommand router) → `Gistx.setup()` or `Gistx.clone()`

**`Clix`** (`clix.py`) builds argparse subcommands: `setup`, `clone`, `check`. Each subcommand dispatches to a method on `Gistx`.

### Core Components

**`Gistx`** (`gistx.py`) — top-level orchestrator
- Initializes `AppStore` (from `yklibpy`) to manage config/DB files and directories
- `setup` subcommand: runs `CommandSetup` which detects `gh` user and writes config
- `clone` subcommand: validates flags, registers YAML constructors once (class-level flag), then delegates to `CommandClone`

**`AppConfigx`** (`appconfigx.py`) — extends `yklibpy.AppConfig`
- Declares two DB keys: `list` (YAML file of cached `GistInfo` objects) and `repo` (directory for cloned gists)
- Config key `user` stores the GitHub username

**`CommandSetup`** (`command_setup.py`) — writes initial config and empty DB files via `AppStore`

**`CommandClone`** (`command_clone.py`) — main clone logic
- Fetches gists from `https://api.github.com/users/{user}/gists` with pagination (100/page)
- Caches result as YAML via `AppStore`; uses cache on subsequent runs unless `--force`
- Separates public/private gists; clones into a versioned directory tree:
  `{repo_dir}/{top_dir}/{fetch_count}/{public|private}/{dir_name}`
- Uses `FetchCount` (from `yklibpy`) to manage versioned fetch directories

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
