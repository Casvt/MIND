# -*- coding: utf-8 -*-

from dataclasses import _MISSING_TYPE, asdict, dataclass
from functools import lru_cache
from logging import DEBUG, INFO
from os import sep
from os.path import abspath, isdir
from typing import Any, Dict, Mapping

from backend.base.custom_exceptions import InvalidKeyValue, KeyNotFound
from backend.base.definitions import Constants, Interval
from backend.base.helpers import (Singleton, folder_path, get_python_version,
                                  get_version_from_pyproject)
from backend.base.logging import LOGGER, set_log_level
from backend.internals.db import DBConnection, commit
from backend.internals.db_migration import get_latest_db_version
from backend.internals.db_models import ConfigDB


@lru_cache(1)
def get_about_data() -> Dict[str, Any]:
    """Get data about the application and it's environment.

    Raises:
        RuntimeError: Application version not found in pyproject file.

    Returns:
        Dict[str, Any]: The information.
    """
    return {
        "version": get_version_from_pyproject(folder_path("pyproject.toml")),
        "python_version": get_python_version(),
        "database_version": get_latest_db_version(),
        "database_location": DBConnection.default_file,
        "data_folder": folder_path()
    }


@dataclass(frozen=True)
class PublicSettingsValues:
    log_level: int = INFO

    host: str = '0.0.0.0'
    port: int = 8080
    url_prefix: str = ''

    allow_new_accounts: bool = True
    login_time: int = Interval.ONE_HOUR.value
    login_time_reset: bool = True

    db_backup_interval: int = Interval.ONE_DAY.value
    db_backup_amount: int = 3
    db_backup_folder: str = folder_path(*Constants.DB_FOLDER)
    db_backup_last_run: int = 0

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SettingsValues(PublicSettingsValues):
    database_version: int = get_latest_db_version()

    backup_host: str = '0.0.0.0'
    backup_port: int = 8080
    backup_url_prefix: str = ''

    measured_timezone: int = -1 # = no value


class Settings(metaclass=Singleton):
    def __init__(self) -> None:
        self._insert_missing_settings()
        return

    def _insert_missing_settings(self) -> None:
        """Insert any missing keys from the settings into the database"""
        config_db = ConfigDB()
        for key, value in asdict(SettingsValues()).items():
            config_db.insert(key, value)
        commit()
        return

    @lru_cache(1)
    def get_settings(self) -> SettingsValues:
        """Get the settings, including internal ones.

        Returns:
            SettingsValues: The settings.
        """
        db_values = {
            k: v
            for k, v in ConfigDB().fetch_all()
            if k in SettingsValues.__dataclass_fields__
        }

        bool_fields = (
            field.name
            for field in SettingsValues.__dataclass_fields__.values()
            if field.type is bool
        )

        for b_key in bool_fields:
            db_values[b_key] = bool(db_values[b_key])

        return SettingsValues(**db_values)

    @lru_cache(1)
    def get_public_settings(self) -> PublicSettingsValues:
        """Get the public settings, so excluding internal ones.

        Returns:
            PublicSettingsValues: The public settings.
        """
        return PublicSettingsValues(
            **{
                k: v
                for k, v in self.get_settings().todict().items()
                if k in PublicSettingsValues.__dataclass_fields__
            }
        )

    def clear_cache(self) -> None:
        """Clear the cache of the settings"""
        self.get_settings.cache_clear()
        self.get_public_settings.cache_clear()
        return

    # Alias, better in one-liners
    # sv = Settings Values
    @property
    def sv(self) -> SettingsValues:
        """Get the settings, including internal ones.

        Returns:
            SettingsValues: The settings.
        """
        return self.get_settings()

    def update(
        self,
        data: Mapping[str, Any],
        from_public: bool = False
    ) -> None:
        """Change the settings, in a `dict.update()` type of way.

        Args:
            data (Mapping[str, Any]): The keys and their new values.

            from_public (bool, optional): If True, only allow public settings to
                be changed.
                Defaults to False.

        Raises:
            KeyNotFound: Key is not a setting.
            InvalidKeyValue: Value of the key is not allowed.
        """
        formatted_data = {}
        for key, value in data.items():
            formatted_data[key] = self.__format_setting(key, value, from_public)

        config_db = ConfigDB()
        for key, value in formatted_data.items():
            config_db.update(key, value)

        old_settings = self.get_settings()
        if (
            'log_level' in data
            and formatted_data['log_level'] != old_settings.log_level
        ):
            set_log_level(formatted_data['log_level'])

        if (
            'db_backup_interval' in data
            and formatted_data['db_backup_interval'] != old_settings.db_backup_interval
        ):
            from backend.internals.db_backup_import import \
                DatabaseBackupHandler

            DatabaseBackupHandler().set_backup_timer()

        self.clear_cache()

        LOGGER.info(f"Settings changed: {formatted_data}")

        return

    def get_default_value(self, key: str) -> Any:
        """Get the default value of a setting.

        Args:
            key (str): The key of the setting.

        Returns:
            Any: The default value.
        """
        if not isinstance(
            SettingsValues.__dataclass_fields__[key].default_factory,
            _MISSING_TYPE
        ):
            return SettingsValues.__dataclass_fields__[key].default_factory()

        else:
            return SettingsValues.__dataclass_fields__[key].default

    def reset(self, key: str, from_public: bool) -> None:
        """Reset the value of the key to the default value.

        Args:
            key (str): The key of which to reset the value.
            from_public (bool): If True, only allow public settings to
                be reset.

        Raises:
            KeyNotFound: Key is not a setting.
        """
        LOGGER.debug(f'Setting reset: {key}')

        self.update({key: self.get_default_value(key)}, from_public=from_public)

        return

    def backup_hosting_settings(self) -> None:
        """Backup the hosting settings in the database"""
        s = self.get_settings()
        backup_settings = {
            'backup_host': s.host,
            'backup_port': s.port,
            'backup_url_prefix': s.url_prefix
        }
        self.update(backup_settings)
        return

    def __format_setting(self, key: str, value: Any, from_public: bool) -> Any:
        """Check if the value of a setting is allowed and convert if needed.

        Args:
            key (str): Key of setting.
            value (Any): Value of setting.
            from_public (bool): If True, only allow public settings
                to be changed.

        Raises:
            KeyNotFound: Key is not a setting.
            InvalidKeyValue: Value is not allowed.

        Returns:
            Any: (Converted) Setting value.
        """
        converted_value = value

        KeyCollection = PublicSettingsValues if from_public else SettingsValues

        if key not in KeyCollection.__dataclass_fields__:
            raise KeyNotFound(key)

        key_data = KeyCollection.__dataclass_fields__[key]

        if not isinstance(value, key_data.type):
            raise InvalidKeyValue(key, value)

        if key == 'login_time':
            if not (
                Interval.ONE_MINUTE.value
                <= value
                <= Interval.THIRTY_DAYS.value
            ):
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

        elif key == 'db_backup_interval':
            if value < Interval.ONE_HOUR.value:
                raise InvalidKeyValue(key, value)

        elif key == 'db_backup_amount':
            if value <= 0:
                raise InvalidKeyValue(key, value)

        elif key == 'db_backup_folder':
            converted_value = abspath(value.rstrip(sep))
            if not isdir(converted_value):
                raise InvalidKeyValue(key, value)

        elif key == 'db_backup_last_run':
            if value < 0:
                raise InvalidKeyValue(key, value)

        return converted_value
