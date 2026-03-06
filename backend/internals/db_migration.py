# -*- coding: utf-8 -*-

from typing import Callable, Dict

from backend.base.definitions import Constants
from backend.base.logging import LOGGER
from backend.internals.db import get_db, iter_commit


# region Handler
class DatabaseMigrationHandler:
    """Handles the registration of all migrators and running them if needed.
    To add a migration, simply write the funtion and decorate it with
    `register_handler(...)`. The `migrate(...)` method will take care of running
    it.
    """

    handlers: Dict[int, Callable[[], None]] = {}

    @classmethod
    def register_handler(cls, start_version: int):
        """Register a database migrator.

        Args:
            start_version (int): The database version that it migrates _from_.
                So start_version=2 means migrating from 2 to 3.

        Raises:
            RuntimeError: A database migration with the given start_version is
                already registered.
        """
        def wrapper(migrator: Callable[[], None]):
            if start_version in cls.handlers:
                raise RuntimeError(
                    f"Database migration with start version {start_version} "
                    "registered multiple times"
                )
            cls.handlers[start_version] = migrator
            return migrator
        return wrapper

    @classmethod
    def latest_db_version(cls) -> int:
        """Get the latest database version supported.

        Returns:
            int: The version.
        """
        return max(cls.handlers) + 1

    @classmethod
    def migrate(cls) -> None:
        """
        Migrate a MIND database from its current version to the newest
        version supported by the MIND version installed.
        """
        from backend.internals.settings import Settings

        s = Settings()
        current_db_version = s.sv.database_version
        newest_version = cls.latest_db_version()

        if current_db_version > newest_version:
            LOGGER.warning(
                "Database is for newer version of MIND"
            )
            return

        if current_db_version == newest_version:
            return

        LOGGER.info("Migrating database to newer version...")
        LOGGER.debug(
            "Database migration: %d -> %d",
            current_db_version, newest_version
        )

        for start_version in iter_commit(
            range(current_db_version, newest_version)
        ):
            if start_version not in cls.handlers:
                continue

            cls.handlers[start_version]()
            s.update({"database_version": start_version + 1})

        get_db().execute("VACUUM;")
        s.clear_cache()

        return


# region Migrators
# Please name all of the migrators with an underscore prefix. This way they
# won't show up as importable functions in other files by IDEs.

@DatabaseMigrationHandler.register_handler(1)
def _migrate_to_utc():
    from datetime import datetime
    from time import time

    cursor = get_db()

    t = time()
    utc_offset = datetime.fromtimestamp(t) - datetime.utcfromtimestamp(t)

    cursor.execute("SELECT time, id FROM reminders;")
    new_reminders = [
        [
            round((
                datetime.fromtimestamp(r["time"]) - utc_offset
            ).timestamp()),
            r["id"]
        ]
        for r in cursor
    ]

    cursor.executemany(
        "UPDATE reminders SET time = ? WHERE id = ?;",
        new_reminders
    )
    return


@DatabaseMigrationHandler.register_handler(2)
def _migrate_add_color():
    get_db().executescript("""
        ALTER TABLE reminders
            ADD color VARCHAR(7);
        ALTER TABLE templates
            ADD color VARCHAR(7);
    """)

    return


@DatabaseMigrationHandler.register_handler(3)
def _migrate_fix_rq():
    get_db().executescript("""
        UPDATE reminders
        SET repeat_quantity = repeat_quantity || 's'
        WHERE repeat_quantity NOT LIKE '%s';
    """)

    return


