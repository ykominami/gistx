# subcommand `clone` 外部仕様

## 1. 対象
- サブコマンド: `gistx clone`
- 関連クラス: `Clix`, `Gistx`, `CommandClone`, `GistInfo`
- 必要に応じて追加する独立関数:
  - なし

## 2. 目的
- 対象ユーザが保持する gist 一覧を取得または再利用する。
- 指定された公開範囲と最大件数に従って gist を clone する。
- gist 一覧取得履歴と clone 実行履歴をユーザ別ワークスペースへ記録する。

## 3. 呼び出し仕様
- コマンド形式:
  - `gistx clone --public [--max_gists <number>] [-f] [-v]`
  - `gistx clone --private [--max_gists <number>] [-f] [-v]`
  - `gistx clone --all [--max_gists <number>] [-f] [-v]`
- オプション:
  - `--public`
  - `--private`
  - `--all`
  - `--max_gists <number>`
  - `-f`, `--force`
  - `-v`, `--verbose`
- `Clix` は `--public`, `--private`, `--all` を相互排他的な必須オプションとして受け付ける。
- `Clix` は `--max_gists` に整数値を受け付ける。
- `Clix` は `-f`, `--force`, `-v`, `--verbose` を受け付ける。
- `Clix` はサブコマンド `clone` を受け付け、`Gistx.clone(args)` に委譲する。
- `Gistx.clone(args)` はログレベルを設定し、設定ファイルを読み込み、`CommandClone.run(args, repo_kind)` を呼び出す。

## 4. 対象パス
- コンフィグファイル
  - Windows: `%APPDATA%/gistx/config.yaml`
  - Unix 系: `~/.config/gistx/config.yaml`
- ユーザ別ワークスペース
  - Windows: `%LOCALAPPDATA%/gistx/<user>/`
  - Unix 系: `~/.local/share/gistx/<user>/`
- `clone` の生成物
  - `fetch.yaml`
    - Windows: `%LOCALAPPDATA%/gistx/<user>/fetch.yaml`
    - Unix 系: `~/.local/share/gistx/<user>/fetch.yaml`
  - `gistlist` トップディレクトリ
    - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/`
    - Unix 系: `~/.local/share/gistx/<user>/gistlist/`
  - gist 一覧スナップショット
    - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/<list_count>/list.yaml`
    - Unix 系: `~/.local/share/gistx/<user>/gistlist/<list_count>/list.yaml`
  - clone 実行履歴
    - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/<list_count>/gistrepo/progress.yaml`
    - Unix 系: `~/.local/share/gistx/<user>/gistlist/<list_count>/gistrepo/progress.yaml`
  - clone 先ディレクトリ
    - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/<list_count>/gistrepo/<clone_count>/{public|private}/<dir_name>/`
    - Unix 系: `~/.local/share/gistx/<user>/gistlist/<list_count>/gistrepo/<clone_count>/{public|private}/<dir_name>/`

## 5. 前提
- `setup` 実行済みで、`config.yaml` に `user` が設定されていること。
- `gh` CLI が利用可能であり、対象 gist にアクセスできる認証状態であること。
- `clone` は必要に応じて `<user>/`, `fetch.yaml`, `gistlist/` を補完作成してよい。
- `--max_gists` を指定する場合、その値は 1 以上の整数でなければならない。

## 6. オプション仕様
### 6.1 公開範囲オプション
- `--public` を指定した場合は public な gist のみを clone する。
- `--private` を指定した場合は private な gist のみを clone する。
- `--all` を指定した場合は public と private の両方を clone する。
- 上記 3 オプションは同時指定できず、必ず 1 つだけ指定しなければならない。

### 6.2 `--max_gists`
- `--max_gists <number>` は clone 対象 gist の最大件数を表す。
- `--max_gists` を省略した場合は、公開範囲で抽出された全件を clone 対象とする。
- `--max_gists` を指定した場合は、抽出後の gist 一覧の先頭から指定件数分だけを clone 対象とする。

