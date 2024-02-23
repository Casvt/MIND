#-*- coding: utf-8 -*-

"""
Setting up and interacting with the database.
"""

import logging
from datetime import datetime
from sqlite3 import Connection, ProgrammingError, Row
from threading import current_thread, main_thread
from time import time
from typing import Type, Union

from flask import g
from waitress.task import ThreadedTaskDispatcher as OldThreadedTaskDispatcher

from backend.custom_exceptions import AccessUnauthorized, UserNotFound

__DATABASE_VERSION__ = 8

class DB_Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		i = f'{cls}{current_thread()}'
		if (i not in cls._instances
		or cls._instances[i].closed):
			cls._instances[i] = super(DB_Singleton, cls).__call__(*args, **kwargs)

		return cls._instances[i]

class ThreadedTaskDispatcher(OldThreadedTaskDispatcher):
	def handler_thread(self, thread_no: int) -> None:
		super().handler_thread(thread_no)
		i = f'{DBConnection}{current_thread()}'
		if i in DB_Singleton._instances and not DB_Singleton._instances[i].closed:
			DB_Singleton._instances[i].close()
		return

	def shutdown(self, cancel_pending: bool = True, timeout: int = 5) -> bool:
		print()
		logging.info('Shutting down MIND')
		result = super().shutdown(cancel_pending, timeout)
		return result

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
