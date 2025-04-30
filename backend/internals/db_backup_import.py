# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from os import remove
from os.path import basename, dirname, join
from re import compile
from shutil import move
from sqlite3 import Connection, OperationalError
from time import time
from typing import TYPE_CHECKING, List, Union

from backend.base.custom_exceptions import (DatabaseFileNotFound,
                                            InvalidDatabaseFile)
from backend.base.definitions import Constants, DatabaseBackupEntry, StartType
from backend.base.helpers import Singleton, copy, folder_path, list_files
from backend.base.logging import LOGGER
from backend.internals.db import DBConnection, get_db
from backend.internals.db_migration import get_latest_db_version
from backend.internals.settings import Settings

if TYPE_CHECKING:
    from threading import Timer

# ===================
# region Backup
# ===================
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
        index (int): The index (supplied by `get_backups()`) of the backup.

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
    get_db().execute(
        "VACUUM INTO ?;",
        (filename,)
    )
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


class DatabaseBackupHandler(metaclass=Singleton):
    backup_timer: Union[Timer, None] = None

    def set_backup_timer(self) -> None:
        """Update the timer for the backup process. Start one if it hasn't
        already. Replace it if it does already exist, in case the interval
        setting has a new value.
        """
        sv = Settings().get_settings()

        if self.backup_timer is not None:
            self.backup_timer.cancel()

        from backend.internals.server import Server
        self.backup_timer = Server().get_db_timer_thread(
            sv.db_backup_last_run + sv.db_backup_interval - time(),
            backup_database
        )
        self.backup_timer.start()
        return

    def stop_backup_timer(self) -> None:
        "If the backup timer is running, stop it"
        if self.backup_timer is not None:
            self.backup_timer.cancel()
        return


# ===================
# region Import
# ===================
def revert_db_import(
    swap: bool,
    imported_db_file: str = ''
) -> None:
    """Revert the database import process. The original_db_file is the file
    currently used (`DBConnection.file`).

    Args:
        swap (bool): Whether or not to keep the imported_db_file or not,
        instead of the original_db_file.

        imported_db_file (str, optional): The other database file. Keep empty
        to use `Constants.DB_ORIGINAL_FILENAME`.
            Defaults to ''.
    """
    original_db_file = DBConnection.file
    if not imported_db_file:
        imported_db_file = join(
            dirname(DBConnection.file),
            Constants.DB_ORIGINAL_NAME
        )

    if swap:
        remove(original_db_file)
        move(
            imported_db_file,
            original_db_file
        )

    else:
        remove(imported_db_file)

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
    LOGGER.info(f'Importing new database; {copy_hosting_settings=}')

    cursor = Connection(new_db_file, timeout=20.0).cursor()
    try:
        database_version = cursor.execute(
            "SELECT value FROM config WHERE key = 'database_version' LIMIT 1;"
        ).fetchone()[0]
        if not isinstance(database_version, int):
            raise InvalidDatabaseFile(new_db_file)

    except (OperationalError, InvalidDatabaseFile):
        LOGGER.error('Uploaded database is not a MIND database file')
        cursor.connection.close()
        revert_db_import(
            swap=False,
            imported_db_file=new_db_file
        )
        raise InvalidDatabaseFile(new_db_file)

    if database_version > get_latest_db_version():
        LOGGER.error(
            'Uploaded database is higher version than this MIND installation can support')
        revert_db_import(
            swap=False,
            imported_db_file=new_db_file
        )
        raise InvalidDatabaseFile(new_db_file)

    if copy_hosting_settings:
        hosting_settings = get_db().execute("""
			SELECT key, value
			FROM config
			WHERE key = 'host'
				OR key = 'port'
				OR key = 'url_prefix'
			LIMIT 3;
			"""
        ).fetchalldict()
        cursor.executemany("""
			INSERT INTO config(key, value)
			VALUES (:key, :value)
			ON CONFLICT(key) DO
			UPDATE
			SET value = :value;
			""",
            hosting_settings
        )
    cursor.connection.commit()
    cursor.connection.close()

    move(
        DBConnection.file,
        join(dirname(DBConnection.file), Constants.DB_ORIGINAL_NAME)
    )
    move(
        new_db_file,
        DBConnection.file
    )

    from backend.internals.server import Server
    Server().restart(StartType.RESTART_DB_CHANGES)

    return


def import_db_backup(
    index: int,
    copy_hosting_settings: bool
) -> None:
    """Replace the current database with a backup.

    Args:
        index (int): The index (supplied by `get_backups()`) of the backup.
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
