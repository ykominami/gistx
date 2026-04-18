# 外部仕様書 — `CommandClone`

**ファイル**: `src/gistx/command_clone.py`

## 概要

`gistx clone` サブコマンドの実装クラス。`gh gist list` で gist 一覧を取得し、指定した公開範囲の gist を `gh gist clone` で clone する。取得した一覧・進捗情報を YAML ファイルに記録する。

---

## 継承

```
yklibpy.command.command.Command
    └── CommandClone
```

---

## モジュールレベル定数

| 定数名 | 値 | 説明 |
|---|---|---|
| `GIST_ID_PATTERN` | `re.compile(r"^[0-9a-f]{7,}$", re.IGNORECASE)` | gist ID の妥当性チェック用正規表現 |
| `TABLE_SPLIT_PATTERN` | `re.compile(r"\t+\|\s{2,}")` | `gh gist list` 出力の列分割用正規表現 |
| `WINDOWS_INVALID_DIR_CHARS_PATTERN` | `re.compile(r'[<>:"/\\|?*\x00-\x1F]')` | Windows 禁則文字の置換用正規表現 |

---

## クラス定数

| 定数名 | 値 | 説明 |
|---|---|---|
| `REPO_KIND_PUBLIC` | `"public"` | public gist を対象にする種別文字列 |
| `REPO_KIND_PRIVATE` | `"private"` | secret gist を対象にする種別文字列 |
| `REPO_KIND_ALL` | `"all"` | 全 gist を対象にする種別文字列 |
| `GH_GIST_LIST_LIMIT` | `1000` | `gh gist list --limit` に渡す最大件数 |
| `_RECORD_TIMESTAMP_FORMAT` | `"%Y-%m-%d %H:%M:%S"` | YAML 記録用タイムスタンプのフォーマット |

---

## 補助型

### `ConfigFileInfo` *(NamedTuple)*

```python
class ConfigFileInfo(NamedTuple):
    parent_path: Path
    assoc: dict[str, dict[str, Any]]
```

設定ファイルの親ディレクトリと内容をまとめて保持する。

---

## コンストラクタ

```python
CommandClone(appstore: AppStore) -> None
```

### パラメータ

| 名前 | 型 | 説明 |
|---|---|---|
| `appstore` | `AppStore` | 設定済みの `yklibpy.AppStore` インスタンス |

### 例外

| 例外 | 条件 |
|---|---|
| `ValueError` | `config.yaml` に `user` キーが設定されていない場合 |

---

## パブリックメソッド

### `run`

```python
def run(self, args: argparse.Namespace, repo_kind: str) -> None
```

指定された公開範囲の gist を clone し、進捗情報を記録する。

#### パラメータ

| 名前 | 型 | 説明 |
|---|---|---|
| `args` | `argparse.Namespace` | `clone` サブコマンドの解析済み引数 |
| `repo_kind` | `str` | `"public"` / `"private"` / `"all"` のいずれか |

#### 処理手順

1. `_resolve_gist_list(args.force)` でワークスペースを確保し、gist 一覧を取得または読み込む。
2. `_filter_gists()` で `repo_kind` に応じて対象 gist を絞り込む。
3. `_limit_gists()` で `args.max_gists` 件に制限する。
4. `gistrepo/<クローンID>/` ディレクトリを作成する。
5. `_clone_gists()` で対象 gist を clone し、成功・失敗件数を取得する。
6. `_write_progress_yaml()` で `progress.yaml` に実行結果を記録する。
7. 新規取得した場合のみ `_write_workspaces_yaml()` で `workspaces.yaml` を更新する。

#### 記録内容（`progress.yaml` エントリ）

| キー | 値 |
|---|---|
| `timestamp` | JST タイムスタンプ（`YYYY-MM-DD HH:MM:SS`） |
| `repo_kind` | `"public"` / `"private"` / `"all"` |
| `requested_count` | 対象 gist 件数 |
| `success_count` | clone 成功件数 |
| `failure_count` | clone 失敗件数 |
| `workspace_id` | ワークスペースID（整数） |

