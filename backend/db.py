#-*- coding: utf-8 -*-

"""
Setting up and interacting with the database.
"""

import logging
from datetime import datetime
from os import makedirs, remove
from os.path import dirname, isfile, join
from shutil import move
from sqlite3 import Connection, OperationalError, ProgrammingError, Row
from threading import current_thread, main_thread
from time import time
from typing import Type, Union

from flask import g

from backend.custom_exceptions import (AccessUnauthorized, InvalidDatabaseFile,
                                       UserNotFound)
from backend.helpers import RestartVars, folder_path
from backend.logging import set_log_level

DB_FILENAME = 'db', 'MIND.db'
__DATABASE_VERSION__ = 10
__DATEBASE_NAME_ORIGINAL__ = "MIND_original.db"

class DB_Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		i = f'{cls}{current_thread()}'
		if (i not in cls._instances
		or cls._instances[i].closed):
			cls._instances[i] = super(DB_Singleton, cls).__call__(*args, **kwargs)

		return cls._instances[i]

class DBConnection(Connection, metaclass=DB_Singleton):
	file = ''

	def __init__(self, timeout: float) -> None:
		logging.debug(f'Creating connection {self}')
		super().__init__(self.file, timeout=timeout)
		super().cursor().execute("PRAGMA foreign_keys = ON;")
		self.closed = False
		return

	def close(self) -> None:
		logging.debug(f'Closing connection {self}')
		self.closed = True
		super().close()
		return

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}; {current_thread().name}; {id(self)}>'

def setup_db_location() -> None:
	"""Create folder for database and link file to DBConnection class
	"""
	if isfile(folder_path('db', 'Noted.db')):
		move(folder_path('db', 'Noted.db'), folder_path(*DB_FILENAME))

	db_location = folder_path(*DB_FILENAME)
	logging.debug(f'Database location: {db_location}')
	makedirs(dirname(db_location), exist_ok=True)

	DBConnection.file = db_location
	return

def get_db(output_type: Union[Type[dict], Type[tuple]]=tuple):
	"""Get a database cursor instance. Coupled to Flask's g.

	Args:
		output_type (Union[Type[dict], Type[tuple]], optional):
		The type of output: a tuple or dictionary with the row values.
			Defaults to tuple.

	Returns:
		Cursor: The Cursor instance to use
	"""	
	try:
		cursor = g.cursor
	except AttributeError:
		db = DBConnection(timeout=20.0)
		cursor = g.cursor = db.cursor()

	if output_type is dict:
		cursor.row_factory = Row
	else:
		cursor.row_factory = None

	return g.cursor

def close_db(e=None) -> None:
	"""Savely closes the database connection
	"""	
	try:
		cursor = g.cursor
		db: DBConnection = cursor.connection
		cursor.close()
		delattr(g, 'cursor')
		db.commit()
		if current_thread() is main_thread():
			db.close()
	except (AttributeError, ProgrammingError):
		pass
	return

