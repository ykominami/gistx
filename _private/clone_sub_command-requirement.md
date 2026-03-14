クラスCommandListおよび関連したクラス、関数に対し、以下の要望を満たすように変更した、クラス定義と(必要であれば)クラスとは独立した関数の外部仕様書(_private/add_force_sub_command_list-spec.md)を作成して。
1.コマンドラインのサブコマンドlistに、--forceオプション（短縮形-f）を追加する。--forceオプションが指定された場合、およびfetchファイルが存在しないときのみ、gh repo listを実行するようにする。
2.コマンドラインのサブコマンドlistに、--verboseオプション（短縮形-v）を追加する。--verboseオプションが指定された場合、ログレベルをLogging.DEBUGに設定する。指定されない場合は、Logging.INFOに設定する。
3.コマンドラインのサブコマンドlistに、--オプション（短縮形-v）を追加する。--verboseオプションが指定された場合、ログレベルをLogging.DEBUGに設定する。指定されない場合は、Logging.INFOに設定する。

3. クラスCommandListのメソッドget_command_for_projectをメソッドget_command_for_repositoryに変更し、変更前のメソッド名で呼び出している個所すべてにおいて、変更後のメソッド名で正しく呼び出せるように修正する。