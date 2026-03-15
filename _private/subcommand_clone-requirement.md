クラスCommandCloneおよび関連したクラス、関数に対し、以下の要望を満たすように追加、修正した、クラス定義と(必要であれば)クラスとは独立した関数の外部仕様書(_private/subcommand_clone-spec.md)を作成して。

1.1 gh glist cloneでユーザの持つすべてのgistの一覧を取得する。
1.2 指定個数分のgistをgistに対応するrepositoryからcloneする。

2.コマンドラインのサブコマンドcloneに、--forceオプション（短縮形-f）を設ける。--forceオプションが指定された場合、およびfetchファイルが存在しないときのみ、gh repo cloneを実行し、するようにする。

3.コマンドラインのサブコマンドcloneに、--verboseオプション（短縮形-v）を設ける。--verboseオプションが指定された場合、ログレベルをlogging.DEBUGに、指定されなけばlogging.INFOに設定する。

4.コマンドラインのサブコマンドcloneに、--publicオプションと--privateオプションと--allオプションを設ける。
これら３つはどれか一つしか指定できない。
--publicオプションを指定した場合は、publicなgistのみをcloneする。
--privateオプションを指定した場合は、privateなgistのみをcloneする。
--allオプションを指定した場合は、publicなgistと、privateなgistの両方をcloneする。

5.コマンドラインのサブコマンドcloneに、--max_gistsオプションを設ける。
--max_gistsオプションは1個の数値引数を取り、指定された引数をgistをcloneする最大個数とする。
--max_gistsオプションが指定されない場合は、すべてのgistをcloneする。

