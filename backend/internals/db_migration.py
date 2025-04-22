# -*- coding: utf-8 -*-

from typing import Dict, Type

from backend.base.definitions import Constants, DBMigrator
from backend.base.logging import LOGGER


class VersionMappingContainer:
    version_map: Dict[int, Type[DBMigrator]] = {}


def _load_version_map() -> None:
    if VersionMappingContainer.version_map:
        return

    VersionMappingContainer.version_map = {
        m.start_version: m
        for m in DBMigrator.__subclasses__()
    }
    return


def get_latest_db_version() -> int:
    _load_version_map()
    return max(VersionMappingContainer.version_map) + 1


def migrate_db() -> None:
    """
    Migrate a MIND database from it's current version
    to the newest version supported by the MIND version installed.
    """
    from backend.internals.db import iter_commit
    from backend.internals.settings import Settings

    s = Settings()
    current_db_version = s.get_settings().database_version
    newest_version = get_latest_db_version()
    if current_db_version == newest_version:
        return

    LOGGER.info('Migrating database to newer version...')
    LOGGER.debug(
        "Database migration: %d -> %d",
        current_db_version, newest_version
    )

    for start_version in iter_commit(range(current_db_version, newest_version)):
        if start_version not in VersionMappingContainer.version_map:
            continue
        VersionMappingContainer.version_map[start_version]().run()
        s.update({'database_version': start_version + 1})

    s._fetch_settings()

    return


class MigrateToUTC(DBMigrator):
    start_version = 1

    def run(self) -> None:
        # V1 -> V2

        from datetime import datetime
        from time import time

        from backend.internals.db import get_db

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


class MigrateAddColor(DBMigrator):
    start_version = 2

    def run(self) -> None:
        # V2 -> V3

        from backend.internals.db import get_db

        get_db().executescript("""
			ALTER TABLE reminders
			ADD color VARCHAR(7);
			ALTER TABLE templates
			ADD color VARCHAR(7);
		""")

        return


class MigrateFixRQ(DBMigrator):
    start_version = 3

    def run(self) -> None:
        # V3 -> V4

        from backend.internals.db import get_db

        get_db().executescript("""
			UPDATE reminders
			SET repeat_quantity = repeat_quantity || 's'
			WHERE repeat_quantity NOT LIKE '%s';
		""")

        return


class MigrateToReminderServices(DBMigrator):
    start_version = 4

    def run(self) -> None:
        # V4 -> V5

        from backend.internals.db import get_db

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
			INSERT INTO temp_reminder_services(reminder_id, notification_service_id)
			SELECT id, notification_service
			FROM reminders;

			CREATE TEMPORARY TABLE temp_reminders AS
				SELECT id, user_id, title, text, time, repeat_quantity, repeat_interval, original_time, color
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
			INSERT INTO temp_reminder_services(template_id, notification_service_id)
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


class MigrateRemoveUser1(DBMigrator):
    start_version = 5

    def run(self) -> None:
        # V5 -> V6
        from backend.base.custom_exceptions import (AccessUnauthorized,
                                                    UserNotFound)
        from backend.implementations.users import Users

        try:
            Users().login('User1', 'Password1').delete()

        except (UserNotFound, AccessUnauthorized):
            pass

        return


class MigrateAddWeekdays(DBMigrator):
    start_version = 6

    def run(self) -> None:
        # V6 -> V7

        from backend.internals.db import get_db

        get_db().executescript("""
			ALTER TABLE reminders
			ADD weekdays VARCHAR(13);
		""")

        return


class MigrateAddAdmin(DBMigrator):
    start_version = 7

    def run(self) -> None:
        # V7 -> V8

        from backend.implementations.users import Users
        from backend.internals.db import get_db
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
            ).update(
                new_username='admin_old',
                new_password=None
            )

        users.add(
            Constants.ADMIN_USERNAME, Constants.ADMIN_PASSWORD,
            force=True,
            is_admin=True
        )

        return


class MigrateHostSettingsToDB(DBMigrator):
    start_version = 8

    def run(self) -> None:
        # V8 -> V9
        # In newer versions, the variables don't exist anymore, and behaviour
        # was to then set the values to the default values. But that's already
        # taken care of by the settings, so nothing to do here anymore.
        return


class MigrateUpdateManifest(DBMigrator):
    start_version = 9

    def run(self) -> None:
        # V9 -> V10

        # Nothing is changed in the database
        # It's just that this code needs to run once
        # and the DB migration system does exactly that:
        # run pieces of code once.
        from backend.internals.settings import Settings, update_manifest

        update_manifest(
            Settings().get_settings().url_prefix
        )

        return