@DatabaseMigrationHandler.register_handler(4)
def _migrate_to_reminder_services():
    get_db().executescript("""
        BEGIN TRANSACTION;
        PRAGMA defer_foreign_keys = ON;

        CREATE TEMPORARY TABLE temp_reminder_services(
            reminder_id,
            static_reminder_id,
            template_id,
            notification_service_id
        );

        -- Reminders
        INSERT INTO temp_reminder_services(
            reminder_id, notification_service_id
        )
        SELECT id, notification_service
        FROM reminders;

        CREATE TEMPORARY TABLE temp_reminders AS
            SELECT
                id, user_id, title, text,
                time, repeat_quantity, repeat_interval, original_time,
                color
            FROM reminders;
        DROP TABLE reminders;
        CREATE TABLE reminders(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            text TEXT,
            time INTEGER NOT NULL,

            repeat_quantity VARCHAR(15),
            repeat_interval INTEGER,
            original_time INTEGER,

            color VARCHAR(7),

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        INSERT INTO reminders
            SELECT * FROM temp_reminders;

        -- Templates
        INSERT INTO temp_reminder_services(
            template_id, notification_service_id
        )
        SELECT id, notification_service
        FROM templates;

        CREATE TEMPORARY TABLE temp_templates AS
            SELECT id, user_id, title, text, color
            FROM templates;
        DROP TABLE templates;
        CREATE TABLE templates(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            text TEXT,

            color VARCHAR(7),

            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        INSERT INTO templates
            SELECT * FROM temp_templates;

        INSERT INTO reminder_services
            SELECT * FROM temp_reminder_services;

        COMMIT;
    """)

    return


@DatabaseMigrationHandler.register_handler(5)
def _migrate_remove_user1():
    from backend.base.custom_exceptions import AccessUnauthorized, UserNotFound
    from backend.implementations.users import Users

    try:
        Users().login('User1', 'Password1').delete()

    except (UserNotFound, AccessUnauthorized):
        pass

    return


@DatabaseMigrationHandler.register_handler(6)
def _migrate_add_weekdays():
    get_db().executescript("""
        ALTER TABLE reminders
            ADD weekdays VARCHAR(13);
    """)

    return


@DatabaseMigrationHandler.register_handler(7)
def _migrate_add_admin():
    from backend.implementations.users import Users
    from backend.internals.settings import Settings

    cursor = get_db()

    cursor.executescript("""
        DROP TABLE config;
        CREATE TABLE IF NOT EXISTS config(
            key VARCHAR(255) PRIMARY KEY,
            value BLOB NOT NULL
        );
        """
    )
    Settings()._insert_missing_settings()

    cursor.executescript("""
        ALTER TABLE users
            ADD admin BOOL NOT NULL DEFAULT 0;
        """
    )
    users = Users()
    if 'admin' in users:
        users.get_one(
            users.user_db.username_to_id('admin')
        ).update_username('admin_old')

    users.add(
        Constants.ADMIN_USERNAME, Constants.ADMIN_PASSWORD,
        force=True,
        is_admin=True
    )

    return


@DatabaseMigrationHandler.register_handler(8)
def _migrate_host_settings_to_db():
    # In newer versions, the variables don't exist anymore, and behaviour
    # was to then set the values to the default values. But that's already
    # taken care of by the settings, so nothing to do here anymore.
    return


@DatabaseMigrationHandler.register_handler(9)
def _migrate_update_manifest():
    # There used to be a migration here that fixed the manifest file.
    # That has since been replaced by the dynamic endpoint serving the JSON.
    # So the migration doesn't do anything anymore, and a function used
    # doesn't exist anymore, so the whole migration is just removed.
    return


@DatabaseMigrationHandler.register_handler(10)
def _migrate_add_enabled():
    get_db().execute("""
        ALTER TABLE reminders
            ADD enabled BOOL NOT NULL DEFAULT 1;
    """)
    return


@DatabaseMigrationHandler.register_handler(11)
def _migrate_set_db_backup_folder():
    from backend.internals.settings import Settings, SettingsValues

    s = Settings()
    sv = s.get_settings()
    if sv.db_backup_folder == '':
        s.update({"db_backup_folder": SettingsValues.db_backup_folder})

    return


@DatabaseMigrationHandler.register_handler(12)
def _migrate_add_cron_schedule_column():
    get_db().executescript("""
        PRAGMA foreign_keys = OFF;
        BEGIN TRANSACTION;

        CREATE TEMPORARY TABLE temp_reminders_13 AS
            SELECT * FROM reminders;
        DROP TABLE reminders;

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

        INSERT INTO reminders
            SELECT
                id, user_id,
                title, text, time,
                repeat_quantity, repeat_interval,
                original_time, weekdays,
                NULL AS cron_schedule,
                color, enabled
            FROM temp_reminders_13;

        COMMIT;
        PRAGMA foreign_keys = ON;
    """)


@DatabaseMigrationHandler.register_handler(13)
def _migrate_add_mfa_column():
    get_db().executescript("""
        ALTER TABLE users
            ADD mfa_apprise_url TEXT;
    """)
    return
