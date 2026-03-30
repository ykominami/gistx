# `fix` サブコマンド 外部仕様書

## 1. 概要

`gistx fix` は `repo` ディレクトリ以下を整理する保守コマンド。以下の 2 つの操作を順に行う。

1. **空ディレクトリの削除**: `repo` ディレクトリ以下を再帰的に走査し、空のディレクトリをすべて削除する。
2. **`fetch.yml` の整合修正**: `repo` 以下 2 段階下にある数字名ディレクトリの最大値が `fetch.yml` の最大エントリ名と一致するように `fetch.yml` を修正する。

---

## 2. 新設クラス: `CommandFix`

**ファイル**: `src/gistx/command_fix.py`

### 2.1 継承

```python
class CommandFix(Command):
```

`yklibpy.command.command.Command` を継承する（`CommandClone` / `CommandSetup` と同様）。

---

### 2.2 コンストラクタ

```python
def __init__(self, appstore: AppStore) -> None:
```

| 引数 | 型 | 説明 |
|---|---|---|
| `appstore` | `AppStore` | 設定・DB ファイルへのアクセスを提供する |

- `self.appstore = appstore` を保持する。
- repo ディレクトリパスは `run()` 内で `appstore` から取得する。

---

### 2.3 パブリックメソッド

#### `run`

```python
def run(self, args: argparse.Namespace) -> None:
```

以下を順に実行する。

1. `appstore` から `repo` ディレクトリのパス (`Path`) を取得する。  
   取得方法: `appstore.get_directory_assoc_from_db(AppConfigx.BASE_NAME_REPO)[AppConfigx.PATH]`
2. repo パスが存在しない場合は `FileNotFoundError` を raise する。
3. `_remove_empty_dirs(repo_path)` を呼び出す。
4. `_fix_fetch_yaml(repo_path)` を呼び出す。

---

### 2.4 プライベートメソッド

#### `_remove_empty_dirs`

```python
def _remove_empty_dirs(self, path: Path) -> int:
```

**責務**: `path` 以下を bottom-up で走査し、空のディレクトリをすべて削除する。

**アルゴリズム**:

- `os.walk(path, topdown=False)` を使用して bottom-up 走査を行う。
- 各ディレクトリについて、`Path.iterdir()` でエントリが存在しない場合（空）に `Path.rmdir()` で削除する。
- `path` 自体は削除しない（repo ルートは保持する）。

**戻り値**: 削除したディレクトリの数 (`int`)

**例外**: ディレクトリ削除に失敗した場合は `OSError` を伝播させる。

---

#### `_get_max_numeric_dir`

```python
def _get_max_numeric_dir(self, repo_path: Path) -> int | None:
```

**責務**: `repo/{*}/{*}` の形で 2 段階下に存在する、名前が数字のみのディレクトリの中から最大の整数値を返す。

**アルゴリズム**:

1. `repo_path` の直下ディレクトリ (`level1`) を列挙する。
2. 各 `level1` の直下ディレクトリ (`level2`) を列挙する。
3. `level2` の名前が `str.isdigit()` を満たし、かつ整数値が正 (`> 0`) の場合のみ収集する。
4. 収集した整数値が空の場合は `None` を返す。
5. 最大値を返す。

---

#### `_fix_fetch_yaml`

```python
def _fix_fetch_yaml(self, repo_path: Path) -> None:
```

**責務**: `fetch.yml` の最大キーを `repo` 以下 2 段階下の数字名ディレクトリの最大値に合わせる。

**アルゴリズム**:

1. `_get_max_numeric_dir(repo_path)` を呼び出し `max_dir` を取得する。
2. `max_dir` が `None` の場合は何もせずに返る。
3. `appstore.get_file_assoc_from_db(AppConfig.BASE_NAME_FETCH)` で現在の `fetch.yml` を `dict` として取得する。  
   取得値が `None` または空の場合は空 dict として扱う。
4. `max_dir` を文字列キーとして持たない場合、`Timex.get_now()` を値として追加する。
5. `int(k) > max_dir` となるキー `k` をすべて削除する（`max_dir` より大きいエントリを除去）。
6. `appstore.output_db(AppConfig.BASE_NAME_FETCH, fetch_assoc)` で書き出す。

**事後条件**:

- `fetch.yml` に `str(max_dir)` キーが存在する。
- `fetch.yml` のすべてのキー `k` について `int(k) <= max_dir` が成立する。

---

### 2.5 エラー処理まとめ

| 状況 | 挙動 |
|---|---|
| repo ディレクトリが存在しない | `run()` で `FileNotFoundError` を raise |
| 空ディレクトリの削除失敗 | `OSError` を伝播 |
| repo 以下 2 段階に数字名ディレクトリが存在しない | `_fix_fetch_yaml` は何も変更せずに正常終了 |
| `fetch.yml` が存在しない / 空 | 空 dict として扱い、`max_dir` のみを含む dict を書き出す |

---

## 3. 既存ファイルの変更

### 3.1 `src/gistx/clix.py`

**追加定数**:

```python
FIX = "fix"
```

**サブパーサー追加** (`__init__` 内):

```python
p_fix = subparsers.add_parser(self.FIX, help="Fix repo directory and fetch.yml")
p_fix.set_defaults(func=command_dict[self.FIX])
p_fix.add_argument("-v", "--verbose", action="store_true")
```

**`command_dict` の受け入れ**: `command_dict[Clix.FIX]` が参照できるよう、呼び出し元 `mainx()` でキーを追加する（次節参照）。

---

### 3.2 `src/gistx/gistx.py`

**インポート追加**:

```python
from gistx.command_fix import CommandFix
```

**クラスメソッド追加** (`Gistx` クラス内):

```python
@classmethod
def fix(cls, args: argparse.Namespace) -> None:
    if args.verbose:
        Loggerx.set_log_level(logging.DEBUG)
    else:
        Loggerx.set_log_level(logging.INFO)
    appstore = cls.init_appstore()
    appstore.load_file_all()
    command = CommandFix(appstore)
    command.run(args)
```

**`mainx()` の変更**:

```python
command_dict = {
    Clix.SETUP: Gistx.setup,
    Clix.CLONE: Gistx.clone,
    Clix.CHECK: Gistx.check,
    Clix.FIX:   Gistx.fix,   # 追加
}
```

---

## 4. ディレクトリ構造と `fetch.yml` の対応関係

```
AppData\Local\gistx\
  fetch.yml           ← FetchCount が管理するカウンタ台帳
  repo\               ← BASE_NAME_REPO ディレクトリ
    {N}\              ← 段階 1（実行グループ番号）
      {M}\            ← 段階 2（fetch count。fetch.yml のキーと対応）
        public\
        private\
```

`fetch.yml` の内容例:

```yaml
'1': '2025-01-10 12:00:00'
'2': '2025-02-01 09:30:00'
'3': '2025-03-06 15:00:00'
```

`fix` 実行後、ディスク上の `{M}` 最大値が `3` であれば fetch.yml の最大キーも `'3'` になる。

---

## 5. `fix` 実行後の保証

| 保証項目 | 内容 |
|---|---|
| 空ディレクトリなし | `repo` 以下のいかなるディレクトリも空でない |
| `fetch.yml` 最大キー整合 | `fetch.yml` の最大キー（整数値として評価）= `repo` 以下 2 段階の数字名ディレクトリの最大整数値 |

---

## 6. 使用例

```bash
gistx fix
gistx fix -v   # デバッグログ出力
```
