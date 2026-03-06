# from ghprj.command import Command
from yklibpy.command.command import Command
from yklibpy.command.command_gh_user import CommandGhUser
from yklibpy.common.util import Util
from yklibpy.db.appstore import AppStore
from gistx.appconfigx import AppConfigx

class CommandSetup(Command):
  def __init__(self, appstore: AppStore):
    self.appstore = appstore

  def run(self) -> None:
    user = CommandGhUser().run()
    if Util.is_empty(user):
      user = AppConfigx.DEFAULT_VALUE_USER
    print(f"user={user}")
    data = {
      AppConfigx.KEY_USER: user,
      AppConfigx.KEY_URL_API: AppConfigx.DEFAULT_VALUE_URL_API,
      AppConfigx.KEY_GISTS: AppConfigx.DEFAULT_VALUE_GISTS,
    }

    self.appstore.output_config(AppConfigx.KIND_CONFIG, data)
    self.appstore.output_db(AppConfigx.BASE_NAME_DB, {})
    self.appstore.output_db(AppConfigx.BASE_NAME_FETCH, {})
    self.appstore.output_db(AppConfigx.BASE_NAME_LIST, {})
    self.appstore.mkdir_db(AppConfigx.BASE_NAME_REPO)
