# -*- coding: utf-8 -*-

"""
Setting up the database and handling connections
"""

from __future__ import annotations

from os import remove
from os.path import dirname, exists, isdir, isfile, join
from shutil import move
from sqlite3 import (PARSE_DECLTYPES, Connection, Cursor,
                     OperationalError, ProgrammingError, Row,
                     register_adapter, register_converter)
from threading import current_thread
from typing import Any, Dict, Generator, Iterable, List, Type, Union

from flask import g

from backend.base.custom_exceptions import InvalidDatabaseFile
from backend.base.definitions import Constants, ReminderType, StartType, T
from backend.base.helpers import create_folder, folder_path, rename_file
from backend.base.logging import LOGGER, set_log_level
from backend.internals.db_migration import get_latest_db_version, migrate_db

REMINDER_TO_KEY = {
    ReminderType.REMINDER: "reminder_id",
    ReminderType.STATIC_REMINDER: "static_reminder_id",
    ReminderType.TEMPLATE: "template_id"
}


class MindCursor(Cursor):

    row_factory: Union[Type[Row], None] # type: ignore

    @property
    def lastrowid(self) -> int:
        return super().lastrowid or 1

    def fetchonedict(self) -> Union[Dict[str, Any], None]:
        """Same as `fetchone` but convert the Row object to a dict.

        Returns:
            Union[Dict[str, Any], None]: The dict or None i.c.o. no result.
        """
        r = self.fetchone()
        if r is None:
            return r
        return dict(r)

    def fetchmanydict(self, size: Union[int, None] = 1) -> List[Dict[str, Any]]:
        """Same as `fetchmany` but convert the Row object to a dict.

        Args:
            size (Union[int, None], optional): The amount of rows to return.
                Defaults to 1.

        Returns:
            List[Dict[str, Any]]: The rows.
        """
        return [dict(e) for e in self.fetchmany(size)]

    def fetchalldict(self) -> List[Dict[str, Any]]:
        """Same as `fetchall` but convert the Row object to a dict.

        Returns:
            List[Dict[str, Any]]: The results.
        """
        return [dict(e) for e in self]

    def exists(self) -> Union[Any, None]:
        """Return the first column of the first row, or `None` if not found.

        Returns:
            Union[Any, None]: The value of the first column of the first row,
            or `None` if not found.
        """
        r = self.fetchone()
        if r is None:
            return r
        return r[0]


class DBConnectionManager(type):
    instances: Dict[int, DBConnection] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> DBConnection:
        thread_id = current_thread().native_id or -1

        if (
            not thread_id in cls.instances
            or cls.instances[thread_id].closed
        ):
            cls.instances[thread_id] = super().__call__(*args, **kwargs)

        return cls.instances[thread_id]


class DBConnection(Connection, metaclass=DBConnectionManager):
    file = ''

    def __init__(self, timeout: float) -> None:
        """Create a connection with a database.

        Args:
            timeout (float): How long to wait before giving up on a command.
        """
        LOGGER.debug(f'Creating connection {self}')
        super().__init__(
            self.file,
            timeout=timeout,
            detect_types=PARSE_DECLTYPES
        )
        super().cursor().execute("PRAGMA foreign_keys = ON;")
        self.closed = False
        return

    def cursor( # type: ignore
        self,
        force_new: bool = False
    ) -> MindCursor:
        """Get a database cursor from the connection.

        Args:
            force_new (bool, optional): Get a new cursor instead of the cached
            one.
                Defaults to False.

        Returns:
            MindCursor: The database cursor.
        """
        if not hasattr(g, 'cursors'):
            g.cursors = []

        if not g.cursors:
            c = MindCursor(self)
            c.row_factory = Row
            g.cursors.append(c)

        if not force_new:
            return g.cursors[0]
        else:
            c = MindCursor(self)
            c.row_factory = Row
            g.cursors.append(c)
            return g.cursors[-1]

    def close(self) -> None:
        """Close the database connection"""
        LOGGER.debug(f'Closing connection {self}')
        self.closed = True
        super().close()
        return

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}; {current_thread().name}; {id(self)}>'


