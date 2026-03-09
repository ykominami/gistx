from copy import deepcopy

from yklibpy.config.appconfig import AppConfig


class AppConfigx(AppConfig):
    file_type_dict = {**AppConfig.file_type_dict, AppConfig.FILE_TYPE_YAML: ".yaml"}
    file_type_reverse_dict = {ext_name: file_type for file_type, ext_name in file_type_dict.items()}
    file_synonym_dict = {
        **AppConfig.file_synonym_dict,
        ".yml": ".yaml",
    }
    file_assoc = deepcopy(AppConfig.file_assoc)
    directory_assoc = deepcopy(AppConfig.directory_assoc)

    BASE_NAME_FETCH = AppConfig.BASE_NAME_FETCH
    BASE_NAME_LIST = "list"
    BASE_NAME_GIST = "gist"
    BASE_NAME_GISTLIST_TOP = "gistlist"
    BASE_NAME_PROGRESS = "progress"
    BASE_NAME_GISTREPO_DB = "db"
    BASE_NAME_REPO = "repo"

    file_assoc[AppConfig.KIND_DB][BASE_NAME_LIST] = {
        AppConfig.FILE_TYPE: AppConfig.FILE_TYPE_YAML,
        AppConfig.EXT_NAME: "",
        AppConfig.PATH: {},
        AppConfig.VALUE: {},
    }
    directory_assoc[AppConfig.KIND_DB][BASE_NAME_GISTLIST_TOP] = {
        AppConfig.PATH: {},
    }
    directory_assoc[AppConfig.KIND_DB][BASE_NAME_REPO] = {
        AppConfig.PATH: {},
    }

    KEY_USER = "user"
    KEY_URL_API = "url_api"
    KEY_GISTS = "gists"
    DEFAULT_VALUE_URL_API = "https://api.github.com"
    DEFAULT_VALUE_GISTS = "gists"
