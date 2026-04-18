# 外部仕様書 — `Clix`

**ファイル**: `src/gistx/clix.py`

## 概要

`gistx` CLI のサブコマンド定義とオプション解析を担当するクラス。`yklibpy.Cli` をラップして `argparse` パーサを構築し、各サブコマンドのオプションを設定する。

---

## クラス定数

| 定数名 | 値 | 説明 |
|---|---|---|
| `SETUP` | `"setup"` | setup サブコマンド識別子 |
| `CLONE` | `"clone"` | clone サブコマンド識別子 |
| `CHECK` | `"check"` | check サブコマンド識別子（未実装） |
| `FIX` | `"fix"` | fix サブコマンド識別子 |

---

## コンストラクタ

```python
Clix(
    description: str,
    command_dict: dict[str, CommandHandler],
) -> None
```

`argparse` パーサを構築し、4 つのサブコマンド（`setup`・`clone`・`check`・`fix`）を登録する。

### パラメータ

| 名前 | 型 | 説明 |
|---|---|---|
| `description` | `str` | CLI 全体のヘルプ文字列 |
| `command_dict` | `dict[str, CommandHandler]` | サブコマンド名 → ハンドラ関数の辞書 |

### 登録されるサブコマンドとオプション

#### `setup`

| オプション | 型 | 説明 |
|---|---|---|
| （なし） | — | オプションなし |

#### `clone`

| オプション | 型 | 必須 | 説明 |
|---|---|---|---|
| `--public` | フラグ | 排他必須 | public gist のみ clone |
| `--private` | フラグ | 排他必須 | secret gist のみ clone |
| `--all` | フラグ | 排他必須 | すべての gist を clone |
| `--max_gists` | `int` | — | clone する最大件数（省略時: 無制限） |
| `-v` / `--verbose` | フラグ | — | ログを DEBUG レベルで出力 |
| `-f` / `--force` | フラグ | — | キャッシュを無視して gist 一覧を再取得 |

`--public`・`--private`・`--all` は排他グループ（`required=True`）。

#### `check`

| オプション | 型 | 説明 |
|---|---|---|
| `-v` / `--verbose` | フラグ | ログを DEBUG レベルで出力 |

> `check` サブコマンドは現在未実装（`Gistx.check()` が `NotImplementedError` を送出する）。

#### `fix`

| オプション | 型 | 説明 |
|---|---|---|
| `-v` / `--verbose` | フラグ | ログを DEBUG レベルで出力 |

---

## インスタンスメソッド

### `parse_args`

```python
def parse_args(self) -> argparse.Namespace
```

コマンドライン引数を解析して `argparse.Namespace` を返す。解析結果は `self.args` にも保持する。

**戻り値**: `argparse.Namespace`（各オプション値と `func` 属性を含む）  
**例外**: argparse がエラー時に `SystemExit` を送出

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `Gistx` / `mainx()` | `Clix` を生成し `parse_args()` を呼び出してサブコマンドをディスパッチ |
