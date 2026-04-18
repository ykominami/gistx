# 外部仕様書 — `CommandSetup`

**ファイル**: `src/gistx/command_setup.py`

## 概要

`gistx setup` サブコマンドの実装クラス。`gh` CLI から GitHub ユーザ名を取得し、設定ファイル（`config.yaml`）の書き出しとユーザ別 workspace ディレクトリの初期化を行う。

---

## 継承

```
yklibpy.command.command.Command
    └── CommandSetup
```

---

## コンストラクタ

```python
CommandSetup(appstore: AppStore) -> None
```

### パラメータ

| 名前 | 型 | 説明 |
|---|---|---|
| `appstore` | `AppStore` | 設定ファイルの書き出しに使用する `yklibpy.AppStore` インスタンス |

---

## インスタンスメソッド

### `run`

```python
def run(self) -> None
```

GitHub ユーザを決定し、設定ファイルと workspace を初期化する。

#### 処理手順

1. `CommandGhUser().run()` で `gh auth status` からログイン中のユーザ名を取得する。
2. 取得できない場合は `CommandGhUser.DEFAULT_VALUE_USER` を使用する。
3. 取得したユーザ名を標準出力に表示する（`user=<username>`）。
4. 以下のキーを持つ辞書を `AppStore.output_config()` に渡し、`config.yaml` を書き出す。

   | キー（`AppConfigx` 定数） | 値 |
   |---|---|
   | `KEY_GISTS` | `DEFAULT_VALUE_GISTS`（`"gists"`） |
   | `KEY_URL_API` | `DEFAULT_VALUE_URL_API`（`"https://api.github.com"`） |
   | `KEY_USER` | 取得したユーザ名 |

5. `_prepare_user_workspace(user)` を呼び出して workspace を初期化する。

**戻り値**: なし  
**例外**: `gh` CLI の実行に失敗した場合、親クラス `Command` の例外に準ずる

---

### `_prepare_user_workspace` *(プライベート)*

```python
def _prepare_user_workspace(self, user: str) -> None
```

ユーザ別 workspace ディレクトリと初期ファイルを作成する。

#### 作成するパス

| パス | 説明 |
|---|---|
| `<ユーザディレクトリ>/` | ユーザ別 workspace ルート（`mkdir -p`） |
| `<ユーザディレクトリ>/gistlist/` | gistlist トップディレクトリ（`mkdir -p`） |
| `<ユーザディレクトリ>/fetch.yaml` | 空ファイルとして初期化 |

> `<ユーザディレクトリ>` については後述の「ユーザディレクトリ解決ルール」を参照。

**戻り値**: なし  
**例外**: ファイルシステムへの書き込みが失敗した場合は OS 例外

---

### `_get_workspace_path` *(プライベート)*

```python
def _get_workspace_path(self, user: str) -> Path
```

OS に応じてユーザ別 workspace の `Path` を返す。

#### ユーザディレクトリ解決ルール

| プラットフォーム | パス |
|---|---|
| Windows (`win32`) | `%LOCALAPPDATA%/gistx/<user>/`（環境変数未設定時は `~/AppData/Local`） |
| Unix 系 | `~/.local/share/gistx/<user>/` |

**戻り値**: `Path`  
**例外**: なし

---

## 設定ファイルの出力先

| ファイル | パス |
|---|---|
| `config.yaml` | Windows: `%APPDATA%/gistx/config.yaml`、Unix: `~/.config/gistx/config.yaml` |

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `Gistx.setup()` | `AppStore` を渡してインスタンス化し `run()` を呼び出す |
