# 型ヒント追加 外部仕様書

`gistx` の `src/gistx/` 配下に存在する、すべてのクラスメソッド・インスタンスメソッド・独立関数について、引数の型と返値の型を明示する。

## 基本方針

- Python 3.14 の構文を用いる。
- `dict[str, X]`、`list[X]`、`tuple[...]`、`X | None` を用いる。
- `yklibpy` や YAML 読み込み境界では動的型を受け入れてもよいが、`gistx` 内部では可能な限り具体型へ絞り込む。
- 型を隠すための広い `# type: ignore` は追加しない。

## 対象シグネチャ

### `src/gistx/gistinfo.py`

- `GistInfo.__init__(self, gist_id: str, name: str, public: bool = True, dir_name: str = "") -> None`
- `GistInfo.add_dir_name(self, dir_name: str) -> None`

補足:

- `GistInfo` のインスタンス属性 `gist_id`、`name`、`public`、`dir_name` はそれぞれ `str`、`str`、`bool`、`str` とする。

### `src/gistx/tomlx.py`

- `Tomlx.__init__(self, toml_flle_path: Path, config_file_path: Path) -> None`
- `Tomlx.run(self) -> None`
- `main() -> None`

### `src/gistx/clix.py`

- `Clix.__init__(self, description: str, command_dict: dict[str, Callable[[argparse.Namespace], None]]) -> None`
- `Clix.parse_args(self) -> argparse.Namespace`

### `src/gistx/command_setup.py`

- `CommandSetup.__init__(self, appstore: AppStore) -> None`
- `CommandSetup.run(self) -> None`
- `CommandSetup._prepare_user_workspace(self, user: str) -> None`
- `CommandSetup._get_workspace_path(self, user: str) -> Path`

### `src/gistx/command_fix.py`

- `remove_empty_directories(root: Path) -> int`
- `collect_existing_gistlist_counts(gistlist_top_dir: Path) -> list[int]`
- `reconcile_fetch_entries(fetch_assoc: dict[str, object], existing_counts: list[int]) -> dict[str, object]`
- `CommandFix.__init__(self, appstore: AppStore) -> None`
- `CommandFix.run(self, args: argparse.Namespace) -> None`
- `CommandFix._remove_empty_dirs(self, path: Path) -> int`
- `CommandFix._collect_existing_counts(self, gistlist_top_dir: Path) -> list[int]`
- `CommandFix._fix_fetch_yaml(self, fetch_path: Path, existing_counts: list[int]) -> None`
- `CommandFix._load_yaml_file(self, path: Path) -> dict[str, object]`
- `CommandFix._save_yaml_file(self, path: Path, data: Mapping[str, object]) -> None`
- `CommandFix._get_workspace_path(self) -> Path`

### `src/gistx/command_clone.py`

- `ConfigFileInfo` の属性:
- `parent_path: Path`
- `assoc: dict[str, dict[str, Any]]`
- `CommandClone.__init__(self, appstore: AppStore) -> None`
- `CommandClone._prepare_clone(self, force: bool) -> tuple[dict[str, GistInfo], Path, int, Path, str, int]`
- `CommandClone.run(self, args: argparse.Namespace, repo_kind: str) -> None`
- `CommandClone._parse_gh_gist_list_output(self, stdout_str: str) -> dict[str, GistInfo]`
- `CommandClone._parse_gh_gist_list_line(self, line: str) -> GistInfo | None`
- `CommandClone._sanitize_gist_name(self, name: str) -> str`
- `CommandClone._make_unique_dir_name(self, base_name: str, used_names: set[str]) -> str`
- `CommandClone._load_yaml_file(self, path: Path) -> dict[str, object]`
- `CommandClone._save_yaml_file(self, path: Path, data: Mapping[str, object]) -> None`
- `CommandClone._serialize_gist_info_assoc(self, gist_info_assoc: dict[str, GistInfo]) -> dict[str, dict[str, object]]`
- `CommandClone._deserialize_gist_info_assoc(self, data: dict[str, object]) -> dict[str, GistInfo]`
- `CommandClone._ensure_user_workspace(self) -> Path`
- `CommandClone._get_workspace_path(self) -> Path`
- `CommandClone._should_refresh_list(self, fetch_path: Path, gistlist_top_dir: Path, force: bool) -> bool`
- `CommandClone._execute_gh_gist_list(self, limit: int) -> str`
- `CommandClone._fetch_list_snapshot(self, gistlist_top_dir: Path) -> tuple[int, dict[str, GistInfo]]`
- `CommandClone._decode_command_output(self, data: bytes | None, stream_name: str, command_name: str, hypothesis_id: str) -> str`
- `CommandClone._create_list_snapshot(self, gistlist_top_dir: Path, stdout_str: str) -> tuple[int, dict[str, GistInfo]]`
- `CommandClone._load_latest_list_snapshot(self, gistlist_top_dir: Path) -> tuple[int, dict[str, GistInfo]]`
- `CommandClone._get_latest_list_path(self, gistlist_top_dir: Path) -> Path | None`
- `CommandClone._filter_gists(self, gist_info_assoc: dict[str, GistInfo], repo_kind: str) -> list[GistInfo]`
- `CommandClone._limit_gists(self, gist_infos: list[GistInfo], max_gists: int | None) -> list[GistInfo]`
- `CommandClone._get_next_clone_count(self, gistrepo_top_dir: Path) -> int`
- `CommandClone._get_next_numeric_dir_value(self, top_dir: Path) -> int`
- `CommandClone._get_numeric_subdirs(self, top_dir: Path) -> list[int]`
- `CommandClone._clone_gists(self, gist_infos: list[GistInfo], clone_dir: Path) -> tuple[int, int]`
- `CommandClone._write_fetch_yaml(self, fetch_path: Path, list_count: int, timestamp: str, clone_target_count: int) -> None`
- `CommandClone._write_progress_yaml(self, progress_path: Path, clone_count: int, summary: dict[str, object]) -> None`

### `src/gistx/gistx.py`

- `Gistx.init_appstore(cls, *, prepare_db_file: bool = False, prepare_db_directory: bool = False) -> AppStore`
- `Gistx._load_config_with_legacy_fallback(cls, appstore: AppStore) -> None`
- `Gistx.setup(cls, args: argparse.Namespace) -> None`
- `Gistx.clone(cls, args: argparse.Namespace) -> None`
- `Gistx.check(cls, args: argparse.Namespace) -> None`
- `Gistx.fix(cls, args: argparse.Namespace) -> None`
- `mainx() -> None`
