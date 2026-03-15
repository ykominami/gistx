# gistx コメント追加 外部仕様書

## 1. 目的

`src/gistx` 配下のソースコードに対して、クラス定義、メソッド定義、関数定義の先頭へ日本語 docstring を追加する。
docstring は実装の読み手が責務、前提条件、戻り値、失敗条件を短時間で把握できることを目的とする。

## 2. 対象範囲

- `src/gistx/gistx.py`
- `src/gistx/clix.py`
- `src/gistx/command_clone.py`
- `src/gistx/command_fix.py`
- `src/gistx/command_setup.py`
- `src/gistx/gistinfo.py`
- `src/gistx/appconfigx.py`
- `src/gistx/tomlx.py`

対象は以下の定義とする。

- すべてのクラス定義
- すべてのクラスメソッド
- すべてのインスタンスメソッド
- すべてのトップレベル関数

## 3. 記述ルール

### 3.1 言語

- docstring は日本語で記述する
- クラス名、メソッド名、関数名、引数名、外部コマンド名は英語の識別子をそのまま用いる

### 3.2 基本形式

- PEP 257 ベースの簡潔な docstring とする
- 短い定義は 1 から 3 段落で記述する
- 複雑な引数、戻り値、例外の説明が必要な定義のみ Google style を使う
- 型の説明は型ヒントに任せ、docstring には意味、制約、前提、失敗条件を書く

### 3.3 記述内容

各 docstring では必要に応じて以下を記述する。

- 何をするか
- どのような前提や条件で動作するか
- 何を返すか
- どのような場合に失敗するか

### 3.4 既存記述の扱い

- 既存の仕様記述に相当する docstring があれば削除し、新しい docstring に置き換える
- 既存のインラインコメントは、責務説明と重複する場合のみ整理対象とする

## 4. モジュール別の記述観点

### 4.1 `gistx.py`

- `Gistx` クラスは CLI 全体のオーケストレーション責務を記述する
- `init_appstore()` は設定ファイル、DB ファイル、DB ディレクトリの準備条件を記述する
- `_load_config_with_legacy_fallback()` は `.yaml` と旧 `.yml` の後方互換読込を記述する
- `setup()`、`clone()`、`fix()` は各サブコマンドの入口としての責務と主な失敗条件を記述する
- `mainx()` は引数解析からサブコマンド実行までの流れを記述する

### 4.2 `clix.py`

- `Clix` クラスはサブコマンド定義と `argparse` 設定の責務を記述する
- `__init__()` は `setup`、`clone`、`check`、`fix` のオプション構築を記述する
- `parse_args()` は CLI 入力を解析して `Namespace` を返すことを記述する

### 4.3 `command_clone.py`

- `ConfigFileInfo` は設定ファイル関連情報をまとめる補助データであることを記述する
- `CommandClone` クラスは gist 一覧取得、一覧キャッシュ再利用、clone 実行、進捗記録の責務を記述する
- `run()` は clone 全体フローを記述し、複雑なため Google style を用いてよい
- `_prepare_clone()` は workspace、`gistlist`、`gistrepo`、`clone_count` 準備の意味を記述する
- `_parse_gh_gist_list_output()` と `_parse_gh_gist_list_line()` は `gh gist list` 出力の前提と失敗条件を記述する
- `_sanitize_gist_name()` と `_make_unique_dir_name()` は clone 先ディレクトリ名の正規化規則を記述する
- YAML 入出力系メソッドは、YAML ルートが mapping である前提を記述する
- `_decode_command_output()` はデコードの試行順とフォールバックを記述する
- `_clone_gists()` は clone の成功件数、失敗件数、既存ディレクトリ検出時の扱いを記述する
- `fetch.yaml` と `progress.yaml` 更新メソッドは更新内容の意味を記述する

### 4.4 `command_fix.py`

- トップレベル関数は、空ディレクトリ削除と `fetch.yaml` 整合化の純粋な補助処理として記述する
- `CommandFix` クラスは保守用サブコマンドの責務を記述する
- `run()` は workspace 存在確認、空ディレクトリ削除、`fetch.yaml` 修復の流れを記述する
- `_fix_fetch_yaml()` は既存ディレクトリ一覧に合わせて `fetch.yaml` を再構成することを記述する

### 4.5 `command_setup.py`

- `CommandSetup` クラスは初期設定とユーザ workspace の準備責務を記述する
- `run()` は `gh` からユーザ名を取得し、設定ファイルを書き出すことを記述する
- `_prepare_user_workspace()` は `fetch.yaml` と `gistlist` トップディレクトリの初期化を記述する
- `_get_workspace_path()` は OS ごとのデータディレクトリ解決を記述する

### 4.6 `gistinfo.py`

- `GistInfo` クラスは gist 1 件分の識別子、表示名、公開状態、clone 先ディレクトリ名を保持することを記述する
- `add_dir_name()` は clone 実行時に決定したディレクトリ名を反映することを記述する

### 4.7 `appconfigx.py`

- `AppConfigx` クラスは `gistx` 用の設定名、DB 名、ディレクトリ名、既定値の定義を記述する

### 4.8 `tomlx.py`

- `Tomlx` クラスは `Tomlop` の薄いラッパーであることを記述する
- `run()` は変換処理の実行を記述する
- `main()` は既定ファイルを使って `Tomlx` を起動することを記述する

## 5. 実装上の注意

- docstring 追加によって既存の型ヒントや処理ロジックは変更しない
- docstring のために import 構成や公開 API を変更しない
- 非自明な補足が必要な場合のみ、最小限のインラインコメントを残す

## 6. 完了条件

- 対象ファイル内の全クラス、全メソッド、全トップレベル関数に日本語 docstring が存在する
- docstring は本仕様書の形式と記述内容に従っている
- 追加後に構文エラーや明白な lint エラーが発生していない
