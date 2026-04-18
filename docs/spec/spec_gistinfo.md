# 外部仕様書 — `GistInfo`

**ファイル**: `src/gistx/gistinfo.py`

## 概要

gist 1 件分の基本情報（ID・表示名・公開状態・clone 先ディレクトリ名）を保持するデータクラス。`CommandClone` が gist 一覧を構築する際に生成し、clone 処理全体を通じて受け渡される。

---

## クラス変数（アノテーションのみ）

| 名前 | 型 | 説明 |
|---|---|---|
| `gist_id` | `str` | GitHub が割り当てる gist の一意識別子（16進数文字列） |
| `name` | `str` | gist の表示名（`gh gist list` の DESCRIPTION 列） |
| `public` | `bool` | `True` = public gist、`False` = secret gist |
| `dir_name` | `str` | clone 先ディレクトリ名（clone 実行後に `add_dir_name()` で設定） |

---

## コンストラクタ

```python
GistInfo(
    gist_id: str,
    name: str,
    public: bool = True,
    dir_name: str = "",
) -> None
```

### パラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `gist_id` | `str` | ○ | gist の識別子 |
| `name` | `str` | ○ | gist の表示名 |
| `public` | `bool` | — | 公開状態（デフォルト: `True`） |
| `dir_name` | `str` | — | clone 先ディレクトリ名（デフォルト: 空文字） |

---

## インスタンスメソッド

### `add_dir_name`

```python
def add_dir_name(self, dir_name: str) -> None
```

clone 実行時に確定したディレクトリ名を `self.dir_name` に設定する。`CommandClone._clone_gists()` が各 gist を clone する直前に呼び出す。

| パラメータ | 型 | 説明 |
|---|---|---|
| `dir_name` | `str` | clone 先ディレクトリ名（Windows 禁則文字をサニタイズ済みの文字列） |

**戻り値**: なし  
**例外**: なし

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `CommandClone` | `_parse_gh_gist_list_line()` で生成、`_clone_gists()` で `add_dir_name()` を呼び出す |
