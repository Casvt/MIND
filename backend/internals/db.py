# -*- coding: utf-8 -*-

"""
Setting up the database, handling connections, using it and closing it.
"""

from __future__ import annotations

from os.path import dirname, exists, isdir, isfile, join
from sqlite3 import (PARSE_DECLTYPES, Connection, Cursor, ProgrammingError,
                     Row, register_adapter, register_converter)
from threading import current_thread
from typing import Any, Dict, Generator, Iterable, List, Type, Union

from flask import g

from backend.base.definitions import Constants, ReminderType, T
from backend.base.helpers import (create_folder, current_thread_id,
                                  folder_path, rename_file)
from backend.base.logging import LOGGER, set_log_level

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

    @property
    def connection(self) -> DBConnection:
        return super().connection # type: ignore

    def __init__(self, cursor: DBConnection, /) -> None:
        super().__init__(cursor)
        return

    def fetchonedict(self) -> Union[Dict[str, Any], None]:
        """Same as `fetchone` but convert the Row object to a dict.

        Returns:
            Union[Dict[str, Any], None]: The dict or None in case of no result.
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

    def __enter__(self):
        """Start a transaction"""
        self.connection.isolation_level = None
        self.execute("BEGIN TRANSACTION;")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit the transaction or rollback if an exception occurred"""
        if self.connection.in_transaction:
            if exc_type is not None:
                self.execute("ROLLBACK;")
            else:
                self.execute("COMMIT;")

        self.connection.isolation_level = ""
        return


class DBConnectionManager(type):
    instances: Dict[int, DBConnection] = {}

    def __call__(cls, **kwargs: Any) -> DBConnection:
        if kwargs.get('db_file'):
            return super().__call__(**kwargs)

        thread_id = current_thread_id()

        if (
            not thread_id in cls.instances
            or cls.instances[thread_id].closed
        ):
            cls.instances[thread_id] = super().__call__(**kwargs)

        return cls.instances[thread_id]


class DBConnection(Connection, metaclass=DBConnectionManager):
    default_file = ''

    def __init__(
        self, *,
        db_file: Union[str, None] = None,
        timeout: float = Constants.DB_TIMEOUT
    ) -> None:
        """Create a connection with a database.

        Args:
            db_file (Union[str, None], optional): The database file to connect
                to. If `None`, the default file will be used. If something else
                than the default file is given, then a new connection will
                always be returned.
                Defaults to None.

            timeout (float, optional): How long to wait before giving up
                on a command.
                Defaults to Constants.DB_TIMEOUT.
        """
        LOGGER.debug(f'Creating connection {self}')
        self.db_file = db_file or self.default_file
        super().__init__(
            self.db_file,
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
        """Get a database cursor of the connection.

        Args:
            force_new (bool, optional): Get a new cursor instead of the cached
                one.
                Defaults to False.

        Returns:
            MindCursor: The database cursor.
        """
        if not hasattr(g, 'cursors'):
            g.cursors = {}

        if self.db_file not in g.cursors:
            g.cursors[self.db_file] = []

        if not g.cursors[self.db_file]:
            c = MindCursor(self)
            c.row_factory = Row
            g.cursors[self.db_file].append(c)

        if not force_new:
            return g.cursors[self.db_file][0]
        else:
            c = MindCursor(self)
            c.row_factory = Row
            g.cursors[self.db_file].append(c)
            return g.cursors[self.db_file][-1]

    def create_backup(self, filepath: str) -> None:
        """Create a backup of the current database.

        Args:
            filepath (str): What the filepath of the backup will be.
        """
        self.execute(
            "VACUUM INTO ?;",
            (filepath,)
        )
        return

    def merge_wal_files(self) -> None:
        """Merge the WAL files into the main database file"""
        self.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        return

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
    from backend.internals.settings import SettingsValues

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

    DBConnection.default_file = db_file_location
    SettingsValues.db_backup_folder = dirname(db_file_location)

    return


def get_db(force_new: bool = False) -> MindCursor:
    """Get a database cursor instance or create a new one if needed.

    Args:
        force_new (bool, optional): Decides whether a new cursor is
            returned instead of the standard one.
            Defaults to False.

    Returns:
        MindCursor: Database cursor instance that outputs Row objects.
    """
    return DBConnection().cursor(force_new=force_new)


def commit() -> None:
    """Commit the database changes"""
    get_db().connection.commit()
    return


def iter_commit(iterable: Iterable[T]) -> Generator[T]:
    """Commit the database after yielding each value in the iterable. Also
    commits just before the first iteration starts.

    ```
    # commits
    for i in iter_commit(iterable):
        cursor.execute(...)
        # commits
    ```

    Args:
        iterable (Iterable[T]): Iterable that will be iterated over like normal.

    Yields:
        Generator[T]: Items of iterable.
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
    if not hasattr(g, 'cursors'):
        return

    try:
        cursors = g.cursors
        for cursors in g.cursors.values():
            db: DBConnection = cursors[0].connection
            for c in cursors:
                c.close()
            db.commit()
            if not current_thread().name.startswith('waitress-'):
                db.close()
        delattr(g, 'cursors')

    except ProgrammingError:
        pass

    return


def setup_db_adapters_and_converters() -> None:
    """Add DB adapters and converters for custom types and bool"""
    register_adapter(bool, lambda b: int(b))
    register_converter("BOOL", lambda b: b == b'1')
    return


def setup_db() -> None:
    """Setup the default config and database connection and tables"""
    from backend.implementations.users import Users
    from backend.internals.db_migration import migrate_db
    from backend.internals.settings import Settings

    cursor = get_db()
    cursor.execute("PRAGMA journal_mode = wal;")
    setup_db_adapters_and_converters()

    cursor.executescript(DB_SCHEMA)

    settings = Settings()
    settings_values = settings.get_settings()

    set_log_level(settings_values.log_level)

    migrate_db()

    # DB Migration might change settings directly in database,
    # so clear cache just to be sure.
    settings.clear_cache()

    # Add admin user if it doesn't exist
    users = Users()
    if Constants.ADMIN_USERNAME not in users:
        users.add(
            Constants.ADMIN_USERNAME, Constants.ADMIN_PASSWORD,
            force=True,
            is_admin=True
        )

    return


DB_SCHEMA = """
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
        cron_schedule VARCHAR(255),

        color VARCHAR(7),
        enabled BOOL NOT NULL DEFAULT 1,

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
"""
