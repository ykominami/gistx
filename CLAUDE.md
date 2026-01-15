# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gistx` is a Python CLI tool that clones all public GitHub Gists from a specified user to a local directory. It fetches gist metadata via the GitHub API, processes descriptions to extract titles, handles naming conflicts, and clones repositories using git.

## Commands

### Installation and Setup
```bash
# Install dependencies (uses uv package manager)
uv sync

# Install in development mode
uv pip install -e .
```

### Running the Tool
```bash
# Main command - clones all gists for configured user
gistx
# or
x

# Check for gists with duplicate name_alnum values
check

# Check for gists with missing clone_url
check2

# Check for gists with short directory names (< 2 chars)
check3
```

### Linting
```bash
# Run ruff linter
uv run ruff check src/
```

## Architecture

### Entry Points

The package defines multiple entry points in `pyproject.toml`:
- `gistx` and `x`: Main clone operation (src/gistx/x.py:mainx)
- `check`, `check2`, `check3`: Diagnostic utilities (src/gistx/x.py)

Configuration (username and dest_dir) is currently hardcoded in `x.py`.

### Core Components

**Gistx class** (`src/gistx/gistx.py`)
- Main orchestrator for fetching and cloning gists
- Handles GitHub API pagination (100 gists per page)
- Manages YAML caching of gist metadata in `gist_info_3.yaml`
- Registers custom YAML constructors for GistInfo serialization

**GistInfo class** (`src/gistx/gistinfo.py`)
- Data model for gist metadata
- Key fields:
  - `gist_id`: GitHub gist ID
  - `name`: Original description from GitHub
  - `title`: Extracted from `[title]` pattern in description
  - `name_alnum`: Alphanumeric-only version (used for directory naming)
  - `clone_url`: Git clone URL
  - `dir_name`: Final local directory name

**clone_my_public_gists** (`src/gistx/main.py`)
- Public API function
- Workflow:
  1. Fetch or load gist metadata
  2. Classify gists by name_alnum
  3. Handle naming conflicts by appending `-{index}` suffix
  4. Clone each gist to appropriate directory

### Data Flow

1. **Fetch**: GitHub API → raw gist JSON (with pagination)
2. **Transform**: Extract/sanitize names → GistInfo objects → YAML cache
3. **Classify**: Group by name_alnum, detect duplicates
4. **Clone**: Execute `git clone` for each gist to `dest_dir/dir_name`

### Naming Convention

Directory names are derived from gist descriptions:
- Descriptions with `[title]` extract the title
- Japanese characters are removed to create `name_without_japanese`
- Only alphanumeric chars are kept to create `name_alnum`
- Gists with duplicate `name_alnum` get `-0`, `-1`, `-2` suffixes
- Gists with empty `name_alnum` go to `_none/0`, `_none/1`, etc.

### Dependencies

- **requests**: GitHub API communication
- **yklibpy**: Local utility library at `../yklibpy` (YAML handling, file utilities)
- **pathlib**: Path manipulation
- **subprocess**: Git clone operations

### Important Notes

- The tool skips gists without descriptions or where Japanese removal results in empty strings
- YAML cache prevents redundant API calls on subsequent runs
- Already-cloned directories are skipped (no updates/pulls)
- Custom YAML constructors must be registered once for GistInfo deserialization