**戻り値**: なし  
**例外**: `RuntimeError`（`gh gist list` / `gh gist clone` の失敗）、`ValueError`（不正な `repo_kind`）

---

## プライベートメソッド

### `_record_timestamp_jst` *(staticmethod)*

```python
@staticmethod
def _record_timestamp_jst() -> str
```

現在時刻の JST タイムスタンプを `YYYY-MM-DD HH:MM:SS` 形式で返す。

---

### `_resolve_gist_list`

```python
def _resolve_gist_list(self, force: bool) -> tuple[
    dict[str, GistInfo], Path, Path, str, int, bool
]
```

ワークスペースを確保し、gist 一覧を取得または最新スナップショットを読み込む。

**戻り値**: `(gist_info_assoc, workspaces_top_dir, workspace_path, timestamp, list_count, fetched_new_list)`

| 要素 | 型 | 説明 |
|---|---|---|
| `gist_info_assoc` | `dict[str, GistInfo]` | gist ID → GistInfo の辞書 |
| `workspaces_top_dir` | `Path` | `<ユーザディレクトリ>/workspaces/` |
| `workspace_path` | `Path` | `<ユーザディレクトリ>/` |
| `timestamp` | `str` | 実行時刻（JST） |
| `list_count` | `int` | ワークスペースID |
| `fetched_new_list` | `bool` | 新規取得したか否か |

**例外**: `FileNotFoundError`（キャッシュ消失かつ再取得失敗時）

---

### `_parse_gh_gist_list_output`

```python
def _parse_gh_gist_list_output(self, stdout_str: str) -> dict[str, GistInfo]
```

`gh gist list` の標準出力全体を `GistInfo` の辞書へ変換する。空行・ヘッダ行はスキップする。

---

### `_parse_gh_gist_list_line`

```python
def _parse_gh_gist_list_line(self, line: str) -> GistInfo | None
```

`gh gist list` の 1 行を解析して `GistInfo` を返す。ヘッダ行・空行は `None` を返す。

#### 解析ルール

| 列 | 内容 |
|---|---|
| 0 | gist ID（`GIST_ID_PATTERN` で検証） |
| 1 〜 visibility の直前 | gist 名（スペース結合） |
| `public` または `secret` トークン | 公開状態 |

**例外**: `ValueError`（gist ID 抽出不可、公開状態不明、gist 名抽出不可の場合）

---

### `_should_refresh_list`

```python
def _should_refresh_list(
    self, workspaces_yaml_path: Path, workspaces_top_dir: Path, force: bool
) -> bool
```

以下のいずれかを満たす場合に `True` を返す。

- `force` が `True`
- `workspaces.yaml` が空または存在しない
- 最新の `gists.yaml` が存在しない

---

### `_execute_gh_gist_list`

```python
def _execute_gh_gist_list(self, limit: int) -> str
```

`gh gist list --limit <limit>` を実行し、標準出力を文字列で返す。

**例外**:
- `SystemExit`（認証エラーまたは権限不足）
- `RuntimeError`（その他の失敗）

---

### `_decode_command_output`

```python
def _decode_command_output(
    self,
    data: bytes | None,
    stream_name: str,
    command_name: str,
    hypothesis_id: str,
) -> str
```

コマンド出力の `bytes` を UTF-8 → ロケール既定 → UTF-8（エラー置換）の順にデコードする。

---

### `_fetch_list_snapshot`

```python
def _fetch_list_snapshot(self, workspaces_top_dir: Path) -> tuple[int, dict[str, GistInfo]]
```

`gh gist list` を実行し、新しいワークスペースディレクトリと `gists.yaml` を作成する。

**戻り値**: `(list_count, gist_info_assoc)`

---

### `_create_list_snapshot`