def set_db_location(
    db_folder: Union[str, None]
) -> None:
    """Setup database location. Create folder for database and set location for
    `db.DBConnection`.

    Args:
        db_folder (Union[str, None], optional): The folder in which the database
        will be stored or in which a database is for MIND to use. Give
        `None` for the default location.

    Raises:
        ValueError: Value of `db_folder` exists but is not a folder.
    """
    if db_folder:
        if exists(db_folder) and not isdir(db_folder):
            raise ValueError('Database location is not a folder')

    db_file_location = join(
        db_folder or folder_path(*Constants.DB_FOLDER),
        Constants.DB_NAME
    )

    LOGGER.debug(f'Setting database location: {db_file_location}')

    create_folder(dirname(db_file_location))

    if isfile(folder_path('db', 'Noted.db')):
        rename_file(
            folder_path('db', 'Noted.db'),
            db_file_location
        )

    DBConnection.file = db_file_location

    return


def get_db(force_new: bool = False) -> MindCursor:
    """Get a database cursor instance or create a new one if needed.

    Args:
        force_new (bool, optional): Decides if a new cursor is
        returned instead of the standard one.
            Defaults to False.

    Returns:
        MindCursor: Database cursor instance that outputs Row objects.
    """
    cursor = (
        DBConnection(timeout=Constants.DB_TIMEOUT)
        .cursor(force_new=force_new)
    )
    return cursor


def commit() -> None:
    """Commit the database"""
    get_db().connection.commit()
    return


def iter_commit(iterable: Iterable[T]) -> Generator[T, Any, Any]:
    """Commit the database after each iteration. Also commits just before the
    first iteration starts.

    Args:
        iterable (Iterable[T]): Iterable that will be iterated over like normal.

    Yields:
        Generator[T, Any, Any]: Items of iterable.
    """
    commit = get_db().connection.commit
    commit()
    for i in iterable:
        yield i
        commit()
    return


def close_db(e: Union[None, BaseException] = None) -> None:
    """Close database cursor, commit database and close database.

    Args:
        e (Union[None, BaseException], optional): Error. Defaults to None.
    """
    try:
        cursors = g.cursors
        db: DBConnection = cursors[0].connection
        for c in cursors:
            c.close()
        delattr(g, 'cursors')
        db.commit()
        if not current_thread().name.startswith('waitress-'):
            db.close()

    except (AttributeError, ProgrammingError):
        pass

    return


def close_all_db() -> None:
    "Close all non-temporary database connections that are still open"
    LOGGER.debug('Closing any open database connections')

    for i in DBConnectionManager.instances.values():
        if not i.closed:
            i.close()

    c = DBConnection(timeout=20.0)
    c.commit()
    c.close()
    return


def setup_db() -> None:
    """
    Setup the database tables and default config when they aren't setup yet
    """
    from backend.implementations.users import Users
    from backend.internals.settings import Settings

    cursor = get_db()
    cursor.execute("PRAGMA journal_mode = wal;")
    register_adapter(bool, lambda b: int(b))
    register_converter("BOOL", lambda b: b == b'1')

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            salt VARCHAR(40) NOT NULL,
            hash VARCHAR(100) NOT NULL,
            admin BOOL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS notification_services(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255),
            url TEXT,

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            text TEXT,
            time INTEGER NOT NULL,

            repeat_quantity VARCHAR(15),
            repeat_interval INTEGER,
            original_time INTEGER,
            weekdays VARCHAR(13),

            color VARCHAR(7),

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS templates(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            text TEXT,

            color VARCHAR(7),

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS static_reminders(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            text TEXT,

            color VARCHAR(7),

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reminder_services(
            reminder_id INTEGER,
            static_reminder_id INTEGER,
            template_id INTEGER,
            notification_service_id INTEGER NOT NULL,

            FOREIGN KEY (reminder_id) REFERENCES reminders(id)
                ON DELETE CASCADE,
            FOREIGN KEY (static_reminder_id) REFERENCES static_reminders(id)
                ON DELETE CASCADE,
            FOREIGN KEY (template_id) REFERENCES templates(id)
                ON DELETE CASCADE,
            FOREIGN KEY (notification_service_id) REFERENCES notification_services(id)
        );
        CREATE TABLE IF NOT EXISTS config(
            key VARCHAR(255) PRIMARY KEY,
            value BLOB NOT NULL
        );
	""")

    settings = Settings()
    settings_values = settings.get_settings()

    set_log_level(settings_values.log_level)

    migrate_db()

    # DB Migration might change settings, so update cache just to be sure.
    settings._fetch_settings()

    # Add admin user if it doesn't exist
    users = Users()
    if Constants.ADMIN_USERNAME not in users:
        users.add(
            Constants.ADMIN_USERNAME, Constants.ADMIN_PASSWORD,
            force=True,
            is_admin=True
        )

    return


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
