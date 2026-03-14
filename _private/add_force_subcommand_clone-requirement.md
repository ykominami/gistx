クラスCommandCloneおよび関連したクラス、関数に対し、以下の要望を満たすように追加、修正した、クラス定義と(必要であれば)クラスとは独立した関数の外部仕様書(_private/add_force_subcommand_clone-spec.md)を作成して。
# 用語の定義
- ユーザ
gh auth login　で認証されたGitHubのアカウント
指定されGitHubアカウントのアカウント名と同一のユーザ名を持つ
- ユーザディレクトリ
ディレクトリ名はユーザ名
以下の位置に存在する
　AppData\Local\gistx\ユーザ名

この下にfetchファイル、gistlistトップディレクトリが存在する
gistlistトップディレクトリは1個のみ存在する。
以下の位置に存在する
　AppData\Local\gistx\ユーザ名\fetch.yaml
　AppData\Local\gistx\ユーザ名\gistlist

- fetchファイル
ファイル名は"fetch.yaml"
gh gist list を実行した回数とcloneしたgistの個数を記録するYAML形式ファイル
gh gist list の実行が成功した後に更新される。
1回のgh gist listですべてのgistの一覧を取得できるように、十分大きな最大個数を指定して実行する。

フォーマットは、以下の通り
　回数: 
　- 実行時のタイムスタンプ
  - clonesしたgistの個数

- gistlistトップディレクトリ
ディレクトリ名は"gistlist"
この下にgistlistディレクトリが存在する。
gistlistトップディレクトリは複数個存在してもよい。


- gistlistディレクトリ
ディレクトリ名はgh gist listを実行した回数
gh repo listの出力を格納するlist.yamlとgistrepoトップディレクトリをもつ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>

- gistrepoトップディレクトリ
ディレクトリ名は"gistrepo"
gh repo cloneの出力を格納するdb.yamlをもつ。
またgitrepoディレクトリも持つ。
gitrepoディレクトリは複数個存在する場合もある。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo

- gistrepoディレクトリ
ディレクトリ名はサブコマンドcloneを実行して、ghコマンドを用いて、指定個数分のgistのリポジトリをcloneしようとした回数

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>

- publicトップディレクトリ
ディレクトリ名は"public"
publicなgistのclone先ディレクトリを持つ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\public

- 個別publicなgistディレクトリ
ディレクトリ名はgistの名称
gistの名称は、gh gist listで取得する。
publicなgistのclone先ディレクトリ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\publc\<gistの名称>

- privateトップディレクトリ
ディレクトリ名は"private"
privateなgistのclone先ディレクトリを持つ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\private

- 個別privateなgistディレクトリ
ディレクトリ名はgistの名称
gistの名称は、gh gist listで取得する。
privatecなgistのclone先ディレクトリ。

以下の位置に存在する
　AppData\Local\gistx\ユーザ名\gistlist\<gh gist listを実行した回数>\gistrepo\<cloneしようとした回数>\private\<gistの名称>

1.コマンドラインのサブコマンドcloneを設ける。
1.1 gh glist listでユーザの持つすべてのgistの一覧を取得する。
1.2 指定個数分のgistをgistに対応するrepositoryからcloneする。

1.コマンドラインのサブコマンドcloneに、--forceオプション（短縮形-f）を追加する。--forceオプションが指定された場合、およびfetchファイルが存在しないときのみ、gh repo cloneを実行し、するようにする。

2.コマンドラインのサブコマンドcloneに、--verboseオプション（短縮形-v）を追加する。--verboseオプションが指定された場合、ログレベルをlogging.DEBUGに、指定されなけばlogging.INFOに設定する。

3.コマンドラインのサブコマンドcloneに、--publicオプションと--privateオプションと--allオプションを追加する。
これら３つはどれか一つしか指定できない。
--publicオプションを指定した場合は、publicなgistのみをcloneする。
--privateオプションを指定した場合は、privateなgistのみをcloneする。
--allオプションを指定した場合は、publicなgistと、privateなgistの両方をcloneする。

4.コマンドラインのサブコマンドcloneに、--max_gistsオプションを追加する。
--max_gistsオプションは1個の数値引数を取り、指定された引数をgistをcloneする最大個数とする。
--max_gistsオプションが指定されない場合は、すべてのgistをcloneする。