def migrate_db(current_db_version: int) -> None:
	"""
	Migrate a MIND database from it's current version 
	to the newest version supported by the MIND version installed.
	"""
	logging.info('Migrating database to newer version...')
	cursor = get_db()
	if current_db_version == 1:
		# V1 -> V2
		t = time()
		utc_offset = datetime.fromtimestamp(t) - datetime.utcfromtimestamp(t)
		cursor.execute("SELECT time, id FROM reminders;")
		new_reminders = []
		new_reminders_append = new_reminders.append
		for reminder in cursor:
			new_reminders_append([round((datetime.fromtimestamp(reminder[0]) - utc_offset).timestamp()), reminder[1]])
		cursor.executemany("UPDATE reminders SET time = ? WHERE id = ?;", new_reminders)
		current_db_version = 2
		
	if current_db_version == 2:
		# V2 -> V3
		cursor.executescript("""
			ALTER TABLE reminders
			ADD color VARCHAR(7);
			ALTER TABLE templates
			ADD color VARCHAR(7);
		""")
		current_db_version = 3
		
	if current_db_version == 3:
		# V3 -> V4
		cursor.executescript("""
			UPDATE reminders
			SET repeat_quantity = repeat_quantity || 's'
			WHERE repeat_quantity NOT LIKE '%s';
		""")
		current_db_version = 4

	if current_db_version == 4:
		# V4 -> V5
		cursor.executescript("""
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
		current_db_version = 5

	if current_db_version == 5:
		# V5 -> V6
		from backend.users import User
		try:
			User('User1', 'Password1').delete()
		except (UserNotFound, AccessUnauthorized):
			pass
		
		current_db_version = 6

	if current_db_version == 6:
		# V6 -> V7
		cursor.executescript("""
			ALTER TABLE reminders
			ADD weekdays VARCHAR(13);
		""")
		current_db_version = 7

	if current_db_version == 7:
		# V7 -> V8
		from backend.settings import _format_setting, default_settings
		from backend.users import Users

		cursor.executescript("""
			DROP TABLE config;
			CREATE TABLE IF NOT EXISTS config(
				key VARCHAR(255) PRIMARY KEY,
				value BLOB NOT NULL
			);
			"""
		)
		cursor.executemany("""
			INSERT OR IGNORE INTO config(key, value)
			VALUES (?, ?);
			""",
			map(
				lambda kv: (kv[0], _format_setting(*kv)),
				default_settings.items()
			)
		)

		cursor.executescript("""
			ALTER TABLE users
			ADD admin BOOL NOT NULL DEFAULT 0;
					   
			UPDATE users
			SET username = 'admin_old'
			WHERE username = 'admin';
		""")

		Users().add('admin', 'admin', True)

		cursor.execute("""
			UPDATE users
			SET admin = 1
			WHERE username = 'admin';
		""")

		current_db_version = 8

	if current_db_version == 8:
		# V8 -> V9
		from backend.settings import set_setting
		from MIND import HOST, PORT, URL_PREFIX

		set_setting('host', HOST)
		set_setting('port', int(PORT))
		set_setting('url_prefix', URL_PREFIX)

		current_db_version = 9

	if current_db_version == 9:
		# V9 -> V10

		# Nothing is changed in the database
		# It's just that this code needs to run once
		# and the DB migration system does exactly that:
		# run pieces of code once.
		from backend.settings import update_manifest

		url_prefix: str = cursor.execute(
			"SELECT value FROM config WHERE key = 'url_prefix' LIMIT 1;"
		).fetchone()[0]
		update_manifest(url_prefix)

		current_db_version = 10

	return

def setup_db() -> None:
	"""Setup the database
	"""
	from backend.settings import (_format_setting, default_settings, get_setting,
	                              set_setting)
	from backend.users import Users

	cursor = get_db()
	cursor.execute("PRAGMA journal_mode = wal;")

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

	cursor.executemany("""
		INSERT OR IGNORE INTO config(key, value)
		VALUES (?, ?);
		""",
		map(
			lambda kv: (kv[0], _format_setting(*kv)),
			default_settings.items()
		)
	)

	set_log_level(get_setting('log_level'))

	current_db_version = get_setting('database_version')
	if current_db_version < __DATABASE_VERSION__:
		logging.debug(
			f'Database migration: {current_db_version} -> {__DATABASE_VERSION__}'
		)
		migrate_db(current_db_version)
		set_setting('database_version', __DATABASE_VERSION__)

	users = Users()
	if not 'admin' in users:
		users.add('admin', 'admin', True)
		cursor.execute("""
			UPDATE users
			SET admin = 1
			WHERE username = 'admin';
		""")

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
		to use `__DATABASE_NAME_ORIGINAL__`. Defaults to ''.
	"""
	original_db_file = DBConnection.file
	if not imported_db_file:
		imported_db_file = join(dirname(DBConnection.file), __DATEBASE_NAME_ORIGINAL__)
	
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
	logging.info(f'Importing new database; {copy_hosting_settings=}')
	try:
		cursor = Connection(new_db_file, timeout=20.0).cursor()

		database_version = cursor.execute(
			"SELECT value FROM config WHERE key = 'database_version' LIMIT 1;"
		).fetchone()[0]
		if not isinstance(database_version, int):
			raise InvalidDatabaseFile

	except (OperationalError, InvalidDatabaseFile):
		logging.error('Uploaded database is not a MIND database file')
		cursor.connection.close()
		revert_db_import(
			swap=False,
			imported_db_file=new_db_file
		)
		raise InvalidDatabaseFile

	if database_version > __DATABASE_VERSION__:
		logging.error('Uploaded database is higher version than this MIND installation can support')
		revert_db_import(
			swap=False,
			imported_db_file=new_db_file
		)
		raise InvalidDatabaseFile

	if copy_hosting_settings:
		hosting_settings = get_db().execute("""
			SELECT key, value, value
			FROM config
			WHERE key = 'host'
				OR key = 'port'
				OR key = 'url_prefix'
			LIMIT 3;
			"""
		)
		cursor.executemany("""
			INSERT INTO config(key, value)
			VALUES (?, ?)
			ON CONFLICT(key) DO
			UPDATE
			SET value = ?;
			""",
			hosting_settings
		)
	cursor.connection.commit()
	cursor.connection.close()

	move(
		DBConnection.file,
		join(dirname(DBConnection.file), __DATEBASE_NAME_ORIGINAL__)
	)
	move(
		new_db_file,
		DBConnection.file
	)

	from backend.server import SERVER
	SERVER.restart([RestartVars.DB_IMPORT.value])

	return
