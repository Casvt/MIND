# -*- coding: utf-8 -*-

from dataclasses import _MISSING_TYPE, asdict, dataclass
from functools import lru_cache
from json import dump, load
from logging import DEBUG, INFO
from typing import Any, Dict, Mapping

from backend.base.custom_exceptions import InvalidKeyValue, KeyNotFound
from backend.base.helpers import (Singleton, folder_path,
                                  get_python_version, reversed_tuples)
from backend.base.logging import LOGGER, set_log_level
from backend.internals.db import DBConnection, commit, get_db
from backend.internals.db_migration import get_latest_db_version

THIRTY_DAYS = 2592000


@lru_cache(1)
def get_about_data() -> Dict[str, Any]:
    """Get data about the application and it's environment.

    Raises:
        RuntimeError: If the version is not found in the pyproject.toml file.

    Returns:
        Dict[str, Any]: The information.
    """
    with open(folder_path("pyproject.toml"), "r") as f:
        for line in f:
            if line.startswith("version = "):
                version = "V" + line.split('"')[1]
                break
        else:
            raise RuntimeError("Version not found in pyproject.toml")

    return {
        "version": version,
        "python_version": get_python_version(),
        "database_version": get_latest_db_version(),
        "database_location": DBConnection.file,
        "data_folder": folder_path()
    }


@dataclass(frozen=True)
class SettingsValues:
    database_version: int = get_latest_db_version()
    log_level: int = INFO

    host: str = '0.0.0.0'
    port: int = 8080
    url_prefix: str = ''
    backup_host: str = '0.0.0.0'
    backup_port: int = 8080
    backup_url_prefix: str = ''

    allow_new_accounts: bool = True
    login_time: int = 3600
    login_time_reset: bool = True

    def todict(self) -> Dict[str, Any]:
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith('backup_')
        }


class Settings(metaclass=Singleton):
    def __init__(self) -> None:
        self._insert_missing_settings()
        self._fetch_settings()
        return

    def _insert_missing_settings(self) -> None:
        "Insert any missing keys from the settings into the database."
        get_db().executemany(
            "INSERT OR IGNORE INTO config(key, value) VALUES (?, ?);",
            asdict(SettingsValues()).items()
        )
        commit()
        return

    def _fetch_settings(self) -> None:
        "Load the settings from the database into the cache."
        db_values = {
            k: v
            for k, v in get_db().execute(
                "SELECT key, value FROM config;"
            )
            if k in SettingsValues.__dataclass_fields__
        }

        for b_key in ('allow_new_accounts', 'login_time_reset'):
            db_values[b_key] = bool(db_values[b_key])

        self.__cached_values = SettingsValues(**db_values)
        return

    def get_settings(self) -> SettingsValues:
        """Get the settings from the cache.

        Returns:
            SettingsValues: The settings.
        """
        return self.__cached_values

    # Alias, better in one-liners
    # sv = Settings Values
    @property
    def sv(self) -> SettingsValues:
        """Get the settings from the cache.

        Returns:
            SettingsValues: The settings.
        """
        return self.__cached_values

    def update(
        self,
        data: Mapping[str, Any]
    ) -> None:
        """Change the settings, in a `dict.update()` type of way.

        Args:
            data (Mapping[str, Any]): The keys and their new values.

        Raises:
            KeyNotFound: Key is not a setting.
            InvalidKeyValue: Value of the key is not allowed.
        """
        formatted_data = {}
        for key, value in data.items():
            formatted_data[key] = self.__format_setting(key, value)

        get_db().executemany(
            "UPDATE config SET value = ? WHERE key = ?;",
            reversed_tuples(formatted_data.items())
        )

        if (
            'log_level' in data
            and formatted_data['log_level'] != getattr(
                self.get_settings(), 'log_level'
            )
        ):
            set_log_level(formatted_data['log_level'])

        self._fetch_settings()

        LOGGER.info(f"Settings changed: {formatted_data}")

        return

    def reset(self, key: str) -> None:
        """Reset the value of the key to the default value.

        Args:
            key (str): The key of which to reset the value.

        Raises:
            KeyNotFound: Key is not a setting.
        """
        LOGGER.debug(f'Setting reset: {key}')

        if not isinstance(
            SettingsValues.__dataclass_fields__[key].default_factory,
            _MISSING_TYPE
        ):
            self.update({
                key: SettingsValues.__dataclass_fields__[key].default_factory()
            })
        else:
            self.update({
                key: SettingsValues.__dataclass_fields__[key].default
            })

        return

    def backup_hosting_settings(self) -> None:
        "Backup the hosting settings in the database."
        s = self.get_settings()
        backup_settings = {
            'backup_host': s.host,
            'backup_port': s.port,
            'backup_url_prefix': s.url_prefix
        }
        self.update(backup_settings)
        return

    def __format_setting(self, key: str, value: Any) -> Any:
        """Check if the value of a setting is allowed and convert if needed.

        Args:
            key (str): Key of setting.
            value (Any): Value of setting.

        Raises:
            KeyNotFound: Key is not a setting.
            InvalidKeyValue: Value is not allowed.

        Returns:
            Any: (Converted) Setting value.
        """
        converted_value = value

        if key not in SettingsValues.__dataclass_fields__:
            raise KeyNotFound(key)

        key_data = SettingsValues.__dataclass_fields__[key]

        if not isinstance(value, key_data.type):
            raise InvalidKeyValue(key, value)

        if key == 'login_time':
            if not 60 <= value <= THIRTY_DAYS:
                raise InvalidKeyValue(key, value)

        elif key in ('port', 'backup_port'):
            if not 1 <= value <= 65535:
                raise InvalidKeyValue(key, value)

        elif key in ('url_prefix', 'backup_url_prefix'):
            if value:
                converted_value = ('/' + value.lstrip('/')).rstrip('/')

        elif key == 'log_level':
            if value not in (INFO, DEBUG):
                raise InvalidKeyValue(key, value)

        return converted_value
