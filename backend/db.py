#-*- coding: utf-8 -*-

from datetime import datetime
import logging
from sqlite3 import Connection, ProgrammingError, Row
from threading import current_thread, main_thread
from time import time
from typing import Union

from flask import g
from waitress.task import ThreadedTaskDispatcher as OldThreadedTaskDispatcher

from backend.custom_exceptions import AccessUnauthorized, UserNotFound

__DATABASE_VERSION__ = 7

class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		i = f'{cls}{current_thread()}'
		if (i not in cls._instances
      	or cls._instances[i].closed):
			logging.debug(f'Creating singleton instance: {i}')
			cls._instances[i] = super(Singleton, cls).__call__(*args, **kwargs)

		return cls._instances[i]

class ThreadedTaskDispatcher(OldThreadedTaskDispatcher):
	def handler_thread(self, thread_no: int) -> None:
		super().handler_thread(thread_no)
		i = f'{DBConnection}{current_thread()}'
		if i in Singleton._instances and not Singleton._instances[i].closed:
			logging.debug(f'Closing singleton instance: {i}')
			Singleton._instances[i].close()
			
	def shutdown(self, cancel_pending: bool = True, timeout: int = 5) -> bool:
		print()
		logging.info('Shutting down MIND...')
		super().shutdown(cancel_pending, timeout)
		DBConnection(20.0).close()

class DBConnection(Connection, metaclass=Singleton):
	file = ''
	
	def __init__(self, timeout: float) -> None:
		logging.debug(f'Opening database connection for {current_thread()}')
		super().__init__(self.file, timeout=timeout)
		super().cursor().execute("PRAGMA foreign_keys = ON;")
		self.closed = False
		return

	def close(self) -> None:
		logging.debug(f'Closing database connection for {current_thread()}')
		self.closed = True
		super().close()
		return

def get_db(output_type: Union[dict, tuple]=tuple):
	"""Get a database cursor instance. Coupled to Flask's g.

	Args:
		output_type (Union[dict, tuple], optional): The type of output: a tuple or dictionary with the row values. Defaults to tuple.

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

	return

def setup_db() -> None:
	"""Setup the database
	"""
	cursor = get_db()
	cursor.execute("PRAGMA journal_mode = wal;")

	cursor.executescript("""
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER PRIMARY KEY,
			username VARCHAR(255) UNIQUE NOT NULL,
			salt VARCHAR(40) NOT NULL,
			hash VARCHAR(100) NOT NULL
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
			value TEXT NOT NULL
		);
	""")

	cursor.execute("""
		INSERT OR IGNORE INTO config(key, value)
		VALUES ('database_version', ?);
		""",
		(__DATABASE_VERSION__,)
	)
	current_db_version = int(cursor.execute(
		"SELECT value FROM config WHERE key = 'database_version' LIMIT 1;"
	).fetchone()[0])
	
	logging.debug(f'Current database version {current_db_version} and desired database version {__DATABASE_VERSION__}')
	if current_db_version < __DATABASE_VERSION__:
		migrate_db(current_db_version)
		cursor.execute(
			"UPDATE config SET value = ? WHERE key = 'database_version';",
			(__DATABASE_VERSION__,)
		)

	return
