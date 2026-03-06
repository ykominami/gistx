from yklibpy.config.appconfig import AppConfig

class AppConfigx(AppConfig):
    BASE_NAME_LIST = "list"
    BASE_NAME_REPO = "repo"

    AppConfig.file_assoc[AppConfig.KIND_DB][BASE_NAME_LIST] = {
        AppConfig.FILE_TYPE: AppConfig.FILE_TYPE_YAML,
        AppConfig.EXT_NAME: "",
        AppConfig.PATH: {},
        AppConfig.VALUE: {},
    }
    AppConfig.directory_assoc[AppConfig.KIND_DB][BASE_NAME_REPO] = {
        AppConfig.PATH: {},
    }
    KEY_USER = "user"
    KEY_URL_API = "url_api"
    KEY_GISTS = "gists"
    DEFAULT_VALUE_URL_API = "https://api.github.com"
    DEFAULT_VALUE_GISTS = "gists"
    DEFAULT_VALUE_USER = None