```python
def _create_list_snapshot(
    self, workspaces_top_dir: Path, stdout_str: str
) -> tuple[int, dict[str, GistInfo]]
```

取得した gist 一覧から `workspaces/<ワークスペースID>/gists.yaml` を作成する。

#### 作成するパス

| パス | 説明 |
|---|---|
| `workspaces/<ワークスペースID>/` | 新規ワークスペースディレクトリ |
| `workspaces/<ワークスペースID>/gists.yaml` | gist 一覧スナップショット |
| `workspaces/<ワークスペースID>/gistrepo/` | clone 用ディレクトリ |

---

### `_load_latest_list_snapshot`

```python
def _load_latest_list_snapshot(
    self, workspaces_top_dir: Path
) -> tuple[int, dict[str, GistInfo]]
```

最大数値のワークスペースディレクトリにある `gists.yaml` を読み込む。

**例外**: `FileNotFoundError`（`gists.yaml` が存在しない場合）

---

### `_filter_gists`

```python
def _filter_gists(
    self, gist_info_assoc: dict[str, GistInfo], repo_kind: str
) -> list[GistInfo]
```

`repo_kind` に応じて gist 一覧を絞り込む。

| `repo_kind` | 対象 |
|---|---|
| `"public"` | `gist_info.public == True` のみ |
| `"private"` | `gist_info.public == False` のみ |
| `"all"` | すべて |

**例外**: `ValueError`（想定外の `repo_kind`）

---

### `_limit_gists`

```python
def _limit_gists(
    self, gist_infos: list[GistInfo], max_gists: int | None
) -> list[GistInfo]
```

`max_gists` が指定されていれば先頭から `max_gists` 件に絞る。`None` の場合はそのまま返す。

---

### `_clone_gists`

```python
def _clone_gists(
    self, gist_infos: list[GistInfo], clone_dir: Path
) -> tuple[int, int]
```

各 gist を `gh gist clone <gist_id> <target_dir>` で clone する。

#### clone 先パス

```
<clone_dir>/<public|private>/<gist_id>/
```

#### 失敗カウントの条件

- clone 先ディレクトリが既に存在する（pull/update は行わない）
- `gh gist clone` のリターンコードが 0 以外

**戻り値**: `(success_count, failure_count)`

---

### `_write_workspaces_yaml`

```python
def _write_workspaces_yaml(
    self,
    workspaces_yaml_path: Path,
    list_count: int,
    timestamp: str,
    clone_target_count: int,
) -> None
```

`workspaces.yaml` に新しいエントリを追記する。

#### エントリ形式

```yaml
"<ワークスペースID>": ["YYYY-MM-DD HH:MM:SS", <件数>]
```

---

### `_write_progress_yaml`

```python
def _write_progress_yaml(
    self,
    progress_path: Path,
    clone_count: int,
    summary: dict[str, object],
) -> None
```

`progress.yaml` にクローンID をキーとして実行結果を追記する。

---

### `_get_next_numeric_dir_value`

```python
def _get_next_numeric_dir_value(self, top_dir: Path) -> int
```

`top_dir` 直下の数値名ディレクトリの最大値 + 1 を返す。ディレクトリが存在しない場合は `1` を返す。

---

### `_build_clone_dir_name`

```python
def _build_clone_dir_name(self, gist_id: str) -> str
```

gist ID から Windows 禁則文字を `_` に置換してディレクトリ名を生成する。

---

## ディレクトリ/ファイル構造（`run()` 実行後）

```
<ユーザディレクトリ>/
  workspaces.yaml                          # ワークスペース作成記録
  workspaces/
    <ワークスペースID>/
      gists.yaml                           # gist 一覧スナップショット
      gistrepo/
        progress.yaml                      # clone 実行結果記録
        <クローンID>/
          public/
            <gist_id>/                     # public gist の clone 先
          private/
            <gist_id>/                     # secret gist の clone 先
```

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `Gistx.clone()` | `AppStore` を渡してインスタンス化し `run()` を呼び出す |
