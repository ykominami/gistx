# subcommand `setup` 外部仕様

## 1. 対象
- サブコマンド: `gistx setup`
- 関連クラス: `Clix`, `Gistx`, `CommandSetup`

## 2. 目的
- `clone` 実行前の初期化を行う。
- 設定ファイルに初期値を設定する。
- ユーザ別ワークスペースを作成する。

## 3. 呼び出し仕様
- コマンド形式: `gistx setup`
- 引数: なし
- `Clix` はサブコマンド `setup` を受け付け、`Gistx.setup()` に委譲する。
- `Gistx.setup()` は `AppStore` を初期化し、`CommandSetup.run()` を呼び出す。

## 4. 入力
- GitHub ユーザ名は `CommandGhUser().run()` の戻り値を用いる。
- 戻り値が空の場合は `CommandGhUser.DEFAULT_VALUE_USER` を用いる。

## 5. 出力生成物
`setup` が正として作成、更新する生成物は次の 3 点のみとする。

1. コンフィグファイル
   - パス
     - Windows: `%APPDATA%/gistx/config.yaml`
     - Unix 系: `~/.config/gistx/config.yaml`
   - YAML フォーマット

```yaml
gists: gists
url_api: https://api.github.com
user: <ユーザ名>
```

2. fetch ファイル
   - パス
     - Windows: `%LOCALAPPDATA%/gistx/<user>/fetch.yaml`
     - Unix 系: `~/.local/share/gistx/<user>/fetch.yaml`
   - 初期状態
     - 空ファイルとする。
     - `setup` 再実行時も空ファイルへ初期化する。

3. gistlist トップディレクトリ
   - パス
     - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/`
     - Unix 系: `~/.local/share/gistx/<user>/gistlist/`
   - 初期状態
     - 空ディレクトリとして存在する。
     - `setup` はこの直下に子要素を作成しない。

## 6. 非生成物
- `setup` は以下の旧生成物を作成しない。
  - `%LOCALAPPDATA%/gistx/db.yaml`
  - `%LOCALAPPDATA%/gistx/fetch.yaml`
  - `%LOCALAPPDATA%/gistx/list.yaml`
  - `%LOCALAPPDATA%/gistx/repo/`
  - `%LOCALAPPDATA%/gistx/gistlist/`

## 7. 再実行時の振る舞い
- `config.yaml` は同じ初期値で上書きする。
- `fetch.yaml` は空ファイルに戻す。
- `gistlist/` が存在しない場合は作成する。
- `gistlist/` がすでに存在する場合、既存内容は削除しない。
  - 理由: 既存の取得済みデータを `setup` が破壊しないため。

## 8. 異常系
- コンフィグファイル、`fetch.yaml`、`gistlist/` の作成に失敗した場合は例外を送出する。
- GitHub ユーザ名が取得できなくても、既定値へフォールバックして継続する。

## 9. 関連サブコマンドとの契約
- `clone` は `setup` 実行後、追加の初期化なしで次を前提に動作できること。
  - `config.yaml` に `user` が設定済みであること
  - `%LOCALAPPDATA%/gistx/<user>/fetch.yaml` が存在すること
  - `%LOCALAPPDATA%/gistx/<user>/gistlist/` が存在すること

## 10. クラス責務
- `Clix`
  - `setup` サブコマンドを登録する。
- `Gistx.setup()`
  - `config.yaml` を扱うための `AppStore` を初期化する。
  - `CommandSetup` を生成して実行する。
- `CommandSetup.run()`
  - ユーザ名を確定する。
  - `config.yaml` を出力する。
  - ユーザ別ワークスペースを初期化する。
- `CommandSetup._prepare_user_workspace(user)`
  - `<user>/fetch.yaml` を空ファイルとして初期化する。
  - `<user>/gistlist/` を作成する。
- `CommandSetup._get_workspace_path(user)`
  - OS ごとのユーザ別ワークスペースパスを返す。
