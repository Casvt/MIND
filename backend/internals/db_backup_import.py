# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from os import remove
from os.path import basename, dirname, exists, join
from re import compile
from shutil import move
from sqlite3 import OperationalError
from time import time
from typing import TYPE_CHECKING, List, Union

from backend.base.custom_exceptions import (DatabaseFileNotFound,
                                            InvalidDatabaseFile)
from backend.base.definitions import Constants, DatabaseBackupEntry, StartType
from backend.base.helpers import copy, folder_path, list_files
from backend.base.logging import LOGGER
from backend.internals.db import DBConnection
from backend.internals.db_migration import get_latest_db_version
from backend.internals.db_models import ConfigDB
from backend.internals.settings import Settings

if TYPE_CHECKING:
    from threading import Timer


# region Backup
DB_FILE_REGEX = compile(
    r'MIND_(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_(?P<hour>\d{2})_(?P<minute>\d{2}).db'
)


def get_backups() -> List[DatabaseBackupEntry]:
    """Get a list of currently existing backups, as found in the backup folder.

    Returns:
        List[DatabaseBackupEntry]: The backups found.
    """
    db_files = list_files(Settings().sv.db_backup_folder, ('.db',))
    result: List[DatabaseBackupEntry] = []

    for file in db_files:
        file_match = DB_FILE_REGEX.match(basename(file))
        if file_match is None:
            continue

        time_els = file_match.groupdict()
        timestamp = datetime(
            year=int(time_els['year']),
            month=int(time_els['month']),
            day=int(time_els['day']),
            hour=int(time_els['hour']),
            minute=int(time_els['minute'])
        ).timestamp()

        result.append({
            "index": len(result),
            "creation_date": int(timestamp),
            "filepath": file,
            "filename": basename(file)
        })

    result.sort(key=lambda f: f["creation_date"], reverse=True)

    return result


def get_backup(index: int) -> DatabaseBackupEntry:
    """Get info on a specific database backup.

    Args:
        index (int): The index of the backup (supplied by `get_backups()`).

    Raises:
        DatabaseFileNotFound: No backup entry with the given index.

    Returns:
        DatabaseBackupEntry: The info on the backup entry.
    """
    for b in get_backups():
        if b['index'] == index:
            return b
    raise DatabaseFileNotFound(index)


def create_database_copy(folder: str) -> str:
    """Export the current database into a file.

    Args:
        folder (str): The folder to put the copy into.

    Returns:
        str: The complete filepath of the created file.
    """
    current_date = datetime.now().strftime(r"%Y_%m_%d_%H_%M")
    filename = join(folder, f'MIND_{current_date}.db')
    DBConnection().create_backup(filename)
    return filename


def backup_database() -> None:
    """
    Create a backup of the database, delete old backups that
    surpass the backup limit and set timer for next run.
    """
    settings = Settings()
    sv = settings.get_settings()
    current_backups = get_backups()

    while len(current_backups) >= sv.db_backup_amount:
        removed_backup = current_backups.pop()["filepath"]
        remove(removed_backup)
        LOGGER.info(f"Removed database backup: {removed_backup}")

    filepath = create_database_copy(sv.db_backup_folder)
    LOGGER.info(f"Created database backup: {filepath}")

    settings.update({"db_backup_last_run": int(time())})

    DatabaseBackupHandler().set_backup_timer()

    return


class DatabaseBackupHandler:
    backup_timer: Union[Timer, None] = None

    def set_backup_timer(self) -> None:
        """Update the timer for the backup process. Start one if it hasn't
        already. Replace it if it does already exist, in case the interval
        setting has a new value.
        """
        from backend.internals.server import Server

        sv = Settings().get_settings()

        if self.__class__.backup_timer is not None:
            self.__class__.backup_timer.cancel()

        self.__class__.backup_timer = Server().get_db_timer_thread(
            sv.db_backup_last_run + sv.db_backup_interval - time(),
            backup_database,
            "DatabaseBackupHandler"
        )
        self.__class__.backup_timer.start()
        return

    def stop_backup_timer(self) -> None:
        "If the backup timer is running, stop it"
        if self.__class__.backup_timer is not None:
            self.__class__.backup_timer.cancel()
        return


# region Import
def revert_db_import(
    swap: bool,
    other_db_file: str = ''
) -> None:
    """Revert the database import process.

    Args:
        swap (bool): Keep the other database file instead of the current
            database file.

        other_db_file (str, optional): The other database file. Keep empty to
            use `Constants.DB_ORIGINAL_FILENAME`.
            Defaults to ''.

    Raises:
        InvalidDatabaseFile: The other database file does not exist.
    """
    original_db_file = DBConnection.default_file
    if not other_db_file:
        other_db_file = join(
            dirname(DBConnection.default_file),
            Constants.DB_ORIGINAL_NAME
        )

    if not exists(other_db_file):
        raise InvalidDatabaseFile(
            other_db_file,
            "Database file does not exist"
        )

    if swap:
        remove(original_db_file)
        move(
            other_db_file,
            original_db_file
        )

    else:
        remove(other_db_file)

    return


def import_db(
    new_db_file: str,
    copy_hosting_settings: bool
) -> None:
    """Replace the current database with a new one.

    Args:
        new_db_file (str): The path to the new database file.
        copy_hosting_settings (bool): Keep the hosting settings from the current
            database.

    Raises:
        InvalidDatabaseFile: The new database file is invalid or unsupported.
    """
    from backend.internals.server import Server

    LOGGER.info(f"Importing new database; {copy_hosting_settings=}")

    cursor_new = DBConnection(db_file=new_db_file).cursor()
    config_current = ConfigDB()
    config_new = ConfigDB(cursor_new)

    try:
        try:
            database_version = config_new.fetch_key("database_version")
            if not isinstance(database_version, int):
                raise OperationalError
        except OperationalError:
            raise InvalidDatabaseFile(
                new_db_file,
                "Uploaded database is not a MIND database file"
            )

        if database_version > get_latest_db_version():
            raise InvalidDatabaseFile(
                new_db_file,
                "Uploaded database is higher version than this MIND installation can support")

    except InvalidDatabaseFile:
        cursor_new.connection.close()
        revert_db_import(
            swap=False,
            other_db_file=new_db_file
        )
        raise

    if copy_hosting_settings:
        hosting_settings = config_current.fetch_all()
        for key, value in hosting_settings:
            if key in ('host', 'port', 'url_prefix'):
                config_new.update(key, value)

    cursor_new.connection.commit()
    cursor_new.connection.close()

    move(
        DBConnection.default_file,
        join(dirname(DBConnection.default_file), Constants.DB_ORIGINAL_NAME)
    )
    move(
        new_db_file,
        DBConnection.default_file
    )

    Server().restart(StartType.RESTART_DB_CHANGES)

    return


def import_db_backup(
    index: int,
    copy_hosting_settings: bool
) -> None:
    """Replace the current database with a backup.

    Args:
        index (int): The index of the backup (supplied by `get_backups()`).
        copy_hosting_settings (bool): Keep the hosting settings from the current
            database.

    Raises:
        DatabaseFileNotFound: No backup entry with the given index.
        InvalidDatabaseFile: The new database file is invalid or unsupported.
    """
    LOGGER.info(f"Importing database backup with index {index}")

    backup = get_backup(index)
    dest = copy(
        backup["filepath"],
        folder_path("db", "MIND_upload.db")
    )

    import_db(dest, copy_hosting_settings)
    return
