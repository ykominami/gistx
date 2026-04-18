# クラス `Clix` 外部仕様

## 1. 対象
- クラス: `Clix`
- モジュール: `src/gistx/clix.py`
- 利用箇所: `gistx.py` の `mainx()` 関数

## 2. 目的
- `gistx` CLI のサブコマンドとオプションを `argparse` ベースで構築する。
- 各サブコマンドに対するハンドラ関数を外部から受け取り、引数解析後に自動的に呼び出せる状態にする。
- `mainx()` はこのクラスを経由することで、CLI 定義とサブコマンド実装を分離できる。

## 3. クラス定数

| 定数名  | 値        | 用途                              |
|---------|-----------|-----------------------------------|
| `SETUP` | `"setup"` | サブコマンド名。辞書キーとしても使用 |
| `CLONE` | `"clone"` | 同上                              |
| `CHECK` | `"check"` | 同上                              |
| `FIX`   | `"fix"`   | 同上                              |

## 4. インスタンス変数

| 変数名   | 型                            | 説明                                 |
|----------|-------------------------------|--------------------------------------|
| `cli`    | `yklibpy.cli.Cli`             | パーサ生成を委譲する `Cli` インスタンス |
| `parser` | `argparse.ArgumentParser`     | `cli.get_parser()` から取得したメインパーサ |
| `args`   | `argparse.Namespace \| None`  | `parse_args()` の解析結果。初期値 `None` |

## 5. コンストラクタ

### シグネチャ
```python
def __init__(self, description: str, command_dict: dict[str, CommandHandler]) -> None:
```

### 引数

| 引数名         | 型                              | 説明                                              |
|----------------|---------------------------------|---------------------------------------------------|
| `description`  | `str`                           | CLI 全体のヘルプ文字列                            |
| `command_dict` | `dict[str, CommandHandler]`     | サブコマンド名をキー、ハンドラ関数を値とする辞書 |

`CommandHandler` は `Callable[[argparse.Namespace], None]` の型エイリアスである。

### 動作
1. `Cli(description)` を生成して `self.cli` に保持する。
2. `self.cli.get_parser()` でメインパーサを取得して `self.parser` に保持する。
3. `self.cli.get_subparsers('command')` でサブパーサグループを取得する。
4. 下記 §6 で定義する 4 つのサブコマンドを登録する。

### 前提
- `command_dict` は `SETUP`・`CLONE`・`CHECK`・`FIX` の 4 キーをすべて含まなければならない。
- キーが不足している場合の動作は未定義（`KeyError` が送出される）。

## 6. サブコマンド定義

### 6.1 `setup`
- ヘルプ文字列: `"Setup for config file"`
- 追加オプション: なし
- デフォルトハンドラ: `command_dict[Clix.SETUP]`

### 6.2 `clone`
- ヘルプ文字列: `"Clone gists"`
- デフォルトハンドラ: `command_dict[Clix.CLONE]`
- オプション:

| オプション          | 型        | 必須 | 説明                                              |
|---------------------|-----------|------|---------------------------------------------------|
| `--public`          | フラグ    | 相互排他グループで必須 | public gist のみを clone する |
| `--private`         | フラグ    | 同上 | private gist のみを clone する                    |
| `--all`             | フラグ    | 同上 | すべての gist を clone する                       |
| `--max_gists`       | `int`     | 任意 | clone 対象件数の上限。省略時は `None`             |
| `-v`, `--verbose`   | フラグ    | 任意 | 詳細ログ出力。省略時は `False`                    |
| `-f`, `--force`     | フラグ    | 任意 | キャッシュを無視して gist 一覧を再取得する。省略時は `False` |

- `--public`、`--private`、`--all` は相互排他グループ（`add_mutually_exclusive_group(required=True)`）として定義され、必ず 1 つだけ指定しなければならない。

### 6.3 `check`
- ヘルプ文字列: `"Check for duplicates"`
- デフォルトハンドラ: `command_dict[Clix.CHECK]`
- オプション:

| オプション        | 型     | 必須 | 説明           |
|-------------------|--------|------|----------------|
| `-v`, `--verbose` | フラグ | 任意 | 詳細ログ出力。省略時は `False` |

### 6.4 `fix`
- ヘルプ文字列: `"Fix gistlist directory and fetch.yaml"`
- デフォルトハンドラ: `command_dict[Clix.FIX]`
- オプション:

| オプション        | 型     | 必須 | 説明           |
|-------------------|--------|------|----------------|
| `-v`, `--verbose` | フラグ | 任意 | 詳細ログ出力。省略時は `False` |

## 7. メソッド

### `parse_args`

#### シグネチャ
```python
def parse_args(self) -> argparse.Namespace:
```

#### 動作
- `self.parser.parse_args()` を呼び出してコマンドライン引数を解析する。
- 解析結果を `self.args` に保持し、同値を返す。
- 返り値の `argparse.Namespace` には `func` 属性が含まれ、その値は該当サブコマンドのハンドラ関数である。

#### 戻り値
- `argparse.Namespace`: 解析済みの引数オブジェクト

## 8. 利用パターン

```python
from gistx.clix import Clix
from gistx.gistx import Gistx

command_dict = {
    Clix.SETUP: Gistx.setup,
    Clix.CLONE: Gistx.clone,
    Clix.CHECK: Gistx.check,
    Clix.FIX:   Gistx.fix,
}

clix = Clix("get list of gists", command_dict)
args = clix.parse_args()
args.func(args)
```

`args.func` は `set_defaults(func=...)` によって設定されたハンドラであり、`args` を引数として呼び出すことでサブコマンドが実行される。

## 9. 非対象
- `Clix` はサブコマンドハンドラの実装を持たない。
- `Clix` は設定ファイルの読み書きを行わない。
- `Clix` は引数のバリデーション（`--max_gists` の正値チェック等）を行わない。バリデーションはハンドラ（`Gistx.clone` 等）の責務である。

## 10. 異常系
- `command_dict` に必要なキーが含まれない場合、コンストラクタ内で `KeyError` が送出される。
- 無効なサブコマンドまたは必須オプション未指定でコマンドが実行された場合、`argparse` がエラーメッセージを標準エラー出力へ書き出し、終了コード 2 でプロセスを終了する。

## 11. 依存
- `argparse`（標準ライブラリ）
- `yklibpy.cli.Cli`: パーサ生成・サブパーサグループ取得のラッパー

## 12. 関連クラスとの責務分担

| クラス      | 責務                                                    |
|-------------|---------------------------------------------------------|
| `Clix`      | CLI の構造定義（サブコマンド・オプション登録）と引数解析 |
| `Gistx`     | 各サブコマンドの実行ロジック（ハンドラの実装）           |
| `CommandSetup` / `CommandClone` / `CommandFix` | 各サブコマンドの具体的な処理本体 |