### 6.3 `-f`, `--force`
- `--force` を指定した場合は、既存の `fetch.yaml` や最新 `list.yaml` の有無にかかわらず gist 一覧を再取得する。
- `--force` は既存 clone 済みディレクトリの上書きや再 clone を意味しない。
- `--force` を指定しない場合でも、`fetch.yaml` が空または存在しない場合、または最新 `list.yaml` が存在しない場合は gist 一覧を再取得する。

### 6.4 `-v`, `--verbose`
- `--verbose` を指定した場合、ログレベルを `logging.DEBUG` に設定する。
- `--verbose` を指定しない場合、ログレベルを `logging.INFO` に設定する。

## 7. gist 一覧取得仕様
- gist 一覧取得には `gh gist list --limit 1000` を用いる。
- `clone` は gist 一覧の取得結果を `gistlist/<list_count>/list.yaml` として保存する。
- gist 一覧を新規取得した場合、`list_count` は `gistlist/` 直下の数値名ディレクトリの最大値に 1 を加えた値とする。
- gist 一覧を再利用する場合、`clone` は最新の `gistlist/<list_count>/list.yaml` を読み込む。
- `gh gist list --limit 1000` を用いるため、現行実装で取得対象となる gist 一覧の上限は 1000 件である。

## 8. gist 一覧解析仕様
- `gh gist list` の各行から少なくとも gist ID、gist 名、公開範囲を抽出する。
- 公開範囲文字列 `public` は public gist、`secret` は private gist として扱う。
- gist 名が空の場合は gist ID を gist 名として扱う。
- gist 一覧の保存形式は次のマッピングを許容する。

```yaml
<gist_id>:
  gist_id: <gist_id>
  name: <gist_name>
  public: true
  dir_name: ""
```

## 9. `gistx clone` の処理仕様
`clone` は次の手順で処理する。

1. 設定ファイルから対象ユーザを取得し、ユーザ別ワークスペースを確定する。
2. `fetch.yaml` と `gistlist/` の存在を確認し、必要なら作成する。
3. `--force` とキャッシュ状態に基づき gist 一覧を新規取得するか、最新 `list.yaml` を再利用するかを決定する。
4. 公開範囲オプションに従って clone 対象 gist を抽出する。
5. `--max_gists` が指定されている場合は、抽出後の先頭から指定件数へ制限する。
6. 対象 `list_count` 配下の `gistrepo/<clone_count>/` を新規作成する。
7. 各 gist に対して clone 先ディレクトリ名を決定し、`gh gist clone <gist_id> <target_dir>` を実行する。
8. clone 試行結果を `progress.yaml` へ追記する。
9. gist 一覧を新規取得した場合のみ、`fetch.yaml` に当該 `list_count` の取得記録を追記する。

## 10. clone 先ディレクトリ名仕様
- clone 先ディレクトリ名は gist 名を元に決定する。
- Windows 予約文字 `<`, `>`, `:`, `"`, `/`, `\\`, `|`, `?`, `*` および制御文字は `_` に置換する。
- 前後の空白は除去する。
- 末尾の `.` は除去する。
- サニタイズ後に空文字となる場合は `_none` を用いる。
- 同一 clone 実行内で重複するディレクトリ名が発生する場合は、`<base_name>-1`, `<base_name>-2`, ... のように連番を付与して一意化する。
- 一意化は同一 clone 実行全体に対して行い、`public` と `private` をまたいでも重複させない。

## 11. 記録ファイル仕様
### 11.1 `fetch.yaml`
- gist 一覧を新規取得した場合のみ更新する。
- キーは `list_count` を表す文字列とする。
- 値は `[timestamp, clone_target_count]` の 2 要素リストとする。

```yaml
'1':
  - '2026-03-09 10:00:00'
  - 12
```

- `clone_target_count` は clone 成功件数ではなく、公開範囲と `--max_gists` 適用後の対象件数を表す。

### 11.2 `progress.yaml`
- `progress.yaml` は `gistrepo/` 直下に保持する。
- キーは `clone_count` を表す文字列とする。
- 値は少なくとも次の項目を持つマッピングとする。

```yaml
'1':
  timestamp: '2026-03-09 10:00:00'
  repo_kind: public
  requested_count: 12
  success_count: 11
  failure_count: 1
  list_count: 3
```

