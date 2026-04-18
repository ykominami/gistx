# 外部仕様書 — `Gistx` / `mainx`

**ファイル**: `src/gistx/gistx.py`

## 概要

`gistx` CLI の最上位調停クラス。`AppStore` の初期化と設定読み込みを行い、各サブコマンド（`setup`・`clone`・`check`・`fix`）を対応する `Command` クラスに委譲する。すべてのメソッドはクラスメソッドとして実装されており、インスタンス化は不要。

モジュールレベル関数 `mainx()` がエントリポイントであり、`pyproject.toml` の `[project.scripts]` から `gistx` コマンドとして登録される。

---

## エントリポイント

### `mainx`

```python
def mainx() -> None
```

CLI のエントリポイント。`Clix` でコマンドライン引数を解析し、対応するサブコマンドハンドラ（`Gistx` のクラスメソッド）を呼び出す。

#### サブコマンドとハンドラの対応

| サブコマンド | ハンドラ |
|---|---|
| `setup` | `Gistx.setup` |
| `clone` | `Gistx.clone` |
| `check` | `Gistx.check` |
| `fix` | `Gistx.fix` |

---

## クラスメソッド

### `init_appstore`

```python
@classmethod
def init_appstore(
    cls,
    *,
    prepare_db_file: bool = False,
    prepare_db_directory: bool = False,
) -> AppStore
```

`gistx` 用の `AppStore` を初期化して返す。設定ファイルは常に準備する。

#### パラメータ

| 名前 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `prepare_db_file` | `bool` | `False` | DB ファイルを準備するか |
| `prepare_db_directory` | `bool` | `False` | DB ディレクトリを準備するか |

#### 処理内容

1. `Storex.set_file_type_dict(AppConfigx.file_type_dict)` でファイルタイプを設定する。
2. `AppStore("gistx", AppConfigx.file_assoc, None, AppConfigx.directory_assoc)` を生成する。
3. `appstore.prepare_config_file()` を呼び出す（常に実行）。
4. フラグに応じて `prepare_db_file()`・`prepare_db_directory()` を呼び出す。

**戻り値**: 初期化済みの `AppStore`  
**例外**: ファイルシステム操作の失敗時は OS 例外

---

### `_load_config_with_legacy_fallback`

```python
@classmethod
def _load_config_with_legacy_fallback(cls, appstore: AppStore) -> None
```

`config.yaml` を読み込み、内容が空の場合はレガシーの `config.yml` へフォールバックする。

#### 処理手順

1. `appstore.load_file_config_all()` で `config.yaml` を読み込む。
2. 読み込んだ内容が空でなければ終了。
3. 空の場合、`config.yml`（`.yml` 拡張子）が存在するか確認する。
4. 存在すれば `config.yml` を読み込み、`appstore.file_assoc` に内容を注入する。

**戻り値**: なし  
**例外**: `ValueError`（`config.yml` のルートが mapping でない場合）

---

### `setup`

```python
@classmethod
def setup(cls, args: argparse.Namespace) -> None
```

`setup` サブコマンドを実行する。`AppStore` を初期化し、`CommandSetup.run()` に委譲する。

**戻り値**: なし  
**例外**: `CommandSetup.run()` が送出する例外に準ずる

---

### `clone`

```python
@classmethod
def clone(cls, args: argparse.Namespace) -> None
```

`clone` サブコマンドを実行する。

#### 処理手順

1. `args.verbose` に応じてログレベルを `DEBUG` または `INFO` に設定する。
2. `--public`・`--private`・`--all` のうち正確に 1 つが指定されているか検証する。
3. `args.max_gists` が指定されている場合、1 以上であるか検証する。
4. `repo_kind` を決定する。
5. `AppStore` を初期化し、設定を読み込む。
6. `CommandClone(appstore).run(args, repo_kind)` に委譲する。

#### 例外

| 例外 | 条件 |
|---|---|
| `ValueError` | `--public`・`--private`・`--all` の指定が正確に 1 つでない場合 |
| `ValueError` | `--max_gists` が 0 以下の場合 |

---

### `check`

```python
@classmethod
def check(cls, args: argparse.Namespace) -> None
```

未実装のサブコマンド。常に `NotImplementedError` を送出する。

**例外**: `NotImplementedError`（常に）

---

### `fix`

```python
@classmethod
def fix(cls, args: argparse.Namespace) -> None
```

`fix` サブコマンドを実行する。

#### 処理手順

1. `args.verbose` に応じてログレベルを `DEBUG` または `INFO` に設定する。
2. `AppStore` を初期化し、設定を読み込む。
3. `CommandFix(appstore).run(args)` に委譲する。

**戻り値**: なし  
**例外**: `CommandFix.run()` が送出する例外に準ずる

---

## CLI フロー

```
mainx()
  └── Clix.parse_args()
        └── args.func(args)   # サブコマンドに対応する Gistx クラスメソッド
              ├── Gistx.setup(args)  → CommandSetup.run()
              ├── Gistx.clone(args)  → CommandClone.run(args, repo_kind)
              ├── Gistx.check(args)  → NotImplementedError
              └── Gistx.fix(args)    → CommandFix.run(args)
```
