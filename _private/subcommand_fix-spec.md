# subcommand `fix` 外部仕様

## 1. 対象
- サブコマンド: `gistx fix`
- 関連クラス: `Clix`, `Gistx`, `CommandFix`
- 必要に応じて追加する独立関数:
  - `remove_empty_directories(root: Path) -> int`
  - `collect_existing_gistlist_counts(gistlist_top_dir: Path) -> list[int]`
  - `reconcile_fetch_entries(fetch_assoc: dict[str, object], existing_counts: list[int]) -> dict[str, object]`

## 2. 目的
- `gistlist` トップディレクトリ配下に空ディレクトリが残らないように保守する。
- 実在する `gistlist` ディレクトリ群と整合するように `fetch.yaml` のエントリを補正する。
- `setup` と `clone` が作るユーザ別ワークスペースを破壊せず、管理情報だけを修復する。

## 3. 呼び出し仕様
- コマンド形式: `gistx fix`
- オプション:
  - `-v`, `--verbose`
- `Clix` はサブコマンド `fix` を受け付け、`Gistx.fix(args)` に委譲する。
- `Gistx.fix(args)` は `AppStore` を初期化し、設定ファイルを読み込み、`CommandFix.run(args)` を呼び出す。

## 4. 対象パス
- コンフィグファイル
  - Windows: `%APPDATA%/gistx/config.yaml`
  - Unix 系: `~/.config/gistx/config.yaml`
- ユーザ別ワークスペース
  - Windows: `%LOCALAPPDATA%/gistx/<user>/`
  - Unix 系: `~/.local/share/gistx/<user>/`
- `fix` の直接対象
  - `fetch.yaml`
    - Windows: `%LOCALAPPDATA%/gistx/<user>/fetch.yaml`
    - Unix 系: `~/.local/share/gistx/<user>/fetch.yaml`
  - `gistlist` トップディレクトリ
    - Windows: `%LOCALAPPDATA%/gistx/<user>/gistlist/`
    - Unix 系: `~/.local/share/gistx/<user>/gistlist/`

## 5. 前提
- `setup` 実行済みで、`config.yaml` に `user` が設定されていること。
- `clone` は `gistlist/<list_count>/list.yaml` を作成し、同じ `list_count` をキーとして `fetch.yaml` を更新する。
- `fetch.yaml` の 1 エントリは次の形式を許容する。

```yaml
'1':
  - '2026-03-09 10:00:00'
  - 12
```

- `fix` はキーの整合を主目的とし、既存エントリ値の詳細は必要最小限しか変更しない。

## 6. `gistx fix` の処理仕様
`fix` は次の 2 段階を順に実行する。

1. `gistlist` トップディレクトリ配下を再帰走査し、空ディレクトリを削除する。
2. 削除後に実在する `gistlist/<number>/` ディレクトリを基準に `fetch.yaml` のエントリを補正する。

## 7. 空ディレクトリ削除仕様
### 7.1 対象
- `gistlist` トップディレクトリ自身は削除対象にしない。
- `gistlist` トップディレクトリ配下のすべての子孫ディレクトリを対象にする。

### 7.2 判定
- あるディレクトリ直下にファイルもディレクトリも存在しない場合、そのディレクトリは空とみなす。
- bottom-up で判定し、子の削除によって親が空になった場合は親も続けて削除する。

### 7.3 事後条件
- `gistlist` トップディレクトリ配下に空ディレクトリは存在しない。
- `gistlist` トップディレクトリ自体は常に残す。

## 8. `fetch.yaml` 整合調整仕様
### 8.1 基準となる `gistlist` ディレクトリ
- `gistlist` トップディレクトリ直下の子ディレクトリのうち、名前が 10 進整数文字列のものを `gistlist` ディレクトリとして扱う。
- それ以外の名前の子要素は `fetch.yaml` 整合判定の対象外とする。

### 8.2 調整ルール
- 実在する `gistlist/<number>/` に対応するキー `"<number>"` が `fetch.yaml` に存在しない場合、そのキーを追加する。
- `fetch.yaml` に存在しても、対応する `gistlist/<number>/` が存在しないキーは削除する。
- 実在する `gistlist/<number>/` と同じキーを持つ既存エントリは保持する。
- 追加するキーの値は、最低限 `clone` が生成する形式と矛盾しない値を設定する。
  - 推奨値: `[Timex.get_now(), 0]`
  - `0` は clone 対象 gist 数が不明な補完値を表す。
- `fetch.yaml` のキー集合は、調整後に実在する `gistlist/<number>/` の集合と一致しなければならない。

### 8.3 `gistlist` ディレクトリが存在しない場合
- `gistlist` トップディレクトリ直下に数値名ディレクトリが 1 件も存在しない場合、`fetch.yaml` は空のマッピングにする。
- この場合でも `fetch.yaml` 自体は存在し続けること。

## 9. 非対象
- `list.yaml` の内容は変更しない。
- `gistrepo/`, `public/`, `private/`, Git 管理下の clone 済みリポジトリ内容は変更しない。
- `config.yaml` の内容は変更しない。
- `gistlist` 直下以外のディレクトリ構造は変更しない。

## 10. 異常系
- `config.yaml` から `user` を取得できない場合は例外を送出し、処理を中止する。
- ユーザ別ワークスペースが存在しない場合は例外を送出する。
- `gistlist` トップディレクトリが存在しない場合は例外を送出する。
- `fetch.yaml` が存在しない場合は新規作成して整合済み内容を書き出す。
- `fetch.yaml` の YAML ルートがマッピングでない場合は例外を送出する。
- 空ディレクトリ削除中の `OSError` は送出元例外として伝播させる。

## 11. クラス責務
- `Clix`
  - `fix` サブコマンドを登録する。
  - `-v`, `--verbose` を受け付ける。
- `Gistx.fix(args)`
  - ログレベルを設定する。
  - `AppStore` を初期化する。
  - 設定ファイルを読み込み、`CommandFix` を生成して実行する。
- `CommandFix.run(args)`
  - 対象ユーザのワークスペースを特定する。
  - `gistlist` 配下の空ディレクトリ削除を実行する。
  - `fetch.yaml` の整合調整を実行する。
- `CommandFix._remove_empty_dirs(gistlist_top_dir)` または独立関数 `remove_empty_directories()`
  - bottom-up で空ディレクトリを削除する。
- `CommandFix._collect_existing_counts(gistlist_top_dir)` または独立関数 `collect_existing_gistlist_counts()`
  - 実在する `gistlist/<number>/` の数値一覧を返す。
- `CommandFix._reconcile_fetch_yaml(fetch_path, existing_counts)` または独立関数 `reconcile_fetch_entries()`
  - `fetch.yaml` を読み込み、キー集合を `existing_counts` に一致させて保存する。

## 12. 実行後保証
- `gistlist` トップディレクトリ配下に空ディレクトリが存在しない。
- `fetch.yaml` の数値キー集合は、`gistlist` トップディレクトリ直下の実在する数値名ディレクトリ集合と一致する。
- `setup` と `clone` が利用するパス構成は維持される。

## 13. 使用例
```bash
gistx fix
gistx fix -v
```

## 14. 関連サブコマンドとの契約
- `setup` は `<user>/fetch.yaml` と `<user>/gistlist/` を作成する。
- `clone` は `gistlist/<list_count>/list.yaml` を生成し、`fetch.yaml` の同一キーを更新する。
- `fix` は `clone` の生成物が部分的に欠落した場合でも、空ディレクトリ除去と `fetch.yaml` のキー整合だけを回復対象とする。