## 12. 非対象
- `clone` は `config.yaml` の内容を変更しない。
- `clone` は既存の `list.yaml` を再利用する場合、その内容を書き換えない。
- `clone` は既存 clone 済みディレクトリを削除しない。
- `clone` は既存 clone 済みディレクトリを上書きしない。
- `clone` は `gistlist` 直下以外に gist clone 用ディレクトリを作成しない。

## 13. 異常系
- `config.yaml` から `user` を取得できない場合は例外を送出し、処理を中止する。
- `--public`, `--private`, `--all` の指定数が 1 つでない場合は例外を送出する。
- `--max_gists` が 0 以下の場合は例外を送出する。
- `gh gist list` が失敗した場合は例外を送出する。
- `gh gist list` の出力から gist ID または公開範囲を解釈できない場合は例外を送出する。
- 最新 `list.yaml` の再利用が必要であるにもかかわらず当該ファイルが存在しない場合は例外を送出する。
- `fetch.yaml`, `list.yaml`, `progress.yaml` の YAML ルートがマッピングでない場合は例外を送出する。
- 個々の gist の clone に失敗した場合、その gist は失敗件数として記録し、残りの gist の処理は継続する。
- clone 先ディレクトリがすでに存在する場合、その gist は失敗件数として記録し、上書きせず継続する。

## 14. クラス責務
- `Clix`
  - `clone` サブコマンドを登録する。
  - `--public`, `--private`, `--all`, `--max_gists`, `-f`, `-v` を受け付ける。
- `Gistx.clone(args)`
  - ログレベルを設定する。
  - 公開範囲オプションと `--max_gists` を検証する。
  - 設定ファイルを読み込み、`CommandClone` を生成して実行する。
- `CommandClone.run(args, repo_kind)`
  - ユーザ別ワークスペースを準備する。
  - gist 一覧の取得または再利用を決定する。
  - gist 一覧の抽出、件数制限、clone 実行、進捗記録を行う。
- `CommandClone._parse_gh_gist_list_output(stdout_str)`
  - `gh gist list` の標準出力全体を `GistInfo` の連想配列へ変換する。
- `CommandClone._parse_gh_gist_list_line(line)`
  - 1 行分のテキストから gist ID、gist 名、公開範囲を抽出する。
- `CommandClone._filter_gists(gist_info_assoc, repo_kind)`
  - `public` / `private` / `all` に応じて対象 gist を抽出する。
- `CommandClone._limit_gists(gist_infos, max_gists)`
  - 最大件数制限を適用する。
- `CommandClone._clone_gists(gist_infos, clone_dir)`
  - clone 先ディレクトリ名を確定し、`gh gist clone` を実行する。

## 15. 実行後保証
- 対象ユーザのワークスペース配下に `fetch.yaml` と `gistlist/` が存在する。
- gist 一覧を新規取得した場合、`gistlist/<list_count>/list.yaml` が新規作成される。
- clone 実行ごとに `gistlist/<list_count>/gistrepo/<clone_count>/` が新規作成される。
- clone 試行結果は `progress.yaml` に記録される。
- gist 一覧を新規取得した場合、`fetch.yaml` に同じ `list_count` の記録が追加される。

## 16. 使用例
```bash
gistx clone --public
gistx clone --private --max_gists 10
gistx clone --all -f -v
```

## 17. 関連サブコマンドとの契約
- `setup` は `config.yaml`, `<user>/fetch.yaml`, `<user>/gistlist/` を初期化する。
- `clone` は `setup` が準備したユーザ別ワークスペースを利用して gist 一覧取得履歴と clone 実行履歴を蓄積する。
- `fix` は `clone` が生成した `gistlist` 配下と `fetch.yaml` の整合を保守対象とする。

## 18. 注記
- 要求文中の `gh glist clone` および `gh repo clone` という表現は、現行実装の外部挙動に合わせて `gh gist list` および `gh gist clone` として解釈する。
- 要求文では「すべての gist の一覧取得」としているが、現行実装の一覧取得上限は `gh gist list --limit 1000` に依存する。
