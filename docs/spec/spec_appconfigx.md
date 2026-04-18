# 外部仕様書 — `AppConfigx`

**ファイル**: `src/gistx/appconfigx.py`

## 概要

`yklibpy.AppConfig` を継承し、`gistx` 固有の設定名・DB 名・ディレクトリ名・既定値を定義するクラス。インスタンス化せずにクラス変数・クラス定数として参照する。

---

## 継承

```
yklibpy.config.appconfig.AppConfig
    └── AppConfigx
```

---

## クラス定数

### ベース名（ファイル・ディレクトリ識別子）

| 定数名 | 値 | 用途 |
|---|---|---|
| `BASE_NAME_FETCH` | `AppConfig.BASE_NAME_FETCH` | fetch 系ファイルのベース名（親クラスから継承） |
| `BASE_NAME_LIST` | `"list"` | 一覧系ファイルのベース名 |
| `BASE_NAME_GIST` | `"gist"` | gist 識別子 |
| `BASE_NAME_GISTLIST_TOP` | `"gistlist"` | gistlist トップディレクトリ名 |
| `BASE_NAME_WORKSPACES_TOP` | `"workspaces"` | workspaces トップディレクトリ名 |
| `BASE_NAME_PROGRESS` | `"progress"` | progress ファイルのベース名 |
| `BASE_NAME_GISTREPO_DB` | `"db"` | gistrepo DB のベース名 |
| `BASE_NAME_REPO` | `"repo"` | リポジトリ系のベース名 |

### 設定キー

| 定数名 | 値 | 説明 |
|---|---|---|
| `KEY_USER` | `"user"` | `config.yaml` の GitHub ユーザ名キー |
| `KEY_URL_API` | `"url_api"` | `config.yaml` の GitHub API URL キー |
| `KEY_GISTS` | `"gists"` | `config.yaml` の gists キー |

### 既定値

| 定数名 | 値 | 説明 |
|---|---|---|
| `DEFAULT_VALUE_URL_API` | `"https://api.github.com"` | GitHub API の既定 URL |
| `DEFAULT_VALUE_GISTS` | `"gists"` | gists の既定値 |

---

## クラス変数（継承元から拡張）

### `file_type_dict`

```python
file_type_dict = {**AppConfig.file_type_dict, AppConfig.FILE_TYPE_YAML: ".yaml"}
```

`FILE_TYPE_YAML` を `.yaml` 拡張子にマッピングする辞書。

### `file_type_reverse_dict`

```python
file_type_reverse_dict = {ext_name: file_type for file_type, ext_name in file_type_dict.items()}
```

拡張子からファイルタイプへの逆引き辞書。

### `file_synonym_dict`

```python
file_synonym_dict = {**AppConfig.file_synonym_dict, ".yml": ".yaml"}
```

`.yml` を `.yaml` にエイリアスする辞書。レガシー設定ファイルの後方互換対応に使用。

### `file_assoc`

親クラスの `file_assoc` をディープコピーして拡張。`KIND_DB` に `BASE_NAME_LIST` を登録。

| キー | ファイルタイプ | 説明 |
|---|---|---|
| `KIND_DB / BASE_NAME_LIST` | `FILE_TYPE_YAML` | 一覧用 YAML ファイル |

### `directory_assoc`

親クラスの `directory_assoc` をディープコピーして拡張。以下を登録。

| キー | 説明 |
|---|---|
| `KIND_DB / BASE_NAME_WORKSPACES_TOP` | workspaces トップディレクトリ |
| `KIND_DB / BASE_NAME_REPO` | リポジトリディレクトリ |

---

## 利用箇所

| 利用クラス | 利用目的 |
|---|---|
| `Gistx` | `AppStore` 初期化時に `file_assoc`・`directory_assoc` を渡す |
| `CommandSetup` | 設定キーと既定値の参照 |
| `CommandClone` | ベース名・設定キーの参照 |
| `CommandFix` | ベース名の参照 |
