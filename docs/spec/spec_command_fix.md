# 外部仕様書 — `CommandFix`

**ファイル**: `src/gistx/command_fix.py`

## 概要

`gistx fix` サブコマンドの実装クラス。`<ユーザディレクトリ>/gistlist/` 配下の空ディレクトリを削除し、`fetch.yaml` のエントリを実在するディレクトリに合わせて修復する。

---

## 継承

```
yklibpy.command.command.Command
    └── CommandFix
```

---

## モジュールレベル定数

| 定数名 | 値 | 説明 |
|---|---|---|
| `GISTLIST_DIR_NAME` | `"gistlist"` | gistlist トップディレクトリ名 |
| `FETCH_YAML_NAME` | `"fetch.yaml"` | 修復対象の YAML ファイル名 |

---

## モジュールレベル関数

> これらは `CommandFix` クラスのプライベートメソッドから委譲呼び出しされる補助関数。

### `remove_empty_directories`

```python
def remove_empty_directories(root: Path) -> int
```

`root` 配下の空ディレクトリを再帰的に削除する（`root` 自体は削除しない）。

| パラメータ | 型 | 説明 |
|---|---|---|
| `root` | `Path` | 探索起点のディレクトリ |

**戻り値**: 削除したディレクトリの件数  
**例外**: なし

---

### `collect_existing_gistlist_counts`

```python
def collect_existing_gistlist_counts(gistlist_top_dir: Path) -> list[int]
```

`gistlist/` 直下の数値名ディレクトリを昇順の整数リストとして返す。

| パラメータ | 型 | 説明 |
|---|---|---|
| `gistlist_top_dir` | `Path` | `gistlist/` トップディレクトリのパス |

**戻り値**: 昇順にソートされた数値リスト  
**例外**: なし

---

### `reconcile_fetch_entries`

```python
def reconcile_fetch_entries(
    fetch_assoc: dict[str, object],
    existing_counts: list[int],
) -> dict[str, object]
```

実在する gistlist カウントに合わせて `fetch.yaml` の内容を再構成する。

- `fetch_assoc` に存在しないカウントは `[<現在時刻>, 0]` を補う
- `fetch_assoc` に存在しても対応ディレクトリがないキーは削除する

| パラメータ | 型 | 説明 |
|---|---|---|
| `fetch_assoc` | `dict[str, object]` | 既存の `fetch.yaml` 内容 |
| `existing_counts` | `list[int]` | 実在するディレクトリの数値一覧 |

**戻り値**: 修復後の辞書  
**例外**: なし

---

## コンストラクタ

```python
CommandFix(appstore: AppStore) -> None
```

### パラメータ

| 名前 | 型 | 説明 |
|---|---|---|
| `appstore` | `AppStore` | 設定読み込みに使用する `yklibpy.AppStore` インスタンス |

### 例外

| 例外 | 条件 |
|---|---|
| `ValueError` | `config.yaml` に `user` キーが設定されていない場合 |

---

## パブリックメソッド

### `run`

```python
def run(self, args: argparse.Namespace) -> None
```

ワークスペースを検査し、空ディレクトリ削除と `fetch.yaml` 修復を実行する。

#### 処理手順

1. `_get_workspace_path()` でユーザ別 workspace パスを取得する。
2. workspace が存在しない場合は `FileNotFoundError` を送出する。
3. `<ユーザディレクトリ>/gistlist/` が存在しない場合は `FileNotFoundError` を送出する。
4. `_remove_empty_dirs(gistlist_top_dir)` で空ディレクトリを削除する。
5. `_collect_existing_counts(gistlist_top_dir)` で実在する数値ディレクトリを収集する。
6. `_reconcile_fetch_yaml(fetch_path, existing_counts)` で `fetch.yaml` を修復する。

**戻り値**: なし  
**例外**: `FileNotFoundError`（workspace または `gistlist/` が存在しない場合）

---

## プライベートメソッド

### `_remove_empty_dirs`

```python
def _remove_empty_dirs(self, path: Path) -> int
```

`remove_empty_directories(path)` に委譲する。

---

### `_collect_existing_counts`

```python
def _collect_existing_counts(self, gistlist_top_dir: Path) -> list[int]
```

`collect_existing_gistlist_counts(gistlist_top_dir)` に委譲する。

---

### `_reconcile_fetch_yaml`

```python
def _reconcile_fetch_yaml(self, fetch_path: Path, existing_counts: list[int]) -> None
```

既存の `fetch.yaml` を読み込み、`reconcile_fetch_entries()` で再構成して上書き保存する。

---

### `_load_yaml_file`

```python
def _load_yaml_file(self, path: Path) -> dict[str, object]
```

YAML ファイルを読み込み mapping として返す。ファイルが存在しない場合は空辞書を返す。

**例外**: `ValueError`（YAML ルートが mapping でない場合）

---

### `_save_yaml_file`

```python
def _save_yaml_file(self, path: Path, data: Mapping[str, object]) -> None
```

mapping を UTF-8 の YAML として保存する。親ディレクトリが存在しない場合は作成する。

---

### `_get_workspace_path`

```python
def _get_workspace_path(self) -> Path
```

OS に応じてユーザ別 workspace の `Path` を返す。

| プラットフォーム | パス |
|---|---|
| Windows (`win32`) | `%LOCALAPPDATA%/gistx/<user>/`（環境変数未設定時は `~/AppData/Local`） |
| Unix 系 | `~/.local/share/gistx/<user>/` |

---

## 操作対象パス

| パス | 操作 |
|---|---|
| `<ユーザディレクトリ>/gistlist/` | 空ディレクトリ削除 |
| `<ユーザディレクトリ>/fetch.yaml` | エントリ修復・上書き保存 |

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `Gistx.fix()` | `AppStore` を渡してインスタンス化し `run()` を呼び出す |
